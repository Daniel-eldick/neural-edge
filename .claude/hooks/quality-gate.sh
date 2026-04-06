#!/bin/bash
# Stop hook — runs quality check before Claude finishes a task
# Exit 0 = pass (allow stop), Exit 2 = fail (prevent stop, force fix)

# Activate venv if present
if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

output=$(ruff check . && mypy . && pytest -x --timeout=30 2>&1)
exit_code=$?

if [ $exit_code -ne 0 ]; then
  echo "QUALITY CHECK FAILED — fix errors before finishing:" >&2
  echo "$output" | head -30 >&2
  exit 2
fi

exit 0
