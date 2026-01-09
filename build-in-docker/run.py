#!/usr/bin/env python3
"""
Build a project inside a Docker container.

This script runs a build script inside a Docker container, mapping the source
directory and install directory from the host.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_IMAGE = (
    "compute-artifactory.amd.com:5000/rocm-base-images/ubuntu-24.04-bld:latest"
)


def check_docker_available():
    """Check if Docker is available on the system."""
    if shutil.which("docker") is None:
        print("Error: Docker is not installed or not in PATH", file=sys.stderr)
        sys.exit(1)


def validate_paths(src: Path, install: Path, script: Path):
    """Validate that required paths exist."""
    if not src.exists():
        print(f"Error: Source directory does not exist: {src}", file=sys.stderr)
        sys.exit(1)

    if not src.is_dir():
        print(f"Error: Source path is not a directory: {src}", file=sys.stderr)
        sys.exit(1)

    if not script.exists():
        print(f"Error: Build script does not exist: {script}", file=sys.stderr)
        sys.exit(1)

    if not script.is_file():
        print(f"Error: Build script is not a file: {script}", file=sys.stderr)
        sys.exit(1)

    # Create install directory if it doesn't exist
    if not install.exists():
        print(f"Creating install directory: {install}")
        install.mkdir(parents=True, exist_ok=True)


def build_docker_command(
    src: Path, install: Path, script: Path, image: str, uid: int, gid: int
) -> list[str]:
    """Build the Docker command to run."""
    # Resolve to absolute paths
    src_abs = src.resolve()
    install_abs = install.resolve()
    script_abs = script.resolve()

    cmd = [
        "docker",
        "run",
        "-it",
        "--rm",
        "--network=host",
        "--ipc=host",
        "--device=/dev/kfd",
        "--device=/dev/dri",
        "--group-add",
        "video",
        "--cap-add=SYS_PTRACE",
        "--cap-add=SYS_ADMIN",
        "--cap-add=DAC_READ_SEARCH",
        "--security-opt",
        "seccomp=unconfined",
        # Mount source directory
        "-v",
        f"{src_abs}:/src",
        # Mount install directory
        "-v",
        f"{install_abs}:/install",
        # Mount build script
        "-v",
        f"{script_abs}:/tmp/build.sh:ro",
        # Docker image
        image,
        # Command to run inside container
        "bash",
        "-c",
        f"mkdir -p /build && bash /tmp/build.sh /src /build /install && chown -R {uid}:{gid} /install",
    ]

    return cmd


def main():
    parser = argparse.ArgumentParser(
        description="Build a project inside a Docker container.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  %(prog)s -s ./llvm-project -i ./install -S ./build_llvm.sh

The build script will be called with three arguments:
  <script> /src /build /install

Where:
  /src     - Source directory (mapped from --src)
  /build   - Temporary build directory inside container
  /install - Install directory (mapped from --install)
""",
    )

    parser.add_argument(
        "-s",
        "--src",
        type=Path,
        required=True,
        help="Path to the source directory on the host",
    )

    parser.add_argument(
        "-i",
        "--install",
        type=Path,
        required=True,
        help="Path to the install directory on the host (will be created if it doesn't exist)",
    )

    parser.add_argument(
        "-S",
        "--script",
        type=Path,
        required=True,
        help="Path to the build script on the host",
    )

    parser.add_argument(
        "--image",
        type=str,
        default=DEFAULT_IMAGE,
        help=f"Docker image to use (default: {DEFAULT_IMAGE})",
    )

    args = parser.parse_args()

    # Check Docker is available
    check_docker_available()

    # Validate paths
    validate_paths(args.src, args.install, args.script)

    # Get current user's UID and GID
    uid = os.getuid()
    gid = os.getgid()

    # Build the Docker command
    cmd = build_docker_command(
        args.src, args.install, args.script, args.image, uid, gid
    )

    # Print the command for visibility
    print("Running Docker command:")
    print(" ".join(cmd))
    print()

    # Run the command
    result = subprocess.run(cmd)

    # Propagate the exit code
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
