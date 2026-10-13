#!/usr/bin/env python3
"""Render a post.json page spec into a finished single-file HTML page.

    python3 render.py post.json --out page.html [--keep-dir build/]

post.json holds the page as data: `meta` (title, brand, date, desc, lang, md_filename,
storage_key, optional ui_lang, sidebar_note, ban, strict_paths), an optional `hero`, a list of
`sections` (each with `blocks`) and an optional `footer`. Every block has a `type` from
assets/components.json; its fields are checked against that registry, then the block's
template in assets/blocks/<type>.j2 renders it twice — once as HTML for the page, once as
Markdown for the Markdown tab. build.assemble() then fills the shell and runs every check.

--keep-dir writes the intermediate body.html and the generated Markdown for inspection.
Paths in a block's `file` field are relative to post.json.
Requires jinja2 and markdown-it-py.
"""

import argparse
import html
import json
import pathlib
import re
import sys

from jinja2 import Environment, FileSystemLoader, StrictUndefined, UndefinedError
from markdown_it import MarkdownIt
from markupsafe import Markup

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build import SKILL_DIR, assemble, fail  # noqa: E402

BLOCKS = SKILL_DIR / "assets" / "blocks"
REGISTRY = json.loads((SKILL_DIR / "assets" / "components.json").read_text())["components"]
META_FIELDS = {"title", "brand", "date", "desc", "lang", "ui_lang", "md_filename", "storage_key",
               "sidebar_note", "ban", "strict_paths"}
TOP_FIELDS = {"$schema", "meta", "hero", "sections", "footer"}
KINDS = {"ok", "warn", "bad", "info", "acc", "mute"}
CALLOUT_KINDS = {"note", "warn", "key"}
SECTION_ID = re.compile(r"^[a-z][a-z0-9-]*$")
FENCE_LINE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
COPY_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" '
             'width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>')


def codebox(text: str, label: str) -> Markup:
    return Markup(f'<div class="codebox"><div class="bar"><span>{html.escape(label)}</span>'
            f'<button class="btn" data-action="copy:code">{COPY_ICON}__UI:copy__</button></div>'
            f'<pre><code>{html.escape(text, quote=False)}</code></pre></div>')


def make_markdown() -> MarkdownIt:
    mdi = MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"])
    rules = mdi.add_render_rule

    def table_open(self, tokens, idx, options, env):
        return '<div class="tw"><table>\n'

    def table_close(self, tokens, idx, options, env):
        return "</table></div>\n"

    def fence(self, tokens, idx, options, env):
        tok = tokens[idx]
        return str(codebox(tok.content.rstrip("\n"), tok.info.strip() or "text"))

    def link_open(self, tokens, idx, options, env):
        tok = tokens[idx]
        if (tok.attrGet("href") or "").startswith(("http://", "https://")):
            tok.attrSet("target", "_blank")
            tok.attrSet("rel", "noopener")
        return self.renderToken(tokens, idx, options, env)

    rules("table_open", table_open)
    rules("table_close", table_close)
    rules("fence", fence)
    rules("code_block", fence)
    rules("link_open", link_open)
    return mdi


MD = make_markdown()


def f_md(text: str) -> Markup:
    prose = outside_fences(text)
    if re.search(r"^#{1,2} ", prose, re.M) or re.search(r"^[^\n\s].*\n {0,3}(=+|-+) *$", prose, re.M):
        fail(f"markdown blocks may use ### and below only (sections own h2): {text[:60]!r}")
    return Markup(f'<div class="prose">{MD.render(text)}</div>')


def closes(line: str, fence: str) -> bool:
    m = FENCE_LINE.match(line)
    return bool(m) and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not line.strip()[len(m.group(1)):]


def outside_fences(text: str) -> str:
    """The text with fenced code blocks blanked out, so checks see only prose."""
    out, fence = [], ""
    for line in text.split("\n"):
        if fence:
            fence = "" if closes(line, fence) else fence
            out.append("")
        elif m := FENCE_LINE.match(line):
            fence = m.group(1)
            out.append("")
        else:
            out.append(line)
    return "\n".join(out)


