# Self-review before opening a PR — 10 minutes that save two review rounds

> Run in order. Steps 1–4 are machines; 5–8 are you reading your own work as a stranger.

## 0. Branch hygiene (30 seconds)

- [ ] rebased/merged current base, so the reviewer sees your change, not a rebase artefact
- [ ] only files related to the ticket in the diff (`git diff --stat origin/main...HEAD`)
- [ ] commit messages readable on their own; `refactor:` commits contain no behaviour change
- [ ] branch name or PR title carries the ticket id

## 1. Machine: format + lint + scan (not negotiable)

```bash
# JS/TS
npx prettier --write . && npx eslint . --fix && npx eslint . --max-warnings=0

# Python
ruff check --fix . && ruff format . && mypy .       # or: bash configs/python/lint.sh

# Go
gofmt -w . && golangci-lint run

# every language: the team's clean-code standard
python3 tools/cc-scan.py . --fail-on error

# and the structure, if you added a folder or changed imports
python3 tools/arch-scan.py src --fail-on error
```

Run the tools on **the files you touched**, then on the repo once — the first catches your
violations, the second catches the ones your change created elsewhere (a new upward edge, a
duplicate that now exists in two files).

## 2. Machine: dead code and leftovers

```bash
rg -n "console\.(log|debug|info|trace)\(|debugger\b|\.only\(" src      # JS/TS
rg -n "System\.(out|err)\.print|printStackTrace\(\)" src               # Java
rg -n "fmt\.Print|println\(" src                                       # Go
rg -n "^\s*(print|pprint)\(" src                                       # Python debug
rg -n "TODO|FIXME|XXX|HACK" src | grep -v -E "(AC|JIRA|#[0-9]{3,})"    # TODO without a ticket
rg -n "(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]{8,}" src   # suspicious literals
```

Anything the last pattern hits is not a style issue: remove the secret, rotate it, and if it was ever
committed, treat it as leaked.

## 3. Machine: tests, and coverage of the lines you changed

```bash
npx vitest run --coverage          # or: pytest -q --cov=src --cov-report=term-missing
```

Open your own files in the report: **every red line inside your diff** needs a reason — untestable
by construction (say which), or dead and therefore deletable. Then run the suite **twice in a
different order** (or with `-p randomly`); a test that fails second is a bug in the test, and you
just saved the team a week of "flaky" labels.

## 4. Machine: the diff you are about to show

```bash
git diff origin/main...HEAD --stat
git diff origin/main...HEAD
git log --oneline origin/main..HEAD
```

Read the diff, not the files — reading files lets your brain fill in what you meant.

## 5. Human: six questions about your own code

1. Did I leave anything because **I** already know it? → rename, extract, or write the why.
2. Any function over 40 lines or over 3 parameters? → split, or add one sentence justifying why not.
3. Any `catch` / `_ = err` / `except: pass`? → handle it, or point at the ticket that explains why not.
4. Did I copy logic from another file? → extract it, or write why the copy is temporary (with an id).
5. Which name will I not understand in three weeks? → change it now; now is ten times cheaper.
6. What in this diff is **not** in the ticket? → move it out into its own PR.

## 6. Human: three design questions

- If a new variant arrived (a fee kind, an order type, a report format), how many files would I edit?
  **More than three** means the design is scattered, not that the task is big.
- Can a newcomer read `createOrder()` and tell what it does, what it calls and how it fails?
- Where did I write "refactor later"? → open the issue with a link now, or spend the ten minutes.
- Does this change belong on a path the dependency rule cares about? Run `arch-scan`: a new
  `domain → infrastructure` import is a design answer, and it will outlive your feature.

## 7. The PR body: three blocks (your reviewer reads this before the code)

```md
## Why
The shipping-fee rule changes: free from 500k, and the old logic was hard-coded in 3 places.

## What
- one source of truth: `PricingPolicy.freeShippingThresholdMinor`
- `checkout.ts` and `invoice.ts` call the policy instead of computing it by hand
- 6 boundary tests (499_999 / 500_000 / 0 / empty cart / single line / unicode sku)

## Risk & evidence
- behaviour changes **on purpose** for orders 300k-500k (~2% of shipping revenue); finance informed
- no migration; feature flag `pricing.free_ship_500k` (off in prod, on in staging)
- `cc-scan` 96/100 (was 71) · `arch-scan` 100/100, no new edge · billing coverage 91%
- staged run: requestId `cc-8842`, mismatch rate 0 over 1,000 sample orders
```

Three rules for the body: state the **intended** behaviour change (so a reviewer cannot mistake it for
a regression), give the **evidence** (commands run and their numbers, not "tested locally"), and
name the **rollback** (a flag, a revert, or "irreversible because of X").

## 8. Self-scoring rubric — under 8, you are borrowing the reviewer's time

| Criterion | 0 | 1 | 2 |
|---|---|---|---|
| names clear, no magic values | you have to guess | mostly clear | reads in one pass |
| functions ≤ 40 lines, ≤ 3 params | several violate | one, with a reason | none |
| failures carry information | a swallow somewhere | logged, no context | typed + cause + test |
| tests prove behaviour | none | happy path only | behaviour + errors + boundaries |
| no dead code or debug logs | several | a couple | zero |
| layering respected | mixed | one deviation, flagged | clean, no cycle in `arch-scan` |
| PR body explains why/risk/evidence | absent | partial | complete, with numbers |

14/14 means: request the review. Anything ≤ 9 means one more pass is cheaper than one more round
trip — and the honest signal is not the score, it is whether you could have written the PR body
**before** writing the code. If not, the change was still being designed while you typed it.
