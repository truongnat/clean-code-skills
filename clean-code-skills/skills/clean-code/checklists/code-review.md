# PR review checklist (clean code) — five minutes, in cost order

> The order below is deliberate: expensive → cheap. A design error costs two weeks, a formatting
> error costs two seconds and the machine does it for free. Do not spend 30 minutes of review on
> what ESLint catches.

## 0. Before reading any code (30 seconds)

- [ ] One goal per PR? **> 400 changed lines or > 15 files** → "please split before I read it".
  A mixed refactor+feature PR is two PRs; you cannot review behaviour inside 900 lines of moves.
- [ ] Ticket and a "what/why" description? Missing → ask, never guess. If the description does not
  mention a file you see changed, that file is scope creep.
- [ ] CI green (build, tests, lint, format, `arch-scan`)? Red → hand it back; do not read code that
  does not compile.
- [ ] Format noise in the diff (`prettier`/`gofmt` not run)? One sentence: "run `make fmt`".

```bash
git diff --shortstat origin/main...HEAD                                   # size
git diff --name-only origin/main...HEAD | wc -l                           # files
python3 tools/cc-scan.py $(git diff --name-only origin/main...HEAD |
  grep -E '\.(ts|tsx|js|jsx|py|java|kt|go)$') --fail-on error --json -o review.json
python3 tools/arch-scan.py src --fail-on none | sed -n '1,12p'           # structure, if folders moved
```

## 1. Design and boundaries — the part only a human can do

- [ ] Is new code in the **right layer**? (domain importing DB/HTTP, a controller holding a business
  rule, logic parked in `utils` are all blockers-by-definition, not taste)
- [ ] Does a new concept have **one owner**, or does it live in three files?
- [ ] Any **copy-pasted business logic**? A real DRY violation → one place, others derive.
- [ ] A new abstraction with **one implementation and no second user**? YAGNI → ask for it to go.
- [ ] New public API: versioning, compatibility, migration path considered? A published contract is
  the one place YAGNI does not apply.
- [ ] New **seam** (port/interface): does the domain own it? If infra owns it, the dependency points
  the wrong way and the layer rule will rot quietly.

## 2. Data

- [ ] States are enums / sealed types / unions, not `string` or magic ints?
- [ ] Money, durations and measurements carry a **unit in the type or the name**
  (`amountMinor`, `timeoutMs`, `weightKg`)? Float money is a blocker, not a nit.
- [ ] Does the object hold its own **invariant**, or must every caller remember a check?
- [ ] Defaults defined **once** (schema, factory, config), not repeated in four call sites?
- [ ] Migration: reversible or explicitly documented as one-way, with a data-backfill plan for rows
  that already exist?

## 3. Functions

- [ ] ≤ 40 lines, one level of abstraction, name states the **intent**?
- [ ] ≤ 3 parameters? No boolean flag argument (split, or an enum)?
- [ ] Side effects visible in the name or the docs? A query does not mutate.
- [ ] A compound condition extracted into a predicate (`isEligibleForZeroVat`) rather than 4 lines of
  `&&`/`||`?
- [ ] Guard clauses up front; nothing nested past level 2-3?

## 4. Failure handling

- [ ] Specific exception types with a message **you can act on** (id + numbers + next step)?
- [ ] Every `catch` does something: log-and-throw-once, wrap with cause, or handle with a written
  reason. `catch {}` is a blocker in this pack — `cc-scan` scores it at error for that reason.
- [ ] No catching the root (`Exception`/`Throwable`/bare `except:`), no `except: pass`, no `_ = err`?
- [ ] Third-party calls: timeout + bounded retry + backoff, and **no** retry of business rejections?
- [ ] Fallback/degraded paths emit a **metric**, not only a log line, and the alarm has a runbook line?
- [ ] Error responses never leak internals (stack, SQL, secrets) and carry `requestId`?

## 5. Tests

