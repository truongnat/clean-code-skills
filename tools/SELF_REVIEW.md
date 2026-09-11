# Self-review of `cc-scan.py` — the tool eating its own cooking

```bash
$ cd tools && python3 cc-scan.py . --no-baseline --json | jq '{score, counts}'
```

Scanning `tools/` covers 5 files: `cc-scan.py`, `arch-scan.py`, `check_links.py` and the two test
runners. The numbers below are from that run on the release date.

## What the tool **deliberately** accepts (and why)

| Violation | Count | Reason (recorded in place, and scoped) |
|---|---|---|
| `HUGE_FUNCTION` (`scan_file` 202 lines, `main` 130, `split_line` 79, `find_functions` 79, and `arch-scan`'s `scan_tree` 81) | 5 | `cc-scan.py` is deliberately **one single file with zero dependencies**, so copying it into any repo is enough to run it. Splitting `scan_file` across 6 modules would destroy that property. |
| `HARD_COMPLEXITY` | 12 | Each of these functions is a sequential parser (a state machine). Split them and you jump between 8 files to debug one parse bug. |
| `DEEP_NESTING` | 32 | `find_empty_catch` nests 8 deep, `scan_file` 11 — sequential parsing again; inverting the conditions breaks the "one line = one step" reading order. |
| `MAGIC_NUMBER` | 55 (42 of them in `cc-scan.py`) | The `DEFAULTS` table (120/40/3/10) **must** sit in the code so the tool needs no config file. Switched off at the `tools/` level through `skipRules` plus the reason in `clean-code.config.json`. |
| `DEBUG_STATEMENT` (`print(`) | 46 (20 in `cc-scan.py`) | These are CLIs — printing to stdout is **the feature**, not litter. Also in `skipRules`. |
| `TOO_MANY_PARAMS` / `LONG_FUNCTION` / `COMPLEXITY` | 4 / 3 / 6 | Internal functions threading `(path, root, cfg, is_test)` — collapsible into a `ScanCtx` if the tool grows more rules. |
| `HARD_PARAMS` (`arch-scan._finding`, 6 params) | 1 | A finding constructor with positional fields; a record type is the fix, and it is on the debt list below rather than pretended away. |
| `BOOLEAN_PARAM` (`scan_file(..., is_test)`) | 1 | Splitting it into two functions duplicates the body; the trade is not worth it yet. |

Today's measurements (runnable, so you can re-check them):

```bash
$ cd tools && python3 cc-scan.py . --no-baseline
Clean Code score: 0.0/100 (grade E)  · error=18 warning=46 info=2   # tools/ uses clean-code.config.json
$ python3 cc-scan.py cc-scan.py --no-baseline
Clean Code score: 35.8/100 (grade E)  · error=11 warning=20 info=1  # cc-scan.py on its own
$ # measured raw against DEFAULTS (MAGIC_NUMBER + DEBUG_STATEMENT back on): 0.0/100 (grade E)
```

The tool grades itself **E** and does not argue its way out by switching rules off: a low score is
good news — it points at exactly where the debt is (the "remaining debt" table below).

The rule it applies to itself: an exception must be (1) **explicit** in a config file, (2) carry a
**reason**, (3) be **scoped** (the `tools/` directory, never the code you write), and (4) be
**re-measurable** when you tighten it.

## What the tool does **not** let itself off (and has verified)

| Rule | Result across `tools/` |
|---|---|
| `EMPTY_CATCH` | 0 — every `except OSError` either `continue`s or returns a deliberate value; every `try` does something |
| `COMMENTED_CODE` | 0 — no commented-out code (I had to rewrite 3 regex comments because the tool correctly caught the `if (!a && !b)` example I had left inside one) |
| `MIXED_INDENT` / `TRAILING_WHITESPACE` | 0 |
| `TODO_MARK` | 0 — no technical debt hidden in the source |
| `LOW_TEST_RATIO` | 0 — `tests/run_checks.py`, `tests/run_arch_checks.py` and the fixtures |

## What I learned letting the tool read itself (worth putting in the playbook)

1. **A false positive is a real cost.** The first version of `COMMENTED_CODE` flagged
   `import java.util.List;` (because I checked the whole line, not just the comment part) → 279
   false reports on the fixture. The fix: only examine the comment portion returned by the
   code/comment splitter.
2. Every rule **needs a "compliant" fixture**, not only a "wrong" one. `fixtures/clean/` (5 files
   across TS/Python/Java/Go) is what forced me to fix `MAGIC_NUMBER` so it spares constant
   declarations (`const VAT_RATE = 0.1`, `VAT_RATE = 0.1` in Python, `static final` in Java) —
   without that, the tool teaches people to switch it off.
3. `except Exception: print(e)` used to be reported as swallowing the error (wrong — `print` is an
   action). The filler filter is now just `pass`/`...`/`noop`; `continue` and `return` are **not**
   treated as empty any more.
4. A heuristic needs a **deliberate escape hatch** or it dies: that is why `cc-scan:allow`,
   `cc-scan:allow-file`, `skipRulesForTests` and the baseline exist — and all of them have tests in
   `run_checks.py` (61/61 checks passed).
5. A rule only earns its place if it **catches what humans get lazy about** (debug logs, empty
   catches, dead code) and **does not ask a human to do a machine's job** (layout aesthetics).

## Remaining debt (open, on purpose — not "refactor later")

| Debt | Impact | What doing it would involve |
|---|---|---|
| Functions are found by regex, not an AST | generated code and macros can shift the line count | `pip install tree-sitter` + a grammar per language; zero-dependency is gone → needs two modes (fast/exact) |
| `DUPLICATE_BLOCK` only finds **byte-identical** blocks | duplication with renamed variables slips through | normalise identifiers + an `ast` dump; roughly 10× more expensive |
| No **repo-wide duplication ratio** (% of lines) | no number to set the 3% gate against | add `--dup-ratio` |
| `COMPLEXITY` is approximate (keyword counting), not true cyclomatic | ±20% off in functions with many ternaries | the docstring already says "heuristic"; call `lizard`/`radon` in CI if you need the real number |
| `HARD_PARAMS` on `arch-scan._finding` | the tool reports its own 6-parameter constructor | turn it into a dataclass/record; XS, and worth doing the next time that file is touched |
| Does not read a PR's diff (it scans the paths you pass) | reports old findings in a file you touched | `--changed-since origin/main` using `git diff -U0` to filter by hunk |

There is no deadline on that table — **on purpose**. Every tool carries debt; the difference is
whether the debt is **declared** or buried in a `// TODO`. This skill teaches the first.

---

## `arch-scan.py` self-review (added in 1.1.0, written in English)

Measured with its own defaults over `configs/architecture/demo/python`: **82.0/100, 3 errors**
(`DOMAIN_FRAMEWORK_IMPORT`, `UPWARD_DEPENDENCY`, `LAYER_CYCLE`) — and the same 3 on the Java demo via
ArchUnit. The clean fixture scores **100.0/100 with zero findings**, which is the number that keeps
the other one honest.

| Debt `arch-scan` accepts | Where | Why it stays |
|---|---|---|
| regex over a real parser | `extract_imports`, `Layout.resolve` | stdlib-only, zero-install is the product requirement; a 1 MB `ast` fallback would break "copy one file into any repo" |
| path-based layer classification | `Layout.layer_of` | import direction *is* a path fact in every language we support; when the layout lies about its contents, the `UNCLASSIFIED_FILES` info fires instead of pretending |
| only `rootPackages`-declared internal imports | `layer_of_spec` | with the "dotted name is a folder in this repo" fallback; a config-free run still catches `app.domain → app.infrastructure`, which was the top false negative in the first draft |
| no baseline | CLI | `cc-scan` has one; duplicating the freeze file was worse than documenting the gap. Use the language-native exact checker (import-linter/ArchUnit) for per-edge waivers |

Three lessons worth putting on a team wall:

1. **A "green" scan of a repo it does not understand is a bug, not a pass.** The first version
   returned 0 findings for a flat legacy tree. Now it reports `UNCLASSIFIED_FILES` — silence must be
   earned by a config, not granted by the absence of one.
2. **Cross-checking against the exact tool is the cheapest correctness proof we have.** The Python
   demo was written to be *obviously* bad; import-linter agreed on both edges, and that agreement is
   what makes the heuristic trustworthy in languages with no exact tool available.
3. **Two rules that lived in different places had to agree.** `frameworkPackages` in
   `arch-scan.config.json` and the ESLint `no-restricted-imports` paths in `configs/js` described the
   same ban with different package lists; the first PR that passed one and failed the other is how we
   found it. One source of truth: the config file, referenced by the linter config.
