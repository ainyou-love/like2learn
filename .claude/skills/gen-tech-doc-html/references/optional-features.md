# The two opt-in extras

Both are off by default. Each is real machinery — build it when the user asks for
it, not because the architecture supports it.

---

## Multiple languages

### What changes

`SRC` stops being a string and becomes a map. Everything downstream already
routes through one `render()`, so the work is smaller than it looks.

**Content.** One file per language: `src-vi.md`, `src-en.md`. `build.py` detects
them and emits one `<script type="text/plain" id="src-vi">` per file. Keep the
structure identical across languages — same parts, same `@fig:` ids, same order —
or the table of contents and the figures drift apart.

**Layer 1.**

    var STATE = { lang: 'vi', view: 'doc', nav: false };

    var SRC = {
      vi: document.getElementById('src-vi').textContent,
      en: document.getElementById('src-en').textContent
    };

    var I18N = { vi: { doc: 'Tài liệu', … }, en: { doc: 'Document', … } };

`I18N` holds **UI chrome only** — button labels, the contents heading, the copy
confirmation. Never prose. Prose lives in the markdown, once per language.

**Figures.** One `FIG` entry, with a payload per language, so a diagram's labels
cannot drift:

    fourQ: { type: 'questions',
             vi: { items: […], scores: […] },
             en: { items: […], scores: […] },
             cap: { vi: '…', en: '…' } }

Then `BLOCK.fig` passes `f[STATE.lang]` to the renderer and `f.cap[STATE.lang]`
to the caption. This is the one place a component is allowed to receive
language-shaped data — the renderer itself still must not read `STATE`; the
parent picks the payload and hands it down.

**Layer 3.** `sections()` reads `SRC[STATE.lang]`. Add:

    function setLang(l){ STATE.lang = l; render(); }

and a `<select id="langsel">` in the bar wired to it. `render()` already rebuilds
the table of contents from the rendered DOM, so sections in the other language
appear automatically — no filtering needed.

### What to check

`scripts/test.js` finds `#langsel` and asserts the document rerenders and the
table of contents rebuilds. Add your own count parity check: headings, tables and
figures should match across languages. A mismatch means a part was translated but
not restructured.

---

## Depth dropdown that cuts content

### What changes

The document is sliced *as text*, before parsing, so both views read the same
sliced string and cannot disagree.

**Content, authored for the cut.** This is the part that bites. Every removable
part needs:

- its own lede line in the front matter, on one line
- its own footer paragraph, as a whole paragraph
- a heading whose exact text you can search for

Give every removable sentence its own line or its own paragraph **at authoring
time**. Retro-fitting a cut into a mid-paragraph clause always leaves a stump.

**Layer 1 — the markers.**

    var CUT = {
      p2:   '\n# PHẦN 2 — ',
      p3:   '\n# PHẦN 3 — ',
      foot: '\nNguồn: ',                       // a string only the footer holds
      n2:   '\n\nPhần 2 nói về',               // first words of part 2's footer note
      n3:   '\n\nPhần 3 nói về',
      l2:   /\n> Phần 2 — [^\n]*/,             // part 2's lede line
      l3:   /\n> Phần 3 — [^\n]*/
    };

**Layer 3 — the slicer.** Cut deeper parts first, so the footer marker stays
findable:

    /* remove the region between the rule before `head` and the rule before `stop` */
    function dropPart(t, head, stop){
      var a = t.indexOf(head);           if(a < 0) return t;
      a = t.lastIndexOf('\n---\n', a);
      var b = t.indexOf(stop, a);        if(b < 0) return t;
      b = t.lastIndexOf('\n---\n', b);
      return (a > -1 && b > a) ? t.slice(0, a) + t.slice(b) : t;
    }

    function dropNote(t, note){
      var i = t.indexOf(note);           if(i < 0) return t;
      var e = t.indexOf('\n\n', i + note.length);
      if(e < 0) e = t.length;
      return t.slice(0, i) + t.slice(e);
    }

    function sliced(depth){
      var t = SRC, m = CUT;
      if(depth < 3){ t = dropPart(t, m.p3, m.foot); t = t.replace(m.l3, ''); t = dropNote(t, m.n3); }
      if(depth < 2){ t = dropPart(t, m.p2, m.foot); t = t.replace(m.l2, ''); t = dropNote(t, m.n2); }
      return t.replace(/\n{3,}$/, '\n');
    }

Cache by key — slicing on every scroll tick is waste.

`sections()` and `forCopy()` both read `sliced(STATE.depth)`. Because the lede
lines and footer paragraphs live in the same sliced text as the body, **one cut
updates all three at once.** Anything you keep outside the markdown must be
genuinely depth-independent or it falls out of sync.

**The control is a `<select>`, not buttons** — it gets the native picker on a
phone, and depth is one choice from an ordered set, which is what a select means.

### What to check

`scripts/test.js` finds `#depthsel` and asserts that depth 1 drops sections, that
the table of contents follows the cut, that the sliced markdown stays
directive-free, and that full depth restores everything. Run every combination of
language × view × depth — the playbook's test protocol asks for exactly that, and
combinations are where this feature breaks.

### The trap worth naming

A lazy regex with a lookahead silently removes nothing: `^[\s\S]*?(?=\n\n)`
matches empty at position 0. Find the paragraph boundary by index, as `dropNote`
does above.
