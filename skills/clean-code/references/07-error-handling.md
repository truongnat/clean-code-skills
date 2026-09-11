# 07 · Error handling — the part that decides whether your code is debuggable

> Errors are not rare; **information at the moment of failure** is rare. This chapter exists so
> that at 2 a.m. you open the log and know what happened, where, and why.
> Day-to-day checklist version: the `clean-code-error-handling` skill. This file is the reasoning.

## 1. Five foundational rules

1. **Use exceptions, not error codes / null / flags.** `return -1` makes every caller remember a
   rule and allows them to forget it. An exception cannot be skipped by accident — only on purpose.
2. **Write the happy path first.** `try` wraps only what can fail; do not wrap the whole function.
   The main flow must read top to bottom without hopping over three `catch` blocks.
3. **Never swallow.** `catch {}` / `except: pass` converts an incident into an unknown. Catching
   means doing something: log, wrap, fall back, or rethrow with context.
4. **Specific types, actionable messages.** No `throw new Exception("error")`. The message carries
   **what is wrong + the data involved + what the caller should do**.
5. **Keep the cause.** Losing the original stack loses half the truth:
   `throw new X(msg, { cause })` · `raise X from err` · `throw new X(msg, e)` · Go
   `fmt.Errorf("…: %w", err)` · Kotlin `X(msg, e)`.

The corollary that makes all five easy: **a failure is either a normal outcome or an anomaly**, and
the type system should say which. `Result`/`Option` for the first, exception for the second.

## 2. Business failure vs system failure — they differ in who handles them

| Kind | Examples | Who handles it | How it travels |
|---|---|---|---|
| **User-fixable** | out of stock, declined payment, invalid coupon | the caller's UI, immediately | `Result` failure or a typed exception → 4xx with a machine code |
| **System-transient** | gateway timeout, DB connection reset | infrastructure policy (retry, circuit breaker) | retryable exception → bounded retry → 503 + `Retry-After` |
| **Bug in our code** | `IndexOutOfBounds`, a failed invariant, `null` where the type said otherwise | nobody at runtime — it must fail loudly | do not catch it; let it crash, log with stack, page someone |
| **Fatal / environmental** | disk full, missing config, expired credentials | the platform (restart, alarm, deploy) | exit non-zero at startup; a readiness alarm |

Mistaking the third row for the second is how a team ships a `try/catch` that hides a
`NullPointerException` for eleven months and calls it "resilience".

```ts
// domain: a business failure is a valid outcome of the flow
export class InsufficientStockError extends Error {
  constructor(readonly sku: string, readonly requested: number, readonly available: number) {
    super(`out of stock ${sku}: requested ${requested}, available ${available} - ` +
          `reduce the quantity or notify the customer`);
  }
}

// infrastructure: "retryable" is a property of the failure, decided where the failure is known
export class TaxProviderTimeout extends Error implements Retryable {
  retry = true;
  constructor(readonly provider: string, opts?: ErrorOptions) {
    super(`tax provider ${provider} timed out - retry with backoff`, opts);
  }
}
```

```py
# ✅ Python: a specific exception + `from err` so the chain survives
class PaymentDeclined(Exception):
    """Tell the customer now - no retry, no 500."""

class GatewayUnavailable(Exception):
    retryable = True

def charge(order: Order, gateway: PaymentGateway) -> Receipt:
    try:
        return gateway.charge(order.total)
    except TimeoutError as err:
        raise GatewayUnavailable(f"gateway timeout while charging order {order.id}") from err
    except CardDeclinedError as err:
        raise PaymentDeclined(f"order {order.id} declined: {err.reason}") from err
```

```go
// ✅ Go has no try/catch; the same principles apply to the error value
func (s *Service) Charge(ctx context.Context, order Order) (Receipt, error) {
	receipt, err := s.gateway.Charge(ctx, order.Total())
	if err != nil {
		// wrap: add context, keep the sentinel so the caller can classify with errors.Is
		return Receipt{}, fmt.Errorf("charge order %s: %w", order.ID, err)
	}
	return receipt, nil
}

// the caller classifies - it never compares strings
if errors.Is(err, gateway.ErrCardDeclined) { return respond(402, "card declined") }
```

## 3. Anti-patterns (some of these are machine-checkable)

