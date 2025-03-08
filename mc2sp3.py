#!/usr/bin/env python3

import argparse


def convert_bytes_to_32bit(hex_values):
    """
    Convert a comma-separated string of hex bytes to 32-bit words in SP3 format.

    Args:
        hex_values (str): Comma-separated hexadecimal values from llvm-mc (e.g. "0x1a,0x2b,0x3c,0x4d")

    Returns:
        str: Space-separated 32-bit values in SP3 hexadecimal format

    Raises:
        ValueError: If the input length is not a multiple of 4 bytes
    """
    # Strip any whitespace and handle '0x' prefix if present
    clean_values = hex_values.replace(" ", "")
    clean_values = clean_values.replace("[", "")
    clean_values = clean_values.replace("]", "")

    # Convert input string to a list of integers
    try:
        bytes_list = [int(x, 16) for x in clean_values.split(",")]
    except ValueError:
        raise ValueError("Invalid hexadecimal value in input")

    # Ensure the input length is a multiple of 4
    if len(bytes_list) % 4 != 0:
        raise ValueError(
            "Input length must be a multiple of 4 bytes (32 bits per number)"
        )

    # Process in chunks of 4 bytes (32-bit numbers)
    result = []
    for i in range(0, len(bytes_list), 4):
        # Combine 4 bytes into a 32-bit word (little-endian)
        num = (
            bytes_list[i]
            | (bytes_list[i + 1] << 8)
            | (bytes_list[i + 2] << 16)
            | (bytes_list[i + 3] << 24)
        )
        result.append(f"0x{num:08x}")

    return " ".join(result)


def main():
    parser = argparse.ArgumentParser(
        prog="mc2sp3.py",
        description="Convert instruction encoding by llvm-mc to the SP3 format",
    )
    parser.add_argument(
        "input",
        nargs="+",
        help="Comma-separated hexadecimal byte encodings from llvm-mc",
    )

    args = parser.parse_args()

    for v in args.input:
        try:
            print(convert_bytes_to_32bit(v))
        except ValueError as e:
            print(f"Error processing '{v}': {e}")


if __name__ == "__main__":
    main()
