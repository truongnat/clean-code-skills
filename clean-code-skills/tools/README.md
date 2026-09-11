# tools — the two scanners and how to run them

| Script | Question it answers | Rules | Deps |
|---|---|---|---|
| `cc-scan.py` | is each **module** built to standard? | 20 | Python 3.9+ stdlib |
| `arch-scan.py` | does the **system** respect its declared layers? | 6 | Python 3.9+ stdlib |
| `check_links.py` | do the pack's own cross-references resolve? | — | stdlib |

Both are heuristic on purpose: regex + counting, no parser, no install, no network. That is what
lets them run in a pre-commit hook in 0.2 s and on a machine where nothing is installed. They are
**signals for a reviewer**, not verdicts — see §5 for what they miss.

```bash
python3 cc-scan.py . --fail-on error            # gate CI on errors only
python3 cc-scan.py src --json -o cc.json        # machine-readable report
python3 arch-scan.py src --fail-on error        # dependency direction gate
python3 tests/run_checks.py                     # 60/60 — the suites run on real fixtures
python3 tests/run_arch_checks.py                # 30/30
python3 check_links.py                          # every doc reference resolves
```

## 1. `cc-scan.py` — 20 rules

| Rule | Level | What it catches |
|---|---|---|
| `LONG_FUNCTION` | warn | function over `maxFunctionLines` (40) |
| `HUGE_FUNCTION` | error | over `hardFunctionLines` (70) — must be split |
| `TOO_MANY_PARAMS` | warn | more than `maxParams` (3) |
| `HARD_PARAMS` | error | more than `hardParams` (5) |
| `BOOLEAN_PARAM` | info | `fn(x, isTest)` — two functions in one |
| `COMPLEXITY` | warn | branch count above `maxComplexity` (10) |
| `HARD_COMPLEXITY` | error | branch count above `hardComplexity` (15) |
| `DEEP_NESTING` | warn | control flow deeper than `maxNesting` (3) |
| `MAGIC_NUMBER` | warn | numeric literal inside logic (allow-list below) |
| `LINE_TOO_LONG` | warn | line longer than `maxLineLength` (120) |
| `MIXED_INDENT` | warn | tabs and spaces in the same file |
| `TRAILING_WHITESPACE` | info | whitespace at end of line |
| `COMMENTED_CODE` | warn | commented-out code kept "for reference" |
| `BLOCK_COMMENT` | info | long comment block that belongs in docs |
| `TODO_MARK` | info | `TODO`/`FIXME`/`XXX`/`HACK` without a ticket ID |
| `EMPTY_CATCH` | error | `catch {}` / `except: pass` |
| `DEBUG_STATEMENT` | warn | `console.log`, `print(`, `System.out`, `fmt.Print` |
| `NEGATIVE_CONDITIONAL` | info | `if (!a && !b)`, `!isNotValid` |
| `DUPLICATE_BLOCK` | warn | ≥ `dupMinLines` (8) identical lines in ≥ 2 places |
| `LOW_TEST_RATIO` | info | test-file/source-file ratio under `minTestRatio` (0.15) |

**Score**: `100 - (4*errors + 1*warning + 0.25*info)`, clamped to 0..100.
Grades: A ≥ 90, B ≥ 80, C ≥ 70, D ≥ 55, else E. Languages understood: TS/JS/JSX/TSX, Python,
Java, Kotlin, Scala, C, C++, C#, Go, Rust, PHP, Swift, Ruby.

Measured on this pack (from the repo root):

```
tools/demo/src/legacy-order-service.ts + legacy-renderer.ts   -> 72.0/100 (4 error, 11 warn, 4 info)
tools/demo/src/order-service.ts + order-service.test.ts       -> 100.0/100 (0 findings)
```

## 2. `arch-scan.py` — 6 rules

Layers are declared with a `rank`; **rank 0 is innermost** (the domain). A file may import layers of
rank ≤ its own, never outward. That single rule is what the tool checks.

| Rule | Level | What it catches |
|---|---|---|
| `UPWARD_DEPENDENCY` | error | `domain` importing `infrastructure` (or any inner→outer edge) |
| `LAYER_CYCLE` | error | layers importing each other in a ring — nothing in the ring is testable alone |
| `DOMAIN_FRAMEWORK_IMPORT` | error | a driver/ORM/web-framework import inside a layer listed in `frameworkPackages` |
| `BOUNDARY_LEAK` | error | `features/a` importing `features/b/<internals>` instead of its published API |
| `UNCLASSIFIED_FILES` | info | more than `maxUnclassifiedPct` of code files match no layer (the config drifted) |
| `LAYER_UNUSED` | info | a declared layer matches nothing |

**Score**: `100 - (6*errors + 1*info)`. Output also prints a **layer census** (files per layer and per
vertical slice) and the **dependency matrix** (`application → domain: 3 import(s)`, `x` marking the
illegal edges) — that matrix is usually the most useful slide in an architecture review.

It understands: Python (`import`/`from`, including `from ..x import y`), JS/TS (`from`, `import()`,
`require()`), Java/Kotlin (`import a.b.C;`), Go (single-line and `import ( … )` blocks). Dotted
imports are treated as internal when they match a `rootPackages` prefix — or, if you have not
configured that yet, when the dotted name is a real folder inside the scanned tree.

