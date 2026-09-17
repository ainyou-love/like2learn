#!/usr/bin/env python3
"""Fill assets/template.html with a notebook entry and validate the result.

Usage:
  python3 build_doc.py --meta meta.json --sections sections.html --out-dir resources/<folder> [--force]

meta.json keys: no, title, year, kicker, subtitle, pills (list), source; optional chapter ("1", "4–5")
Entry numbers are unique across every folder under resources/, because /NN short links resolve by number.
sections.html: consecutive <section class="entry" id="sN" data-toc="..."> blocks.
"""
import argparse
import html
import json
import re
import sys
import unicodedata
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "assets" / "template.html"
REQUIRED_META = ["no", "title", "year", "kicker", "subtitle", "pills", "source"]


def slugify(text):
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def split_sections(fragment):
    blocks = re.findall(r"<section\b.*?</section>", fragment, flags=re.S)
    leftover = re.sub(r"<section\b.*?</section>", "", fragment, flags=re.S)
    leftover = re.sub(r"<!--.*?-->", "", leftover, flags=re.S).strip()
    return blocks, leftover


def check_section(idx, block, errors, warnings):
    n = f"{idx:02d}"
    open_tag = re.match(r"<section\b[^>]*>", block).group(0)
    if 'class="entry"' not in open_tag:
        errors.append(f"section {n}: missing class=\"entry\"")
    if f'id="s{idx}"' not in open_tag:
        errors.append(f"section {n}: id must be s{idx}")
    if not re.search(r'data-toc="[^"]+"', open_tag):
        errors.append(f"section {n}: missing data-toc short title")
    if f'<span class="eyebrow">Mục {n}</span>' not in block:
        errors.append(f'section {n}: eyebrow must be <span class="eyebrow">Mục {n}</span>')
    for needle, label in [
        ('class="entry-head"', "entry-head"),
        ("<h2>", "h2"),
        ('class="summary-line"', "summary-line"),
        ('class="frame"', "illustration frame"),
        ('<ul class="points">', "ul.points"),
    ]:
        if needle not in block:
            errors.append(f"section {n}: missing {label}")
    svg = re.search(r"<svg\b[^>]*>", block)
    if not svg:
        errors.append(f"section {n}: missing inline SVG illustration")
    else:
        tag = svg.group(0)
        for attr in ['class="ill"', 'viewBox="0 0 160 120"', 'aria-hidden="true"']:
            if attr not in tag:
                errors.append(f"section {n}: svg needs {attr}")
        shapes = re.findall(r"<(path|circle|rect|line|polyline|polygon|ellipse)\b", block)
        if not 3 <= len(shapes) <= 14:
            warnings.append(f"section {n}: illustration has {len(shapes)} shapes (aim for 5-12)")
    if len(re.findall(r"<li>", block)) < 2:
        warnings.append(f"section {n}: fewer than 2 bullets")
    if 'class="callout"' not in block:
        warnings.append(f"section {n}: no callout (fine for a few sections, not most)")

    text = re.sub(r"<em>.*?</em>", "", block, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    for quote in re.findall(r"[\"“][^\"”]{6,}[\"”]", text):
        errors.append(f"section {n}: quoted phrase not wrapped in <em>: {quote[:60]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True)
    ap.add_argument("--sections", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--force", action="store_true", help="overwrite an existing entry with the same number")
    args = ap.parse_args()

    meta = json.loads(Path(args.meta).read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED_META if not meta.get(k)]
    if missing:
        sys.exit(f"ERROR meta.json missing: {', '.join(missing)}")
    no = f"{int(meta['no']):02d}"
    chapter = str(meta.get("chapter", "")).strip()

    blocks, leftover = split_sections(Path(args.sections).read_text(encoding="utf-8"))
    errors, warnings = [], []
    if not blocks:
        sys.exit("ERROR sections.html contains no <section> blocks")
    if leftover:
        errors.append(f"content outside <section> blocks: {leftover[:80]}")
    for i, block in enumerate(blocks, 1):
        check_section(i, block, errors, warnings)
    if re.search(r"<(img|script|iframe)\b", "".join(blocks)):
        errors.append("sections must not contain <img>, <script> or <iframe>")
    if errors:
        print("\n".join(f"ERROR {e}" for e in errors))
        sys.exit(1)

    toc = []
    for i, block in enumerate(blocks, 1):
        label = re.search(r'data-toc="([^"]+)"', block).group(1)
        toc.append(f'        <li><a href="#s{i}"><span class="t">{label}</span><span class="num">{i:02d}</span></a></li>')

    esc = html.escape
    out = TEMPLATE.read_text(encoding="utf-8")
    replacements = {
        "{{NO}}": no,
        "{{TAB_TITLE}}": esc(f"Chương {chapter}: {meta['title']}" if chapter else meta["title"], quote=False),
        "{{TITLE}}": esc(meta["title"], quote=False),
        "{{YEAR}}": esc(str(meta["year"])),
        "{{KICKER}}": esc(meta["kicker"], quote=False),
        "{{SUBTITLE}}": esc(meta["subtitle"], quote=False),
        "{{META_PILLS}}": "\n".join(f'        <span class="pill">{esc(p, quote=False)}</span>' for p in meta["pills"]),
        "{{TOC_ITEMS}}": "\n".join(toc),
        "{{SECTIONS}}": "\n\n".join(f"    <!-- SECTION {i} -->\n    {b}" for i, b in enumerate(blocks, 1)),
        "{{SOURCE_LINE}}": esc(meta["source"], quote=False),
    }
    for key, value in replacements.items():
        out = out.replace(key, value)
    if "{{" in out:
        sys.exit("ERROR unfilled placeholder left in output")

    out_dir = Path(args.out_dir)
    resources_root = next((p for p in [out_dir, *out_dir.parents] if p.name == "resources"), out_dir)
    existing = sorted(resources_root.rglob(f"{no}-*.html"))
    chapter_slug = "-".join(f"{int(n):02d}" for n in re.findall(r"\d+", chapter))
    name = f"{no}-chuong-{chapter_slug}-{slugify(meta['title'])}" if chapter_slug else f"{no}-{slugify(meta['title'])}"
    target = out_dir / f"{name}.html"
    if existing and not args.force:
        sys.exit(f"ERROR entry No.{no} already exists: {existing[0]} (rerun with --force to overwrite)")
    out_dir.mkdir(parents=True, exist_ok=True)
    target.write_text(out, encoding="utf-8")

    for w in warnings:
        print(f"WARN {w}")
    print(f"OK wrote {target} ({len(blocks)} sections)")


if __name__ == "__main__":
    main()
