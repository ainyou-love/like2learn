#!/usr/bin/env python3
"""Sync resources/post_metadata.json with the HTML posts under resources/.

Usage:
  python3 _tools/sync_post_metadata.py
  python3 _tools/sync_post_metadata.py --set-category <key> "<category>"
  python3 _tools/sync_post_metadata.py --set-feature-img <key> "<path>"

Key: the post path relative to resources/ (NFC), e.g. "Custom-Post/01-tam-ly-hoc-ve-tien.html".
Value: {"subject", "description", "created_at", "categories", "feature_img"}.

subject and description come from the post's <title> and <meta name="description">; only the
<head> is read, in small chunks, so the body is never loaded. They are refreshed on every run:
edit the post's <head>, not the JSON. created_at is kept once set; a new entry takes the date
git first added the file (following renames), or the file's mtime when it is not committed yet.
Entries whose file is gone are dropped.

categories holds exactly one category, assigned by whoever adds the post (not derived from the
file) and kept across runs. Every run prints the categories in use with their post counts; reuse
one of those, and only add a new category when none fits.

feature_img is the post's lead image shown above the reader, "" when there is none. Like
categories it is assigned by hand and kept across runs; the path is relative to resources/,
e.g. "topics/others/apollo13-con-da-ve-dat-me.webp". Convention: keep it beside the post and
named after it (same name, .webp instead of .html), so a post's lead image is never mistaken for
gallery content and never lands in an album by accident. Convert with:
  cwebp -q 80 <source> -o resources/<post path minus .html>.webp
Pass an empty PATH to --set-feature-img to clear a post's lead image again.

Top-level keys that do not end in .html are settings rather than post entries, and are kept
across runs: set feature_image_enabled to false to stop the reader showing any lead image,
without clearing the per-post feature_img values.
"""
import argparse
import json
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RESOURCES = REPO / "resources"
OUT = RESOURCES / "post_metadata.json"
SETTINGS = {"feature_image_enabled": True}
CHUNK = 4096
NOTEBOOK_PREFIX = re.compile(r"^Sổ ghi chép\s*·?\s*No\.\s*\d+\s*[—·–-]\s*")
NOTEBOOK_SUFFIX = re.compile(r"\s*[—·–-]\s*Sổ ghi chép$")


class HeadParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title, self.description = "", ""
        self.in_title = self.done = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            a = dict(attrs)
            if (a.get("name") or "").lower() == "description" and not self.description:
                self.description = a.get("content") or ""
        elif tag == "body":
            self.done = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "head":
            self.done = True

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def clean(text):
    return re.sub(r"\s+", " ", text).strip()


def read_head(path):
    parser = HeadParser()
    with path.open(encoding="utf-8") as f:
        while not parser.done and (chunk := f.read(CHUNK)):
            parser.feed(chunk)
    subject = NOTEBOOK_SUFFIX.sub("", NOTEBOOK_PREFIX.sub("", clean(parser.title)))
    return subject, clean(parser.description)


def created_at(path):
    log = subprocess.run(
        ["git", "log", "--follow", "--diff-filter=A", "--format=%aI", "--", str(path)],
        cwd=REPO, capture_output=True, text=True,
    ).stdout.split()
    if log:
        return log[-1]
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds")


def main():
    ap = argparse.ArgumentParser(description="Sync resources/post_metadata.json with the posts under resources/.")
    ap.add_argument("--set-category", nargs=2, metavar=("KEY", "CATEGORY"),
                    help="assign the post's single category, then sync")
    ap.add_argument("--set-feature-img", nargs=2, metavar=("KEY", "PATH"),
                    help="assign the post's lead image (path relative to resources/, empty to clear), then sync")
    args = ap.parse_args()

    stored = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    old = {k: v for k, v in stored.items() if k.endswith(".html")}
    settings = {**SETTINGS, **{k: v for k, v in stored.items() if not k.endswith(".html")}}
    posts, missing = {}, []
    categorized = {k: v["categories"] for k, v in old.items() if v.get("categories")}
    featured = {k: v["feature_img"] for k, v in old.items() if v.get("feature_img")}
    if args.set_category:
        key, category = (unicodedata.normalize("NFC", a.strip()) for a in args.set_category)
        if not (RESOURCES / key).is_file():
            sys.exit(f"ERROR no post at resources/{key}")
        categorized[key] = [category]
    if args.set_feature_img:
        key, image = (unicodedata.normalize("NFC", a.strip()) for a in args.set_feature_img)
        if not (RESOURCES / key).is_file():
            sys.exit(f"ERROR no post at resources/{key}")
        if image and not (RESOURCES / image).is_file():
            sys.exit(f"ERROR no image at resources/{image}")
        if image:
            featured[key] = image
        else:
            featured.pop(key, None)
    for path in sorted(RESOURCES.rglob("*.html")):
        key = unicodedata.normalize("NFC", path.relative_to(RESOURCES).as_posix())
        subject, description = read_head(path)
        if not subject or not description:
            missing.append(key)
        posts[key] = {
            "subject": subject,
            "description": description,
            "created_at": old.get(key, {}).get("created_at") or created_at(path),
            "categories": categorized.get(key, []),
            "feature_img": featured.get(key, ""),
        }

    added = sorted(posts.keys() - old.keys())
    removed = sorted(old.keys() - posts.keys())
    changed = sorted(k for k in posts.keys() & old.keys() if posts[k] != old[k])
    new = {**settings, **posts}
    if new != stored:
        OUT.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for label, keys in [("added", added), ("updated", changed), ("removed", removed)]:
        for key in keys:
            print(f"{label}: {key}")
    for key in missing:
        print(f"WARN {key}: no <title> or <meta name=\"description\"> in <head>", file=sys.stderr)
    for key, meta in posts.items():
        if len(meta["categories"]) != 1:
            print(f"WARN {key}: needs exactly one category (--set-category)", file=sys.stderr)
        if meta["feature_img"] and not (RESOURCES / meta["feature_img"]).is_file():
            print(f"WARN {key}: feature_img not found at resources/{meta['feature_img']}", file=sys.stderr)
    counts = Counter(c for meta in posts.values() for c in meta["categories"])
    print("categories: " + (" · ".join(f"{c} ({n})" for c, n in counts.most_common()) or "none"))
    print("settings: " + " · ".join(f"{k}={json.dumps(v)}" for k, v in settings.items()))
    print(f"OK {OUT.relative_to(REPO)}: {len(posts)} posts ({len(added)} added, {len(changed)} updated, {len(removed)} removed)")


if __name__ == "__main__":
    main()
