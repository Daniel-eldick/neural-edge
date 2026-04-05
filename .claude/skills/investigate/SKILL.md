---
name: investigate
description: >-
  Tiered internal codebase research. Acts as a system architect — takes plain
  English questions, knows where to look, produces structured insights, and
  maintains a living knowledge map. Three tiers: Quick (1-2 min), Investigate
  (5-10 min), Audit (15-30 min). Looks inward (code, docs, git) not outward.
  Triggers: /investigate, "how does X work?", "trace the flow of", "is X correct?"
allowed-tools: Read, Edit, Write, Grep, Glob, Bash, Task, AskUserQuestion, mcp__database__execute_sql, mcp__database__list_tables
---

# Investigate Skill

Structured internal research that produces architect-level insights about your codebase. Three tiers match depth to question complexity. Maintains a living knowledge map that improves with every use.

**A valid outcome is "this needs a specialist skill."** Knowing when to hand off to `/db-audit`, `/perf-audit`, or `/diagnose` is a feature, not a failure.

## When to Use

- `/investigate`, "how does X work?", "where is Y?", "trace the flow of Z"
- Before modifying a system — understand its tentacles first
- "Something feels off" — investigating a hunch about drift or dormant issues
- "Catch me up" — deep-dive beyond `/session-start` into specific systems
- Session-internal: Claude can follow this protocol silently during other work

## When NOT to Use

- Question requires external/internet knowledge (use `/research`)
- Specific error to debug (use `/diagnose`)
- Running tests (use `/test`)
- Deep database security/performance audit (use `/db-audit`)
- Bundle size or Core Web Vitals (use `/perf-audit`)
- Checking doc synchronization (use `/sync-docs`)
- Monthly code cleanup (use `/hygiene`)

---

## Knowledge Map

**File**: `memory/knowledge-map.md` — a living structural index of the codebase.

**Lifecycle**:

1. **Seeded** from CLAUDE.md + ORIENTATION.md architecture sections (done at skill creation)
2. **Consulted** at the start of every investigation (Step 2)
3. **Verified** against actual code when entries are consulted — if reality doesn't match, update the map
4. **Grown** by appending new structural findings after each investigation (Step 5)
5. **Pruned** when verification finds stale entries — delete or correct them

**What goes IN the map** (structural facts):

- Where systems live (directories, key files, entry points)
- How systems connect (data flows, provider hierarchy, event chains)
- What consumes what (callers, dependencies)
- Quick lookups (common questions → direct file:line answers)

**What stays OUT** (goes elsewhere):

- Lessons learned, gotchas, behavioral knowledge → `memory/MEMORY.md`
- Patterns noticed, smells, hunches → `memory/observations.md`
- Detailed investigation findings → conversation output (ephemeral)

**Staleness rule**: Entries older than 90 days without verification should be treated as hints, not facts. Always verify against code before trusting old entries.

---

## Step 1: Parse & Classify

Restate the question as a crisp **investigation question**. Then classify:

### Tier (auto-detect from phrasing, override with flag)

| Tier            | Trigger Phrases                                                           | Duration  | Tool Budget                        |
| --------------- | ------------------------------------------------------------------------- | --------- | ---------------------------------- |
| **Quick**       | "where is", "what is", "show me", "find"                                  | 1-2 min   | 3-5 tool calls                     |
| **Investigate** | "how does", "why does", "explain", "trace", "what calls"                  | 5-10 min  | 8-15 tool calls                    |
| **Audit**       | "is X correct?", "validate", "are there issues with", "compare X to docs" | 15-30 min | 15-30 tool calls, may spawn agents |

**Override**: User says `--quick`, `--investigate`, or `--audit` to force a tier.

### Category (determines where to look)

