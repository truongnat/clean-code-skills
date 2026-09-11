---
name: clean-code-formatting-hooks
description: >-
  Set up the automatic guardrails for clean code: EditorConfig, Prettier/Black/gofmt,
  ESLint/ruff/golangci-lint/Checkstyle, husky + lint-staged, pre-commit hooks, cc-scan and
  arch-scan in CI, a SonarQube quality gate, and a baseline for legacy code. Use when the
  user asks how to configure eslint/prettier/ruff/checkstyle, "set up pre-commit", "add lint
  to GitHub Actions", "onboard lint on a legacy repo", or when the team is arguing about
  formatting and the decision needs to move to a machine.
metadata:
  version: "1.1.0"
  companion: "clean-code"
---

# Formatting, hooks & CI — make the standard the default

> **Scanner path:** commands below assume `tools/cc-scan.py` / `tools/arch-scan.py` are in the
> repo. If they are not, the same scanners may be on `PATH` as `cc-scan` / `arch-scan` (identical
> flags) — see `INSTALL.md` §1b. If neither exists, ask for the report instead of guessing numbers.

A rule nobody enforces is a suggestion. This skill is about moving decisions out of code
review and into tooling, so review time goes to design instead of commas.

## 0. Division of labour (exactly one owner per decision)

| Layer | Tool | Catches | Runs |
|---|---|---|---|
| Editor | `.editorconfig` | indent, LF, final newline | on open |
| Format | Prettier · ruff-format/Black · gofmt/gofumpt · ktlint | layout only | save / pre-commit |
| Language lint | ESLint · ruff · golangci-lint · Checkstyle | bugs + style that has a rule | pre-commit + CI |
| **Clean Code team rules** | `tools/cc-scan.py` | function size, params, magic values, comments, debug logs, duplication | pre-commit + CI |
| **Structure** | `tools/arch-scan.py` + one exact tool (`import-linter`, ArchUnit, dependency-cruiser, `depguard`) | dependency direction, cycles, boundary leaks | pre-commit (0.2 s) + CI |
| SAST / quality | SonarQube · Semgrep | security, debt, fuzzy duplication | CI + PR gate |
| Tests | vitest / pytest / go test + coverage-diff | behaviour | CI |

Never run two tools that **decide the same thing** (Black + Prettier on the same Python files
= a war that ends with someone disabling CI). Every layer has one owner; the owner writes the
config, the config lives in the repo.

## 1. Install in five minutes

```bash
# --- Node/TS ---
npm i -D prettier eslint @eslint/js typescript-eslint husky lint-staged
npx husky init
echo 'npx lint-staged' > .husky/pre-commit
cp configs/js/.prettierrc.json . && cp configs/js/eslint.config.js .

# --- Python ---
cp configs/python/pyproject.toml .              # ruff + black + mypy
pipx install pre-commit && pre-commit install
cp configs/ci/.pre-commit-config.yaml . && cp -r configs/ci/hooks .   # hooks/ ships check-hygiene.sh + check-arch.sh

# --- Go ---
cp configs/go/.golangci.yml . && go install mvdan.cc/gofumpt@latest
# Makefile: lint: gofumpt -l . && golangci-lint run

# --- every repo: turn on the pack's scanners first ---
mkdir -p tools && cp tools/cc-scan.py tools/arch-scan.py tools/
python3 tools/cc-scan.py . --update-baseline                       # legacy: freeze today's debt
git add .clean-code-baseline.json
```

## 2. Architecture gate (the part most teams forget)

Formatting settles in a week. Layering rots silently, because nothing fails when
`domain/` starts importing `db/`. Wire `arch-scan` where the formatter already runs:

```bash
cp configs/architecture/arch-scan.config.json .      # edit layers to your folder names
python3 tools/arch-scan.py src --fail-on error
```

```yaml
# .github/workflows — one step, before the expensive ones
- name: Architecture scan (arch-scan)
  env: { CC_ARCH_FAIL_ON: error }
  run: python3 tools/arch-scan.py src --fail-on "$CC_ARCH_FAIL_ON"
```

