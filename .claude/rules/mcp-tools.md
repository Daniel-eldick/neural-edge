---
description: MCP tools usage guidelines
alwaysApply: false
---

# MCP Tools & Agents - ALWAYS USE PROACTIVELY

**User Mandate**: _"Use of agents, MCPs, and frequent commits to GitHub are always encouraged"_

**Key Principle**: Use Task agents for complex multi-step work. No database or browser MCPs currently configured — this is a Python trading bot with CLI-based development.

## Available Tools

### 1. Task Agents

Complex multi-step work:

- **Explore Agent** - Codebase exploration ("where is...", "how does...")
- **Plan Agent** - Feature breakdown, implementation roadmaps
- Use proactively for 3+ step tasks

### 2. TodoWrite

Progress tracking for complex tasks (3+ steps):

- Mark "in_progress" BEFORE starting
- Mark "completed" IMMEDIATELY after finishing
- Always have EXACTLY ONE task "in_progress"

## When to Use

| Operation       | Use This                | Not This    |
| --------------- | ----------------------- | ----------- |
| Complex search  | Task Explore agent      | Simple grep |
| Multi-step work | TodoWrite + Task agents | Ad-hoc      |
| API testing     | pytest with mocks       | Manual curl |
| Strategy testing| Freqtrade CLI           | Raw Python  |
