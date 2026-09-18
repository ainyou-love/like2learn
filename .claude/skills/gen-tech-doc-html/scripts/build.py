#!/usr/bin/env python3
"""Assemble a single-file HTML doc site from its parts.

Why a build step at all, for one output file: the playbook's token-economy rule.
Re-emitting a whole 60 KB document to change one CSS rule is the largest avoidable
cost in this kind of work. Keeping CSS, each script layer and the markdown in
separate files means a change costs one file, and this script costs nothing.

Layout expected in --content:

    style.css          the stylesheet
    src.md             the markdown source        (single-language, the default)
    src-<lang>.md      one per language           (multilingual variant)
    layer1.js          DATA      (STATE, I18N, SRC, FIG)
    layer2*.js         COMPONENTS (parser, figure renderers) -- any number, sorted
    layer3.js          LOGIC
    shell.html         optional; falls back to the skill's assets/shell.html

Usage:
    build.py --content DIR --out FILE.html --title "..." [--desc "..."] [--lang vi]
"""
from __future__ import annotations

import argparse
import pathlib
import sys

TOKENS = ("/*__LANG__*/", "/*__TITLE__*/", "/*__DESC__*/",
          "/*__CSS__*/", "/*__SRC__*/", "/*__JS__*/")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--content", required=True, help="directory holding the parts")
    ap.add_argument("--out", required=True, help="the HTML file to write")
    ap.add_argument("--title", required=True)
    ap.add_argument("--desc", default="")
    ap.add_argument("--lang", default="vi")
    ap.add_argument("--shell", default="", help="override the shell template")
    a = ap.parse_args()

    c = pathlib.Path(a.content).resolve()
    if not c.is_dir():
        sys.exit(f"build: --content is not a directory: {c}")

    css_f = c / "style.css"
    if not css_f.exists():
        sys.exit(f"build: missing {css_f}")
    css = css_f.read_text()

    # markdown: one src.md, or several src-<lang>.md rendered into one tag each
    singles = sorted(c.glob("src-*.md"))
    if (c / "src.md").exists():
        srcs = [("src", (c / "src.md").read_text())]
    elif singles:
        srcs = [(f.stem, f.read_text()) for f in singles]   # src-vi -> id "src-vi"
    else:
        sys.exit(f"build: no src.md or src-<lang>.md in {c}")

    layers = [p for p in sorted(c.glob("layer*.js"))]
    if not layers:
        sys.exit(f"build: no layer*.js in {c}")
    js = "\n\n".join(p.read_text() for p in layers)

    # A text/plain block needs no escaping, but it must not close the script early.
    for name, blob in [("javascript", js)] + [(f"markdown {i}", s) for i, s in srcs]:
        if "</script" in blob.lower():
            sys.exit(f"build: {name} contains a closing script tag")

    shell_f = pathlib.Path(a.shell) if a.shell else (
        c / "shell.html" if (c / "shell.html").exists()
        else pathlib.Path(__file__).resolve().parent.parent / "assets" / "shell.html")
    shell = shell_f.read_text()

    src_block = "\n".join(
        f'<script type="text/plain" id="{i}">{s}</script>' for i, s in srcs)
    # the shell already wraps __SRC__ in one script tag; with several sources we
    # replace that whole tag instead of nesting tags inside it
    if len(srcs) > 1:
        one = '<script type="text/plain" id="src">/*__SRC__*/</script>'
        if shell.count(one) != 1:
            sys.exit("build: cannot place multilingual sources -- shell tag not found")
        shell = shell.replace(one, src_block, 1)
        subs = [("/*__LANG__*/", a.lang), ("/*__TITLE__*/", a.title),
                ("/*__DESC__*/", a.desc), ("/*__CSS__*/", css), ("/*__JS__*/", js)]
    else:
        subs = [("/*__LANG__*/", a.lang), ("/*__TITLE__*/", a.title),
                ("/*__DESC__*/", a.desc), ("/*__CSS__*/", css),
                ("/*__SRC__*/", srcs[0][1]), ("/*__JS__*/", js)]

    for token, blob in subs:
        # An anchor that matches twice silently corrupts the file; one that matches
        # zero times fails loudly, which is what we want.
        if shell.count(token) != 1:
            sys.exit(f"build: token {token} appears {shell.count(token)} times, expected 1")
        shell = shell.replace(token, blob, 1)

    left = [t for t in TOKENS if t in shell]
    if left:
        sys.exit(f"build: unsubstituted tokens remain: {left}")

    out = pathlib.Path(a.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(shell)

    print(f"built: {out}")
    print(f"  {len(shell):,} chars / {len(shell.encode()):,} bytes")
    print(f"  markdown: {', '.join(i + ' ' + str(len(s.splitlines())) + 'L' for i, s in srcs)}")
    print(f"  layers:   {', '.join(p.name for p in layers)} ({len(js.splitlines())}L)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