| Anti-pattern | Why it hurts | Fix | Enforced by |
|---|---|---|---|
| `catch (e) {}` | an incident becomes silence; metrics flat, customers complain | log + rethrow, or an explicit fallback with a comment | `cc-scan EMPTY_CATCH`, ruff `S110` |
| catching the root (`Exception`/`Throwable`) | swallows `OutOfMemory` and your own bugs | catch the specific type; let the rest crash | Checkstyle `IllegalCatch`, Sonar `S1181` |
| `throw new RuntimeException(e)` | the error type is lost, the caller cannot branch | a domain-specific exception | review + `wrapcheck` (Go) |
| returning `null` on failure | NPE twelve frames later, reason unknown | `Optional`/`Result`, or throw | TS strict null checks, `nilerr` |
| log **and** rethrow | one incident prints three times, ordering is lost | log once at the boundary, or throw; never both | Sonar `S2139` |
| `try` around 60 lines | you cannot tell which step failed | a small `try` around the one operation | `HUGE_FUNCTION`, review |
| retry on every error | retrying a business rejection is spam and costs money | retry only `Retryable`/timeout, with a cap and backoff | review |
| `return 0` as fallback | 0 becomes real data in tomorrow's report | a **flagged** degraded path (status + metric) | review |
| exception for normal flow ("not found") | slow and noisy | `Optional`/`Result`/empty list | review |
| `finally` used to commit/roll back | hides the original error, double-faults | try-with-resources / `defer` / context managers | review |
| catching inside a loop and continuing | 3% silent data loss per run, forever | collect failures, report a count, stop at a threshold | review + a metric |
| error message with the token / PII in it | your logs become the breach | allow-list fields; mask helper | Semgrep, review |
| `200 OK` with `{ "error": … }` | clients, retries, dashboards and WAFs all misread it | correct status code + error body | contract test |
| exception built with a query inside it | the error path hits the DB and fails recursively | pass the data you already have into the constructor | review |

## 4. "One `try`" at the boundary (API / CLI / job)

```ts
// exactly one place translates exceptions into HTTP; it lives in the adapter
app.use(async (ctx, next) => {
  try {
    await next();
  } catch (err) {
    if (err instanceof ValidationError) return ctx.throw(422, err.issues);
    if (err instanceof NotFoundError) return ctx.throw(404, err.message);
    if (err instanceof InsufficientStockError) return ctx.throw(409, err.message);
    if (err instanceof PaymentDeclined) return ctx.throw(402, err.message);
    ctx.app.log.error({ err, requestId: ctx.state.requestId }, "unhandled");   // log EVERYTHING
    ctx.status = 500;
    ctx.body = { message: "temporarily unavailable, please retry", requestId: ctx.state.requestId };
  }
});
```

```py
# FastAPI: the same idea, one handler per exception type, registered at the edge
@app.exception_handler(InsufficientStockError)
async def _stock(_, exc): return JSONResponse(409, {"code": exc.code, "sku": exc.sku, "requestId": ...})
```

```java
// Spring: @RestControllerAdvice - one class, no try/catch inside controllers
@ExceptionHandler(IllegalOrderTransition.class)
ResponseEntity<ApiError> onTransition(IllegalOrderTransition e) { return ResponseEntity.status(409).body(ApiError.of(e)); }
```

Inside domain and application code there are **no** HTTP status codes and no `throw new Error("500")`
— that mapping is an adapter's job. A batch job or CLI inverts the default: **fail loudly, exit
non-zero, print the context**, and only catch at the very top to format the message. "Crash-only"
workers that leave a resumable cursor are more reliable than ones that try to recover politely.

## 5. Validation at the boundary: parse, don't validate

```ts
// ❌ hand-rolled checks scattered through the function: never complete, and you must remember them
function createOrder(body: any) {
  if (!body.amount || body.amount <= 0) throw new Error("bad amount");
  ...
}

// ✅ one gate: raw input -> a guaranteed type; inside, you trust the types
const CreateOrderDto = z.object({
  amountMinor: z.number().int().positive(),
  currency: z.enum(["VND", "USD"]),
  items: z.array(z.object({ sku: z.string().min(1), qty: z.number().int().positive() })).min(1),
});

function createOrder(input: unknown): Order {
  const dto = CreateOrderDto.parse(input);   // 422 automatically, machine-readable details
  return Order.from(dto);
}
```

Python: Pydantic `BaseModel` / `model_validate`. Java: Bean Validation on the controller **plus**
the value-object constructor for the invariant. Go: unmarshal into a DTO, call `Validate() error`,
then build the domain type. TS: zod/io-ts/`typebox`.

Validation therefore lives in exactly **two** places: the boundary schema (is the shape right?) and
the type constructor (is the meaning right?). Any check in a third place means either the schema or
the type is under-specified — that is the fix, not another `if`.

## 6. Error-path tests — the most skipped and the most brittle

