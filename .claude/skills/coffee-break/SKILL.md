# Coffee Break Skill

Observations review session. Claude initiates discussion about patterns, smells, and ideas collected in `memory/observations.md` during recent work.

## When to Use

- `/coffee-break`, "let's do a coffee break", "any observations?"
- Proactively suggest after 3+ observations accumulate
- During natural pauses between tasks

## When NOT to Use

- No observations collected yet (nothing to discuss)
- In the middle of active implementation (focus first, reflect later)

---

## Workflow

### Step 1: Read Observations

Read `memory/observations.md`. If empty or no active observations, say so and skip.

### Step 1.5: Validate Observations

Before prioritizing, run each observation through 3 validation questions:

| Question                                                                     | If NO                              |
| ---------------------------------------------------------------------------- | ---------------------------------- |
| **Concrete?** — Does it reference specific files, functions, or data?        | Rewrite with evidence or dismiss   |
| **Specific?** — Could someone act on this without asking "what do you mean?" | Sharpen the wording                |
| **Evidence-based?** — Was this observed during actual work, not theorized?   | Mark as hypothesis, don't graduate |

Observations that fail all 3 should be dismissed. Observations that fail 1-2 should be rewritten before prioritizing.

### Step 2: Prioritize

Group observations by impact:

| Priority      | Criteria                                       |
| ------------- | ---------------------------------------------- |
| **Act now**   | Could cause production issues or data problems |
| **Plan soon** | Worth a `/plan` or BACKLOG entry               |
| **FYI**       | Interesting but no action needed yet           |

### Step 3: Present

```markdown
## Coffee Break — [Date]

### Observations ([N] collected)

| #   | Observation | Priority                  | Suggested Action     |
| --- | ----------- | ------------------------- | -------------------- |
| 1   | [summary]   | Act now / Plan soon / FYI | [specific next step] |

### Discussion

[For each "Act now" or "Plan soon" item, explain why it matters and what you'd recommend.]
```

### Step 4: Decide Together — Graduation Routing

For each observation, CEO decides its destination:

| Decision                      | Destination               | What happens                                                |
| ----------------------------- | ------------------------- | ----------------------------------------------------------- |
| **Graduate to Intuition**     | `memory/intuitions.md`    | Compress into When/Do/Why format. Remove from observations. |
| **Graduate to Memory**        | `memory/MEMORY.md`        | Add as a Key Learning. Remove from observations.            |
| **Graduate to Knowledge Map** | `memory/knowledge-map.md` | Add structural finding. Remove from observations.           |
| **Act now**                   | Create task or `/plan`    | Keep in observations until resolved.                        |
| **Backlog**                   | `docs/BACKLOG.md`         | Add entry. Remove from observations.                        |
| **Dismiss**                   | Delete                    | Remove from observations.                                   |

### Step 4.5: Compress for Graduation

For intuition graduations, compress the observation into the standard format before writing:

```markdown
### [Short Title]

**When**: [situation — the trigger]
**Do**: [compressed action — the fast path]
**Why**: [one-line lesson + reference]
```

**Compression example** (before/after):

**Before** (raw observation): "I noticed that when I was working on the admin orders page, the useAdminOrders hook's activeTab parameter always overrides the statusFilter. I had to read the code three times to understand why my filter wasn't working. The mapping is at line 42-43."

**After** (compressed intuition):

```
### useAdminOrders activeTab Override
**When**: Debugging why statusFilter isn't working in admin orders
**Do**: Check activeTab first — it overrides statusFilter at line 42-43
**Why**: activeTab maps directly to status return value, ignoring statusFilter entirely
```

Place under the appropriate domain heading in `memory/intuitions.md`. If no matching domain exists, create one.

### Step 5: Clean Up

Process each routed observation:

- **Graduated** (intuition / memory / knowledge map): Remove from `memory/observations.md`
- **Backlogged**: Remove from observations after adding to BACKLOG.md
- **Act now**: Keep in observations with a note that action is planned
- **Dismissed**: Remove from observations

Keep only unresolved "Act now" items in observations.

**Health signal**: If `memory/observations.md` has > 10 unreviewed entries, something is wrong — observations are being collected without processing. Recommend a `/coffee-break` before continuing other work.

---

## Principles

1. **Concrete, not casual** — Every observation has evidence from actual work
2. **Short** — 10 minutes max. Prioritize ruthlessly.
3. **Actionable** — Each item ends with a clear next step recommendation
4. **Earn the interruption** — Only suggest coffee break when observations are worth discussing
