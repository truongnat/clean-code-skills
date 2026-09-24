---
name: clean-code-refactoring
description: >-
  Refactor without changing behaviour: split oversized functions, remove duplication,
  replace magic numbers and strings with named constants, break deep nesting with guard
  clauses, move logic into the domain as value objects, replace type-switches with
  strategy or polymorphism, and add characterization tests to untested legacy code.
  Use when the user says "refactor this", "clean this up", "extract a function",
  "reduce complexity", "this code is a mess", or when a module needs a better
  cc-scan or arch-scan score.
metadata:
  version: "1.1.0"
  companion: "clean-code"
---

# Safe refactoring (behaviour unchanged)

> **Scanner path:** commands below assume `tools/cc-scan.py` / `tools/arch-scan.py` are in the
> repo. If they are not, the same scanners may be on `PATH` as `cc-scan` / `arch-scan` (identical
> flags) — see `INSTALL.md` §1b. If neither exists, ask for the report instead of guessing numbers.

## 0. Four preconditions before you touch a key

1. **Behaviour is locked** — tests are green, or you have characterization/snapshot tests (§4) proving exact input→output.
2. **Small scope** — one function, one problem class, one atomic commit.
3. **No behaviour change** — anything that alters logic is a separate feature/bugfix commit.
4. **No micro-fragmentation** — do not split cohesive logic into single-use 3-line helpers.

If any of these is false, stop and lock it first.

## 1. Pick the refactoring by symptom

| Symptom you can see | Refactoring | Steps |
|---|---|---|
| Cognitive complexity > 10 / Branch storm | `Guard Clauses` + `Decompose Conditional` + `Strategy` | 1–2 |
| `if` nested ≥ 3 deep | `Guard Clauses` (invert `if` and return early) | 1 |
| 4+ parameters | `Introduce Parameter Object` / Options object | 1 |
| `f(true)` flag argument | `Split Predicate` → two explicit functions | 1 |
| `switch (type)` repeated in several places | `Replace Conditional with Polymorphism`, or **table-driven** when the variants are data | 2–3 |
| Two near-identical blocks | `Extract Function` / `Extract Superclass` **only after** proving they change for the same reason | 1–2 |
| A temp variable lives for 60 lines | `Replace Temp with Query`, `Inline Temp` | 1 |
| Data lives here, behaviour lives there | `Move Method/Field` onto the owner of the data | 1 |
| Class of 500 lines, 3 reasons to change | `Extract Class`, one per reason | 3–5 |
| `try/catch` sprinkled everywhere | `Replace Exception with Precheck`, keep one `try` at the boundary | 2 |
| Everything is `string` / `double` | `Introduce Value Object` (`Money`, `Email`, `Percentage`) | 1 per type |
| No one knows who calls this function | `Rename` first — a clear name often removes the need to refactor | 0 |
| Module imports outward (`domain → db`) | move the *decision*, not the code: define a port in the domain, push the DB call behind an adapter | 2–4 (see `../clean-code/references/12-clean-architecture.md`) |

**Rule of thumb for the first column**: if you cannot name the *reason this code will change
next*, you do not yet have a seam — extracting one now is guesswork (see
`../clean-code/references/14-design-patterns.md`, "pattern-first design").

## 2. Six-step loop (repeat until the numbers move)

```bash
# 1. Snapshot baseline state & verify existing test suite is GREEN
python3 tools/test-lock.py snapshot --test-cmd "npx vitest run src/billing" src/billing

# 2. Choose ONE refactoring from the table above, apply it via AST-grep or structured refactor

# 3. Format changed files
npx prettier --write src/billing    # or: ruff format src/billing ; gofmt -l src/

# 4. Verify safety harness: runs tests, checks score, blocks regressions
python3 tools/test-lock.py verify

# 5. Commit the atomic refactor on its own
git commit -am "refactor(billing): extract pricingPolicy from placeOrder"
```

**Score unchanged = you moved complexity around, you did not remove it.** Go back to step 1
with a different refactoring. This is the moment most cleanups fail: a 90-line function split
into four 25-line functions named `step1`…`step4` has more lines and the same difficulty.

Measured on the demo in this pack (`tools/demo/`), the same pricing logic scored
**72.0/100 before and 100.0/100 after** — the difference was naming, one value object, guard
clauses and deleting a dead block, not adding files.

## 3. Commit discipline

```text
refactor: rename usrProfile -> userProfile
refactor: extract guard clauses in CheckoutService
refactor: introduce Money value object
test: characterization tests for TaxCalculator (snapshot of current behaviour)
feat(billing): free shipping from 500_000 VND     <- only AFTER the commits above are merged
```

- **One commit = one refactoring.** A reviewer reading `git diff --stat` should see the name
  of the refactoring, not a 900-line wall.
