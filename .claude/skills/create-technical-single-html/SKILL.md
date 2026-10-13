---
name: create-technical-single-html
description: >-
  Turn a technical review into one self-contained HTML report a reader can act on:
  a design review, architecture or database-design review, code/system verification,
  RFC or proposal assessment — anything with findings, decisions, options to compare,
  and questions for an owner. Produces a single .html with a review checklist, a
  "start here" guide, findings (What/Example/Value/Fix), decision cards with honest
  status, option comparisons with schemas and per-option state machines, hand-drawn
  SVG diagrams, a Report/Markdown tab pair with .md download, light/dark theme and a
  phone-friendly drawer menu. Use it whenever someone wants a review, assessment or
  decision document "as a single HTML page", "as a report I can send to the design
  owner", "like the review page we made", or asks to turn review notes / a review
  .md into a shareable page — even when they don't say "HTML report". Also use it for
  any page built from a post.json page spec (the ported posts under
  resources/topics/ai/, sources in _sources/): editing their content, re-rendering after
  a shell or block change, or porting another post to the same look. Not for a
  general explainer or learning page that should keep its own design (gen-tech-doc-html),
  a periodic what-changed tech report (tech-doc-report), markdown docs in a repo
  (create-doc), or web apps and dashboards.
---

# create-technical-single-html

Build one HTML file that a reader can open from disk, work through with a checklist, and act
on. The shell (CSS, layout, theme, tabs, menu, JS) and a library of content blocks are already
built; each page is a **`post.json` page spec** — data only — that `render.py` turns into the
finished page, Markdown tab included.

## What is already built

| Path | What it is |
|---|---|
| `assets/shell.html` | Page skeleton: all CSS, top bar, sidebar TOC, Report/Markdown panels, JS (atoms → components → workflows → events). Page tokens `__TITLE__ __BODY__ …`; interface text as `__UI:key__` |
| `assets/ui-strings.json` | Interface text per language (`en`, `vi`): tab names, buttons, toasts, checklist counter. Add a language here, never in the shell |
| `assets/components.json` | **Block registry.** For every block type: `purpose`, `use_when`, `required` and `optional` fields (with their format). Read it to pick blocks; `render.py` validates every block against it |
| `assets/blocks/<type>.j2` | One template per block, each with two macros: `html` (the page) and `md` (the Markdown tab). `_lib.j2` / `_fcard.j2` hold shared pieces |
| `assets/example/` | A worked review (`post.json`, `scope.svg`, `schema.sql`) — copy its shape — and `all-blocks.post.json`, a fixture that renders every block and the edge cases that broke before |
| `scripts/render.py` | `post.json` → body HTML + Markdown → `build.assemble()` |
| `scripts/build.py` | Fills the shell, generates the TOC, refuses on broken links, duplicate ids, leftover tokens, banned words or home paths. Still usable on its own with a hand-written body |

## Procedure

Work in a scratch directory; write the deliverable last.

**1 — Get the substance right.** For a review, follow the page order in
`references/content-rules.md` — checklist, start here, scope, requirements, decisions,
findings, current state, design options, open questions. For an explainer or a ported post,
keep the content's own outline. Thin content shows; fix it before styling.

**2 — Write `post.json`.** `meta` (title, brand, date, desc, lang, md_filename, storage_key;
optional ui_lang, sidebar_note, ban, strict_paths), `hero`, `sections` (each `id`, `title`,
optional `no`, `intro`, `toc_group`, and its `blocks`), `footer`. Pick each block from
`assets/components.json`: `md` for running prose, a structured block wherever the content has
a shape (`steps` for a sequence, `cards` for parallel items, `kv` for one object's fields,
`tags` for values with a status, `findings` / `fcards` for ID'd items, `checklist` for things to
work through). Keep section ids stable — the TOC and cross-links (`["L2", "#l2"]`) use them.
Use pills only with their fixed meanings (`references/design-system.md`).

**3 — Draw the diagrams.** Hand-write SVG with the theme classes only, one idea per diagram,
computed positions for scales; put each in its own `.svg` file referenced by a `figure` block's
`file`, with an `ascii` twin for the Markdown tab. Shapes that have worked are in
`references/design-system.md`.

**4 — Render.**

    python3 <skill>/scripts/render.py post.json --out <file>.html [--keep-dir build/]

It validates every block against the registry and writes only when every check passes; fix
what it reports rather than working around it. `--keep-dir` drops the intermediate body and
the generated Markdown for inspection. New standalone pages are named
`<YYYYMMDDHHMMSS>-<slug>.html` (timestamp from `date +%Y%m%d%H%M%S`); a re-render of an
existing page keeps its filename.

**5 — Run the page, don't just read it.** Open it in a browser (the built-in browser pane or
`agent-browser`) and check: no console errors; no page-level horizontal scroll at 390, 768 and
1280 px; tabs, theme toggle, drawer, filters and checklist work; every diagram looks right
(labels don't overlap, arrows land). Screenshots in some panes lag a step — scroll with
`behavior: "instant"`, wait, then capture, or verify with DOM checks.

**6 — Iterate from `post.json`.** Content changes go into `post.json` (or a figure's `.svg`),
then re-render; never hand-edit the built HTML. In this project a page's sources live in
`_sources/<path under resources/ without .html>/` (Jekyll skips `_` folders, so they never
deploy). When the output lands under `resources/`, file and register it with the
`page-structure` skill.

## Adding a block

When a shape recurs and nothing in the registry fits: add `assets/blocks/<type>.j2` with both
macros (HTML from the shell's classes only; Markdown that reads well as plain text), register
it in `components.json` with purpose, use_when and every field (`nested` for list items), add
CSS to the shell if needed, add it to `all-blocks.post.json`, and re-render both example files.
After any change to the shell, a template or `render.py`, re-render the fixture and every page
under `_sources/`. Use `raw` only for a true one-off.

## Judgement calls

- **Honest status.** "Confirmed" only for what a stakeholder confirmed. A reviewer's
  recommendation is "Request review", however confident. Readers act on these pills.
- **Examples carry the value.** A finding without a concrete scenario reads as opinion; one
  timeline or set of numbers makes it obvious why it matters.
- **Show each option before comparing.** Goal, how it works, strong, weak, schema, and how its
  state machine behaves — then the comparison matrix against the business questions.
- **Plain words.** Explain technical names in a "What it does" column; ban jargon the reader
  doesn't use (`meta.ban`).
- **One version.** If the reader only ever gets this page, it has no "v2", no "what changed".

## Reference files

| File | Read it when |
|---|---|
| `assets/components.json` | choosing blocks and filling their fields |
| `references/content-rules.md` | planning the content and the order of sections; writing findings, decisions, options |
| `references/design-system.md` | choosing pills, tables, diagram shapes; checking typography, colour and layout rules |
| `references/js-architecture.md` | adding an interactive feature or debugging the shell's behaviour |
