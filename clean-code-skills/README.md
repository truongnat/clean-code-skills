# Clean Code & Clean Architecture — Skill Pack

One standard, packaged in three usable forms that stay in sync:

```
clean-code-skills/
├── skills/          ① Agent Skills — so an AI (Claude Code / Cursor / Codex) applies the standard
│   ├── clean-code/                  ← main skill: SKILL.md + 14 references + checklists + templates + snippets
│   ├── clean-architecture/          ← the system-level half: layers, boundaries, pattern choice
│   ├── clean-code-review/           ← PR review by the 9 criteria, comments graded by severity
│   ├── clean-code-naming/           ← safe renames + killing magic values
│   ├── clean-code-refactoring/      ← behaviour-preserving refactoring with a safety net
│   ├── clean-code-error-handling/   ← exceptions, retry, timeout, no swallowed errors
│   └── clean-code-formatting-hooks/ ← prettier/ruff/gofmt + pre-commit + CI
├── playbook/        ② Team curriculum & policy — 12 sessions (01→12) + 2 appendices
├── prompts/         ③ Prompt pack — 14 copy-paste prompts for ChatGPT/Copilot/Cursor
├── tools/           ④ Two zero-dependency scanners + their test suites
│   ├── cc-scan.py                   ← module quality: 20 rules (functions, naming, comments, errors, dupes)
│   ├── arch-scan.py                 ← system quality: 6 rules (dependency direction, cycles, boundaries)
│   ├── check_links.py               ← proves the docs' 100+ cross-references resolve
│   ├── tests/                       ← 60 + 30 assertions run against real fixtures (no mocks)
│   └── demo/                        ← one business feature: legacy (72/100) vs refactored (100/100)
└── configs/         ⑤ Working configs: JS/TS · Python · Java · Go · CI · Sonar · hooks · architecture
```

Three layers, one standard: **machines enforce what is measurable** (`tools/`, `configs/`) →
**AI applies the standard while writing** (`skills/`) → **humans argue about design**
(`playbook/`, `prompts/`).

## 30 seconds to see it work

```bash
cd clean-code-skills

# module quality, before and after refactoring the same business logic
python3 tools/cc-scan.py tools/demo/src/legacy-order-service.ts tools/demo/src/legacy-renderer.ts --no-baseline
#   -> 72.0/100, 4 errors: HARD_PARAMS, EMPTY_CATCH x2, HARD_COMPLEXITY; 11 warnings
python3 tools/cc-scan.py tools/demo/src/order-service.ts tools/demo/src/order-service.test.ts --no-baseline
#   -> 100.0/100, 0 findings

# architecture: dependency direction in a layered demo
python3 tools/arch-scan.py configs/architecture/demo/python
#   -> 82.0/100, 3 errors: DOMAIN_FRAMEWORK_IMPORT, UPWARD_DEPENDENCY, LAYER_CYCLE

# the pack's own test suites
python3 tools/tests/run_checks.py        # -> 60/60
python3 tools/tests/run_arch_checks.py   # -> 30/30
python3 tools/check_links.py             # -> every relative reference resolves
```

## Install into your project

```bash
# Claude Code / Arena agent (skills are auto-discovered)
cp -r clean-code-skills/skills/clean-* ~/.claude/skills/     # global
cp -r clean-code-skills/skills/clean-* .claude/skills/       # or per repo
cp clean-code-skills/tools/*.py tools/                       # so the skills can call the scanners

# Cursor
cp clean-code-skills/skills/clean-code/SKILL.md .cursor/rules/clean-code.mdc   # + the references you need

# Codex / org-wide: keep this tree in an `.agent-skills` repo and symlink
```
Full steps and post-install checks: `INSTALL.md`.

## The 9 code criteria + 3 architecture sessions, and where they live

| # | Standard | Skill | Playbook | Reference | Machine check |
|---|---|---|---|---|---|
| 1 | Why clean code (readable · maintainable · extensible · testable) | `clean-code` §0–1 | `01` | `references/01` | `LOW_TEST_RATIO` |
| 2 | Naming | `clean-code-naming` | `02` | `references/02` | `MAGIC_NUMBER`, ESLint naming, ruff `N`, Checkstyle |
| 3 | Functions | `clean-code` §2.2 | `03` | `references/03` | `LONG/HUGE_FUNCTION`, `TOO_MANY/HARD_PARAMS`, `COMPLEXITY`, `DEEP_NESTING`, `BOOLEAN_PARAM` |
| 4 | Comments | `clean-code` §2.4 | `04` | `references/04` | `COMMENTED_CODE`, `TODO_MARK`, `BLOCK_COMMENT` |
| 5 | Formatting | `clean-code-formatting-hooks` | `05` | `references/05` | `LINE_TOO_LONG`, `MIXED_INDENT`, `TRAILING_WHITESPACE` + prettier/black/gofmt |
| 6 | Objects & data structures (encapsulation, Demeter) | `clean-code` §2.5 | `06` | `references/06` | review + `madge`, ArchUnit, import-linter |
| 7 | Error handling | `clean-code-error-handling` | `07` | `references/07` | `EMPTY_CATCH` + ESLint `no-empty`, ruff `TRY/S110/E722`, `IllegalCatch` |
| 8 | SOLID · DRY · KISS · YAGNI | `clean-code` §3 | `08` | `references/08` | `DUPLICATE_BLOCK` + ADR required for every new abstraction |
| 9 | Code health & workflow (refactor, hygiene, CI) | `clean-code` §4–7 | `09` | `references/09`,`10`,`11` | `DEBUG_STATEMENT`, CI gates, coverage-diff, Sonar `new_*` |
| 10 | **Clean architecture** (layers, dependency rule, ports & adapters) | `clean-architecture` | `10` | `references/12` | `UPWARD_DEPENDENCY`, `LAYER_CYCLE`, `DOMAIN_FRAMEWORK_IMPORT` |
| 11 | **Architecture patterns** (modular monolith, events, CQRS, services…) | `clean-architecture` §4 | `11` | `references/13` | ADR with cost sheet + outbox/idempotency review lines |
| 12 | **Design patterns** (and when each is premature) | `references/14` | `12` | `references/14` | `BOUNDARY_LEAK`, `BOOLEAN_PARAM`, review rule "name the cost or delete it" |

