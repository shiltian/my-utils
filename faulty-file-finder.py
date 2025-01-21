#!/usr/bin/env python3

import os
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
        file_list = f.readlines()

    for f in file_list:
        logger.info(f"trying file {f}...")
        cmd = [args.build_script, f]
        logger.debug(f"building file {f}")
        subprocess.check_call(cmd)
        cmd = [args.test_script, f]
        r = subprocess.call(cmd)
        if r == 0:
            logger.info(f"file {f} test okay. move on.")
        else:
            logger.info(f"found faulty file {f}")
            return

    logger.info(f"run all files in {args.file_list} but couldn't find faulty file")


if __name__ == "__main__":
    main()
