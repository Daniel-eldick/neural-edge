---
description: Database safety rules for migrations and RLS policies
globs:
  - 'supabase/migrations/**'
  - 'src/integrations/supabase/**'
---

# Database Safety - CRITICAL

## RLS & Multi-Tenant Isolation

- All tables MUST have `tenant_id` column with FK + RLS policy
- Use `<!-- FILL: your RLS helper function, e.g. is_tenant_staff_secure() -->` in RLS policies — NOT raw subqueries on `<!-- FILL: your role assignments table -->` (causes sequential scan explosion)
- Never add LIMIT to RPC functions (breaks tenant isolation)
- Run `mcp__supabase__get_advisors({ type: "security" })` after any RLS change

## Schema Conventions

- Use `canceled` (single L) to match database enum values — always verify spellings against schema
- Include FK indexes for all foreign keys
- After schema changes: `<!-- FILL: your type generation command -->` to regenerate TypeScript types

## Function EXECUTE Privileges (Deny-All Default)

New security posture: Blanket EXECUTE grants to PUBLIC/anon/authenticated should be revoked. Instead, explicitly grant per-function access based on role needs.

| Role            | Access                                                                 |
| --------------- | ---------------------------------------------------------------------- |
| `anon`          | Only whitelisted functions (guest-facing operations, RLS helpers)      |
| `authenticated` | Whitelisted functions (anon set + auth-only operations)                |
| `service_role`  | All functions (trusted server-side)                                    |
| `PUBLIC`        | Zero                                                                   |

**When creating new functions**: You MUST explicitly GRANT EXECUTE if the function needs to be callable from the client. Default ACLs may auto-grant to some roles but NOT to `anon` for new functions. If a new function needs anon access, add an explicit `GRANT EXECUTE ON FUNCTION ... TO anon;` in the migration.

**Rollback** (emergency): `GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO PUBLIC; GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;`

## Query Safety

- Always `EXPLAIN ANALYZE` new queries before merging
- Watch for N+1 patterns in RPC functions
- Prefer database functions over inline policy subqueries for reuse and performance

## Pre-Migration Backup Checklist

**Before ANY migration or risky database operation:**

1. **Run `<!-- FILL: your backup script path -->`** — creates timestamped schema + data dumps
   - Requires: Docker running + database CLI linked
   - Produces: `<!-- FILL: your backup prefix -->_YYYYMMDD_HHMMSS_schema.sql` + `_data.sql`
2. **Verify backup**: Check script output shows <!-- FILL: your expected table and policy counts -->
3. **Keep backups** until the migration is confirmed successful
4. **Restore procedure**: See [INCIDENT_RESPONSE.md](../../docs/guides/INCIDENT_RESPONSE.md) Option C

**Measured RPO/RTO (March 2026)**: RTO = 2-5 seconds for <!-- FILL: your expected DB size -->. RPO = 0 for planned operations.
