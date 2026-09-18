---
name: skill-study-doc
description: >-
  Use when a Claude Code skill is the *subject* being explained, and the
  explanation must become a file someone else can open — page, write-up,
  study guide, doc, .html — not a chat answer. The skill is named (`akm`,
  `ascii-diagram`, `review-code`) or given by path
  (`.claude/skills/<name>/`, `~/.../skills/...`). If the named skill happens
  to be one of your own installed skills, this is still the right choice:
  the ask is to document that skill, not to run it. Typical asks: study this
  skill and write up what it actually does; explain how it works for the
  team; document it so a colleague can read it; tìm hiểu / làm doc về skill
  X. A destination folder or .html filename is just the output target and
  argues for this skill, not another. Reads the skill's source and the code
  behind it, verifies each claim, builds the finished page. Not for:
  authoring, testing or fixing a skill; chat answers with no file; auditing
  a project's Claude Code setup; documenting ordinary application code.
---

# skill-study-doc

Produce a page that teaches a newcomer two things at once: what this particular
skill does for them, and how a Claude Code skill is put together — so that by the
last section they could build one of their own.

**The reader is not in your domain, and cannot check your work.** They have never
heard of the skill, do not know its vocabulary, and hold no copy of the source to
verify anything against. Two consequences, both absolute: accuracy is entirely
your burden, and proof belongs nowhere on the page.

## What the reader must be able to do afterwards

1. Say what problem the skill solves, and whether they have that problem.
2. Draw the skill's folder from memory, and say what each file and folder is for.
3. Start a skill of their own — because they have watched one being designed and
   now know which decisions are theirs to make.

The third is the one that gets forgotten. Every page is a worked example of skill
design, not merely a description of one skill.

## Never on the page

Each of these has shipped at least once and had to be taken back out.

- **Provenance and methodology.** "Built from the canonical copy at …", sha256
  comparisons, "every number counted by script, not estimated", "the skill has no
  tests so no runtime behaviour was verified here". The reader has no source to
  compare against; this is noise wearing the costume of rigour.
- **Counts as content.** File counts, line counts, character tallies — "5 files,
  704 lines", "0 tabs, widest diagram line 62 columns". Nobody decides anything
  with these.
- **Citations.** No "per `SKILL.md` line 42". Name a file when the file is the
  subject — `references/` holds the material read on demand — never as a footnote.
- **Your audit trail.** What you verified, what you could not, what had drifted:
  that belongs in your message to the user, never in the document.

Verify everything anyway. The rigour is for your accuracy, not for display.

## Inputs

A skill name, a path, or both. Resolve the other from what you are given: skills
live in `.claude/skills/<name>/` under a project, and in `~/.dotfiles/.claude/skills/`
for user-level ones. If several copies exist, ask which is canonical — copies
drift, and documenting the wrong one is worse than documenting none.

**Output** defaults to `resources/topics/ai/claude/<slug>.html`, where `<slug>` is
a short, unaccented, kebab-case Vietnamese phrase describing the subject. Ask for
a different location if the project has no such folder.

**One skill or two.** A skill that only creates something, or only maintains
something, usually cannot fill the workflow, state and guard sections alone. When
a sibling skill completes its lifecycle, document the pair on one page and say in
the opening which half does what. A `Do NOT use for: … use X instead` line in the
frontmatter names the siblings.

## Settle one question before writing

**Is this a study guide, or an engineering assessment?** They are different
documents and mixing them ruins both.

- A **study guide** explains what the thing is for and how it is built. No bug
  list, no "still open" section, no known-defect table.
- An **assessment** is about fitness: what is broken, what is unverified, what
  should change.

If the request does not make this obvious, ask. When it is a study guide,
defects still belong somewhere: report them to the user in your final message,
and say that is where you put them.

## The shape of the document

**Inverted pyramid.** Value first, mechanism last: why it exists → what you get →
what it is made of → how it runs → what can go wrong. Business before technology,
in every section and inside every paragraph. A reader who stops after section 2
should still be able to say what the skill is for and whether they need it.

**Never open with an internal.** A file tally, a benchmark, a diff. A page that
opens by dissecting its subject assumes the reader already decided it was worth
dissecting. They have not.

**Eleven sections, in this order.** The order is the argument; do not rearrange it.

| # | Section | The question it answers |
|---|---|---|
| 1 | Mục đích | What real-world problem does this solve, and who was hurting before it existed? No filenames in this section. |
| 2 | Use case & output | One concrete situation where you would reach for it, and exactly what you are holding when it finishes — which file, where, what shape. |
| 3 | Cấu trúc thư mục | The folder tree, the job each file and folder holds, and why the work is divided that way. |
| 4 | Luồng chạy | From trigger to finish, step by step, in the order they happen. |
| 5 | Dữ liệu & trạng thái | What it reads, what it writes, what it remembers between steps, and where that lives. |
| 6 | Đầu–cuối | One run followed all the way through, with concrete input and concrete output. |
| 7 | Hook | Where it attaches to hooks or settings. If it attaches nowhere, say so in one line. |
| 8 | Guard | What stops a user from getting it wrong, and what breaks when each guard is absent. |
| 9 | Đặc trưng | The design decisions worth stealing, and what each one traded away. |
| 10 | Tự dựng skill của bạn | The recipe this example yields: the decisions a reader now has to make for themselves. |
| 11 | Glossary | Always last. Always present. |

