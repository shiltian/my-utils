#!/usr/bin/env python3

import argparse
import subprocess
import logging
import os

prog = "opt-bisect-runner"

logger = logging.getLogger(prog)


def main():
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Find the first faulty optimization pass via -opt-bisect-limit.",
    )

    parser.add_argument(
        "-b",
        "--build-script",
        required=True,
        help="a script to build",
    )
    parser.add_argument(
        "-t",
        "--test-script",
        required=True,
        help="a script to test",
    )
    parser.add_argument("-l", "--lower", type=int, default=0, help="lower bound")
    parser.add_argument("-u", "--upper", type=int, default=1024, help="upper bound")
    parser.add_argument("-r", "--repeat", type=int, default=1, help="times to run the test script")
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

    build_script = os.path.realpath(args.build_script)
    test_script = os.path.realpath(args.test_script)

    lo = args.lower
    hi = args.upper
    repeat = args.repeat
    last_fail = False


    while lo < hi:
        cur = (lo + hi) // 2
        build_cmd = [build_script, f"{cur}"]

        logger.info(f"lo={lo}, hi={hi}, cur={cur}")

        logger.debug(f"build cmd: {" ".join(build_cmd)}")

        logger.info("building...")

        subprocess.check_call(build_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        for t in range(0, repeat):
            logger.info(f"testing...[{t + 1}/{repeat}]")
            r = subprocess.call([test_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            last_fail = r != 0
            if last_fail:
                break

        if last_fail:
            logger.info(f"cur={cur} fails")
            hi = cur
        else:
            logger.info(f"cur={cur} succeeds")
            lo = cur + 1

    logger.info(f"faulty={hi if last_fail else lo}")


if __name__ == "__main__":
    main()
