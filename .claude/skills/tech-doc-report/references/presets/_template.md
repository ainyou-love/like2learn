# Writing a new preset

A preset is the subject of a report: who it is for, what their stack is, and
the list of topics to dispatch. Copy this file to
`references/presets/<slug>.md` and fill it in. One file, no code.

```markdown
# Preset: <slug>

<One paragraph: what this report tracks and who reads it.>

    slug:   <slug>                 # becomes the {report-what} in the filename
    reader: <who they are>
    stack:  <what they actually run>
    depth:  auto

## Lens

<One paragraph every brief carries: the angle the reader cares about across
all topics. Without it, each topic reads as its own changelog digest.>

## Must sweep

<The kinds of item a first pass drops and the reader cannot afford to miss:
security releases, breaking changes, dated obligations, and whatever else this
subject has. Step 2b checks every topic against this list.>

## Topics

| id | name | brief |
|---|---|---|
| A | <name> | <2-3 sentences: what belongs here, what does not, which sources to prefer> |
| B | <name> | ... |

## Notes for this preset

<Anything the research agents or the orchestrator need to know that is specific
to this subject: where unverified claims cluster, which topics are usually
thin, which numbers are always disputed.>
```

## Choosing topics

**Six to fourteen.** Below six, a report is a list and the sidebar has nothing
to do. Above fourteen, sections thin out until every one reads as "not much
happened", which tells the reader nothing about where to look.

**Split by where you would search, not by subject matter.** Topics exist so
that fourteen agents can work without overlapping. "Security" and "supply
chain" are one topic if you would run the same queries for both. "Database" and
"backend libraries" are two, because the sources have nothing in common.

**One topic, one kind of answer.** A topic that mixes "what shipped" with "what
people think about it" produces items that cannot share a `truth` value
honestly. Separate the release topic from the practice topic.

**Order by what the reader acts on first.** Sections render in `order`, and the
reader stops scrolling somewhere. Put the topic that changes this week's work
above the one that is interesting to know.

**Write the brief for an agent with no context.** Each brief is the entire
instruction one agent gets about its topic. "Database" tells it nothing; "Postgres
and its ecosystem: releases, extensions, branching tooling, migration practice,
pooling and driver changes" tells it where to look and where to stop. Say what
does *not* belong, too — that is what keeps two agents off the same ground.

## Lens and must sweep

**The lens is the question behind the topics.** Topics split the search so
agents do not overlap; the lens keeps them answering the same question. A
report on AI-assisted development whose database topic never mentions agents
has fourteen correct sections and misses its subject.

**The sweep list names what gets dropped, not what is important.** A topic
agent always finds the headline release. What it drops, once it has a few
items, is the security-only patch on an older branch, the SDK whose breaking
release broke someone else's install, the platform change enforced next month.
List those kinds of item, concretely enough that a sweep agent can search for
each one.

## Stack

`stack` drives `stack_relevance` on every item, the stack filter in the
sidebar, and the whole `stack_actions` block. Name the things the reader would
actually patch or upgrade — `Postgres`, `Next.js` — not categories like
"frontend". Confirm it with the user rather than inheriting it from another
preset; a stale stack makes those three features quietly useless while
still looking like they work.

## Reusing the id scheme

Section ids are letters by convention, and item ids are `{letter}-{nnn}`. Keep
both stable across periods for the same preset: it costs nothing, and it means
a deep link into one period's report still resolves to the same subject when
someone reads it beside the next one.
