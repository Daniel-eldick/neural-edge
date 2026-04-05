# Changelog

All notable changes to the simplrr-framework will be documented in this file.

## [1.1.0] — 2026-04-04

### Framework Sync Extraction + Reconciliation

**Manifest schema**: Bumped to `0.2.0`. Added `framework-repo` and `last-sync-commit` fields for bidirectional sync anchoring.

**New skill: `/framework-sync`** — Extracted from `/simplrr-framework` Mode 3 (Sync) into a dedicated maintenance skill. Two modes:
- `push` — Project improvements → framework repo (with contamination defense)
- `pull` — Framework updates → project (with smart merge for adapter files)

**`/simplrr-framework`** reduced to 2 modes (init, integrate). Sync mode deprecated with redirect to `/framework-sync`.

**Blast-radius intelligence** ported to `/test` skill:
- 4 new test tiers: Blast Radius, Auto, E2E UI, Lint+Types
- Blast-radius routing algorithm (6 steps) with `blast-radius-map.json` and `cross-cutting-overrides.json` config files
- Staleness detection for unmapped source files
- Coverage Tax principle (touch logic < 60% coverage → add a test)

**Other skill updates**:
- `/hygiene`: Added Check 9 (Blast Radius Map Staleness)
- `/plan`: Added E2E specs field to Standard and Full test plan templates
- `/sign-off`: Added E2E spec verification to Test Quality dimension
- `/review-pr`: Expanded DDD reconciliation logic in code review step

**Rule updates**:
- `git-workflow.md`: Added Branch Lifecycle tiered policy (auto-delete → tag-archive → keep)
- `worktree-autorun.md`: Added plan doc awareness to execution rules
- `testing.md`: Added Coverage Tax section
- `database-safety.md` (supabase module): Added Function EXECUTE Privileges deny-all-default section

### Stats
- 16 files changed
- 3 new files (framework-sync SKILL.md, blast-radius-map.json, cross-cutting-overrides.json)
- Manifest: 0.1.0 → 0.2.0

---

## [1.0.0] — 2026-03-26

### Initial Release

Stack-agnostic development operating system for Claude Code. Extracted from the Simplrr production codebase, scrubbed of all domain-specific content, and structured as a reusable framework.

### What's Included

**Process Layer (universal — identical across all projects):**

- **10 rules** (.claude/rules/) — Engineering philosophy, document-driven development, production safety, git workflow, worktree autopilot, autonomous guardrails, CEO-CTO communication, error recovery, MCP tools, testing
- **22 core skills** (.claude/skills/) — Full development lifecycle from session-start through self-optimize
- **3 hooks** (.claude/hooks/) — block-dangerous.sh, protect-files.sh, quality-gate.sh
- **1 meta-skill** — `/simplrr-framework` with 3 modes (init, integrate, sync)
- **Memory system** (memory/) — MEMORY.md, observations.md, intuitions.md, knowledge-map.md
- **Documentation infrastructure** (docs/) — 4 core doc templates, 5 guide templates, active/completed lifecycle
- **Safety infrastructure** — landmines.md, coffee-notes.md, claude-cookbooks.md reference
- **Framework manifest** — .framework-manifest.json with file classification and sync defense

**Adapter Layer (template — customized per project via [FILL] markers):**

- CLAUDE.md constitution template
- ORIENTATION.md philosophy template
- Hook scripts with configurable commands
- Settings template with MCP placeholders
- 143 total [FILL] markers across all template files

**Module System (optional add-ons — activated during init):**

| Module | Skills | Rules | References | Total Files |
|--------|--------|-------|------------|-------------|
| supabase | db-audit, scaling-check | database-safety | — | 3 |
| devtools | prod-audit | — | — | 1 |
| legal | legal-compliance | — | 9 (GDPR, CCPA, UK-GDPR, WCAG, PCI-DSS, FOOD-SAFETY, MARKETING, CONSUMER-PROTECTION, INDEX) | 10 |
| content | content | — | — | 1 |
| perf | perf-audit | — | bundle-size lens | 2 |

### Architecture

- **Two layers**: Process (~70%, never modified) + Adapter (~30%, customized with [FILL] markers)
- **Three modes**: `init` (new projects), `integrate` (existing projects), `sync` (contribute back)
- **Defense mechanism**: .framework-manifest.json with rejection patterns prevents project-specific contamination from leaking into the template repo
- **80 total files**: 35 core + 25 adapter + 17 module + 3 infrastructure

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Source of truth | Model B Decentralized | Any project can contribute back; manifest-based defense |
| Module activation | Manifest-driven | init asks about stack → activates relevant modules |
| [FILL] markers | `<!-- FILL: description -->` | Machine-parseable, human-readable, grep-able |
| Memory in repo | `memory/` at root | Enables git tracking, team sharing, backup |
| Core docs | 4 templates (not 5) | Projects define their own 5th doc via init |

### Extracted From

Simplrr — a production multi-tenant restaurant ordering app that has been running this framework since October 2025. The framework represents ~4 months of iterative refinement of development workflows, quality gates, and Claude Code optimization.
