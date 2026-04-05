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

# Block package-lock.json (use npm install instead)
if echo "$file_path" | grep -qE 'package-lock\.json$'; then
  echo "BLOCKED: Cannot modify package-lock.json directly. Use npm install." >&2
  exit 2
fi

# Block .git/ directory
if echo "$file_path" | grep -qE '\.git/'; then
  echo "BLOCKED: Cannot modify files inside .git/ directory." >&2
  exit 2
fi

# FILL: Add project-specific protected file patterns below
# Example: Block existing database migration files
# if echo "$file_path" | grep -qE 'migrations/[0-9]'; then
#   echo "BLOCKED: Cannot modify existing migration files. Use your migration tool." >&2
#   exit 2
# fi

exit 0
