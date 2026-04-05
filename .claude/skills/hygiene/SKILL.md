---
name: hygiene
description: Monthly code-level maintenance check. Catches drift before it accumulates. Use monthly or after major feature work.
allowed-tools: Read, Glob, Grep, Bash
---

# Hygiene Skill

Monthly code-level maintenance check. Catches drift before it accumulates.

**Frequency**: Monthly, or after major feature work.
**Duration**: 5-10 minutes (after first pass).

## When to Use

- `/hygiene` or "run hygiene check"
- Monthly maintenance cycle
- Before a major release
- After a sprint with lots of new files

## When NOT to Use

- For docs/skills organization (use `/organize`)
- For deep code review (use `/code-review`)
- For test failures (use `/diagnose`)
- For document sync issues (use `/sync-docs`)

---

## The Checklist

Run each check. Report findings as a table. Fix only with user approval.

### Check 1: Git Artifact Drift

**Goal**: Nothing that should be gitignored is being tracked.

```
Bash: git ls-files | grep -E '\.(zip|png|webm|trace|json)$' | grep -v -E '(package|tsconfig|components|vercel|eslint|\.audit)' | head -20
```

- [ ] No test artifacts (traces, screenshots, videos) tracked
- [ ] No report files (lighthouse, playwright) tracked
- [ ] No binary blobs tracked

