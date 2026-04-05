---
name: brainstorm
description: Interactive ideation workshop using design thinking. Use before /plan when the problem or solution isn't obvious.
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion, WebFetch, mcp__database__list_tables, mcp__database__execute_sql, mcp__shadcn__search_items_in_registries, mcp__shadcn__view_items_in_registries, mcp__chrome-devtools__take_snapshot
---

# Brainstorm Skill

Interactive ideation workshop between Claude and the user. Two minds building on each other's knowledge to arrive at the right solution before planning.

**A valid outcome is "we're not doing this."** Killing or deferring an idea is a successful brainstorm.

## When to Use

- Problem is unclear or has multiple valid interpretations
- Solution isn't obvious — multiple approaches could work
- New feature with business/UX implications
- `/brainstorm`, "let's think about this", "I have an idea", "how should we approach..."

## When NOT to Use

- Problem and solution are both clear → go straight to `/plan`
- Bug fix with obvious root cause → `/plan` or `/diagnose`
- User gives specific instructions ("add a button that does X") → just do it or `/plan`
- Need facts, not a decision → run `/research` first, then come back if a decision is needed

---

## Timebox

**15-30 minutes**. Converge by **45 minutes max**. If not converging, the problem needs to be split — that itself is a valid outcome.

---

## The Session

### Phase 1: Empathize — Understand the Real Problem

Users often describe solutions, not problems. Dig into the _why_.

1. Listen to the initial idea
2. Use `AskUserQuestion` to dig deeper:
   - "What's the pain point this solves?"
   - "Who experiences this? (admin, customer, both?)"
   - "How are you working around this today?"
3. Use MCP tools to gather facts — **only after you have a draft problem statement AND a specific question to answer** (prevents tool-happy wandering)

**Output**: A clear problem statement both sides agree on — or a realization the problem isn't worth solving now.

### Phase 2: Define — Frame the Challenge

Reframe as "How Might We" (HMW) questions. Present 2-3 variations:

> "How might we [solve problem] for [user type] so that [desired outcome]?"

Use `AskUserQuestion`: "Which best captures what you're after?"

**Output**: One agreed HMW question that scopes the ideation.

### Phase 3: Ideate — Generate Options

**Before generating options**: Scan `.claude/references/claude-cookbooks.md` for relevant patterns. If a cookbook pattern applies, reference it as an option or as prior art for an option. Use `WebFetch` to pull details from specific cookbook links if needed.

**Rules**: Quantity first, build on ideas ("yes, and..."), no judging yet, "do nothing" is always a valid option.

| Option                 | Description  | Pros       | Cons          | Feasibility  |
| ---------------------- | ------------ | ---------- | ------------- | ------------ |
| A                      | [approach]   | [benefits] | [drawbacks]   | Low/Med/High |
| B                      | [approach]   | [benefits] | [drawbacks]   | Low/Med/High |
| C                      | [approach]   | [benefits] | [drawbacks]   | Low/Med/High |
| **Do nothing / Defer** | Keep current | No effort  | Problem stays | -            |

For each option, bring technical context:

- "Option B reuses the existing `feature_config` pattern"
- "Option C needs a new DB table but gives flexibility for future personas"

**Output**: 1-2 shortlisted approaches — or a decision to defer/kill.

### Phase 4: Evaluate — Stress-Test the Favorite

**Skip if decision is defer or kill.**

| Question                                               | Answer   |
| ------------------------------------------------------ | -------- |
| Does this work at 10x load?                            | [assess] |
| What happens when it fails?                            | [assess] |
| Can this be feature-flagged?                           | [yes/no] |
| Does this extend existing patterns or create new ones? | [assess] |
| Is this reversible without a rollback?                 | [yes/no] |

**Output**: A validated approach with known trade-offs explicitly accepted.

### Phase 5: Converge — Declare the Decision

Three valid endings:

**BUILD**: Problem, HMW, decision, trade-offs accepted, options rejected. → "Run `/plan` to create the implementation document."

**BUILD** (UI feature): Problem, HMW, decision, trade-offs accepted. → "Run `/ux-design` to design the user experience, then `/plan` for implementation."

**DEFER**: Problem, why defer, revisit trigger. → Added to BACKLOG.md.

**KILL**: Original idea, why not doing it. → No further action.

---

## Principles

1. **Be a thinking partner, not a question machine** — Contribute ideas, challenge assumptions, offer technical alternatives.
2. **Use MCP to bring facts** — Don't debate "how many orders" — query and know.
3. **Phases are flexible** — Sometimes jump from Empathize to Ideate because the problem is clear.
4. **End with a decision** — Every brainstorm must converge. Open-ended ideation without a conclusion is waste.
5. **No documents produced** — The conversation IS the artifact. `/plan` captures the decision. Exception: DEFER adds to BACKLOG.md.
6. **Respect domain knowledge** — User knows the domain. You know the architecture. Best ideas come from the intersection.
7. **Killing is a win** — Preventing the wrong thing is more valuable than greenlighting the right thing.
8. **Enforce the timebox** — At 30 minutes, actively push toward convergence. At 45, declare the outcome even if imperfect.

---

## Anti-Patterns

- Jumping to solutions before understanding the problem
- Presenting only one option (that's a recommendation, not ideation)
- Skipping the Evaluate phase when building (leads to plans that fail review)
- Producing a document (that's `/plan`'s job)
- Running through phases mechanically without genuine back-and-forth
- Treating "defer" or "kill" as failure
- Pushing toward "build" when the honest answer is "not worth it right now"
- Letting the session drift past 45 minutes without converging

---

## Skill Pipeline

```
/research → /brainstorm → /ux-design → /plan → /sign-off → CEO approval → /worktree create → implement → /code-review → /qa → commit → push → PR → /review-pr (in develop)
                  ↑
             you are here (optional — skip if problem+solution are clear)
```
