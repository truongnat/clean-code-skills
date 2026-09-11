---
name: clean-code-review
description: >-
  Review a pull request, diff or file against the clean-code standard: find design
  flaws, magic values, oversized functions, hidden side effects, swallowed errors
  and missing tests - then write severity-graded review comments (blocker / should /
  nit) that point at the exact line. Use when the user says "review this code",
  "check my PR", "look at the diff before merge", "assess code quality", when a PR is
  about to be opened, or when a team needs review criteria and a rubric.
metadata:
  version: "1.1.0"
  companion: "clean-code"
---

# Clean Code Review

> **Scanner path:** commands below assume `tools/cc-scan.py` / `tools/arch-scan.py` are in the
> repo. If they are not, the same scanners may be on `PATH` as `cc-scan` / `arch-scan` (identical
> flags) — see `INSTALL.md` §1b. If neither exists, ask for the report instead of guessing numbers.

Sibling of `clean-code`. The goal: **find the 3 things worth fixing in 30 minutes**,
not write 300 comments about style. A review that cannot be prioritised is noise that
the author will negotiate away one line at a time.

## 0. Severity vocabulary (use these words only)

| Level | Meaning | Effect on merge |
|---|---|---|
| **blocker** | wrong, lossy, unsafe, or violates an accepted decision (ADR, layer rule, security) | must be fixed here |
| **should** | correct but expensive to live with: unreadable name, 6 params, no test on the error branch | fix here, or open a ticket the author owns |
| **nit** | preference-level, no measurable cost | optional; say "take it or leave it" |
| **question** | you do not understand the intent | the author answers; not a change request |
| **praise** | something worth copying by the rest of the team | always specific, never generic |

Anything you cannot place in this table is not a review comment. A finding without a
**consequence** is a preference: demote it to `nit` or delete it.

## 1. Mandatory flow (in order)

### 1.1 Establish scope before reading a single line

```bash
git diff --stat origin/main...HEAD                      # size and shape of the change
git log --oneline origin/main..HEAD                     # is this one commit or a pile?
python3 tools/cc-scan.py $(git diff --name-only origin/main...HEAD |
  grep -E '\.(ts|tsx|js|jsx|py|java|kt|go|cs)$') --json -o /tmp/review.json
python3 tools/arch-scan.py src --fail-on error           # only if folders or imports moved
```

- **> 400 changed lines** *and* refactor mixed with feature → your first comment is
  "please split the PR", not a line-by-line review. State the split (refactor PR, then
  behaviour PR).
- `cc-scan` red at `error` on a changed file → the first legitimate `blocker`; cite the
  rule ID and line, do not paraphrase.
- `arch-scan` red → blocker **only** when the PR introduces the edge. A pre-existing
  upward dependency belongs in an issue, not on this author's back.
- No tests changed, but behaviour changed → that is a blocker by itself, regardless of
  anything else you found.

### 1.2 Group the machine findings so they cost you no reading time

```bash
jq -r '.findings | group_by(.rule)[] | "\(.[0].rule): \(length)"' /tmp/review.json | sort -t: -k2 -rn
jq -r '.findings[] | select(.severity=="error") | "\(.file):\(.line) \(.rule)"' /tmp/review.json
```

### 1.3 Read expensive → cheap

1. **Boundary / layer**: does the domain import DB or HTTP? Does a controller hold
   business rules? Is new logic in a module or in a "shared" utility nobody owns?
2. **Data model**: `string status` instead of an enum? `double money` instead of `Money`?
   nullable field that means "deleted"?
3. **Signature**: ≤ 3 parameters? does a public function mutate arguments or global state
   without saying so? any boolean flag argument?
4. **Errors**: does every `catch` do something? is the cause kept? do retries have a cap
   and backoff? is a partial write possible?
5. **Tests**: one test per behaviour change? are the error and boundary branches covered,
   not only the happy path?
6. **Readability**: name lies about what the code does, or is ungreppable. Comment only on
   *meaning*, never on taste.
7. **Style/format**: **stay silent** — the machine handles it. If the formatter complains,
   the fix is "run the formatter", not a review thread.

### 1.4 Apply the checklist and the template

`../clean-code/checklists/code-review.md` (9 sections). For every finding answer, in one
line each: **Observation → Consequence → Proposal**. If the consequence is empty, delete
the finding. Write comments with `../clean-code/templates/pr-review-comment.md`.