`.pre-commit-config.yaml` already carries a matching hook (`id: arch-scan` →
`hooks/check-arch.sh`): it stays quiet in a repo that declares no `arch-scan.config.json`, so
copying the pack into a legacy repo cannot break anyone's commit. For the exact version, add
`import-linter` (`.importlinter` in `configs/architecture/`) or ArchUnit
(`configs/architecture/demo/java`); `arch-scan` is the cheap always-on tripwire, the exact tool
is the authority when they disagree.

## 3. lint-staged (format only what you actually staged)

```js
// lint-staged.config.js — full version in configs/ci/lint-staged.config.js
export default {
  "*.{ts,tsx,js,jsx}": ["prettier --write", "eslint --fix --max-warnings=0"],
  "*.py": ["ruff check --fix", "ruff format"],
  "*.go": ["gofmt -w", "gofumpt -w"],
  "*.{md,json,yml}": ["prettier --write"],
  "*.java": ["google-java-format --replace"],
};
```

**A pre-commit hook must stay under ~3 seconds.** No tests, no coverage, no network, no
type-check of the whole project. The moment the hook is slow, the team learns `git commit
--no-verify`, and you have replaced a standard with a ritual. Anything heavier belongs in CI,
or in a pre-push hook that people tolerate.

## 4. Shared configs (copy, don't rewrite)

| File | What it holds |
|---|---|
| `configs/js/.prettierrc.json` | `printWidth: 120`, `semi: true`, `singleQuote: false`, `trailingComma: "all"` |
| `configs/js/eslint.config.js` | flat config; `max-lines-per-function` 40, `max-params` 3, `complexity` 10, `max-depth` 3, `no-restricted-syntax` on 1-char names and `Manager/Util/Data` suffixes, `no-console` warn, type-aware for `.ts` |
| `configs/python/pyproject.toml` | ruff `E,W,F,I,N,UP,B,SIM,RET,ARG,TRY,EM,LOG,G,C901,PL,ERA,T20,PTH,ANN,D,S,DTZ`; `max-args=3`, `max-statements=20`, `max-nested-blocks=2`; Black line-length 88 |
| `configs/java/checkstyle.xml` | `MethodLength` 40, `ParameterNumber` 3, `MagicNumber`, `EmptyCatchBlock`, `NestedIfDepth` 2, `TodoComment`, `SuppressionCommentFilter` |
| `configs/go/.golangci.yml` | `funlen` 60, `cyclop/gocognit` 12, `nestif`, `varnamelen`, `errcheck/wrapcheck/bodyclose`, `depguard` layer ban, `gofumpt` |
| `configs/architecture/arch-scan.config.json` | layers + ranks, `frameworkPackages`, `boundaries`, `rootPackages`, `maxUnclassifiedPct` |
| `tools/clean-code.config.json` | the team's `cc-scan` thresholds + ignores + `skipRules`, each with a written reason |

## 5. Minimal CI that is still enough

```yaml
name: clean-code
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: npm ci
      - run: npx prettier --check .
      - run: npx eslint . --max-warnings=0 --format github
      - run: python3 tools/cc-scan.py . --fail-on error --json -o cc.json   # baseline auto-loaded
      - run: pipx install ruff && ruff check . && ruff format --check .
      - if: always()
        uses: actions/upload-artifact@v4
        with: { name: clean-code-report, path: cc.json }
```

The full template (changed-files-only scanning, a nightly whole-repo job, a PR comment bot,
the `arch-scan` step) is `configs/ci/github-actions-clean-code.yml`; GitLab:
`configs/ci/gitlab-ci-clean-code.yml`.

## 6. Ratchet plan for a legacy repo (how to not paralyse the team)

```bash
# 1. freeze the current state - nobody is blamed for 2019
python3 tools/cc-scan.py . --update-baseline && git add .clean-code-baseline.json
# 2. CI now blocks NEW findings only (cc-scan loads the baseline automatically)
# 3. each sprint: fix one rule group, delete it from the baseline, re-run --update-baseline
# 4. when the baseline is empty: delete it and switch to --fail-on warning
```

Start wide and narrow it, never the reverse — a gate that goes red on day one gets disabled.
Suggested thresholds by stage:

