# 01 · What clean code means — a money problem, not an aesthetics problem

> Use this when you need to **convince** someone (a lead, a PM, an engineer) to spend time on
> quality, or when you need measurable criteria instead of the feeling "this code is dirty".

## 1. Four properties, each convertible into a cost

| Property | The 2 a.m. question | What you pay without it |
|---|---|---|
| **Readability** | Can I follow this flow in five minutes, or do I have to open eight files? | *understanding* takes longer than *fixing* → bugs live long |
| **Maintainability** | If I change this, does something else break? Which test tells me? | "fix one bug, create two" → velocity decays quietly |
| **Extensibility** | To add one new fee type: edit one place, or operate on twelve files? | Each feature gets slower as the repo ages (hyperbolic curve) |
| **Testability** | Can I run this logic in a unit test, or do I need Postgres first? | No tests → no refactoring → the debt freezes in place |

These four are **one** thing seen from four sides: code that explains itself reads fast;
loose coupling means a change does not spread; clear boundaries mean you can add without editing;
injectable dependencies mean you can test. Fix one side and the others move — that is why
"clean code" is not a cosmetic label.

## 2. Why dirty code slows the whole team (mechanics, not morality)

1. **Comprehension cost is non-linear.** A 15-line function with three parameters costs ~30
   seconds. A 300-line function with five shared mutable variables costs ~40 minutes *and
   scares people*, so they patch from the outside instead of fixing the cause. Every outside
   patch is another layer of debt, which makes the next 40 minutes 50.
2. **Every unjustified level of indirection is a tax.** `AbstractXxxManagerFactory` is paid by
   every reader, every read, forever — and it only ever saved its author one decision.
3. **No tests ⇒ no refactoring ⇒ only layering on.** This is the mechanism that stops legacy
   code from "improving with age". Code does not decay because people are lazy; it decays
   because the safe move (a small test-first edit) is unavailable.
4. **Slow review is a multiplier, not a side issue.** Long PR + messy diff → reviewer spends
   their attention on formatting instead of logic → PR sits → the base moves → conflicts →
   the same change is made twice. Your code-quality problem shows up in the cycle-time chart.
5. **The knowledge walks away.** When the person who understands the pricing module moves on -
   and in a small team someone does, every couple of years - what survives them is either the
   tests and the names, or nothing.

```bash
# the debt compounding, visible in your own repo (no install needed)
git log --format= --name-only --since=6.month.ago | sort | uniq -c | sort -rn | head -10   # hotspots
git log --numstat --format= -- <hot-file> | awk '{a+=$1;d+=$2} END {print "churn:", a+d}'   # effort sink
```

**Hotspot = high churn x low quality.** A file everyone avoids and nobody tests is where your
next incident comes from; that is the file to fix, not the ugliest one in the repo.

## 3. Measurement: what you cannot measure, you cannot improve

| Metric | How to get it | Suggested threshold | How to read it |
|---|---|---|---|
| Clean Code score | `python3 tools/cc-scan.py . --json` | ≥ 85 good · 70–85 acceptable · < 70 needs a plan | Compare with **itself last week**, never with another repo |
| Error-level findings | the CI artifact | 0 on new code | +1 must be explained in the PR description |
| Coverage on **new** code | coverage-diff | ≥ 80% | 100% repo-wide is a fantasy; 0% on new code is negligence |
| PR age (open → merge) | `gh pr list --json createdAt,mergedAt` | < 1 day for a mid-size team | High = review bottleneck or oversized PRs |
| Change failure rate | DORA-style tracking | < 15% (team-set) | Low quality shows up here first — this is the number management reads |
| Avg. branch complexity/function | `radon`, ESLint `complexity` | < 6 | > 10 means nobody can test every path |
| Files > 400 lines | `wc -l` | trending down | Module-split candidates |

```bash
python3 tools/cc-scan.py . --json | jq '{score, grade, counts}'
find src -type f \( -name '*.ts*' -o -name '*.py' -o -name '*.java' -o -name '*.go' \) -exec wc -l {} + \
  | sort -rn | head -15
python3 tools/arch-scan.py src --fail-on none | sed -n '1,12p'    # structure never shows up in these rows
```

Two rules about metrics, or they will rot your standard:
- **A metric is a question, not a target.** The day a team's score becomes its performance
  review, the score goes up and the code does not.
- **One number per week, tracked in one place** (a single `docs/quality-trend.md` or a CI
  badge). Ten dashboards = zero behaviour change.

## 4. Which property is enforced by which machine

