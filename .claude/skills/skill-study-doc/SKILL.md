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

Produce a page that lets someone who has never heard of a skill understand what
it is for, what it gives them, and only then how it works — and that stays true
because every claim in it was read from a file, in this session, not recalled.

**The reader is not in your domain.** They do not know the skill exists, do not
know its vocabulary, and will close the tab if the first screen is about
internals. Write for that person. A colleague who already uses the skill is not
the audience; they do not need the page.

## Inputs

A skill name, a path, or both. Resolve the other from what you are given: skills
live in `.claude/skills/<name>/` under a project, and in `~/.dotfiles/.claude/skills/`
for user-level ones. If several copies exist, say so and ask which is canonical —
copies drift, and documenting the wrong one is worse than documenting none.

**Output** defaults to `resources/topics/ai/claude/<slug>.html`, where `<slug>` is
a short, unaccented, kebab-case Vietnamese phrase describing the subject. Ask for
a different location if the project has no such folder.

**One skill or two.** A skill that only creates something, or only maintains
something, usually cannot fill the workflow, state and guard sections on its own.
When a sibling skill completes its lifecycle, document the pair on one page and
say in the opening which half does what. Check for siblings before you start: a
`Do NOT use for: … use X instead` line in the frontmatter names them.

## Settle one question before writing

**Is this a study guide, or an engineering assessment?** They are different
documents and mixing them ruins both.

- A **study guide** explains what the thing is for and how it works. It carries
  no bug list, no "still open" section, no known-defect table. Someone reading it
  wants to learn the design, not inherit a backlog.
- An **assessment** is about fitness: what is broken, what is unverified, what
  should change.

If the request does not make this obvious, ask — it is one question and it
changes what goes in. When it is a study guide, findings about defects still
belong somewhere: report them to the user in your final message, and say that is
where you put them.

## The shape of the document

**Inverted pyramid.** Value first, mechanism last: why it exists → what you get →
what it is made of → how it runs → what can go wrong. Business before technology,
in every section and inside every paragraph. A reader who quits after the second
section should still be able to say what the skill is for and whether they need
it.

**Never open with an internal.** A line count, a benchmark, a diff, a file tally
— these are evidence, and evidence belongs after the claim it supports, never in
the lede. A page that opens by dissecting the thing assumes the reader already
decided it was worth dissecting. They have not.

**Ten sections, in this order.** The order is the argument; do not rearrange it.

| # | Section | The question it answers |
|---|---|---|
| 1 | Mục đích | What real-world problem does this solve, and who was hurting before it existed? No filenames in this section. |
| 2 | Use case & output | One concrete situation where you would reach for it, and exactly what you are holding when it finishes — which file, where, what shape. |
| 3 | Cấu trúc | What the skill is made of, and what job each part holds. |
| 4 | Luồng chạy | From trigger to finish, step by step, in the order they happen. |
| 5 | Dữ liệu & trạng thái | What it reads, what it writes, what it remembers between steps, and where that lives. |
| 6 | Đầu–cuối | One real run followed all the way through, with concrete input and concrete output. |
| 7 | Hook | Where it attaches to hooks or settings. If it attaches nowhere, say so in one line. |
| 8 | Guard | What stops a user from getting it wrong, and what breaks when each guard is absent. |
| 9 | Đặc trưng | Where this differs from the obvious way of doing it, and what that trade buys. |
| 10 | Glossary | Always last. Always present. |

**An honest empty section beats a padded one.** If the skill has no hooks,
section 7 is one sentence saying so. Do not invent material to fill the skeleton
— a reader learns something real from "it attaches to nothing".

**Cover the ten sections, not every flag.** Completeness of structure, not
completeness of surface. A page listing every option is a reference nobody reads.

## Scope hygiene

The page is about the skill. Everything else that appears on it — a CLI it shells
out to, a library it imports, an OS command it depends on, a sibling skill it
hands work to — appears **only as a named external interface**, with one line
saying what the skill asks of it and what comes back. Never explain how the
external thing works inside. `ffmpeg`, `say`, `git`, `jsdom` are interfaces; the
skill is the subject.

The test: delete the skill from the world, and if a passage is still true, it
does not belong on the page unless it is labeled as an interface.

## Glossary

Every page ends with one, and you build it while reading, not afterwards — terms
recovered at the end are always the wrong set, because by then you have stopped
noticing what was unfamiliar.

Include the skill's own jargon, the filenames that get used as nouns, the CLI and
tool names, and the domain words a newcomer would have to look up. One sentence
each, alphabetical, and no definition that leans on another term in the list
without that term also being defined.

## Procedure

**1 — Read everything the skill is.** Not just `SKILL.md`: `references/`,
`scripts/`, `assets/`, any agent definitions it dispatches, and its frontmatter.
Note the description separately — it is the trigger surface and often the
clearest statement of intent.

**2 — Follow the skill to its implementation.** A skill that drives a CLI, a
server or a module is only half the story. Read the code it calls.
`references/research-checklist.md` lists what to look for and in what order.

**3 — Verify, and treat drift as a finding.** A skill's prose and its code drift
apart. When `SKILL.md` says one thing and the source says another, the source
wins, and the discrepancy itself is worth knowing. Check counts rather than
impressions: how many subcommands does the CLI actually expose, how many modes
does the canonical source define, how many of them does the skill carry.

**4 — Find the why before the how.** Hunt for the reason the skill was built:
the manual work it removed, the mistake it keeps people from repeating, the
decision someone got tired of re-making. It is usually in a comment, a commit
message, or the paragraph the author wrote before the rules. That reason is your
opening, and it is what makes the rules memorable instead of arbitrary.

**5 — Fill the ten sections.** Draft them in order. Where a section has no
material, go back to the source before concluding it is empty — an absent
workflow usually means you have not found the entry point yet.

**6 — Decide what becomes a figure.** A diagram earns its place when it shows
ordering, proportion, a gap, or two things side by side. The workflow and the
end-to-end run almost always deserve one. Prose restated in a box does not.

**7 — Hand off the rendering.** Write the markdown, then use **`gen-tech-doc-html`**
to build the page. Do not hand-roll the HTML: that skill carries a tested parser,
an assembler and a jsdom suite, and it is where the single-file architecture is
documented. Default to one language and no depth filter unless asked otherwise.

**8 — Sanitize before it ships.** Absolute home paths become `~/`. Internal
project codenames, employer-identifying strings and private repo names come out
unless they are the subject. The bundled test suite fails the build on a
surviving `/Users/<name>/`, but it cannot recognise a codename — you have to.

**9 — Report what you could not verify.** A short, honest list at the end of your
message, not buried in the page: what you read partially, what you inferred, what
would need a real run to confirm. The value of this document is that its claims
are traceable; the gaps are part of that contract.

## What makes these documents good

**Every claim points at a file.** The reader should be able to check you. Keep a
source list while you work even if it does not ship.

**Plain words first, jargon second.** Say the ordinary thing, then name it: "the
file that records what each scene says — the manifest". After that you may use
the term freely, and it goes in the glossary.

**Explain why, not just what.** A skill's rules exist because something went
wrong without them. Find that reason — it is usually in a comment or a commit —
and the rule becomes memorable instead of arbitrary.

**Numbers support, they do not open.** Where a measurement genuinely helps
someone decide, keep its date attached and put it in section 9 where it belongs.

## Reference files

| File | Read it when |
|---|---|
| `references/research-checklist.md` | starting step 2 — what to read in an implementation, what to collect for each of the ten sections, and the specific discrepancies worth checking |
