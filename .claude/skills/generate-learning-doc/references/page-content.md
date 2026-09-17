# Step 2 — Page content (Opus subagent)

Pass this whole file to the step-2 subagent. It turns the step-1 notes into two content files, then runs the build script, which drops them into the fixed "sổ tiết kiệm" template.

The design (tokens, fonts, layout, sidebar, stamp, scrollspy, mobile drawer, reduced motion, a11y) already lives in `assets/template.html`, copied from entry No.12. Do not write CSS or JS and do not edit the template — keeping every entry identical is why it's fixed. Your job is the words and the illustrations.

## Inputs

- The notes file from step 1 (the only content source — do not reopen the raw script and do not add ideas).
- Entry number `NO`, year `YEAR`, output dir, and the book chapter when the entry is one, given by the orchestrator.

## File 1 — `meta.json`

```json
{
  "no": "13",
  "title": "Thông minh hơn gấp 10 lần",
  "year": "2026",
  "kicker": "Sổ tay tư duy · Giải mã Jim Rohn",
  "subtitle": "Bảy trụ cột rèn tư duy và quản lý cảm xúc: trí tuệ không bẩm sinh mà là hành trình bạn tự tạo ra.",
  "pills": ["7 phần", "Nguồn · Jim Rohn", "Ghi chú · No.13"],
  "source": "Nguồn: Kênh Giải mã Jim Rohn (YouTube) · Ghi chú No.13 · 2026"
}
```

- `title`: the notes' `#` heading, tightened if needed. Also becomes the file slug.
- `kicker`: short mono label, `<Loại sổ> · <Nguồn/tác giả>`. For a book chapter use `<Tên sách> · Chương N` instead (e.g. `Nghệ thuật đàm phán · Chương 4–5`).
- `subtitle`: 1–2 sentences, based on the notes' `Tóm lược`. Paraphrase it without quoting: meta fields are plain text, so a quote here can't get its `<em>` styling. Put the quote in a section instead.
- `pills`: exactly 3 — part count, source, `Ghi chú · No.NN`.
- `source`: footer line, taken from the notes' `Nguồn`.
- `chapter` (only for a book chapter): the chapter number as given, e.g. `"1"` or `"4–5"`. The script puts it in the browser tab title and the file name (`NN-chuong-04-05-<slug>.html`). Leave the key out for anything else.
- Plain text only (the script escapes it). Keep the JSON valid UTF-8, no HTML.

## File 2 — `sections.html`

One `<section>` per `## Phần N` in the notes, same order, nothing else in the file. The `## Sửa lỗi phiên âm` list is only for the orchestrator to check name corrections, so it doesn't become a section. Exact markup (this is Mục 01 of entry No.12):

```html
<section class="entry" id="s1" data-toc="Trí tuệ do rèn luyện">
  <div class="entry-head">
    <div>
      <span class="eyebrow">Mục 01</span>
      <h2>Trí tuệ là kết quả rèn luyện</h2>
      <p class="summary-line">Trí tuệ do rèn luyện mà thành, không phải quà bẩm sinh.</p>
    </div>
    <div class="frame">
      <svg class="ill" viewBox="0 0 160 120" aria-hidden="true">
        <path class="thin" d="M30 96 H130"/>
        <path d="M60 96 L66 112 H94 L100 96"/>
        <path d="M80 96 V54"/>
        <path d="M80 78 C66 74 58 62 62 52 C74 54 82 66 80 78 Z"/>
        <path d="M80 70 C94 66 102 56 98 46 C86 48 78 58 80 70 Z"/>
        <path class="b" d="M80 50 V28"/>
        <path class="b" d="M72 36 L80 26 L88 36"/>
      </svg>
    </div>
  </div>
  <ul class="points">
    <li><strong>Trí tuệ không có sẵn</strong> khi sinh ra — là kết quả rèn tư duy liên tục mỗi ngày. Jim Rohn: <em>"trí tuệ không phải là thứ bạn có sẵn mà là thứ bạn phải tạo ra, bảo vệ và phát triển mỗi ngày"</em>.</li>
    <li>Muốn <strong>thông minh hơn gấp 10 lần</strong>: kết hợp tư duy chiến lược, biết khi nào cần thay đổi và khi nào cần giữ lập trường.</li>
  </ul>
  <div class="callout">
    <span class="clabel">Nguyên tắc</span>
    <p>Muốn thay đổi thế giới, bắt đầu từ chính mình — <em>"nếu bạn muốn thay đổi thế giới, hãy bắt đầu từ chính bản thân mình"</em>.</p>
  </div>
</section>
```

Rules, and why:

- `id="sN"` and `Mục NN` count from 1 with no gaps — the TOC and scrollspy are generated from them.
- `data-toc`: 2–5 words; the sidebar is 288px wide, so long H2s wrap badly there.
- `summary-line`: one italic line, under ~90 characters.
- Bullets: one per note bullet (merge only true duplicates). Wrap 1–2 key phrases per bullet in `<strong>`. Keep every number, name, and concrete action from the notes.
- **Verbatim phrases:** every `"…"` phrase in the notes stays word-for-word, keeps its quotes, and is wrapped as `<em>"…"</em>` — in bullets and callouts alike. The build fails on any quoted phrase outside `<em>`, because a quote that loses its styling reads like the note-taker's own words.
- Callout: use the note's `Bài học:` / `Nguyên tắc:` line if there is one (label = that word). If not, write one short sentence that restates that section's main point from its bullets, labeled `Bài học` — no new ideas. Most sections should have a callout; skip it only when the section truly has no takeaway.
- Escape `&` as `&amp;` and `<` as `&lt;` in text.

## Illustrations

One inline SVG per section: a simple visual metaphor for that section's idea (seed → growth, mountain + flag → winning, broken chain → breaking limits, clock → time block, book → reading).

- Root `<svg class="ill" viewBox="0 0 160 120" aria-hidden="true">`. The template's `.ill` class already sets fill:none, stroke 3, round caps/joins, green stroke.
- 5–12 shapes (`path`, `circle`, `rect`, `line`, `polyline`, `ellipse`). Keep drawings within x 16–144 and y 12–112 so the tilted frame doesn't clip them.
- Accents: `class="b"` brass, `class="s"` seal red, `class="thin"` 2px stroke. Use 1–3 accent shapes, not all.
- No `fill` colors, no `<text>`, no `<image>`, no gradients. Line art only, so the entries match.
- Make each section's drawing different; don't reuse one icon across sections.

## Build

```bash
python3 <skill-dir>/scripts/build_doc.py --meta <work>/meta.json --sections <work>/sections.html --out-dir <output dir>
```

The script generates the TOC, fills the template, checks structure and verbatim-quote wrapping, and writes `<output dir>/NN-<slug>.html` (the slug has no diacritics; `NN-chuong-XX-<slug>.html` when `chapter` is set). `ERROR` lines mean nothing was written: fix `sections.html`/`meta.json` and rerun. `WARN` lines are advisory; fix them if the fix is quick. Never pass `--force` unless the orchestrator says so — an existing file with that number anywhere under `resources/` is someone's earlier entry.

When done, reply with the output path, the section count, and any remaining WARN lines.
