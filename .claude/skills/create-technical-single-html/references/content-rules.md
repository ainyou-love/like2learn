# Content rules

The page exists so one reader can act on a review. Structure and wording serve that.

## Page order

1. **Hero** — kicker (what this is, for whom), a claim headline, one-paragraph lede, meta
   chips (owner, evidence, link to the original), 4 stat tiles.
2. **Review checklist** — 4–6 steps the reader ticks: align business → requirements →
   current system state → findings → design → decisions/questions. Each step links its sections
   and lists 1–3 checks.
3. **Start here** — what to change, what to answer, what is reference only, and a reading path.
4. **Scope** (confirmed facts) → **Requirements** (functional, non-functional, boundaries) →
   **Decisions** → domain sections → **Findings** → **Current state** → **Design options** →
   registries/capacity → **Verification details** (reference) → **Open questions** → Appendix.

Requirements come before evidence because they frame everything after. Verification goes last
because only some readers need it.

## Cards and their fields

| Element | Fields | Rule |
|---|---|---|
| Finding | ID + priority · What · Example · Value · Fix | Example is a concrete scenario (times, values, counts). Value says what fixing it buys. |
| Decision | ID + status · Why · Value · Example | Status is honest: **Confirmed** only when a stakeholder confirmed it; otherwise **Request review**; unanswered = **Open**. |
| Design option | Goal · How · Strong · Weak · schema | Show every option's design before comparing them. |
| State machine | one diagram per option + a comparison table | Compare: where state lives, states it can express, who moves it, concurrency guard, invalid states, history, cost of a new state. |
| Business question | ID · question · example | Group by job (e.g. S = serving the customer, M = monitoring and tuning). |
| Technical object | name · type · what it does | Add a prefix legend (`uq_`, `ix_`, `v_` …). |

## Wording

- Plain business language. Replace jargon with what it means to the reader
  ("Serving the customer" / "Monitoring and tuning" instead of OLTP / OLAP). Pass the jargon list
  to `meta.ban` in post.json (or `build.py --ban`).
- Never let wording imply a business change that did not happen (a sequenced item is not "cut").
- Evidence labels: **verified** (with `file:line`), **[ASSUMPTION]**, **[UNKNOWN]**. Every number
  comes from a source you read; dev-data counts are labelled as shape, not volume.
- If this is the only version the reader receives, leave out version history, "what changed",
  withdrawn items and "new" tags.
- `post.json` is the source of truth; the Markdown tab is generated from the same blocks, so both say the same thing.

## Before handing over

- Every finding and decision has an example.
- Each status pill matches what was actually confirmed.
- No internal paths, usernames or confidential names if the page may be shared
  (`meta.strict_paths`, or `build.py --strict-paths`).
