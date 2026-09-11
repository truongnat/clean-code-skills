#!/usr/bin/env bash
# Architecture gate for pre-commit: only active when the repo declares its layers.
# Deliberately quiet when there is no config, so copying this folder never breaks a repo.
set -uo pipefail

[ -f arch-scan.config.json ] || exit 0
[ -f tools/arch-scan.py ] || exit 0

SRC="src"
[ -d "$SRC" ] || SRC="."

out=$(python3 tools/arch-scan.py "$SRC" --fail-on error --json 2>&1)
status=$?
if [ "$status" -ne 0 ]; then
  echo "$out" | python3 -c '
import json, sys
raw = sys.stdin.read()
start = raw.find("{")
if start < 0:
    print(raw[:400]); sys.exit(1)
d = json.loads(raw[start:])
print("arch-scan: %s/100 (grade %s) - %d error(s)" % (d["score"], d["grade"], d["counts"]["error"]))
for f in d["findings"][:8]:
    print("  %s:%s  %s  %s" % (f["file"], f["line"], f["rule"], f["message"]))
print()
print("Fix the direction (port + adapter), or scope an exception in the file:")
print("  # arch-scan:allow UPWARD_DEPENDENCY - ticket ARCH-142, removed in Q4")
'
  exit 1
fi
exit 0