| Property | Enforced by | What the machine cannot see |
|---|---|---|
| Readability | `cc-scan` `LONG_FUNCTION`, `LINE_TOO_LONG`, `MAGIC_NUMBER`; formatter | whether the name matches the domain's vocabulary |
| Maintainability | tests + `git diff -w` discipline; `DUPLICATE_BLOCK` | whether two similar blocks change for the same reason |
| Extensibility | `TOO_MANY_PARAMS`, `COMPLEXITY`, `DEEP_NESTING`; `arch-scan` boundaries | whether the seam you chose is where the next requirement lands |
| Testability | coverage-diff, Sonar gate; the DI-friendly layout `arch-scan` protects | whether the test asserts the *business* rule or the implementation |
| (structure) | `arch-scan` + import-linter/ArchUnit/depguard | intent behind a deliberate exception — that is the reason text |

This table is the pack's spine: every reference in this folder has one, and a rule with no
enforcement in it is marked as "human-only" instead of pretending to be a standard.

## 5. Talking to a PM or a lead: trade "nice code" for what they already care about

Don't say: *"this code is dirty, we have to refactor."* Say:

> The same change to the shipping-fee rule took 5 days last quarter. This one I estimate at 11,
> because the rule lives in 7 files, 3 of them duplicated and none of them tested. Give me 2 days
> in this sprint to put the rule in one place with 6 tests; after that, a fee-rule change is about
> 1 day. If we skip it, we keep paying 8–10 days per quarter for the same kind of change.

Three reusable techniques inside that sentence:
1. **Anchor on a cost already paid** (5 → 11 days), not on a feeling.
2. **Name the mechanism** (duplication, no tests), not the aesthetics.
3. **Trade in packages**: a small slice, a deadline, and an explicit dividend (11 → 1 day).

And be honest about the cheap option: *"If we only patch it, I need 20% extra buffer for
follow-up bugs, because nothing protects the area."* That buffer is the real price of dirty code,
and it is usually larger than the refactor.

One-slide template if you have to write it down: **cost paid → mechanism → proposed package →
dividend → what happens if we don't**. No adjectives. Adjectives start arguments; numbers close them.

## 6. A rollout strategy that does not bankrupt the team

| Phase | Do | Do not |
|---|---|---|
| 1. Diagnose | `cc-scan .` for the score; pick 3 hotspots (churn x quality) | enable every ESLint rule at once |
| 2. Stop the bleeding | baseline + CI blocking **new** findings; automatic formatting | demand "100% clean before merge" |
| 3. Fertilise locally | boy-scout rule: each PR tidies the area it touches | a 4,000-line "refactor the module" PR mid-sprint |
| 4. Ratchet | one threshold per quarter (40 → 30 lines/function), shrink the baseline | set a standard and never measure it |
| 5. Vaccinate | Definition of Done + review checklist + tests on the PR | rely on individual conscientiousness |
| 6. Structure (when the code is stable) | declare layers, run `arch-scan` as a check, add one exact tool | reorganise the whole tree "to be clean" in one week |

Rule of thumb: **10–15% of sprint capacity** repays technical debt while the team still ships
features. Below 5%, the debt grows faster than the repayments and the plan is self-defeating.

## 7. Three misunderstandings to remove before teaching anyone

- *"Clean code = lots of abstraction layers + design patterns."* No. Clean code is **clear
  communication with the reader**. Patterns are targeted medicine, not vitamins; applying a
  pattern to a problem you do not yet have is speculative generality
  (see `14-design-patterns.md`).
- *"Fast code is dirty code; you clean it when you have time."* Dirty code is not speed, it is
  **credit**: 20% faster this sprint, 50% slower three sprints out. Kent Beck's
  "make it work, make it right, make it fast" is a *sequence*, not a menu.
- *"We have lint and formatting, so design thinking is optional."* The machine measures
  *shape* (length, parameters, duplication, import direction). It has no idea whether the
  business concept is in the right place. That is still a human review judgement — and it is
  exactly what `references/12-clean-architecture.md` is for.

## 8. A 10-minute team exercise (run it in a retro or a knowledge share)

1. Open the most-edited file of the last 3 months:
   `git log --format= --name-only --since=3.month.ago | sort | uniq -c | sort -rn | head`.
2. Count together: longest function in lines? how many nested `if`s? any magic number or magic
   string? how many tests import it?
3. Rewrite **one function** to the rules in `03-functions.md`, behaviour unchanged, tests untouched.
4. Run `cc-scan` on that file before and after; put both numbers on one slide.

What usually happens: the room concludes on its own that "refactoring was not hard, we just never
spent 20 minutes on it" — that conclusion is the deliverable, not the lecture. Then book the
next 20 minutes for the second-hot file; a standard without a calendar slot dies (see
`09-code-health-workflow.md`).
