---
name: simplrr-framework
description: >-
  Meta-skill for the development operating system. Two modes:
  init (new project setup), integrate (adopt into existing project).
  For sync operations, use /framework-sync instead.
  Triggers: /simplrr-framework init, /simplrr-framework integrate
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, Task, TodoWrite
---

# Simplrr Framework Skill

The meta-skill that makes the framework come alive. Sets up the development operating system on new or existing projects.

> **Sync has moved**: Use `/framework-sync push` to contribute improvements back to the template repo, or `/framework-sync pull` to get updates. The old `/simplrr-framework sync` trigger is deprecated.

## Two Modes

| Mode            | When                             | Behavior                                          |
| --------------- | -------------------------------- | ------------------------------------------------- |
| **`init`**      | New project (just forked/cloned) | Brainstorm-style questionnaire → fills all markers |
| **`integrate`** | Existing project with code       | Investigate → create phased integration plan      |

---

## Mode 1: Init (New Project Setup)

**Trigger**: `/simplrr-framework init`

Transforms the generic framework into a project-specific development operating system. Fills all `[FILL]` markers, activates relevant modules, and seeds documentation.

### Step 1: Welcome + Validate

1. Verify we're in a framework repo (check for `.framework-manifest.json`)
2. Count remaining `[FILL]` markers: `grep -r 'FILL:' --include='*.md' --include='*.sh' --include='*.json' | wc -l`
3. If zero markers remain, warn: "This project appears already initialized. Use `/framework-sync pull` to get updates."

### Step 2: Project Discovery (Brainstorm-Style)

Use `AskUserQuestion` for each category. Gather enough context to fill all markers.

**Round 1: Identity**

```
- What is this project? (1-2 sentence pitch)
- What's the tech stack? (language, framework, database, hosting)
- Production URL? (or "not deployed yet")
- Staging URL? (or "not set up yet")
- Repo name and org?
```

**Round 2: Architecture**

```
- Multi-tenant or single-tenant?
- Key domain concepts? (orders, users, products, etc.)
- State management pattern? (server state, app state, form state)
- Primary user types? (admin, customer, both?)
- Core data flow? (describe the most important operation)
```

**Round 3: Development Context**

```
- How do you build? (npm run build, go build, etc.)
- How do you test? (test runner, test command)
- How do you lint/format? (linter, quality check command)
- How do you type-check? (tsc, mypy, etc.)
- Pre-commit workflow? (quality:check equivalent)
```

**Round 4: Operational Context**

```
- Target users' network conditions? (fiber, 3G, mixed?)
- Performance budget? (or "use defaults")
- UX litmus test? (who is the primary user, what's their context?)
- Risk tolerance? (how critical is this system?)
```

**Round 5: Modules**

```
Which optional modules should be activated?
- [ ] Supabase (database audit, scaling checks, safety rules)
- [ ] Chrome DevTools (production audit via browser MCP)
- [ ] Legal Compliance (GDPR, CCPA, accessibility, etc.)
- [ ] Content (brand voice-driven content generation)
- [ ] Performance (bundle analysis, Core Web Vitals, self-optimize lens)
```

### Step 3: Fill Markers

Process all files with `[FILL]` markers. For each file:

1. Read the file
2. Identify all `<!-- FILL: ... -->` and `# FILL: ...` markers
3. Replace with project-specific content based on discovery answers
4. Write the updated file

**Priority order** (most important first):

1. `CLAUDE.md` — The constitution. Must be complete and accurate.
2. `docs/guides/ORIENTATION.md` — The philosophy + architecture.
3. `.claude/hooks/*.sh` — Hook scripts with correct commands.
4. `.claude/settings.local.json` — MCP configs and permissions.
5. `.claude/rules/testing.md` — Test commands.
6. `.claude/rules/mcp-tools.md` — Available MCP tools.
7. `.claude/rules/engineering-philosophy.md` — Domain examples.
8. `docs/guides/INCIDENT_RESPONSE.md` — Infrastructure details.
9. All remaining files with markers.

### Step 4: Activate Modules

For each selected module:

1. Read `.framework-manifest.json` to find module files and dependencies
2. Copy skills from `_modules/<module>/` to `.claude/skills/`
3. Copy rules from `_modules/<module>/` to `.claude/rules/`
4. Copy references from `_modules/<module>/references/` to `.claude/references/`
5. Update `CLAUDE.md` rules table and skills table to include module entries
6. Update `docs/guides/SKILLS_MANUAL.md` to reflect activated modules

**Dependency chain**: If module A depends on a rule from module B, install B's dependencies too.

### Step 5: Seed Documentation

1. Create `docs/completed/.gitkeep` (empty archive directory)
2. Set dates in `memory/MEMORY.md` and `memory/knowledge-map.md`
3. Initialize `docs/INCOMPLETE_FEATURES.md` with any known items from discovery
4. Update `.framework-manifest.json` with activated modules

### Step 6: Verification

Run the contamination check:

```bash
grep -r 'FILL:' --include='*.md' --include='*.sh' --include='*.json' | grep -v '_modules/' | grep -v 'SKILL.md'
```

**Expected**: Zero unfilled markers outside of module templates and this skill file.

Present summary:

```
## Init Complete

**Project**: [name]
**Stack**: [tech stack]
**Modules activated**: [list]
**Markers filled**: X/Y (Z remaining in inactive modules — expected)
**Files modified**: [count]

### What's Ready
- CLAUDE.md configured for your project
- [N] rules active (X core + Y module)
- [N] skills available
- Memory system initialized
- Documentation structure seeded

### Next Steps
1. Review CLAUDE.md — make sure it reflects your project accurately
2. Run `/session-start` to begin your first session
3. Start with `/investigate` to build your knowledge map
```

---

## Mode 2: Integrate (Existing Project)

**Trigger**: `/simplrr-framework integrate`

For projects that already have code, configs, and possibly their own `.claude/` directory. Creates a phased integration plan rather than overwriting.

### Step 1: Investigate Existing Setup

1. Check for existing `.claude/` directory
2. Check for existing `CLAUDE.md`
3. Check for existing `docs/` structure
4. Check for existing hooks, rules, skills
5. Identify potential conflicts

### Step 2: Assess Compatibility

| Check | Conflict? | Resolution |
|-------|-----------|------------|
| Existing CLAUDE.md | Compare sections → merge plan | Keep existing mandates, add framework structure |
| Existing rules | Diff against framework rules | Merge non-conflicting, flag conflicts |
| Existing skills | List and categorize | Keep existing, add framework skills that don't overlap |
| Existing hooks | Compare scripts | Merge or chain hooks |
| Existing docs | Check structure | Adapt framework docs to fit existing pattern |

### Step 3: Discovery (Abbreviated)

Same questions as `init` mode, but many answers can be inferred from the existing codebase:

- Read `package.json` for stack info
- Read existing `CLAUDE.md` for mandates
- Read existing test configs for test commands
- Read CI configs for quality gates

Only ask what can't be inferred.

### Step 4: Create Integration Plan

Create `docs/active/FRAMEWORK_INTEGRATION.md` with phased adoption plan (Non-Destructive → Merge → Activate). Present to CEO for `/sign-off`.

---

## Defense Logic (Slim — Init/Integrate Relevant)

The `.framework-manifest.json` classifies files:

| Category | Init Behavior | Integrate Behavior |
|----------|--------------|-------------------|
| **core** | Copy as-is (no markers) | Add if missing, don't overwrite |
| **adapter** | Fill `[FILL]` markers | Merge with existing |
| **module** | Copy if activated | Copy if activated, flag conflicts |
| **never-sync** | Initialize templates | Don't touch existing |

For sync defense logic (contamination checks, rejection patterns), see `/framework-sync`.

---

## Principles

1. **Init is generous** — Help fill everything. Ask questions. Be thorough.
2. **Integrate is cautious** — Never overwrite without asking. Existing work has value.
3. **The manifest is infrastructure** — Don't modify it casually.
4. **Modules are opt-in** — Never activate a module the user didn't choose.
5. **Memory never syncs** — Memory is always project-specific.

---

## Skill Pipeline

```
Fork template repo → /simplrr-framework init → /session-start → begin working
                     /simplrr-framework integrate → /sign-off → phased adoption

For ongoing maintenance:
/framework-sync push → contribute improvements back
/framework-sync pull → get framework updates
```
