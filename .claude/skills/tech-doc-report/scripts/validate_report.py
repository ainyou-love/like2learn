#!/usr/bin/env python3
"""Check a report JSON against the schema before it is ever built into a page.

The research step writes this file from many parallel agents, so the failures
worth catching are the ones that come from stitching: an item citing a source
another agent never wrote, a Vietnamese field left empty, two sections both
claiming id "C". Every one of those renders as a page that looks finished and
is quietly wrong, which is the expensive kind of wrong.

    validate_report.py report.json            # human-readable
    validate_report.py report.json --json     # machine-readable

Exit code 1 on any error; warnings alone still exit 0.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URLISH = re.compile(r"https?://|www\.", re.I)
# A command pasted into localized prose is a real data bug -- it cannot be
# copied with the copy button and it drifts between the two languages. But the
# tool names double as product names, and matching the bare word made this fire
# 24 times in one real run on "npm CLI 12.1.0", "an npm token" and "npm plugin".
# A warning that is wrong 24 times out of 24 only teaches the operator to stop
# reading warnings, so both halves now have to match: something shaped like a
# subcommand, AND punctuation that prose does not use.
# \b rather than \s, so a command fenced in backticks still counts; [a-z-]*
# rather than + so "npm i" does. Both are safe only because CMDPUNCT must match.
TOOLCMD = re.compile(
    r"\b(?:npm|npx|pnpm|yarn|bun|pip|uv|poetry|git|curl|wget|brew|docker|"
    r"kubectl|psql|sudo|make|cargo|go)\s+[a-z][a-z-]*")
# No ";" here: a semicolon is ordinary English punctuation, and including it
# flagged a perfectly clean pnpm changelog paragraph. What is left is
# punctuation prose genuinely does not use -- a flag, a shell chain, a pinned
# version, a prompt, a code fence.
CMDPUNCT = re.compile(r"\s--?[A-Za-z]|&&|\|\||@\d|\$\s|`")


def looks_like_command(text: str) -> bool:
    return bool(TOOLCMD.search(text) and CMDPUNCT.search(text))

ENUMS = {
    "date_precision": {"day", "month", "quarter", "tbd"},
    "action": {"patch_now", "try_now", "watch", "ignore"},
    "truth": {"FACT", "ASSUMPTION", "UNVERIFIED", "VENDOR_CLAIM"},
    "confidence": {"HIGH", "MEDIUM", "LOW"},
    "tag": {"RISK", "RISK/SECURITY", "RISK/MIGRATION", "TRADE_OFF", "DECISION", "CONCERN"},
    "kind": {"release", "incident", "event", "tool", "repo", "pattern", "stat", "model",
             "person", "channel", "community", "spec", "video"},
    "status": {"ok", "empty"},
    "dl_status": {"upcoming", "passed", "tbd"},
    "source_type": {"official", "changelog", "repo", "security_lab", "paper",
                    "practitioner_blog", "media", "vendor", "listicle", "community", "video"},
    "trust": {"high", "medium", "low"},
    "depth": {"brief", "standard", "deep"},
}


class Check:
    def __init__(self):
        self.errors: list = []
        self.warnings: list = []

    def err(self, where: str, msg: str):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str):
        self.warnings.append(f"{where}: {msg}")

    def enum(self, where: str, field: str, value, group: str, allow_none=False):
        if value is None and allow_none:
            return
        if value not in ENUMS[group]:
            self.err(where, f"{field}={value!r} is not one of {sorted(ENUMS[group])}")

    def ltext(self, where: str, field: str, node, langs):
        """An LText carries the whole point of the bilingual pipeline: if one
        language is missing the page has to show the other one and flag it, so
        an empty key is a data bug, not a rendering choice."""
        if not isinstance(node, dict):
            self.err(where, f"{field} must be an object with keys {langs}, got {type(node).__name__}")
            return
        for lg in langs:
            v = node.get(lg)
            if not isinstance(v, str) or not v.strip():
                self.err(where, f"{field}.{lg} is missing or empty")
                continue
            if URLISH.search(v):
                self.err(where, f"{field}.{lg} contains a URL -- put it in links[] instead")
            if looks_like_command(v):
                self.warn(where, f"{field}.{lg} looks like it contains a command -- commands[] is the neutral field")
        extra = set(node) - set(langs)
        if extra:
            self.warn(where, f"{field} has languages not declared in meta.languages: {sorted(extra)}")

    def date(self, where: str, field: str, value, precision):
        if value is None:
            if precision != "tbd":
                self.err(where, f"{field} is null so {field}_precision must be \"tbd\", got {precision!r}")
            return
        if not ISO.match(str(value)):
            self.err(where, f"{field}={value!r} is not YYYY-MM-DD")


def validate(d: dict) -> Check:
    c = Check()
    if d.get("schema_version") != "1.0":
        c.err("root", f"schema_version must be \"1.0\", got {d.get('schema_version')!r}")

    meta = d.get("meta") or {}
    langs = meta.get("languages") or ["vi", "en"]
    if not langs:
        c.err("meta", "languages is empty")
    if meta.get("default_language") not in langs:
        c.err("meta", f"default_language {meta.get('default_language')!r} is not in languages {langs}")
    c.enum("meta", "depth", meta.get("depth"), "depth")
    for f in ("title", "subtitle", "data_quality_note"):
        c.ltext("meta", f, meta.get(f), langs)
    win = meta.get("time_window") or {}
    for f in ("from", "to"):
        if not ISO.match(str(win.get(f, ""))):
            c.err("meta.time_window", f"{f}={win.get(f)!r} is not YYYY-MM-DD")
    if ISO.match(str(win.get("from", ""))) and ISO.match(str(win.get("to", ""))) and win["from"] > win["to"]:
        c.err("meta.time_window", "from is after to")

    # ---- ids ----
    seen: dict = {}

    def claim(kind: str, i: str, where: str):
        if not i:
            c.err(where, "missing id")
            return
        if i in seen:
            c.err(where, f"id {i!r} already used by {seen[i]}")
        else:
            seen[i] = f"{kind} at {where}"

    items: dict = {}
    for s in d.get("sections") or []:
        where = f"section {s.get('id')}"
        claim("section", s.get("id"), where)
        c.enum(where, "status", s.get("status"), "status")
        for f in ("title", "summary"):
            c.ltext(where, f, s.get(f), langs)
        if s.get("status") == "ok" and not (s.get("items") or []):
            c.warn(where, 'status is "ok" but there are no items -- use "empty"')
        for it in s.get("items") or []:
            iw = f"item {it.get('id')}"
            claim("item", it.get("id"), iw)
            items[it.get("id")] = it
            if not str(it.get("id", "")).startswith(str(s.get("id", "")) + "-"):
                c.warn(iw, f"id does not start with its section id {s.get('id')!r}")
            c.enum(iw, "kind", it.get("kind"), "kind")
            c.enum(iw, "truth", it.get("truth"), "truth")
            c.enum(iw, "action", it.get("action"), "action", allow_none=True)
            c.enum(iw, "date_precision", it.get("date_precision"), "date_precision")
            for tg in it.get("tags") or []:
                c.enum(iw, "tags[]", tg, "tag")
            c.date(iw, "date", it.get("date"), it.get("date_precision"))
            for f in ("headline", "body"):
                c.ltext(iw, f, it.get(f), langs)
            if it.get("truth") == "ASSUMPTION":
                c.enum(iw, "confidence", it.get("confidence"), "confidence")
            if not isinstance(it.get("name"), str) or not it.get("name", "").strip():
                c.err(iw, "name is missing")
            if not (it.get("source_ids") or []) and it.get("truth") != "ASSUMPTION":
                c.err(iw, f"no source_ids and truth is {it.get('truth')!r} -- only ASSUMPTION may go unsourced")
            for st in it.get("stack_relevance") or []:
                if st not in (meta.get("stack") or []):
                    c.warn(iw, f"stack_relevance {st!r} is not in meta.stack")
            if it.get("date") and ISO.match(str(win.get("from", ""))) and ISO.match(str(win.get("to", ""))):
                outside = it["date"] < win["from"] or it["date"] > win["to"]
                if outside and not it.get("older_context"):
                    c.err(iw, f"date {it['date']} is outside the window but older_context is not true")
                if not outside and it.get("older_context"):
                    c.warn(iw, "older_context is true but the date is inside the window")
            for m in it.get("metrics") or []:
                c.ltext(iw + " metric " + str(m.get("key")), "label", m.get("label"), langs)
            for lk in it.get("links") or []:
                if not str(lk.get("url", "")).startswith("https://"):
                    c.warn(iw, f"link {lk.get('url')!r} is not https")
                c.ltext(iw + " link", "label", lk.get("label"), langs)

    sources: dict = {}
    for s in d.get("sources") or []:
        where = f"source {s.get('id')}"
        claim("source", s.get("id"), where)
        sources[s.get("id")] = s
        c.enum(where, "source_type", s.get("source_type"), "source_type")
        c.enum(where, "trust", s.get("trust"), "trust")
        if not str(s.get("url", "")).startswith("https://"):
            c.err(where, f"url {s.get('url')!r} must be an absolute https URL")
        if s.get("published_at") and not ISO.match(str(s["published_at"])):
            c.err(where, f"published_at {s['published_at']!r} is not YYYY-MM-DD")
        for f in ("title", "publisher"):
            if not str(s.get(f, "")).strip():
                c.err(where, f"{f} is empty")
        if "youtu" in str(s.get("url", "")) and s.get("source_type") not in ("video", "community", "media"):
            c.warn(where, 'a YouTube URL usually wants source_type "video" so the page embeds a player')

    for coll, fields in (("highlights", ("text",)), ("stack_actions", ("text",)),
                         ("checklist", ("text",)), ("verify", ("text",))):
        for x in d.get(coll) or []:
            where = f"{coll} {x.get('id')}"
            claim(coll, x.get("id"), where)
            for f in fields:
                c.ltext(where, f, x.get(f), langs)
    for x in d.get("stack_actions") or []:
        c.enum(f"stack_actions {x.get('id')}", "action", x.get("action"), "action")
    for x in d.get("deadlines") or []:
        where = f"deadline {x.get('id')}"
        claim("deadline", x.get("id"), where)
        c.ltext(where, "event", x.get("event"), langs)
        c.enum(where, "status", x.get("status"), "dl_status")
        c.enum(where, "date_precision", x.get("date_precision"), "date_precision")
        c.date(where, "date", x.get("date"), x.get("date_precision"))
    for x in d.get("conflicts") or []:
        where = f"conflict {x.get('id')}"
        claim("conflict", x.get("id"), where)
        c.ltext(where, "subject", x.get("subject"), langs)
        c.ltext(where, "note", x.get("note"), langs)
        if len(x.get("values") or []) < 2:
            c.err(where, "a conflict needs at least two competing values")
    for g in d.get("glossary") or []:
        c.ltext(f"glossary {g.get('term')}", "definition", g.get("definition"), langs)

    # ---- cross references ----
    def refs(where, ids, pool, what):
        for i in ids or []:
            if i not in pool:
                c.err(where, f"{what} {i!r} does not exist")

    for s in d.get("sections") or []:
        for it in s.get("items") or []:
            refs(f"item {it.get('id')}", it.get("source_ids"), sources, "source_id")
            for m in it.get("metrics") or []:
                refs(f"item {it.get('id')} metric", [m.get("source_id")], sources, "source_id")
    for coll in ("highlights", "stack_actions", "checklist"):
        for x in d.get(coll) or []:
            refs(f"{coll} {x.get('id')}", x.get("item_ids"), items, "item_id")
    for x in d.get("deadlines") or []:
        refs(f"deadline {x.get('id')}", x.get("source_ids"), sources, "source_id")
    for x in d.get("conflicts") or []:
        refs(f"conflict {x.get('id')}", [v.get("source_id") for v in x.get("values") or []],
             sources, "source_id")

    cited = set()
    for s in d.get("sections") or []:
        for it in s.get("items") or []:
            cited |= set(it.get("source_ids") or [])
            cited |= {m.get("source_id") for m in it.get("metrics") or []}
    for x in d.get("deadlines") or []:
        cited |= set(x.get("source_ids") or [])
    for x in d.get("conflicts") or []:
        cited |= {v.get("source_id") for v in x.get("values") or []}
    for sid in sorted(set(sources) - cited):
        c.warn(f"source {sid}", "listed but never cited by any item")

    if not (d.get("sections") or []):
        c.err("root", "no sections")
    if not (d.get("sources") or []):
        c.err("root", "no sources")
    return c


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true", help="emit the findings as JSON")
    a = ap.parse_args()

    text = pathlib.Path(a.path).read_text()
    try:
        d = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"validate_report: not valid JSON: {e}", file=sys.stderr)
        return 1

    c = validate(d)
    n_items = sum(len(s.get("items") or []) for s in d.get("sections") or [])
    if a.json:
        print(json.dumps({"errors": c.errors, "warnings": c.warnings,
                          "sections": len(d.get("sections") or []), "items": n_items,
                          "sources": len(d.get("sources") or [])}, ensure_ascii=False, indent=2))
    else:
        for e in c.errors:
            print("ERROR  " + e)
        for w in c.warnings:
            print("warn   " + w)
        print(f"\n{len(d.get('sections') or [])} sections / {n_items} items / "
              f"{len(d.get('sources') or [])} sources")
        print(f"{len(c.errors)} errors, {len(c.warnings)} warnings")
    return 1 if c.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
