#!/usr/bin/env python3
"""Assemble a technical single-file HTML report.

    python3 build.py --body body.html --md src.md --out report.html \
        --title "Order alerts review" --brand "Order alerts · Design review" \
        --date 2026-10-13 [--desc "..."] [--lang en] [--md-filename report.md] \
        [--storage-key orders-review] [--sidebar-note note.html] \
        [--ui-lang vi] [--code ddl=schema.sql ...] [--ban OLTP,OLAP] [--strict-paths]

Inputs
  --body   HTML fragment for the Report tab: hero, sections, footer. Sections use
           <section class="sec" id="..."> with a .sec-head (number + h2). The table of
           contents is generated from them; override a label with data-toc-label and a
           number with data-toc-no (e.g. on the checklist and "start here" sections).
           data-toc-group="Part 1 · ..." puts a group heading above that section's entry.
  --md     the Markdown source of truth; embedded raw for the Markdown tab.
  --code   name=path, repeatable: replaces __CODE:name__ in the body with the
           HTML-escaped file content (for appendix SQL / code boxes).

The script never edits its inputs. It refuses to write when a check fails.
"""

import argparse
import html
import json
import pathlib
import re
import sys

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
SHELL = SKILL_DIR / "assets" / "shell.html"
UI_STRINGS = SKILL_DIR / "assets" / "ui-strings.json"
ONCE = ["__LANG__", "__TITLE__", "__DESC__", "__BRAND__", "__DATE__", "__TOC__",
        "__SIDEBAR_NOTE__", "__BODY__", "__MD_SOURCE__"]
MANY = ["__MD_FILENAME__", "__STORAGE_KEY__"]


def fail(msg: str) -> None:
    sys.exit(f"build: {msg}")


def strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s).strip()


def build_toc(body: str) -> tuple[str, int]:
    items = []
    for m in re.finditer(r'<section\b([^>]*)>(.*?)(?=<section\b|\Z)', body, re.S):
        attrs, inner = m.group(1), m.group(2)
        sid = re.search(r'\bid="([^"]+)"', attrs)
        if not sid or 'class="sec' not in attrs:
            continue
        label = re.search(r'data-toc-label="([^"]+)"', attrs)
        group = re.search(r'data-toc-group="([^"]+)"', attrs)
        if group:
            items.append(f'      <li class="grp">{html.escape(html.unescape(group.group(1)), quote=False)}</li>')
        no = re.search(r'data-toc-no="([^"]+)"', attrs)
        if not label:
            h2 = re.search(r"<h2[^>]*>(.*?)</h2>", inner, re.S)
            label_text = html.unescape(strip_tags(h2.group(1))) if h2 else sid.group(1)
        else:
            label_text = html.unescape(label.group(1))
        if not no:
            sec_no = re.search(r'<span class="sec-no">([^<]+)</span>', inner)
            no_text = html.unescape(sec_no.group(1)) if sec_no else "·"
        else:
            no_text = html.unescape(no.group(1))
        items.append(f'      <li><a href="#{sid.group(1)}" data-action="nav"><span>{html.escape(no_text)}</span>'
                     f"{html.escape(label_text, quote=False)}</a></li>")
    return "\n".join(items), sum('class="grp"' not in i for i in items)


def check(out: str, md: str, bans: list[str], strict_paths: bool) -> list[str]:
    problems = []
    own = "|".join(t.strip("_") for t in ONCE + MANY)
    before, _, rest = out.partition('id="md-source">')
    outside_md = before + rest.partition("</script>")[2]
    left = sorted(set(re.findall(rf"__(?:{own}|UI:[a-z0-9_]+|CODE:[a-z0-9_-]+)__", outside_md)))
    if left:
        problems.append(f"unreplaced placeholders: {left}")
    if "__UI:" in md:
        problems.append("a __UI:key__ token reached the Markdown; interface tokens belong in HTML only")
    ids = re.findall(r'\bid="([^"]+)"', out.split('<script type="text/plain"')[0])
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        problems.append(f"duplicate ids: {dupes}")
    targets = set(re.findall(r'href="#([^"]+)"', out.split('<script type="text/plain"')[0])) - {"markdown"}
    missing = sorted(t for t in targets if t not in ids)
    if missing:
        problems.append(f"links to missing ids: {missing}")
    page = out.split('<script type="text/plain"')[0]
    for word in bans:
        if word and re.search(rf"\b{re.escape(word)}\b", page + md):
            problems.append(f"banned word present: {word}")
    if strict_paths and re.search(r"/Users/[^/\s]+/|/home/[^/\s]+/", page + md):
        problems.append("absolute home path present (rewrite as ~/)")
    return problems


