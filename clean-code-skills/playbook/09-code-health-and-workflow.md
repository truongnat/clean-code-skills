# Session 9 · Code health and workflow — holding the line when the pressure rises

**Duration:** 60 minutes, the final session of Part I; it ends with a pipeline that actually runs.
**Output:** clean-code CI enabled, baseline frozen, the Definition of Done signed at the retro.

## 1. Four layers of fence (miss one and the standard leaks)

```text
Layer 0  Dev machine     .editorconfig + formatter on save + lint-staged/pre-commit (< 3 s)
Layer 1  CI, fast         formatter --check + lint + cc-scan --fail-on error + arch-scan + coverage-diff
Layer 2  CI, deep         SonarQube Quality Gate on new code + nightly whole-repo scan + secret scan
Layer 3  Humans, in PR    design, business rules, boundaries - the only part a person should spend time on
```

🔧 **The agreed process:** the pre-commit hook stays under three seconds (no test suites there), the
fast CI lane stays under eight minutes, and every rule in `tools/clean-code.config.json` has a named
owner. A rule with no owner is a rule that will be switched off by whoever is annoyed first.

## 2. Do it for real during the session (30 minutes — leave with a working CI)

```bash
# 1) scan and freeze the current state
python3 ../tools/cc-scan.py . --json -o /tmp/before.json && jq '{score,counts}' /tmp/before.json
python3 ../tools/cc-scan.py . --update-baseline
git add .clean-code-baseline.json      # the tool prints this name; the baseline is committed
# 2) copy the config
cp ../configs/ci/.editorconfig .
cp ../configs/ci/github-actions-clean-code.yml .github/workflows/clean-code.yml
cp ../configs/js/.prettierrc.json ../configs/js/eslint.config.js .
cp ../configs/python/pyproject.toml .
# 3) turn on pre-commit hooks
npx husky init && echo 'npx lint-staged' > .husky/pre-commit && cp ../configs/ci/lint-staged.config.js .
# (Python: pipx install pre-commit && pre-commit install)
# 4) test the fence on purpose: leave a `console.log` in a file and open a PR
```

**If CI does not go red, the session is not finished.** Debug until it does — it is usually an
`ignoreDirs` mismatch, the file living outside the scanned folder, or `--fail-on` set to `none`. A
gate you have never seen fail is not a gate; deliberately failing it is the last ten minutes of this
session and the most valuable.

Same for structure: commit a file that makes `domain` import `infrastructure`, and confirm the
`arch-scan` step blocks. Measured in this pack's own demo hook, a dirty tree prints
`[pre-commit] ARCHITECTURE: Architecture score: 92.0/100 (grade A) - 1 error(s)` and **exit 1**; the
clean tree exits 0 — that pair is the acceptance test for the whole chapter.

## 3. Definition of Done (paste into `CONTRIBUTING.md`, sign it at the retro)

```md
- [ ] `cc-scan`: 0 new error findings, 0 new warnings versus the baseline
- [ ] `arch-scan --fail-on error`: no new upward edge, no cycle, no boundary leak
- [ ] formatter + linter green (`make fmt-check`, `make lint`)
- [ ] functions <= 40 lines / <= 3 params; exceptions carry `cc-scan:allow` + reason
- [ ] no debug prints, no commented-out code, every TODO has a ticket id
- [ ] tests: behaviour + each new `catch` + boundaries; coverage on new code >= 80%
- [ ] no behaviour change inside a `refactor:` commit
- [ ] PR <= 400 changed lines, or the description says why not
```

Eight lines is already a lot; if your team has twenty, half will be ignored — trim to what you will
actually enforce on a Friday afternoon.

## 4. The SonarQube quality gate (the block to paste)

```text
new_coverage < 80%                       -> fail
new_duplicated_lines_density > 3%        -> fail
new_blocker_violations > 0               -> fail
new_critical_violations > 0              -> fail
sqale_rating(new_code) worse than A      -> fail
security_hotspots(new_code) > 0          -> fail
```

Apply it to **new code only**. A three-year-old repo cannot be "clean" before merge, but it can be
forbidden to get dirtier — and that is the honest answer to "we have no time to clean up": you do not
need time to clean up, you need a ratchet.

