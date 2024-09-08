#!/usr/bin/env python3

import argparse
import subprocess
import pathlib
import logging

logger = logging.getLogger("faulty-file-finder")


def main():
    parser = argparse.ArgumentParser(
        prog="faulty-file-finder.py",
        description="Find the first faulty file that causes test failure.",
    )

    parser.add_argument(
        "-b",
        "--build-script",
        type=pathlib.Path,
        required=True,
        help="a script to build",
    )
    parser.add_argument(
        "-f",
        "--file-list",
        type=pathlib.Path,
        required=True,
        help="a list of files to check",
    )
    parser.add_argument(
        "-t",
        "--test-script",
        type=pathlib.Path,
        required=True,
        help="a script to test",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="verbose mode",
    )


    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    with open(args.file_list, "r") as f:
        file_list = f.readlines();


if __name__ == "__main__":
    main()