| Category                    | Signal Words                                                    | Primary Sources                                    | Secondary Sources                    | Specialist Handoff            |
| --------------------------- | --------------------------------------------------------------- | -------------------------------------------------- | ------------------------------------ | ----------------------------- |
| **Architecture / flow**     | "how does", "flow", "architecture", "provider", "hierarchy"     | knowledge-map.md, docs/guides/, src/App.tsx        | git log for "why" decisions          | —                             |
| **Feature implementation**  | "where is", "how is X built", "component", "hook", "page"       | src/components/, src/hooks/, src/contexts/         | docs/completed/ for original plan    | —                             |
| **Bug investigation**       | "something is wrong", "feels off", "broken", "failing"          | git log --since (recent changes), error boundaries | test files covering the area         | `/diagnose` if specific error |
| **Doc vs code drift**       | "is X still accurate", "does code match docs", "drift"          | docs/ vs src/ side-by-side                         | git blame for when they diverged     | `/sync-docs` for full scan    |
| **Database**                | "table", "column", "RLS", "policy", "schema", "migration"       | Database MCP list_tables, migrations/              | database types file   | `/db-audit` for deep analysis |
| **Performance**             | "slow", "bundle", "load time", "render", "memory"               | Component tree, lazy-loading config                | TECHNICAL_DEBT.md                    | `/perf-audit` for full audit  |
| **Prepare for change**      | "before I change", "what depends on", "blast radius", "callers" | Grep for imports/callers, dependency graph         | test files covering the area         | —                             |
| **Code patterns**           | "convention", "pattern", "how do we handle", "standard"         | Grep across src/, existing implementations         | CLAUDE.md conventions section        | `/hygiene` for drift          |
| **Git history / decisions** | "why was", "when did", "who changed", "history of"              | git log, git blame, gh pr list                     | docs/completed/ for planning context | —                             |

**Multiple categories**: Questions often span 2 categories. Use the primary for source priority, check both.

---

## Step 2: Consult Knowledge Map

Read `memory/knowledge-map.md`. Look for entries matching the investigation question.

- **Entry found, recent**: Use as starting point. Verify 1-2 key claims against actual code.
- **Entry found, old (>90 days)**: Treat as hint only. Verify before trusting.
- **No entry found**: Proceed to Step 3. This is expected — the map grows over time.

**If entry is stale**: Correct it inline during Step 5. This is the self-healing mechanism.

---

## Step 3: Execute Investigation

Follow the routing table from Step 1. Scale tool usage to the tier.

### Quick Tier (3-5 tool calls)

1. Grep/Glob for the target (file, function, component, type)
2. Read the key file(s)
3. Answer with file:line references

### Investigate Tier (8-15 tool calls)

1. Start from knowledge map entry or routing table's primary sources
2. Read entry point file(s) for the system
3. Trace connections: imports, callers, consumers (Grep for the export name)
4. Check test coverage: Glob for related test files
5. Optionally check git history: `git log --oneline -10 -- [path]` for recent changes
6. For cross-system flows: trace data through each layer

### Audit Tier (15-30 tool calls, agents allowed)

1. Full Investigate tier, PLUS:
2. Read the relevant documentation (docs/guides/, docs/completed/)
3. Compare documentation claims against actual code — flag discrepancies
4. Check for patterns that should exist but don't (missing error handling, missing tests)
5. For broad audits: spawn `Task` agents (subagent_type: `Explore`) for parallel sub-investigations
6. Cross-reference with TECHNICAL_DEBT.md — is this system mentioned?
7. If database-adjacent: lightweight Database MCP queries (save deep analysis for `/db-audit`)

### Git Investigation Commands

```bash
# Recent changes to a file/directory
git log --oneline -20 -- src/path/

# Who last changed a specific area
git log --oneline --since="2 months ago" -- src/path/

# Why a specific line exists
git blame -L 40,60 src/path/file.ts

# PR history for a path
gh pr list --state merged --search "path/keyword" --limit 10
```

---

## Step 4: Synthesize

**Never dump raw tool output.** Always structure findings.

### Quick Output

```markdown
## [Restated question]

**Answer**: [Direct answer in 1-3 sentences]

**Location**: [file.ts:line](src/file.ts#Lline)

**Key files**:

- [file.ts](src/file.ts) — [what it does]
```

### Investigate Output

```markdown
## Investigation: [Restated question]

**Tier**: Investigate | **Sources**: [N files, N tool calls]

### How It Works

[Architecture summary — 3-8 sentences explaining the system. Use a flow diagram if helpful:]
```

Component A → Component B → Database
↓ (on failure)
Retry logic → ...

```

### Key Files

| File | Purpose | Key lines |
|------|---------|-----------|
| [file.ts](src/file.ts) | [role] | L42-60: [what happens] |

### Connections

- **Depends on**: [upstream systems/providers/hooks]
- **Consumed by**: [downstream components/pages]
- **Tests**: [test files covering this]

### Notable

[Anything surprising, risky, or worth remembering — patterns, gotchas, technical debt]
```

### Audit Output

