# Preset: ai-dev

AI-assisted software development, tracked for a full-stack developer working
across web, mobile and backend. This is the default preset.

    slug:   ai-dev
    reader: full-stack developer (web + mobile + backend)
    stack:  Postgres, Python, TypeScript, Next.js, React Native/Expo
    depth:  auto (follows the window)

Confirm the stack with the user before dispatching — it drives
`stack_relevance`, the stack filter and the whole `stack_actions` block, and a
stale stack makes those three quietly useless.

## Lens

Every topic brief carries this lens verbatim:

> The reader works with AI coding agents every day, so this report answers two
> questions at once: what changed in the stack, and what changed in how a
> developer works with agents on it. Besides what shipped, look for what this
> topic's tools ship *for agents* — MCP servers, agent skills, AGENTS.md or
> bundled docs, agent-facing CLIs — and how practitioners report using them. An
> agent-facing feature of a stack tool belongs in that tool's topic, not in G.

Without it, the stack topics read as a changelog digest and the agent side of
the subject disappears — the first run of this preset missed Expo's MCP server,
Supabase's MCP token cost and Next.js's agent dev-loop skill for exactly that
reason.

## Must sweep

The first pass of a topic agent finds the biggest items and stops. These are
the kinds of item that get dropped when it does, and they are the ones a reader
can least afford to miss. They go into every brief, and step 2b's sweep pass
checks for them explicitly:

- security releases and advisories for every part of the stack the topic
  touches, including security-only releases of older supported branches
- breaking releases: new majors, changed defaults, dropped support, and
  libraries whose missing upper bound turned someone else's release into your
  broken install
- dated obligations: deprecations, shutdowns, enforced platform changes,
  end-of-life dates
- for A, B and G: what independent communities visibly converged on, shown by
  the same thing recurring across separate sources

## Topics

Fourteen topics, dispatched as fourteen parallel agents. Each `brief` goes
into that agent's prompt verbatim, together with the lens and the sweep list above.

| id | name | brief |
|---|---|---|
| A | Sources & people | Who practitioners of agent-assisted coding actually follow, and why: authors, blogs, newsletters, podcasts, YouTube channels, subreddits, Discords. Evidence of standing — cited by other practitioners, recurring in community threads, invited talks — not a list of names. A long-running guide or channel counts when it published something new in the window (`older_context` if it started earlier). Framework blogs and changelogs do not belong here; they are the stack topics' sources. |
| B | GitHub repos | Repos that gained real traction in the window around working with agents: harnesses, skill collections, memory layers, gateways, MCP servers, document tooling for agents, a project that replaced a common approach. Star growth is the story here: report the gain with its source, mark counts `UNVERIFIED` unless read from GitHub itself, and put differing counts in disagreements. Releases of the reader's own frameworks and tools (TypeScript, Next.js, uv) belong to D, E and F, not here. |
| C | Workflows & thinking | How people actually work with coding agents: prompting and context management; how work is split across skills, hooks, subagents, MCP and scripted workflows; review and triage of agent-written PRs; permission and credential practice for agents; what practitioners report abandoning. |
| D | Full-stack web/mobile | Framework and runtime changes touching the reader's web and mobile stack: Next.js, React Native/Expo, bundlers, auth libraries, UI libraries, deployment targets. Include what these frameworks and libraries ship for agents: MCP servers, agent skills, AGENTS.md or bundled docs, and devtools an agent can drive to verify its own work (browser, simulator, device). |
| E | Database | Postgres and its ecosystem: releases and what the next major gains or loses, extensions, branching and preview-database tooling, migration and schema-diff practice, pooling, drivers and ORMs' database side. Include agent-facing database tooling — MCP servers for Postgres and hosted platforms, their token cost and read-only modes — and hosted-platform policy changes that carry a deadline. |
| F | Backend languages & libs | Python and TypeScript language and library changes: interpreter and runtime releases, including security-only releases of older supported branches; type checkers; packaging and dependency tooling; ORMs and web frameworks; alternative runtimes. Include AI SDKs and agent frameworks (vendor SDKs, Pydantic AI, LangChain, Vercel AI SDK) — a breaking SDK release that breaks downstream installs is exactly the item this topic exists for. |
| G | CLI & terminal | Command-line tooling a developer uses daily: agent CLIs, agent multiplexers and terminal workspaces for running several agents in parallel, shell and terminal tooling, and anything that changed how a terminal session is driven. A new tool qualifies on evidence of adoption — trending, star growth, community threads — not on its launch post alone. |
| H | Security & supply chain | Package-registry incidents, malicious releases, preinstall-hook abuse, lockfile and provenance tooling, advisories affecting the reader's stack. Bias toward the actionable. |
| I | Testing, QA, evals | Test tooling, and how teams evaluate AI-generated code and agent behaviour: harnesses, benchmarks, review gates. |
| J | Observability & cost | Tracing, logging and cost attribution, especially for LLM-backed features: token accounting, latency budgets, spend control. |
| K | Models & pricing | Model releases, deprecations, context-window and pricing changes, and rate-limit or availability shifts — including the open-weight and low-cost models developers route coding work to, and independent benchmark indexes that score agent-plus-model pairs. Vendor self-benchmarks are VENDOR_CLAIM. |
| L | DevOps, CI/CD, infra | Pipeline and platform changes: runners, caching, build times, deployment platforms, container and edge runtimes. |
| M | Standards & protocols | Specs and protocols that affect integration work: MCP, tool-calling formats, auth standards, RFCs and PEPs that reached a new status. |
| N | Career & team impact | Evidence only. Measured effects on how teams work and hire — surveys with a method, published postmortems, company-level reports. No speculation about the future of the profession. |

## Notes for this preset

**Section id = topic letter, item id = `{letter}-{nnn}`.** Keep them stable
across reports so a link to `#vi/report/H-001` from one period still means
something when someone reads it next to the following period's report.

**H and K are where the schema's honesty machinery earns its place.** Security
reporting attracts unverified claims, and model pricing is largely announced by
the parties selling it. Expect `UNVERIFIED` and `VENDOR_CLAIM` in both, expect
`conflicts[]` entries in K, and do not let a vendor's own benchmark through as
`FACT`.

**N is the easiest topic to fill with nothing.** "AI is changing engineering
careers" is not a finding. If there is no survey with a stated method, no
published postmortem and no company-level report inside the window, set
`status: "empty"` and move on.

**C is the topic most worth the reader's time and the hardest to source.**
Prefer practitioners describing what they changed and why over anyone selling
a workflow. A blog post with a before and after beats ten posts with a list of
tips.

**A, B and G live on community evidence.** Who is worth following, which repo
took off and which CLI people switched to are not announced in changelogs;
they show up in Reddit threads, Hacker News, Discords, podcasts and trending
pages. Cite those as sources with a low or medium `trust`, and keep a claim
`UNVERIFIED` until a primary source or a second independent community backs
it. A topic built only from official pages will describe the vendors' view of
the quarter, not the practitioners'.
