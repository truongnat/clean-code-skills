# 02 · Extract function — split a long function without changing behaviour

```text
PROMPT
───
Refactor the function I paste under one rule: EXTRACT ONLY, NO BEHAVIOUR CHANGE, NO CHANGE TO THE
EXTERNAL API.

Hard constraints:
- Each step outputs a diff of at most 40 lines; each new function is named <verb + object> and
  states ONE business rule (`step1`, `doPart`, `handleData` are rejected).
- No new boolean flags; never more than 3 parameters (if you need more → propose a Parameter
  Object and ask me before doing it).
- Guard clauses are allowed, but turning `if (valid) {…}` into `if (!valid) return;` must be
  called out as its own step.
- If a block needs a **shared mutable accumulator** and extracting it would mean threading 4
  parameters → STOP and tell me why that is the wrong seam.

The procedure you must follow (print all 5 steps):
1. One-sentence summary of what the function does → that is the name of the coordinating function.
2. List the "steps" you found + the line count of each + its complexity (branch count).
3. For each step: code BEFORE / AFTER, and why this seam is safe (which variables cross it, which
   side effects sit on each side).
4. The commit order you suggest (one commit per step, message prefixed `refactor:`).
5. The tests that must exist **before** extracting; if I have none → propose characterization tests
   (with sample inputs taken from the code I pasted) and state the risk of extracting untested.

Language: [TS/Python/Java/Go] · Framework: [Next/Express/FastAPI/Spring/stdlib]
I DO/DO NOT have tests for this function: [yes — 6 unit tests | no]

CODE:
[PASTE THE FUNCTION]
───
```

## Sample output (abridged)

```text
1) Summary: "price an order, then persist it and notify"
   → coordinating function: `placeOrder`
2) Steps: validateCart(9 lines, 2 branches) · priceCart(14, 6) · persist(11, 1 try/catch) · notify(7, 2)
3) priceCart: crossing variable = `totalVnd`; side effects = NONE (pure) → safe seam, the test
   needs no mocks.
   persist: side effects = DB write + event publish; runs AFTER priceCart, no data loop → safe seam.
   validateCart + priceCart: do NOT split these further — both read `items` and share `lineTotals`;
   the natural seam is `pricingPolicy`.
4) Commits: `extract priceCart` → `extract persistOrder` → `guard clauses in placeOrder`
5) Tests needed: empty cart, out of stock, VAT boundary, DB error. You have no DB-error test →
   write `expect(placeOrder).rejects.toThrow(OrderPersistenceError)` before extracting persist.
```

## Minimum input

- the **entire function**, including its closing brace — a half-pasted body produces seams that do
  not exist;
- whatever it **calls and mutates** that is not obvious from the body (a module-level variable, an
  injected client), or the safety analysis in step 3 is fiction;
- **whether tests exist**, honestly. "No tests" changes the answer from a refactor plan into a
  characterization-test plan, and that is the correct answer;
- the **language and runtime**, because what is safe to extract differs between a `goroutine`, an
  `async` closure and a plain method.

## Output acceptance criteria

- [ ] all 5 steps present, in order — a model that jumps straight to code skipped the safety work;
- [ ] step 3 names the crossing variables and the side effects for **every** seam, not just the
      easy one;
- [ ] at least one seam is rejected, or the model says explicitly that every candidate seam is safe;
- [ ] no new function takes a boolean parameter, and none is named after a step number;
- [ ] the "AFTER" code is complete enough to paste — no `// … rest unchanged` inside a body you
      are meant to replace;
- [ ] behaviour is identical: same ordering of side effects, same exceptions, same return values
      for the same inputs. If the model changed one, it should have flagged it as a separate step.

## Keeping it from inventing symbols

```text
Rules on evidence:
- Extract only from the code I pasted. Every "AFTER" body must be made of lines that appear in the
  "BEFORE", reordered at most — if you need a line that is not there, mark it NEW and justify it.
- Do not invent helper functions, utilities or framework calls to make the result shorter. If a
  clean extraction needs a helper I do not have, name it and leave a stub with its signature.
- Do not assume what a function I called (but did not paste) does. If a seam's safety depends on
  it, list it under "Files I need to confirm this seam".
- End with: "Lines in AFTER that existed in BEFORE: N/M. New lines: list them."
```

## Tips

- Work in a loop: after each answer run the tests and `cc-scan`; if the score does not move, paste
  it back with "`COMPLEXITY` is still 14, find a different seam".
- Add a closing request: `"After extracting, which functions are ≤ 8 lines with a single caller?
  Propose inlining or keeping them (give the readability reason)."` — that is what stops you ending
  up with twelve one-line functions.

## Verification

```bash
python3 tools/cc-scan.py <file> --no-baseline   # LONG_FUNCTION / COMPLEXITY / DEEP_NESTING gone?
npx vitest run <file>.test.ts                   # or pytest / go test — behaviour unchanged
git diff --stat                                 # each commit small enough to revert alone
```

Related: `../skills/clean-code-refactoring/SKILL.md` · `08-legacy-refactor-plan.md` ·
`07-testability.md`