- Never mix `refactor` and `fix` in one commit: when the fix is reverted you revert the
  cleanup too, and `git bisect` becomes useless.
- `git diff -w` on a refactor commit: if there is a real change in it, split it out.
- Rename commits are reviewable with `git diff --word-diff`; do them first, they shrink every
  later diff.

## 4. Untested legacy code: characterization tests

```py
# Pins CURRENT behaviour (bugs included) - this is not "the correct behaviour"
@pytest.mark.parametrize("order", read_fixture_json("legacy_orders.json"))   # 50 real orders
def test_tax_matches_snapshot(order, snapshot):
    snapshot.assert_equal(compute_tax_vnd(order), key=f"tax:{order['id']}")
```

Rules:
1. The snapshot is generated by **the old code**, before you touch anything.
2. After each refactoring step the snapshot must be **byte-identical**.
3. If a case must change, that is a behaviour change: mark it
   `// KNOWN-BUG(AC-1250): rounding is wrong for mixed cart` and **do not fix it** in the
   refactor PR. A bug fixed inside a refactor is a bug nobody can attribute later.
4. Feed the test from production-shaped data (or anonymised exports). A snapshot over a
   hand-typed example pins only the example.

## 5. Worked micro-examples (the four that cover 80% of the work)

```ts
// (a) Extract + name the intent, don't just cut the lines
- if (cart.total > 500000 && !cart.coupon) { cart.shippingFee = 0 }        // 1 function, 4 jobs
+ const FREE_SHIPPING_THRESHOLD_MINOR = 500_000_00;
+ function shippingFeeFor(cart: Cart): MinorUnits {
+   if (cart.hasCoupon || cart.subtotal >= FREE_SHIPPING_THRESHOLD_MINOR) return 0;
+   return flatShippingFee(cart.weightGrams);
+ }

// (b) Guard clauses: remove a level instead of adding a comment about it
- for (const line of order.lines) { if (line.qty > 0) { if (!line.isGift) { total += line.price * line.qty; } } }
+ for (const line of order.lines) {
+   if (line.qty <= 0 || line.isGift) continue;
+   total += line.price * line.qty;
+ }

// (c) Parameter object, only when the parameters actually travel together
- function placeOrder(userId, addressId, sku, qty, coupon, asDraft) { }
+ function placeOrder(cmd: PlaceOrderCommand) { }   // PlaceOrderCommand: dataclass/record

// (d) Type-switch → table, when the variants are data rather than behaviour
- switch (kind) { case 'pdf': ... case 'csv': ... case 'xlsx': ... }   // 4 places, always out of sync
+ const RENDERERS: Record<ReportKind, Renderer> = { pdf: pdfRenderer, csv: csvRenderer, xlsx: xlsxRenderer };
```

```py
# Magic number → named constant with its unit, at the top of the module
- if amount > 500000: fee = 0
+ FREE_SHIPPING_THRESHOLD_VND = 500_000
+ if amount > FREE_SHIPPING_THRESHOLD_VND: fee = 0
```

## 6. The 1500-line file

1. Read it once, no edits. Underline 3–5 **phrases** that recur in comments and block
   headers — those are the future module names, and they are already in the author's language.
2. `Extract Module` per phrase: move its **data and behaviour together**, never the function
   alone while the field stays behind.
3. Between the two modules: one interface or port. No back-imports, no shared mutable state.
4. After every move, re-check the cycle tools: `npx madge --circular src`,
   `python3 tools/arch-scan.py src --fail-on error`, `lint-imports`.
5. Stop when the file is ≤ 400 lines **and** the file name states its scope. Do not chase
   100 lines for the screenshot.

## 7. When to stop refactoring (a skill, not laziness)

| Stop when | Do not "refactor" when |
|---|---|
| Threshold reached: ≤ 40 lines/function, ≤ 3 params, cc-scan ≥ 85 | The module is being deleted or replaced within the quarter |
| The rest of the debt is **not** on the ticket's path | The code merely differs from your taste |
| The next step costs > 2 days and does not reduce the place that changes most | You are renaming 30 variables nobody complained about |
| Tests are too thin to trust → **stop, write tests first** | You found 40 smells and want them all gone this week |
| Reviewers start disagreeing about the new shape | The refactor exists to make a metric green (a metric gamed is a metric retired) |

Leave the debt written down: `// TODO(refactor, AC-1240): fold VAT into TaxPolicy` or one
small issue with three lines of description. An invisible intention is not a plan.

## 8. Output the user should get when they ask "refactor this for me"

Return **small steps**, each with: (a) the refactoring name, (b) before/after code, (c) the
command that proves behaviour is unchanged, (d) one sentence on why it is safe, (e) the score
delta. Do **not** return "the whole file, rewritten, 900 lines": nobody reviews that, and it
destroys the blame history the team depends on. A good answer ends with what you deliberately
did *not* touch and why.
