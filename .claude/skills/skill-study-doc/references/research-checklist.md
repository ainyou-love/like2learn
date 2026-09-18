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
design decision worth knowing" or "why X and not Y" are the author telling you
what belongs in section 9.

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

## Collecting for the eleven sections

The page has a fixed skeleton, so read with those slots in mind. Most of a
rewrite is caused by finishing the reading and only then discovering that four
sections have nothing in them.

| Section | What to look for while reading |
|---|---|
| Mục đích | The manual work the skill replaced. Commit messages and the paragraph above the rules say it more plainly than the rules do. |
| Use case & output | The example the author chose, and the exact artifact produced — path, extension, and what opening it looks like. |
| Cấu trúc thư mục | `find <skill> -type f` for the tree, one sentence per entry on the job it holds, and which of `references/` / `scripts/` / `templates/` the skill chose to use or skip. A missing folder is a design decision — find out what replaced it. |
| Luồng chạy | The entry point, then each step in the order it fires. A numbered procedure in `SKILL.md` is a claim; the script is the fact. |
| Dữ liệu & trạng thái | Files written, temp directories, manifests, env vars, anything that survives between steps. Note where it lives and who cleans it up. |
| Đầu–cuối | One example you can follow all the way through. Prefer one the repo already contains over one you invent. |
| Hook | Grep the settings layers for the skill or script name. Finding nothing is a result — record it as "attaches to nothing". |
| Guard | Validation, `set -euo pipefail`, refusals, preflight checks, tests that fail the build. For each, what breaks without it. |
| Đặc trưng | The choice a reasonable person would have made differently, and the sentence where the author defends it. |
| Tự dựng skill của bạn | Every decision the author had to make that a reader will also face: what stayed in `SKILL.md` and what moved to `references/`, why a script exists instead of more prose, how the description was shaped to fire at the right moment. |
| Glossary | Every term you had to look up, the moment you look it up. |

## External interfaces

List every tool, binary, library or sibling skill the skill reaches for, and for
each one capture only two things: **what the skill hands it** and **what it gets
back**. That pair is all that belongs on the page. Resist reading further into
the external tool — its internals are someone else's document.

## Things to capture while reading

Keep these as you go — reconstructing them later costs more than noting them.

- **A source list.** File and what it established. This is what makes the
  document checkable.
- **Exact identifiers.** Node labels, relationship names, enum values, subcommand
  names, env var names, default values. Spelling them right is most of what makes
  a technical page trustworthy.
- **Glossary terms, as they surprise you.** The moment a word needs looking up is
  the only moment you can tell it needed looking up.
- **The reason the skill exists**, in the author's own words if you can find them.
- **Design decisions, with the alternative rejected.** These become section 10,
  and they are the reason someone can build their own skill after reading.
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
