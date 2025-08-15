#!/usr/bin/env python3

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Set up logger
logger = logging.getLogger(os.path.basename(__file__))


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def find_compile_commands_files(directory: Path) -> List[Path]:
    """
    Recursively find all compile_commands.json files in the given directory.

    Args:
        directory: The root directory to search in

    Returns:
        List of Path objects pointing to compile_commands.json files
    """
    compile_commands_files = []

    for root, dirs, files in os.walk(directory):
        if "compile_commands.json" in files:
            compile_commands_files.append(Path(root) / "compile_commands.json")

    return compile_commands_files


def load_compile_commands(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load and parse a compile_commands.json file.

    Args:
        file_path: Path to the compile_commands.json file

    Returns:
        List of compilation database entries
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                logger.warning(f"{file_path} does not contain a JSON array")
                return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing {file_path}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return []


def merge_compile_commands(directory: Path) -> List[Dict[str, Any]]:
    """
    Merge all compile_commands.json files found in the directory tree.

    Args:
        directory: The root directory to search in

    Returns:
        Merged list of compilation database entries
    """
    compile_commands_files = find_compile_commands_files(directory)

    if not compile_commands_files:
        logger.error(f"No compile_commands.json files found in {directory}")
        return []

    logger.info(f"Found {len(compile_commands_files)} compile_commands.json files:")
    for file_path in compile_commands_files:
        logger.info(f"  - {file_path}")

    merged_commands = []
    seen_entries = set()

    for file_path in compile_commands_files:
        commands = load_compile_commands(file_path)
        logger.debug(f"Loaded {len(commands)} entries from {file_path}")

        for command in commands:
            # Create a unique identifier for each entry to avoid duplicates
            # Use file path and command as the key
            if "file" in command and "command" in command:
                # Normalize the file path to handle different representations
                file_key = os.path.normpath(command["file"])
                entry_key = (file_key, command["command"])

                if entry_key not in seen_entries:
                    seen_entries.add(entry_key)
                    merged_commands.append(command)
                else:
                    logger.debug(f"Skipping duplicate entry for {command['file']}")
            else:
                # If the entry doesn't have required fields, include it anyway
                logger.warning(f"Entry missing 'file' or 'command' field: {command}")
                merged_commands.append(command)

    logger.info(f"Merged {len(merged_commands)} unique compilation entries")
    return merged_commands


def save_compile_commands(commands: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the merged compile commands to a JSON file.

    Args:
        commands: List of compilation database entries
        output_path: Path where to save the merged file
    """
    try:
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created output directory: {output_path.parent}")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(commands, f, indent=2, ensure_ascii=False)

        logger.info(f"Merged compile_commands.json saved to: {output_path}")
    except Exception as e:
        logger.error(f"Error saving to {output_path}: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Merge all compile_commands.json files from a directory tree",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -d /path/to/project -o merged_compile_commands.json
  %(prog)s --dir . --output ./build/compile_commands.json
  %(prog)s -d . -o merged.json --verbose
        """,
    )

    parser.add_argument(
        "-d",
        "--dir",
        type=str,
        required=True,
        help="Directory to search for compile_commands.json files",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Output path for the merged compile_commands.json file",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)",
    )

    args = parser.parse_args()

    # Set up logging
    setup_logging(args.verbose)

    # Convert to Path objects and validate
    input_dir = Path(args.dir).resolve()
    output_path = Path(args.output).resolve()

    logger.debug(f"Input directory: {input_dir}")
    logger.debug(f"Output path: {output_path}")

    if not input_dir.exists():
        logger.error(f"Directory {input_dir} does not exist")
        sys.exit(1)

    if not input_dir.is_dir():
        logger.error(f"{input_dir} is not a directory")
        sys.exit(1)

    # Merge compile commands
    merged_commands = merge_compile_commands(input_dir)

    if not merged_commands:
        logger.error("No compilation entries to merge")
        sys.exit(1)

    # Save merged file
    save_compile_commands(merged_commands, output_path)
    logger.info("Merge operation completed successfully")


if __name__ == "__main__":
    main()
