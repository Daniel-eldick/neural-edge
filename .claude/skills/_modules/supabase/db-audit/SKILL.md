---
name: db-audit
description: Database security and performance audit using Supabase advisors. Use for periodic DB health checks.
allowed-tools: Read, Edit, mcp__supabase__get_advisors, mcp__supabase__execute_sql, mcp__supabase__list_tables
---

# Database Audit Skill

Database security and performance audit using Supabase MCP tools.

## When to Use

- `/db-audit`, "check database", "audit RLS", "database health"
- After schema changes (migrations, new tables, RLS policies)
- Monthly health check
- When `/session-start` flags CRITICAL security/performance issues

## When NOT to Use

- Debugging application code errors (use `/diagnose`)
- Reviewing code quality (use `/code-review`)
- Planning schema changes (use `/plan` with Full tier)

---

## Project-Specific Knowledge

### Known Issues (update after first audit)

| Issue                               | Count  | Impact                                                               | Reference                                     |
| ----------------------------------- | ------ | -------------------------------------------------------------------- | --------------------------------------------- |
| RLS initplan problems               | <!-- FILL --> | CPU waste per query — `auth.uid()` evaluated per-row instead of once | Use `(select auth.uid())` wrapper             |
| Duplicate permissive policies       | <!-- FILL --> | 2x CPU on affected tables — OR logic means all execute               | Consolidate to single policy per table/action |
| SECURITY DEFINER missing safeguards | <!-- FILL --> | Vulnerable to search path injection                                  | Add `SET search_path TO ''`                   |
| Missing `search_path` on functions  | <!-- FILL --> | Security advisor flags these                                         | Set on all SECURITY DEFINER functions         |

### Key Numbers

- **Max connections**: <!-- FILL: your Supabase plan connection limit -->
- **Batch size**: <!-- FILL: your batch size config --> (sequential sync, 1 connection per device)
- **Sync queue**: <!-- FILL: your max concurrent sync operations -->
- **Production scale**: <!-- FILL: your production scale -->

### RLS Fix Pattern

**Correct** (evaluates once per query):

```sql
WHERE user_id = (select auth.uid())
```

**Incorrect** (evaluates per-row — initplan problem):

```sql
WHERE user_id = auth.uid()
```

**Do NOT use JWT claims** (`current_setting('request.jwt.claims'...)`) — staleness security hole.

### Reference Docs

- [SCALING_GUIDE.md](docs/guides/SCALING_GUIDE.md) — full scaling analysis
- [SCALING_P0_FIXES.md](docs/active/SCALING_P0_FIXES.md) — P0 fix status
- [TECHNICAL_DEBT.md](docs/TECHNICAL_DEBT.md) — tracked DB debt

---

## Workflow

### Step 1: Run Security Advisor

```
mcp__supabase__get_advisors({ type: "security" })
```

Check for: Tables without RLS, overly permissive policies, SECURITY DEFINER risks, exposed sensitive columns, auth configuration issues.

### Step 2: Run Performance Advisor

```
mcp__supabase__get_advisors({ type: "performance" })
```

Check for: Missing indexes on foreign keys, unused indexes (bloat), tables without primary keys, large sequential scans, connection pool issues.

### Step 3: Custom Checks (Project-Specific)

**Initplan check** — Count remaining `auth.uid()` without `(select ...)` wrapper:

```sql
SELECT count(*) FROM pg_policies
WHERE qual::text LIKE '%auth.uid()%'
AND qual::text NOT LIKE '%(select auth.uid())%';
```

**Duplicate policy check** — Find tables with multiple permissive policies for same action:

```sql
SELECT tablename, cmd, count(*)
FROM pg_policies
WHERE permissive = 'PERMISSIVE'
GROUP BY tablename, cmd
HAVING count(*) > 1;
```

**Tenant isolation check** — Verify `tenant_id` appears in key table policies:

```sql
SELECT tablename, policyname, qual
FROM pg_policies
WHERE tablename IN (<!-- FILL: your core tenant-scoped tables, e.g. 'orders', 'items', 'tenants' -->)
ORDER BY tablename;
```

### Step 4: Generate Report

```markdown
## Database Audit Report

**Date**: YYYY-MM-DD
**Project**: Your Project

### Security Findings

| Severity | Issue   | Table/Function | Remediation |
| -------- | ------- | -------------- | ----------- |
| [level]  | [issue] | [location]     | [fix + URL] |

**Security Score**: X/10

### Performance Findings

| Severity | Issue   | Table/Index | Remediation |
| -------- | ------- | ----------- | ----------- |
| [level]  | [issue] | [location]  | [fix]       |

**Performance Score**: X/10

### Project-Specific Checks

| Check                       | Count           | Status   | Trend                  |
| --------------------------- | --------------- | -------- | ---------------------- |
| Initplan issues             | X remaining     | [status] | [improving/same/worse] |
| Duplicate policies          | X remaining     | [status] | [trend]                |
| SECURITY DEFINER safeguards | X missing       | [status] | [trend]                |

### Critical Actions Required

[Numbered list with impact and fix]

### Next Audit

Recommended: [Date — typically 30 days]
```

### Step 5: Flag Critical Issues

If critical issues found, offer to add to TECHNICAL_DEBT.md.

---

## Principles

1. **MCP-verified, not guessed** — Always run the advisors. Don't assume the DB is healthy.
2. **Track trends** — Compare against known issue counts. Are we improving or regressing?
3. **Include remediation URLs** — Supabase advisor provides clickable links. Always include them.
4. **Connect to scaling docs** — Reference SCALING_GUIDE.md and SCALING_P0_FIXES.md for context.
5. **Initplan fix is `(select auth.uid())`** — Not JWT claims (staleness security hole).

---

## Anti-Patterns

- Making schema changes without approval (audit only, report findings)
- Ignoring critical security issues ("we'll fix it later")
- Skipping custom project-specific checks (they catch what advisors miss)
- Using JWT claims for RLS optimization (creates staleness security hole)
- Not including remediation URLs from advisor output

---

## Skill Pipeline

```
/db-audit (monthly) — standalone audit
Also: /plan (Full tier) → /db-audit → /sign-off (for DB-touching plans)
```

---

## Summary + Next Step (CEO Footer)

After presenting the audit report, close with a 3-line summary:

```
**Summary**: [1 sentence — DB health status in plain language]
**Status**: Clean / X issues found (Y critical)
**Next step**: [specific action — e.g., "/plan to fix critical RLS gaps" or "schedule next audit in 30 days"]
```
