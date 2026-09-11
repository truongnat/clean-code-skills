# Session 7 · Error handling — the chapter that saves you at 2 a.m.

**Duration:** 60 minutes · **Pre-work:** paste one production error line from last week into the doc
(the worse, the better). **Output:** `EMPTY_CATCH` blocking in CI + a written error catalogue.

## 1. Team standard

```text
1) Exceptions, not error codes, not null, not flag fields.
2) No catch is empty. Catching means doing one of four things: log-and-rethrow with the cause,
   an explicit fallback plus a metric, translate into a domain exception, or retry.
3) Domain-specific exception types, with data in the message (id, quantity), and the cause kept.
4) `try` wraps only what can fail; the main flow reads straight through, top to bottom.
5) Validation happens at the boundary (a schema: zod / pydantic / Bean Validation); inside, you
   trust the types.
6) Exceptions map to HTTP status / CLI exit code in exactly ONE place - the adapter.
7) An incident-grade failure logs the business id and the requestId; a 404 never pages a human.
```

Rule 7 is the one teams skip and then discover during an incident: the log line said "failed", the
order id was nowhere, and the search took 40 minutes instead of 40 seconds.

## 2. Exercise: the swallow hunt (20 minutes, on the real repo)

```bash
python3 ../tools/cc-scan.py . --json | jq '[.findings[] | select(.rule=="EMPTY_CATCH")]'
rg -n --multiline "catch\s*\([^)]*\)\s*\{\s*\}" -g '!*_test.*'
rg -n -U "except\s*:|except\s+\w+\s*:\s*\n\s*(pass|continue)" -g '!*test*'
rg -n "_ = err|_, _ :=|ignore_error" -g '!*_test.go'
```

For every hit, answer three questions out loud: (a) when does this fire? (b) if it fired and nothing
was logged, how would we find out? (c) what should the caller do? Then fix **one** place and add **one**
test. Hunting ten and fixing none is the failure mode of this exercise, so cap the room at three fixes.

Our own demo file is the calibration: `configs/python/src/orders_bad.py` reports **39 ruff errors**,
of which `E722` (bare except) x1, `S110` (try/except/pass) x1, `TRY002` (vanilla raise) x2 and
`EM101` (raw string in exception) x3 — the same shapes your repo will have. Show the count first, fix
them second; the number is what makes the fix feel worth an hour.

## 3. The exception catalogue (made once, used forever)

Create `docs/error-catalogue.md`, one row per type:

| Exception | Layer | What the client sees | Retry? | Developer action |
|---|---|---|---|---|
| `ValidationError` | api | 422 + field list | no | fix the input |
| `InsufficientStock` | domain | 409 + `available` | no | business case, no alert |
| `PaymentDeclined` | domain | 402 | no | the customer resolves it |
| `IllegalOrderTransition` | domain | 409 + current state | no | usually a client race; log at warn |
| `GatewayTimeout` | infra | 503 + `Retry-After` | yes: max 3, backoff | check the provider dashboard |
| `DataCorruption` | infra | 500 + requestId | no | **page** on-call |

The benefit is not tidiness: it is that nobody has to invent "what does a 500 mean" while writing
code under a deadline, and the reviewer gains a measuring stick instead of a taste argument. When a PR
adds a failure mode with no row here, that is the comment: `blocker: catalogue row missing`.

## 4. Three classic refactorings

```py
# (1) a try around the whole function -> wrap the risky call, raise specific failures
# ❌
def create_order(payload):
    try:
        dto = validate(payload); order = build(dto); repo.save(order); notify(order); return order.id
    except Exception:
        return None
# ✅
def create_order(payload: dict) -> OrderId:
    dto = validate(payload)              # a validation failure is bad input, not a mystery
    order = repo.save(build(dto))        # only this line can fail on infrastructure
    notify_later(order)                  # fire-and-forget, with its own bounded handling
    return order.id
```

```java
// (2) an error code -> an exception
// ❌ int result = pay(); if (result == -3) …
// ✅ try { pay(); } catch (CardDeclined e) { … } catch (GatewayUnavailable e) { retryLater(e); }
```

```go
// (3) swallowing -> wrapping with context; the caller classifies with errors.Is
// ❌ res, _ := call()
// ✅ if err := call(); err != nil { return fmt.Errorf("charge order %s: %w", order.ID, err) }
```