def assemble(*, body: str, md: str, out_path: str, title: str, brand: str, date: str, desc: str = "",
             lang: str = "en", ui_lang: str = "", md_filename: str = "report.md", storage_key: str = "report",
             sidebar_note: str = "", code: dict[str, str] | None = None, bans: list[str] | None = None,
             strict_paths: bool = False) -> None:
    """Fill the shell, run every check, and write out_path only when all pass."""
    shell = SHELL.read_text()
    for ph in ONCE:
        if shell.count(ph) != 1:
            fail(f"shell token {ph} must appear exactly once (found {shell.count(ph)})")
    strings = json.loads(UI_STRINGS.read_text())
    ui_lang = ui_lang or (lang if lang in strings else "en")
    if ui_lang not in strings:
        fail(f"no UI strings for {ui_lang!r}; add them to {UI_STRINGS.name} (have: {', '.join(strings)})")
    if "</script" in md.lower() or ("<!--" in md and "<script" in md.lower()):
        fail("markdown contains </script, or <!-- together with <script, and cannot be embedded safely")
    if not re.fullmatch(r"[A-Za-z0-9._-]+\.md", md_filename):
        fail(f"md filename {md_filename!r} must be ascii letters, digits, . _ - and end in .md")
    for lang_key, table in strings.items():
        gap = sorted(set(strings["en"]) ^ set(table))
        if gap:
            fail(f"{UI_STRINGS.name}: {lang_key} and en differ in keys {gap}")
    for name, text in (code or {}).items():
        token = f"__CODE:{name}__"
        if token not in body:
            fail(f"{token} not found in body")
        body = body.replace(token, html.escape(text, quote=False))

    toc, n_sections = build_toc(body)
    out = shell
    for ph, val in [("__LANG__", lang), ("__TITLE__", html.escape(title)), ("__DESC__", html.escape(desc or title)),
                    ("__BRAND__", html.escape(brand, quote=False)), ("__DATE__", html.escape(date)),
                    ("__TOC__", toc), ("__SIDEBAR_NOTE__", sidebar_note.strip()), ("__BODY__", body.rstrip("\n"))]:
        out = out.replace(ph, val, 1)
    for key, val in strings[ui_lang].items():
        if re.search(r'[<>&"`\\]', val):
            fail(f"UI string {ui_lang}.{key} must not contain < > & \" ` or \\ (it lands in HTML and JS)")
        out = out.replace(f"__UI:{key}__", val)
    out = out.replace("__MD_FILENAME__", html.escape(md_filename)).replace("__STORAGE_KEY__", re.sub(r"[^a-z0-9-]", "-", storage_key.lower()))
    out = out.replace("__MD_SOURCE__", "\n" + md, 1)

    problems = check(out, md, [w.strip() for w in bans or []], strict_paths)
    if problems:
        fail("refusing to write:\n  - " + "\n  - ".join(problems))
    pathlib.Path(out_path).write_text(out)
    page = out.split('<script type="text/plain"')[0]
    cards = page.count('class="fcard"')
    print(f"wrote {out_path} · {len(out) / 1024:.1f} KB · sections {n_sections} · svg {page.count('<svg')} · "
          f"tables {page.count('<table')} · cards {cards} · md lines {len(md.splitlines())}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--body", required=True)
    ap.add_argument("--md", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--brand", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--desc", default="")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--ui-lang", default="", help="language of the page chrome (default: --lang when available, else en)")
    ap.add_argument("--md-filename", default="")
    ap.add_argument("--storage-key", default="report")
    ap.add_argument("--sidebar-note", default="", help="path to an HTML snippet shown under the TOC")
    ap.add_argument("--code", action="append", default=[], help="name=path, fills __CODE:name__ in the body")
    ap.add_argument("--ban", default="", help="comma-separated words that must not appear")
    ap.add_argument("--strict-paths", action="store_true", help="fail on absolute home paths")
    a = ap.parse_args()

    code = {}
    for spec in a.code:
        name, _, path = spec.partition("=")
        code[name] = pathlib.Path(path).read_text()
    assemble(body=pathlib.Path(a.body).read_text(), md=pathlib.Path(a.md).read_text(), out_path=a.out,
             title=a.title, brand=a.brand, date=a.date, desc=a.desc, lang=a.lang, ui_lang=a.ui_lang,
             md_filename=a.md_filename or pathlib.Path(a.md).name, storage_key=a.storage_key,
             sidebar_note=pathlib.Path(a.sidebar_note).read_text() if a.sidebar_note else "",
             code=code, bans=a.ban.split(","), strict_paths=a.strict_paths)


if __name__ == "__main__":
    main()
