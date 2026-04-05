---
name: scaling-check
description: >-
  Runs capacity assessment against Supabase metrics and SCALING_GUIDE.md thresholds.
  Reports GREEN/YELLOW/RED status per metric. Use for periodic health checks,
  before onboarding new tenants, or before major deployments.
allowed-tools: Read, Grep, mcp__supabase__execute_sql, mcp__supabase__get_advisors, mcp__supabase__list_tables
---

# Scaling Check Skill

Capacity assessment against live Supabase metrics and documented thresholds.

## When to Use

- `/scaling-check`, "check capacity", "scaling health", "are we ready for more tenants?"
- Before onboarding a new tenant (called automatically by `/onboard` as gate)
- Before major deployments that affect data volume
- Monthly health check alongside `/db-audit`

## When NOT to Use

- Debugging app errors (use `/diagnose`)
- Schema changes (use `/plan` with Full tier)
- Security-only audit (use `/db-audit`)

---

## Step 1: Read Thresholds

Read `docs/guides/SCALING_GUIDE.md`. Find the `<!-- SCALING-CHECK-READS-THIS -->` marker (or the `## 📈 Capacity Planning` heading if marker absent). Extract:

- **Target tenant count** (from "Target Scale" section)
- **Target peak orders/min** (from "Target Scale" section)
- **Max connections** (from connection pool section — currently 60)
- **P0 bottleneck status** (from "Critical Bottlenecks (P0" heading)

These are the reference values. Never hardcode them — always read fresh.

## Step 2: Run 6 Checks

Run all checks via `mcp__supabase__execute_sql` and `mcp__supabase__get_advisors`. Present results as a report card.

### Check 1: Tenant Count

```sql
SELECT count(*) FROM tenants WHERE is_test = false -- FILL: adjust for your test data exclusion;
```

| Status | Condition                        |
| ------ | -------------------------------- |
| GREEN  | < 60% of target tenant count |
| YELLOW | 60-85% of target                 |
| RED    | > 85% of target                  |

### Check 2: Connection Pool

```sql
SELECT count(*) FROM pg_stat_activity WHERE state IS NOT NULL;
```

| Status | Condition                |
| ------ | ------------------------ |
| GREEN  | < 50% of max connections |
| YELLOW | 50-75% of max            |
| RED    | > 75% of max             |

### Check 3: Peak Order Volume

```sql
SELECT max(orders_per_min) FROM (
  SELECT date_trunc('minute', created_at) AS minute, count(*) AS orders_per_min
  FROM orders
  WHERE created_at > now() - interval '7 days'
  GROUP BY minute
) sub;
```

| Status | Condition                       |
| ------ | ------------------------------- |
| GREEN  | < 50% of target peak orders/min |
| YELLOW | 50-80% of target                |
| RED    | > 80% of target                 |

### Check 4: RLS Performance

Use `mcp__supabase__get_advisors` with `type: "performance"`.

Count advisories mentioning "initplan" or suboptimal RLS patterns.

| Status | Condition           |
| ------ | ------------------- |
| GREEN  | 0 initplan issues   |
| YELLOW | 1-5 initplan issues |
| RED    | 6+ initplan issues  |

### Check 5: Security Issues

Use `mcp__supabase__get_advisors` with `type: "security"`.

| Status | Condition               |
| ------ | ----------------------- |
| GREEN  | 0 critical issues       |
| YELLOW | 1-2 non-critical issues |
| RED    | Any critical issue      |

### Check 6: P0 Fix Status

Read `docs/guides/SCALING_GUIDE.md` and grep for the "Critical Bottlenecks (P0" heading. Count items marked FIXED vs open.

| Status | Condition                                 |
| ------ | ----------------------------------------- |
| GREEN  | All P0 items deployed/fixed               |
| YELLOW | Some in progress                          |
| RED    | Any not started AND tenant count > 20 |

## Step 3: Present Report Card

Format output as:

```
┌─────────────────────────────────────────────────┐
│  SCALING CHECK — [date]                         │
├─────────────────────────────────────────────────┤
│  1. Tenant Count    [GREEN/YELLOW/RED]  X/Y │
│  2. Connection Pool     [GREEN/YELLOW/RED]  X/Y │
│  3. Peak Order Volume   [GREEN/YELLOW/RED]  X/Y │
│  4. RLS Performance     [GREEN/YELLOW/RED]  X   │
│  5. Security Issues     [GREEN/YELLOW/RED]  X   │
│  6. P0 Fix Status       [GREEN/YELLOW/RED]  X/Y │
├─────────────────────────────────────────────────┤
│  Overall: [GREEN/YELLOW/RED]                    │
│  [Summary sentence]                             │
└─────────────────────────────────────────────────┘
```

- Overall = worst status among all 6 checks
- For YELLOW/RED checks: include 1-line remediation note
- For RED checks: include specific action to take before proceeding

## Step 4: Gate Logic (When Called by /onboard)

When running as a gate for `/onboard`:

- **All GREEN** → Proceed with onboarding
- **Any YELLOW** → Proceed with WARNING shown to user. Log the warning.
- **Any RED** → **BLOCK** — do not proceed. Show remediation steps. User must fix RED items and re-run `/scaling-check` before onboarding.

## Step 5: Optional — Update Baseline

Ask user if they want to update `docs/guides/SCALING_GUIDE.md` baseline metrics with current values (tenant count, peak volume, date checked). Only update if user confirms.

---

## Summary + Next Step (CEO Footer)

After presenting the report card, close with a 3-line summary:

```
**Summary**: [1 sentence — capacity status in plain language, e.g., "Running at 37% capacity, plenty of room"]
**Status**: All GREEN / X checks YELLOW / Y checks RED
**Next step**: [specific action — e.g., "safe to onboard" or "/plan to address RED items before next tenant"]
```
