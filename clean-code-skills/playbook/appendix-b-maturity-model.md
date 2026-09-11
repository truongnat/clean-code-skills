# Appendix B · Maturity model and a module scoring rubric

> Use it to self-assess the team, to plan a quarter, and to answer "where are we?" with something
> other than a feeling. Every level below has a check you can run in ten minutes.

## 1. Five levels of clean-code maturity

| Level | What you can observe | The single step to the next one |
|---|---|---|
| **0. Chaos** | no formatter, no lint; review looks only for bugs; "it works, ship it" | install the formatter + `.editorconfig`, and one `make lint` that everyone can run |
| **1. Aware** | lint exists but is **switched off** because of the noise; `--no-verify` is a known flag | baseline + incremental: block **new** violations, not the whole repo |
| **2. Enforced** | CI is red for format/lint; `cc-scan --fail-on error` runs; the DoD is in `CONTRIBUTING.md` | add coverage-diff + a `new_*` quality gate; and **delete one noisy rule** (with a written reason) |
| **3. Internalized** | no more "fix the lint" PRs; review talks about design; hotspots get refactored **before** anyone needs them | ADRs for abstraction decisions; boundaries enforced by a tool (import-linter / dependency-cruiser / ArchUnit) |
| **4. Compounding** | new features get **faster** over time; the quality curve rises; new joiners change core code confidently | export the standard: a scaffold/template repo with lint + CI + scanners — this level is rare and worth writing down |

Ten-minute checks, one per level:

```bash
# L0 -> L1: does a single command format+lint the repo, and is it in the README?
grep -n "make lint\|npm run lint\|ruff check" README.md Makefile package.json pyproject.toml 2>/dev/null | head

# L1 -> L2: does CI fail on a NEW violation only? (a baseline file must exist and be committed)
ls -l .clean-code-baseline.json 2>/dev/null; grep -rn "fail-on" .github/workflows/* 2>/dev/null | head -3

# L2 -> L3: is the DoD real? (it is in CONTRIBUTING.md and appears in recent PR descriptions)
grep -c "Definition of Done" CONTRIBUTING.md; gh pr list --limit 5 --json body | jq '[.[] | .body | test("cc-scan|coverage")]'

# L3 -> L4: are boundaries machine-enforced and documented?
python3 tools/arch-scan.py src --fail-on error | tail -3; ls docs/adr/ 2>/dev/null | tail -3

# L4: is the trend moving without a champion pushing it?
ls docs/quality-trend.md && tail -4 docs/quality-trend.md
```

Answer these five out loud and you have your level:
1. Would a new joiner break CI on formatting? (yes → 0–1)
2. Can you name the module getting worse within five minutes? (`cc-scan --json` + the trend file)
3. In your last team PR, how many comments were about style? (more than a third → 1–2)
4. How many files does a new business variant touch? (more than three → the design is not at 3)
5. Does a developer need permission to refactor? (if yes, you are not at 3, whatever the CI says)

## 2. Module rubric (0–100) — for an assessment or an acceptance review

| Group | Pts | What "met" means | How to check |
|---|---|---|---|
| **Readable** | 20 | functions ≤ 40 lines; names self-explanatory; no redundant comments | `cc-scan`, plus one human read |
| | | no magic numbers or string states in logic | `cc-scan --json`, `rg` |
| **Structure** | 20 | one class ≤ 400 lines; no cycles; the domain imports no infrastructure | `arch-scan`, madge, import-linter |
| | | no `a.b().c().d` train wrecks | review + `rg` |
| **Failures** | 15 | zero swallowing `catch`; specific exceptions that keep the cause | `cc-scan` (`EMPTY_CATCH`), ruff `E722/S110`, ESLint `no-empty` |
| | | every outbound I/O has a timeout and a bounded retry | review + the catalogue row |
| **Tests** | 20 | module coverage ≥ 80%; **every** new `catch` has a test; the lane runs in seconds | coverage report, `pytest -q --durations=10` |
| | | mutation score ≥ 60% on the core module | Stryker / mutmut |
| **Hygiene** | 10 | no debug prints, no dead code, every TODO has a ticket | `cc-scan`, `rg` |
| **Documentation** | 10 | public API docstrings; one ADR per non-obvious decision; a 10-line module README | a human, briefly |
| **Stability** | 5 | no flaky tests in the module (measured over 20 runs) | CI history |

Reading the total:

| Score | Meaning |
|---|---|
| < 50 | nobody edits it alone; pair, and fix the top rule first |
| 50–69 | small PRs only; expect review rounds |
| 70–84 | independent edits, normal review |
| ≥ 85 | trusted; review may be async, and this is the module you point new joiners at |

