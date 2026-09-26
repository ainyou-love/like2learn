# The components, and how to add one

The page is assembled from files in `assets/`. They are the asset — the built
HTML is output. A fix belongs in `assets/`, where every future report inherits
it; patch a built page directly only for a one-off tweak to that one report.

## Contents

- [File order](#file-order)
- [Atoms](#atoms)
- [Business components](#business-components)
- [Adding a component type](#adding-a-component-type)
- [Adding a field to the schema](#adding-a-field-to-the-schema)
- [Editing a built page](#editing-a-built-page)

## File order

`build_report.py` concatenates in exactly this order. CSS order is the
cascade; JS order is definition-before-use.

```
CSS   tokens.css  base.css  atoms.css  biz.css  layout.css  print.css
JS    i18n.js  util.js  atoms.js  biz.js
      app-state.js  app-view.js  app-events.js
      shell.html wraps them, and the dataset goes last
```

Layering, and what each layer may touch:

| layer | file | may read |
|---|---|---|
| 1 data | the embedded JSON | — (never mutated) |
| 2 atoms | `atoms.js` | its props and `ctx` only. **Never `DATA`** |
| 3 business | `biz.js` | `DATA`, `ctx.state.idx`, and atoms |
| 4 app | `app-state.js` `app-view.js` `app-events.js` | everything; owns `state`, routing, events |

`ctx = { lang, t, L, esc, state, pass, counts }`. An atom that reaches for
`DATA` stops being reusable, which is the only thing atoms are for.

Two invariants the build script enforces, because breaking either one makes
every later grep-and-replace edit a coin flip:

- Every marker string is unique in the file.
- Every `@@BEGIN:X` has a matching `@@END:X`, and regions never nest.

That is also why region names must not appear in prose inside the page.

## Atoms

Pure functions, `(props, ctx) -> HTML string`. One CSS region and one JS
region per name.

| atom | what it does |
|---|---|
| `Text` | renders an `LText`; falls back to the other language and marks it rather than going blank |
| `Badge` | `variant` picks the I18N namespace: `action` \| `truth` \| `tag` \| `trust` \| `kind` \| `srctype` |
| `DateLabel` | ISO date honouring `date_precision`; `tbd` prints the localized "no date yet" |
| `CiteChip` | `[n]` with a hover card; click jumps to the source. An unknown id renders `[?]` and warns |
| `Cites` | a list of chips |
| `ExtLink` | http(s) only, `rel="noopener noreferrer"`, with a domain hint |
| `CopyButton` | Clipboard API with a textarea fallback, announced via `aria-live` |
| `CodeBlock` | `commands[]` with a copy button |
| `Metric` / `Metrics` | value + unit + label + citation, in an auto-fitting grid |
| `Card` | header plus collapsible body |
| `Table` | at most 4 columns; stacks into labelled rows on a phone |
| `Tabs` | accessible tablist |
| `FilterChip` | toggle with a live count |
| `Callout` | `info` \| `risk` \| `conflict` |
| `EmptyState` | an empty section, or zero filter results |
| `Icon` | the inline SVG set |
| `YouTube` | click-to-load facade; no request leaves the page until the reader asks |

Three of these encode decisions worth not undoing:

**`Badge` always prints its label.** Colour is a scanning aid, never the
carrier of meaning — `PATCH NGAY` has to survive greyscale, a colour-blind
reader, and a printout.

**`CiteChip` renders `[?]` for an unknown id.** A dropped citation that renders
as nothing is indistinguishable from a claim that never had one.

**`YouTube` creates no iframe until clicked.** Twelve embedded talks would
otherwise mean twelve third-party connections on open, on a phone, before the
reader has decided to watch anything.

## Business components

Read `DATA`, compose atoms.

| component | notes |
|---|---|
| `TopBar` | title, window, search, language, theme, print. Two rows on a phone |
| `Sidebar` | nav with live counts, then `FilterPanel`; a drawer under 900px |
| `FilterPanel` | AND across groups, OR within one. Counts ignore their own group, so a chip says "how many would I get", not "how many are left" |
| `HeroHighlights` | ranked highlights plus the `data_quality_note` callout |
| `StackActionsTable` | target, action, what, linked items |
| `DeadlineTimeline` | sorted by date; undated entries last, because they cannot be planned around |
| `SectionBlock` | title, summary, items; distinguishes "nothing happened" from "nothing matches your filter" |
| `ItemCard` | collapsed shows badges and headline; expanded shows body, metrics, commands, links, embedded video, citations |
| `ChecklistBlock` | per-viewer ticks in `localStorage` |
| `VerifyList` | text plus commands |
| `ConflictsPanel` | competing values with their sources, side by side |
| `GlossaryBlock` | neutral term, localized definition |
| `SourcesTab` | grouped by topic / type / trust, with back-links to the citing items |
| `JsonTab` | the original embedded text, collapsible, copy and download |

`ItemCard` keeps its body in the DOM and merely hides it. That is what lets the
print stylesheet expand every item and lets the browser's own find-in-page
reach a collapsed one — both of which break if collapsed content is simply not
rendered.

## Adding a component type

When a report needs a shape none of these carry — a comparison matrix, a
dependency graph, a pricing table — add it rather than bending `ItemCard`. Five
edits, all at markers, no full-file reads:

1. **CSS** — insert a `@@BEGIN:CSS:BIZ:<Name>` … `@@END:CSS:BIZ:<Name>` region
   before `@@SLOT:CSS_BIZ` in `assets/biz.css`. Mobile-first: the base rules
   are the phone, `min-width` queries are the enhancement.
2. **JS** — insert `@@BEGIN:JS:BIZ:<Name>` … `@@END:JS:BIZ:<Name>` before
   `@@SLOT:JS_BIZ` in `assets/biz.js`.
3. **I18N** — add its labels before `@@SLOT:I18N_KEYS` in `assets/i18n.js`,
   one key per line, both languages.
4. **Render** — call it from `render()`, in `JS:APP:RENDER`
   (`assets/app-view.js`). A new click target goes in `JS:APP:EVENTS`
   (`assets/app-events.js`), on the existing delegated handler — never a
   fresh `addEventListener` per element, which would not survive a re-render.
5. **Test** — add an assertion to `scripts/test_report.js` that fails if it
   stops rendering.

An atom instead of a business component: same steps, `ATOM` in place of `BIZ`,
`@@SLOT:CSS_ATOMS` and `@@SLOT:JS_ATOMS`, and it must not read `DATA`.

Then update the table above, so the next reader finds it without grepping.

## Adding a field to the schema

In order, or the pipeline breaks in the middle:

1. `references/schema.md` — document it, including its field class.
2. `scripts/validate_report.py` — validate it. An undocumented, unvalidated
   field is one an agent will populate inconsistently across fourteen parallel
   runs.
3. `references/research-brief.md` — tell the agents to produce it.
4. `assets/biz.js` — render it.
5. `references/sample-report.json` — add it to the fixture, so the acceptance
   suite exercises it.

## Editing a built page

The built page carries a `MANIFEST` and an `EDIT-PROTOCOL` comment at the top
so that an agent asked to change one label does not read 2000 lines to find it.

| the ask | mode | how to find it |
|---|---|---|
| change a label | REPLACE | `grep -n '"tab.json"'` — do not read the file |
| change the accent colour | REPLACE | `grep -n -- '--accent'` |
| fix item H-001's text | READ-REGION | `grep -n '"id": "H-001"'` |
| add a source | INSERT | `grep -n '"sources"'`, append to the array |
| add an atom | INSERT ×2 | `@@SLOT:CSS_ATOMS`, `@@SLOT:JS_ATOMS` |
| change what ItemCard shows | READ-REGION | `grep -n '@@BEGIN:JS:BIZ:ItemCard'` |
| swap in a new period's data | REPLACE region | the `DATA` region at the end |
| add a tab | READ-FULL | it touches shell, tabs, render and I18N |

Never navigate by line number; it changes on the next edit. Navigate by marker
or by key, and check the anchor matches exactly once — an anchor matching twice
corrupts the file silently, while one matching zero times fails loudly, which
is the outcome you want.

A structural fix found this way belongs back in `assets/`, or the next report
ships the same bug.
