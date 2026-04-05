---
name: test
description: Smart test runner with failure analysis. Use when running tests or debugging failures.
allowed-tools: Read, Bash, Glob, Grep
---

# Test Skill

Smart test runner with tiered execution, blast-radius intelligence, and failure analysis.

## When to Use

- `/test`, "run tests", "test this"
- After making code changes
- Before committing (via `/commit` integration)
- When verifying a fix from `/diagnose`

## When NOT to Use

- Deep error analysis needed (use `/diagnose` after test results)
- Code quality review (use `/code-review`)
- Production verification (use Chrome DevTools MCP directly)

---

## Project-Specific Knowledge

### Known Pre-Existing Failures (11 total)

These fail on clean `main` too — they are NOT regressions:

| Test File                 | Count | Root Cause                       |
| ------------------------- | ----- | -------------------------------- |
| `rpc-performance.test.ts` | 6     | RLS auth context missing in test |
| `useTestAuth.test.tsx`    | 2     | Mock setup issues                |
| `OrdersList.test.tsx`     | 3     | Virtualized list testid mismatch |

**When reporting results**: Subtract these from failure count. Only flag NEW failures.

### E2E Requirements

- **Playwright browsers**: Must be installed (`npx playwright install`)
- **Dev server**: Must be running on `localhost:5173` (Playwright auto-starts via `npm run dev`)
- **Workers**: Always 1 (prevents local database race conditions)
- **Test tenant**: Configure your test tenant in the test setup files

### Available Commands

| Command               | Purpose                        | When to Use        |
| --------------------- | ------------------------------ | ------------------ |
| `npm test`            | Unit tests (watch mode)        | During development |
| `npm run test:run`    | Unit tests (single run)        | Quick verification |
| `npm run test:e2e`    | E2E tests (headless)           | Full flow testing  |
| `npm run test:e2e:ui` | E2E tests (Playwright UI)      | Debugging E2E      |
| `npm run test:all`    | Full suite (lint + unit + E2E) | Before commits     |

---

## Test Tiers

Infer from context or user input. Don't ask unless unclear:

| Tier             | Shorthand                   | What Runs                                           | When to Use                       |
| ---------------- | --------------------------- | --------------------------------------------------- | --------------------------------- |
| **Quick**        | `/test` or `/test unit`     | `npm run test:run`                                  | Unit tests only, fast feedback    |
| **Lint+Types**   | `/test lint`                | `npm run lint && npm run type-check`                | UI/styling changes                |
| **Blast Radius** | `/test blast`               | Targeted E2E (Chromium-only) based on changed files | After feature work, before commit |
| **E2E Full**     | `/test e2e`                 | All E2E specs, all browsers                         | Periodic full regression          |
| **E2E UI**       | `/test e2e:ui`              | Launch Playwright UI mode                           | Interactive debugging             |
| **Full**         | `/test all` or `/test full` | `npm run test:all` (lint + unit + all E2E)          | Pre-release, major changes        |
| **Specific**     | `/test src/path/file.ts`    | Single file/pattern                                 | Targeted debugging                |
| **Auto**         | `/test auto`                | Unit for changed files + blast radius E2E           | Smart default for feature work    |

**Default behavior**: `/test` with no args → **Quick** (fast feedback). `/test auto` is the smart tier. This preserves backwards compatibility.

---

## Blast Radius Workflow

The blast-radius system maps changed source files to relevant E2E specs. Used by `/test blast` and `/test auto`.

### Algorithm (6 Steps)