- [ ] Every behaviour change has a test that proves it (a pure refactor needs no new test — that is
  the point of separating them)?
- [ ] Error branches and boundaries covered (0 / empty / negative / unicode+diacritics), not only the
  happy path?
- [ ] Assertions go through the **public API**: no private calls, no asserting on log strings?
- [ ] No sleeps, no randomness, no real clock (injected `Clock`, fixed seed)?
- [ ] Test names read as a **specification** ("a stock shortfall reports the remaining quantity")?
- [ ] Coverage on new code ≥ 80%; a red suite is never "re-run until green"?

## 6. Hygiene (20 seconds with tools)

- [ ] no leftover `console.log` / `print` / `fmt.Print` / `System.out`
- [ ] no commented-out code, no `*.old.ts`, no algorithm-narrating block comments
- [ ] every `TODO` has a ticket id (`TODO(AC-1234, owner)`)
- [ ] **no hardcoded secrets** — key, password, token, connection string. This one is a hard block
  with no negotiation: rotate the credential, then clean the history
- [ ] any new dependency explained (size, license, maintenance, does something in the stack already
  do this?) — a 40-kb package to `padStart` a string is a `should`, a second HTTP client is a `blocker`
- [ ] no lockfile churn beyond the dependency being added

## 7. Readability (maintainability)

- [ ] Would someone who did not write this understand it in under 10 minutes? If you needed three
  questions from the author, the code needs names or docs, not a verbal explanation.
- [ ] Names use the team's **ubiquitous language**, not `data2`/`flag`/`tmp`?
- [ ] New config or feature flag has a safe default and is described where it is declared?
- [ ] A large rename or API shift has a deprecate/migrate plan (expand → contract)?
- [ ] Comments left in the diff explain *why*; nothing in the diff is "I know this is bad"?

## 8. How to phrase findings

| Level | Prefix | Example |
|---|---|---|
| must fix | `blocker:` | "`catch` swallows the timeout → the customer sees a stuck order and the log has nothing" |
| should fix | `should:` | "extract `feeOf` into a policy — the formula is now copied in `checkout.ts`" |
| small note | `nit:` | "`res` → `response` (greppable)" — the author may skip it, no explanation owed |
| want to understand | `question:` | "why `<=` here and `<` in `invoice.ts`?" |
| reinforce | `praise:` | "this builder made the test readable at a glance; let's use the shape in billing too" |

Frame: **Observation → Consequence → Proposal (or question)**. Link the rule in the skill/playbook
instead of offering an opinion, and never say "change it" without the *because*. Anything you cannot
place in this table is taste — keep it.

## 9. Verdict (write it out, always)

- ✅ **Approve** — good to merge
- 💬 **Comment** — suggestions, not blocking
- 🔄 **Request changes** — has `blocker`s; list at most five, ordered by damage
- ⏸ **Split first** — scope too wide to review honestly

Then two closing lines that cost you nothing and change the culture: **one specific `praise`**, and
**the next step you expect** ("fix 1 and 3, then I'll approve without re-reading the rest"). A
review that ends with 14 open items and no path is a demotivating to-do list, not a decision.

## 10. Special cases

**A dependency bump or lockfile change**: read the upstream diff or release notes, not just the
version number; check license and transitive size (`npm why <pkg>`); ask whether the project's
existing tooling already covers it. **A schema migration**: two PRs when possible (expand then
contract), no destructive statement in the same release as the code that depends on it, and a
written backfill with a row count. **A hotfix**: allowed to skip §3 and §7, never §4 and §5 — and it
carries a follow-up ticket in the PR body before it merges. **An AI-authored PR**: same standard, plus
verify every imported symbol, config key and test id actually exists, and watch for the shapes the
models overproduce (indirection without a second implementation, docstrings restating signatures,
`try/except: pass`). **Your own PR**: run the checklist with the files closed, from memory — what you
cannot recall is what the reviewer will not find.
