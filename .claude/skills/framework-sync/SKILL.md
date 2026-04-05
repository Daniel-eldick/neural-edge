---
name: framework-sync
description: >-
  Two-way framework synchronization. Push improvements to the template repo,
  or pull updates from it. Contamination defense prevents project-specific
  content from leaking into the universal framework.
  Triggers: /framework-sync push, /framework-sync pull
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, Task, TodoWrite
---

# Framework Sync Skill

Ongoing maintenance skill for keeping projects and the framework template repo in sync. Two directions, same safety pattern.

## Two Modes

| Mode       | Direction                      | When                                          |
| ---------- | ------------------------------ | --------------------------------------------- |
| **`push`** | Project → framework repo       | You improved a skill/rule and want to share it |
| **`pull`** | Framework repo → project       | Framework has updates you want to adopt        |

---

## Shared Safety Pattern (Both Directions)

```
Step 1: Pre-flight     → Version check, identify remote, validate manifest
Step 2: Diff report    → Categorize changes by core/adapter/module
Step 3: Merge proposal → Core: recommend accept. Adapter: smart merge. Module: if activated.
Step 4: CEO review     → Present proposal. CEO approves/rejects each change or batch.
Step 5: Apply          → Only after CEO says "go". Commit with conventional format.
```

---

## Pre-Flight (Both Modes)

### Step 1: Validate Manifest

1. Read `.framework-manifest.json` from project root
2. Verify required fields exist:
   - `framework-version` (current: `0.2.0`)
   - `classification` (core, adapter, module definitions)
   - `sync.rejection-patterns`
   - `sync.never-sync`
   - `sync.always-sync`
3. If `framework-repo` or `last-sync-commit` fields are missing (pre-0.2.0 manifest):
   - Ask user for the repo owner/name
   - Write both fields to manifest
   - Set `last-sync-commit` to framework repo's current HEAD

### Step 2: Identify Remote

```bash
# Get the framework repo from manifest
REPO=$(jq -r '.["framework-repo"]' .framework-manifest.json)
# Verify it exists
gh repo view "$REPO" --json name
```

### Step 3: Get Sync Anchor

```bash
# SHA of last successful sync
LAST_SYNC=$(jq -r '.["last-sync-commit"]' .framework-manifest.json)
# Current HEAD of framework repo
REMOTE_HEAD=$(gh api "repos/$REPO/commits/main" --jq '.sha')
```

---

## Mode 1: Push (Project → Framework Repo)

**Trigger**: `/framework-sync push`

Extracts framework-level improvements from this project and pushes them to the template repo. Defense mechanism prevents project-specific contamination.

### Step 1: Identify Changed Files

Compare framework-classified files against the template repo:

```bash
# Clone framework repo to temp directory
gh repo clone "$REPO" /tmp/framework-sync-work
```

For each file in `classification.core.files`:
1. Compare local version vs framework repo version
2. If different, add to candidate list

### Step 2: Contamination Check

For each candidate file, run rejection patterns from the manifest:

```bash
# Load rejection patterns from manifest
# Check each candidate against patterns
```

**Default rejection patterns** catch:
- Project name (bare, without `-framework` suffix)
- Domain-specific terms (e.g., industry-specific nouns unique to the project)
- Staging/production URLs
- API keys or tokens

**Classification-driven behavior**:

| Classification  | Push behavior                                |
| --------------- | -------------------------------------------- |
| **core**        | Contamination check → accept if clean        |
| **adapter**     | Contamination check → manual review if mixed |
| **module**      | Only if module exists in framework           |
| **never-sync**  | Blocked (memory, active docs, etc.)          |
| **always-sync** | Auto-included in push                        |

### Step 3: Generate Diff Report

```markdown
## Push Report

**Source**: [project name]
**Target**: [framework repo]
**Last sync**: [SHA] ([date])
**Files scanned**: [count]

### Clean (ready to push)

| File | Change Summary |
|------|---------------|
| [file] | [what changed] |

### Rejected (contamination detected)

| File | Pattern Matched |
|------|----------------|
| [file] | [what triggered rejection] |

### Manual Review (mixed changes)

| File | Reason |
|------|--------|
| [file] | [some changes universal, some project-specific] |
```

### Step 4: CEO Review

Present the diff report. CEO approves/rejects each file or batch.

### Step 5: Apply + Push

1. Apply approved changes to the cloned framework repo
2. Commit with: `sync: improvements from [project] ([date])`
3. Push to framework repo
4. Update `last-sync-commit` in local manifest with new HEAD SHA

---

## Mode 2: Pull (Framework Repo → Project)

**Trigger**: `/framework-sync pull`

Gets framework updates and applies them to the current project. Smart merge for adapter files preserves project customizations.

### Step 1: Check for Updates

