#!/bin/bash
# Stop hook — runs quality check before Claude finishes a task
# Exit 0 = pass (allow stop), Exit 2 = fail (prevent stop, force fix)

# FILL: Replace with your project's type-check or quality command
# Examples:
#   npx tsc --noEmit --pretty     (TypeScript)
#   mypy .                        (Python)
#   go vet ./...                  (Go)
#   cargo check                   (Rust)
output=$(npx tsc --noEmit --pretty 2>&1)
exit_code=$?

if [ $exit_code -ne 0 ]; then
  echo "QUALITY CHECK FAILED — fix errors before finishing:" >&2
  echo "$output" | head -30 >&2
  exit 2
fi

exit 0
