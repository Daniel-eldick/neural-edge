---
description: Global error recovery patterns for tool/MCP failures during skill execution
alwaysApply: true
---

# Error Recovery — Global Rule

Standard error recovery patterns for when tools or MCPs fail during skill execution. This is Layer 1 (infrastructure). Per-skill overrides (Layer 2) take precedence when they exist.

## Relationship to autonomous-guardrails.md

These two global rules have **distinct scopes**:

- **error-recovery.md** (this file): Handles **tool/MCP failures** — retries, fallbacks, escalation when external tools break
- **autonomous-guardrails.md**: Handles **quality gate self-correction** — anti-gaming, scoring integrity, scope reduction prevention

They don't conflict. If a tool fails during a quality gate, this rule governs the retry/fallback. If the quality gate's scoring or scope is in question, autonomous-guardrails governs.

## Retry Pattern

When a tool call fails (timeout, connection error, unexpected response):

```
Attempt 1: Retry immediately (transient failures resolve fast)
Attempt 2: Wait 3 seconds, retry
Attempt 3: Check known fallback table below
```

**Do NOT retry**: Permission denied, invalid arguments, resource not found. These are logic errors, not transient failures.

## Known Fallback Table

| Primary Tool                 | Fallback                               | When to Switch                                   |
| ---------------------------- | -------------------------------------- | ------------------------------------------------ |
| Chrome DevTools MCP          | Playwright CLI (`npx playwright test`) | DevTools MCP unresponsive after 2 retries        |
| Database MCP (query)         | Direct SQL connection if available     | MCP returns connection errors                    |
| Database MCP (advisors)      | Skip advisory check, note in output    | Advisory service unavailable                     |
| WebSearch                    | WebFetch with known URLs               | Search API unavailable                           |
| Task agent spawn             | Inline execution (same context)        | Agent spawn fails or times out                   |
| Fresh-eyes agent             | Inline re-score with anti-bias prompt  | Agent spawn fails (per autonomous-guardrails.md) |

## Escalation Tiers

```
Tier 1: AUTO-RETRY (2 attempts + fallback)
  → Silent. No CEO notification.
  → Log what failed and what fallback was used.

Tier 2: CEO NOTIFICATION (fallback also failed OR no fallback exists)
  → Tell the CEO: "[Tool] failed. Tried [fallback]. Skipping [check/step]."
  → Continue with remaining work if possible.
  → Mark the skipped step clearly in output.

Tier 3: FULL STOP (failure affects data integrity or correctness)
  → Tell the CEO: "[Tool] failed. Cannot continue safely."
  → Stop execution. Do not proceed with partial results.
  → Examples: DB migration tool fails mid-migration, sync tool fails during data operation.
```

## Per-Skill Overrides (Layer 2)

These skills already have bespoke error handling. Their patterns take precedence over this global rule:

| Skill       | Override                                             | Location                    |
| ----------- | ---------------------------------------------------- | --------------------------- |
| `/qa`       | G8 circuit breaker for Check 10 manual verification  | SKILL.md line ~159          |
| `/deploy`   | Edge case table for branch/push failures             | SKILL.md Edge Cases section |
| `/diagnose` | 3-fix architectural gate — stop after 3 failed fixes | SKILL.md Step 2.5           |

**Rule**: If a skill defines its own retry count, fallback, or escalation for a specific failure mode, follow the skill's pattern. This global rule only covers gaps.

## What This Rule Does NOT Cover

- Quality gate scoring integrity → `autonomous-guardrails.md`
- Production deployment safety → `production-safety.md`
- Database operation safety → see database module rule (if activated)
- When to stop self-correcting → `autonomous-guardrails.md` Rule 4
