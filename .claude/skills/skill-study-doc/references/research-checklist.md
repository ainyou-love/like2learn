# Research checklist

What to read, in what order, and which discrepancies are worth hunting for.

## Reading order

Cheapest first — each step tells you what is worth reading next.

1. **Frontmatter.** The description is the trigger surface and usually the
   sharpest statement of what the skill is for. Note the boundaries it draws
   ("do NOT use for…") — they tell you which neighbours it competes with.
2. **`SKILL.md` body.** The claimed procedure. Treat it as a claim, not a fact.
3. **The file listing.** `find <skill> -type f` plus line counts. The shape of
   the skill is visible here: a fat `references/` means progressive disclosure, a
   fat `scripts/` means the skill delegates real work to code.
4. **Bundled scripts.** Read the module docstrings first — in a well-written
   script the docstring says *why* it exists, which is exactly what a document
   needs and what the code alone cannot tell you.
5. **The implementation the skill points at.** A project README, a server, a CLI.
   This is where the measured claims live.
6. **Tests.** They name the invariants the authors actually cared about, and a
   test written "directly" rather than through the normal path usually marks a
   correctness boundary someone thought hard about.

## Where the good material hides

**Module docstrings and comments that explain a decision.** A comment saying a
sentinel value is used "because a uniqueness constraint does not apply when a
property is null" is worth more than any amount of API listing.

**READMEs with a section named for a single decision.** Headings like "the one
design decision worth knowing" or "why X and not Y" are the author handing you
the spine of the document.

**Numbers with dates.** Benchmarks, before-and-after counts, measured medians.
Grep for `ms`, `measured`, dates, and percentage signs. Keep the date attached —
an undated number ages badly and a dated one stays honest.

**"Not in this slice" / "Limitations" / "Out of scope".** Shows a scope that was
cut on purpose, which is instructive in itself.

**Config with defaults and thresholds.** A settings module tells you which knobs
the authors expected to move, and default values are often the result of a
measurement recorded nearby.

## Discrepancies worth hunting

These are the ones that have actually shown up. Check counts; do not eyeball.

| Check | How |
|---|---|
| Does the skill's prose match its own scripts? | count the subcommands the CLI parser defines, compare with what `SKILL.md` claims |
| Does the skill match its canonical source? | when a skill says it mirrors something, count both sides — "mirror" often means "overlaps" |
| Are there several copies of this skill? | search the machine for the directory name; compare with `diff -rq` and by hash |
| Which copy actually runs? | grep the settings layers for the path a hook or command invokes — it may not be the one in the project |
| Do the docs name paths that exist? | resolve every path the skill mentions before repeating it |
| Are documented env vars real? | grep the code for each name |

When prose and source disagree, the source wins. Say so plainly in your report to
the user; whether it belongs in the page depends on whether the page is a study
guide or an assessment.

## Things to capture while reading

Keep these as you go — reconstructing them later costs more than noting them.

- **A source list.** File and what it established. This is what makes the
  document checkable.
- **Exact identifiers.** Node labels, relationship names, enum values, subcommand
  names, env var names, default values. Spelling them right is most of what makes
  a technical page trustworthy.
- **The one memorable claim**, and whether it is measured or argued.
- **What you did not read.** A file you skipped, a directory you sampled. This
  becomes the honest gaps list.

## Sanitizing

Run these before shipping:

- `/Users/<name>/` and `/home/<name>/` → `~/`
- internal project codenames → a generic descriptor, unless the codename *is*
  the subject
- employer or client names, including inside config directory names
- private repository names in lists and examples

The bundled test suite catches absolute home paths. It cannot recognise a
codename, so that pass is yours.
