---
name: gen-tech-doc-html
description: >-
  Build a self-contained single-file HTML document site from technical content —
  one file, no build step, no assets beyond Google Fonts, with a sidebar menu, a
  Document/Markdown view toggle, and diagrams rendered as CSS/HTML figure
  components rather than images. Use this whenever someone wants technical
  material turned into a shareable web page: "make this a single HTML page",
  "build a doc site for X", "turn these notes into a page I can send someone",
  "write it up as HTML", "generate a technical doc page", or any request that
  ends in an .html file holding an explanation rather than an app. Also use it
  when another skill needs a page rendered and hands over finished markdown.
  Defaults to ONE language with no depth filter; multilingual and a
  depth-dropdown that cuts content are opt-in extras. Do NOT use for: markdown
  files in a repo (create-doc), a chat-only explanation (ask), a learning
  notebook built from a video transcript (generate-learning-doc), or web apps
  and dashboards.
---

# gen-tech-doc-html

Turn technical content into one HTML file that opens from disk, survives being
emailed, and reads well on a phone.

The architecture, the traps and the acceptance checklist come from
`references/playbook.md`. **Read it before writing any code** — it is the source
this skill exists to apply, and it carries detail this file deliberately does not
repeat. What follows is the operating procedure plus the parts already built for
you.

## What is already built

Rewriting the markdown parser and the assembler each time is the single largest
waste in this job. Both are here, and both have been run end to end:

| Path | What it is |
|---|---|
| `assets/shell.html` | the page skeleton, with six substitution tokens |
| `assets/base.css` | structural CSS: tokens declared three times, drawer, tables, markdown view, and a catalog of figure classes |
| `assets/md-parser.js` | LAYER 2 — `esc` / `el` / `inline`, `BLOCK`, and `MD.parse` / `MD.render` |
| `assets/figure-renderers.js` | LAYER 2 — eleven `FIGURE` renderers; keep the ones you use |
| `assets/logic.js` | LAYER 3 — one render path, table of contents built from the rendered DOM, drawer, scrollspy, copy-out |
| `scripts/build.py` | assembles the parts into the deliverable; refuses on a token that is not unique |
| `scripts/test.js` | jsdom acceptance suite; run it before you ship |

You still write, every time: the markdown, the `FIG` data, the figure renderers
your content needs, and the palette. Those are the parts that carry the subject.

## Procedure

Work in a scratch directory, not in the output folder. One file per part.

**1 — Content first.** Write the markdown before anything else. Every
architecture decision in the playbook exists to serve a document that already
knows what it wants to say, and a page assembled around thin content just makes
the thinness legible.

Shape it like this, splitting on the outer rules:

    # <title>                      <- the h1 is read from here, not retyped in the shell
    > <lede line>
    > <lede line>
    ---
    # PHẦN 1 — <heading>           <- or PART 1 — ; becomes an h2 with an eyebrow
    ## <section>                   <- h3
    ---
    # PHẦN 2 — <heading>
    ---
    <footer paragraph>
    <footer paragraph>

**2 — Mark the regions that become figures.** Where a diagram earns its place,
wrap an ASCII fallback in a directive:

    @fig:someId
        ASCII the markdown view keeps
    @endfig

The document view renders `FIG.someId` through its component and skips the ASCII;
the markdown view keeps the ASCII and drops the directive lines. That is how one
source feeds two very different renderings.

**3 — Author the figure data.** `FIG` entries are data, not markup: a `type` that
picks a renderer, a `cap` caption, and the payload. See
`references/figure-catalog.md` for the eleven shapes already written, with the
data each one expects. Reuse a shape when it fits; write a new renderer when the
content genuinely has a form none of them carry.

**4 — Ground the design in the subject.** `base.css` ships a placeholder palette.
Replace the token values. Pick two families with clearly different jobs, and let
colour carry a distinction the reader actually needs — an evidence level, a risk
band, an ownership boundary — never decoration. Playbook section 7 lists the
generated-page tells worth avoiding.

**5 — Assemble.**

    python3 <skill>/scripts/build.py --content <dir> --out <file>.html \
        --title "..." --desc "..." --lang vi

`--content` needs `style.css`, `src.md`, and `layer1.js` / `layer2*.js` /
`layer3.js`. Copy the bundled assets in as your starting `layer2*` and `layer3`.

**6 — Run the page, do not just read it.**

    npm install jsdom        # once, in any scratch directory
    node <skill>/scripts/test.js <file>.html <content-dir>

A CSS rule that overrides `hidden`, a figure whose renderer is missing, a
code-span sentinel left unrestored — none of these are visible by reading the
HTML, and all of them fail here. Ship only on a green run.

## Defaults, and the two opt-in extras

**One language. No depth filter.** That is the default because most documents are
read once, in one language, by someone who wants the whole thing. A depth
dropdown that hides content is machinery to build, to test in every combination,
and to keep in sync with the footer and the lede.

Add an extra only when asked for it, and read
`references/optional-features.md` first — it carries the exact deltas:

- **Multilingual** — `SRC` becomes one source per language, `FIG` payloads gain a
  per-language key, and every control routes through the same `render()`.
- **Depth dropdown** — cut markers, `dropPart` / `dropNote`, and the rule that
  each removable part needs its own lede line and its own footer paragraph.

`scripts/test.js` detects both automatically and adds the matching checks.

## Traps that have actually cost time

**Never run a build script to find out what it does.** `build.py` writes its
output file. Running it to "check something" overwrites whatever is there — read
it instead.

**Edit by anchor, and assert the anchor is unique.** An anchor matching twice
corrupts the file silently; matching zero times fails loudly, which is what you
want. `build.py` already enforces this for its own tokens.

**Keep prose out of JavaScript string literals.** A `<script type="text/plain">`
block needs no escaping at all. Escaped backticks inside template literals keep
their backslashes and show up in the copied markdown.

**The generic `code` rule leaks into the markdown view.** A `<code>` holding the
whole copy-out block inherits background, padding and a relative font-size that
compounds with the `<pre>`. `base.css` already resets it; keep that reset if you
rewrite the CSS.

**Verify by printing counts, not content.** Structural parity is a handful of
numbers — headings, tables, figures, anchors resolved. Dumping two documents and
comparing by eye costs far more and finds less.

**Sanitize before shipping.** Absolute home directories, usernames, internal
project codenames and employer-identifying strings do not belong on a page that
may be shared. Rewrite `/Users/<name>/` as `~/`; the test suite fails the build if
one survives.

## Reference files

| File | Read it when |
|---|---|
| `references/playbook.md` | before writing any code — the full architecture, content model, token economy and acceptance checklist |
| `references/figure-catalog.md` | authoring `FIG` data, or deciding whether a new renderer is needed |
| `references/optional-features.md` | the user asked for multiple languages or a depth dropdown |
