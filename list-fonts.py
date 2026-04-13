#!/usr/bin/env python3
"""List font family names found under a directory, with optional fixed-width filtering."""

import argparse
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

FONT_EXTENSIONS = {".ttf", ".otf", ".ttc", ".otc"}
NERD_FONT_VARIANT_SUFFIXES = (" Nerd Font Mono", " Nerd Font Propo")


def is_fixed_width(font):
    """Determine whether a font is fixed-width (monospaced).

    Checks the post table's isFixedPitch flag and the OS/2 table's Panose
    proportion field (value 9 = monospaced).  Returns True if either
    indicator says monospaced.
    """
    try:
        if font["post"].isFixedPitch:
            return True
    except (KeyError, AttributeError):
        pass
    try:
        panose = font["OS/2"].panose
        if panose.bProportion == 9:
            return True
    except (KeyError, AttributeError):
        pass
    return False


def get_family_name(font):
    """Extract the typographic family name from the name table.

    Prefers nameID 16 (Typographic Family) and falls back to nameID 1 (Family).
    """
    name_table = font.get("name")
    if name_table is None:
        return None
    for name_id in (16, 1):
        rec = name_table.getName(name_id, 3, 1, 0x0409)
        if rec:
            return str(rec)
        rec = name_table.getName(name_id, 1, 0, 0)
        if rec:
            return str(rec)
    return None


def normalize_family_name(family):
    """Collapse Nerd Font Mono/Propo variants into the base family name."""
    for suffix in NERD_FONT_VARIANT_SUFFIXES:
        if family.endswith(suffix):
            return family[: -len(suffix)] + " Nerd Font"
    return family


def scan_fonts(directory, fixed_width_only=False, recursive=True):
    """Walk *directory* and yield (family_name, is_mono, path) for every font found."""
    root = Path(directory)
    if not root.is_dir():
        print(f"Error: '{directory}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    glob = root.rglob("*") if recursive else root.glob("*")
    for path in sorted(glob):
        if path.suffix.lower() not in FONT_EXTENSIONS:
            continue
        try:
            font = TTFont(path, fontNumber=0)
        except Exception:
            continue
        family = get_family_name(font)
        if family is None:
            continue
        mono = is_fixed_width(font)
        font.close()
        if fixed_width_only and not mono:
            continue
        yield family, mono, path


def main():
    parser = argparse.ArgumentParser(
        description="List font family names under a directory."
    )
    parser.add_argument("directory", help="Root directory to scan")
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Scan subdirectories recursively",
    )
    parser.add_argument(
        "--fixed-width",
        "-fw",
        action="store_true",
        help="Only show fixed-width (monospace) fonts",
    )
    parser.add_argument(
        "--show-paths",
        "-p",
        action="store_true",
        help="Show the file path for each font",
    )
    parser.add_argument(
        "--normalize-nerd-variants",
        action="store_true",
        help="Merge 'Nerd Font Mono/Propo' families into the base 'Nerd Font' name",
    )
    args = parser.parse_args()

    seen_families = {}
    for family, mono, path in scan_fonts(
        args.directory, args.fixed_width, args.recursive
    ):
        normalized_family = (
            normalize_family_name(family) if args.normalize_nerd_variants else family
        )
        if normalized_family not in seen_families:
            seen_families[normalized_family] = {"mono": False, "paths": []}
        seen_families[normalized_family]["mono"] = (
            seen_families[normalized_family]["mono"] or mono
        )
        seen_families[normalized_family]["paths"].append(path)

    if not seen_families:
        label = "fixed-width fonts" if args.fixed_width else "fonts"
        print(f"No {label} found under '{args.directory}'.")
        return

    tag_width = 6
    for family in sorted(seen_families):
        mono = seen_families[family]["mono"]
        paths = seen_families[family]["paths"]
        tag = "[mono]" if mono else ""
        line = f"  {tag:<{tag_width}}  {family}"
        if args.show_paths:
            line += f"  ({len(paths)} file{'s' if len(paths) != 1 else ''})"
            for p in paths:
                line += f"\n{'':>{tag_width + 10}}{p}"
        print(line)

    total = len(seen_families)
    mono_count = sum(1 for family in seen_families.values() if family["mono"])
    print(f"\n{total} families ({mono_count} monospace)")


if __name__ == "__main__":
    main()
