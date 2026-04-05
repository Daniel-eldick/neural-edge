#!/bin/bash
# PreToolUse hook for Bash — blocks dangerous git commands
# Exit 0 = allow, Exit 2 = block

# Require jq for JSON parsing
if ! command -v jq &>/dev/null; then
  echo "WARNING: jq not installed — hook cannot parse input, allowing by default." >&2
  exit 0
fi

# Read JSON from stdin
input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')

if [ -z "$command" ]; then
  exit 0
fi

# FILL: Replace 'main' with your production branch name if different
# Block patterns
if echo "$command" | grep -qE 'git\s+push\s+(origin\s+)?main(\s|$)'; then
  # Allow /release skill to promote develop → main (CEO-approved)
  if [ -f /tmp/.claude-release-push ]; then
    rm -f /tmp/.claude-release-push
    exit 0
  fi
  echo "BLOCKED: Direct push to main is not allowed. Use /release to promote develop → main." >&2
  exit 2
fi

if echo "$command" | grep -qE 'git\s+push\s+.*--force|git\s+push\s+.*-f(\s|$)'; then
  echo "BLOCKED: Force push is not allowed." >&2
  exit 2
fi

if echo "$command" | grep -qE 'git\s+reset\s+--hard'; then
  echo "BLOCKED: git reset --hard can destroy work. Use git stash instead." >&2
  exit 2
fi

if echo "$command" | grep -qE 'git\s+clean\s+-f'; then
  echo "BLOCKED: git clean -f can delete untracked files permanently." >&2
  exit 2
fi

exit 0