The same philosophy differs by tool on purpose: `cc-scan` **has** a baseline (a style scanner would
otherwise block everything at adoption), while the architecture gates **do not** (import-linter,
ArchUnit and `arch-scan` all fail on the first new violation, and an architecture freeze would make
the dependency rule decorative). If you must freeze structure, do it as an explicit `allow` list with
a ticket and a date, not as a baseline file.

## 5. Ratchet schedule (quarter / half-year) — committed by date, not by willpower

| Milestone | Work | Owner |
|---|---|---|
| Week 1 | baseline + CI blocks at `error` + formatter live | DevOps / lead |
| Month 1 | `COMMENTED_CODE` and `DUPLICATE_BLOCK` to zero; `no-console` on | one PR per team per week |
| Month 2 | `LONG_FUNCTION` → `error`; `MAGIC_NUMBER` tightened in `src/domain` | module owners |
| Month 3 | Sonar gate on `new_*`; DoD applies to **every** PR | lead |
| Next quarter | tighten 40 → 30 lines/function in the two hottest modules; re-measure | |

Each milestone: one line in `docs/clean-code-changelog.md` with the score before and after. Without a
log, a standard is forgotten in six weeks — not because people are careless, but because nobody can
tell whether the current rule is the one they agreed to.

## 6. The weekly ritual (15 minutes inside the retro; this is what turns it into culture)

1. Read this week's score for the three hottest modules — the **trend**, not the absolute.
2. One person opens a piece of their own code they are not happy with; the room offers one suggestion
   each, three minutes per case. Voluntarily showing your mess is the practice that makes code review
   non-adversarial; no rule does that.
3. One `praise`: which PR had a beautiful refactor, and what made it good.
4. Register **one** rule to tighten next week, with a name against it.

## 7. Three traps that kill the process (seen in team after team)

| Trap | Symptom | Cure |
|---|---|---|
| "refactor next sprint", which never arrives | 8 `tech-debt` issues, no assignee | one debt slot per sprint, counted in capacity, not "squeezed in" |
| CI switched off because it is annoying | 200 warnings per PR, `--no-verify` in the commit list | baseline + incremental checks; **turn off the noisy rule, never the CI** |
| review turns into a style tribunal | 40 comments about names | make lint strong enough that style comments are out of bounds by policy (§1 of session 5) |
| a gate red for a week | "we'll fix it after the release" | same-day rule: fix it, or delete the check in a PR that says why — silence is the only wrong answer |

## 8. Final exam (end of the course)

1. Why must `cc-scan` run on the dev machine **and** in CI with the same command and the same config?
   (it kills "works locally, fails in CI", which is how scanners lose all trust)
2. Which is worse: one new violation slipping through, or one rule holding three PRs for two days?
   Balance it (a rule that cannot be machine-fixed or auto-suggested should drop to `info` plus an
   issue, not stay at `error` and breed bypasses).
3. Rewrite your team's DoD in ≤ 8 lines and submit it as a PR to `CONTRIBUTING.md`. If you cannot cut
   it to eight, you have a wish list, not a definition.
4. Show the numbers: run `cc-scan` on your own module now, then after one week of the ratchet. A
   change of +2 points with an empty baseline is a healthier programme than +15 with a baseline nobody
   dares to open.

## 9. What "the programme is working" looks like at three months

- the weekly score line trends up and nobody has to be asked to post it;
- the baseline file is **smaller** than last quarter, and its diff appears in PRs like code;
- review comments are about design and business rules; style arguments are absent, not suppressed;
- a new joiner's first PR passes CI without a human explaining a rule;
- someone proposes deleting a check, and the team has a real conversation about it — that, more than
  a rising score, is the sign the culture is working: the gates are now **owned**, not imposed.

Materials: `../skills/clean-code/references/09-code-health-workflow.md` · skill
`clean-code-formatting-hooks` · `../tools/README.md` · `../configs/ci/`

*One disclaimer to keep saying: this pack's Go config (`.golangci.yml`) is written and linted-by-review
but has never been **executed** in our sandbox — no Go toolchain is installed here. Run
`golangci-lint run` on your own repo before you advertise the numbers, and report back what differs.*
