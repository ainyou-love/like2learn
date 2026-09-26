# The report dataset, schema_version 1.0

`scripts/validate_report.py` enforces everything on this page. Read it as the
executable version of this document; when the two disagree, the script wins.
`references/sample-report.json` is a small, valid instance of the whole thing.

## Contents

- [The one rule that shapes everything](#the-one-rule-that-shapes-everything)
- [Types](#types)
- [Report](#report)
- [Section and Item](#section-and-item)
- [Source](#source)
- [What validation refuses](#what-validation-refuses)

## The one rule that shapes everything

Every field is exactly one of two classes.

**NEUTRAL** — identical in every language, stored as a plain scalar or array:
ids, URLs, dates, versions, numbers, units, product / repo / person names,
commands, code, enum values, and source titles (kept in their original
language).

**LOCALIZED** (`LText`) — always an object with every language in
`meta.languages` as a key: `{"vi": "...", "en": "..."}`.

Enum values stay neutral in the data. `patch_now` is stored once and the page
renders it as "Patch ngay" or "Patch now" through the `I18N` table, so adding a
third language never means touching an item. The corollary matters just as
much: **never put a URL, command, or code snippet inside an LText.** They are
neutral by definition, they belong in `links[]` / `commands[]`, and the
validator rejects them in localized text because a translated URL is a broken
URL.

Writing the two languages:

- `vi` — natural Vietnamese. Keep developer terms in English: *subagent,
  breaking change, copy-on-write branching, lockfile, preinstall hook*. Never
  translate a product name.
- `en` — plain, concise technical English.
- Both carry the same facts, numbers and caveats. Write each one naturally.
  Do not translate word by word; a sentence that reads like a translation reads
  like nobody checked it.

## Types

```ts
type LText   = { vi: string; en: string };          // every language in meta.languages
type ISODate = string;                               // "YYYY-MM-DD"
type DatePrecision = "day" | "month" | "quarter" | "tbd";
type Action  = "patch_now" | "try_now" | "watch" | "ignore";
type Truth   = "FACT" | "ASSUMPTION" | "UNVERIFIED" | "VENDOR_CLAIM";
type Tag     = "RISK" | "RISK/SECURITY" | "RISK/MIGRATION"
             | "TRADE_OFF" | "DECISION" | "CONCERN";
```

`truth` is the field a reader trusts the page for, so it is worth being exact:

| value | means | how the page shows it |
|---|---|---|
| `FACT` | confirmed against a primary source | solid border |
| `ASSUMPTION` | your inference; needs `confidence` | solid border + confidence badge |
| `UNVERIFIED` | claimed somewhere, not confirmed | **dashed** border |
| `VENDOR_CLAIM` | the party with an interest is the only source | **dashed** border |

A vendor benchmarking or ranking itself is `VENDOR_CLAIM`, not `FACT`, however
official the page it appears on.

## Report

```ts
type Report = {
  schema_version: "1.0";
  meta: {
    report_id: string;            // "{slug}_{from}_{to}"
    generated_at: string;         // ISO 8601 datetime; its date names the file
    time_window: { preset: string; from: ISODate; to: ISODate };
    topics: string[];             // the section ids, in order
    stack: string[];              // what the reader actually runs
    depth: "brief" | "standard" | "deep";
    languages: string[];
    default_language: string;     // must be one of languages
    title: LText;
    subtitle: LText;
    data_quality_note: LText;     // what this report could not establish
  };
  highlights:  { id; rank: number; text: LText; item_ids: string[] }[];
  sections:    Section[];
  stack_actions: { id; target: string; action: Action; text: LText; item_ids: string[] }[];
  deadlines:   { id; date: ISODate|null; date_precision: DatePrecision;
                 status: "upcoming"|"passed"|"tbd"; event: LText; source_ids: string[] }[];
  checklist:   { id; order: number; text: LText; commands: string[]; item_ids: string[] }[];
  verify:      { id; text: LText; commands: string[] }[];
  conflicts:   { id; subject: LText;
                 values: { value: string; source_id: string }[]; note: LText }[];
  glossary:    { term: string; definition: LText }[];
  sources:     Source[];
};
```

`data_quality_note` is not boilerplate. It is where the report says what it
could not establish — which topics were thin, which numbers rest on one
source, what a reader should not conclude. A report without it invites more
confidence than it earned.

`conflicts` exists so that two sources disagreeing on a number never gets
resolved silently. Record both values with their sources and say in `note` why
they differ. Picking one quietly is how a report becomes wrong in a way nobody
can trace back.

## Section and Item

```ts
type Section = {
  id: string;        // "A".."N" or whatever the preset defines
  slug: string;      // "security-supply-chain"
  order: number;
  title: LText;
  summary: LText;    // 1-2 sentences: what changed in this window
  status: "ok" | "empty";
  items: Item[];
};

type Item = {
  id: string;        // "{section}-{nnn}" e.g. "H-001"; stable across reports
  kind: "release"|"incident"|"event"|"tool"|"repo"|"pattern"|"stat"
      | "model"|"person"|"channel"|"community"|"spec"|"video";
  name: string;                  // proper name, neutral
  version: string | null;
  date: ISODate | null;
  date_precision: DatePrecision;
  older_context: boolean;
  truth: Truth;
  confidence: "HIGH"|"MEDIUM"|"LOW"|null;   // required when truth = ASSUMPTION
  tags: Tag[];
  action: Action | null;
  stack_relevance: string[];     // subset of meta.stack
  headline: LText;               // ~15 words, no more
  body: LText;                   // 1-3 sentences: what changed, why it matters
  metrics: { key: string; value: number|string; unit: string|null;
             label: LText; source_id: string }[];
  commands: string[];
  links: { url: string; label: LText }[];   // repo or docs, not citations
  source_ids: string[];          // at least one, unless truth = ASSUMPTION
};
```

`status: "empty"` is a real answer. A section with nothing significant in the
window renders an honest empty state; padding it with filler is worse than
leaving it empty, because the reader cannot tell the difference between
"nothing happened" and "nobody looked".

An item dated outside the window may only appear when it is still the canonical
reference **and** something relevant changed inside the window. Set
`older_context: true` on it; the validator insists.

`links` are things to open — a repo, the docs. `source_ids` are what the claim
rests on. Keep them apart: a link is a convenience, a source is evidence.

## Source

```ts
type Source = {
  id: string;                 // "S001" after the merge
  title: string;              // original title, original language
  publisher: string;
  url: string;                // absolute https
  published_at: ISODate | null;
  source_type: "official"|"changelog"|"repo"|"security_lab"|"paper"
             | "practitioner_blog"|"media"|"vendor"|"listicle"|"community"|"video";
  trust: "high"|"medium"|"low";
  original_lang: string;      // BCP 47, e.g. "en"
  topics: string[];
};
```

A YouTube URL wants `source_type: "video"`. The page then renders a
click-to-load player under the item that cites it and in the source card, so a
recorded talk can be watched where it is being relied on instead of being
filed away as a link. Nothing loads from YouTube until the reader clicks.

`trust` describes the source, not the claim. An official changelog is `high`
even when the release it documents turned out to be broken.

## What validation refuses

Errors (exit 1) — the page would be quietly wrong:

1. `schema_version` is not `"1.0"`.
2. Any id is reused, anywhere in the file.
3. Any `item_ids` / `source_ids` / `source_id` names something that does not exist.
4. An `LText` is missing a declared language, or has it empty.
5. A URL appears inside an `LText`.
6. An item has no `source_ids` and `truth` is not `ASSUMPTION`.
7. `truth: "ASSUMPTION"` without a `confidence`.
8. A date that is not `YYYY-MM-DD`, or `null` without `date_precision: "tbd"`.
9. A date outside the window without `older_context: true`.
10. Any enum value outside its set.
11. A source URL that is not absolute https.
12. A conflict with fewer than two competing values.
13. `default_language` not in `languages`; `from` after `to`.
14. No sections, or no sources.

Warnings (still exit 0) — worth a look, not always wrong:

- A command-looking string inside an `LText`.
- `stack_relevance` naming something absent from `meta.stack`.
- A source listed but never cited.
- `status: "ok"` on a section with no items.
- An item id that does not start with its section id.
- A YouTube URL whose `source_type` is not `video`.
