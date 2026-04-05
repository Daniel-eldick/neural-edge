---
name: diagnose
description: Error analysis and fix suggestions. Use when tests fail, builds break, or runtime errors occur.
allowed-tools: Read, Grep, Glob, Bash, mcp__database__execute_sql
---

# Diagnose Skill

Deep error analysis with root cause identification and fix suggestions.

## When to Use

- `/diagnose`, "help me debug", "what's wrong"
- After test failures (unit or E2E)
- When build breaks
- Runtime errors or stack traces
- Database/RLS errors

## When NOT to Use

- No specific error message (use `/session-start` for "what should I do next?")
- Reviewing code quality (use `/code-review`)
- Running tests (use `/test`)
- General exploration without a concrete error

---

## Project-Specific Knowledge

### Known Pre-Existing Failures (11 total — NOT regressions)

| Test File                 | Count | Root Cause                       |
| ------------------------- | ----- | -------------------------------- |
| `rpc-performance.test.ts` | 6     | RLS auth context missing in test |
| `useTestAuth.test.tsx`    | 2     | Mock setup issues                |
| `OrdersList.test.tsx`     | 3     | Virtualized list testid mismatch |

**If a failure matches one of these**: report it as pre-existing, not a new bug.

### Common Offline-Specific Errors

| Error Pattern                       | Likely Cause                              | Fix Direction                                          |
| ----------------------------------- | ----------------------------------------- | ------------------------------------------------------ |
| `sync_status: undefined`            | Local DB `undefined` != `null`            | Use explicit `'pending'` value (Landmine #2)           |
| Sync hangs after reconnect          | Missing stagger delay                     | Check reconnection delay config in sync manager        |
| Records stuck in local DB           | Sync manager not retrying                 | Check slow-retry phase and batch size config           |
| React Query hang offline            | `onSuccess` refetch while offline         | Wrap refetch in `navigator.onLine` check (Landmine #4) |

### E2E Test Requirements

- Playwright browsers must be installed: `npx playwright install`
- Dev server must be running on `localhost:5173`
- Workers=1 (prevents local database race conditions)

---

## Workflow

### Step 1: Gather Error Information

Accept error from user paste, recent command output, or file reference.

### Step 2: Parse Error Type

| Contains                        | Error Type        |
| ------------------------------- | ----------------- |
| `TS` + number                   | TypeScript error  |
| `eslint`                        | ESLint error      |
| `vite` or `esbuild`             | Build error       |
| `vitest` or `expect`            | Unit test failure |
| `playwright` or `locator`       | E2E test failure  |
| Stack trace with `.ts:`         | Runtime error     |
| `database` or `schema` or `policy` | Database error    |

### Step 2.5: Root Cause First

```
┌─────────────────────────────────────────────────────────┐
│  HARD-GATE: Root Cause Before Fix                       │
│                                                         │
│  BEFORE proposing ANY fix, you MUST:                    │
│  1. State a root cause hypothesis in writing            │
│  2. Cite evidence (error message, stack trace, code)    │
│  3. Explain WHY the error occurs, not just WHAT         │
│                                                         │
│  If you catch yourself thinking "quick fix" — STOP.     │
│  Quick fixes that don't address root cause create       │
│  more bugs than they solve.                             │
└─────────────────────────────────────────────────────────┘
```

**Root cause template** (fill this BEFORE Step 3):

```markdown
### Root Cause Hypothesis

**Error**: [the error message]
**Location**: [file:line]
**Hypothesis**: [WHY this is happening — the mechanism, not the symptom]
**Evidence**: [what supports this hypothesis — code reading, stack trace, MCP query]
**Confidence**: High / Medium / Low
```

If confidence is Low, gather more evidence before proceeding. Read more code. Run MCP queries. Don't guess.

**3-Fix Architectural Gate**: If you have attempted 3+ fixes for the same error and none have worked:

```
┌─────────────────────────────────────────────────────────┐
│  STOP — 3 fixes failed. Question the architecture.      │
│                                                         │
│  You are likely treating symptoms, not the root cause.  │
│  Before attempting fix #4:                              │
│  1. Re-read the original error with fresh eyes          │
│  2. Check: Am I fixing the right thing?                 │
│  3. Check: Is the architecture sound, or is the error   │
│     a symptom of a deeper design problem?               │
│  4. Consider: Escalate to /code-review or ask user      │
└─────────────────────────────────────────────────────────┘
```

### Step 3: Deep Analysis by Type

#### TypeScript Errors

```markdown
### TypeScript Error Analysis

**Error**: TS#### - [description]
**Location**: `src/path/file.tsx:42`
**Root Cause**: [analysis]
**Fix**:
[code snippet]
```

#### Test Failures

**First check**: Is this one of the 11 known pre-existing failures? If yes, report as such.

```markdown
### Test Failure Analysis

**Test**: [test name]
**File**: `src/path/test.ts:156`
**Pre-existing?**: Yes/No
**Root Cause**: [analysis]
**Fix**: [code snippet or "known issue, not a regression"]
```

#### Database Errors

```markdown
### Database Error Analysis

**Error**: [message]
**Root Cause**: [analysis]
**Investigation**:
-- Run via mcp**database**execute_sql
SELECT \* FROM pg_policies WHERE tablename = '[table]';
```

#### Build Errors

| Error                    | Cause               | Fix                                  |
| ------------------------ | ------------------- | ------------------------------------ |
| `VITE_* is not defined`  | Missing env var     | Add to `.env` file                   |
| `Cannot find module 'X'` | Missing dependency  | `npm install X`                      |
| `esbuild: Build failed`  | Import path error   | Check relative paths, use `@/` alias |
| `npm ERR! ERESOLVE`      | Dependency conflict | `npm install --legacy-peer-deps`     |

### Step 4: Resolution Options

**Option 1 — Apply Fix Automatically**: Show code snippet, ask "Apply this fix?"

**Option 2 — Investigation Required**: List manual steps, suggest related skills.

**Option 3 — Escalate**: Database issues → `/db-audit`. Architecture issues → `/code-review`.

### Step 5: After Fix

Always recommend: "Run `/test` to verify the fix."

---

## Principles

1. **Read before diagnosing** — Always read the actual source file at the error location. Never guess.
2. **Check pre-existing first** — Don't waste time debugging known failures.
3. **Root cause, not symptoms** — Trace back to the actual cause, not the surface error.
4. **Cross-reference landmines** — Many errors match patterns in `.claude/landmines.md`.
5. **Check cookbook patterns** — Scan `.claude/references/claude-cookbooks.md` (Quality & Evaluation section) for relevant debugging and eval patterns.
6. **Fix one thing at a time** — Don't bundle fixes. One error, one fix, one test run.

---

## Anti-Patterns

- Guessing root cause without reading source files
- Applying fixes without user approval
- Not checking if the failure is pre-existing (11 known failures)
- Ignoring edge cases in fix suggestions
- Skipping `/test` after applying fix
- Bundling multiple fixes (makes it unclear what fixed what)

---

## Skill Pipeline

```
[Error occurs] → /diagnose → [Apply fix] → /test → [Pass] → commit → push → PR
                                               ↓ [Fail]
                                          /diagnose again
```

---

## Summary + Next Step (CEO Footer)

After presenting the diagnosis, close with a 3-line summary:

```
**Summary**: [1 sentence — root cause in plain language]
**Status**: Fix ready / Needs investigation / Escalate
**Next step**: [specific action — e.g., "apply fix and run /test" or "/code-review for architectural issue"]
```
