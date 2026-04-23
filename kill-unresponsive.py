#!/usr/bin/env python3
from __future__ import annotations

"""Detect and kill 'Not Responding' GUI applications on macOS.

Uses the private SkyLight framework API (SLSEventIsAppUnresponsive) -- the same
mechanism Activity Monitor uses -- to detect unresponsive apps, then optionally
kills them after a configurable grace period.

Requirements:
  - macOS only (uses private WindowServer APIs)
  - Must be run from a logged-in GUI session (not over SSH)
  - Private APIs verified on macOS 26.4; may break on future releases
"""

import argparse
import ctypes
from ctypes import POINTER, Structure, byref, c_bool, c_int, c_uint32
import logging
import os
from pathlib import Path
import plistlib
import re
import signal
import subprocess
import sys
import time

logger = logging.getLogger(os.path.basename(__file__))


class ProcessSerialNumber(Structure):
    _fields_ = [("highLongOfPSN", c_uint32), ("lowLongOfPSN", c_uint32)]


class SkyLightAPI:
    """Thin wrapper around the private SkyLight + Carbon APIs needed for
    detecting unresponsive applications."""

    _SKYLIGHT_PATH = "/System/Library/PrivateFrameworks/SkyLight.framework/SkyLight"
    _CARBON_PATH = "/System/Library/Frameworks/Carbon.framework/Carbon"

    def __init__(self):
        skylight = ctypes.cdll.LoadLibrary(self._SKYLIGHT_PATH)
        carbon = ctypes.cdll.LoadLibrary(self._CARBON_PATH)

        self._main_cid = skylight.SLSMainConnectionID
        self._main_cid.restype = c_int

        self._is_unresponsive = skylight.SLSEventIsAppUnresponsive
        self._is_unresponsive.restype = c_bool
        self._is_unresponsive.argtypes = [c_int, POINTER(ProcessSerialNumber)]

        self._get_psn = carbon.GetProcessForPID
        self._get_psn.restype = c_int  # OSStatus
        self._get_psn.argtypes = [c_int, POINTER(ProcessSerialNumber)]

        self.cid = self._main_cid()
        if self.cid == 0:
            raise RuntimeError(
                "Failed to obtain WindowServer connection. "
                "Are you running from a GUI session?"
            )

        self._hide_dock_icon(carbon)

    @staticmethod
    def _hide_dock_icon(carbon) -> None:
        """Prevent the Python rocket icon from appearing in the Dock by
        transforming this process into a UI-element (agent) app."""
        _K_CURRENT_PROCESS = ProcessSerialNumber(0, 2)
        _K_TRANSFORM_TO_UI_ELEMENT = 4
        transform = carbon.TransformProcessType
        transform.restype = c_int
        transform.argtypes = [POINTER(ProcessSerialNumber), c_uint32]
        transform(byref(_K_CURRENT_PROCESS), _K_TRANSFORM_TO_UI_ELEMENT)

    def is_unresponsive(self, pid: int) -> bool | None:
        """Return True if *pid* is unresponsive, False if responsive, or None
        if the PID could not be resolved to a ProcessSerialNumber."""
        psn = ProcessSerialNumber()
        if self._get_psn(pid, byref(psn)) != 0:
            return None
        return self._is_unresponsive(self.cid, byref(psn))


def running_gui_apps() -> list[tuple[str, int]]:
    """Return ``[(name, pid), ...]`` for all LaunchServices-registered apps."""
    out = subprocess.check_output(["lsappinfo", "list"], text=True)
    apps: list[tuple[str, int]] = []
    current_name: str | None = None
    for line in out.splitlines():
        m = re.match(r'\s*\d+\)\s+"([^"]+)"', line)
        if m:
            current_name = m.group(1)
            continue
        m = re.match(r"\s+pid\s*=\s*(\d+)", line)
        if m and current_name is not None:
            apps.append((current_name, int(m.group(1))))
            current_name = None
    return apps