```
/test blast (or /test auto)
    │
    ├── Step 1: Read .test-last-run marker (commit SHA + timestamp)
    │           If missing → fall back to "last 5 commits"
    │
    ├── Step 2: git diff <last-sha>..HEAD --name-only
    │           Filter to src/ files only (ignore docs, config, skills)
    │
    ├── Step 3: Route changed files through blast-radius-map.json
    │           Convention-based: src/path/ → e2e/dir/
    │           Returns list of E2E spec files/directories
    │
    ├── Step 3.5: Validate coverage (staleness detection)
    │             For each changed file with NO route match in
    │             blast-radius-map.json, check cross-cutting-overrides.json.
    │             If STILL no match → warn: "Unmapped file: <path> — falling
    │             back to e2e/01-smoke/". Add e2e/01-smoke/ to the spec list.
    │             This enforces Rule 3 with an explicit warning so drift
    │             is visible, not silent.
    │
    ├── Step 4: Check cross-cutting-overrides.json
    │           If any changed file matches an override pattern,
    │           add the override's additional specs
    │
    ├── Step 5: Deduplicate + run
    │           npx playwright test --project=chromium [spec-list]
    │
    └── Step 6: Update .test-last-run with current HEAD SHA + timestamp
```

### Routing Rules

1. **Longest prefix wins**: `src/hooks/useData.ts` matches `src/hooks/useData` (specific) over `src/hooks/` (generic)
2. **Empty array = no E2E needed**: Areas like `src/utils/`, `src/data/`, `src/components/ui/` need only unit tests
3. **No match = fallback to smoke**: If a file matches no route, default to `e2e/01-smoke/` (conservative)
4. **Performance specs excluded**: `e2e/09-performance/` is never auto-routed — only via `/test e2e` or `/test full`

### Failure Mode

If `blast-radius-map.json` is missing or malformed, log a warning and fall back to running `e2e/01-smoke/` (safe default). Never crash or run nothing.

### Configuration Files

- **Routing table**: `.claude/skills/test/blast-radius-map.json` — maps `src/` prefixes to E2E directories
- **Override rules**: `.claude/skills/test/cross-cutting-overrides.json` — cross-cutting concern patterns
- **Marker file**: `.test-last-run` (gitignored) — tracks last E2E run SHA

### Marker File Format

```json
{
  "sha": "abc123def",
  "timestamp": "2026-04-04T14:30:00Z",
  "tier": "blast",
  "specs_run": ["e2e/03-orders/", "e2e/06-offline/"],
  "result": "pass"
}
```

If missing (first run, or deleted): fall back to `git log --oneline -5` to check last 5 commits. Self-healing — deleting the marker just means a wider blast radius next run.

### Playwright UI Mode

`/test e2e:ui` launches Playwright's built-in interactive debugger:

```bash
npx playwright test --ui
```

Opens a browser window with test file tree, step-by-step timeline, DOM snapshots, and network/console panels. Simply launch it and let the developer explore — no automated analysis needed.

---

## Coverage Tax

**Principle**: When you touch a source file with < 60% coverage AND the change is logic (not CSS/copy/config), add at least one test for the code you touched. Coverage grows organically with every PR — like cleaning your station as you cook.

### How to Check Coverage

```bash
npm run test:coverage
# Look for file-level coverage in the output
```

### Exemptions (no tax required)

- **CSS/styling-only changes** — no logic to test
- **Copy/text changes** — no behavior change
- **Config/docs/skills** — not production code
- **Files already at >= 60% coverage** — above the threshold

### Enforcement

The coverage tax is a principle, not an automated gate. It's enforced via:

- `/plan` templates requiring Test Plan sections with E2E spec references
- `/sign-off` dimension 6 (Test Quality) checking for adequate test coverage
- Code review culture — reviewers check for untested logic changes

---

## Workflow

### Step 0: Pre-Flight Checks

Before running E2E, Blast Radius, or Full tier, verify the environment:

```bash
# Dev server running?
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173
# PASS: 200. FAIL: connection refused → run `npm run dev` first

# Playwright browsers installed?
npx playwright --version 2>/dev/null && echo "OK" || echo "MISSING: run 'npx playwright install'"
```

| Check                 | Required for     | If missing                           |
| --------------------- | ---------------- | ------------------------------------ |
| Dev server on `:5173` | E2E, Blast, Full | `npm run dev` in a separate terminal |
| Playwright browsers   | E2E, Blast, Full | `npx playwright install` (one-time)  |
| `node_modules/`       | All              | `npm install`                        |

