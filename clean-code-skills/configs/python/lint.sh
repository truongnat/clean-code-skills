#!/usr/bin/env bash
# Run the Python lint set against the clean-code standard.
#   ./lint.sh          -> check the reference file (must be clean)
#   ./lint.sh bad      -> check the violating demo (to see the rules fire)
#   ./lint.sh fix      -> autofix + format
# Tools live in .venv-cc inside the workspace; nothing to prepare.
set -uo pipefail
cd "$(dirname "$0")"
VENV="${VENV:-$HOME/.venv-cc}"
if [ ! -x "$VENV/bin/ruff" ]; then
  echo "[lint] ruff/black/mypy missing in $VENV - creating a temporary venv..."
  python3 -m venv "$VENV" >/dev/null 2>&1
  "$VENV/bin/pip" install -q --disable-pip-version-check ruff black mypy || {
    echo "[lint] could not install the tools (network?); run: make setup"; exit 127; }
fi
MODE="${1:-check}"
case "$MODE" in
  bad)  TARGET="src/orders_bad.py" ;;
  *)    TARGET="src/orders_good.py" ;;
esac
fail=0
if [ "$MODE" = "fix" ]; then
  "$VENV/bin/ruff" check --fix . && "$VENV/bin/black" . ; exit $?
fi
echo "[lint] ruff check $TARGET"
"$VENV/bin/ruff" check "$TARGET" || fail=1
echo "[lint] black --check $TARGET"
"$VENV/bin/black" --check --quiet "$TARGET" || fail=1
echo "[lint] mypy $TARGET"
"$VENV/bin/mypy" "$TARGET" || fail=1
exit $fail
