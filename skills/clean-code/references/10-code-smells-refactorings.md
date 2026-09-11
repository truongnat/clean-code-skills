# 10 · Code smells → refactorings (lookup table)

> How to use it: see a smell → read the "Refactor" column → act **step by step**, tests after each
> step. No smell is obligatory unless it sits on your path of change.

## 0. Triage before you touch anything

A smell is a **hypothesis**, not a verdict: "this shape usually costs more than it saves". Before
fixing, three questions:

1. Is it on the file I am already changing, or on the path of the next requirement?
2. What does it cost me concretely (a bug last quarter? a 40-minute read? three copies of a rule)?
3. What is the smallest move that removes the cost?

Then pick your ladder rung — always the lowest that pays:
**rename → extract a function → move a method → introduce a type → split a class → open a seam →
move a boundary.** Skipping rungs (jumping to "we need a new module") is how clean-up PRs become
architecture reviews and die.

## 1. Function-level smells

| Smell | How you spot it | Refactoring | Machine check |
|---|---|---|---|
| Long Method | you scroll to read it | `Extract Method`, one step each | `cc-scan LONG/HUGE_FUNCTION`, `funlen`, `MethodLength`, `max-lines-per-function` |
| Too many parameters | callers must remember the order | `Introduce Parameter Object` | `TOO_MANY_PARAMS`, `max-params`, `PLR0913` |
| Flag argument | `f(true, false, true)` | split into two functions, or an enum | `BOOLEAN_PARAM` |
| Deep nesting | `if` four levels in | `Decompose Conditional` + guard clauses | `DEEP_NESTING`, `nestif`, `NestedIfDepth` |
| Switch on type | the same `switch (kind)` in 3 places | polymorphism, or a table | `COMPLEXITY`, `HARD_COMPLEXITY` |
| Temporary zoo | 12 locals, `t1`…`t3`, alive the whole function | `Replace Temp with Query`, extract | review |
| Hidden side effect | `getX()` writes to the DB | separate the command, rename honestly | review, `arch-scan` for the layer it implies |
| Repeated try/catch | six identical `catch` blocks | precondition checks, one `try` at the boundary | ruff `TRY300`, `no-useless-catch` |
| Loops that only filter/map | 8 lines doing `map`+`filter` | a pipeline (`filter/map/reduce`), or a named query method | review |
| Message chain | `a.getB().getC().doIt()` | move the behaviour onto the owner (`a.doIt()`) | review (Demeter, `06` §2) |
| Unreadable one-liner | you read it twice | split by step, name the middle values | `LINE_TOO_LONG`, review |

## 2. Class- and module-level smells

| Smell | How you spot it | Refactoring |
|---|---|---|
| God Class | > 400 lines, ≥ 3 reasons to change, 25 methods | `Extract Class` by reason for change; `Extract Interface` only when a test or a second adapter needs it |
| Feature Envy | a method uses another type's data more than its own | `Move Method` onto the data's owner |
| Data Clumps | `(from, to, tz)` always travel together | `Introduce Parameter Object` / a value object (`DateRange`) |
| Primitive Obsession | `String status`, `double money`, `int phone` | `Replace Primitive with Object` (`Money`, enum) |
| Anemic Domain | all logic in `XxxService`, entities are getter bags | move invariants and rules into the type; the service only orchestrates |
| Shotgun Surgery | one rule change touches 7 files | `Move Statements` into one policy (single source of truth) |
| Divergent Change | one file edited for 3 unrelated reasons | `Extract Class`, one per reason |
| Middle Man | a class that only forwards 8 calls | `Remove Middle Man`, call the real object |
| Inappropriate Intimacy | two classes poke into each other's internals | `Hide Delegate`, or make the relation one-way |
| Lazy Class | 3 lines, 1 method, its own file | `Inline Class` |
| Speculative Generality | an abstract base with one child "for later" | delete it; add it when the second child arrives (YAGNI) |
| Persistent Data Class | an object of fields that travels the whole app | give it behaviour, or split DTO from domain type |
| Comment smell | a comment narrating *how* | rename + extract, until the comment is unnecessary |

