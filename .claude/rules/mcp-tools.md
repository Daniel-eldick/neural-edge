---
description: MCP tools usage guidelines
alwaysApply: false
---

# MCP Tools & Agents - ALWAYS USE PROACTIVELY

**User Mandate**: _"Use of agents, MCPs, and frequent commits to GitHub are always encouraged"_

**Key Principle**: Prefer MCP tools over bash commands for database and browser operations.

## Available Tools

<!-- FILL: List your project's MCP tools. Examples below. -->
<!-- Remove sections that don't apply. Add sections for your MCPs. -->

### 1. Database MCP

<!-- FILL: Replace with your database MCP commands -->
Database queries, migrations, security audits:

- `mcp__database__execute_sql` - Query data, verify security, check indexes
- `mcp__database__apply_migration` - Schema changes (DDL)
- `mcp__database__get_advisors` - Security/performance audits
- `mcp__database__list_tables` - Schema exploration

### 2. Chrome DevTools MCP

Browser testing, manual verification:

- `take_snapshot`, `navigate_page`, `click`, `fill`, `emulate`
- Use for manual testing verification
- Playwright for automated regression tests only

### 3. Task Agents

Complex multi-step work:

- **Explore Agent** - Codebase exploration ("where is...", "how does...")
- **Plan Agent** - Feature breakdown, implementation roadmaps
- Use proactively for 3+ step tasks

### 4. TodoWrite

Progress tracking for complex tasks (3+ steps):

- Mark "in_progress" BEFORE starting
- Mark "completed" IMMEDIATELY after finishing
- Always have EXACTLY ONE task "in_progress"

## When to Use

<!-- FILL: Update the table with your actual MCP tool names -->
| Operation       | Use This                | Not This    |
| --------------- | ----------------------- | ----------- |
| Database query  | Database MCP            | bash psql   |
| Manual testing  | Chrome DevTools MCP     | Playwright  |
| Complex search  | Task Explore agent      | Simple grep |
| Multi-step work | TodoWrite + Task agents | Ad-hoc      |
