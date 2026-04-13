#!/usr/bin/env python3
"""Download and install all Nerd Fonts from the latest GitHub release."""

import argparse
import json
import os
import platform
import shutil
import signal
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

GITHUB_API_URL = "https://api.github.com/repos/ryanoasis/nerd-fonts/releases/{version}"
FONT_EXTENSIONS = {".ttf", ".otf"}
SKIP_ASSETS = {"FontPatcher"}


def get_font_dir():
    system = platform.system()
    if system == "Linux":
        return Path.home() / ".local" / "share" / "fonts" / "NerdFonts"
    if system == "Darwin":
        return Path.home() / "Library" / "Fonts" / "NerdFonts"
    if system == "Windows":
        local = os.environ.get("LOCALAPPDATA", "")
        if not local:
            raise RuntimeError("%LOCALAPPDATA% is not set")
        return Path(local) / "Microsoft" / "Windows" / "Fonts"
    raise RuntimeError(f"Unsupported OS: {system}")


def fetch_release(version):
    tag = "latest" if version == "latest" else f"tags/{version}"
    url = GITHUB_API_URL.format(version=tag)
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"Error: release '{version}' not found.", file=sys.stderr)
            sys.exit(1)
        raise


def parse_assets(release):
    """Return a dict mapping font_name -> download_url, choosing the right archive format."""
    use_zip = platform.system() == "Windows"
    suffix = ".zip" if use_zip else ".tar.xz"
    fonts = {}
    for asset in release["assets"]:
        name = asset["name"]
        if name.endswith(".tar.xz"):
            base = name[: -len(".tar.xz")]
        elif name.endswith(".zip"):
            base = name[: -len(".zip")]
        else:
            continue
        if base in SKIP_ASSETS:
            continue
        if name.endswith(suffix):
            fonts[base] = asset["browser_download_url"]
    return fonts


def download_file(url, dest):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as f:
        shutil.copyfileobj(resp, f)


def extract_fonts(archive_path, dest_dir):
    """Extract font files from an archive, returning the list of installed paths."""
    installed = []
    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                p = Path(info.filename)
                if p.suffix.lower() in FONT_EXTENSIONS:
                    target = dest_dir / p.name
                    with zf.open(info) as src, open(target, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    installed.append(target)
    else:
        with tarfile.open(archive_path, "r:xz") as tf:
            for member in tf.getmembers():
                if not member.isfile():
                    continue
                p = Path(member.name)
                if p.suffix.lower() in FONT_EXTENSIONS:
                    target = dest_dir / p.name
                    with tf.extractfile(member) as src, open(target, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    installed.append(target)
    return installed


def register_windows_fonts(font_paths):
    """Register per-user fonts in the Windows registry."""
    if platform.system() != "Windows":
        return
    try:
        import winreg
    except ImportError:
        return

    key_path = r"Software\Microsoft\Windows NT\CurrentVersion\Fonts"
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
    ) as key:
        for fp in font_paths:
            winreg.SetValueEx(key, fp.stem, 0, winreg.REG_SZ, str(fp))


def refresh_font_cache():
    system = platform.system()
    if system == "Linux":
        fc = shutil.which("fc-cache")
        if fc:
            print("Refreshing font cache...")
            os.system(f"{fc} -fv")
        else:
            print(
                "Warning: fc-cache not found. "
                "Install fontconfig to refresh the font cache.",
                file=sys.stderr,
            )
    elif system == "Darwin":
        print("macOS will detect the new fonts automatically.")


def download_and_install_one(name, url, font_dir, tmp_dir, force):
    """Download and install a single font family. Returns (name, count, error)."""
    suffix = ".zip" if url.endswith(".zip") else ".tar.xz"
    archive = Path(tmp_dir) / f"{name}{suffix}"
    family_dir = font_dir / name
    if family_dir.exists() and any(family_dir.iterdir()) and not force:
        return name, 0, "skipped (already installed)"
    family_dir.mkdir(parents=True, exist_ok=True)
    try:
        download_file(url, archive)
        installed = extract_fonts(archive, family_dir)
        return name, len(installed), None
    except Exception as e:
        return name, 0, str(e)


def main():
    parser = argparse.ArgumentParser(description="Download and install all Nerd Fonts.")
    parser.add_argument(
        "--jobs",
        "-j",
        type=int,
        default=4,
        help="Number of parallel downloads (default: 4)",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep downloaded archives after installation",
    )
    parser.add_argument(
        "--font-dir",
        type=Path,
        default=None,
        help="Override the font installation directory",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_fonts",
        help="List available fonts and exit",
    )
    parser.add_argument(
        "--version",
        default="latest",
        help="Release version to install (default: latest)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download and overwrite existing fonts",
    )
    args = parser.parse_args()

    font_dir = args.font_dir or get_font_dir()

    print(f"Fetching release info ({args.version})...")
    release = fetch_release(args.version)
    tag = release["tag_name"]
    fonts = parse_assets(release)
    print(f"Release: {tag} — {len(fonts)} font families available\n")

    if args.list_fonts:
        for name in sorted(fonts):
            print(f"  {name}")
        return

    font_dir.mkdir(parents=True, exist_ok=True)
    print(f"Install directory: {font_dir}")
    print(f"Parallel jobs:    {args.jobs}\n")

    tmp_dir = tempfile.mkdtemp(prefix="nerd-fonts-")
    interrupted = False

    def handle_sigint(_sig, _frame):
        nonlocal interrupted
        interrupted = True
        print("\nInterrupted — cleaning up...", file=sys.stderr)

    prev_handler = signal.signal(signal.SIGINT, handle_sigint)

    total_fonts = 0
    skipped = 0
    failed = []
    sorted_fonts = sorted(fonts.items())

    try:
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = {
                pool.submit(
                    download_and_install_one, name, url, font_dir, tmp_dir, args.force
                ): name
                for name, url in sorted_fonts
            }
            for i, future in enumerate(as_completed(futures), 1):
                if interrupted:
                    break
                name, count, error = future.result()
                if error and "skipped" in error:
                    skipped += 1
                    status = f"[{i}/{len(fonts)}] {name}: {error}"
                elif error:
                    failed.append((name, error))
                    status = f"[{i}/{len(fonts)}] {name}: FAILED — {error}"
                else:
                    total_fonts += count
                    status = f"[{i}/{len(fonts)}] {name}: installed {count} font files"
                print(status)
    finally:
        signal.signal(signal.SIGINT, prev_handler)
        if not args.keep:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        else:
            print(f"\nArchives kept in: {tmp_dir}")

    if interrupted:
        print("\nAborted by user.", file=sys.stderr)
        sys.exit(130)

    print(f"\nDone: {total_fonts} font files installed, {skipped} skipped.")
    if failed:
        print(f"{len(failed)} failed:", file=sys.stderr)
        for name, err in failed:
            print(f"  {name}: {err}", file=sys.stderr)

    all_font_paths = []
    if platform.system() == "Windows":
        for child in font_dir.iterdir():
            if child.is_dir():
                all_font_paths.extend(
                    p for p in child.iterdir() if p.suffix.lower() in FONT_EXTENSIONS
                )
        if all_font_paths:
            print("Registering fonts in Windows registry...")
            register_windows_fonts(all_font_paths)

    refresh_font_cache()


if __name__ == "__main__":
    main()