## 3. Architecture-level smells

| Smell | Symptom | Cure |
|---|---|---|
| Cyclic dependency | you cannot delete a file; tests must load the whole cluster | `Dependency Inversion` at the boundary; move the shared type down a layer |
| Leaky boundary | the domain imports `express` / `ResultSet` / `sqlalchemy` | push it into an adapter; the domain sees only its own port |
| Serialisation of everything | `any` / `Map<String,Object>` between layers | type at the edge, real types inside (parse, don't validate) |
| Golden hammer | every problem is solved with the same pattern | compare two candidates, pick the least exciting one that works |
| Premature abstraction | an interface with one implementation and a comment "for later" | inline or delete it; wait for variant two |
| God folder | `common/`, `shared/`, `core/` growing for every ticket | a bucket is not a module: name the concept, then place it |
| Big ball of mud | nobody can say where execution starts | `Strangler Fig` around the area you are changing; one ADR naming the target architecture |
| Distributed monolith | microservice boundaries with one shared DB, synchronous everywhere | name the true seams; the pack's answer is a modular monolith first (`13-architecture-patterns.md`) |

```bash
python3 tools/arch-scan.py src --fail-on error     # LAYER_CYCLE, UPWARD_DEPENDENCY, BOUNDARY_LEAK
npx madge --circular --extensions ts,tsx src
lint-imports                                        # the exact contract version, Python
```

## 4. Test smells (the ones that keep the code dirty forever)

| Smell | Why it is dangerous | Refactoring |
|---|---|---|
| Happy-path only | refactoring becomes suicide: nothing guards the error branches | one test per `catch` / `if err != nil` you ship |
| Mock everything | the test proves "code calls code"; any restructure breaks it | test behaviour through the real API; fake at the edges (DB, network, clock) |
| Unreadable assertion | `assert(3)` protects nothing anybody can name | name it: `expect(receipt.totalVnd).toBe(480_000)` |
| Order/time dependent | flakes → the team starts ignoring CI | inject `Clock`/`Random`, fixed seeds, no file-order assumptions |
| Copy-paste fixtures | one fixture change needs ten edits | a test data builder: `aValidOrder().withQty(3).build()` |
| 90% coverage, no assertions | a pretty number, zero protection | cheap mutation check: break one line, see if anything turns red |
| Slow suite | people run it less, then not at all | keep unit tests in-process and < 2 s; move I/O to an integration lane |
| Test named after the method | `testPlaceOrder` says nothing about behaviour | name the rule: `"rejects a coupon already redeemed by this customer"` |

A suite is part of the code: it obeys the same rules about size, naming and duplication — with one
exception, documented on purpose: **clarity beats brevity in a test**, so a 30-line explicit test
with a self-documenting arrange is better than a clever 10-line one (`configs/js/eslint.config.js`
relaxes `max-lines-per-function` and `max-params` for test files for exactly this reason).

## 5. Fifteen-minute worked recipe: the 120-line function

```text
0. A clean tree. Current tests MUST be green. Record lines + branches (your before number).
1. Read it once, change nothing. Write down the 3-7 "steps" the function performs.
2. Extract by step. For each one:
     - Extract Method (IDE, not hand-edit), name it after the step (the name must say the job)
     - run the tests -> commit "refactor: extract X from Y"
     If you cannot find a name, that step is still too big: split it again.
3. Guard clauses at the top of each new function: `if (invalid) throw/return` beats nesting.
4. Delete the temps that no longer earn their keep (Replace Temp with Query / Inline Temp).
5. Any new function used from one place only -> make it private and put it under its caller.
6. Re-measure: functions <= 40 lines? branches <= 10? cc-scan score up? arch-scan unchanged?
7. Only after step 6 may behaviour change - and that is a different PR.
```

Expected shape of a good run (from the pack's own demo, `tools/demo/`): **72.0/100 → 100.0/100**
with the behaviour frozen — and the *diff* of each commit readable in a minute. If your run ends with
the same score, you moved knowledge instead of removing it: pick a different refactoring (§0 ladder,
next rung).

**Insurance when there are no tests at all** (legacy):
1. write a **characterization test**: call the function with 5–10 real inputs, *photograph* the
   current output (bugs included), assert it verbatim — this is a behaviour lock, not a correctness
   claim;
2. or a golden file / snapshot, diffed in review;
3. refactor between photographs. Every assertion you change is a behaviour change, and you must say
   so in the PR text;
4. keep the fixture data production-shaped: 50 real rows beat 3 invented ones, because invented
   rows only exercise the paths you already thought of.

## 6. Naming the refactor, so commits and PRs read like a table of contents

```text
refactor(billing): extract PricingPolicy out of OrderService
refactor: replace flag argument with renderForPrint / renderForScreen
refactor: introduce Money value object (replaces double + currency string)
style: rename usrPrflNm -> userProfileName (no behaviour change)
test: characterization tests for legacy TaxCalculator (behaviour snapshot)
```

Rule: a `refactor:` commit contains **no** behaviour change. If a reviewer sees a `-`/`+` pair that
could alter output inside a `refactor:` commit, that is a latent bug — split it, review it twice,
bisect it once. (Conventional Commits is not required by this pack; consistency in prefixing is what
buys you `git log --grep refactor` during an incident.)

## 7. Smells that itch — record them, do not fix them inline

Why not: a feature PR plus an unrelated refactor is a 900-line diff nobody reviews properly, and it
kills `git blame` for the lines you "only moved".

Three professional responses, in increasing cost:
1. **in-PR separation** — "commit 1 refactor, commit 2 feature; I review them independently";
2. **a written marker with a ticket** — `// TODO(refactor, AC-1234): fold VAT into TaxPolicy`;
3. **a small issue** with three lines (symptom, cost, suggested rung from §0) and a link in the PR
   thread — then merge and move on.

What is not acceptable is the fourth option people actually choose: saying nothing and letting the
smell sit uncounted until the module is rewritten.

## 8. Verify with numbers, not feelings

```bash
python3 tools/cc-scan.py src/billing --json | jq '{score, error: .counts.error, warning: .counts.warning}'
ruff check --select C901,PLR0912,PLR0915,PLR0913 src/billing
npx eslint src/billing --rule '{"complexity":["error",10],"max-lines-per-function":["error",40]}'
python3 tools/arch-scan.py src --fail-on none | sed -n '1,12p'      # structure did not rot on the way
```

If the score did not rise, you relocated knowledge rather than reducing it. The success signal that
no tool measures but every reader feels: **the number of lines you must read to understand one
business flow went down**, and the tests are still green. Say that number in the PR description —
"understanding the pricing flow: 1 function of 120 lines → a 6-line outline + 4 named steps" is the
most convincing sentence a refactor PR can contain.

## 9. When the smell is the tool's, not yours

Machine findings are heuristics. Real examples you should be able to defend:

| Finding | Why it is fine | What to do |
|---|---|---|
| `DUPLICATE_BLOCK` on two 8-line validation blocks | they look alike today and will diverge tomorrow (different rules, different owners) | keep both; note it in the PR text so the next reader does not "helpfully" merge them |
| `LONG_FUNCTION` on a declarative config table | the length *is* the readability (a rate table, a state-transition map) | `// cc-scan:allow LONG_FUNCTION — table by design, see ADR-0012` |
| `MAGIC_NUMBER` on a Go `const vipRate = 0.9` | the scanner exempts `UPPER_SNAKE`; Go uses `camelCase` | allow-comment, or `magicNumbersAllowed` in config — measured case in `configs/go/README.md` |
| `UNCLASSIFIED_FILES` after a folder rename | the layer config still names the old path | fix the config (that is the drift detector working) |
| `COMPLEXITY` on an exhaustive `match` over a sealed union | the branches are the design; each is one line | raise the language linter's threshold for that file, or split the mapping into a table |

The discipline that keeps this honest: an exception names **one rule**, covers **one range**,
carries a **reason**, and is visible in `git log` (a config `skipRules` entry for anything repo-wide).
A blanket disable is not an exception, it is the deletion of the standard with extra steps — and the
next person inherits a repo where nobody knows which rules still apply.
