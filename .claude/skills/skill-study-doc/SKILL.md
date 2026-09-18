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

Produce a page that lets someone else understand a skill without reading it —
and that stays true because every claim in it was read from a file, in this
session, not recalled.

## Inputs

A skill name, a path, or both. Resolve the other from what you are given: skills
live in `.claude/skills/<name>/` under a project, and in `~/.dotfiles/.claude/skills/`
for user-level ones. If several copies exist, say so and ask which is canonical —
copies drift, and documenting the wrong one is worse than documenting none.

**Output** defaults to `resources/topics/ai/claude/<slug>.html`, where `<slug>` is
a short, unaccented, kebab-case Vietnamese phrase describing the subject. Ask for
a different location if the project has no such folder.

## Settle one question before writing

**Is this a study guide, or an engineering assessment?** They are different
documents and mixing them ruins both.

- A **study guide** explains how the thing works and why it was built that way.
  It carries no bug list, no "still open" section, no known-defect table. Someone
  reading it wants to learn the design, not inherit a backlog.
- An **assessment** is about fitness: what is broken, what is unverified, what
  should change.

If the request does not make this obvious, ask — it is one question and it
changes what goes in. When it is a study guide, findings about defects still
belong somewhere: put them in a separate feedback file and say where you put it.

## Procedure

**1 — Read everything the skill is.** Not just `SKILL.md`: `references/`,
`scripts/`, `assets/`, any agent definitions it dispatches, and its frontmatter.
Note the description separately — it is the trigger surface and often the
clearest statement of intent.

**2 — Follow the skill to its implementation.** A skill that drives a CLI, a
server or a module is only half the story. Read the code it calls. `references/research-checklist.md`
lists what to look for and in what order.

**3 — Verify, and treat drift as a finding.** A skill's prose and its code drift
apart. When `SKILL.md` says one thing and the source says another, the source
wins, and the discrepancy itself is worth knowing. Check counts rather than
impressions: how many subcommands does the CLI actually expose, how many modes
does the canonical source define, how many of them does the skill carry.

**4 — Find the spine.** The best technical documents have one memorable claim,
and the strongest version of that claim is **measured rather than argued**. Hunt
for it: a benchmark with a date, a before-and-after count, a component deleted to
prove it was load-bearing. If you find one, build the document around it and give
it the boldest figure on the page. If there genuinely is none, say what the
design buys instead — but look hard first, because these numbers are usually
written down and usually skipped over.

**5 — Structure.** Three parts reads well for a skill:

    1. the problem, and the one design decision worth knowing
    2. the surface someone actually uses
    3. what is inside — isolation, performance, concurrency, limits

A skill's own "not in this slice" or "limitations" section is worth a passage. It
shows the shape of a scope that was cut deliberately, which is itself instructive.

**6 — Decide what becomes a figure.** A diagram earns its place when it shows
ordering, proportion, a gap, or two things side by side. Data models, hook
matrices, decision flows and measured timings all qualify. Prose restated in a box
does not.

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

**Numbers keep their dates.** "234 ms cold, 9–19 ms warm, measured 2026-09-14" is
worth ten sentences of "much faster".

**Explain why, not just what.** A skill's rules exist because something went
wrong without them. Find that reason — it is usually in a comment or a commit —
and the rule becomes memorable instead of arbitrary.

**Resist completeness theater.** A page covering every flag is a reference
nobody reads. Pick what changes how someone uses or trusts the thing.

## Reference files

| File | Read it when |
|---|---|
| `references/research-checklist.md` | starting step 2 — what to read in an implementation, and the specific discrepancies worth checking |