Run each on a file from the repo, not on a toy: the point is seeing that the fix is ten minutes and
that the tests already exist to prove it.

## 5. Retry and timeout — the incident-reading drill

Hand the room a snippet that calls HTTP with **no timeout and unbounded retry** (rewrite a real file
if you have one). Six faults to find:

1. no timeout → a thread parks forever, and the pool dies before the provider does;
2. retry on every error → you hammer a partner who is returning 4xx, and pay per call;
3. no idempotency key → the retry **charges the customer twice**;
4. fixed sleep between attempts → a synchronised herd when the provider comes back;
5. no attempt ceiling and no total budget → a 30 s request becomes 30 minutes of retries;
6. no circuit breaker → every request pays the timeout while the partner is down.

The fix, in this order: `withTimeout(2s)`, `MAX_ATTEMPTS = 3`, exponential backoff **with jitter**, an
idempotency key carried through, a total deadline for the request, then a breaker on the provider
client. Then the review question that catches this class forever: *"if this call is retried twice,
what breaks?"*

## 6. Minimum tests for the failure paths

```ts
it("reports the stock gap with numbers the customer can act on", async () => {
  const err = await placeOrder({ sku: "A1", qty: 5 }).catch(e => e);
  expect(err).toBeInstanceOf(InsufficientStockError);
  expect(err).toMatchObject({ available: 2, requested: 5 });
});

it("retries a timeout but never a card decline", /* …fake gateway, assert call counts… */);
```

Review rule: **every `catch` you write must have a test.** If you are not going to test it, remove the
`catch` and let the failure surface — failing fast is the honest option, and it is cheaper than a
silent branch nobody will ever read again.

## 7. Machine-enforce it

```bash
python3 tools/cc-scan.py . --fail-on error          # EMPTY_CATCH scores at error (-4 points)
npx eslint . --rule '{"no-empty":["error",{"allowEmptyCatch":false}],"@typescript-eslint/no-floating-promises":"error"}'
ruff check --select E722,TRY,S110,EM,LOG004,B904 .
golangci-lint run --enable errcheck,wrapcheck,nilerr
```

Plus the Checkstyle pair shipped in this pack (`configs/java/checkstyle.xml`): `IllegalCatch`,
`EmptyCatchBlock` and a `SuppressionCommentFilter`, so `// checkstyle: suppress` works — but note it
has **no** `SuppressWarningsHolder`, so the TS-style `@SuppressWarnings` does not apply in Java: use
the comment form, and put the reason in the same line.

## 8. Mini-drill: from error type to alarm (10 minutes)

For each catalogue row, write three cells; this is the part that turns a log into an operation:

| Exception | Metric | Threshold → action | Runbook line |
|---|---|---|---|
| `GatewayTimeout` | `tax.timeout.rate` | > 5% for 10 min → disable the flow, page provider contact | "toggle `feature.tax.api` off; orders queue and reconcile" |
| `DataCorruption` | `data.corruption.count` | ≥ 1 → page immediately | "stop writes, take the snapshot, run `tools/reconcile`" |
| `PaymentDeclined` | `payment.declined.rate` | no alert; dashboard only | "product question, not an on-call page" |

A runbook line is one sentence that starts with a verb. If a row's action is "check the logs", the
alarm is decoration: it will wake someone who then does the same unguided search you just automated.

## 9. Closing check

1. Why is "log and rethrow" a defect? (one incident printed four times, and the context that mattered
   is on the copy that was logged badly)
2. When is returning `null`/`Optional` right and `requireX()` throwing right? ("absence" is a
   legitimate state → `Optional`; the caller has no other option → throw)
3. Why is `return 0` as a fallback worse than crashing? (0 becomes real data in tomorrow's report,
   and the report is believed)
4. Which catalogue row is missing from your repo today, and who adds it this week?

**Policy line for `CONTRIBUTING.md`:** *"No empty catch (CI blocks). Every new failure mode has a
catalogue row, a metric, and a test. HTTP mapping lives in one adapter. Retries only for retryable
failures, with a cap, jitter and an idempotency key."*

**If you only have 15 minutes:** run §2, fix the single worst swallow, and add the test for it. One
swallowed error removed is worth more this week than the whole rest of this chapter.

Materials: `../skills/clean-code/references/07-error-handling.md` · skill `clean-code-error-handling`
