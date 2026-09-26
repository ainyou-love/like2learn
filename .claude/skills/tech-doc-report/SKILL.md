---
name: tech-doc-report
description: |-
  Use for the periodic technical-intelligence report: research what changed in a tech area over a time window and publish it as a bilingual VI/EN single-file HTML page — sourced, filterable, phone-first, dataset embedded so the next period swaps only data.

  Trigger on:
  • "what shipped/changed/happened in X" over a week, month, quarter, "since June", "last 30 days", "the last six months" — releases, breaking changes, deprecations, pricing shifts, spec and protocol movement, tech radar across a stack, báo cáo tech. A research or deep-dive request that spans a period and a tech area belongs here however it is phrased.
  • cadence requests with the noun dropped: "the weekly one", "this month's again", "end of quarter, same as before". An unstated subject, stack or window is something to ask about, never a reason to skip.
  • any change to an existing report page in resources/topics/tech-reports/ (files like 26-06-30--ai-dev--….html): rebuild or re-render it after a component or CSS fix, or edit one label, colour or item in place — the page carries an edit protocol for exactly that.

  Not for: an explainer page from content already in hand, a video-transcript notebook, one named source to go read, or analysis that stays in chat.
---

# tech-doc-report

Two steps that stay apart on purpose:

```
research   ->  report.json   bilingual, every claim carrying its sources
build      ->  report.html   one file, dataset embedded, editable by region
```

Keeping them apart is what makes the next period cheap. Re-running research for
October means producing a new JSON and rebuilding — never rebuilding the page.
And because the two languages live in the data, the page only chooses which one
to show; adding a language never touches an item.

Output goes to `resources/topics/tech-reports/`, named
`{yy-mm-dd}--{report-what}--{from}_{to}.html`, e.g.
`26-09-26--ai-dev--2026-06-27_2026-09-26.html`. `build_report.py --out-dir`
derives that name itself, so it cannot drift.

## What is already built

The components are the asset; the page is output. Do not write HTML, CSS or
JS from scratch for a report — a fix belongs in `assets/`, where every future
report inherits it.

| path | what it is |
|---|---|
| `assets/shell.html` | the page skeleton, with the manifest and edit protocol |
| `assets/tokens.css` `base.css` | colour tokens for both themes, element defaults |
| `assets/atoms.css` `atoms.js` | LAYER 2 — 17 atoms, pure `(props, ctx) -> string` |
| `assets/biz.css` `biz.js` | LAYER 3 — 14 business components |
| `assets/layout.css` `print.css` | mobile-first layout, then the print sheet |
| `assets/i18n.js` | every UI string and enum label, one key per line |
| `assets/app-state.js` `app-view.js` `app-events.js` | LAYER 4 — dataset and indexes; filters, router and render; events and boot |
| `scripts/resolve_window.py` | a preset or spoken phrase to absolute dates |
| `scripts/merge_sections.py` | fragments to one dataset; collapses duplicate sources |
| `scripts/validate_report.py` | the schema, enforced |
| `scripts/build_report.py` | assets + dataset to the deliverable |
| `scripts/test_report.js` | jsdom acceptance suite; 80 checks |
| `references/sample-report.json` | a small valid dataset, for testing components |

**Read `references/schema.md` before writing any data**, and
`references/component-catalog.md` before touching any component. They carry
detail this file deliberately does not repeat.

## Procedure

Work in a scratch directory. Only the finished HTML lands in the project.

### 0 — Agree the scope

Three things decide everything downstream, and guessing any of them wastes a
fourteen-agent research run:

- **Subject** → which preset. `references/presets/ai-dev.md` is the default.
  A different subject needs its own preset file; `presets/_template.md` says
  how, and it is one markdown file, not code.
- **Window** → `today`, `last_7_days`, `this_month`, `last_30_days`,
  `last_3_months`, `last_6_months`, `this_year`, or `YYYY-MM-DD..YYYY-MM-DD`.
  Spoken forms work too — "last week", "3 months", "quarter".
- **Stack** → confirm it, do not inherit it. It drives `stack_relevance`, the
  stack filter and the whole `stack_actions` block.

Use `AskUserQuestion` when any of these is unstated.

### 1 — Resolve the window from the clock

```bash
python3 <skill>/scripts/resolve_window.py last_3_months
```

Prints absolute `from` / `to`, the day count, the depth the window implies,
and `items` — how many items that depth means per topic.
Pass those absolute dates into every agent brief. An agent that recomputes
"last 3 months" from its own sense of today researches a different quarter, and
nothing downstream notices.

### 2 — Dispatch one agent per topic, in parallel

Build each brief from the template in `references/research-brief.md`,
substituting the topic, the preset's lens and must-sweep list, the absolute
window, the stack, the `items` range and the output path. Send them all in one
message so they run concurrently.

Each agent writes `<scratch>/frags/section-<ID>.json` and namespaces its own
source ids (`H-S01`) — they cannot see each other, so they cannot agree on
global numbering. That is the merge's job, not theirs. Do not try to make them
coordinate.

### 2b — Sweep each topic for what the first pass dropped

Once every fragment is back, dispatch one sweep agent per topic, in parallel,
from the sweep template in `references/research-brief.md`. Each gets its
topic's already-found items and the preset's must-sweep list, searches only for
what that list names, and appends to its own fragment.

A topic agent reliably finds the headline release and then stops. The
security-only patch on an older branch, the SDK release that broke downstream
installs and the platform change enforced next month are the items it drops,
and they are the ones the reader acts on. A sweep that adds nothing is a
normal result.

### 3 — Write the cross-topic blocks yourself

