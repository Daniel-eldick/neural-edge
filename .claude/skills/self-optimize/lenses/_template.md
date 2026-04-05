# Lens: [Name]

> Copy this template to create a new lens. Fill in every section.

## Objective

**Metric**: [what number to optimize]
**Direction**: [lower is better / higher is better]
**Current baseline**: [value as of date]
**Target**: [aspirational goal, if any]

## Evaluator

The command(s) that produce the metric. The agent MUST NOT modify these.

```bash
[exact command to run]
```

**How to extract the metric from output**: [describe parsing — e.g., "last line contains the number"]

## Target Files

Files the agent is allowed to modify during optimization.

```
[glob pattern or explicit file list]
```

## Scope Boundaries

Files and patterns the agent must NEVER touch, even if they seem related.

```
[explicit exclusions — e.g., "never modify vite.config.ts", "never delete tests"]
```

## Safety Checks

Commands that must pass BEFORE a change is kept. If any fail, DISCARD.

```bash
[e.g., npm run quality:check]
```

## Hints

Optimization ideas to seed the first few iterations. The agent should try these first before exploring freely.

- [hint 1]
- [hint 2]
- [hint 3]

## Known Dead Ends

Approaches that have been tried and don't work. Save the agent from repeating mistakes. Updated automatically by the journal.

- (none yet)
