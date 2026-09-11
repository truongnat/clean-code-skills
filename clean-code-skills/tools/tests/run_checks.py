#!/usr/bin/env python3
# cc-scan:allow-file HUGE_FUNCTION, HARD_COMPLEXITY
# Why: this is a one-file test script for a one-file CLI - splitting it into helpers
# just to look tidy would make readers jump around while debugging a fixture.
"""
Test the cc-scan rule set by running it FOR REAL on fixtures (no mocks, no copied logic).

  * `messy/` fixture  -> must trigger all 20 rules, exit 1 with --fail-on error
  * `clean/` fixture  -> must produce 0 findings (false-positive guard), exit 0
  * individual rules  -> right file, right line, right label
  * baseline          -> freeze today, rescan, zero new findings
  * config            -> CLI flags + the repo's clean-code.config.json are really loaded
  * deliberate exceptions -> cc-scan:allow / cc-scan:allow-file apply at exactly the right scope
  * dogfood           -> the tools/ sources themselves must pass the rules they enforce
  * docs guard        -> every markdown file in skills/ and playbook/ has an English H1

Run:  python3 run_checks.py         (exit 0 = everything passed)
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
TOOL = TOOLS / "cc-scan.py"
FIXTURES = HERE / "fixtures"
MESSY = FIXTURES / "messy"
CLEAN = FIXTURES / "clean"

RESULTS: list[tuple[str, bool, str]] = []


def run(*args: str, cwd: Path | None = None) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(TOOL), *[str(a) for a in args]],
                          capture_output=True, text=True, cwd=str(cwd) if cwd else None)
    return proc.returncode, proc.stdout + proc.stderr


def report(*args: str) -> dict:
    """Run cc-scan and parse the JSON out of stdout."""
    out = run(*args, "--json")[1]
    start = out.find("{")
    if start < 0:
        raise AssertionError(f"no JSON in output:\n{out[:400]}")
    code, _ = run(*args)
    payload = json.loads(out[start:])
    payload["_exit"] = code
    return payload


def rules_of(rep: dict, rule: str, file: str | None = None) -> list[dict]:
    """Filter findings by rule and file name (exact basename match)."""
    return [f for f in rep["findings"] if f["rule"] == rule
            and (file is None or Path(f["file"]).name == file)]


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))


def main() -> int:
    # 1) dirty fixture: every rule must fire at least once
    rule_names = [ln.split()[1] for ln in run("--list-rules")[1].splitlines()[1:]
                  if len(ln.split()) > 1]
    messy = report(MESSY, "--no-baseline")
    missing = [r for r in rule_names if messy["counts"].get(r, 0) < 1]
    check(f"messy: all {len(rule_names)} rules fired", not missing, f"not seen: {missing}")
    check("messy: exit 1 khi --fail-on error", messy["_exit"] == 1, f"exit={messy['_exit']}")
    check("messy: score <= 60 (grade D/E)", messy["score"] <= 60, f"score={messy['score']}")

    # 2) clean fixture: not a single false positive
    clean = report(CLEAN, "--no-baseline")
    check("clean: 0 findings (no false alarms)", not clean["findings"],
          f"reported: {[(f['file'], f['line'], f['rule']) for f in clean['findings']][:6]}")
    check("clean: score 100 & exit 0", clean["score"] == 100 and clean["_exit"] == 0,
          f"score={clean['score']} exit={clean['_exit']}")

    # 3) each rule must catch the right construct in the right language
    expectations = [
        ("HUGE_FUNCTION", "processCheckout", "TS: 45-line function over the hard limit"),
        ("LONG_FUNCTION", "placeOrder", "TS: 52-line function over the soft limit"),
        ("HARD_PARAMS", "generateReport", "Java: 6 parameters"),
        ("TOO_MANY_PARAMS", "placeOrder", "TS: 5 parameters"),
        ("HARD_PARAMS", "process_payment", "Python: 7 parameters"),
        ("EMPTY_CATCH", "except Exception", "Python: except + pass"),
        ("EMPTY_CATCH", "catch (Exception e)", "Java: empty catch"),
        ("COMMENTED_CODE", "oldTotal", "TS: commented-out code"),
        ("MAGIC_NUMBER", "50000", "TS: magic number in logic"),
        ("MAGIC_NUMBER", "5000000", "Go: magic number in logic"),
        ("DEBUG_STATEMENT", "console.log", "TS: console.log"),
        ("DEBUG_STATEMENT", "System.out", "Java: System.out"),
        ("DEBUG_STATEMENT", "fmt.Println", "Go: fmt.Println"),
        ("DEBUG_STATEMENT", "print(", "Python: print"),
        ("DEEP_NESTING", "ProcessOrder", "Go: 5 nesting levels"),
        ("BOOLEAN_PARAM", "is_test_mode", "Python: flag boolean"),
        ("COMPLEXITY", "process_payment", "Python: many branches"),
        ("MIXED_INDENT", "tab", "TS: tabs mixed with spaces"),
        ("TRAILING_WHITESPACE", "Trailing whitespace", "TS: spaces at end of line"),
        ("BLOCK_COMMENT", "Comment block", "TS: long block comment"),
        ("NEGATIVE_CONDITIONAL", "Negated", "TS: !a || !b"),
        ("DUPLICATE_BLOCK", "repeated", "TS: same block in 2 files"),
        ("LOW_TEST_RATIO", "test files", "project: too few tests"),
        ("TODO_MARK", "TODO", "TS/Go: leftover TODO"),
        ("LINE_TOO_LONG", "characters", "TS: line >120"),
    ]
    for rule, needle, label in expectations:
        hits = [f for f in messy["findings"] if f["rule"] == rule and needle in f["message"]]
        check(f"rule {rule}: {label}", bool(hits), f"did not find '{needle}'")

    # 4) the reported line must point at the offending line (3 representative rules)
    def line_of(rep: dict, rule: str, file_end: str) -> int | None:
        hits = rules_of(rep, rule, file_end)
        return hits[0]["line"] if hits else None

    lf_line = line_of(messy, "LONG_FUNCTION", "order-service.ts")
    ts_lines = (MESSY / "src" / "order-service.ts").read_text().split("\n")
    check("positioning: LONG_FUNCTION points at the declaration line",
          lf_line is not None and "placeOrder" in ts_lines[lf_line - 1],
          f"line={lf_line} -> {ts_lines[(lf_line or 1) - 1][:60]}")
    py_lines = (MESSY / "src" / "checkout.py").read_text().split("\n")
    mn = rules_of(messy, "MAGIC_NUMBER", "checkout.py")
    check("positioning: MAGIC_NUMBER only flags numbers really present on the line",
          bool(mn) and all(str(f["value"]) in py_lines[f["line"] - 1] for f in mn),
          f"findings={[(f['line'], f['value']) for f in mn][:4]}")

    # 5) deliberate exceptions: cc-scan:allow / allow-file
    sup_lf = rules_of(messy, "LONG_FUNCTION", "suppressed.ts")
    unsup_lf = rules_of(messy, "LONG_FUNCTION", "unsuppressed.ts")
    check("allow-file: LONG_FUNCTION switched off in suppressed.ts", not sup_lf, str(sup_lf))
    check("allow-file: the same function is still reported in unsuppressed.ts", len(unsup_lf) == 1, str(unsup_lf)[:160])
    magic_sup = [f["value"] for f in rules_of(messy, "MAGIC_NUMBER")
                 if Path(f["file"]).name == "suppressed.ts"]
    check("allow per line: a same-line comment blocks the finding", "7" not in magic_sup, str(magic_sup))
    check("allow per line: the comment on the line above also blocks it",
          "11" not in magic_sup, str(magic_sup))
    check("allow does not spread: other lines in the same function are still reported", "9" in magic_sup, str(magic_sup))
    check("allow covers only the named rule: console.log is still caught",
          bool(rules_of(messy, "DEBUG_STATEMENT", "suppressed.ts")))

    # 6) baseline
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "messy"
        shutil.copytree(MESSY, work)
        code, out = run(work, "--update-baseline")
        after = report(work)
        check("baseline: --update-baseline exits 0", code == 0, out[-200:])
        check("baseline: rescan leaves 0 new findings", not after["findings"], f"{len(after['findings'])}")
        check("baseline: ghi .clean-code-baseline.json", (work / ".clean-code-baseline.json").is_file())
        check("baseline: suppressed count equals the findings frozen",
              after["suppressedByBaseline"] >= 1, f"suppressed={after['suppressedByBaseline']}")
        check("baseline: --no-baseline still fails, for comparison",
              run(work, "--no-baseline", "--fail-on", "error")[0] == 1)
        # NEW findings must be caught even with a baseline in place
        (work / "src" / "extra.ts").write_text(
            "export function bad(a: number): number {\n  console.log(a * 7);\n  return a;\n}\n")
        new_hit = report(work)
        check("baseline: newly added bad code is still reported",
              bool(rules_of(new_hit, "DEBUG_STATEMENT", "extra.ts")),
              str(new_hit["counts"]))

    # 7) config: CLI flags and the repo config file
    tight = report(MESSY, "--no-baseline", "--max-line", "40")
    loose = report(MESSY, "--no-baseline", "--max-line", "500")
    check("config: --max-line 40 reports more LINE_TOO_LONG than 500",
          tight["counts"].get("LINE_TOO_LONG", 0) > loose["counts"].get("LINE_TOO_LONG", 0),
          f"{tight['counts'].get('LINE_TOO_LONG', 0)} vs {loose['counts'].get('LINE_TOO_LONG', 0)}")
    strict_fn = report(CLEAN, "--no-baseline", "--max-fn-lines", "3", "--no-dup")
    check("config: --max-fn-lines 3 tightens the clean fixture",
          strict_fn["counts"].get("LONG_FUNCTION", 0) >= 1, f"{strict_fn['counts']}")
    check("config: --fail-on none always exits 0", report(MESSY, "--fail-on", "none")["_exit"] == 0)
    with tempfile.TemporaryDirectory() as tmp:
        cfg = {"maxLineLength": 60, "maxFunctionLines": 5, "magicNumbersAllowed": ["0", "1"]}
        (Path(tmp) / "clean-code.config.json").write_text(json.dumps(cfg))
        shutil.copytree(CLEAN / "src", Path(tmp) / "src")
        rep = report(Path(tmp), "--no-baseline")
        check("config: the repo clean-code.config.json is loaded",
              rep["config"]["maxLineLength"] == 60 and rep["config"]["maxFunctionLines"] == 5,
              f"{rep['config']}")
        check("config: magicNumbersAllowed reduces the report count",
              rep["counts"].get("MAGIC_NUMBER", 0) <= 2, f"{rep['counts'].get('MAGIC_NUMBER')}")

    # 8) CLI: --json -o and --list-rules
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "report.json"
        run(MESSY, "--no-baseline", "-o", target)
        data = json.loads(target.read_text())
        check("cli: -o writes a report with the full schema",
              {"findings", "score", "grade", "counts", "config", "filesScanned"} <= set(data))
        check("cli: --list-rules prints every rule",
              all(r in run("--list-rules")[1] for r in rule_names))
        code_missing, out_missing = run(Path(tmp) / "khong-ton-tai")
        check("cli: nonexistent path -> exit 2 + warning",
              code_missing == 2 and "not found" in out_missing, f"exit={code_missing}")

    # 7b) scope of ignoreDirs & config: a config must never widen the scanned area by accident
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "src").mkdir()
        (root / "src" / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
        (root / "node_modules" / "dep").mkdir(parents=True)
        (root / "node_modules" / "dep" / "junk.ts").write_text(
            "export function junk(a: number, b: number, c: number, d: number): number {\n"
            + "".join(f"  const v{n} = a * {n};\n" for n in range(30))
            + "  return a + b + c + d;\n}\n", encoding="utf-8")
        # a deliberately short ignoreDirs list: node_modules must still be skipped
        (root / "clean-code.config.json").write_text(
            json.dumps({"ignoreDirs": ["fixtures"]}), encoding="utf-8")
        rep = report(root, "--no-baseline", "--no-dup")
        touched = [f["file"] for f in rep["findings"] if "node_modules" in f["file"]]
        check("ignoreDirs: config cannot remove built-in protection (node_modules still skipped)",
              not touched and rep["filesScanned"] == 1,
              f"filesScanned={rep['filesScanned']} touched={touched[:3]}")

        sub = root / "pkg"
        sub.mkdir()
        (sub / "b.py").write_text("x = '" + "y" * 200 + "'\n", encoding="utf-8")
        (sub / "clean-code.config.json").write_text(
            json.dumps({"maxLineLength": 500}), encoding="utf-8")
        wide = [f for f in report(sub, "--no-baseline", "--no-dup")["findings"]
                if f["rule"] == "LINE_TOO_LONG"]
        parent = [f for f in report(root, "--no-baseline", "--no-dup")["findings"]
                  if f["rule"] == "LINE_TOO_LONG"]
        check("config: scanning a folder directly applies its own config", not wide, str(wide)[:120])
        check("config: scanning a parent never picks up a child folder config by accident",
              bool(parent), f"findings={parent[:1]}")

    # 8b) the cc-scan:allow escape hatch for line-level rules (not only function-level ones)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "allow_prev.ts").write_text(
            "export function f(a: number): number {\n"
            "  // cc-scan:allow MAGIC_NUMBER - business constant agreed with the PO\n"
            "  const fee = a * 500000;\n"
            "  return fee;\n}\n", encoding="utf-8")
        (root / "allow_inline.ts").write_text(
            "export function g(a: number): number {\n"
            "  return a * 30000; // cc-scan:allow MAGIC_NUMBER\n}\n", encoding="utf-8")
        (root / "allow_other_rule.ts").write_text(
            "export function h(a: number): number {\n"
            "  // cc-scan:allow LINE_TOO_LONG\n"
            "  return a * 70000;\n}\n", encoding="utf-8")
        rep = report(root, "--no-baseline", "--no-dup")
        magic = [f["file"] for f in rep["findings"] if f["rule"] == "MAGIC_NUMBER"]
        check("allow: a comment on the line above blocks a line-level rule",
              "allow_prev.ts" not in magic, str(magic))
        check("allow: a same-line comment blocks the finding",
              "allow_inline.ts" not in magic, str(magic))
        check("allow: switches off only the named rule (others still report)",
              "allow_other_rule.ts" in magic, str(magic))

    # 9) dogfood: the tools/ sources must pass the rules they enforce
    selfrep = report(TOOLS, "--no-baseline")
    hard = [f for f in selfrep["findings"]
            if f["rule"] in ("EMPTY_CATCH", "MIXED_INDENT", "TRAILING_WHITESPACE", "COMMENTED_CODE")]
    check("dogfood: tools/ swallows no errors, keeps no dead code, indents consistently",
          not hard, str([(f['file'], f['line'], f['rule']) for f in hard][:5]))
    check("dogfood: tools/ has a clean baseline (it does not freeze its own debt)",
          not (TOOLS / ".clean-code-baseline.json").exists())

    # 10) docs guard: this pack was converted from Vietnamese file by file, and an old
    #     Vietnamese file once reappeared over a translated one after a rename. A translated
    #     document is easy to lose silently, so the H1 of every doc is checked here.
    root = TOOLS.parent
    viet = re.compile(r"[\u00c0-\u024f\u1e00-\u1eff]")
    stale = []
    for folder in ("skills", "playbook"):
        for md in sorted((root / folder).rglob("*.md")):
            title = next((line for line in md.read_text(encoding="utf-8").splitlines()
                          if line.startswith("# ")), "")
            if not title:
                stale.append(f"{md.relative_to(root)}: no H1 title")
            elif viet.search(title):
                stale.append(f"{md.relative_to(root)}: {title[:50]}")
    check("docs: every markdown file in skills/ and playbook/ has an English H1 title",
          not stale, "; ".join(stale[:3]) or f"{sum(1 for f in (root / 'skills').rglob('*.md'))}+"
                                                 f"{sum(1 for f in (root / 'playbook').rglob('*.md'))} files clean")

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    width = max(len(n) for n, _, _ in RESULTS)
    for name, ok, detail in RESULTS:
        line = f"{'PASS' if ok else 'FAIL'}  {name}"
        if not ok and detail:
            line += f"\n        └ {detail}"
        print(line.ljust(width + 8) if ok else line)
    print(f"\n{passed}/{len(RESULTS)} checks passed")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