def squeeze_blank_lines(md: str) -> str:
    """Collapse runs of blank lines between blocks, never inside fenced code."""
    out, fence, blank = [], "", False
    for line in md.split("\n"):
        if fence:
            fence = "" if closes(line, fence) else fence
            out.append(line)
            continue
        if m := FENCE_LINE.match(line):
            fence = m.group(1)
        if not line.strip():
            if blank:
                continue
            blank = True
        else:
            blank = False
        out.append(line)
    return "\n".join(out).strip("\n") + "\n"


def f_fence(text) -> str:
    """A backtick fence longer than any backtick run inside the text."""
    runs = [len(r) for r in re.findall(r"`+", str(text))]
    return "`" * max(3, max(runs, default=0) + 1)


def f_inl(text) -> Markup:
    return Markup(MD.renderInline(str(text)))


def f_plain(text) -> str:
    """Inline markdown reduced to plain text, for aria labels and <title>."""
    s = re.sub(r"`([^`]+)`", r"\1", str(text))
    s = re.sub(r"\*\*([^*]+)\*\*|\*([^*]+)\*", lambda m: m.group(1) or m.group(2), s)
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)


def f_cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def make_env() -> Environment:
    env = Environment(loader=FileSystemLoader(str(BLOCKS)), autoescape=True, undefined=StrictUndefined,
                      trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
    env.filters.update(md=f_md, inl=f_inl, plain=f_plain, cell=f_cell, fence=f_fence)
    env.globals["codebox"] = codebox
    return env


def check_fields(b: dict, where: str) -> None:
    kind = b.get("type")
    spec = REGISTRY.get(kind)
    if not spec:
        fail(f"{where}: unknown block type {kind!r} (known: {', '.join(sorted(REGISTRY))})")
    allowed = set(spec["required"]) | set(spec.get("optional", {})) | {"type"}
    missing = [f for f in spec["required"] if f not in b]
    unknown = sorted(set(b) - allowed)
    if missing:
        fail(f"{where} ({kind}): missing {missing}")
    if unknown:
        fail(f"{where} ({kind}): unknown fields {unknown}; allowed: {sorted(allowed - {'type'})}")
    one_of = spec.get("one_of")
    if one_of and sum(f in b for f in one_of) != 1:
        fail(f"{where} ({kind}): give exactly one of {one_of}")
    for field, item_spec in spec.get("nested", {}).items():
        for i, item in enumerate(b.get(field, [])):
            if not isinstance(item, dict):
                fail(f"{where} ({kind}).{field}[{i}]: expected an object")
            item_missing = [f for f in item_spec["required"] if f not in item]
            item_unknown = sorted(set(item) - set(item_spec["required"]) - set(item_spec["optional"]))
            if item_missing or item_unknown:
                fail(f"{where} ({kind}).{field}[{i}]: missing {item_missing}, unknown {item_unknown}; "
                     f"allowed: {item_spec['required'] + item_spec['optional']}")
    if kind == "callout" and not (b.get("title") or b.get("text", "").strip()):
        fail(f"{where} (callout): give a title, a text, or both")
    if kind == "callout" and b.get("kind", "note") not in CALLOUT_KINDS:
        fail(f"{where} (callout): kind must be one of {sorted(CALLOUT_KINDS)}")
    if "cols" in b and b["cols"] not in (2, 3):
        fail(f"{where} ({kind}): cols must be 2 or 3")
    if kind == "video" and not re.fullmatch(r"[A-Za-z0-9_-]{11}", str(b["youtube"])):
        fail(f"{where} (video): youtube must be the 11-character id, not a URL: {b['youtube']!r}")
    if kind == "video" and "start" in b and not (isinstance(b["start"], int) and b["start"] >= 0):
        fail(f"{where} (video): start must be whole seconds")
    if kind == "section" and not SECTION_ID.match(b["id"]):
        fail(f"{where}: section id {b['id']!r} must be lowercase ascii, start with a letter, use only a-z 0-9 -")
    if kind != "callout":
        check_kinds(b, f"{where} ({kind})")


def check_kinds(node, where: str) -> None:
    """Every `kind` below a block (pills, tags, status, legends) uses the fixed semantic set."""
    if isinstance(node, dict):
        if "kind" in node and node["kind"] not in KINDS:
            fail(f"{where}: kind {node['kind']!r} is not one of {sorted(KINDS)}")
        for v in node.values():
            check_kinds(v, where)
    elif isinstance(node, list):
        for v in node:
            check_kinds(v, where)


class Renderer:
    def __init__(self, base: pathlib.Path):
        self.env = make_env()
        self.base = base

    def load_files(self, b: dict) -> dict:
        if "file" in b:
            b = {**b, "file": (self.base / b["file"]).read_text().rstrip("\n")}
        return b

    def block(self, b: dict, where: str, inner: tuple[str, str] = ("", "")) -> tuple[str, str]:
        check_fields(b, where)
        b = self.load_files(b)
        mod = self.env.get_template(REGISTRY[b["type"]]["template"]).module
        try:
            return str(mod.html(b, Markup(inner[0]))), str(mod.md(b, inner[1]))
        except UndefinedError as e:
            fail(f"{where} ({b['type']}): {e} — check the field shapes in components.json")

    def page(self, spec: dict) -> tuple[str, str]:
        unknown = set(spec) - TOP_FIELDS
        if unknown:
            fail(f"post.json: unknown top-level fields {sorted(unknown)}")
        html_parts, md_parts = [], []
        if "hero" in spec:
            h, m = self.block({"type": "hero", **spec["hero"]}, "hero")
            html_parts.append(h); md_parts.append(m)
        for i, sec in enumerate(spec.get("sections", [])):
            where = f"sections[{i}] ({sec.get('id', '?')})"
            inner_h, inner_m = [], []
            for j, b in enumerate(sec.get("blocks", [])):
                h, m = self.block(b, f"{where}.blocks[{j}]")
                inner_h.append(h); inner_m.append(m)
            h, m = self.block({"type": "section", **{k: v for k, v in sec.items() if k != "blocks"}}, where,
                              ("\n".join(inner_h), "\n\n".join(inner_m)))
            html_parts.append(h); md_parts.append(m)
        if "footer" in spec:
            h, m = self.block({"type": "footer", "text": spec["footer"]}, "footer")
            html_parts.append(h); md_parts.append(m)
        md = squeeze_blank_lines("\n\n".join(p.strip("\n") for p in md_parts if p.strip()))
        return "\n".join(html_parts) + "\n", md


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("post", help="path to post.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--keep-dir", default="", help="also write body.html and the Markdown here")
    a = ap.parse_args()

    post_path = pathlib.Path(a.post)
    spec = json.loads(post_path.read_text())
    meta = spec.get("meta") or fail("post.json: meta is required")
    unknown = set(meta) - META_FIELDS
    if unknown:
        fail(f"meta: unknown fields {sorted(unknown)}; allowed: {sorted(META_FIELDS)}")
    for field in ("title", "brand", "date", "md_filename", "storage_key"):
        if not meta.get(field):
            fail(f"meta.{field} is required")

    body, md = Renderer(post_path.parent).page(spec)
    if a.keep_dir:
        keep = pathlib.Path(a.keep_dir)
        keep.mkdir(parents=True, exist_ok=True)
        (keep / "body.html").write_text(body)
        (keep / meta["md_filename"]).write_text(md)
    assemble(body=body, md=md, out_path=a.out, title=meta["title"], brand=meta["brand"], date=meta["date"],
             desc=meta.get("desc", ""), lang=meta.get("lang", "en"), ui_lang=meta.get("ui_lang", ""),
             md_filename=meta["md_filename"], storage_key=meta["storage_key"],
             sidebar_note=meta.get("sidebar_note", ""),
             bans=meta["ban"].split(",") if isinstance(meta.get("ban"), str) else meta.get("ban", []),
             strict_paths=meta.get("strict_paths", False))


if __name__ == "__main__":
    main()
