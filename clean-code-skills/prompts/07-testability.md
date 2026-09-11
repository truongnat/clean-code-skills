# 07 · Testability unlock — code you cannot test is code designed wrong

```text
PROMPT
───
The function/class I paste is VERY hard to unit test. Your job: find the **design cause**, not to
write a test that mocks 12 layers.

Step 1 — Diagnose (each item: yes/no + the line that proves it):
- a dependency `new`ed or imported mid-function (DB, HTTP, clock, randomness, filesystem)
- reads/writes global state or a singleton
- the function does both a query and a command
- a condition that depends on "now" / the current timezone
- the function is ≥ 40 lines or does ≥ 3 jobs
- the return value is not enough to assert on (it only logs, or mutates its input)

Step 2 — Propose ONE of 4 techniques, choosing the one that changes the API least:
(a) Introduce Seam: pass the dependency in (constructor/parameter) — keep the public signature
    if you can
(b) Extract Pure Core: split out the calculation, leave the I/O in a wrapper
(c) Return a Result instead of mutating: the function returns something assertable
(d) Introduce an injected Clock/Random/IdGenerator (a one-method interface — do not
    over-engineer it)
Give a diff for each technique and "which unit test this change makes possible".

Step 3 — Write the tests (AAA shape, assert THROUGH THE PUBLIC API, do not mock what we own):
happy path · every error branch · boundaries (0/empty/negative/one element/Unicode/exactly the
threshold) · idempotency.

Step 4 — State the trade-off plainly: which technique makes the production code *weirder* (e.g.
having to pass 5 dependencies into one function) → if so, propose redesigning the function's scope
instead of forcing the test.

Test framework I use: [vitest | jest | pytest | junit | go test]
CODE:
[PASTE THE CODE]
───
```

## An example of a correct diagnosis

```text
- Singleton: line 8 `db.query(...)` inside `PricingPolicy` → the core is not pure (b1)
- Time: line 21 `Date.now()` → the test goes flaky after midnight (d)
- Mutates its input: `applyDiscount(order)` changes `order.totalVnd` and returns `void` → asserting
  means reading the object being mutated (c): return a new `PricedOrder`
- 3 jobs: validate + price + notify (b)
Fix order: (b)+(d) first — cheap and no API change; (a) later because 5 callers depend on it.
```

## Minimum input

- the function **and its constructor/module scope** — the singleton or the imported client is
  usually declared outside the function, and that is the diagnosis;
- the **call sites count** for anything whose signature would change (`rg -n "<name>(" src | wc -l`),
  because that is what decides between (a) and (b);
- your **test framework**, so the step-3 tests are pasteable rather than pseudo-code;
- any existing test file for this code, even a bad one. "Tests exist but mock everything" is a
  different problem from "no tests", and needs a different answer.

## Output acceptance criteria

- [ ] every step-1 item answered yes/no with a line number for each yes — no unproven diagnosis;
- [ ] exactly one technique recommended as first, with the API-change cost stated;
- [ ] the tests assert **business outcomes**, not call order. `expect(spy).toHaveBeenCalled()` as
      the only assertion is a failed answer;
- [ ] nothing we own is mocked — only the real boundaries (clock, network, DB, filesystem);
- [ ] boundary tests cover threshold −1 / = / +1, not just the happy path;
- [ ] step 4 is present and honest. An answer where every technique is free is an answer that did
      not think about production code.

## Keeping it from inventing symbols

```text
Rules on evidence:
- Diagnose only from the pasted code. Every "yes" cites a line number and quotes that line.
- Do not invent the interface of a dependency you cannot see. If a seam needs one, define the
  minimal interface yourself and mark it NEW, listing the methods you assumed it has.
- Tests may only call functions and fields that exist in the paste (or that your own diff created).
  Do not use a test helper, factory or fixture from my repo that I did not show you.
- Do not assume the assertion API of my framework beyond its documented basics; if you need
  something exotic, say so instead of guessing a method name.
- End with: "Diagnoses with a quoted line: N/N. Symbols used in the tests that I did not paste: list them."
```

## Tips

- If the model produces tests that are all `expect(spy).toHaveBeenCalled()`, paste it back with the
  constraint: "tests assert the **business result**, never the call order; at most 3 assertions
  per test".
- Run timings/coverage-diff to prove the new tests mean something:
  `pytest -q --durations=10`, `npx vitest run --coverage`.

## Verification

```bash
python3 tools/cc-scan.py <file> --no-baseline   # LOW_TEST_RATIO / HARD_PARAMS after the seam
npx vitest run --coverage                       # the new branches are actually covered
```

Related: `../skills/clean-code/references/11-testing-for-clean-code.md` · `02-extract-function.md` ·
`08-legacy-refactor-plan.md`
