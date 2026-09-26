#!/usr/bin/env python3
"""Stitch the per-topic research fragments into one report JSON.

Parallel agents cannot agree on source numbering without talking to each other,
and making them talk would serialise the thing we parallelised. So each agent
namespaces its own ids -- "H-S03" -- and this script does the only job that
genuinely needs the whole picture: collapse sources that are the same URL seen
by two agents, renumber them S001.., and rewrite every reference.

Expected layout in --dir:

    shared.json        meta + highlights + stack_actions + deadlines
                       + checklist + verify + conflicts + glossary
    section-A.json     { "section": {...}, "sources": [...] }
    section-B.json     ...

    merge_sections.py --dir <dir> --out report.json
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

ORDER = ["schema_version", "meta", "highlights", "sections", "stack_actions",
         "deadlines", "checklist", "verify", "conflicts", "glossary", "sources"]


def canon(url: str) -> str:
    """Same page, different decoration: trailing slash, utm noise, #anchor.
    A YouTube watch URL keeps its v= though, or every video collapses into one."""
    u = str(url or "").strip().lower()
    u = u.split("#", 1)[0]
    if "?" in u:
        base, qs = u.split("?", 1)
        keep = [p for p in qs.split("&")
                if p and not re.match(r"(utm_|ref=|src=|si=|feature=)", p)]
        u = base + ("?" + "&".join(sorted(keep)) if keep else "")
    u = re.sub(r"^https?://(www\.)?", "", u)
    return u.rstrip("/")


def collect_source_refs(node, out: set):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "source_ids" and isinstance(v, list):
                out |= {x for x in v if isinstance(x, str)}
            elif k == "source_id" and isinstance(v, str):
                out.add(v)
            else:
                collect_source_refs(v, out)
    elif isinstance(node, list):
        for v in node:
            collect_source_refs(v, out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    d = pathlib.Path(a.dir).resolve()
    shared_f = d / "shared.json"
    if not shared_f.exists():
        sys.exit(f"merge_sections: missing {shared_f}")
    out = json.loads(shared_f.read_text())
    out.setdefault("schema_version", "1.0")

    frags = sorted(d.glob("section-*.json"))
    if not frags:
        sys.exit(f"merge_sections: no section-*.json in {d}")

    by_url: dict = {}
    remap: dict = {}
    sources: list = []
    sections: list = []
    notes: list = []

    for f in frags:
        frag = json.loads(f.read_text())
        sec = frag.get("section") or {}
        local = {s["id"]: s for s in frag.get("sources") or []}
        for sid, s in local.items():
            key = canon(s.get("url"))
            if not key:
                notes.append(f"{f.name}: source {sid} has no usable URL, dropped")
                continue
            if key in by_url:
                remap[sid] = by_url[key]["id"]
                # Keep the higher-trust description of the same page.
                rank = {"high": 3, "medium": 2, "low": 1}
                if rank.get(s.get("trust"), 0) > rank.get(by_url[key].get("trust"), 0):
                    keep_id = by_url[key]["id"]
                    by_url[key].update(s)
                    by_url[key]["id"] = keep_id
                by_url[key]["topics"] = sorted(set(by_url[key].get("topics") or []) |
                                               set(s.get("topics") or []))
            else:
                new = dict(s)
                new["id"] = "S%03d" % (len(sources) + 1)
                remap[sid] = new["id"]
                by_url[key] = new
                sources.append(new)
        sections.append(sec)

    def rewrite(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "source_ids" and isinstance(v, list):
                    node[k] = [remap.get(x, x) for x in v]
                elif k == "source_id" and isinstance(v, str):
                    node[k] = remap.get(v, v)
                else:
                    rewrite(v)
        elif isinstance(node, list):
            for v in node:
                rewrite(v)

    rewrite(sections)
    rewrite(out.get("deadlines"))
    rewrite(out.get("conflicts"))

    sections.sort(key=lambda s: (s.get("order", 99), str(s.get("id"))))
    out["sections"] = sections
    out["sources"] = sources

    dupe = [i for i, n in collections.Counter(
        [s.get("id") for s in sections] +
        [it.get("id") for s in sections for it in s.get("items") or []]).items() if n > 1]
    if dupe:
        notes.append("duplicate section/item ids across fragments: " + ", ".join(map(str, dupe)))

    # Two topics citing the same page for different items usually means both
    # reported one event. Validation cannot see this: the ids differ.
    cited_by: dict = collections.defaultdict(set)
    for s in sections:
        for it in s.get("items") or []:
            for sid in it.get("source_ids") or []:
                cited_by[sid].add((s.get("id"), it.get("id")))
    pairs = sorted({tuple(sorted(it for _, it in hits))
                    for hits in cited_by.values() if len({sec for sec, _ in hits}) > 1})
    if pairs:
        notes.append("items in different sections cite the same page -- same event twice? "
                     + "; ".join(" + ".join(p) for p in pairs))

    known = {s["id"] for s in sources}
    refs: set = set()
    collect_source_refs(out, refs)
    dangling = sorted(refs - known)
    if dangling:
        notes.append("references to sources no fragment supplied: " + ", ".join(dangling))

    ordered = {k: out[k] for k in ORDER if k in out}
    ordered.update({k: v for k, v in out.items() if k not in ordered})
    p = pathlib.Path(a.out).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n")

    n_items = sum(len(s.get("items") or []) for s in sections)
    print(f"merged: {p}")
    print(f"  {len(frags)} fragments -> {len(sections)} sections / {n_items} items")
    print(f"  {len(sources)} sources after collapsing duplicate URLs "
          f"({len(remap) - len(sources)} collapsed)")
    for n in notes:
        print("  warn: " + n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
