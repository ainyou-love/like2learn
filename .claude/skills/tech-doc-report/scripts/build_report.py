#!/usr/bin/env python3
"""Compose a report page from the shared assets plus one report JSON.

Why a build step for a single output file: the components are the asset, not
the page. A fix to ItemCard belongs in assets/biz.js once, and every report
built afterwards inherits it. Re-emitting 2000 lines of HTML per report throws
that away and makes each report its own unmaintained fork.

    build_report.py --data report.json --out-dir <dir> --slug ai-dev
    build_report.py --data report.json --out path/to/page.html
    build_report.py --from-html page.html --out page.html     # rebuild in place

--from-html pulls the dataset back out of a page that was already built, so a
report can be re-rendered against improved components without the original
JSON still being on disk.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"

# Order matters twice over: CSS cascade, and JS definition-before-use.
CSS_ORDER = ["tokens.css", "base.css", "atoms.css", "biz.css", "layout.css", "print.css"]
JS_ORDER = ["i18n.js", "util.js", "atoms.js", "biz.js",
            "app-state.js", "app-view.js", "app-events.js"]
TOKENS = ("/*__LANG__*/", "/*__LANG__2__*/", "/*__TITLE__*/", "/*__DESC__*/",
          "/*__CSS__*/", "/*__JS__*/", "/*__DATA__*/")


def die(msg: str) -> "None":
    sys.exit("build_report: " + msg)


def extract_data(html: str) -> str:
    m = re.search(r'<script type="application/json" id="report-data">(.*?)</script>',
                  html, re.S)
    if not m:
        die("no embedded report-data block in that HTML")
    # Undo exactly the escape apply_escape() puts in, nothing else.
    return m.group(1).replace(r"<\/", "</").strip()


def apply_escape(raw: str) -> str:
    """`</script` inside a JSON string value ends the block early and the rest
    of the report becomes markup. `\\/` is a legal JSON escape for `/`, and `<`
    cannot appear in JSON outside a string, so this is safe everywhere."""
    return raw.replace("</", r"<\/")


def lang_text(node, lang: str, fallback: str = "") -> str:
    if isinstance(node, str):
        text = node
    elif isinstance(node, dict):
        text = node.get(lang) or next((v for v in node.values() if v), fallback)
    else:
        text = fallback
    # These land in <title> and in a content="" attribute, so they are the two
    # places where researched text becomes markup without passing through the
    # page's own esc(). A quote in a subtitle would otherwise end the attribute.
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def check_markers(html: str) -> list:
    """An @@BEGIN with no @@END, or a marker string that occurs twice, makes
    every later grep-and-replace edit a coin flip. Fail here instead."""
    problems = []
    begins = re.findall(r"@@BEGIN:([A-Za-z0-9_:*.-]+)", html)
    ends = re.findall(r"@@END:([A-Za-z0-9_:*.-]+)", html)
    for name in begins:
        if html.count("@@BEGIN:" + name) != 1:
            problems.append(f"@@BEGIN:{name} appears {html.count('@@BEGIN:' + name)} times")
    for name in set(begins) - set(ends):
        problems.append(f"@@BEGIN:{name} has no @@END")
    for name in set(ends) - set(begins):
        problems.append(f"@@END:{name} has no @@BEGIN")
    return sorted(set(problems))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", help="the report JSON")
    ap.add_argument("--from-html", dest="from_html", help="reuse the JSON embedded in this page")
    ap.add_argument("--out", help="the HTML file to write")
    ap.add_argument("--out-dir", dest="out_dir", help="write into this directory, naming the file by the convention")
    ap.add_argument("--slug", default="", help="the {report-what} part of the filename")
    ap.add_argument("--assets", default=str(ASSETS), help="override the component directory")
    a = ap.parse_args()

    if not a.data and not a.from_html:
        die("give --data or --from-html")
    raw = (extract_data(pathlib.Path(a.from_html).read_text())
           if a.from_html else pathlib.Path(a.data).read_text().strip())
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        die(f"the dataset is not valid JSON: {e}")

    meta = data.get("meta") or {}
    win = meta.get("time_window") or {}
    lang = meta.get("default_language") or "vi"

    adir = pathlib.Path(a.assets).resolve()
    missing = [f for f in CSS_ORDER + JS_ORDER + ["shell.html"] if not (adir / f).exists()]
    if missing:
        die(f"missing component files in {adir}: {', '.join(missing)}")

    css = "\n".join((adir / f).read_text() for f in CSS_ORDER)
    js = "\n".join((adir / f).read_text() for f in JS_ORDER)
    shell = (adir / "shell.html").read_text()

    for name, blob in (("stylesheet", css), ("javascript", js)):
        if "</script" in blob.lower():
            die(f"{name} contains a closing script tag")

    subs = [
        ("/*__LANG__*/", lang),
        ("/*__LANG__2__*/", lang),
        ("/*__TITLE__*/", lang_text(meta.get("title"), lang, "Technical report")),
        ("/*__DESC__*/", lang_text(meta.get("subtitle"), lang, "")),
        ("/*__CSS__*/", css),
        ("/*__JS__*/", js),
        ("/*__DATA__*/", apply_escape(raw)),
    ]
    for token, blob in subs:
        n = shell.count(token)
        if n != 1:
            die(f"token {token} appears {n} times in the shell, expected exactly 1")
        shell = shell.replace(token, blob, 1)
    left = [t for t in TOKENS if t in shell]
    if left:
        die(f"unsubstituted tokens remain: {left}")

    problems = check_markers(shell)
    if problems:
        die("marker problems:\n  " + "\n  ".join(problems))

    if a.out:
        out = pathlib.Path(a.out).resolve()
    else:
        if not a.out_dir:
            die("give --out or --out-dir")
        stamp = (meta.get("generated_at") or "")[:10]
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", stamp):
            die("meta.generated_at must start with YYYY-MM-DD to name the file")
        slug = a.slug or re.sub(r"[^a-z0-9-]+", "-", str(meta.get("report_id", "report")).split("_")[0].lower()).strip("-")
        name = f"{stamp[2:]}--{slug}--{win.get('from', '?')}_{win.get('to', '?')}.html"
        out = (pathlib.Path(a.out_dir) / name).resolve()

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(shell)

    n_items = sum(len(s.get("items") or []) for s in data.get("sections") or [])
    regions = sorted(set(re.findall(r"@@BEGIN:([A-Za-z0-9_:*.-]+)", shell)))
    print(f"built: {out}")
    print(f"  {len(shell.encode()):,} bytes   dataset {len(raw.encode()):,} bytes")
    print(f"  {len(data.get('sections') or [])} sections / {n_items} items / "
          f"{len(data.get('sources') or [])} sources")
    print(f"  {len(regions)} regions, all paired and unique")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