Two rules that keep this honest. **Never use the score to rank people** — you will get gaming instead
of quality: comments deleted to please a linter, functions split into unreadable shards, and a baseline
that quietly grows. And the score of *one* module is a decision aid; the useful signal for the team is
the **series** over weeks, which is why the trend file belongs next to the roadmap.

Ten minutes to score a module:

```bash
M=src/billing
python3 tools/cc-scan.py $M --json | jq '{score, counts, top: ([.findings[].rule]|group_by(.)|map("\(length) \(.[0])")|sort|reverse)[:5]}'
python3 tools/arch-scan.py src --fail-on none | sed -n '/Layer census/,/^$/p'
git log --since="6 months ago" --format= --name-only | grep "$M" | sort | uniq -c | sort -rn | head -5
```

## 3. A sample 90-day plan (a team of six, a two-year-old repo)

| Weeks | Goal | Committed artefact | Gate to move on |
|---|---|---|---|
| 1–2 | machine fences | `.editorconfig`, Prettier/ruff/gofmt, ESLint/ruff configs, pre-commit, `cc-scan --update-baseline` | the repo-wide format commit is merged and blame-ignored |
| 3–4 | stop getting dirtier | CI `--fail-on error`; the DoD signed; `DEBUG_STATEMENT` to zero | a deliberately broken PR is actually blocked |
| 5–6 | pay down one hot module | split the 3 classes over 400 lines; zero `MAGIC_NUMBER` in `src/domain`; ADR-0001 | that module's score ≥ 80 and its baseline entry deleted |
| 7–8 | failure paths | every `catch` has a test; coverage-diff gate at 80%; mutation on the core module | the suite still fails when you break the code on purpose |
| 9–10 | tighten further | `COMMENTED_CODE` + `DUPLICATE_BLOCK` to error; delete one YAGNI abstraction | review comments about style = 0 for two sprints |
| 11–12 | close the loop | the four-metric dashboard; the training playbook runs for the next joiner; a quarter review | the trend line moves without a champion pushing it |

Announce the plan in a sprint retro with **one "done?" box per week**. What is not measured does not
happen, and what is measured but never looked at does not happen either — the second one is how most
quality programmes actually die.

## 4. Anti-patterns of the improvement programme itself (read this before you start)

| Anti-pattern | What it produces | Replace with |
|---|---|---|
| a two-week "tech sprint" to fix everything | zero features, 200 conflicts, and quality back to baseline within a month | 10–15% of capacity per sprint, one rule at a time |
| quality owned by one enthusiastic person | a bus factor of 1: they leave, the standard follows | the DoD on every PR + machines enforcing it |
| a "lines of refactor" KPI | a 900-line PR nobody reviews | KPI: rules tightened, and the hot module's score |
| enabling 40 ESLint rules at once | `--no-verify` across the team | five rules that block; everything else at `info` |
| demanding 100% coverage | assertions written to satisfy a number | coverage on **new** code + tested error branches |
| a quality dashboard nobody opens | the same number, unowned | one line per week in the retro, read aloud |
| gate that stays red for a week | everyone learns the gates are theatre | same-day rule: fix it, or delete the check with a written reason |
| "the score dropped, so we banned dropping the score" | allow-comments multiply to dodge the metric | discuss the *why* behind a drop; adjust the ratchet, not the thermometer |

## 5. Which artefact belongs to which level (self-check list)

| Level | The repo should contain |
|---|---|
| 0 → 1 | `.editorconfig`, one formatter config, one linter config, `make lint` documented |
| 1 → 2 | `tools/cc-scan.py` + `tools/clean-code.config.json`, a committed baseline, a CI job that blocks new errors |
| 2 → 3 | `CONTRIBUTING.md` DoD, a coverage-diff gate, a weekly trend file, a TODO-with-ticket check |
| 3 → 4 | `ARCHITECTURE.md` + `arch-scan` config + a real contract tool (import-linter/ArchUnit/dependency-cruiser), `docs/adr/` in use, `.pre-commit-config.yaml` |
| 4 | a scaffold/template repo carrying all of the above, plus the playbook sessions as onboarding material |

If a level's artefact is missing, do not "advance" to the next level by willpower — the artefact is the
proof that the previous step stuck.

## 6. Re-audit, and what regression looks like

Re-run this appendix **once a quarter**, in the same order, and store the result next to the trend file.
Three numbers tell you nearly everything: the new-error count per PR, the baseline size, and the count
of style comments in review. Regression is rarely a decision; it is three quiet things — a gate
switched to `warn`, a hook removed "temporarily" in a rush, and a rule deleted without a note. Each is
reasonable on its own and, together, they return the repo to level 1 inside a quarter, which is why
the anti-pattern table above is the most-read page of this appendix.
