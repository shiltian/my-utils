#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys

DEFAULT_IMAGE = (
    "compute-artifactory.amd.com:5000/rocm-base-images/ubuntu-24.04-bld:latest"
)


def main():
    parser = argparse.ArgumentParser(
        description="Run a Docker container with ROCm development setup",
        epilog="All other arguments are passed directly to docker run.",
    )
    parser.add_argument(
        "-i",
        "--image",
        default=DEFAULT_IMAGE,
        help=f"Docker image to use (default: {DEFAULT_IMAGE})",
    )

    # Parse known args, rest go to docker
    args, docker_args = parser.parse_known_args()

    # Validate BUILD_ROOT
    build_root = os.environ.get("BUILD_ROOT")
    if not build_root:
        print("Error: BUILD_ROOT environment variable is not set", file=sys.stderr)
        sys.exit(1)

    # Build docker command
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
        "-v",
        "/home/shiltian/Documents/docker:/root",
        "-v",
        f"{build_root}/lightning-llvm/release/:/llvm",
        *docker_args,
        args.image,
        "bash",
        "-c",
        "apt-get update && apt-get install -y zsh vim cmake ninja-build && exec zsh",
    ]

    # Execute docker
    os.execvp("docker", cmd)


if __name__ == "__main__":
    main()
