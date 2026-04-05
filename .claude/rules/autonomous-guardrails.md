---
description: Anti-gaming guardrails for autonomous quality gate loops
alwaysApply: true
---

# Autonomous Quality Gate Guardrails

These rules govern self-correction loops in `/sign-off`, `/code-review`, and `/qa`. They prevent the agent from gaming its own evaluation — the #1 alignment risk in autonomous development.

## Rule 1: Immutable Scoring Rubric

During quality gate execution, the skill's scoring dimensions, thresholds, and verdict criteria are **READ-ONLY**. The self-correction loop modifies the WORK (plan, code), never the GRADING.

- Do not adjust dimension weights, threshold values, or verdict criteria mid-execution
- Do not reinterpret what a dimension measures to make scoring easier
- Do not skip or merge dimensions to avoid low scores
- The evaluator is infrastructure — like autoresearch's immutable `prepare.py`

## Rule 2: Anti-Scope-Reduction

Before entering a self-correction loop, **snapshot scope metrics**:

- `/sign-off`: task count + file count from the plan
- `/code-review`: finding counts by severity (CRITICAL, HIGH, MEDIUM, LOW)
- `/qa`: check count + which checks apply

After each iteration, compare against the snapshot. **Flag and escalate if**:

- Task count decreased without documented reason
- File count decreased without documented reason
- Findings disappeared without evidence of fix (diff showing the fix)
- Checks that previously applied were reclassified as SKIP

Scope can GROW during self-correction (discovering new requirements). It must never shrink to pass.

## Rule 3: Suspicion Escalation

If any quality gate score improves by **> 2 points in a single iteration** without substantial changes, flag for CEO review.

What counts as "substantial":

- `/sign-off`: Plan sections rewritten or expanded (not just rephrased)
- `/code-review`: Code changes with corresponding test updates
- `/qa`: Failing checks fixed with verifiable command output

Large score jumps on cosmetic changes = likely inflation. The CEO decides if the improvement is genuine.

## Rule 4: Circuit Breaker

When a tool or MCP fails during a quality gate:

```
Tool fails → Known fallback exists?
                ├── Yes → Try fallback → Fallback works? → Continue
                │                          └── No → STOP + notify CEO
                └── No → STOP + notify CEO
```

Known fallbacks:
| Primary Tool | Fallback | Context |
|-------------|----------|---------|
| Chrome DevTools MCP | Playwright CLI | QA manual verification |
| Database MCP | Direct SQL connection | DB verification |
| Fresh-eyes agent spawn | Inline re-score with anti-bias prompt | Sign-off/code-review re-scoring |

**Non-negotiable**:

- Never silently skip a quality gate step
- Never invent creative workarounds to bypass a broken tool
- Never continue with partial verification as if it were complete
- Always notify the CEO when the chain of trust is broken
