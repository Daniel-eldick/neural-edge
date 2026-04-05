---
name: research
description: >-
  Conducts structured internet research with confidence-tagged findings.
  Three gears: Quick Scan (facts), Investigation (comparison/best practices),
  Deep Research (landscape analysis with parallel agents).
  Use before /brainstorm or /plan when current external knowledge is needed.
  Triggers: /research, "research this", "what's the current state of", "compare X vs Y".
allowed-tools: WebSearch, WebFetch, Read, Glob, Grep, AskUserQuestion, Task, mcp__database__execute_sql, mcp__database__list_tables
---

# Research Skill

Structured internet investigation that produces confidence-tagged, sourced findings. Three gears match depth to question complexity. Output is conversation — no document produced.

**A valid outcome is "not enough reliable information exists."** Honest gaps beat fabricated findings.

## When to Use

- Question requires current external knowledge (beyond training data cutoff)
- Technology evaluation, standards, best practices, feasibility, competitive analysis
- `/research`, "research this", "what's the latest on", "compare X vs Y"

## When NOT to Use

- Answer is in the codebase (use Grep/Read directly)
- Decision needed, not knowledge (`/brainstorm`)
- Problem and solution both clear (`/plan`)

---

## Step 1: Scope

Restate the user's question as a crisp **research question**. This prevents drift.

**Classify the gear:**

| Gear    | Name          | When                                     | Duration | Searches | Steering   |
| ------- | ------------- | ---------------------------------------- | -------- | -------- | ---------- |
| **1st** | Quick Scan    | Single factual question                  | ~5 min   | 2-3      | None       |
| **2nd** | Investigation | Comparison, best practice, evaluation    | ~15 min  | 5-8      | 1 round    |
| **3rd** | Deep Research | Landscape, architecture, market analysis | ~30 min  | 10+      | 2-3 rounds |

**Auto-detection heuristic:**

- 1st: "What version...", "Is X still...", "Does Y support...", version checks
- 2nd: "What's the best...", "How should we...", "Compare X vs Y"
- 3rd: "Full landscape of...", "How do others solve...", "Architecture for..."

**Override**: User says "go deeper" at any time -> shift up. "That's enough" -> synthesize immediately.

**For 2nd/3rd gear**: Use `AskUserQuestion` to clarify scope if ambiguous.

**For 3rd gear**: Decompose into 3-5 **sub-questions** before searching.

> Example: "Best analytics for our stack" ->
>
> 1. What are the top analytics tools for React SPAs in 2026?
> 2. How do they compare on bundle size? (Lebanon bandwidth constraint)
> 3. What's the self-hosted vs cloud trade-off?
> 4. How do they integrate with our backend stack?

Present gear + research question to user. Proceed unless they redirect.

---

## Visibility Control — What the CEO Sees

**Show the CEO (interactive moments):**

- Step 1 (Scope): Gear + research question — confirm or redirect
- Step 4 (Steer): Findings summary with substance — pick direction
- Step 6 (Synthesize): Final CEO-brief

**Do silently (no narration, no play-by-play):**

- Steps 2-3 (Search + Triangulate): Just do the work. Don't say "let me search for X now" — search and come back with findings.
- Step 5 (Critique): Internal self-review. Only surface to CEO if a gap requires their input.

**Why**: The CEO's time is the scarcest resource. Research noise (query formulation, intermediate results, source-by-source commentary) wastes it. Deliver signal at checkpoints, work silently between them.

---

## Step 2: Search

### Query Formulation Strategy

For each angle or sub-question, craft 2-3 **varied** search queries:

| Query Type             | Purpose               | Example                                          |
| ---------------------- | --------------------- | ------------------------------------------------ |
| **Specific technical** | Precise data points   | "Sentry vs Datadog React SDK bundle size 2026"   |
| **Broad context**      | Industry landscape    | "best analytics tools for SPA 2026"              |
| **Community/opinion**  | Real-world experience | "Sentry production experience site:reddit.com"   |

**Rules:**

- **Always include current year** in queries (training data cutoff is real)
- Use `WebFetch` to deep-read promising sources, not just search snippets
- For 3rd gear: launch parallel `Task` agents (subagent_type: `general-purpose`) for independent sub-questions
- Don't search randomly — every query must tie back to the research question or a sub-question

### Search Depth by Gear

| Gear | WebSearch calls | WebFetch deep-reads | Task agents                        |
| ---- | --------------- | ------------------- | ---------------------------------- |
| 1st  | 2-3             | 0-1                 | None                               |
| 2nd  | 5-8             | 2-3                 | None                               |
| 3rd  | 10+             | 4-6                 | Yes, for independent sub-questions |

---

## Step 3: Triangulate

Cross-reference findings across sources. Tag each finding:

| Confidence | Criteria                                                           |
| ---------- | ------------------------------------------------------------------ |
| **HIGH**   | 3+ independent sources agree, recent (< 12 months), authoritative  |
| **MEDIUM** | 2 sources agree, or single authoritative source, or slightly dated |
| **LOW**    | Single source, conflicting info found, or > 18 months old          |

**Rules:**

- Single-source claims get LOW, period
- Flag contradictions explicitly — present both sides, don't silently pick a winner
- Note when information is dated — "as of [date]" qualifiers matter

