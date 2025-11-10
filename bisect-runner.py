#!/usr/bin/env python3
import subprocess
import sys
import argparse
import os


def run_script(script_path, test_value, extra_args=None):
    """
    Run a script and return True if it succeeds (exit code 0), False otherwise.
    """
    if extra_args is None:
        extra_args = []

    try:
        # Make the script executable if it's not already
        if os.path.isfile(script_path):
            os.chmod(script_path, 0o755)

        # Run the script with test value as first argument, followed by extra args
        cmd = [script_path, str(test_value)] + extra_args
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300
        )  # 5 minute timeout

        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"Script timed out after 300 seconds")
        return False
    except Exception as e:
        print(f"Error running script: {e}")
        return False


def find_upper_bound(lower_bound, script_path, extra_args=None, verbose=False):
    """
    Find an upper bound by starting from lower_bound and doubling until the script fails.

    Args:
        lower_bound: Starting point for the search
        script_path: Path to the script to execute
        extra_args: Additional arguments to pass to the script
        verbose: Whether to print detailed output

    Returns:
        tuple: (updated_lower_bound, upper_bound) where script succeeds at updated_lower_bound
               and fails at upper_bound
    """
    if extra_args is None:
        extra_args = []

    print(f"Finding upper bound starting from {lower_bound}")

    current = lower_bound
    last_success = None

    while True:
        if verbose:
            print(f"Testing value: {current}")

        success = run_script(script_path, current, extra_args)

        if success:
            if verbose:
                print(f"✓ Script succeeded with value {current}")
            last_success = current
            current *= 2
        else:
            if verbose:
                print(f"✗ Script failed with value {current}")
            # Found our upper bound
            if last_success is None:
                # The script failed even at the starting point
                print(f"Error: Script fails at starting value {lower_bound}")
                sys.exit(1)
            print(f"Upper bound found at: {current}")
            return last_success, current


def binary_search(
    lower_bound, upper_bound, script_path, extra_args=None, verbose=False
):
    """
    Perform binary search between lower_bound and upper_bound.

    Args:
        lower_bound: Lower bound of search range
        upper_bound: Upper bound of search range
        script_path: Path to the script to execute
        extra_args: Additional arguments to pass to the script
        verbose: Whether to print detailed output

    Returns:
        The boundary value where the script behavior changes
    """
    if extra_args is None:
        extra_args = []

    left = lower_bound
    right = upper_bound

    print(f"Starting binary search between {left} and {right}")
    print(f"Script: {script_path}")
    if extra_args:
        print(f"Extra args: {' '.join(extra_args)}")
    print("-" * 50)

    while left < right:
        mid = (left + right) // 2

        if verbose:
            print(f"Testing value: {mid} (range: {left}-{right})")

        # Pass the current value as the first argument to the script
        success = run_script(script_path, mid, extra_args)

        if success:
            if verbose:
                print(f"✓ Script succeeded with value {mid}")
            # Script succeeded, search in the upper half
            left = mid + 1
        else:
            if verbose:
                print(f"✗ Script failed with value {mid}")
            # Script failed, search in the lower half
            right = mid

    return left


def main():
    parser = argparse.ArgumentParser(
        description="Binary search tool that finds the boundary where a script's behavior changes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -l 1 -u 100 -t ./test_script.sh
  %(prog)s --lower 0 --upper 1000 --test ./my_test.py --verbose
  %(prog)s -l 1 -t ./check.sh  # Auto-discover upper bound
  %(prog)s -l 1 -u 50 -t ./check.sh -- --flag value --config test.conf
        """,
    )

    parser.add_argument(
        "-l", "--lower", type=int, required=True, help="Lower bound of the search range"
    )
    parser.add_argument(
        "-u",
        "--upper",
        type=int,
        help="Upper bound of the search range (optional - will auto-discover if not provided)",
    )
    parser.add_argument(
        "-t",
        "--test",
        type=str,
        required=True,
        help="Path to the test script to execute",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    # Parse known args to handle the -- separator
    args, extra_args = parser.parse_known_args()

    # Remove the -- separator if it exists
    if extra_args and extra_args[0] == "--":
        extra_args = extra_args[1:]

    # Validate bounds if upper is provided
    if args.upper is not None and args.lower >= args.upper:
        print("Error: Lower bound must be less than upper bound")
        sys.exit(1)

    # Check if script exists
    if not os.path.isfile(args.test):
        print(f"Error: Script '{args.test}' not found")
        sys.exit(1)

    try:
        # If upper bound is not provided, find it automatically
        if args.upper is None:
            lower_bound, upper_bound = find_upper_bound(
                args.lower, args.test, extra_args, args.verbose
            )
            print("-" * 50)
        else:
            lower_bound = args.lower
            upper_bound = args.upper

        result = binary_search(
            lower_bound, upper_bound, args.test, extra_args, args.verbose
        )

        print("-" * 50)
        print(f"Binary search completed!")
        print(f"Boundary found at: {result}")
        print(f"Script succeeds for values < {result}")
        print(f"Script fails for values >= {result}")

    except KeyboardInterrupt:
        print("\nSearch interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during binary search: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