## Verified, not "looks right to me"

| Thing | How it was checked | Result |
|---|---|---|
| `cc-scan.py` v1.0.1 | `tools/tests/run_checks.py` | **60/60 PASS** — 20/20 rules fire on the dirty fixture; clean fixture **0 findings**; baseline, config, `cc-scan:allow`, CLI flags, and a regression test for the escape hatch all behave |
| `arch-scan.py` v1.0.0 | `tools/tests/run_arch_checks.py` | **30/30 PASS** — 4 error rules fire on `layers/dirty`, `layers/clean` = **100.0/100 (0 findings)**, Java/Go imports resolved via `rootPackages`, allow-comment scoped per line, drift detection works |
| ESLint 9.39 + Prettier | `npm run check` in `configs/js` | configs parse · `samples/good-example.ts` = **0 problems** · the 2 deliberate bad samples = 10 problems, right rules |
| ruff 0.16 + black + mypy | `configs/python/lint.sh` | `orders_good.py` passes all three · `orders_bad.py` = **39 errors** (ANN001 x9, EM101 x3, TRY002 x2, T201 x2, S110, E722, C901, PLR0912/0915/0917, PLR2004, E711…) |
| Checkstyle 10.21.4 | `java -jar checkstyle.jar -c configs/java/checkstyle.xml configs/java/demo/OrderTotalsBad.java` | **8 audit messages** on the bad demo = 7 WARN (1 `ParameterNumber`, 5 `MagicNumber`, 1 `EmptyCatchBlock`) + 1 INFO (`TodoComment`); `OrderTotalsGood.java` = **0** |
| **import-linter 2.15** | `configs/architecture/demo/python` | `Layers point inward` + `Domain stays framework-free` **BROKEN → KEPT** after deleting one file (exit 1 → exit 0, "Analyzed 13 files, 14 dependencies") |
| **ArchUnit 1.3.0 (JDK 11)** | `configs/architecture/demo/java` | 3 rules **BROKEN → KEPT** on the same code shape, exit 1 → 0 |
| pre-commit hooks | `hooks/check-hygiene.sh`, `hooks/check-arch.sh` in a temp git repo | dirty staged file → **exit 1** naming the exact lines; clean → **exit 0** |
| CI templates | `yaml.safe_load` on all 5 YAML files (`configs/ci/*`, `configs/go/.golangci.yml`) | parse OK; jobs/steps/hooks contain the `arch-scan` + `cc-scan` gates. The commands themselves need a runner — each one is the tested CLI above |
| Docs cross-references | `python3 tools/check_links.py` | **200 references checked, 0 broken** · the checker itself scores **100.0/100** under `cc-scan` when run from `tools/` (where `clean-code.config.json` skips `DEBUG_STATEMENT`/`MAGIC_NUMBER` for CLI scripts); 95.8 from the pack root, where that config is not loaded — that gap is the config-scoping rule documented in `tools/README.md` §3, not a bug |
| One standard everywhere | thresholds 120 / 40 / 3 params / complexity 10 repeated in `cc-scan`, ESLint, ruff, Checkstyle, golangci, `.editorconfig` | read by hand + asserted in `run_checks.py` |
| golangci-lint | **not run** | no Go toolchain in this sandbox; `configs/go/README.md` says so. `demo/*.go` were scanned by `cc-scan`, and `.golangci.yml` (incl. the new `depguard` rules) parses as valid YAML |

## What to read, depending on the question

- **"Make the AI write to standard"** → `skills/clean-code/SKILL.md` (self-sufficient) + `skills/clean-architecture/SKILL.md`.
- **"I'm about to review a PR"** → `skills/clean-code/checklists/code-review.md` + `prompts/00`.
- **"How should this be structured / monolith or services / which pattern?"** → `references/12`–`14`, `skills/clean-architecture/SKILL.md`, `prompts/11`–`13`.
- **"Get the whole team on one standard"** → playbook sessions 01→12; settle the 3 policies at the top of `playbook/README.md` first.
- **"Our repo is 3 years old, lint would report 12 000 errors"** → `configs/ci/` + `--update-baseline` (§5 of `tools/README.md`).
- **"Boss asks how our quality measures"** → `references/01-why-clean-code.md#3` and `playbook/appendix-b-maturity-model.md`.

## Four-line philosophy

1. Code is read far more than written → every rule is derived from reading cost and change cost.
2. Anything a machine can decide must not be decided by a human (format, one-letter names, log leftovers).
3. No standard survives without a transparent exception path: `cc-scan:allow` / `arch-scan:allow` + reason + ADR.
4. Refactoring without tests is a gamble, not bravery — every technique here starts by locking behaviour.

`CHANGELOG.md` · `tools/SELF_REVIEW.md` (the tools reviewed by themselves, including the debt table).
