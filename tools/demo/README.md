# Demo: before / after applying the skill

Two versions of **the same business feature** (placing an order) so you can *see* the Clean Code
standard instead of reading about it. The imports in these files are illustrative — they do not
run, and they do not need to.

```bash
cd tools/demo

# 1) The legacy version (deliberately dirty)
python3 ../cc-scan.py src/legacy-order-service.ts src/legacy-renderer.ts --no-baseline

# 2) The refactored version — same feature, plus tests
python3 ../cc-scan.py src/order-service.ts src/order-service.test.ts --no-baseline

# 3) Compare the JSON if you want it on a slide
python3 ../cc-scan.py src/legacy-order-service.ts --json | jq '{score, counts}'
python3 ../cc-scan.py src/order-service.ts       --json | jq '{score, counts}'
```

What it actually prints (cc-scan v1.0.1, both commands run from the pack root):

| Version | Score | error | warning | info |
|---|---|---|---|---|
| `legacy-order-service.ts` + `legacy-renderer.ts` | **72.0 / 100** (grade C) | 4 | 11 | 4 |
| `order-service.ts` + `order-service.test.ts` | **100.0 / 100** (grade A) | 0 | 0 | 0 |

## What the legacy version gets caught for

| Rule | Line | Detail |
|---|---|---|
| `HARD_PARAMS` | 15 | `placeOrder(user, items, coupon, force, skipStockCheck, currency)` — 6 parameters |
| `HARD_COMPLEXITY` | 15 | ~16 logical branches (hard limit 15) |
| `LONG_FUNCTION` | 15 | 52 lines (recommended ≤ 40) |
| `DEEP_NESTING` | 15 | nests 7 levels deep (recommended ≤ 3) |
| `BOOLEAN_PARAM` | 15 | `force`, `skipStockCheck` |
| `LINE_TOO_LONG` | 15 | 141 characters |
| `EMPTY_CATCH` ×2 | 50, 56 | two empty `catch` blocks → the customer sees "success" while the DB holds nothing |
| `DEBUG_STATEMENT` ×2 | 18, 39 | leftover `console.log`, `console.warn` |
| `MAGIC_NUMBER` ×3 | 28, 30, 45 | `0.8`, `25000`, `500000` sitting inside the logic |
| `COMMENTED_CODE` ×2 | 10, 59 | the old constant + `// total = total * 1.1;` |
| `TODO_MARK` ×2 | 4, 9 | two TODOs with no ticket (one of them in the file header) |
| `DUPLICATE_BLOCK` | 70 | an 8-line block repeated in `legacy-renderer.ts:4` |
| `LOW_TEST_RATIO` | project | 0 test files for 2 source files |

## What the refactored version does about it (one to one)

| Problem | The fix | Clean Code section |
|---|---|---|
| 6 parameters | collected into `PlaceOrderCommand` (an interface) | 3 — at most 3 parameters |
| one 52-line function | `priceCart` (pure) + `PlaceOrder.run` (coordination) | 3 — one job, one level of abstraction |
| 7 levels of nesting | guard clauses + `filter`/`some` | 3, 6 |
| `catch {}` | `throw new OrderPersistenceError(userId, reason)` (data in the message) | 7 |
| magic numbers | `VIP_MULTIPLIER`, `STANDARD_COUPON_DISCOUNT`, `REVIEW_THRESHOLD_VND` | 2 |
| debug logs | deleted (if needed: a `Logger.debug` with a log level) | 9 |
| dead code | deleted — Git keeps the history | 4 |
| an 8-line duplicate | one shared render function | 8 — DRY |
| `boolean force` | `notify: "always" \| "onForce"` | 3 |
| untestable | the pure logic split out → 5 tests, 0 mocks, running in 0ms | 1, 3 |

## Exercises with these two files

1. Add `if (currency == "USD") total = total * 23000;` to `legacy-order-service.ts`, then scan
   again: you will see `MAGIC_NUMBER` go up, and the line-level rules on `placeOrder` get worse.
   Fix it your way, then compare with how `order-service.ts` does it.
2. Try refactoring `legacy-renderer.ts` **without looking at** `order-service.ts`. Then diff the
   two: where did you choose differently, and why do both still meet the standard? (That is the
   point: the standard removes the pointless arguments, it does not turn everyone into a robot
   writing identical code.)
