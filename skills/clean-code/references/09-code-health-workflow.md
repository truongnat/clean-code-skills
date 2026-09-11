# 09 · Code health & workflow — keeping the standard when pressure rises

> Clean code is not a state you reach once; it is a state you **maintain** across hundreds of
> commits, new joiners and deadlines. This chapter is where the pack becomes a routine.

## 1. Red → Green → Refactor, and why TDD is a dirty-code machine

```text
RED     : write a failing test for a missing behaviour  -> you prove the test can fail
GREEN   : write just enough code to pass, ugly allowed    -> you never design under panic
REFACTOR: clean it, tests stay green                     -> this is where Clean Code is applied
```

Three conditions that make the third step safe:
1. the tests are green **and real** — break one line on purpose and check that something turns red;
   a suite that cannot go red is decoration (see `11-testing-for-clean-code.md` §mutation-lite);
2. no behaviour change: the refactor diff contains no modified assertions;
3. each step is its own commit (`refactor: extract pricingPolicy`), never mixed with the feature.

You do not have to practise full TDD to keep the rule that matters: **separate refactoring from
behaviour change** (Fowler's two branching trees). Everything else in this chapter is downstream of
that one habit, because it is what makes a diff reviewable and `git bisect` usable.

When TDD is the wrong tool, say so and use the weaker but honest version: exploratory prototypes
(delete them, do not grow them), purely visual UI, Terraform/K8s manifests (use plan-time
validation + `checkov`), and one-off data fixes (a reviewed script + a snapshot of the before
state). The common thread: something must still *prove* the outcome — the proof just is not a unit
test.

## 2. Definition of Done for a PR (paste this into `CONTRIBUTING.md`)

```md
## Definition of Done
- [ ] `cc-scan` + formatter + linter: 0 errors, 0 new warnings versus the baseline
- [ ] no new `arch-scan` finding: no upward edge, no layer cycle, no boundary leak
- [ ] every function <= 40 lines, <= 3 params, no unnamed number in logic
- [ ] no leftover `console.log` / `debugger` / `System.out` / `fmt.Print`
- [ ] no `catch {}`; every failure is logged-thrown-once or handled with a written reason
- [ ] tests: happy path + each new error branch; coverage on new code >= 80%
- [ ] no behaviour change outside the ticket's scope (if there is one -> separate PR, say so)
- [ ] `ARCHITECTURE.md` / ADR / README updated if a port, module, env var or business rule moved
- [ ] a second reviewer understood it in < 15 minutes (if not: the author documents first)
```

Add two more lines when the repo carries architecture:

```md
- [ ] a new module is declared in the layer config (`arch-scan.config.json`) — not "unclassified"
- [ ] an intentional exception carries `cc-scan:allow`/`arch-scan:allow` + reason + ticket id
```

For a **release**, the DoD is different in kind — it is about leaving nothing running in the dark:
no debug logs at default level, every feature flag has an expiry and an owner, the runbook has a
line for each new alarm, the migration is reversible or documented as irreversible, and the
rollback command is *written down and tested*, not remembered.

## 3. Baseline: onboarding legacy code without freezing the repo

The problem: switching a new rule on in a 500k-line repo yields 12,000 findings and the team turns
CI off. The pack's answer: **block the new, improve the old gradually**.

```bash
python3 tools/cc-scan.py . --update-baseline                       # freeze today's state
git add .clean-code-baseline.json && git commit -m "chore: baseline clean-code (existing debt)"
python3 tools/cc-scan.py . --fail-on error                          # from now on, only NEW findings bite
```

CI pattern, incremental per changed file:

```yaml
- name: Clean Code (touched files only)
  run: |
    FILES=$(git diff --name-only origin/${{ github.base_ref }}...HEAD \
            | grep -E '\.(ts|tsx|js|py|java|go)$' || true)
    [ -z "$FILES" ] && exit 0
    python3 tools/cc-scan.py $FILES --fail-on error
- name: Architecture scan (whole tree, it needs the full picture)
  run: python3 tools/arch-scan.py src --fail-on error
- name: Clean Code (whole repo, nightly)
  if: github.event_name == 'schedule'
  run: python3 tools/cc-scan.py . --no-baseline --fail-on warning
```

Quarterly ratchet, three steps and no more:
1. fix one rule everywhere until its baseline entry is under 20;
2. move that rule from `warning` to `error` and delete its baseline entry;
3. promote **one** new rule into `--fail-on error`. Five at once is how you get `--no-verify`.

Three rules about the baseline itself, or it becomes a hiding place:
- it is **code, reviewed like code**: one owner, changes only by PR, and its size is a metric you
  post weekly (a growing baseline is a failed quarter, said out loud);
- **never baseline a security or correctness rule** (secrets, empty catch, unvalidated input):
  "existing violations" of those are incidents waiting, not debt;
- architecture has **no baseline** in this pack on purpose. A `domain → db` edge is either removed
  or explicitly `allow`-ed with a ticket and a date; a silent 400-file freeze would make the
  dependency rule decorative, and the exact tools (import-linter, ArchUnit) have no freeze either.

## 4. Review protocol: five minutes, in an order most teams reverse

Design errors cost more than formatting errors, so read in cost order:

1. **Scope.** Is this PR one thing? 800 lines / 20 files → "please split before I read it".
2. **Boundary.** Is the new code in the right place? (domain touching DB? controller holding rules?
   new folder unclassified in the layer config?)
3. **Data model.** Does the new type protect its own invariant, or is it `string status` again?
4. **Public functions.** Signature review: ≤ 3 params, no unannounced side effects, errors typed.
5. **Failures.** Is every new branch tested? Does any `catch` swallow?
6. **Readability.** Try to improve three names. If you cannot find better ones, say one sentence and
   move on.
7. Only now: lint/format — the machine has it; you stay silent.

```bash
gh pr diff 1234 --color=always | npx diff-so-fancy | less -R          # a clean diff, no noise
python3 tools/arch-scan.py src --fail-on none | sed -n '1,12p'       # the matrix, when folders moved
jq -r '.findings[] | select(.severity=="error") | "\(.file):\(.line) \(.rule)"' /tmp/review.json
```

Two shortcuts that pay: read the **test names first** (they are the specification the author
actually meant), and read the **PR description before the diff** — if it says "refactor + fix
timeout bug", your first comment is about splitting it, not about commas. Time-box yourself: at
30 minutes, stop and write what you have; an unread-in-full approval is more dangerous than a
late review.

## 5. Review comments that do not start wars

| Don't | Do |
|---|---|
| "Wrong." | "If `items` is empty, line 42 throws before the test catches it — add a guard?" |
| "Why did you write it like this?" | "A and C differ on X — what made you pick A?" (ask, don't accuse) |
| "Change this." | "Suggestion, non-blocking: extract `feeOf` into a policy; the formula is now in 2 places." |
| a 20-line essay | one sentence + **a link to the rule** in this pack |
| taste-driven rename requests | comment on a name only when it **lies** or is ungreppable |
| "we need an architecture rewrite" | the smallest reversible step: declare the seam, one port, one adapter |

The three-part frame, always: **Observation → Consequence → Proposal (or question)**. Label the
severity (`blocker:` / `should:` / `nit:` / `praise:` / `question:`) so the author knows what is
optional — a `nit` may be declined without justification, and that promise is what keeps people
reading your other comments.

If the author pushes back twice and you still disagree: stop arguing in the thread. Write the two
options with their costs in three lines, let a third person or the ADR decide, and accept the
outcome in the same thread. Two rounds max, then escalate — review is not a duel, and the decision
matters more than who was right.

## 6. Three debt techniques that need no feature freeze

| Technique | Use when | How you prove it works |
|---|---|---|
| **Expand–contract** | changing an API/schema that 5+ places already use | add the new → alias/deprecate → migrate → delete; each step green; the count of remaining callers in the PR body |
| **Strangler** | replacing a module inside a live app | new routes go to the new module; flip **one** endpoint, watch the metric, delete the old path |
| **Branch by abstraction** | swapping a library/ORM/driver | an interface over the old code, both implementations live behind a flag, flip, then remove |
| **Seam-first** (added) | you want to change behaviour but there are no tests | write tests at the seam you can already inject (constructor, HTTP, CLI); only then touch logic |

All four share one property: **the system stays green and shippable at every commit**. That is the
test of a good migration plan — if you cannot name a commit where the app is healthy, you have a
rewrite, not a migration. And a rewrite is allowed, but as a *named project with a date*, not as a
comment in someone's PR.

## 7. Weekly repo health, five minutes, scripted

```bash
python3 tools/cc-scan.py . --json -o .artifacts/cc-weekly.json
jq '{score, grade, counts}' .artifacts/cc-weekly.json
python3 tools/arch-scan.py src --json -o .artifacts/arch-weekly.json
jq '{score, grade, counts, layers}' .artifacts/arch-weekly.json

# the worst rules, by count
python3 tools/cc-scan.py . --json | jq -r '[.findings[].rule] | group_by(.)
  | map("\(length)\t\(.[0])") | .[]' | sort -rn | head

# real hotspots: changed often, not "the ugliest file you remember"
git log --since=6.month --name-only --format= | sort | uniq -c | sort -rn | head -20
```

Three tables belong on the team page:
- **top 10 files by churn** → the refactor candidates, cross-checked against the score of that file;
- **top 10 rules by finding count** → the single rule to ratchet next quarter;
- **score per week** (cc-scan + arch-scan) → the curve must rise; flat for two quarters means the
  commitment was cosmetic, and that is the number to bring to the retro.

Gate the **trend**, not the absolute: a repo at 78 that was 64 in January is healthy; a repo at 90
that was 93 is quietly sliding, and nobody will notice without the series. One row per week,
appended in `docs/quality-trend.md` by the nightly job — a number nobody has to remember to write
is a number that survives.

## 8. Onboarding with this very standard

- **Day 1**: run `make lint && make test` — everything must already be green. A repo that arrives
  red teaches the new joiner that ignoring failures is normal (broken windows, in code form).
- **Week 1**: give them one PR that is *only* renames and an extracted function, in a file they will
  work in later. Zero product risk, full toolchain practice, and a reviewer explains the layer map
  while it is cheap.
- **Month 1**: they write the ADR for their first small design decision, and run the DoD checklist
  themselves before requesting review.
- Standing rule for everyone: before asking, run `cc-scan` on the file and read the checklist —
  it saves both sides a round trip, and it turns "does this look right?" into a number.
- Point them at the pack's own **playbook** sessions in order (01 → 09), not at "read the codebase":
  reading code teaches style, not decisions. Session 10 and `references/12-clean-architecture.md`
  come after their first PR, when they have context for it.

## 9. When to stop polishing and ship

Refactoring is a means. Stop when any of these is true:
- the module's score is ≥ 85 **and** the error branches have tests;
- what is left is **not** on the ticket's path;
- the next step costs more than it saves — then write it down (ADR or issue) instead of doing it;
- your improvement has become the PR's subject, not the ticket's.

Never use "we'll refactor later" to merge code you believe is designed wrong. In practice "later"
means "the next person's problem", and the specific failure is that the *next* change will be built
on top of the shape you approved — at which point fixing it is a migration, not an edit. If the
disagreement is real, record it in one ADR line: decision, cost, revisit trigger.

## 10. Hygiene that belongs to this chapter (and is cheap to lose)

| Item | The rule | The check |
|---|---|---|
| Debug output | nothing prints to stdout in production paths; a logger with a level instead | `cc-scan DEBUG_STATEMENT`, `check-hygiene.sh`, `forbidigo` |
| Secrets | no token in source, in logs, or in error payloads | pre-commit secret scan + Semgrep; a secret in git history is rotated **and** rewritten |
| TODO debt | `TODO(TICKET, owner)` or it becomes an issue now | `cc-scan TODO_MARK`, `TodoComment` (Checkstyle), `no-warning-comments` (ESLint) |
| Stale feature flags | every flag has an expiry + an owner; deleting a flag is a 5-minute PR | a monthly `rg flagname` sweep, or a CI check that fails a flag older than 30 days |
| Dead branches | deleted code and unused exports go away, not into comments | `cc-scan COMMENTED_CODE`, `--no-unused-vars`/`ruff F401`, `depcheck` |
| Log level config | defaults to info in prod, debug available at runtime, never per-file hardcoded | config test + review |
| Failing nightly | a red nightly is fixed the same day or the job is deleted | on-call rota, explicitly |

The last row is the one that decides whether everything above survives: **a check nobody fixes is
not a standard, it is decoration.** If a gate is red for more than a day, either it gets fixed or it
gets removed in a PR that explains why — both are respectable, silence is not.

## 11. What "healthy" looks like, in an auditable list

A repo in this pack's target state, checkable by a stranger in under ten minutes:

- [ ] clone → install → `make lint && make test` green, in a documented path (no tribal knowledge)
- [ ] `.editorconfig`, one formatter, one linter, one clean-code scanner, all committed at the root
- [ ] `cc-scan` score ≥ 85 with a **shrinking** baseline; CI fails on new errors only
- [ ] an `ARCHITECTURE.md` of one page and a layer config that `arch-scan` accepts with 0 errors
- [ ] no `catch {}`, no debug prints, every TODO has a ticket (the CI greps for these)
- [ ] coverage on new code ≥ 80%; error branches tested; the suite can go red when you break the code
- [ ] one quality-trend table, updated weekly, with two rows: cc-scan and arch-scan
- [ ] a review DoD in `CONTRIBUTING.md` that a new joiner can satisfy without asking anyone
- [ ] the exception paths documented: `cc-scan:allow`/`arch-scan:allow` with reasons, plus `skipRules`

Print that list in the retro every quarter. Nine boxes, ticked honestly, is a stronger quality
programme than any policy document — and every unticked box is your next sprint's work, already
written for you.
