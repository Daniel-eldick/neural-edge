# Landmines

Known failure patterns specific to this project. Each entry documents a mistake that has happened (or nearly happened) and the prevention check to avoid it.

Referenced by `/plan` (landmine check section), `/code-review`, and `/qa` during quality gates.

---

## How to Use

- **During `/plan`**: Scan this file. Add relevant prevention checks to the plan's Landmine Check section.
- **During `/code-review`**: Check if any findings match known landmine patterns.
- **During `/qa`**: Verify prevention checks for relevant landmines pass.
- **After incidents**: Add new entries immediately. This file is the institutional memory for "never again."

## Entry Format

```markdown
### #[N]: [Short descriptive title]

**Pattern**: [What goes wrong — the specific mistake]
**Trigger**: [When this typically happens — what action/context leads to it]
**Prevention**: [Specific check to add to plans/reviews]
**Discovered**: [Date] — [Brief story of how it was found]
```

## Entries

_No entries yet. Add your first landmine after your first incident or near-miss._

<!--
Example entry:

### #1: Missing tenant isolation in new queries

**Pattern**: New database query added without tenant_id filter, leaking data across tenants.
**Trigger**: Adding a new query or RPC function to a multi-tenant table.
**Prevention**: Every new query touching a multi-tenant table must include `tenant_id = ?` in WHERE clause. RLS is defense-in-depth, not a replacement.
**Discovered**: 2026-01-15 — Customer saw another tenant's data briefly during a demo.
-->
