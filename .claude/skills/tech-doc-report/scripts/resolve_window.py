#!/usr/bin/env python3
"""Turn a time-window preset into an absolute date range, from the clock.

The window is the one fact the whole report is filtered on, and a model's idea
of "today" is whatever was true when it was trained. Ask the machine.

    resolve_window.py last_3_months
    resolve_window.py custom --from 2026-01-01 --to 2026-03-31

Prints JSON: preset, from, to, days, the depth the window implies, and the
item count that depth means.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys

PRESETS = ("today", "last_7_days", "this_month", "last_30_days", "last_3_months",
           "last_6_months", "this_year", "custom")


def resolve(preset: str, frm: str, to: str, today: dt.date):
    if preset == "custom":
        if not (frm and to):
            sys.exit("resolve_window: custom needs --from and --to")
        a, b = dt.date.fromisoformat(frm), dt.date.fromisoformat(to)
    elif preset == "today":
        a = b = today
    elif preset == "last_7_days":
        a, b = today - dt.timedelta(days=6), today
    elif preset == "this_month":
        a, b = today.replace(day=1), today
    elif preset == "last_30_days":
        a, b = today - dt.timedelta(days=29), today
    elif preset == "last_3_months":
        a, b = today - dt.timedelta(days=91), today
    elif preset == "last_6_months":
        a, b = today - dt.timedelta(days=182), today
    elif preset == "this_year":
        a, b = today.replace(month=1, day=1), today
    else:
        sys.exit(f"resolve_window: unknown preset {preset!r}; one of {', '.join(PRESETS)}")
    if a > b:
        sys.exit("resolve_window: from is after to")
    return a, b


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("preset", nargs="?", default="last_30_days")
    ap.add_argument("--from", dest="frm", default="")
    ap.add_argument("--to", dest="to", default="")
    a = ap.parse_args()

    preset = a.preset.strip().lower().replace("-", "_").replace(" ", "_")
    # "3 months", "last week", "hôm nay" all mean something specific; map the
    # common spoken forms rather than making the caller learn the enum.
    alias = {"week": "last_7_days", "last_week": "last_7_days", "7_days": "last_7_days",
             "month": "last_30_days", "last_month": "last_30_days", "30_days": "last_30_days",
             "3_months": "last_3_months", "quarter": "last_3_months",
             "6_months": "last_6_months", "half_year": "last_6_months",
             "year": "this_year", "hom_nay": "today", "tuan_nay": "last_7_days"}
    preset = alias.get(preset, preset)
    if preset not in PRESETS and re.fullmatch(r"\d{4}-\d{2}-\d{2}\.\.\d{4}-\d{2}-\d{2}", a.preset):
        a.frm, a.to = a.preset.split("..")
        preset = "custom"

    today = dt.date.today()
    frm, to = resolve(preset, a.frm, a.to, today)
    days = (to - frm).days + 1
    depth = "brief" if days <= 1 else "standard" if days <= 31 else "deep"
    # A long window holds more that matters, not just bigger items: capping a
    # quarter at the monthly range drops the security releases and deadlines first.
    items = ("5-10 in total" if depth == "brief" else "2-4 per topic" if days <= 7
             else "3-8 per topic" if depth == "standard" else "5-12 per topic")
    print(json.dumps({"preset": preset, "from": frm.isoformat(), "to": to.isoformat(),
                      "days": days, "depth": depth, "items": items,
                      "today": today.isoformat()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
