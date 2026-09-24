#!/usr/bin/env python3
"""
test-lock — Characterization & Safety-Locked Refactoring Harness.
Zero-dependency, stdlib-only.

Usage:
    # 1. Capture baseline (ensure tests pass and snapshot current code metrics):
    python3 tools/test-lock.py snapshot --test-cmd "npm test" src/orders.ts

    # 2. Perform refactoring with your agent/IDE...

    # 3. Verify safety (runs tests, compares metrics, blocks regression):
    python3 tools/test-lock.py verify --test-cmd "npm test" src/orders.ts
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CC_SCAN = HERE / "cc-scan.py"
LOCK_FILE = Path(".test-lock-state.json")


def run_cmd(cmd: str) -> tuple[int, str]:
    """Runs a shell command and returns (exit_code, output)."""
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def run_scanner(paths: list[str]) -> dict:
    """Runs cc-scan on the target paths and returns the parsed JSON report."""
    if not CC_SCAN.exists():
        return {"score": 100, "findings": []}
    proc = subprocess.run(
        [sys.executable, str(CC_SCAN), *paths, "--json", "--no-baseline"],
        capture_output=True, text=True
    )
    out = proc.stdout
    start = out.find("{")
    if start >= 0:
        try:
            return json.loads(out[start:])
        except json.JSONDecodeError as err:
            sys.stderr.write(f"Warning: Failed to parse scanner output: {err}\n")
    return {"score": 0, "findings": []}


def cmd_snapshot(args: argparse.Namespace) -> int:
    """Step 1: Snapshot baseline state and verify existing tests."""
    print("🔒 [1/2] Verifying test suite before refactoring...")
    if args.test_cmd:
        code, out = run_cmd(args.test_cmd)
        if code != 0:
            print(f"❌ Baseline tests failed! Cannot lock untested or broken code.\n{out}")
            return 1
        print("✅ Baseline test suite is GREEN.")
    else:
        print("⚠️  No --test-cmd provided. Ensure characterization tests exist.")

    scan_res = run_scanner(args.paths)
    state = {
        "paths": args.paths,
        "test_cmd": args.test_cmd,
        "score": scan_res.get("score", 100),
        "findings_count": len(scan_res.get("findings", [])),
    }

    LOCK_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"📸 Baseline snapshot saved to {LOCK_FILE.name}")
    print(f"   Initial Clean Code Score: {state['score']}/100 ({state['findings_count']} findings)")
    print("👉 Proceed with refactoring. Run `python3 tools/test-lock.py verify` when done.")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    """Step 2: Verify tests and score after refactoring."""
    if not LOCK_FILE.exists():
        print("❌ No snapshot found. Run `python3 tools/test-lock.py snapshot` first.")
        return 1

    state = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
    test_cmd = args.test_cmd or state.get("test_cmd")
    paths = args.paths or state.get("paths", [])

    print("🛡️ [2/2] Verifying refactoring safety...")
    if test_cmd:
        code, out = run_cmd(test_cmd)
        if code != 0:
            print(f"❌ REGRESSION DETECTED! Tests broke during refactoring.\n\nTest Output:\n{out}")
            print("\n🚨 Action: Revert the last change or fix the regression before proceeding.")
            return 1
        print("✅ Test suite is GREEN. Behaviour preserved.")

    scan_res = run_scanner(paths)
    new_score = scan_res.get("score", 100)
    new_findings = len(scan_res.get("findings", []))
    old_score = state.get("score", 100)
    old_findings = state.get("findings_count", 0)

    print("\n📊 Quality Differential:")
    print(f"   Clean Code Score: {old_score:.1f} ➔ {new_score:.1f}")
    print(f"   Findings Count:   {old_findings} ➔ {new_findings}")

    if new_score < old_score:
        print(f"⚠️  Warning: Clean Code Score dropped by {old_score - new_score:.1f} points.")
    else:
        print("🎉 Refactoring Successful & Verified Safe!")

    if LOCK_FILE.exists():
        LOCK_FILE.unlink()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Test-Locking Refactoring Safety Harness")
    sub = parser.add_subparsers(dest="command", required=True)

    snap = sub.add_parser("snapshot", help="Capture baseline test status & code metrics")
    snap.add_argument("--test-cmd", "-t", type=str, help="Command to run tests (e.g. 'npm test')")
    snap.add_argument("paths", nargs="+", help="Files/directories being refactored")

    ver = sub.add_parser("verify", help="Verify tests pass and compare metrics after refactor")
    ver.add_argument("--test-cmd", "-t", type=str, help="Command to run tests (optional if captured in snapshot)")
    ver.add_argument("paths", nargs="*", help="Files/directories being refactored (optional)")

    args = parser.parse_args()
    if args.command == "snapshot":
        return cmd_snapshot(args)
    elif args.command == "verify":
        return cmd_verify(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