```bash
# Compare last-sync-commit to current framework HEAD
# If same → "Already up to date. No changes since last sync."
# If different → proceed with diff
```

### Step 2: Categorize Changes

For each file changed in the framework repo since `last-sync-commit`:

```bash
# Get changed files between last sync and current HEAD
gh api "repos/$REPO/compare/$LAST_SYNC...$REMOTE_HEAD" --jq '.files[].filename'
```

Categorize by manifest classification:

| Classification  | Pull behavior                                     |
| --------------- | ------------------------------------------------- |
| **core**        | Auto-recommend accept (these should be universal) |
| **adapter**     | Smart merge proposal (preserve customizations)    |
| **module**      | Only if module is activated in project            |
| **never-sync**  | Blocked (same list as push)                       |
| **always-sync** | Auto-included in pull                             |

### Step 3: Smart Merge for Adapter Files

When both the template and the project have modified an adapter file:

1. Read the template's current version (from framework repo)
2. Read the project's current version (local)
3. Understand the intent of each change
4. Propose a merged version that preserves project customizations while incorporating template improvements
5. **Always show a unified diff** of proposed result vs project's current version — CEO must see exactly what's being lost/gained
6. CEO reviews the proposed merge before applying

### Step 4: Generate Pull Report

```markdown
## Pull Report

**Source**: [framework repo]
**Target**: [project name]
**Changes since**: [last-sync-commit SHA] ([date])

### Core Updates (recommend accept)

| File | Change Summary |
|------|---------------|
| [file] | [what changed] |

### Adapter Merges (review required)

| File | Template Change | Project Has Custom | Merge Proposed |
|------|----------------|-------------------|----------------|
| [file] | [what changed] | Yes/No | [summary] |

### Module Updates (if activated)

| Module | File | Change |
|--------|------|--------|
| [module] | [file] | [what changed] |

### Skipped (not activated or never-sync)

| File | Reason |
|------|--------|
| [file] | [module not activated / never-sync] |
```

### Step 5: CEO Review

Present the pull report with diffs. CEO approves/rejects.

### Step 6: Apply

1. Apply approved core updates (overwrite — core files are universal)
2. Apply approved adapter merges (write merged version)
3. Apply approved module updates
4. Update `last-sync-commit` in manifest with framework repo HEAD

---

## Defense Logic

### The `.framework-manifest.json` Classification System

The manifest is the single source of truth for what syncs and what doesn't.

| Category        | Description                                              | Push             | Pull              |
| --------------- | -------------------------------------------------------- | ---------------- | ----------------- |
| **core**        | Universal process files. Identical across all projects.  | Accept if clean  | Auto-recommend    |
| **adapter**     | Template files customized per project.                   | Manual review    | Smart merge       |
| **module**      | Optional add-ons. Only active if module is enabled.      | Module-scoped    | Module-scoped     |
| **never-sync**  | Project-specific files that must never leave.            | Blocked          | Blocked           |
| **always-sync** | Critical process files. Always included.                 | Auto-included    | Auto-included     |

### Contamination Patterns

Rejection patterns live in `sync.rejection-patterns` in the manifest. They are regex patterns applied to file content before pushing to the framework repo.

**Example patterns** (customize per project during `/simplrr-framework init`):
```json
[
  "\\bmy-project\\b",
  "\\bmy-supabase-id\\b",
  "my-project\\.app",
  "staging\\.my-project\\.app",
  "\\bmy-company\\b"
]
```

### `last-sync-commit` Anchor

Both push and pull use this SHA as the diff anchor. It records the framework repo's HEAD at the time of the last successful sync. This eliminates fuzzy version comparisons — we know exactly what was synced.

---

## Principles

1. **Push is strict, pull is helpful** — Push rejects anything suspicious. Pull recommends and assists.
2. **Contamination is the #1 risk** — Project-specific content in the template repo poisons all future projects.
3. **Smart merge preserves work** — Never overwrite adapter customizations without showing the diff.
4. **CEO reviews every sync** — No auto-apply. The CEO sees every change before it lands.
5. **The manifest is infrastructure** — Like autoresearch's immutable `prepare.py`. Don't modify to bypass defense.
6. **Memory never syncs** — Memory is always project-specific. Period.

---

## Anti-Patterns

- Modifying rejection patterns to push contaminated files
- Auto-approving adapter merges without reading the diff
- Pulling without reviewing what changed (breaking customizations)
- Syncing memory files (project-specific context)
- Running push without contamination check
- Skipping `last-sync-commit` update after sync

---

## Skill Pipeline

```
/framework-sync push → contamination check → CEO review → push to template
/framework-sync pull → version check → diff report → CEO review → apply locally

Lifecycle skills (run once or rarely):
/simplrr-framework init      → set up new project
/simplrr-framework integrate → adopt into existing project
```
