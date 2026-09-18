# Prompt: Build a self-contained bilingual document site

A reusable brief for producing a single-file HTML document like `typesafe-jev-brief-v3.html`:
one file, two languages, two views, three depth levels, a sidebar, and inline diagram
components — with a layered architecture that keeps content authored exactly once.

Paste this whole file as the prompt, then add a short task line describing the subject.

---

## 0. Task line template

> Build a single self-contained HTML document about **<subject>**.
> Languages: **<VI/EN>**. Depth levels: **<names>**. Ship it as one file, no build step,
> no external assets beyond Google Fonts.
> Follow the architecture, content model, and checklists in this brief.

---

## 1. Non-negotiables

| Rule | Why |
|---|---|
| One HTML file, self-contained | It must open from disk with no server and survive being emailed |
| Content authored **once** per language | Any second copy of the same prose will drift within two edits |
| No browser storage for content state | Per-viewer conveniences only; wrap in try/catch |
| Only Google Fonts as an external asset | Everything else is inlined; give every font a real fallback stack |
| Works with JavaScript in a hostile environment | No `matchMedia`, no `localStorage`, no clipboard API assumed |

---

## 2. Layer architecture

Three layers in one `<script>`, separated by banner comments, in this order. A lower layer
must never reach upward.

```
LAYER 1 · DATA          no DOM, no logic
  STATE     mutable view state: { lang, view, depth, nav }
  I18N      UI chrome strings ONLY — never prose
  SRC       the single source of truth: one markdown document per language
  CUT       string/regex markers the depth slicer uses
  FIG       figure payloads keyed by the directive id used in the markdown

LAYER 2 · COMPONENTS    pure functions: data in, DOM out; must not read STATE
  el / esc / inline / withTag      primitives
  BLOCK   { h, p, ul, ol, table, code, quote, hr, details }
  FIGURE  { one renderer per figure `type` }
  MD      { parse(src) -> blocks, render(blocks, lang) -> DocumentFragment }

LAYER 3 · LOGIC         the only layer that touches STATE
  slice(depth) -> sections(front | body | footer) -> MD.parse -> MD.render -> DOM
  controls: setLang / setView / setDepth / setNav / copy
  scrollspy, table of contents, keyboard and resize handling
```

**The test for correct layering:** you can delete Layer 3 and still unit-test every component
by calling it with a literal object.

---

## 3. Content model

### 3.1 Markdown is the source; HTML is derived

Put each language's full document in `<script type="text/plain" id="src-xx">`.

Never store prose in JavaScript template literals. Escaped backticks inside `String.raw`
keep their backslashes and appear in the output. A `text/plain` script block needs no
escaping at all — only assert the content contains no `</script`.

### 3.2 Document shape

The markdown splits on its outer horizontal rules into three regions, and each region
feeds a different part of the page:

```
# <document title>                  ← markdown-only, not rendered
> Part 1 — <one line>               ← hero lede, one cuttable line per part
> Part 2 — <one line>
> Part 3 — <one line>
---
<body: all parts, separated by --->  ← the document view
---
<footer paragraph 1>                 ← page footer, one paragraph per note
<footer paragraph 2>
```

Because the lede lines and footer paragraphs live in the same sliced text as the body,
**depth slicing updates all three at once**. Anything you keep outside the markdown —
in `I18N` — must be genuinely depth-independent, or it will fall out of sync.

### 3.3 Layout directives

Region markers let one markdown source drive two very different renderings:

```
@fig:<id>
    <ASCII fallback used by the markdown view>
@endfig

@box:<css-class>
...markdown...
@endbox
```

- Document view: `@fig:` renders `FIG[id]` through its component; the ASCII body is skipped.
- Markdown view: directive lines are stripped; the ASCII body remains.

This is how a figure's labels stay bilingual without duplicating its markup: the prose
lives in the markdown, the figure data lives once in `FIG` with a `vi` and an `en` payload.

### 3.4 Depth slicing

Slice deeper parts first so the footer marker stays findable:

```js
if (depth < 3) { drop part 3; drop its lede line; drop its footer note }
if (depth < 2) { drop part 2; drop its lede line; drop its footer note }
```