**If found**: Add to `.gitignore`, run `git rm --cached` (NOT `git rm` — Landmine #10).

### Check 2: Console.log Creep

**Goal**: No new unintentional console.log in production source.

```
Grep: console\.log in src/**/*.{ts,tsx} excluding __tests__, .test., .spec., e2e/
```

**Allowed** (intentional, don't flag):

<!-- FILL: List your project's intentional console.log locations here. Common examples:
- Debug utilities gated behind feature flags or dev-only checks
- Logger implementations (the logger itself)
- Security audit trail logging
- Sync/offline debug logging (critical for debugging connectivity issues)
- Comments/docstrings (not runtime code)
-->

**If new ones found**: Replace with `debug.log()` from `src/lib/debug.ts` or remove.

### Check 3: Dead Code Detection

**Goal**: No component/hook files with zero imports.

**Automated scan script** (copy-paste ready):

```bash
# Find exported components/hooks with zero imports elsewhere
for f in $(find src/components src/hooks -name '*.ts' -o -name '*.tsx' | grep -v __tests__ | grep -v '.test.' | grep -v '.spec.'); do
  name=$(basename "$f" | sed 's/\.\(ts\|tsx\)$//')
  count=$(grep -rl "$name" src/ --include='*.ts' --include='*.tsx' | grep -v "$f" | grep -v __tests__ | grep -v '.test.' | wc -l | tr -d ' ')
  if [ "$count" = "0" ]; then
    echo "ZERO IMPORTS: $f"
  fi
done
```

**Known false-positive whitelist** (do NOT flag these):

<!-- FILL: List your project's known false positives for dead code detection. Common examples:
- Feature-flagged component variants (all active, routing determines which loads)
- Consolidated/refactored hooks that ARE the primary implementations
- Health check endpoints (uptime monitoring)
- Index/barrel files (re-export files have no direct importers by name)
-->

| File/Pattern                    | Why it's not dead                                |
| ------------------------------- | ------------------------------------------------ |
| Index/barrel files (`index.ts`) | Re-export files have no direct importers by name |

Focus on files with `Enhanced`, `V2`, `Simple`, `Old`, `Legacy`, `Deprecated` in the name — these are most likely to be migration residue.

**If found**: Verify with user before deleting.

### Check 4: Package Identity

**Goal**: `package.json` has correct project name and version.

- [ ] Name matches your project (not placeholder)
- [ ] Version reflects actual state

### Check 5: Root Cleanliness

**Goal**: Project root has only essential files.

**Expected at root**: `README.md`, `CLAUDE.md`, `package.json`, `package-lock.json`, config files (vite, ts, eslint, tailwind, playwright, postcss, vercel), `index.html`, and directories (`src/`, `docs/`, `e2e/`, `public/`, `scripts/`, `node_modules/`, `dist/`).

### Check 6: .gitignore Completeness

**Goal**: `.gitignore` covers all generated/artifact paths.

Verify present: `playwright-report/`, `test-results/`, `.lighthouseci/`, `debug-screenshots/`, `bun.lockb`, `metrics/`, `monitoring/`, `coverage/`, `dist/`, `.env` and variants.

### Check 7: Critical Gitignored Files Exist

**Goal**: Files that should be gitignored but must exist locally are present.

```
Bash: ls -la .mcp.json .claude/settings.local.json .env 2>&1
```

**Required files**:

- `.mcp.json` — MCP server configuration (configured MCP servers)
- `.claude/settings.local.json` — Local Claude settings
- `.env` — Environment variables (`your API URL and key env vars`)

**If .mcp.json is missing**: Restore from git history: `git show b5e2500:.mcp.json > .mcp.json`

**Why this matters**: Landmine #10 — `git rm` (without `--cached`) accidentally deleted `.mcp.json` in Feb 2026.

### Check 8: Core Doc Weight

**Goal**: Core docs stay slim (<200 lines each). Drift = resolved items accumulating instead of being archived.

```
Bash: wc -l docs/TECHNICAL_DEBT.md docs/INCOMPLETE_FEATURES.md docs/PRODUCTION_READINESS_ROADMAP.md docs/OFFLINE_SYSTEM_STATUS.md docs/BACKLOG.md
```

- [ ] Each doc under 200 lines (BACKLOG exempt — mostly active content)
- [ ] Total of first 4 docs under 600 lines

**If over threshold**: Completed/resolved entries have crept back in. Archive current version to `docs/archive/[DOC_NAME]_[DATE].md`, then slim back to active-only content. See [docs/active/CORE_DOCS_CLEANUP.md](../../docs/active/CORE_DOCS_CLEANUP.md) for the cleanup rules.

### Check 9: Blast Radius Map Staleness

If `.claude/skills/test/blast-radius-map.json` exists, verify it's not stale:

**Sub-check A: Orphaned E2E specs**

```bash
# Find E2E spec directories referenced in the map
jq -r '.routes | to_entries[] | .value[]' .claude/skills/test/blast-radius-map.json | sort -u > /tmp/mapped-specs
# Find actual E2E directories
ls -d e2e/*/ 2>/dev/null | sort > /tmp/actual-specs
# Orphaned = in map but not on disk
comm -23 /tmp/mapped-specs /tmp/actual-specs
```

WARN if any orphaned specs found (map references directories that don't exist).

**Sub-check B: Unmapped source directories**

```bash
# Find src/ directories that have .ts/.tsx files
find src -name '*.ts' -o -name '*.tsx' | sed 's|/[^/]*$||' | sort -u > /tmp/source-dirs
# Find src/ prefixes in the map
jq -r '.routes | keys[]' .claude/skills/test/blast-radius-map.json | sort > /tmp/mapped-dirs
# Unmapped = on disk but not in map
comm -23 /tmp/source-dirs /tmp/mapped-dirs
```

INFO (not WARN) for unmapped source directories — many intentionally map to empty (unit-test only). Flag only if > 30% of src/ directories are unmapped.

---

## Output Format

```markdown
## Hygiene Check - [Date]

| #   | Check                     | Status    | Findings  |
| --- | ------------------------- | --------- | --------- |
| 1   | Git artifact drift        | PASS/FAIL | [details] |
| 2   | Console.log creep         | PASS/FAIL | [details] |
| 3   | Dead code detection       | PASS/FAIL | [details] |
| 4   | Package identity          | PASS/FAIL | [details] |
| 5   | Root cleanliness          | PASS/FAIL | [details] |
| 6   | .gitignore completeness   | PASS/FAIL | [details] |
| 7   | Critical gitignored files | PASS/FAIL | [details] |
| 8   | Core doc weight           | PASS/FAIL | [details] |
| 9   | Blast radius map staleness| PASS/FAIL | [details] |

**Overall**: X/9 checks passed.
[If any FAIL: list specific fixes with user approval]
```

---

## After Fixes

If any fixes were applied:

1. Run `npm run lint && npm run type-check` to verify nothing broke
2. Commit with: `chore(hygiene): monthly cleanup - [brief summary]`

---

## Principles

1. **Structural, not logical** — This is a surface-level hygiene pass, not a code review.
2. **Know the false positives** — Review the whitelist above. Files flagged as false positives are NOT dead code.
3. **`--cached` not bare** — When untracking gitignored files, ALWAYS use `git rm --cached` (Landmine #10).
4. **Don't expand scope** — If issues are complex, create a `/plan` instead of fixing inline.
5. **15 minutes max** — This is a quick sweep, not a deep dive.

---

## Anti-Patterns

- Deleting files without verifying zero imports first
- Removing console.logs from debug utilities (they're intentional)
- Expanding scope into code review territory
- Spending more than 15 minutes
- Using `git rm` instead of `git rm --cached` for gitignored files

---

## Relationship to Other Skills

| Skill          | Scope                  | Boundary                                |
| -------------- | ---------------------- | --------------------------------------- |
| `/organize`    | Docs structure, skills | /hygiene is code-level only             |
| `/code-review` | Code quality, logic    | /hygiene is lighter, structural only    |
| `/sync-docs`   | Doc content alignment  | /hygiene doesn't read doc content       |
| `/wow-audit`   | Process health         | /hygiene is code artifacts, not process |

---

## Skill Pipeline

```
/hygiene (monthly) — standalone maintenance, not part of feature pipeline
Also useful: before /review-pr (quick sanity check)
```
