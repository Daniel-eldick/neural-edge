---
name: wow-audit
description: Ways of Working auditor with 10 concrete heuristic checks. Use to review and improve processes.
allowed-tools: Read, Glob, Grep, Bash
---

# Ways of Working Audit Skill

Reviews processes and documentation with 10 concrete, automated checks.

## When to Use

- `/wow-audit`, "audit our processes", "check our ways of working"
- End of major feature (suggested check-in)
- Quarterly review

## When NOT to Use

- For document content alignment (use `/sync-docs`)
- For file structure/archival (use `/organize`)
- For code-level cleanup (use `/hygiene`)
- For database health (use `/db-audit`)

**Ownership boundary**: `/wow-audit` owns **process health** (commit patterns, rules freshness, DDD compliance). `/sync-docs` owns content alignment. `/organize` owns file structure. `/hygiene` owns code artifacts.

---

## The 10 Heuristic Checks

### Category 1: Documentation Health (3 checks)

| #   | Check                   | Pass Condition                                          | Auto-Fix?   |
| --- | ----------------------- | ------------------------------------------------------- | ----------- |
| 1   | Active docs health      | No stale (>14 days) or orphaned files in `docs/active/` | Conditional |
| 2   | Completed docs archived | No "✅ COMPLETE" or "100%" files in `docs/active/`      | Yes         |
| 3   | Percentage alignment    | PRODUCTION_READINESS % ± 5% of OFFLINE_SYSTEM %         | No          |

### Category 2: Process Adherence (3 checks)

| #   | Check                | Pass Condition                                    | Auto-Fix? |
| --- | -------------------- | ------------------------------------------------- | --------- |
| 4   | DDD compliance       | ≥7/10 feat/fix commits have matching docs         | No        |
| 5   | Conventional commits | ≥8/10 recent commits match `type(scope): message` | No        |
| 6   | Lint + type-check    | `npm run lint && npm run type-check` passes       | No        |

### Category 3: System Health (4 checks)

| #   | Check            | Pass Condition                                        | Auto-Fix?   |
| --- | ---------------- | ----------------------------------------------------- | ----------- |
| 7   | Rules freshness  | CLAUDE.md modified within 30 days                     | No          |
| 8   | Core docs synced | All 5 core docs have "Last Updated" within 14 days    | Conditional |
| 9   | Skills health    | All skills have valid frontmatter + required sections | Yes         |
| 10  | Git hygiene      | <10 uncommitted files AND 0 stashed changes           | Conditional |

---

## Workflow

### 1. Run All Checks

Execute each check and collect results.

**Check 1-3**: Read docs, compare dates and percentages.

**Check 4**: Get last 10 feat/fix commits, match against docs:

```bash
git log -10 --oneline --grep="^feat\|^fix" --extended-regexp
```

**Check 5**: Validate conventional commit format:

```bash
git log -10 --oneline --format="%s"
# Match: ^(feat|fix|docs|chore|refactor|test|perf)\(.+\): .+
```

**Check 6**: Run lint + type-check (lighter than full `test:all`):

```bash
npm run lint && npm run type-check
```

**Check 7-10**: Read files, check dates, validate structure.

### 2. Calculate Scores

Each check = 1 point. Direct /10 scale.

| Category             | Checks | Points   |
| -------------------- | ------ | -------- |
| Documentation Health | 3      | X/3      |
| Process Adherence    | 3      | X/3      |
| System Health        | 4      | X/4      |
| **Total**            | **10** | **X/10** |

**Grading**: 9-10 = A, 7-8 = B, 5-6 = C, 3-4 = D, 0-2 = F

### 3. Generate Report

```markdown
## Ways of Working Audit Report

**Date**: YYYY-MM-DD
**Score**: X/10 (Grade: [A-F])

### Results

| #   | Check              | Status    | Notes     |
| --- | ------------------ | --------- | --------- |
| 1   | Active docs health | PASS/FAIL | [details] |
| ... | ...                | ...       | ...       |

### Critical Issues (Fix Now)

[Numbered list or "None"]

### Warnings (Fix Soon)

[Numbered list or "None"]

### Passed Checks

[Bulleted ✅ list]

### Recommendations

[Based on findings]
```

### 4. Offer Fixes

For fixable issues, present options:

| Issue                    | Auto?       | Fix                    | Approval     |
| ------------------------ | ----------- | ---------------------- | ------------ |
| Completed doc in active/ | Yes         | `git mv` to completed/ | Yes          |
| Broken skill frontmatter | Yes         | Add YAML header        | Yes          |
| Stale active doc         | Conditional | Archive or update      | User decides |
| DDD violation            | No          | Workflow change        | N/A          |

---

## Principles

1. **Concrete, not subjective** — Every check has a measurable pass condition.
2. **Honest reporting** — Don't soften results. A 4/10 is a 4/10.
3. **Fix what's fixable** — Offer auto-fixes for structural issues. Flag workflow issues as non-automatable.
4. **Own process health** — Don't duplicate `/sync-docs` content checks or `/hygiene` code checks.
5. **Check 6 is lightweight** — Lint + type-check only. Full `test:all` is `/test`'s job.

---

## Anti-Patterns

- Skipping checks or giving passing scores to failed checks
- Modifying files without user approval
- Running `npm run test:all` for Check 6 (too heavy — use lint + type-check)
- Duplicating `/sync-docs` content alignment checks
- Duplicating `/organize` file structure checks
- Duplicating `/hygiene` code artifact checks
- Reporting dishonestly even if results are poor

---

## Skill Pipeline

```
/wow-audit (quarterly) — standalone process review
Related: /sync-docs (content), /organize (structure), /hygiene (code), /db-audit (database)
```