def kill_process(pid: int, name: str, force: bool = False) -> None:
    sig = signal.SIGKILL if force else signal.SIGTERM
    sig_name = "SIGKILL" if force else "SIGTERM"
    try:
        os.kill(pid, sig)
        logger.info("Sent %s to '%s' (pid %d)", sig_name, name, pid)
    except ProcessLookupError:
        logger.debug("Process '%s' (pid %d) already exited", name, pid)
    except PermissionError:
        logger.warning(
            "No permission to kill '%s' (pid %d); try running with sudo",
            name,
            pid,
        )


def process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def check_and_kill(
    api: SkyLightAPI,
    *,
    hung_since: dict[int, float],
    grace_period: float,
    exclude: set[str],
    dry_run: bool,
    force_kill_timeout: float,
) -> None:
    """Single pass: detect unresponsive apps and kill those past grace."""
    now = time.monotonic()
    seen_pids: set[int] = set()

    for name, pid in running_gui_apps():
        seen_pids.add(pid)

        if name in exclude:
            continue

        status = api.is_unresponsive(pid)
        if status is None:
            continue

        if status:
            if pid not in hung_since:
                hung_since[pid] = now
                logger.warning("'%s' (pid %d) is not responding", name, pid)
            elapsed = now - hung_since[pid]
            if elapsed >= grace_period:
                if dry_run:
                    logger.info(
                        "[dry-run] Would kill '%s' (pid %d) — "
                        "unresponsive for %.0fs",
                        name,
                        pid,
                        elapsed,
                    )
                else:
                    logger.info(
                        "Killing '%s' (pid %d) — unresponsive for %.0fs",
                        name,
                        pid,
                        elapsed,
                    )
                    kill_process(pid, name)
                    time.sleep(force_kill_timeout)
                    if process_alive(pid):
                        logger.warning(
                            "'%s' (pid %d) did not exit after SIGTERM, "
                            "sending SIGKILL",
                            name,
                            pid,
                        )
                        kill_process(pid, name, force=True)
                    hung_since.pop(pid, None)
            else:
                remaining = grace_period - elapsed
                logger.debug(
                    "'%s' (pid %d) still unresponsive; "
                    "%.0fs until kill (grace=%.0fs)",
                    name,
                    pid,
                    remaining,
                    grace_period,
                )
        else:
            if pid in hung_since:
                logger.info("'%s' (pid %d) became responsive again", name, pid)
                hung_since.pop(pid)

    stale = set(hung_since) - seen_pids
    for pid in stale:
        hung_since.pop(pid)


LAUNCHD_LABEL = "com.user.kill-unresponsive"
INSTALL_DIR = Path.home() / "Library" / "Application Support" / "kill-unresponsive"
INSTALLED_SCRIPT = INSTALL_DIR / "kill-unresponsive.py"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"
LOG_DIR = Path.home() / "Library" / "Logs" / "kill-unresponsive"


def _bootout() -> None:
    subprocess.run(
        ["launchctl", "bootout", f"gui/{os.getuid()}", str(PLIST_PATH)],
        capture_output=True,
    )


