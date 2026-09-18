# Figure catalog

Eleven renderers ship in `assets/figure-renderers.js`, with their classes in
`assets/base.css`. Each takes one `FIG` entry and returns DOM.

A figure earns its place when it shows something prose cannot: ordering,
proportion, a gap, two things side by side. **A diagram that restates a sentence
is noise** — delete it and keep the sentence.

Every entry takes `type` (picks the renderer) and `cap` (the caption, rendered
through the inline markdown formatter, so backticks and `**bold**` work).

## Choosing a shape

| The content is… | Use | Because |
|---|---|---|
| a numbered set of criteria, plus how many were met | `questions` | the score tiles make the measurement the punchline |
| the same system measured twice, one variable removed | `proof` | two big numbers side by side carry the whole argument |
| node labels and the edges between them | `graph` | grouped edge rows stay readable where a drawn graph would not |
| a cycle of steps that returns to its start | `loop` | numbered rows plus an explicit "back" line |
| a surface split into tiers of disclosure | `levels` | name + one-line purpose, grouped under a tier header |
| one rule satisfied by any of several alternatives | `routes` | a funnel: one input, parallel routes, one refusal |
| event sources and what each delivers | `hooks` | three fields per row: trigger, who it reaches, payload |
| thresholds a thing must pass | `gates` | condition on the left, the measured number on the right |
| the same store partitioned by key | `islands` | source on the left, resulting partition on the right |
| timings or magnitudes to compare | `bars` | proportion is the point, so draw proportion |
| two mechanisms where one is the real guarantee | `guards` | side-by-side panels with different accent colours |

## Data shapes

    questions   { items: [string],
                  scores: [{ n: '4/4', label: string, kind: 'good'|'bad' }] }

    proof       { rows: [{ kind: 'keep'|'gone', n: '4/4',
                           what: string, detail: string }],
                  note: string }

    graph       { nodes:  [[label, isCore]],
                  groups: [{ title: string,
                             edges: [[from, REL_NAME, to]] }] }

    loop        { steps: [string], back: string }

    levels      { levels: [{ name: string, note: string,
                             tools: [[name, description]] }] }

    routes      { top: string,
                  routes: [[name, description]],
                  bottom: string }

    hooks       { rows: [{ hook: string, reaches: string,
                           carries: string, none?: true }] }

    gates       { rows: [[condition, detail]] }

    islands     { rows: [{ where: string, scope: string, shared?: true }],
                  note: string }

    bars        { rows: [{ label: string, ms: number,
                           val: string, cold?: true }] }
                  -- `ms` sets the bar width, `val` is the printed number,
                     so "9–19 ms" can display while 19 drives the geometry

    guards      { rows: [{ kind: 'fast'|'bound', tag: string, text: string }] }

## Writing a new renderer

Two things to add, and nothing else:

1. A function in `FIGURE` taking the entry and returning DOM, built with `el()`.
   It must not read `STATE` — components are pure so they can be tested by
   calling them with a literal object.
2. Its classes in the stylesheet, using the existing tokens so the figure
   inherits both themes for free.

Keep figures as CSS and HTML rather than images: they reflow on a phone, they
follow the theme, and they cost nothing to translate.

## Reusing a shape honestly

The shapes are generic on purpose, but do not force content into one that nearly
fits. `bars` for things that are not comparable magnitudes, or `proof` for two
numbers that were not measured the same way, produces a figure that looks
authoritative and says something false. Write the new renderer — it is about
twenty lines.
