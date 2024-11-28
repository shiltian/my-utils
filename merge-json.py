#!/usr/bin/env python3

import argparse
import json
import sys


def merge_compile_commands(input_files):
    """
    Merge multiple compile_commands.json files.

    Args:
        input_files (list): List of paths to compile_commands.json files

    Returns:
        list: A merged list of compilation command objects
    """
    merged_commands = []

    for file_path in input_files:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

                # Ensure the input is a list (typical for compile_commands.json)
                if not isinstance(data, list):
                    print(
                        f"Warning: {file_path} does not contain a list of compilation commands.",
                        file=sys.stderr,
                    )
                    continue

                # Extend the merged commands list
                merged_commands.extend(data)

        except json.JSONDecodeError:
            print(
                f"Error: Invalid JSON in {file_path}. Skipping this file.",
                file=sys.stderr,
            )
        except FileNotFoundError:
            print(f"Error: File not found - {file_path}. Skipping.", file=sys.stderr)
        except PermissionError:
            print(
                f"Error: Permission denied when reading {file_path}. Skipping.",
                file=sys.stderr,
            )

    return merged_commands


def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="Merge multiple compile_commands.json files."
    )
    parser.add_argument(
        "input_files", nargs="+", help="Input compile_commands.json files to merge"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="compile_commands.json",
        help="Output JSON file name (default: compile_commands.json)",
    )

    # Parse arguments
    args = parser.parse_args()

    # Merge compilation command files
    merged_data = merge_compile_commands(args.input_files)

    # Write merged data to output file
    try:
        with open(args.output, "w", encoding="utf-8") as outfile:
            json.dump(merged_data, outfile, indent=2)
        print(f"Successfully merged {len(args.input_files)} files into {args.output}")

    except PermissionError:
        print(
            f"Error: Permission denied when writing to {args.output}", file=sys.stderr
        )
    except IOError as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
