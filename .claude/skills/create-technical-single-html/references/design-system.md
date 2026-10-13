# Design system

The look is an "engineering field report": editorial headings, quiet paper surfaces, and
colour that always means something. Everything below is already implemented in
`assets/shell.html`; this file explains the choices so a new page keeps them.

## Typography

| Role | Family | Why |
|---|---|---|
| Display (h1, h2) | Fraunces 500/700 | Editorial weight; tells the reader this is a document, not an app |
| Body | IBM Plex Sans 400–600 | Neutral, legible at 15.5px on phones |
| Labels, IDs, code, table headers | IBM Plex Mono | Marks anything the reader may copy or cross-reference |

Loaded from Google Fonts with system fallbacks, so the file still reads offline.

## Colour tokens

Declared on `:root` (light), redeclared under `:root[data-theme="dark"]`. Light is the default
for every reader, whatever their OS setting; dark appears only after the reader picks it with the
toggle, and that choice is remembered per page.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` / `--surface` | #f5f2ea / #fffdf8 | #0e1216 / #161d24 | page / cards |
| `--ink` / `--ink-2` / `--ink-3` | #1c1f24 … | #e8ecef … | text levels |
| `--accent` | #0d6e66 | #3fd0bf | links, recommended, active |
| `--ok` `--warn` `--bad` `--info` (+ `-soft`) | green / amber / red / blue | brighter variants | semantic only |

A grain overlay (SVG noise, 3–5% opacity) and soft shadows give depth. Radii ~10–16px.

## Semantic pills — never repurpose

| Class | Meaning |
|---|---|
| `p-ok` | confirmed, ready, OK |
| `p-warn` | partial, in progress, weak spot, open |
| `p-bad` | wrong, P0, blocking |
| `p-info` | proposed, reference, index |
| `p-acc` | recommended, request review |
| `p-mute` | neutral, existing, withdrawn |

Store badges (`.store s-pg / s-rd / s-pb / s-none`) label where data lives.
Column chips (`.col key / warn / bad`) mark identity, weak and wrong columns in schemas.

## Layout

- Sticky top bar (60px): menu toggle · brand + date · Report/Markdown tabs · theme toggle.
- Sidebar TOC 272px, sticky; at ≤900px it becomes a drawer with a scrim. A section's
  `toc_group` puts a small mono group heading above its entry (parts of a long post).
- Interface text (tabs, buttons, toasts) follows `meta.ui_lang`, defaulting to the page `lang`
  when `assets/ui-strings.json` has it — a Vietnamese post gets Vietnamese chrome.
- Content column max 1060px; 16px side gutters.
- Grids `g2` / `g3` collapse to one column at ≤820px.
- The page never scrolls sideways: tables live in `.tw` (scroll inside), diagrams in `.fig > .scroll`
  with `min-width:680px` on the SVG.

## Tables

Mono uppercase sticky headers, bold key column (`td.k`), group rows (`tr.grp`, inside `.mx`),
highlighted row or column (`.hl`, `td.c.sel`). Matrices use `.cy ✓ / .cp ~ / .cn ✗` chips with a
legend. Long technical names get a "What it does" column and a prefix legend.

## Diagrams (inline SVG)

- Colour only through classes: nodes `n-box n-new n-ok n-warn n-bad n-info`, lane `band`,
  text `t t-s t-m t-h t-acc t-ok t-warn t-bad` (+ `t-b` bold), wires `w w-acc w-dash w-ok w-warn
  w-bad ax`. The theme switch then needs no SVG edits. A small diagram that should shrink on
  phones instead of scrolling sets `fit: true` on its `figure` block.
- `role="img"` + `<title>` stating the takeaway; a `figcaption` stating the conclusion.
- Unique `<marker>` id per SVG (two SVGs sharing `id="ar"` break arrowheads in some browsers).
- One idea per diagram. Shapes that worked:
  | Shape | For |
  |---|---|
  | Phase / hand-off flow with two bands | scope: what exists vs what is new |
  | Swimlanes per wave / owner | delivery order, responsibilities |
  | Entity boxes (existing grey, new accent) with FK lines | data model |
  | Lanes per table with state pills | state machines, lifecycle |
  | Hub with satellites | boundaries with neighbouring systems |
  | Log-scale ladder | scale thresholds — compute x = x0 + w·log10(N/N0), never eyeball |
  | Mini timeline inside a finding's Example | timing bugs |
- After building, look at each diagram: labels must not overlap, arrows must land on boxes.

## Motion and accessibility

Hero stats rise in with staggered delays; the signal line draws once. Everything respects
`prefers-reduced-motion`. Focus rings are visible; tabs use `aria-selected`, the menu
`aria-expanded`, filters `aria-pressed`, the active TOC link `aria-current`, the toast
`role="status"`. Print hides chrome.

## Content blocks beyond the review set

| Block | Look | For |
|---|---|---|
| `md` | prose column capped at 76ch; tables and code boxes inside it run full width | running text |
| `steps` | numbered cards in an auto-fit grid, optional ↺ loop line | ordered flows |
| `kv` | receipt sheet, dashed row rules, totals row | one object's fields |
| `tags` | tiles with a coloured left bar + legend dots | values with a status |
| `callout` | `note` (accent), `warn` (amber), `key` (ink) with an optional mono title; title alone = a label | the one point not to miss |
| `video` | 16:9 rounded frame, lazy YouTube embed, caption line ending in a Watch-on-YouTube link | talks and demos the post is about (the link is the fallback when the embed can't play, e.g. from `file://`) |

`cards`, `steps`, `kv`, `tags` and `table` take a `note` (small caption under the block) and an `ascii`
twin that replaces their default Markdown — use it when the original had a text diagram.