```markdown
## Audit: [Restated question]

**Tier**: Audit | **Sources**: [N files, N docs, N tool calls]

### Summary

[2-4 sentence assessment — is this system healthy?]

### Findings

| #   | Finding | Severity     | Evidence                     | Recommendation |
| --- | ------- | ------------ | ---------------------------- | -------------- |
| 1   | [issue] | Low/Med/High | [file:line or doc reference] | [what to do]   |

### Doc vs Code Alignment

| Doc Claim       | Code Reality     | Status                    |
| --------------- | ---------------- | ------------------------- |
| [what docs say] | [what code does] | Aligned / DRIFT: [detail] |

### Specialist Handoffs

[If deeper analysis needed: "Run `/db-audit` for RLS policy review" etc.]

### Notable

[Patterns, risks, or observations worth capturing]
```

---

## Step 5: Update Knowledge Map

After every investigation, check if new structural facts were discovered.

**Update if**:

- A new system/domain was explored that's not in the map
- An existing entry was found to be inaccurate (self-heal)
- New cross-system connections were traced
- Key files or entry points were identified

**Skip update if**:

- The investigation only confirmed what the map already says
- The finding is behavioral (goes to MEMORY.md) not structural
- The finding is a smell/hunch (goes to observations.md)

**Update format**: Edit `memory/knowledge-map.md` — update the relevant section, set `Last verified: [date]`.

**Also consider**: If the investigation revealed something surprising or noteworthy, append to `memory/observations.md`.

---

## Specialist Handoff Table

When investigation reveals the question needs deeper specialized analysis:

| Signal During Investigation                               | Hand Off To   | What to Say                                              |
| --------------------------------------------------------- | ------------- | -------------------------------------------------------- |
| RLS policy gaps, missing indexes, query performance       | `/db-audit`   | "This needs a database security/performance audit."      |
| Bundle size concerns, Core Web Vitals, render performance | `/perf-audit` | "This needs a frontend performance audit."               |
| Specific error with stack trace                           | `/diagnose`   | "This is a concrete error — use `/diagnose`."            |
| Widespread doc drift across core docs                     | `/sync-docs`  | "Multiple docs are out of sync — run `/sync-docs`."      |
| Dead code, stale patterns, accumulated drift              | `/hygiene`    | "This is code-level maintenance — run `/hygiene`."       |
| Production runtime behavior                               | `/prod-audit` | "Need to check production behavior — run `/prod-audit`." |

---

## Principles

1. **Knowledge map first** — Always consult before exploring. Saves 3-5 tool calls per investigation.
2. **Verify, don't trust** — Map entries are hints until confirmed against code. Stale entries mislead.
3. **Tier-appropriate depth** — Don't run 30 tool calls for "where is X?". Don't answer "is X correct?" with a 2-call grep.
4. **Structured output, always** — Raw grep results are noise. Synthesized findings are signal.
5. **Know when to hand off** — An honest "use `/db-audit`" beats a shallow investigation.
6. **Grow the map** — Every investigation is an opportunity to improve future investigations.
7. **File:line references** — Every finding must point to specific code. Vague answers are useless.
8. **Git history is context** — Code says WHAT. Git says WHY. Both matter at Investigate+ tier.
9. **Dual invocation** — Works the same whether user types `/investigate` or Claude follows the protocol silently. Structured output only on explicit invocation.

---

## Anti-Patterns

- Grepping randomly without consulting the knowledge map first
- Dumping raw tool output as the answer (synthesize always)
- Running Audit-tier depth for a Quick question (tier mismatch)
- Updating the knowledge map with behavioral knowledge (that's MEMORY.md)
- Trusting old map entries without verification against actual code
- Investigating database security deeply instead of handing off to `/db-audit`
- Spending 20 tool calls to avoid saying "I need `/perf-audit` for this"
- Skipping the knowledge map update when new structural facts were found
- Investigating without restating the question first (causes drift)

---

## Skill Pipeline

```
/investigate ← standalone (any time, any context)
    │
    ├── feeds into: /plan (understand before planning)
    ├── feeds into: /diagnose (if error found during investigation)
    ├── feeds into: /db-audit, /perf-audit (specialist handoffs)
    │
    └── also: Claude follows this protocol silently during other skills
         (implementation, code-review, qa — whenever understanding is needed)
```

**Also pairs with**: `/session-start` (deep-dive after orientation), `/brainstorm` (fact-finding before ideation), `/code-review` (understanding code before judging it)

---

## Summary + Next Step (CEO Footer)

After presenting findings (any tier), close with a 3-line summary:

```
**Summary**: [1 sentence — what was found, plain language]
**Status**: Healthy / Needs attention / Needs immediate action
**Next step**: [specific skill or action — e.g., "/plan to fix X" or "no action needed"]
```