Cut a part from the rule **before** its heading to the rule **before** the footer marker.
Give every removable sentence its own line or its own paragraph at authoring time —
retro-fitting a cut into a mid-paragraph clause always leaves a stump.

---

## 4. Markdown subset to support

Implement exactly this, no more:

`# ## ### ####` headings · paragraphs with two-space continuation · `- ` and `1. ` lists ·
`| a | b |` tables with a `|---|` separator row · `> ` blockquote · four-space indented code ·
`---` rule · raw `<details>` / `<summary>` passthrough · the directives above.

Inline: `` `code` ``, `**bold**`, `*em*`. Protect code spans **before** escaping, restore after.

Two parser details that will bite:

1. **Indented code blocks separated by blank lines are one block.** Consume blanks while the
   next non-blank line is still indented, then trim back to the last indented line.
2. **A leading `[TAG]`** becomes a semantic chip. Map the tag text to a class by keyword, and
   require the tag to be uppercase so ordinary bracketed prose is untouched.

Mapping headings to the page: `#` → `h2` with an eyebrow span when it matches
`^(PART|PHẦN) \d+ — `; `##` → `h3`; `###` → `h4`.

---

## 5. Controls

Four independent controls, all routed through one `render()`:

| Control | Values | Notes |
|---|---|---|
| Language | vi / en | Rebuilds document and table of contents |
| View | Document / Markdown | Toggle with the `hidden` attribute |
| Depth | 1..N, cumulative | A `<select>`, not buttons — native picker on mobile |
| Sidebar | open / closed | Open by default on wide screens only |

**Single render path.** Every control calls the same function. The moment two controls have
separate update paths, some combination of them will render an inconsistent page.

**Build the table of contents from the rendered DOM,** not from a hand-written list. Assign
ids during the walk. Sliced-away parts are then absent automatically — no filtering needed.

---

## 6. Responsive and accessibility

```
≥1180px   sidebar pinned open, body gets padding-left, content shifts
<1180px   sidebar is an off-canvas drawer with a scrim
          closes on: link click, scrim click, Escape
Markdown  sidebar button hidden, sidebar forced closed (no anchors to jump to)
```

Required regardless of breakpoint:

- `scroll-margin-top` on every heading, or anchors land under the sticky bar
- `height: 100dvh` not `100vh` for the drawer — Safari's address bar eats the difference
- Wide content (tables, code, diagrams) scrolls inside its own `overflow-x: auto` container
  so the page body never scrolls sideways
- Visible keyboard focus, `aria-pressed` on toggles, `aria-expanded` on the drawer button
- `@media (prefers-reduced-motion: reduce)` disables transitions
- Colour tokens defined three times: `:root`, `@media (prefers-color-scheme: dark)` guarded as
  `:root:not([data-theme="light"])`, and `:root[data-theme="dark"]`

---

## 7. Design

Ground the palette and type in the subject, not in a template.

- **Two families at most.** Give them clearly different jobs. A pairing that carries meaning
  beats a pairing that merely looks nice — for example a serif for analysis and a monospace for
  machine state, on a document about typed outputs.
- **Structure encodes information.** Use numbered markers only when the content is a sequence.
  Use colour to carry a distinction the reader needs (evidence level, ownership, risk band),
  never as decoration.
- **Spend boldness once.** One memorable element; everything around it disciplined.
- **Diagrams earn their place** when they show something prose cannot: ordering, proportion,
  a gap, two things side by side. A diagram that restates a sentence is noise.
- Avoid the generated-page tells: cream background with terracotta accent, all-caps eyebrow
  above every heading, identical rounded cards with the same soft shadow, `→` appended to
  every link, meta strings joined with middle dots.

Figures should be CSS and HTML, not images: they inherit the theme tokens, reflow on mobile,
and cost nothing to translate.

---

## 8. Token economy

The largest avoidable cost in this kind of work is re-emitting content you have already
written. Rules, in order of impact:

**1. Never rewrite a file to change part of it.** Edit by anchor. Before every replacement,
assert the anchor appears exactly once:

```python
assert s.count(old) == 1, "anchor not unique"
s = s.replace(old, new, 1)
```

An anchor that matches twice silently corrupts the file; an anchor that matches zero times
fails loudly, which is what you want.

