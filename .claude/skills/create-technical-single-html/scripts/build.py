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
ONCE = ["__TITLE__", "__DESC__", "__BRAND__", "__DATE__", "__TOC__", "__SIDEBAR_NOTE__", "__BODY__",
        "__MD_SOURCE__", "__NOTATION__", "__LANG_SWITCH__", "__ALT_LANG__", "__UI_ALT__", "__MD_ALT__"]
MANY = ["__LANG__", "__MD_FILENAME__", "__STORAGE_KEY__"]


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


def prefix_ids(fragment: str, prefix: str) -> str:
    """Give every id in an alternate-language body a prefix, and point its links and references at the new ids."""
    fragment = re.sub(r'\bid="([^"]+)"', lambda m: f'id="{prefix}{m.group(1)}"', fragment)
    fragment = re.sub(r'\b((?:xlink:)?href)="#([^"]+)"', lambda m: f'{m.group(1)}="#{prefix}{m.group(2)}"', fragment)
    fragment = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{prefix}{m.group(1)})", fragment)
    return re.sub(r'\b(aria-labelledby|aria-describedby|aria-controls|for)="([^"]+)"',
                  lambda m: f'{m.group(1)}="{" ".join(prefix + t for t in m.group(2).split())}"', fragment)


def check(out: str, md: str, bans: list[str], strict_paths: bool) -> list[str]:
    problems = []
    own = "|".join(t.strip("_") for t in ONCE + MANY)
    outside_md = re.sub(r'<script type="text/plain"[^>]*>.*?</script>', "", out, flags=re.S)
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
    if strict_paths and re.search(r"/Users/(?!Shared/)[A-Za-z0-9._-]+/|/home/[A-Za-z0-9._-]+/", page + md):
        problems.append("absolute home path present (rewrite as ~/)")
    return problems


def assemble(*, body: str, md: str, out_path: str, title: str, brand: str, date: str, desc: str = "",
             lang: str = "en", ui_lang: str = "", md_filename: str = "report.md", storage_key: str = "report",
             sidebar_note: str = "", code: dict[str, str] | None = None, bans: list[str] | None = None,
             strict_paths: bool = False, notation: dict[str, str] | None = None, alt: dict | None = None) -> None:
    """Fill the shell, run every check, and write out_path only when all pass.

    alt: a second language of the same page — {lang, body, md, md_filename, title, brand?,
    sidebar_note?, notation?}. Its body gets "<lang>-"-prefixed ids and its interface text from
    ui-strings; a header button switches between the two, the first language being the default."""
    shell = SHELL.read_text()
    for ph in ONCE:
        if shell.count(ph) != 1:
            fail(f"shell token {ph} must appear exactly once (found {shell.count(ph)})")
    strings = json.loads(UI_STRINGS.read_text())
    ui_lang = ui_lang or (lang if lang in strings else "en")
    if ui_lang not in strings:
        fail(f"no UI strings for {ui_lang!r}; add them to {UI_STRINGS.name} (have: {', '.join(strings)})")
    for text, name in [(md, md_filename)] + ([(alt["md"], alt["md_filename"])] if alt else []):
        if "</script" in text.lower() or ("<!--" in text and "<script" in text.lower()):
            fail("markdown contains </script, or <!-- together with <script, and cannot be embedded safely")
        if not re.fullmatch(r"[A-Za-z0-9._-]+\.md", name):
            fail(f"md filename {name!r} must be ascii letters, digits, . _ - and end in .md")
    if alt:
        if alt["lang"] == lang:
            fail(f"alt language {alt['lang']!r} is the same as the page language")
        if alt["lang"] not in strings:
            fail(f"no UI strings for alt language {alt['lang']!r}; add them to {UI_STRINGS.name}")
        if alt["md_filename"] == md_filename:
            fail("the two languages need different md filenames")
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
    lv = f' data-lv="{lang}"' if alt else ""
    toc = f'    <ul class="toc"{lv}>\n{toc}\n    </ul>'
    lang_switch = alt_lang = ui_alt = md_alt = ""
    notes = {lang: notation or {}}
    if alt:
        a = alt["lang"]
        alt_body = prefix_ids(alt["body"].rstrip("\n"), f"{a}-")
        for key, val in strings[a].items():
            alt_body = alt_body.replace(f"__UI:{key}__", val)
        alt_toc, _ = build_toc(alt_body)
        toc += f'\n    <ul class="toc" data-lv="{a}" hidden>\n{alt_toc}\n    </ul>'
        lang_box = lambda code, t, b: (f'<div class="lang-body" data-lang="{code}" data-lv="{code}"'
                                        f' data-title="{html.escape(t)}" data-brand="{html.escape(b)}"')
        body = (f'{lang_box(lang, title, brand)}>\n{body.rstrip()}\n</div>\n'
                f'{lang_box(a, alt["title"], alt.get("brand") or brand)} hidden>\n{alt_body}\n</div>')
        sidebar_note = (f'<div data-lv="{lang}">{sidebar_note.strip()}</div>'
                        f'<div data-lv="{a}" hidden>{prefix_ids(alt.get("sidebar_note", "").strip(), f"{a}-")}</div>')
        lang_switch = (f'  <button class="icon-btn lang-btn" data-action="lang:toggle" aria-label="__UI:toggle_lang__"'
                       f' data-ui-aria="toggle_lang">{html.escape(a.upper())}</button>\n')
        alt_lang = a
        ui_alt = json.dumps(strings[a], ensure_ascii=False)
        md_alt = (f'\n<script type="text/plain" id="md-source-{a}" data-lang="{a}" data-file="{html.escape(alt["md_filename"])}">'
                  f'\n{alt["md"]}</script>')
        notes[a] = alt.get("notation") or {}
    out = shell
    for ph, val in [("__TITLE__", html.escape(title)), ("__DESC__", html.escape(desc or title)),
                    ("__BRAND__", html.escape(brand, quote=False)), ("__DATE__", html.escape(date)),
                    ("__TOC__", toc), ("__SIDEBAR_NOTE__", sidebar_note.strip()), ("__BODY__", body.rstrip("\n")),
                    ("__LANG_SWITCH__", lang_switch), ("__ALT_LANG__", alt_lang), ("__UI_ALT__", ui_alt)]:
        out = out.replace(ph, val, 1)
    out = out.replace("__LANG__", lang)
    for key, val in strings[ui_lang].items():
        if re.search(r'[<>&"`\\]', val):
            fail(f"UI string {ui_lang}.{key} must not contain < > & \" ` or \\ (it lands in HTML and JS)")
        out = out.replace(f"__UI:{key}__", val)
    out = out.replace("__MD_FILENAME__", html.escape(md_filename)).replace("__STORAGE_KEY__", re.sub(r"[^a-z0-9-]", "-", storage_key.lower()))
    out = out.replace("__NOTATION__", json.dumps(notes, ensure_ascii=False).replace("<", "\\u003c"), 1)
    out = out.replace("__MD_SOURCE__", "\n" + md, 1).replace("__MD_ALT__", md_alt, 1)

    problems = check(out, md + ("\n" + alt["md"] if alt else ""), [w.strip() for w in bans or []], strict_paths)
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
