# Project Memory

<!-- This file is auto-loaded into Claude Code's system prompt every session.
     Keep it under 200 lines (lines after 200 are truncated).
     Store detailed notes in topic files and link them here. -->

## Topic Files
- `memory/observations.md` — Active observations notepad (patterns, smells, ideas noticed during work)
- `memory/intuitions.md` — Compressed "When X, Do Y, Because Z" fast-path lessons (the System 1 cache)
- `memory/knowledge-map.md` — Living structural index of the codebase (auto-maintained by `/investigate`)

## Key Learnings

### Repo Structure
<!-- FILL: Document key structural discoveries as you work -->
<!-- Example entries:
- 5 core docs live in `docs/` (not root): INCOMPLETE_FEATURES, PRODUCTION_READINESS_ROADMAP, etc.
- Package name is `your-project` (v1.0.0)
-->

### Testing
<!-- FILL: Document testing patterns and known issues -->
<!-- Example entries:
- Test suite: X files, Y assertions
- `npm run test:all` requires E2E which needs Playwright browsers installed
- **Test Tenant** = your test data identifier, always exclude from production metrics
-->

### Code Patterns
<!-- FILL: Document code patterns that are easy to misidentify -->
<!-- Example entries:
- Console.logs in source are mostly intentional: debug files, auth security
- `.consolidated.ts` hooks ARE the primary implementations (no originals exist)
-->

### Database
<!-- FILL: Document database-specific learnings -->
<!-- Example entries:
- Initplan issues = 0 (all policies use wrapper pattern)
- Duplicate permissive policies: 0
- Connection usage: X/Y (Z%)
-->

### Scaling
<!-- FILL: Document scaling observations and capacity -->
<!-- Example entries:
- Current load: X orders/day, Y active tenants
- Tier capacity: Z connections, estimated ~N tenants
-->

### Performance / Network
<!-- FILL: Document performance baselines and constraints -->
<!-- Example entries:
- Users are on X-Y Mbps connections. Every KB matters.
- Critical path budget: < 300KB gzipped total
- Current baseline: index.js XKB gzip
-->

### Documentation
<!-- FILL: Document documentation conventions -->
<!-- Example entries:
- User values documentation archive — "cheap to store, useful audit trail"
- DDD workflow is non-negotiable: Plan → Document → Approve → Execute → Archive
-->

### Git Hygiene
<!-- FILL: Document gitignore and cleanup patterns -->
<!-- Example entries:
- test-results/, debug-screenshots/ are gitignored
-->