| Stage | cc-scan | Format | Architecture |
|---|---|---|---|
| Week 1 | `--fail-on error`, baseline committed | `--check` on changed files only | `arch-scan` advisory (`--fail-on none`), report posted to the PR |
| Month 1 | errors **and** warnings on new code; baseline shrinks | whole repo `--check` in CI | `--fail-on error` in CI; one contract in import-linter/ArchUnit |
| Quarter 1 | thresholds tightened (`maxFunctionLines` 40 → 30) | hooks mandatory, no `--no-verify` in policy | boundaries declared for every top-level folder; `LAYER_UNUSED` treated as a bug |

**Never** commit `# noqa`, `eslint-disable` or `--no-verify` if it silences *new* violations.
An exception must be narrow and carry a reason:
`// cc-scan:allow-file LONG_FUNCTION — state machine loop, see docs/adr/0012`.

## 7. SonarQube quality gate (suggested, `new_*` only)

```
new_coverage                 < 80%    → fail
new_duplicated_lines_density > 3%     → fail
new_blocker_violations       > 0      → fail
new_critical_violations      > 0      → fail
sqale_rating(new)            worse than A → fail
```

Gating on **new** code is the only way quality trends up while pull requests keep merging.
Whole-repo ratings are a dashboard, not a gate — nobody fixes 4,000 issues for a badge.

## 8. Local pre-flight before opening a PR

```bash
make fmt     # npx prettier --write . && npx eslint . --fix
make lint    # eslint --max-warnings=0 + ruff + golangci-lint
make scan    # python3 tools/cc-scan.py . --fail-on error
make arch    # python3 tools/arch-scan.py src --fail-on error
make test    # tests + coverage-diff
```

These exist in `configs/python/lint.sh`, `configs/js/package.json` and the CI templates.

## 9. When the tools disagree with you

| Symptom | Cause | Fix |
|---|---|---|
| Hook green locally, red in CI | different Python/Node, or CI has no `.clean-code-baseline.json` | commit the baseline; pin versions in CI |
| Prettier rewrites 900 unrelated files | no ignore file for generated/vendored code | add `.prettierignore`, not a disable comment |
| ESLint 4x slower after enabling types | type-aware linting over the whole repo | scope `parserOptions.project` to `src/` |
| `cc-scan` takes 30 s on a small repo | it is walking `node_modules` because a config replaced `ignoreDirs` | `ignoreDirs` only *adds*; the floor is built in |
| `arch-scan` says `UNCLASSIFIED_FILES` | your folder names differ from the config's globs | edit `layers[].include`, or add `**/interfaces/**` style globs |
| ArchUnit passes, `arch-scan` errors | `arch-scan` reads source imports; ArchUnit reads bytecode | the exact tool wins; add the missing package to `frameworkPackages` or annotate with `arch-scan:allow` + ticket |
| Someone disabled the hook "just this once" | the hook is slow or noisy | fix the hook's cost, do not negotiate the rule |

## 10. Verified in this pack (all re-run for this release)

| Tool | Run? | Result |
|---|---|---|
| ESLint 9 + typescript-eslint + Prettier 3 | ✅ | config parses; `configs/js/samples/good-example.ts` → 0 problems; the two `bad-*` samples → 10 problems (4 errors, 6 warnings) matching the rules above |
| ruff + Black + mypy | ✅ | `configs/python/src/orders_good.py` passes all three (`lint.sh` exit 0); `orders_bad.py` → **39 ruff errors** (ANN001, EM101, T201, TRY002, D103, E722 …) |
| Checkstyle 10.21.4 | ✅ | `java/demo/OrderTotalsBad.java` → **8 violations** (1 `TodoComment`, 1 `ParameterNumber` "More than 3 parameters (found 6)", 5 `MagicNumber`, 1 `EmptyCatchBlock`); `OrderTotalsGood.java` → 0 |
| `cc-scan.py` | ✅ | `tools/tests/run_checks.py` → **60/60 checks passed** |
| `arch-scan.py` | ✅ | `tools/tests/run_arch_checks.py` → **30/30**; `configs/architecture/demo/python` → 82.0/100 with 3 errors |
| import-linter 2.15 | ✅ | demo contract set: 2 contracts BROKEN (exit 1) → 2 kept (exit 0) on the same tree |
| golangci-lint | ⚠️ not executed | no Go toolchain in this sandbox; `.golangci.yml` is YAML-validated and documented in `configs/go/README.md` |