Read the fragments, then write `<scratch>/frags/shared.json`: `meta`,
`highlights`, `stack_actions`, `deadlines`, `checklist`, `verify`, `conflicts`,
`glossary`. These are judgements across topics — an agent that saw one topic
cannot rank the week's three most important items. `research-brief.md` has the
per-block table and the one ordering constraint that bites (`conflicts` and
source-id renumbering).

### 4 — Merge, then validate

```bash
python3 <skill>/scripts/merge_sections.py --dir <scratch>/frags --out <scratch>/report.json
python3 <skill>/scripts/validate_report.py <scratch>/report.json
```

The merge collapses the same URL seen by two agents and renumbers to `S001..`,
rewriting every reference. Validation must reach **0 errors** before you build.
Warnings are worth reading; they are usually a real inconsistency in a
fragment, not noise.

Fix errors in the data. Do not fix them in the page.

### 5 — Build

```bash
python3 <skill>/scripts/build_report.py --data <scratch>/report.json \
    --out-dir <project>/resources/topics/tech-reports --slug ai-dev
```

To re-render an existing report against improved components, with no source
JSON on disk:

```bash
python3 <skill>/scripts/build_report.py --from-html <page>.html --out <page>.html
```

### 6 — Run the page, do not just read it

```bash
npm install jsdom          # once, in any scratch directory
node <skill>/scripts/test_report.js <page>.html <scratch>/report.json
```

A citation pointing at a source the merge dropped, a filter that matches
nothing, a YouTube facade that loaded its iframe on open, a language toggle
that leaves half the page behind — none of these are visible by reading the
HTML, and all of them fail here. Ship only on a green run.

For layout, screenshot it at a real phone viewport. jsdom has no layout engine,
so the suite can only read the stylesheet:

```bash
printf '%s' '<!doctype html><meta charset=utf-8><style>html,body{margin:0}
iframe{width:390px;height:3000px;border:0}</style><iframe src="PAGE.html"></iframe>' > host.html
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new \
  --disable-gpu --hide-scrollbars --allow-file-access-from-files \
  --virtual-time-budget=3000 --screenshot=m.png "file://$PWD/host.html"
```

The iframe is what gives the page a genuine 390px viewport — `--window-size` is
clamped on macOS and silently renders at ~485px, which makes a broken mobile
layout look fine.

### 7 — Report back

Give the path, the counts per section, the source count, any validation
warnings you accepted and why, and the suite result.

## Mobile is the default, not the fallback

Reports get read on a phone, between other things, and the first question there
is "what do I have to act on" — not "where is the sidebar". So the base
stylesheet **is** the phone layout and `min-width` queries are enhancements.
Writing a desktop layout and rescuing it with `max-width` queries is the one
change most likely to quietly ruin this page.

What that already means, and what to preserve:

- The topbar is two rows on a phone — controls, then a full-width search. A
  text field wedged between four buttons at 360px is too narrow to read what
  you typed.
- The search input is exactly 16px. Anything smaller and iOS Safari zooms the
  page on focus, and the reader is then panning a zoomed report.
- Tap targets are at least 44px until 900px, where they shrink for a pointer.
- Tables are not tables on a phone: each row stacks into labelled lines, so the
  column that matters is never the one behind a horizontal scroll.
- The page itself never scrolls sideways. Wide things scroll inside their own
  container.
- `env(safe-area-inset-*)` on the edges, for notched screens.

The suite asserts each of these. Screenshot anyway — an assertion can only
check the rule is present, not that the result reads well.

## Traps that have actually cost time

**The dataset is last in the file, so the script runs before it exists.** That
placement is deliberate — it lets an agent read the components without loading
the JSON into context — and the cost is that initialisation has to wait for
`DOMContentLoaded`. `app-state.js` reads it in `readData()`, which
`app-events.js` calls from `start()`. Anything new that reads `DATA` at top
level will silently get `{}`.

**`history.replaceState` throws on `file://` in some engines.** The page falls
back to assigning the hash. Keep the fallback; without it every deep link and
every tab click dies on a page opened from disk.

**Never run `build_report.py` to see what it does.** It writes its output file.
Read it instead.

**Edit by marker, and check the anchor matches exactly once.** An anchor
matching twice corrupts the file silently; zero matches fails loudly, which is
the outcome you want. `build_report.py` enforces this for its own tokens and
refuses a duplicated region name — which is also why a region name must never
appear in prose inside the page.

**A structural fix found in a built page belongs back in `assets/`.** Otherwise
the next report ships the same bug, and the two diverge until the components are
no longer the source of anything.

**WebSearch has a per-session budget, shared by every agent.** One
fourteen-topic run used most of a 200-call budget; a second run in the same
session found it spent and fell back to fetching pages directly, which cannot
discover what it does not already know the address of. Start a report in a
fresh session, and when agents say the budget is gone, point them at `gh`, the
PyPI and npm registry APIs and the Hacker News Algolia API rather than letting
them guess.

**An empty section is a finding.** `status: "empty"` renders honestly. Padding
a thin topic costs the reader the one thing the report is for — knowing where
to look.

**Vendor self-benchmarks are `VENDOR_CLAIM`.** However official the page they
appear on. The dashed border exists for exactly this.

**Sanitize before shipping.** Absolute home directories, usernames and
employer-identifying strings do not belong on a page that may be shared.
Rewrite `/Users/<name>/` as `~/`; the suite fails the build if one survives.

## Reference files

| file | read it when |
|---|---|
| `references/schema.md` | before writing any data — field classes, every type, what validation refuses |
| `references/research-brief.md` | dispatching the agents, running the sweep pass, or writing `shared.json` |
| `references/component-catalog.md` | before touching a component, adding a component type, or editing a built page |
| `references/presets/ai-dev.md` | the default subject: the fourteen topics and their briefs |
| `references/presets/_template.md` | the subject is not AI-assisted development |
| `references/sample-report.json` | testing a component change without running research |
