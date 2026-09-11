#!/usr/bin/env python3
"""Test suite for arch-scan.py — run it after every change to the tool.

Fixtures under `tests/fixtures/layers/`:
  * `dirty/`  -> must light up all four error rules, exit 1
  * `clean/`  -> must produce zero findings (anti-false-positive guarantee)
  * `java/`, `go/` -> dotted and module-path imports resolved via rootPackages
Plus: the allow-comment mechanism, config fallback, CLI surface, and one dogfood
check proving the tool never shrugs at an unknown layout.

Run:  python3 tests/run_arch_checks.py     (exit 0 = all green)
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                     # tools/
TOOL = ROOT / "arch-scan.py"
FIX = HERE / "fixtures" / "layers"

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))


def run(*args: str, cwd: Path | None = None) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(TOOL), *[str(a) for a in args]],
                          capture_output=True, text=True, cwd=str(cwd) if cwd else None)
    return proc.returncode, proc.stdout + proc.stderr


def report(*args: str) -> dict:
    code, out = run(*args, "--json")
    start = out.find("{")
    payload = json.loads(out[start:]) if start >= 0 else {}
    payload["_exit"] = code
    payload["_raw"] = out
    return payload


def rules_of(rep: dict, rule: str, file: str | None = None) -> list[dict]:
    return [f for f in rep["findings"] if f["rule"] == rule
            and (file is None or Path(str(f["file"])).name == file)]


def main() -> int:
    # 1) the intentionally messy layering must light up all four error rules
    dirty = report(FIX / "dirty")
    check("dirty: all 4 error rules fire",
          all(rules_of(dirty, r) for r in ("UPWARD_DEPENDENCY", "LAYER_CYCLE",
                                           "DOMAIN_FRAMEWORK_IMPORT", "BOUNDARY_LEAK")),
          str(sorted({f['rule'] for f in dirty['findings']})))
    check("dirty: exit 1 with --fail-on error", dirty["_exit"] == 1, f"exit={dirty['_exit']}")
    check("dirty: 6 error findings", dirty["counts"]["error"] == 6, str(dirty["counts"]))
    check("dirty: score in the D band", 55 <= dirty["score"] < 70, f"score={dirty['score']}")
    upward = rules_of(dirty, "UPWARD_DEPENDENCY", "order.py")
    check("dirty: UPWARD points at the import line, not the file top",
          bool(upward) and upward[0]["line"] == 3, str(upward[:1]))
    leak = rules_of(dirty, "BOUNDARY_LEAK")
    check("dirty: BOUNDARY_LEAK names the private module it reached into",
          bool(leak) and "internal.ts" in leak[0]["message"], str(leak[:1]))
    ring = rules_of(dirty, "LAYER_CYCLE")
    check("dirty: LAYER_CYCLE covers the whole 4-layer ring",
          bool(ring) and len(str(ring[0]["value"]).split("+")) == 4, str(ring[:1]))
    check("dirty: every error finding carries a fix hint",
          all(f["hint"] for f in dirty["findings"]), "")

    # 2) the tidy layering must be silent — the anti-false-positive guarantee
    clean = report(FIX / "clean")
    check("clean: 0 findings", not clean["findings"], str(clean["findings"][:2]))
    check("clean: score 100 / grade A", (clean["score"], clean["grade"]) == (100.0, "A"),
          f"{clean['score']}/{clean['grade']}")
    check("clean: exit 0 with --fail-on error", clean["_exit"] == 0, f"exit={clean['_exit']}")
    check("clean: vertical slices are counted, not reported as drift",
          len(clean["slices"]) == 2 and not rules_of(clean, "UNCLASSIFIED_FILES"),
          str(clean["slices"]))
    check("clean: dependency matrix shows the inward edges",
          clean["edges"].get("application->domain") == 2, str(clean["edges"]))

    # 3) dotted / module-path imports (Java, Go) work through rootPackages
    java = report(FIX / "java")
    check("java: framework + upward + cycle detected across com.example packages",
          all(rules_of(java, r) for r in ("DOMAIN_FRAMEWORK_IMPORT", "UPWARD_DEPENDENCY",
                                           "LAYER_CYCLE")), str(sorted({f['rule'] for f in java['findings']})))
    go = report(FIX / "go")
    check("go: import block parsed (framework + upward + cycle)",
          all(rules_of(go, r) for r in ("DOMAIN_FRAMEWORK_IMPORT", "UPWARD_DEPENDENCY",
                                        "LAYER_CYCLE")), str(sorted({f['rule'] for f in go['findings']})))

    # 4) exception mechanism, same shape as cc-scan:allow
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "domain").mkdir()
        (root / "infrastructure").mkdir()
        (root / "infrastructure" / "db.py").write_text("class Repo:\n    pass\n", encoding="utf-8")
        (root / "domain" / "order.py").write_text(
            "from .money import Money\n"
            "# arch-scan:allow UPWARD_DEPENDENCY — temporary, tracked in ARCH-142\n"
            "from ..infrastructure.db import Repo\n"
            "LEGACY = Repo()\n", encoding="utf-8")
        (root / "domain" / "money.py").write_text("class Money:\n    pass\n", encoding="utf-8")
        (root / "domain" / "report.py").write_text(
            "from ..infrastructure.db import Repo\n\nITEM = Repo()\n", encoding="utf-8")
        allowed = report(root)
        check("allow: comment on the line above silences just that import",
              not rules_of(allowed, "UPWARD_DEPENDENCY", "order.py")
              and rules_of(allowed, "UPWARD_DEPENDENCY", "report.py"),
              str([(f['file'], f['line']) for f in rules_of(allowed, 'UPWARD_DEPENDENCY')]))

        (root / "domain" / "order.py").write_text(
            "from .money import Money\n"
            "# arch-scan:allow DOMAIN_FRAMEWORK_IMPORT — not the rule we broke\n"
            "from ..infrastructure.db import Repo\n"
            "LEGACY = Repo()\n", encoding="utf-8")
        wrong_rule = report(root)
        check("allow: only the named rule is silenced",
              bool(rules_of(wrong_rule, "UPWARD_DEPENDENCY", "order.py")),
              str([(f['file'], f['line']) for f in wrong_rule['findings']]))

        (root / "arch-scan.config.json").write_text(json.dumps({"layers": [
            {"name": "domain", "rank": 0, "include": ["**/domain/**"]},
            {"name": "infrastructure", "rank": 2, "include": ["**/infrastructure/**"]},
            {"name": "interface", "rank": 3, "include": ["**/interface/**"]}]}, indent=2),
            encoding="utf-8")
        drift = report(root)
        check("drift: LAYER_UNUSED fires only for the declared-but-empty layer",
              {f["value"] for f in rules_of(drift, "LAYER_UNUSED")} == {"interface"},
              str([f["value"] for f in rules_of(drift, "LAYER_UNUSED")]))
        check("drift: UNCLASSIFIED_FILES absent once the config matches the tree",
              not rules_of(drift, "UNCLASSIFIED_FILES"), "")

        (root / "arch-scan.config.json").write_text("{ not json", encoding="utf-8")
        code, out = run(root)
        check("config: broken JSON warns and falls back to defaults",
              "not valid JSON" in out and code in (0, 1), out[:160])

    # 5) CLI surface
    listing = run("--list-rules")[1]
    check("cli: --list-rules prints every rule",
          all(rule in listing for rule in
              ("UPWARD_DEPENDENCY", "LAYER_CYCLE", "DOMAIN_FRAMEWORK_IMPORT", "BOUNDARY_LEAK",
               "UNCLASSIFIED_FILES", "LAYER_UNUSED")), "")
    check("cli: --explain prints prose",
          len(run("--explain", "upward_dependency")[1]) > 120, "")
    check("cli: --explain on unknown rule exits 2", run("--explain", "NOPE")[0] == 2, "")
    code_missing, out_missing = run("does/not/exist")
    check("cli: missing path -> exit 2 + 'not found'",
          code_missing == 2 and "not found" in out_missing, f"exit={code_missing}")
    check("cli: --version prints a semver",
          run("--version")[1].startswith("arch-scan 1."), run("--version")[1])
    keys = {"tool", "version", "root", "filesScanned", "score", "grade", "counts",
            "layers", "slices", "edges", "findings", "config"}
    check("cli: --json carries the documented schema", keys <= set(clean), str(keys - set(clean)))
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "arch.json"
        run(FIX / "dirty", "-o", target)
        saved = json.loads(target.read_text())
        check("cli: -o writes a report identical to --json",
              saved["score"] == dirty["score"] and len(saved["findings"]) == 6,
              f"{saved.get('score')}")
        text_out = run(FIX / "clean")[1]
        check("cli: text report prints census + matrix",
              "Layer census" in text_out and "Layer dependencies" in text_out, text_out[:120])

    # 6) an unknown layout must be reported as drift, never silently approved
    with tempfile.TemporaryDirectory() as tmp:
        flat = Path(tmp) / "legacy"
        (flat / "app").mkdir(parents=True)
        (flat / "app" / "orders.py").write_text("def total(items):\n    return sum(items)\n",
                                                encoding="utf-8")
        (flat / "app" / "mail.py").write_text("def send(to):\n    return to\n", encoding="utf-8")
        (flat / "app" / "mail.py").write_text("def send(to):\n    return to\n", encoding="utf-8")
        flat_rep = report(flat, "--fail-on", "none")
        check("dogfood: a repo with no layering is reported, not approved",
              bool(rules_of(flat_rep, "UNCLASSIFIED_FILES")) and flat_rep["score"] < 100,
              f"score={flat_rep['score']} rules={[f['rule'] for f in flat_rep['findings']]}")

    # 7) findings carry both a machine key and a human hint
    first = dirty["findings"][0]
    check("schema: value is a short key, hint is prose",
          len(str(first["value"])) < 60 and len(first["hint"]) > 40,
          f"value={first['value']!r} hint={first['hint'][:40]!r}")

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    width = max(len(name) for name, _, _ in RESULTS)
    for name, ok, detail in RESULTS:
        line = f"{'PASS' if ok else 'FAIL'}  {name}"
        if not ok and detail:
            line += f"\n        -> {detail}"
        print(line.ljust(width + 8) if ok else line)
    print(f"\n{passed}/{len(RESULTS)} arch checks passed")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
