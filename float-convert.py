#!/usr/bin/env python3
"""
Floating Point Format Converter

This script converts decimal floating point numbers to hexadecimal format with power-of-2 exponent.
Example: -0.0014473809 -> -0x1.7b6c16p-10
"""

import sys
import argparse


def float_to_hex(value):
    """
    Convert a floating point value to hexadecimal format with power-of-2 exponent.

    Args:
        value (float): The floating point value to convert

    Returns:
        str: Hexadecimal representation with power-of-2 exponent
    """
    if value == 0:
        return "0x0p+0"

    # Handle sign
    sign = "-" if value < 0 else ""
    abs_value = abs(value)

    # Find the exponent
    exponent = 0
    normalized = abs_value

    if abs_value >= 1:
        while normalized >= 2:
            normalized /= 2
            exponent += 1
    else:
        while normalized < 1:
            normalized *= 2
            exponent -= 1

    # Convert the normalized value to hex
    # Multiply by 2^24 to get 24 bits of precision
    int_part = int(normalized * (1 << 24))
    hex_digits = format(int_part, "x")

    # Format with the first digit before the decimal point
    first_digit = hex_digits[0]
    rest_digits = hex_digits[1:].rstrip("0")

    # Determine the exponent sign
    exp_sign = "+" if exponent >= 0 else "-"
    abs_exp = abs(exponent)

    # Construct the result
    if rest_digits:
        return f"{sign}0x{first_digit}.{rest_digits}p{exp_sign}{abs_exp}"
    else:
        return f"{sign}0x{first_digit}p{exp_sign}{abs_exp}"


def main():
    """Parse command line arguments and convert each floating point number."""
    parser = argparse.ArgumentParser(
        description="Convert decimal floating point numbers to hexadecimal format with power-of-2 exponent."
    )
    parser.add_argument(
        "numbers",
        metavar="NUMBER",
        type=float,
        nargs="+",
        help="one or more floating point numbers to convert",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="display both original and converted values",
    )

    args = parser.parse_args()

    for value in args.numbers:
        try:
            hex_representation = float_to_hex(value)
            if args.verbose:
                print(f"{value} -> {hex_representation}")
            else:
                print(f"{hex_representation}")
        except Exception as e:
            print(f"Error converting {value}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
