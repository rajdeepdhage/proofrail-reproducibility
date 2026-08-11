#!/usr/bin/env python3
"""
Guard against Windows line endings in tracked text files.

Why this matters here: .gitattributes normalizes text files to LF, so a file
committed with CRLF is checked out with different bytes than it had on disk.
Its SHA-256 then no longer matches MANIFEST.sha256, and the integrity check
fails on a clean machine while passing locally -- a confusing failure whose
cause is invisible in the diff.

This is easy to reintroduce, because several tools (Python's csv writer, and
some KNIME exports) emit CRLF by default. Run this before regenerating the
manifest.

Usage:
    python scripts/check_line_endings.py          # report
    python scripts/check_line_endings.py --fix    # convert to LF in place

Exit codes: 0 = clean (or fixed), 1 = CRLF found and not fixed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", ".ipynb_checkpoints"}
# Declared binary in .gitattributes: Git leaves these bytes alone.
BINARY_SUFFIXES = {".db", ".png", ".jpg", ".jpeg", ".zip", ".pdf"}


def tracked_text_files():
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in BINARY_SUFFIXES:
            continue
        yield path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fix", action="store_true",
                    help="rewrite offending files with LF endings")
    args = ap.parse_args()

    offenders = []
    for path in tracked_text_files():
        try:
            data = path.read_bytes()
        except OSError:
            continue
        count = data.count(b"\r\n")
        if count:
            offenders.append((path, count))
            if args.fix:
                path.write_bytes(data.replace(b"\r\n", b"\n"))

    rel = lambda p: p.relative_to(ROOT).as_posix()
    if not offenders:
        print("line endings: OK — no CRLF in tracked text files")
        return 0

    if args.fix:
        for path, count in offenders:
            print(f"  fixed {rel(path)} ({count} lines)")
        print(f"converted {len(offenders)} file(s) to LF")
        print("now run: python3 scripts/make_manifest.py")
        return 0

    print("line endings: CRLF found in tracked text files")
    for path, count in offenders:
        print(f"  {rel(path)} ({count} lines)")
    print("\nThese will be normalized by Git on checkout, so their recorded")
    print("hashes will not match on a clean machine. Fix with:")
    print("  python3 scripts/check_line_endings.py --fix")
    return 1


if __name__ == "__main__":
    sys.exit(main())
