---
name: self-optimize
description: "EXPERIMENTAL: Autonomous optimization loop inspired by Karpathy's autoresearch. Modify \u2192 measure \u2192 keep/discard \u2192 repeat. Use with a lens config to optimize any measurable domain."
allowed-tools: Read, Glob, Grep, Bash, Edit, Write, AskUserQuestion, mcp__database__execute_sql, mcp__database__get_advisors
---

# /self-optimize — Autonomous Optimization Engine

> **EXPERIMENTAL** — This skill is a sandbox. It will evolve. No hard expectations.
> Inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch) (630 lines, 50K stars, March 2026).
> See also: [pi-autoresearch](https://github.com/davebcn87/pi-autoresearch) (domain-agnostic adaptation).

## The Pattern

Autoresearch distilled to one sentence: **give an agent a metric and let it try things until the number improves.**

```
┌─────────────────────────────────────────────────────────────┐
│                    THE OPTIMIZATION LOOP                     │
│                                                             │
│   ┌──────────┐    ┌───────────┐    ┌─────────┐             │
│   │ DISCOVER │───>│ HYPOTHESIZE│───>│ EXECUTE │             │
│   │ baseline │    │ one change │    │ apply it│             │
│   └──────────┘    └───────────┘    └────┬────┘             │
│        ▲                                │                   │
│        │          ┌───────────┐    ┌────▼────┐             │
│        │          │   LEARN   │<───│ MEASURE │             │
│        │          │ log result│    │ run eval│             │
│        │          └─────┬─────┘    └────┬────┘             │
│        │                │               │                   │
│        │          ┌─────▼─────┐    ┌────▼────┐             │
│        └──────────│  REPEAT   │<───│ VERDICT │             │
│                   │ next idea │    │keep/toss│             │
│                   └───────────┘    └─────────┘             │
└─────────────────────────────────────────────────────────────┘
```

## When to Use

- `/self-optimize <lens>` — run optimization loop for a specific lens
- `/self-optimize` (no args) — list available lenses and their current baselines
- When you have time to experiment and a clear metric to improve

## When NOT to Use

- During active feature work (context switching kills both)
- When the metric isn't clearly measurable
- When changes need business/UX judgment (this is for objective metrics only)

---

## Step 0: Select Lens

If no lens argument, list available lenses from `lenses/` directory and ask.

Read the lens config file. It defines everything the engine needs:

- **Target**: what files/code to modify
- **Metric**: what number to optimize (and direction: lower/higher)
- **Evaluator**: the command that produces the metric
- **Safety**: checks that must pass before a change is kept
- **Scope boundaries**: what the agent must NOT touch

**The agent CANNOT modify its own evaluator.** This is the alignment constraint — like autoresearch's immutable `prepare.py`. The evaluation command, test suite, and safety checks are infrastructure the agent reads but never edits.

---

## Step 1: Discover (Establish Baseline)

Before changing anything:

1. **Run the evaluator** from the lens config to get the current metric value
2. **Record baseline** in the journal (Step 6)
3. **Read target files** to understand current state
4. **Check the journal** for previous runs — what's been tried, what worked, what's a dead end

Present to user:

```
Lens: [name]
Baseline: [metric value] [unit]
Previous runs: [N experiments, M kept]
Known dead ends: [list from journal, if any]
Target files: [list]
```

**Ask**: "Ready to start the optimization loop? How many iterations?" (default: 5 for copilot mode)

---

## Step 2: Hypothesize (Propose ONE Change)

Based on the lens target, the current code, and journal history (dead ends to avoid):

1. **Identify one specific, atomic change** to try
2. **Explain the hypothesis**: "If I [change], the metric should [improve] because [reasoning]"
3. **Predict the expected impact**: "I expect ~X% improvement"

**Rules**:

- ONE change per iteration. Never bundle multiple changes — you can't attribute improvement.
- Check the journal — don't re-try things that already failed.
- Start with high-confidence, low-risk changes. Save speculative ideas for later iterations.
- Stay within the lens scope boundaries. Never touch files outside the target list.

**In copilot mode**: Present the hypothesis and wait for user approval before executing.

---

## Step 3: Execute (Apply the Change)

1. **Create a git checkpoint**: `git stash` or note the current state
2. **Make the code change** using Edit/Write tools
3. **Verify syntax**: the change must not break parsing/compilation

Keep changes minimal and reversible.

---

## Step 4: Measure (Run the Evaluator)

1. **Run the safety checks** from the lens config FIRST (e.g., `npm run quality:check`)
   - If safety fails → change broke something → go to Step 5 (DISCARD)
2. **Run the evaluator command** from the lens config
3. **Record the new metric value**
4. **Calculate delta**: `new_metric - baseline` (or vs. best-so-far)

---

## Step 5: Verdict (Keep or Discard)

**KEEP if ALL true**:

- Safety checks passed
- Metric improved (in the direction defined by the lens)
- No regressions introduced

**DISCARD if ANY true**:

- Safety checks failed
- Metric worsened or unchanged
- Side effects detected

**On KEEP**:

```bash
git add [changed files] && git commit -m "self-optimize(<lens>): <what changed> (<delta>)"
```

Update the "best so far" baseline.

**On DISCARD**:

```bash
git checkout -- [changed files]
```

Log what was tried and why it failed (prevents re-trying dead ends).

Present result:

```
Iteration [N]: [KEPT ✓ / DISCARDED ✗]
Change: [what was tried]
Metric: [before] → [after] ([+/-delta])
Reason: [why kept/discarded]
Cumulative improvement: [total delta from original baseline]
```

---

## Step 6: Learn (Update the Journal)

After each iteration, append to the lens journal file (`lenses/<lens>-journal.md`):

```markdown
### Run [N] — [date]

- **Hypothesis**: [what and why]
- **Change**: [files modified, what changed]
- **Result**: KEPT / DISCARDED
- **Metric**: [before] → [after] ([delta])
- **Learning**: [what this teaches us for future iterations]
```

The journal is compound memory — each run makes future runs smarter. After 10+ runs, patterns emerge: "tree-shaking saves KB", "moving imports doesn't help", "shorter prompts reduce tokens but hurt quality."

**Create the journal file on first run if it doesn't exist.**

---

## Step 7: Repeat or Stop

**Continue if**:

- User approved more iterations
- Metric is still improving (not plateaued)
- There are untried hypotheses

**Stop if**:

- Iteration budget exhausted
- Last 3 iterations all discarded (plateau — diminishing returns)
- User says stop
- Safety check failure that indicates deeper issues

**On stop**, present summary:

```
Session complete: [N] iterations, [M] kept, [N-M] discarded

Original baseline: [value]
Final metric:      [value]
Total improvement:  [delta] ([%])

Key wins:
- [change 1]: [delta]
- [change 2]: [delta]

Dead ends discovered:
- [approach]: [why it didn't work]

Journal updated: lenses/<lens>-journal.md
```

---

## Trust Levels (Future Evolution)

Currently: **Copilot only** — every hypothesis shown to user before execution.

Future progression (not yet implemented):
| Level | Autonomy | Unlock criteria |
|-------|----------|-----------------|
| **Copilot** | User approves each change | Default |
| **Night shift** | Runs on feature branch, user reviews combined diff | 10+ successful experiments in this lens |
| **Full auto** | Runs, commits, opens PRs | Far future, if ever |

---

## Available Lenses

Lens configs live in `lenses/`. Each is a markdown file the engine reads.

| Lens               | Metric                                     | Speed                       | Status |
| ------------------ | ------------------------------------------ | --------------------------- | ------ |
| `bundle-size`      | Gzipped KB of critical path chunks         | Fast (build ~5s)            | Ready  |
| `eslint-warnings`  | Warning count                              | Fast (lint ~5s)             | Ready  |
| `telegram-prompts` | Feedback ratio + token cost                | Slow (needs deploy + usage) | Stub   |
| `social-content`   | Engagement rate (interactions/impressions) | Slow (days/weeks)           | Ready  |

Future lens ideas (not yet created):

- `lighthouse` — Core Web Vitals score
- `db-queries` — EXPLAIN ANALYZE cost of top RPC functions
- `test-speed` — Test suite execution time
- `landing-page` — SEO score, conversion metrics
- `outbound-copy` — Open/click/response rates

**Creating a new lens**: Copy `lenses/_template.md` and fill in the sections.

---

## Safety (Non-Negotiable)

These hold regardless of trust level or lens:

1. **Never touch `main` or `develop`** — all work happens on the current feature branch
2. **Never modify the evaluator** — test suite, build tools, lint config are immutable during a run
3. **Never skip safety checks** — `quality:check` must pass before any KEEP decision
4. **Never bundle changes** — one hypothesis, one iteration, one verdict
5. **Always log** — every attempt (success or failure) goes in the journal
6. **Budget cap** — stop after N iterations (user-defined, default 5 in copilot mode)

---

## Principles

1. **The metric is the judge** — not intuition, not "it should be better." Run the evaluator.
2. **One change at a time** — attribution requires isolation
3. **Dead ends are data** — a failed experiment that's logged is more valuable than one that's forgotten
4. **Compound learning** — the journal makes every run smarter than the last
5. **Minimal scaffolding** — the skill IS the engine. No external framework, no config schemas, no dashboards. Markdown all the way down.
6. **Evolve by doing** — the skill will change after every few real runs. That's the point.

---

## Skill Pipeline

```
/self-optimize <lens>     → runs the optimization loop
/self-optimize            → lists lenses, shows baselines
/self-optimize --journal  → reviews past experiments across all lenses

Fits into the broader workflow:
/investigate → /self-optimize → /code-review → /qa → commit → /deploy
```

---

## References

- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) — The original pattern (ML training optimization)
- [pi-autoresearch](https://github.com/davebcn87/pi-autoresearch) — Domain-agnostic adaptation with confidence scoring
- [Anthropic: Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Addy Osmani: Self-Improving Coding Agents](https://addyosmani.com/blog/self-improving-agents/)