Verified here: `tools/tests/run_arch_checks.py` (30 assertions, dirty fixture lights up all four
error rules, clean fixture returns 100.0/100 with zero findings) and the same code shape checked by
import-linter and ArchUnit in `configs/architecture/demo/` (they agree).

## 3. Configuration

`cc-scan.config.json` … the file is named **`clean-code.config.json`** (alt `.clean-code.json`);
`arch-scan.config.json` (alt `architecture.config.json`). Looked up in the directory you scan —
one config per invocation, and a config in a *sub*folder is not picked up by accident.

```json
{
  "maxLineLength": 120, "maxFunctionLines": 40, "hardFunctionLines": 70,
  "maxParams": 3, "hardParams": 5, "maxNesting": 3,
  "maxComplexity": 10, "hardComplexity": 15,
  "magicNumbersAllowed": ["0", "1", "-1", "2"],
  "dupMinLines": 8, "minTestRatio": 0.15,
  "ignoreDirs": ["fixtures", "demo"],
  "ignoreGlobs": ["*.generated.*"],
  "skipRules": [],
  "skipRulesForTests": ["MAGIC_NUMBER", "LONG_FUNCTION", "DEBUG_STATEMENT", "LINE_TOO_LONG"]
}
```

Semantics worth knowing, because they are the two ways people get bitten:

- **`ignoreDirs` extends, never replaces.** `node_modules`, `.git`, `__pycache__`, `.venv` are a
  floor (`ALWAYS_IGNORE_DIRS`) no config can lift; to actually scan one, pass it as the path.
- **CLI flags** `--max-line/--max-fn-lines/--max-params/--max-nesting` override the file;
  `--no-dup` turns duplicate detection off; `--no-baseline` ignores the freeze file.
- `tools/clean-code.config.json` in this pack is a worked example of **documented exceptions**:
  `skipRules: ["DEBUG_STATEMENT","MAGIC_NUMBER"]` because `cc-scan.py` is a single-file CLI whose
  output is `print()` and whose threshold table must be literals. Same file for `arch-scan`:
  `configs/architecture/arch-scan.config.json`.

## 4. Exceptions that stay visible

```ts
// cc-scan:allow-file LONG_FUNCTION — state machine loop, see docs/adr/0012
const timeoutMs = 1500; // cc-scan:allow MAGIC_NUMBER — demo, delete in AC-1240
```

```python
# arch-scan:allow UPWARD_DEPENDENCY — temporary while the legacy repository is split, ARCH-142
from app.infrastructure.db import Repo
```

`allow` covers **its own line and the line right after**, only for the **rules named**, and does not
spread through the rest of the function. `allow-file` must appear in the first 30 lines and takes a
comma-separated list. There is no `disable-all`: to quiet a whole repo, use `skipRules` in config,
so the decision shows up in `git log` with a reason.

To inherit a legacy codebase without freezing progress:

```bash
python3 cc-scan.py . --update-baseline      # commits .clean-code-baseline.json — the old debt, accepted
python3 cc-scan.py . --fail-on error        # from now on: only NEW findings break the build
```

Commit the baseline file. It is the record of what the team chose not to fix today.

## 5. Known limits (also why Sonar still has a job)

- **No parser.** Decorators, macros, generated code and unusual formatting can shift a boundary. A
  function's start line is where its declaration is, so the finding is easy to find but not a
  language-lawyer measurement.
- **Duplicate detection is exact-line, not fuzzy**: renamed variables inside a copy defeat it.
  Sonar/`jscpd` catch those; `DUPLICATE_BLOCK` catches the lazy copy-paste.
- **Complexity is branch counting**, not cyclomatic-per-method as tools like `gocognit` compute.
  Use the language-native metric in the linter when you need the precise number.
- **`arch-scan` follows import statements only**: reflection, DI containers, string module paths and
  runtime `require`s are invisible to it. It reports the file's own layer by path pattern, so a
  folder layout that lies about its contents makes it lie too.
- **No diff awareness.** It reports the whole tree; combine with the baseline for "new code only".
- Both tools count **files** for the test ratio, not test *coverage* — coverage belongs to
  `coverage-diff`/Sonar (`configs/ci/sonar-project.properties`).

`SELF_REVIEW.md` lists the debt the tools carry themselves, with numbers.

## 6. Fixtures and tests

```
tests/
├── run_checks.py          # 60 assertions: rule coverage, false positives, baseline, config, CLI
├── run_arch_checks.py     # 30 assertions: 4 error rules, clean = 100, Java/Go imports, allow, drift
└── fixtures/
    ├── messy/             # 7 files that must trigger all 20 cc-scan rules (exit 1)
    ├── clean/             # 5 files that must trigger none (exit 0)  <- anti-false-positive proof
    └── layers/{dirty,clean,java,go}/   # arch fixtures; `clean` is a correct layered app
```

Tests run the real binaries on real files: no mocks, no re-implemented logic. If you change a rule,
add or adjust a fixture, then run both suites — a rule that no fixture triggers is a rule nobody
trusts.
