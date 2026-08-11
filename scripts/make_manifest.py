#!/usr/bin/env python3
"""Generate MANIFEST.sha256 covering every published artifact."""
from __future__ import annotations
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", ".ipynb_checkpoints"}
SKIP_FILES = {"MANIFEST.sha256"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    entries = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in SKIP_FILES:
            continue
        entries.append((sha256_file(path), path.relative_to(ROOT).as_posix()))

    out = ROOT / "MANIFEST.sha256"
    out.write_text(
        "".join(f"{digest}  {name}\n" for digest, name in entries),
        encoding="utf-8",
    )
    print(f"wrote {out.name} covering {len(entries)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