**An honest empty section beats a padded one.** If the skill has no hooks,
section 7 is one sentence saying so. A reader learns something real from "it
attaches to nothing".

**Cover the eleven sections, not every flag.** Completeness of structure, not of
surface. A page listing every option is a reference nobody reads.

## Section 3 carries the most weight

Most readers have never opened a skill folder, so this is where the page stops
being about one skill and starts being about skills. Show the tree first, then
give every entry a job in one sentence, then name the division of labour it
demonstrates:

- **Frontmatter** (`name`, `description`) is the only part always in the agent's
  context. It is the trigger surface: it decides whether the skill is chosen at
  all, which is why it reads like a list of situations, not a summary.
- **`SKILL.md` body** is read whenever the skill fires. Everything in it costs
  context on every run, so it holds procedure and judgement, not detail.
- **`references/`** is read only when the procedure sends the agent there. This is
  where depth lives precisely because it is not always paid for. Name the idea —
  **progressive disclosure** — after showing it, not before.
- **`scripts/`** is work handed to code because code is cheaper and more reliable
  than instructions repeated in prose.
- **`templates/`, `assets/`** are material copied rather than regenerated.

A skill missing one of these is telling you something. Say what.

## Section 10 is what makes the page worth writing

Turn the worked example into a recipe. Not "here is how to write a skill in
general" — that is a different document — but: this author faced a set of
choices, here is what they picked and why, and here is the same choice waiting
for you. The useful ones are usually:

- what earns a place in `SKILL.md` versus what gets pushed into `references/`
- when a skill needs a script instead of more instructions
- how the description is written so the skill fires at the right moment and stays
  quiet at the wrong one
- which rules exist because something went wrong without them

Keep it short and concrete. A reader should finish it with a folder to create and
a first file to write.

## Scope hygiene

The page is about the skill. Everything else that appears on it — a CLI it shells
out to, a library it imports, an OS command it depends on, a sibling skill it
hands work to — appears **only as a named external interface**, with one line
saying what the skill asks of it and what comes back. Never explain how the
external thing works inside. `ffmpeg`, `say`, `git`, `jsdom` are interfaces; the
skill is the subject.

The test: delete the skill from the world, and if a passage is still true, it does
not belong on the page unless it is labelled as an interface.

## Glossary

Every page ends with one, and you build it while reading, not afterwards — terms
recovered at the end are always the wrong set, because by then you have stopped
noticing what was unfamiliar.

Include the skill's own jargon, the filenames used as nouns, the tool names, and
the domain words a newcomer would have to look up. One sentence each,
alphabetical, and no definition that leans on an undefined term.

## Procedure

**1 — Read everything the skill is.** Not just `SKILL.md`: `references/`,
`scripts/`, `assets/`, `templates/`, any agent definitions it dispatches, and its
frontmatter. Note the description separately — it is the trigger surface and often
the clearest statement of intent.

**2 — Follow the skill to its implementation.** A skill that drives a CLI, a
server or a module is only half the story. Read the code it calls.
`references/research-checklist.md` lists what to look for and in what order.

**3 — Verify, and treat drift as a finding.** A skill's prose and its code drift
apart. When `SKILL.md` says one thing and the source says another, the source
wins. The discrepancy goes in your report to the user, not on the page.

**4 — Find the why before the how.** Hunt for the reason the skill was built: the
manual work it removed, the mistake it keeps people from repeating, the decision
someone got tired of re-making. It is usually in a comment, a commit message, or
the paragraph written just before the rules. That reason is your opening.

**5 — Fill the eleven sections.** Draft them in order. Where a section has no
material, go back to the source before concluding it is empty — an absent workflow
usually means the entry point has not been found yet.

**6 — Decide what becomes a figure.** A diagram earns its place when it shows
ordering, proportion, a gap, or two things side by side. The folder tree, the
workflow and the end-to-end run almost always deserve one. Prose restated in a box
does not.

**7 — Hand off the rendering.** Write the markdown, then use **`gen-tech-doc-html`**
to build the page. Do not hand-roll the HTML: that skill carries a tested parser,
an assembler and a jsdom suite. Default to one language and no depth filter unless
asked otherwise.

**8 — Sanitize before it ships.** Absolute home paths become `~/`. Internal project
codenames, employer-identifying strings and private repo names come out unless they
are the subject. The bundled test suite fails the build on a surviving
`/Users/<name>/`, but it cannot recognise a codename — you have to.

**9 — Report what you could not verify.** A short, honest list at the end of your
message to the user: what you read partially, what you inferred, what would need a
real run to confirm. This never appears on the page.

## What makes these documents good

**Accuracy is your burden, not the reader's.** They cannot check you, so the page
carries no apparatus inviting them to try. Be right instead.

**Plain words first, jargon second.** Say the ordinary thing, then name it: "the
file that records what each scene says — the manifest". After that use the term
freely, and put it in the glossary.

**Show the folder, do not describe it.** A tree a reader can copy beats a
paragraph about how the skill is organised.

**Explain why, not just what.** A skill's rules exist because something went wrong
without them. Find that reason and the rule becomes memorable instead of arbitrary.

## Reference files

| File | Read it when |
|---|---|
| `references/research-checklist.md` | starting step 2 — what to read in an implementation, what to collect for each of the eleven sections, and the discrepancies worth checking |