**2. Assemble from parts.** Keep CSS, each script layer, and each markdown source in separate
working files, and concatenate them into the deliverable with a tiny script. Changing the
component layer then costs one file, not the whole document.

**3. Derive variants; never author them twice.** A shorter edition, a language, a depth level —
all are functions of one source. When asked for "the version without part 3", cut it with a
script, do not retype it.

**4. Author repeated markup as data.** Eleven figures became ten entries in `FIG` plus nine
component functions. The same content as literal HTML was roughly four times the bytes and
had to be written once per language.

**5. Verify by printing counts, not content.** Structural parity is a handful of numbers:

```
headings 40 vs 40 · tables 17, shapes identical · figures 11 vs 11 · anchors 30/30 resolve
```

Dumping two documents and comparing them by eye costs thousands of tokens and finds less.

**6. Locate before you edit.** `grep -n` for the anchor, print forty characters of context,
then edit. Reading a whole file to find one line is the most common avoidable cost.

**7. Keep a copy before destructive splices.** A cut with a wrong offset can delete a region
you cannot reconstruct from what remains. `cp` first; it costs nothing.

---

## 9. Test protocol

Install `jsdom` and actually run the page. Static inspection does not catch render bugs.

```js
const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
```

Cover, at minimum:

- every combination of language × view × depth, asserting zero errors
- element counts per combination: headings, tables, figures, paragraphs, TOC links, footer
  paragraphs, markdown length
- `getComputedStyle(...).display` for both view containers in both views — this is the only
  way to catch a CSS rule overriding the `hidden` attribute
- every TOC `href` resolves to an id that exists
- the copy-out markdown contains no layout directives and the expected parts
- structural parity against the previous version when refactoring: heading count, table shapes,
  figure count

---

## 10. Traps that cost real time

| Trap | Symptom | Fix |
|---|---|---|
| Old display rules surviving a refactor | Markdown view shows the document; markdown never appears | Delete `section.x{display:none}` when moving to `[hidden]`; add `[hidden]{display:none !important}` |
| `String.raw` with escaped backticks | Backslashes visible in copied markdown | Use `<script type="text/plain">` |
| Lazy regex with a lookahead | A slice silently removes nothing | `^[\s\S]*?(?=\n\n)` matches empty at position 0; find the paragraph boundary by index instead |
| `matchMedia` assumed present | Page throws in jsdom and some webviews | `(window.innerWidth \|\| 1280) >= 1180` |
| Non-unique anchor text | Wrong occurrence edited | Assert count; disambiguate with an exact full-line match |
| Blank-line-separated indented blocks | One diagram parsed as several code blocks | Merge while the next non-blank line is still indented |
| Anchors under the sticky bar | Heading hidden after clicking a TOC link | `scroll-margin-top` on `h2, h3, h4` |
| Figure labels duplicated per language | Translation drift in diagrams | One `FIG` entry with `vi` / `en` payloads |

---

## 11. Acceptance checklist

- [ ] One file; opens from `file://` with no console errors
- [ ] Language, view, depth and sidebar all route through a single `render()`
- [ ] No prose exists twice anywhere in the file
- [ ] Copy-out markdown is complete, directive-free, and matches the rendered document
- [ ] Table of contents rebuilds on language and depth change; all anchors resolve
- [ ] Footer and hero lede change with depth
- [ ] Drawer behaviour correct at 375px and 1440px; no horizontal page scroll
- [ ] Dark and light both legible; no colour-only distinctions
- [ ] Keyboard: every control reachable, focus visible, Escape closes the drawer
- [ ] jsdom run covers every language × view × depth combination with zero errors

---

## 12. Order of work

1. Write or collect the content as markdown, one file per language.
2. Restructure it for slicing: one lede line and one footer paragraph per removable part.
3. Insert layout directives around regions that become figures.
4. Author `FIG` data for those regions.
5. Write Layer 2, then Layer 1, then Layer 3 — components before the state they consume.
6. Assemble, run the jsdom suite, fix, reassemble.
7. Compare structurally against the previous version if this is a refactor.

Content first. Every architecture decision above exists to serve a document that already
knows what it wants to say.
