#!/usr/bin/env python3
"""
Tool to generate disassembler (dasm) tests from assembler (asm) tests.

This tool parses LLVM MC assembler test files and extracts the instruction
encodings to create corresponding disassembler test files.
"""

import argparse
import re
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Generate dasm test from asm test")
    parser.add_argument(
        "input",
        type=Path,
        help="Input asm test file",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        required=True,
        help="Output dasm test file",
    )
    parser.add_argument(
        "--check-prefix",
        type=str,
        default=None,
        help="Check prefix to filter which check line to use when multiple exist",
    )
    return parser.parse_args()


def parse_asm_blocks(content: str) -> list[dict]:
    """
    Parse the ASM file content into blocks.

    Each block contains:
    - instruction: the actual instruction line
    - check_lines: list of check lines (with their prefix and content)
    """
    lines = content.splitlines()
    blocks = []
    current_block = None

    for line in lines:
        stripped = line.strip()

        # Skip empty lines - they separate blocks
        if not stripped:
            if current_block and current_block.get("instruction"):
                blocks.append(current_block)
            current_block = None
            continue

        # Skip RUN lines and NOTE lines at the top
        if stripped.startswith("//") or stripped.startswith("#"):
            comment_content = stripped.lstrip("/#").strip()
            # Check if this is a RUN or NOTE line (header lines)
            if comment_content.startswith("RUN:") or comment_content.startswith(
                "NOTE:"
            ):
                continue

            # Check if this is a check line (e.g., "// GFX1260: ...")
            # Check lines have format: // PREFIX: content
            match = re.match(r"^[/#]+\s*(\w[\w-]*):\s*(.*)$", stripped)
            if match and current_block:
                prefix = match.group(1)
                check_content = match.group(2)
                current_block["check_lines"].append(
                    {
                        "prefix": prefix,
                        "content": check_content,
                        "raw": stripped,
                    }
                )
            continue

        # This is an instruction line
        if current_block is None:
            current_block = {"instruction": stripped, "check_lines": []}
        else:
            # If we already have an instruction, this shouldn't happen
            # but handle it by starting a new block
            if current_block.get("instruction"):
                blocks.append(current_block)
            current_block = {"instruction": stripped, "check_lines": []}

    # Don't forget the last block
    if current_block and current_block.get("instruction"):
        blocks.append(current_block)

    return blocks


def extract_encoding(check_content: str) -> str | None:
    """
    Extract encoding from a check line content.

    Example input: "v_wmma_bf16f32_32x64x32_bf16 v[0:31], ... ; encoding: [0x00,0x00,0x8f,0xcc,0x20,0x61,0x02,0x1f]"
    Example output: "0x00,0x00,0x8f,0xcc,0x20,0x61,0x02,0x1f"
    """
    match = re.search(r";\s*encoding:\s*\[([^\]]+)\]", check_content)
    if match:
        return match.group(1)
    return None


def get_encoding_from_block(block: dict, check_prefix: str | None) -> str:
    """
    Get the encoding from a block's check lines.

    If check_prefix is provided, only use check lines with that prefix.
    If not provided, there must be exactly one check line with encoding.
    """
    check_lines_with_encoding = []

    for check_line in block["check_lines"]:
        encoding = extract_encoding(check_line["content"])
        if encoding:
            check_lines_with_encoding.append(
                {
                    "prefix": check_line["prefix"],
                    "encoding": encoding,
                }
            )

    if not check_lines_with_encoding:
        raise ValueError(f"No encoding found for instruction: {block['instruction']}")

    if check_prefix:
        # Filter by prefix
        matching = [c for c in check_lines_with_encoding if c["prefix"] == check_prefix]
        if not matching:
            raise ValueError(
                f"No check line with prefix '{check_prefix}' found for instruction: {block['instruction']}"
            )
        if len(matching) > 1:
            raise ValueError(
                f"Multiple check lines with prefix '{check_prefix}' have encoding for instruction: {block['instruction']}"
            )
        return matching[0]["encoding"]
    else:
        # No prefix specified - must have exactly one encoding
        if len(check_lines_with_encoding) > 1:
            prefixes = [c["prefix"] for c in check_lines_with_encoding]
            raise ValueError(
                f"Multiple check lines have encoding for instruction: {block['instruction']}. "
                f"Prefixes: {prefixes}. Use --check-prefix to specify which one to use."
            )
        return check_lines_with_encoding[0]["encoding"]


def read_preserved_lines(output_path: Path) -> list[str]:
    """
    Read the output file and return lines that should be preserved.

    Preserved lines are:
    - RUN lines (comment lines containing "RUN:")
    - NOTE lines (comment lines containing "NOTE:")
    - Other header-like comment lines that are not check lines

    We stop preserving once we hit the first non-header line.
    """
    if not output_path.exists():
        return []

    preserved = []
    content = output_path.read_text()
    lines = content.splitlines()

    for line in lines:
        stripped = line.strip()

        # Empty line in header section - preserve it
        if not stripped:
            preserved.append(line)
            continue

        # Check if it's a comment line
        if stripped.startswith("#") or stripped.startswith("//"):
            comment_content = stripped.lstrip("/#").strip()
            # Check if it's a RUN or NOTE line
            if comment_content.startswith("RUN:") or comment_content.startswith(
                "NOTE:"
            ):
                preserved.append(line)
                continue
            # Otherwise it might be a check line or other content - stop preserving
            break
        else:
            # Non-comment line (like encoding bytes) - stop preserving
            break

    return preserved


def main():
    args = parse_args()

    # Read input file
    if not args.input.exists():
        print(f"Error: Input file does not exist: {args.input}", file=sys.stderr)
        sys.exit(1)

    content = args.input.read_text()

    # Parse into blocks
    blocks = parse_asm_blocks(content)

    if not blocks:
        print("Warning: No instruction blocks found in input file", file=sys.stderr)

    # Extract encodings
    encodings = []
    for block in blocks:
        try:
            encoding = get_encoding_from_block(block, args.check_prefix)
            encodings.append(encoding)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Read preserved lines from output file (if exists)
    preserved_lines = read_preserved_lines(args.output)

    # Build output
    output_lines = preserved_lines[:]

    # Ensure there's an empty line between preserved lines and encodings
    if output_lines and output_lines[-1].strip():
        output_lines.append("")

    # Add encodings with empty lines between them
    for i, encoding in enumerate(encodings):
        output_lines.append(encoding)
        if i < len(encodings) - 1:
            output_lines.append("")

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(output_lines) + "\n")

    print(f"Generated {len(encodings)} encoding(s) to {args.output}")


if __name__ == "__main__":
    main()
