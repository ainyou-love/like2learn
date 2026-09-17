---
name: generate-learning-doc
description: "Turn a raw Vietnamese YouTube transcript (pasted text, a .txt/.md/.docx/.pdf file, or just the YouTube link — the transcript is fetched automatically) into a numbered 'Sổ ghi chép · No.NN' learning notebook HTML page in resources/, using the fixed sổ tiết kiệm passbook template. Runs two sequential subagents: Fable summarizes the script part by part, keeping verbatim quotes, numbers, names and concrete actions; then Opus writes the sections and line-art SVGs and builds the page. Use whenever the user pastes a transcript/script/sub/phụ đề, a lecture/podcast/book-talk text, or a YouTube URL of one, and asks to ghi chú, tóm tắt thành sổ, tạo file html ghi chú, làm entry/số tiếp theo, or 'gen learning doc' — even if they only say 'đây là script, số 13' without mentioning HTML. Do NOT use for editing CSS/JS of an existing entry, the Jekyll index.html, or a plain one-paragraph summary in chat."
argument-hint: "<raw text | file path | YouTube URL> [số thứ tự]"
---

# Generate learning doc

Raw Vietnamese transcript (or a YouTube link to one) → `resources/NN-<slug>.html`, a notebook entry that looks the same as No.12.

This is a pipeline you coordinate. It runs in two stages, one after the other, with a check after each. You don't write the notes or the HTML yourself: separate subagents keep the summary faithful to the script, and keep the page faithful to the summary.

```
raw script ──► [1] Fable: sectioned notes ──► quote check ──► [2] Opus: meta.json + sections.html ──► build_doc.py ──► resources/NN-slug.html
```

| File | Used by | Contains |
|------|---------|----------|
| `references/summary-rules.md` | step 1 subagent | Vietnamese context-keeping rules, notes format |
| `references/page-content.md` | step 2 subagent | meta.json + section markup, callout/quote rules, SVG rules |
| `assets/template.html` | build script | Fixed CSS/JS/layout copied from entry No.12 |
| `scripts/fetch_transcript.py` | you | Downloads a YouTube video's transcript as plain text into `raw.txt` |
| `scripts/check_quotes.py` | you | Flags quoted phrases in the notes that aren't word-for-word from the script |
| `scripts/build_doc.py` | step 2 subagent | Fills template, generates TOC, validates, writes the file |

`<skill-dir>` below = `.claude/skills/generate-learning-doc`.

## 0. Gather inputs

1. **Raw content.** YouTube URL: fetch it in item 4 (below). Pasted text: use it as is. File path: `.txt`/`.md` → Read it; `.pdf` → Read with `pages`; `.docx` → load the `anthropic-skills:docx` skill to extract the text. Nothing given → ask for it.
2. **Entry number.** Use the number the user gave. If they gave none, list `resources/*.html`, take the highest `NN` + 1, and confirm it with AskUserQuestion (gaps like a missing No.10 may be deliberate, so don't fill them silently). If `resources/NN-*.html` already exists, ask before overwriting — that's a published entry.
3. **Time.** Run `date +%Y%m%d%H%M%S` and `date +%Y` in Bash. Don't trust your own sense of today's date.
4. **Work dir.** `tmp/learning-notes/<NN>-<timestamp>/`. Write the raw content to `raw.txt` there, unchanged. Subagents read the file instead of getting the script pasted into their prompt, so nothing gets lost when the prompt is copied.

   For a YouTube URL, let the script write `raw.txt`. It needs `uv`, which installs the library on first run:

   ```bash
   uv run <skill-dir>/scripts/fetch_transcript.py "<url>" -l vi -o <work>/raw.txt
   ```

   On success it prints `SOURCE: <title> · <channel>` and then `OK`. `-l vi` already matches regional tracks like `vi-VN` and prefers uploaded captions over auto-generated ones. Use the `SOURCE` line plus the URL as the source context for step 1: the title and author are what let the notes fix misheard names. If it says `SOURCE: unknown`, ask the user for the title and author before step 1.

   On failure it exits with `ERROR: <ErrorType>: <reason>`:
   - `NoTranscriptFound`: the video has no Vietnamese track; the error lists the languages it does have. Ask the user whether to translate one (`-l <code> --translate vi`). Machine-translated text is weaker, so don't pick it silently.
   - `IpBlocked` / `RequestBlocked`: YouTube is rate-limiting this IP. Don't loop on retries; ask the user to wait and retry, or to paste the text from downsub.com instead.
   - Anything else (`TranscriptsDisabled`, `VideoUnavailable`, `AgeRestricted`, a network or timeout error, …): tell the user the reason and ask them to paste the transcript text instead.

   Auto-generated captions have no punctuation and break lines mid-phrase. That's expected; step 1 handles it.

## 1. Notes — Fable subagent

Spawn with the Agent tool, `model: "fable"`, `subagent_type: "general-purpose"`:

```
Read <skill-dir>/references/summary-rules.md — it is your full instruction set.
Raw script: <work>/raw.txt
Source context: <title / author / URL the user gave or the fetch script's SOURCE line, or "unknown">
Entry number: No.<NN>
Write the notes to: <work>/notes.md
Do not write HTML and do not touch any file outside <work>/.
```

Wait for it to finish before doing anything else. Step 2 depends on this output, so the two steps can't run in parallel.

Then check its work:

```bash
python3 <skill-dir>/scripts/check_quotes.py <work>/notes.md <work>/raw.txt
```

- `NOT VERBATIM` lines mean a quote was reworded, which breaks the main rule. First rule out the name/unit corrections listed under `## Sửa lỗi phiên âm`; those are expected. For each remaining one, find the real sentence in `raw.txt` and fix it in `notes.md` yourself: cut words to shorten it, never reword. If more than a third of the quotes fail, the summary is untrustworthy: send it back to the same agent (SendMessage) with the list.
- Skim `notes.md` against the script's structure. Parts should be in document order, and characters shouldn't be merged together. Don't rewrite the style; only fix things that are missing or wrong.

## 2. Page — Opus subagent

Spawn with the Agent tool, `model: "opus"`, `subagent_type: "general-purpose"`:

```
Read <skill-dir>/references/page-content.md — it is your full instruction set.
Notes (only content source): <work>/notes.md
Entry number: <NN>   Year: <YYYY>
Write meta.json and sections.html into: <work>/
Build into: resources
Do not edit assets/template.html, do not read raw.txt, do not pass --force.
```

(Add `--force is allowed` only if the user approved overwriting in step 0.)

## 3. Verify and report

- Confirm the output file exists and `build_doc.py` finished with `OK`. If the subagent stopped at `ERROR`, run the build again yourself after fixing the reported spot in `sections.html`.
- Tell the user:
  - the output path
  - the section titles
  - any WARN lines
  - the quote-check result (e.g. "18/18 quotes verbatim", or which ones you fixed)
  - where `notes.md` is, so they can proofread the summary

Don't start a dev server or open a browser; the user previews the page themselves. `index.html` lists `resources/` automatically, so there's nothing to register.