---

## Step 4: Steer (2nd/3rd gear only)

### Readiness Gate — Don't Steer on Thin Data

**Before presenting to the CEO, verify ALL of these:**

- [ ] Each option/contender has at least one pro AND one con identified
- [ ] At least 1 deep-read (WebFetch) done, not just search snippets
- [ ] Enough substance for the CEO to pick a direction without asking "but what about...?"

**If not ready**: Do another search round first. Steering on thin data wastes the CEO's time and produces a bad steering decision.

### Steering Prompt

Present findings summary. Use `AskUserQuestion`:

> "Here's what I've found so far. Which threads should I pull deeper?"

Options should reflect the most interesting/divergent findings.

- User selects areas -> focused follow-up searches (back to Step 2 for those threads)
- 3rd gear: repeat steer cycle 2-3 times
- If user says "that's enough" -> skip to Step 6

---

## Step 5: Critique

Self-review before synthesizing:

- Are there obvious gaps in the findings?
- Did any sub-question go unanswered?
- Are there claims with only LOW confidence that matter?

**If gaps found**: Loop back to Step 2 with targeted queries.

- 2nd gear: max 1 critique loop
- 3rd gear: max 2 critique loops

**If no gaps**: Proceed to synthesis.

---

## Step 6: Synthesize

**CEO-brief format**: Compact, scannable, signal over noise. Details available on request.

```markdown
## Research: [Research Question]

**Gear**: [1st/2nd/3rd] | **Sources**: [N]

### Findings

| #   | Finding            | Confidence   | Source |
| --- | ------------------ | ------------ | ------ |
| 1   | [One-line finding] | HIGH/MED/LOW | [link] |
| 2   | [One-line finding] | HIGH/MED/LOW | [link] |

### Open Questions

- [Unanswered question or contradiction — one line each]

### So What? (Codebase Bridge)

- [1-3 bullets: what this means for your project specifically]

### Next Step

[Single line: `/brainstorm`, `/plan`, or "no action needed" + why]
```

**For comparison research** (2+ options evaluated), replace the findings table with:

```markdown
### Comparison

| Option | Best for          | Blocker for us?    | Confidence   |
| ------ | ----------------- | ------------------ | ------------ |
| [name] | [1-line strength] | Yes: [reason] / No | HIGH/MED/LOW |

### Other Findings

| #   | Finding                                              | Confidence   | Source |
| --- | ---------------------------------------------------- | ------------ | ------ |
| 1   | [Market/context finding not tied to a single option] | HIGH/MED/LOW | [link] |
```

The "Blocker for us?" column is the signal — it immediately filters options through your project's constraints (bandwidth, stack, architecture, etc.).

**Rules:**

- **Findings table, not paragraphs** — one row per finding, one sentence max
- Confidence tag + source link on every row
- "So What?" section is mandatory — raw findings without project context are waste
- **Details on demand** — if CEO asks "tell me more about finding #3", expand that one finding only
- Sources section omitted from output (links are inline in the table) — reduces noise
- Next step routes to the right skill in a single line

---

## Stopping Criteria

| Gear | Done When                                                                         |
| ---- | --------------------------------------------------------------------------------- |
| 1st  | Answer found with 2+ agreeing sources                                             |
| 2nd  | Research question answered across all angles, critique finds no gaps              |
| 3rd  | All sub-questions answered, 2+ steer rounds complete, critique loop finds no gaps |

**Timebox enforcement**: At max duration, synthesize what you have. Partial findings with honest gaps > infinite research.

---

## Principles

1. **Methodology over topic** — The skill is about HOW to research, not WHAT
2. **Confidence over completeness** — Tagged uncertainty > false certainty
3. **Gear-appropriate depth** — Don't run a 30-min investigation for "what version is React?"
4. **Sources are non-negotiable** — Every claim must be traceable
5. **Steering is a feature** — User controls depth, not the skill
6. **Cross-reference always** — Single-source claims get LOW confidence
7. **Current year in queries** — Always search for current information
8. **CEO-brief, not research paper** — Table of findings, not walls of text. Details on demand only
9. **Honest gaps beat fabrication** — "Limited data available" is a valid finding

---

## Anti-Patterns

- Searching without a clear research question (tool-happy wandering)
- Trusting a single source for a major claim
- Presenting findings without confidence tags
- Running 3rd gear for a simple factual question (gear mismatch)
- Fabricating findings when sources are scarce
- Letting research drift past timebox without synthesizing
- Skipping the codebase bridge
- Over-researching when user says "that's enough"
- Premature steering (presenting options before each has pros AND cons)
- Narrating search-by-search progress instead of working silently between checkpoints

---

## Skill Pipeline

```
/research -> /brainstorm -> /ux-design -> /plan -> /sign-off -> ...
    ^
you are here (optional — skip if you already have the facts)
```

---

## Summary + Next Step (CEO Footer)

The synthesis (Step 6) already includes a `### Next Step` section. Add a 2-line **Summary** block above it:

```
**Summary**: [1 sentence — key takeaway from the research, plain language]
**Confidence**: HIGH / MEDIUM / LOW (overall — based on source quality and agreement)
```

This pairs with the existing `### Next Step` line to form the complete CEO footer.
