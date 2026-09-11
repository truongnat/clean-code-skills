# Session 3 · Functions — small, one job, no hidden side effects

**Duration:** 60 minutes (the heaviest exercise in the course) · **Pre-work:** each person submits one
file containing a function of 60+ lines. **Output:** function thresholds enabled in CI for every
language in the repo.

## 1. Team thresholds (🔧 one-time decision, then machines enforce it)

| Criterion | Recommended | Warning | Blocks merge |
|---|---|---|---|
| function body lines | ≤ 20 | > 40 | > 70 |
| parameters | 0–2 | 3–4 | ≥ 5 (tests and boundary adapters exempt) |
| cyclomatic complexity | ≤ 6 | > 10 | > 15 |
| `if`/`for` nesting depth | ≤ 2 | > 3 | — |
| jobs per function | 1 | — | — |

Enable the same numbers in three places so nobody can "forget": `tools/clean-code.config.json`,
ESLint (`max-lines-per-function`, `max-params`, `complexity`, `max-depth`, `max-statements`), ruff
(`C901`, `PLR0913`, `PLR0912`, `PLR0915`), Checkstyle (`MethodLength`, `ParameterNumber`), Go
(`funlen`, `cyclop`, `gocognit`, `nestif`).

**Set the initial thresholds near your repo's 90th percentile, not at the ideal.** If today's median
function is 38 lines, blocking at 40 means hundreds of red CI jobs and a rule that gets switched off
by Friday; start at 80, ratchet per the plan in session 9, and the rule survives the year.

## 2. The four shapes that are wrong 90% of the time (5 seconds to spot)

```ts
// (1) three abstraction levels mixed: orchestration + parsing + I/O
function importOrders(path) { readFileSync…; split(",")…; db.createMany…; }

// (2) a boolean flag controlling behaviour
render(document, /* isPrint */ true)

// (3) a query that changes state
if (cache.getOrLoad(key)) { … }          // "get" that writes to the DB

// (4) an if wrapping the whole body instead of a guard clause
if (order) { if (order.items) { … 40 lines … } }
```

Ask the room which shape their submitted file has. Usually four hands for each; being able to name the
shape in five seconds is the skill, because it works on code you have not read yet.

## 3. The repair sequence (teach the order, not the result)

```text
1. Write a one-sentence docstring for the function. That sentence = the name of the ORCHESTRATOR.
2. Underline the verb phrases in the sentence -> those are the functions to extract.
3. Guard clauses first: pull every wrapping `if` up into an early return/throw.
4. Extract Method one step at a time: run tests -> commit. Repeat.
5. Bundle >3 parameters into an Options object (record / dataclass / type).
6. Move side effects into the application service; keep the computation pure.
```

A complete worked example — one 62-line function becoming five functions of ≤ 8 lines, side effects
left only in the orchestrator — is in `../skills/clean-code/references/03-functions.md` §5. The
pack's own legacy demo (`tools/demo/`) measures **72.0/100 before, 100.0/100 after**, and that is a
whole-folder number, not a cherry-picked file.

## 4. Exercise — 25 minutes, on each other's code

Swap files. Refactor the function you received following §3, **without changing behaviour**:

```bash
python3 ../../tools/cc-scan.py . --json | jq .score      # photograph the current state
npx vitest run <module> && python3 ../../tools/cc-scan.py <file>
```

Acceptance: tests green, `LONG_FUNCTION` = 0 on that file, the `cc-scan` score up. If the tests went
**red**, you changed behaviour: revert, write a characterization test first
(`../skills/clean-code-refactoring/SKILL.md` §4), then try again. That failure is the most valuable
twenty minutes of the course — whoever hits it never refactors without a net again.

Debrief with three questions: what made you stop? which extracted function has no good name (i.e. two
jobs still glued)? what would this look like at 1,500 lines instead of 60?

## 5. Command–Query Separation: how to answer the objection

> "But `save()` returns the entity so I can use it right away — that's convenient."

Convenient for one caller, expensive for the twenty future readers who must open the body to learn
whether `save` mutates. Two acceptable answers, pick one per team: `save(order): Promise<void>` and the
caller re-reads; **or** a name that shouts both jobs — `saveAndReturnId()`. The name is the contract;
no linter sees semantics, which is exactly why this line belongs in `CONTRIBUTING.md` and not in a
config file.

## 6. When short functions are the **wrong** answer (so this never becomes dogma)

- splitting one continuous algorithm into nine one-line functions → the reader jumps nine times and
  ends up slower;
- names that became `doStep1 / doStep2` → you moved lines, you did not remove knowledge;
- five-line functions that are 40% forwarding (middle men) → an extra layer, extra reading.

The test to apply in review: **"does the new function's name state a business rule?"** If not, do not
extract — and if the tool still complains, mark it
(`// cc-scan:allow LONG_FUNCTION — state machine loop, see ADR-0012`) rather than arguing in comments.

## 7. Closing check

1. Why is "≥ 5 parameters" a harder block than "45 lines"? (a swapped argument order is a silent bug; a
   long function is merely expensive)
2. Is `getOrCreateUser()` CQS-clean? (the name says query, the behaviour is a command: split it or
   rename it)
3. May a 90-line function stay? (a state-machine loop or a data table: yes, with an allow-comment, a
   reason and an ADR — `../skills/clean-code/SKILL.md` §7)

**Policy line for `CONTRIBUTING.md`:** *"Functions follow the §1 thresholds; the numbers live in
config, not in opinions; an intentional exception names the rule and the reason in one line; a
`refactor:` commit never contains a behaviour change."*

**If you only have 15 minutes:** do §4 on one file and enable `max-params` in CI. Parameter count is
the cheapest, highest-yield gate in this whole pack.

Materials: `../skills/clean-code/references/03-functions.md` ·
`../skills/clean-code/snippets/bad-vs-good.md` §3 · skill `clean-code-refactoring`