```ts
it("reports the stock gap with the numbers a customer can act on", async () => {
  const err = await placeOrder({ sku: "A1", qty: 5 }).catch((e) => e);
  expect(err).toBeInstanceOf(InsufficientStockError);
  expect(err).toMatchObject({ sku: "A1", requested: 5, available: 2 });
});

it("retries a timeout but never a card decline", async () => {
  const gateway = fakeGateway({ firstCall: new TaxProviderTimeout("TAX"), then: ok });
  await expect(service.charge(order, gateway)).resolves.toMatchObject({ status: "ok" });
  expect(gateway.calls).toBe(2);

  const declined = fakeGateway({ firstCall: new PaymentDeclined("insufficient_funds") });
  await expect(service.charge(order, declined)).rejects.toBeInstanceOf(PaymentDeclined);
  expect(declined.calls).toBe(1);                     // <- the assertion that matters
});
```

Minimum set per failure mode you introduce:
1. **classification** — the right type reaches the right layer (and the wrong one is *not* retried);
2. **no half state** — nothing was written, or the compensating action ran;
3. **payload** — status code, machine-readable `code`, `requestId`, and no internal leak on 500;
4. **timeout/fault injection** — fake the provider as slow, assert the deadline fires and the metric
   moves; a test suite without a slow-dependency test proves nothing about resilience.

Rules of thumb: every `catch`/`if err != nil` in production code gets a test that shows it doing
its job; the fake gateway records `calls`, so retry logic is asserted by count, not by mood.

## 7. The error contract you publish (so the client can be written without guessing)

```json
{
  "code": "INSUFFICIENT_STOCK",
  "message": "Only 2 left of A1",
  "details": { "sku": "A1", "requested": 5, "available": 2 },
  "requestId": "req_01H8…",
  "retryable": false
}
```

Four promises: `code` is stable and enumerated (a public API in miniature — changing it is a breaking
change); `message` is safe to show a human; `details` is what the UI needs to fix the input;
`retryable` tells the client whether to try again at all. Add `retryAfterSeconds` when you say 503.
Document them in one place (`docs/api/errors.md`) and let the tests assert the codes, so a renamed
string breaks a test rather than an integration.

## 8. What a machine catches (turn it on)

| Tool | Rule | Catches |
|---|---|---|
| `cc-scan` | `EMPTY_CATCH` (error) | `catch { }`, `except: pass` |
| ESLint | `no-empty{allowEmptyCatch:false}`, `no-floating-promises`, `no-useless-catch`, `require-atomic-updates` | empty catch, dropped promise, pointless rethrow, await-without-assign |
| ruff | `E722`, `TRY002/300/301/400`, `S110`, `EM101/EM102`, `B904`, `B039` | bare except, vanilla raise, try-except-pass, f-string in exception, `raise` without `from`, mutable default in raise |
| Checkstyle | `IllegalCatch`, `IllegalThrows`, `EmptyCatchBlock` | catching `Exception`/`Throwable`, rethrowing the wrong thing |
| golangci | `errcheck`, `wrapcheck`, `bodyclose`, `nilerr` | ignored error returns, wrong wrapping, leaked bodies |
| Sonar | `S108`, `S1181`, `S2139`, `S5753` | as above, with history on the project dashboard |

Measured on this pack's own demo (`configs/python/src/orders_bad.py`, ruff 0.16.6): **39 errors**,
including `ANN001` x9, `EM101` x3 (raw string in exception), `TRY002` x2 (vanilla raise),
`T201` x2, `S110` (try-except-pass), `E722` (bare except), `C901`, `PLR0912/0915/0917`,
`PLR2004`, `E711`. The compliant sibling `orders_good.py` reports **0**.

```bash
rg -n --multiline "catch\s*\([^)]*\)\s*\{\s*\}|except\s*:\s*$|except[^:]*:\s*(pass|continue)\s*$" -g '!*_test.*'
```

## 9. Review checklist for error handling

- [ ] every user-visible failure has its own type (not a `string`), with `code`
- [ ] messages carry data (ids, quantities, field names) — never "something went wrong"
- [ ] system failures: timeout + bounded retry + backoff + jitter; business failures: **no** retry
- [ ] writes are idempotent where they can be retried (a key, or a guard)
- [ ] every wrap preserves the cause; only one layer logs
- [ ] API answers: 4xx "you", 5xx "us", both with `requestId`; 404 logged at info, not error
- [ ] degraded paths are counted by a metric, not just logged, and have an alarm threshold
- [ ] logs carry `requestId` + the business id + the provider name; no token, no PII
- [ ] tests cover: happy path, each `catch`, one garbage-third-party-payload case, one slow-dependency case
- [ ] a runbook line exists for any new alarm: "if `payment.retry_exhausted` spikes, do X"
- [ ] `cc-scan` on the diff: `EMPTY_CATCH` = 0
