#!/usr/bin/env bash
# Pre-commit guardrail: no debug logs and no conflict markers get committed.
# Used by .pre-commit-config.yaml and runnable by hand: bash hooks/check-hygiene.sh
set -uo pipefail

changed=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)
[ -z "$changed" ] && exit 0

status=0

# 1) console.log/debugger in JS/TS
js=$(echo "$changed" | grep -E '\.(ts|tsx|js|jsx)$' || true)
if [ -n "$js" ]; then
  # shellcheck disable=SC2086
  if grep -nHE "console\.(log|debug|info|trace)[[:space:]]*\(|\bdebugger\b|\.only\(" $js; then
    echo "→ remove debug logs / debugger / .only before committing"
    echo "  (skill: clean-code, section 9 - use a logger with a level if you truly need it)"
    status=1
  fi
fi

# 2) marker conflict
if [ -n "$changed" ]; then
  # shellcheck disable=SC2086
  if grep -nE "^(<<<<<<<|>>>>>>>) " $changed 2>/dev/null; then
    echo "→ conflict markers left in the file"
    status=1
  fi
fi

# 3) stray System.out/print in Java and fmt.Print in Go (production sources only)
prod=$(echo "$changed" | grep -E '^(src|internal|cmd/api)/.*\.(java|go)$' || true)
if [ -n "$prod" ]; then
  # shellcheck disable=SC2086
  if grep -nHE "System\.(out|err)\.print|fmt\.Print(ln|f)?\(" $prod; then
    echo "→ log through a logger (SLF4j, Go: log/slog), not straight to stdout"
    status=1
  fi
fi

exit $status
