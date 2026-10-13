# JS architecture

One vanilla IIFE at the end of `assets/shell.html`, commented with four layers. No framework,
no build step.

## Layers

| Layer | What lives there | Rule |
|---|---|---|
| **Atoms** | `theme`, `lang`, `tab`, `menuOpen`, `section`, `filter`, `checklist`, `toast` — small observables with `get` / `set` / `sub` | The only state. `set` notifies subscribers only when the value changes. |
| **Components** | `ThemeSwitch`, `LangView`, `TabBar`, `Menu`, `Toc`, `FindingFilter`, `Checklist`, `Toast`, `MarkdownView` | Render from an atom; never decide. Guard for missing elements so a page without that component still runs. |
| **Workflows** | `theme:toggle`, `lang:toggle`, `tab:html`, `tab:md`, `menu:*`, `nav`, `filter`, `check`, `copy:*`, `download:md` | Named business actions: update atoms + side effects (localStorage, URL hash, scroll, clipboard, Blob download). |
| **Events** | one delegated `click` on `[data-action]`; `keydown` Esc; IntersectionObserver for the active section; `matchMedia` for width (the theme starts light and changes only through the toggle); `hashchange` | Normalise every input into a workflow call. Parametrised actions use a prefix (`filter:P0`, `check:3`). |

Storage is wrapped in `try/catch`: private windows, previews and `data:` origins throw, and the
page must work without it. Keys are `<storage-key>-theme`, `<storage-key>-lang` and `<storage-key>-checklist`.

## Built-in behaviour

- `Notation` runs once at load: it wraps codes from `#notation` (filled from `meta.notation`) in
  `<abbr class="nt" data-action="note">`; the `note` workflow shows the definition in the toast.
- Markdown links to `#ids` get `data-action="nav"` at render time, so they close the drawer and
  switch tabs like TOC links.
- `copy:code` copies the `<code>` of the code box that holds the clicked button, so any number
  of code boxes work without ids. `copy:md` copies the Markdown source.
- Every string the JS shows (toasts, the checklist counter `{done}/{total}`) is a `__UI:key__`
  token filled from `assets/ui-strings.json` at build time; never hard-code interface text.

- `#markdown` in the URL opens the Markdown tab; other hashes scroll to a section.
- `nav` closes the drawer on phones, switches to the Report tab, and resets the findings filter
  if the target card is hidden.
- The Markdown view is built with `textContent` (never `innerHTML`): line numbers, tinted
  headings, table lines and code fences; Copy and Download `.md` (Blob + `revokeObjectURL`).

## Two languages

A page built with `meta.alt` holds one `.lang-body[data-lang]` per language inside the Report
panel, one `.toc` per language, a sidebar note per language, and one `<script type="text/plain"
data-lang data-file>` Markdown source per language. Everything that differs by language carries
`data-lv="<lang>"`; `LangView` shows the active one and sets `<html lang>`, the title, the brand,
the Markdown tab and every `[data-ui]` / `[data-ui-aria]` label. Interface text for the default
language is filled at build time; `#ui-alt` carries the other language's strings, read through
`ui(key, fallback)` — use it for any text the JS shows. Components that query the page
(`Checklist`, `FindingFilter`, `Notation`) work per container, never through a single fixed id,
because each language has its own copy. On a one-language page `langs` is empty and `LangView`
does nothing.

## Adding a feature

1. Add an atom for its state (and its storage key if it should persist).
2. Write a render-only component and subscribe it.
3. Add a workflow; give its trigger a `data-action`.
4. If it is parametrised, add the prefix to the router in `run()`.

Keep it in the shell only if every page could use it; otherwise put a small `<script>` at the
end of the body fragment that follows the same pattern.
