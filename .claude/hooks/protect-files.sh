#!/bin/bash
# PreToolUse hook for Edit|Write — blocks modifications to protected files
# Exit 0 = allow, Exit 2 = block

# Require jq for JSON parsing
if ! command -v jq &>/dev/null; then
  echo "WARNING: jq not installed — hook cannot parse input, allowing by default." >&2
  exit 0
fi

# Read JSON from stdin
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

if [ -z "$file_path" ]; then
  exit 0
fi

# Block .env files (but allow .env.example)
if echo "$file_path" | grep -qE '\.env(\.|$)' && ! echo "$file_path" | grep -qE '\.env\.example$'; then
  echo "BLOCKED: Cannot modify $file_path — environment files are protected." >&2
  exit 2
fi

# Block .git/ directory
if echo "$file_path" | grep -qE '\.git/'; then
  echo "BLOCKED: Cannot modify files inside .git/ directory." >&2
  exit 2
fi

# Block autoresearch evaluator (immutable — Karpathy pattern)
if echo "$file_path" | grep -qE 'src/autoresearch/prepare\.py$'; then
  echo "BLOCKED: Cannot modify prepare.py — the evaluator is immutable. See autoresearch architecture." >&2
  exit 2
fi

exit 0