Skip pre-flight for Quick/Lint+Types/Specific tiers (unit tests don't need these).

### Step 1: Determine Tier

Infer from context:

- User said `/test` with no args → default to **Quick** (fast feedback)
- User said `/test blast` → **Blast Radius** (targeted E2E from changed files)
- User said `/test auto` → **Auto** (unit + blast radius E2E)
- User said `/test all` or "before commit" → **Full**
- User said `/test e2e` → **E2E Full**
- User said `/test e2e:ui` → **E2E UI** (interactive Playwright debugger)
- User said `/test lint` → **Lint+Types**
- User provided a file path → **Specific**

### Step 2: Run Tests

Execute the appropriate command. Use 600s timeout for Full/E2E/Blast tiers.

For **Blast Radius** and **Auto** tiers, follow the 6-step algorithm above to determine which specs to run, then execute:

```bash
npx playwright test --project=chromium [spec-list]
```

For **Auto** tier, also run unit tests for changed files first:

```bash
# Find changed test files
git diff <last-sha>..HEAD --name-only | grep '\.test\.\(ts\|tsx\)$'
# Run them
npm test -- [changed-test-files]
```

### Step 3: Analyze Results

#### All Pass

```markdown
## Test Results: All Passed

- **Tier**: [which tier ran]
- **Unit Tests**: X passed
- **E2E Tests**: X passed (if applicable)
- **Known failures**: 11 pre-existing (not counted)

Ready to proceed.
```

**Failure Analysis Decision Tree** (for each new failure):

```
Failure → Is it one of the 11 pre-existing? → Yes → Report as "known, not regression"
                                              → No ↓
          Error in test file or source? → Test file → Check: wrong selector? Stale mock? Race condition?
                                        → Source ↓
          Recent git change to that file? → `git log --oneline -5 -- src/path/file.ts`
                                           → Yes → Likely regression from that commit
                                           → No → Deeper issue → `/diagnose`
```

#### New Failures Found

```markdown
## Test Results: X New Failures

### Summary

- **Total**: X tests
- **Passed**: Y
- **New failures**: Z (excluding 11 pre-existing)
- **Pre-existing**: 11 (rpc-performance 6, useTestAuth 2, OrdersList 3)

### New Failures

#### 1. [Test Name]

**File**: `src/path/to/test.ts:42`
**Error**: [error message]
**Likely Cause**: [analysis]
**Suggested Fix**: [specific suggestion]

---

### Next Steps

1. Run `/diagnose` for detailed error analysis (Recommended)
2. Fix and re-run: `npm test -- src/path/to/test.ts`
```

---

## Single File Testing

```bash
# Unit test - specific file
npm test -- src/path/to/test.ts

# Unit test - pattern match
npm test -- -t "should handle the operation"

# E2E test - specific file
npm run test:e2e -- e2e/some-flow.spec.ts

# E2E test - grep pattern
npm run test:e2e -- --grep "triggers after input"
```

---

## Principles

1. **Fast feedback first** — Default to Quick tier. Don't run Full unless needed.
2. **Know the 11** — Pre-existing failures are not regressions. Don't waste time on them.
3. **New failures only** — Report and count only NEW failures beyond the known 11.
4. **Blast radius over full suite** — Use `/test blast` for targeted E2E. Full suite is for periodic regression.
5. **Coverage tax** — Touch logic below 60% coverage? Add a test for what you touched.
6. **Escalate to /diagnose** — If failures are complex, hand off to `/diagnose` for root cause analysis.
7. **E2E needs setup** — Playwright browsers + dev server. Check before running.

---

## Anti-Patterns

- Running Full suite for a docs-only change (waste of time)
- Reporting pre-existing failures as new regressions
- Not checking if Playwright browsers are installed before E2E
- Skipping tests and hoping for the best
- Ignoring failures ("it's probably flaky")
- Running `test:all` when `test:run` would suffice
- Running zero E2E when source code changed (use `/test blast` instead)

---

## Skill Pipeline

```
implement → /test → [pass] → /code-review → /qa → commit → push → PR
                      ↓ [fail]
                 /diagnose → fix → /test again
```
