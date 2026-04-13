#!/usr/bin/env bash

set -euo pipefail

ROCM_PATH="/opt/rocm"

usage() {
    echo "Usage: $0 [--rocm-path <path>] <tarball>"
    echo ""
    echo "Install a TheRock distribution tarball to the specified ROCm path."
    echo ""
    echo "Options:"
    echo "  --rocm-path <path>  Installation path (default: /opt/rocm)"
    echo "  -h, --help          Show this help message"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --rocm-path)
            ROCM_PATH="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        -*)
            echo "Error: Unknown option '$1'" >&2
            usage
            ;;
        *)
            TARBALL="$1"
            shift
            ;;
    esac
done

if [[ -z "${TARBALL:-}" ]]; then
    echo "Error: No tarball specified." >&2
    usage
fi

if [[ ! -f "$TARBALL" ]]; then
    echo "Error: '$TARBALL' not found." >&2
    exit 1
fi

echo "Installing TheRock to $ROCM_PATH from $TARBALL ..."

mkdir -p "$ROCM_PATH"

if command -v pv &> /dev/null; then
    pv "$TARBALL" | tar -xf - -C "$ROCM_PATH"
else
    tar -xvf "$TARBALL" -C "$ROCM_PATH"
fi

echo "${ROCM_PATH}/lib" > /etc/ld.so.conf.d/rocm.conf
ldconfig

echo "Done."