## 2. How to conclude

| Situation | Verdict |
|---|---|
| Logic error, data loss, swallowed error, secret in code, layer violation | 🔄 Request changes — at most 5 `blocker`s, ordered by damage |
| Correct but expensive to read | 💬 Comment: "not blocking, but in 3 weeks line 42 costs an hour to decode; here is the shape I would prefer" |
| Design contradicts an accepted ADR | 🔄 blocker + link the ADR + ask "did something change our mind here?" |
| Genuinely good code | ✅ Approve + one specific `praise` (name what to copy) |
| You lack context | ❓ "question: why `<` here but `<=` in `invoice.ts`?" — never guess in a comment |
| 15+ findings | Approve/request on the 5 most expensive + one line: "10 more nits collected at the bottom, safe to ignore" |

**Cap your own output.** More than ~15 findings means either the PR is too big (say that)
or you are reviewing taste (stop).

## 3. Rules that keep the review human

1. **Cite, don't judge.** Every comment carries `file:line` and a rule or document link.
   No link → it is a preference; label it `nit` or keep it to yourself.
2. **Do not silently rewrite it in your head and then declare it wrong.** Try to write the
   one-line fix. If you cannot produce it quickly, that is a `question` for the author, not
   a critique.
3. **Never comment what a tool enforces** (indent, quotes, trailing comma, line length).
   If you find yourself doing it, the real finding is "this repo is missing a hook".
4. **A repeated problem belongs to the repo, not the PR.** Three PRs with the same smell →
   open one issue "add rule X to config / session Y in the playbook" and stop commenting it
   the fourth time.
5. **Attack the code, protect the person.** Write "this function" not "you". Ask about
   constraints you cannot see (deadlines, legacy, a ticket you have not read).
6. **Do not smuggle behaviour changes into review.** A refactor suggestion ships as
   "open an issue, separate PR", never as "while you're at it".
7. **Respond to pushback with data or acceptance.** If the author has a reason you did not
   know, say so in the thread and move on; if you cannot prove the cost, drop the comment.

## 4. Reviewing AI-generated or very large code

Same rules, two additions: (a) **verify existence before trusting it** — every imported
symbol, config key, API name and test ID the model produced must be checked with `rg`; a
plausible-looking test that never runs is worse than no test; (b) **check for the shape the
model loves**: 12 tiny one-line indirection files, `Handler`/`Manager`/`Util` names,
`try/except: pass`, docstrings restating the signature, and confident comments about code
that does not exist. None of that is a blocker by itself; it is a `should` about
substance-over-structure, citing `../clean-code/references/14-design-patterns.md`.

## 5. Expected output

```md
## Review: #567 — pricing policy
**Verdict:** Request changes (1 blocker, 3 should)

**blocker**
1. `checkout.ts:42` swallows `TimeoutError` → order is created with tax=0 and nothing is
   logged. [07-error-handling.md]  Fix: log + rethrow wrapped, or handle with a reason.

**should**
2. `feeCalculator.ts:8` 6 params + 1 boolean → Parameter Object. [03-functions.md]
3. `price.ts:30-90` 61-line function, 4 levels of nesting → extract the guard block.
4. `taxProvider.ts` new upstream call has no timeout, no cap on retry → 503 storms
   become retry storms. [09-code-health-workflow.md]

**praise**
- `MoneyMinor` introduced with rounding at the edge only; worth copying in billing.

**numbers**
- cc-scan: 88/100 (base 74) · new errors: 0 · warnings: 4 (2 pre-existing, in baseline)
- Coverage billing: 91% → 88% (new renderer untested) → AC-1241
- arch-scan: 94.0/100, no new edge (`application → domain` only)
```

## 6. Score your own review (once a quarter, honestly)

- Did the author **fix things faster** because of your comments? Count review rounds per PR.
- Any comment you would not say out loud in front of the team because it is personal taste? → delete it.
- Did you miss something CI caught, then comment formatting instead? → the machine does
  formatting; your job is design, intent and risk.
- Ratio check: `blocker + should` vs `nit`. A healthy review is mostly the first two.
- Do your findings cite rules? If a reviewer two weeks later cannot find the rule text,
  your comment created a legend, not a standard.
