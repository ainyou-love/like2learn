#!/usr/bin/env python3
"""Report quoted phrases in the step-1 notes that don't appear in the raw script.

Usage: python3 check_quotes.py <notes.md> <raw.txt>

Captions break lines mid-sentence, so both sides are compared with whitespace
collapsed and punctuation/case ignored. A quote shortened with "…" or "..." is
checked fragment by fragment.
"""
import re
import sys
import unicodedata
from pathlib import Path


def norm(text):
    text = unicodedata.normalize("NFC", text).lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def main():
    notes = Path(sys.argv[1]).read_text(encoding="utf-8")
    raw = norm(Path(sys.argv[2]).read_text(encoding="utf-8"))
    quotes = re.findall(r"[\"“]([^\"”]{6,})[\"”]", notes)
    missing = []
    for q in quotes:
        fragments = [f for f in re.split(r"…|\.\.\.", q) if len(norm(f).split()) >= 3]
        if any(norm(f) not in raw for f in fragments):
            missing.append(q)
    print(f"{len(quotes)} quoted phrases, {len(quotes) - len(missing)} found verbatim in script")
    for q in missing:
        print(f"NOT VERBATIM: \"{q}\"")


if __name__ == "__main__":
    main()