def install_launchd_service(args: argparse.Namespace) -> None:
    """Copy the script to ~/Library/Application Support, generate a launchd
    plist, and load it so the monitor starts at login."""
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)

    import shutil

    shutil.copy2(Path(__file__).resolve(), INSTALLED_SCRIPT)
    logger.info("Copied script to %s", INSTALLED_SCRIPT)

    program_args = [sys.executable, str(INSTALLED_SCRIPT)]
    if args.interval != 5:
        program_args += ["--interval", str(args.interval)]
    if args.grace_period != 30:
        program_args += ["--grace-period", str(args.grace_period)]
    if args.force_kill_timeout != 5:
        program_args += ["--force-kill-timeout", str(args.force_kill_timeout)]
    if args.exclude:
        program_args += ["--exclude", args.exclude]

    plist = {
        "Label": LAUNCHD_LABEL,
        "ProgramArguments": program_args,
        "ProcessType": "Background",
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": str(LOG_DIR / "stdout.log"),
        "StandardErrorPath": str(LOG_DIR / "stderr.log"),
    }

    if PLIST_PATH.exists():
        _bootout()

    with open(PLIST_PATH, "wb") as f:
        plistlib.dump(plist, f)

    subprocess.run(
        ["launchctl", "bootstrap", f"gui/{os.getuid()}", str(PLIST_PATH)],
        check=True,
    )

    logger.info("Installed and started launchd service")
    logger.info("  Script: %s", INSTALLED_SCRIPT)
    logger.info("  Plist:  %s", PLIST_PATH)
    logger.info("  Logs:   %s/", LOG_DIR)
    logger.info("  The monitor will start automatically at login.")
    logger.info("  Use --uninstall to remove it.")


def uninstall_launchd_service() -> None:
    """Unload the service, remove the plist and the installed script."""
    if not PLIST_PATH.exists() and not INSTALLED_SCRIPT.exists():
        logger.error("No service installed")
        sys.exit(1)

    if PLIST_PATH.exists():
        _bootout()
        PLIST_PATH.unlink()
        logger.info("Removed plist %s", PLIST_PATH)

    if INSTALLED_SCRIPT.exists():
        import shutil

        shutil.rmtree(INSTALL_DIR)
        logger.info("Removed installed script %s", INSTALL_DIR)

    logger.info("Launchd service uninstalled")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Detect and kill 'Not Responding' GUI applications on macOS. "
            "Uses the same private WindowServer API as Activity Monitor."
        ),
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5,
        help="Polling interval in seconds (default: 5)",
    )
    parser.add_argument(
        "--grace-period",
        type=float,
        default=30,
        help=(
            "Seconds an app must remain unresponsive before being killed "
            "(default: 30)"
        ),
    )
    parser.add_argument(
        "--force-kill-timeout",
        type=float,
        default=5,
        help="Seconds to wait after SIGTERM before sending SIGKILL (default: 5)",
    )
    parser.add_argument(
        "--exclude",
        type=str,
        default="",
        help='Comma-separated app names to never kill (e.g. "Finder,Xcode")',
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Detect and log but do not actually kill anything",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single check and exit (no polling loop)",
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install as a launchd service that starts at login",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove the launchd service",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if sys.platform != "darwin":
        logger.error("This script only works on macOS")
        sys.exit(1)

    if args.uninstall:
        uninstall_launchd_service()
        return

    if args.install:
        install_launchd_service(args)
        return

    try:
        api = SkyLightAPI()
    except OSError as e:
        logger.error("Failed to load macOS private frameworks: %s", e)
        sys.exit(1)

    logger.debug("WindowServer connection ID: %d", api.cid)

    exclude = {s.strip() for s in args.exclude.split(",") if s.strip()}
    if exclude:
        logger.info("Excluding apps: %s", ", ".join(sorted(exclude)))

    if args.dry_run:
        logger.info("Dry-run mode — will not kill any processes")

    hung_since: dict[int, float] = {}

    if args.once:
        check_and_kill(
            api,
            hung_since=hung_since,
            grace_period=0,
            exclude=exclude,
            dry_run=args.dry_run,
            force_kill_timeout=args.force_kill_timeout,
        )
        return

    logger.info(
        "Monitoring for unresponsive apps (interval=%.0fs, grace=%.0fs)",
        args.interval,
        args.grace_period,
    )

    try:
        while True:
            check_and_kill(
                api,
                hung_since=hung_since,
                grace_period=args.grace_period,
                exclude=exclude,
                dry_run=args.dry_run,
                force_kill_timeout=args.force_kill_timeout,
            )
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("Stopped by user")


if __name__ == "__main__":
    main()
