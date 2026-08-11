#!/usr/bin/env python3
"""Check that repository-relative Markdown links point to existing files."""

from __future__ import annotations

import re
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def main() -> int:
    problems = []
    checked = 0
    for document in sorted(ROOT.rglob("*.md")):
        if ".git" in document.parts:
            continue
        text = document.read_text(encoding="utf-8")
        for raw in LINK.findall(text):
            target = raw.strip().split(maxsplit=1)[0].strip("<>")
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path_text = urllib.parse.unquote(target.split("#", 1)[0])
            if not path_text:
                continue
            checked += 1
            destination = (document.parent / path_text).resolve()
            if not destination.exists():
                problems.append(
                    f"{document.relative_to(ROOT)} -> {target} (missing)"
                )
    if problems:
        print("BROKEN LOCAL MARKDOWN LINKS")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"checked {checked} local Markdown links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
