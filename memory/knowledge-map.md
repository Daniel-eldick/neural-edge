# Knowledge Map

> Living structural index of the codebase. Auto-maintained by `/investigate`.
> Entries are verified against actual code on consultation — stale entries get corrected.
> **Staleness rule**: Entries >90 days without verification are hints, not facts.

**Last full seed**: <!-- FILL: date of first `/investigate` audit -->

<!-- This map grows organically as you use `/investigate`.
     After each investigation, new structural facts get added here.
     See the `/investigate` skill for what goes IN the map vs elsewhere. -->

---

## Provider / Component Hierarchy

<!-- FILL: Document your app's outermost wrapping and provider order -->
<!-- Example:
```
QueryClientProvider
  └─ AuthProvider
     └─ ThemeProvider
        └─ Router
           ├─ PublicRoutes
           └─ ProtectedRoutes
              └─ TenantProvider
                 └─ AppShell
```
-->

- **Entry point**: <!-- FILL: e.g., src/App.tsx -->
- **Last verified**: <!-- FILL: date -->

---

## Route Structure

<!-- FILL: Document your route tree -->
<!-- Example:
| Route | Component | Loading |
|-------|-----------|---------|
| `/` | HomePage | Direct |
| `/admin/*` | AdminLayout | Lazy |
-->

---

## Domain Systems

<!-- FILL: Add sections for each major system in your codebase -->
<!-- Example sections:
## Authentication System
## Data Sync / Offline System
## Payment System
## Notification System
-->

<!-- For each system, document:
- Where it lives (directories, key files, entry points)
- How it connects to other systems (data flows, events)
- What consumes it (callers, dependencies)
- Quick lookups (common questions → direct file:line answers)
-->

---

## Hook Organization

<!-- FILL: Document your hooks directory structure -->
<!-- Example:
| Domain | Examples |
|--------|----------|
| `auth/` | Authentication, session management |
| `data/` | Data fetching, caching |
| `ui/` | UI utilities, media queries |
-->

---

## Key Integrations

<!-- FILL: Document external service integrations -->
<!-- Example:
| Service | Integration Point | Key Files |
|---------|-------------------|-----------|
| Supabase | Database + Auth | src/integrations/supabase/ |
| Stripe | Payments | src/lib/stripe.ts |
-->
