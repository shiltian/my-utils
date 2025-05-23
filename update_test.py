#!/usr/bin/env python3

import argparse
import os
import subprocess
import logging
import sys

prog = "update-test"

logger = logging.getLogger(prog)


def run_update(llvm_root, updater, file_path, verbose=False):
    updater = os.path.join(os.path.join(llvm_root, "llvm", "utils"), updater)
    out = open(os.devnull, "w") if not verbose else sys.stderr
    subprocess.check_call([updater, file_path], stderr=out, stdout=out)


def main():
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Update LLVM test if the test is generated by script.",
    )

    parser.add_argument(
        "-l",
        "--llvm-src-root",
        required=True,
        help="LLVM source code root",
    )
    parser.add_argument(
        "-f",
        "--test-file",
        required=True,
        help="A list of tests to be updated",
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

    test_file = os.path.realpath(args.test_file)
    llvm_src_root = os.path.realpath(args.llvm_src_root)

    def run_update_wrapper(updater, test_kind, file_path):
        logger.debug(f"test {file_path} is a {test_kind} test. updating...")
        run_update(llvm_src_root, updater, file_path, verbose=args.verbose)
        logger.debug(f"test {file_path} updated.")

    with open(test_file, "r") as f:
        test_list = f.readlines()

    for t in test_list:
        t = t.strip()
        # skip empty line
        if len(t) == 0:
            continue
        if not os.path.isabs(t):
            t = os.path.join(os.path.join(llvm_src_root, "llvm", "test"), t)
        logger.debug(f"processing {t}...")
        with open(t, "r") as f:
            first_line = f.readline()
        if "autogenerated" not in first_line:
            logger.warning(f"test {t} was not auto generated. skipped...")
            continue
        if "update_llc_test_checks.py" in first_line:
            run_update_wrapper("update_llc_test_checks.py", "llc", t)
        elif "update_mir_test_checks.py" in first_line:
            run_update_wrapper("update_mir_test_checks.py", "mir", t)
        elif "update_test_checks.py" in first_line:
            run_update_wrapper("update_test_checks.py", "opt", t)
        elif "update_mc_test_checks.py" in first_line:
            run_update_wrapper("update_mc_test_checks.py", "llvm-mc", t)
        else:
            assert 0, f"unknown test updater {first_line} for test {t}"


if __name__ == "__main__":
    main()
