# Running the research

The research step produces one JSON fragment per topic, in parallel, and the
orchestrator stitches them. This file holds the brief you hand each agent and
the rules you keep for yourself.

## Contents

- [Why one agent per topic](#why-one-agent-per-topic)
- [The per-topic brief](#the-per-topic-brief)
- [The sweep pass](#the-sweep-pass)
- [What the orchestrator writes](#what-the-orchestrator-writes)
- [Research rules worth restating](#research-rules-worth-restating)

## Why one agent per topic

A topic is a self-contained search job: different queries, different sources,
no shared state with its neighbours. Running them in one context means every
search result for every topic lands in the same window, and by topic ten the
early evidence has been pushed out. Running them as separate agents keeps each
one's search noise where it belongs and lets fourteen topics take about as
long as one.

The cost is that no agent can see the others' sources, so none of them can
assign a global source number. That is the whole reason each agent namespaces
its own ids — `H-S01`, `H-S02` — and `scripts/merge_sections.py` does the one
job that genuinely needs the whole picture: collapse the same URL seen by two
agents, renumber to `S001..`, and rewrite every reference.

Do not try to make the agents coordinate. Let them namespace, and merge.

## The per-topic brief

Substitute the bracketed values; the item range is the `items` value
`resolve_window.py` printed. Send this as the entire prompt — the agent has
no other context, which is the point.

```
You are a senior engineering research analyst. You value operational truth over
hype. Your output is a machine-readable JSON fragment, not prose.

# YOUR TOPIC
  id:    [A]
  name:  [Sources & people]
  brief: [what this topic covers, from the preset file]

# LENS
  [the preset's lens paragraph, verbatim]

# MUST SWEEP
  Before you finish, check this topic for each of these. They are what a first
  pass drops once it has a few big items, and the reader can least afford to
  miss them:
  [the preset's must-sweep list, verbatim]

# WINDOW
  [2026-06-27] to [2026-09-26]   (absolute; already resolved -- do not recompute)
  Only include what was published or released inside this range. An older item
  may appear only if it is still the canonical reference AND something relevant
  changed inside the range; set older_context: true on it.

# READER
  stack:     [Postgres, Python, TypeScript, Next.js, React Native/Expo]
  depth:     [deep]  -> [5-12 per topic]
  languages: [vi, en]   both required in every localized field

# HOW TO SEARCH
- Search this topic only. Put the year or month in queries when recency matters.
- For what shipped, prefer primary sources: official blogs and changelogs,
  release notes, GitHub repos, PEPs and RFCs, security-lab write-ups, papers.
- For what practitioners adopt, follow and abandon, the community is the
  primary source: Reddit, Hacker News, Discord, podcasts, YouTube, newsletters,
  trending pages. Cite them (source_type "community" or "video", trust "low" or
  "medium") and keep the claim truth: "UNVERIFIED" until a primary source or a
  second independent community backs it. Leaving them out does not make the
  report more careful; it makes it describe the vendors' quarter instead of the
  practitioners'.
- A guide, channel or repo that started before the window but is still the
  canonical reference may appear when something new happened in it inside the
  window. Set older_context: true.
- Use listicles and vendor comparison pages only to find leads, then verify
  against a primary source. When a vendor ranks or benchmarks itself, the item
  is truth: "VENDOR_CLAIM".
- Never invent a source, URL, date, version or number. If you cannot verify
  something, set truth: "UNVERIFIED" or leave it out.
- Keep quotes under 15 words. Paraphrase everything else.
- A recorded talk or conference video is a legitimate source: source_type
  "video", and the page will embed the player under the item that cites it.
- If two sources disagree on a number, do NOT pick one. Report both in
  disagreements[] (below) and let the orchestrator record the conflict.
- If nothing significant happened in this topic in this window, say so:
  status "empty" and an empty items array. That is a real finding. Do not pad.

# FIELD CLASSES
Read [absolute path to references/schema.md] before you write anything. In
short: ids, URLs, dates, versions, numbers, names, commands and enum values are
neutral scalars; titles, headlines, bodies and notes are {"vi": ..., "en": ...}
objects with both keys non-empty. Never put a URL or a command inside a
localized field -- use links[] and commands[].

# SOURCE IDS
Number your sources [A]-S01, [A]-S02, ... Do not use bare S001; another agent
is using those right now. Reference them by that id from source_ids and
source_id.

# OUTPUT
Write exactly this shape to [absolute path]/section-[A].json and reply with
only the counts:

{
  "section": {
    "id": "[A]", "slug": "...", "order": [1],
    "title":   {"vi": "...", "en": "..."},
    "summary": {"vi": "...", "en": "..."},
    "status": "ok",
    "items": [ ...Item objects per the schema... ]
  },
  "sources": [ ...Source objects, ids namespaced as above... ],
  "disagreements": [
    {"subject": {"vi": "...", "en": "..."},
     "values": [{"value": "41,000", "source_id": "[A]-S01"},
                {"value": "63,500", "source_id": "[A]-S02"}],
     "note": {"vi": "...", "en": "..."}}
  ]
}

Pretty-printed, 2-space indent, UTF-8, strict JSON: no comments, no trailing
commas. Before writing, check: every id unique within this fragment; every
localized field has both languages non-empty; every item has at least one
source unless truth is "ASSUMPTION"; every date is YYYY-MM-DD or null with
date_precision "tbd".
```

## The sweep pass

The first pass of a topic agent finds the headline items and stops. What it
drops once it has a few items is predictable: the security-only release of an
older branch, the SDK whose breaking release broke someone else's install, the
platform change enforced next month. The sweep pass exists to look for exactly
those, with the first pass's findings in hand so it does not re-find them.

Dispatch one sweep agent per topic, all in one message, after every fragment is
back and before you write `shared.json`. Each edits only its own topic's
fragment, so they cannot collide on the file — but they can collide on the
finding. Sweeps run in parallel and cannot see each other's additions, so an
advisory for an auth library is just as findable from the web topic as from
the standards topic. Give every sweep the other fragments' item names, and
after they finish, drop any item two sweeps added under different ids. Send this as the entire prompt:

```
You are checking one research fragment for what it missed. You are not
re-researching the topic; the headline items are already found.

# TOPIC
  id: [H]   name: [Security & supply chain]
  brief: [the preset brief]
  window: [2026-06-27] to [2026-09-26]   (absolute; do not recompute)
  stack:  [Postgres, Python, TypeScript, Next.js, React Native/Expo]

# ALREADY FOUND IN THIS TOPIC
  [one line per item: id | name | version | date]

# ALREADY FOUND IN OTHER TOPICS
  [one line per item from every other fragment: id | name]

# LOOK FOR, AND ONLY FOR
  [the preset's must-sweep list, verbatim]

For each line of LOOK FOR, run searches aimed at this topic and this window.
Add an item only when it is inside the window, inside the brief above, not
already found under another name, and backed by a source you opened. The
LOOK FOR list says where to dig, not what the topic covers: a deadline that
belongs to no part of the brief is out of scope, however dated. If you find
something that belongs to another topic's brief and is not in the list above,
do not add it here: name it in your reply with the topic it belongs to. Adding nothing is a valid result —
say so rather than lowering the bar.

# OUTPUT
Edit [absolute path]/section-[H].json in place: append new items to
section.items and new sources to sources. Continue the numbering after the
highest existing ids ([H]-009, [H]-S15). Follow the same schema rules as the
fragment already does: read [absolute path to references/schema.md] first.
If an added item makes the section summary wrong, fix the summary.
Reply with one line per added item (id | name | why it was missing), then
one line per item you left for another topic (topic | name | source URL), or
"nothing missed".
```

Read the replies. An item the sweep added is often the one that belongs in
`highlights` or `deadlines`, precisely because nothing else surfaced it. Items
a sweep left for another topic are yours to place: add them to that fragment,
or leave them out if that topic already covers them.

## What the orchestrator writes

The agents own `sections` and `sources`. Everything else is a cross-topic
judgement and cannot be delegated to an agent that saw one topic — so write
`shared.json` yourself, after the fragments come back and you have read them:

```json
{
  "schema_version": "1.0",
  "meta": { ... },
  "highlights": [ ... ],
  "stack_actions": [ ... ],
  "deadlines": [ ... ],
  "checklist": [ ... ],
  "verify": [ ... ],
  "conflicts": [ ... ],
  "glossary": [ ... ]
}
```

Where each part comes from:

| block | how you build it |
|---|---|
| `meta` | the resolved window, the preset's topic list, the reader's stack, `generated_at` from the clock |
| `highlights` | the 3–6 items that would change what the reader does this week, ranked. Reference them by `item_ids` |
| `stack_actions` | one row per entry in `meta.stack` that anything touched. `ignore` with "nothing this window" is a useful row, not a wasted one |
| `deadlines` | dated things the reader has to plan around, from any topic |
| `checklist` | the ordered sequence of what to actually do, with the commands |
| `verify` | how the reader confirms each action landed |
| `conflicts` | promoted from the fragments' `disagreements[]`, with source ids **after** the merge renumbered them |
| `glossary` | terms kept in English inside Vietnamese text that a reader may not know |
| `data_quality_note` | inside `meta`: what this report could not establish |

**One event, one home.** A lens that asks every topic about agents means an
AGENTS.md change is findable from four topics and a Postgres security release
from two. Before writing `shared.json`, keep each event in the one topic whose
brief fits it best and drop the others; `highlights` can still point across
topics. `merge_sections.py` warns when items in different sections cite the
same page — read that list, it is usually right.

`conflicts` is the one block with an ordering constraint: the fragments'
`disagreements[]` carry namespaced source ids, and the merge rewrites ids only
inside `sections`, `deadlines` and `conflicts`. So either write `conflicts`
into `shared.json` using the namespaced ids before merging and let the merge
rewrite them, or write it after the merge using the final `S0nn` ids. Do not
mix the two.

## Research rules worth restating

**Depth follows the window.** `today` is 5–10 items in total, not per topic.
`last_7_days` is 2–4 per topic, up to a month is 3–8, and anything longer is
5–12. `scripts/resolve_window.py` prints the range as `items`; pass it through
rather than restating it. A quarter capped at the monthly range does not lose
its least important items, it loses its least prominent ones — and the
security-only patch and next month's enforced change are rarely prominent.

**An empty topic is a finding.** Padding a thin section costs the reader the
one thing the report is for: knowing where to look. The page renders
`status: "empty"` honestly.

**The window is resolved once, by the clock.** Run
`scripts/resolve_window.py` and pass the absolute dates into every brief. An
agent that recomputes "last 3 months" from its own sense of today will quietly
research a different quarter.

**Sources are per claim, not per topic.** An item with three source_ids is
usually one primary source and two that corroborate it. An item with one is
fine when that one is primary. An item with none is only legitimate when it is
explicitly your own inference, marked `ASSUMPTION` with a `confidence`.
