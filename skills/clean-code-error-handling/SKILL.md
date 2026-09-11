---
name: clean-code-error-handling
description: >-
  Design and repair error handling: replace error codes and null-on-failure with typed
  exceptions or Result, delete error-swallowing catches, give every exception a domain
  name and a preserved cause, add bounded retry with backoff and timeout, validate at the
  boundary (parse, don't validate), and map failures to the right HTTP status. Use when the
  user mentions error handling, try/catch, exceptions, retry, timeout, silent failures,
  "it crashes", "it swallows errors", or when a review finds an empty catch or a null return.
metadata:
  version: "1.1.0"
  companion: "clean-code"
---

# Error handling, clean-code style

> **Scanner path:** commands below assume `tools/cc-scan.py` / `tools/arch-scan.py` are in the
> repo. If they are not, the same scanners may be on `PATH` as `cc-scan` / `arch-scan` (identical
> flags) — see `INSTALL.md` §1b. If neither exists, ask for the report instead of guessing numbers.

## 1. The 30-second decision: Result or exception?

```text
Can the caller handle it right here, as a normal outcome?
├─ YES  → Result/Option/enum       (not found, out of stock, validation failed)
└─ NO   → exception                (network down, corrupt data, invariant broken)
```

"A miss" that callers must branch on every time is **not** an error — it is a second return
type. An "error" that the caller cannot do anything about is not their problem: log it,
alarm it, and stop pretending the return value carries the news.

Hard rules:
- **Domain-specific** exception types (`TaxProviderTimeout`), never `Error("lỗi")` /
  `Exception("failed")`.
- `try` wraps **only the statement that can fail**; the happy path reads top to bottom.
- **No** `catch {}`, `except: pass`, `_ = err`. Catching means: log, wrap, fall back, or
  rethrow. Doing nothing is a decision to lose data, and it must be written down.
- Always keep the **cause**. A lost chain removes half the debugging information.
- Log in **one** place (the boundary). Log-and-rethrow at 4 layers turns one incident into
  four identical stack traces and hides the ordering.

## 2. Formula for a good exception class

```ts
export class InsufficientStockError extends Error {
  static readonly code = "INSUFFICIENT_STOCK";
  constructor(
    readonly sku: string,
    readonly requested: number,
    readonly available: number,
  ) {
    super(`out of stock ${sku}: requested ${requested}, available ${available} - ` +
          `reduce the quantity or notify the customer`);
    this.name = "InsufficientStockError";
  }
}
```

Three things in the message: **what happened** + **the numbers** + **what the caller should
do**. `code` exists so the API layer can emit a machine-readable response without string
matching.

| Language | Idiom | Cause |
|---|---|---|
| TS/JS | `class X extends Error { static readonly code = "..." }` | `new X(msg, { cause })` (ES2022) |
| Python | `class X(RuntimeError)` with `@dataclass(kw_only=True)` fields | `raise X(...) from err` |
| Java/Kotlin | `class X extends RuntimeException` (do not spread checked exceptions into the domain) | `super(msg, cause)` |
| Go | sentinel `var ErrNotFound = errors.New(...)` or typed error struct | `fmt.Errorf("load order: %w", err)` + `errors.Is/As` |
| Rust | `enum AppError { #[from] Io(std::io::Error), … }` (`thiserror`) | the variant holds the source |

## 3. Retry / timeout / idempotency — the three are one unit

```ts
// ❌ WRONG: unbounded retry, no timeout, no idempotency key
for (;;) { try { return await api.charge(order); } catch { } }

// ✅ RIGHT
const MAX_ATTEMPTS = 3;
const BASE_DELAY_MS = 200;
const TIMEOUT_MS = 2_000;

export async function chargeWithRetry(
  order: Order,
  gateway: PaymentGateway,
): Promise<Receipt> {
  let lastError: unknown;
  for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
    try {
      return await withTimeout(
        gateway.charge(toChargeRequest(order, idempotencyKey(order))),
        TIMEOUT_MS,
      );
    } catch (err) {
      if (!isRetryable(err)) throw err;              // 4xx / business rejection: never retry
      lastError = err;
      if (attempt < MAX_ATTEMPTS - 1) await sleepBackoff(attempt, BASE_DELAY_MS);  // + jitter
    }
  }
  metrics.increment("payment.retry_exhausted", { provider: gateway.name });
  throw new PaymentUnavailable(order.id, { cause: lastError });
}
```

Checklist (a missing box means the PR is not done):
- [ ] timeout on **every** outbound call (HTTP/DB/queue/file), including "it's an internal
      service, it's fast" — the outage you remember is always someone else's fast service
- [ ] retry **only** retryable failures (5xx, timeout, connection reset); a 4xx is a bug in
      your request, and retrying it multiplies the load of the bug
- [ ] backoff with **jitter** and a hard attempt cap
- [ ] writes carry an **idempotency key** — without one, retry means double charge
- [ ] circuit breaker / bulkhead when a dependency fails often under real traffic
- [ ] budget: total retry time must fit inside *your* caller's timeout, or you produce a
      retry storm that outlives the original request
- [ ] metrics: retry count, retry exhausted, fallback used, breaker open duration
- [ ] a `Retry-After` / 503 response for your own callers, so backpressure propagates

## 4. Parse, don't validate (this is what kills "null everywhere")

```py
# ✅ one gate at the boundary; inside, the type is the proof
class CreateOrder(BaseModel):
    amount_minor: int = Field(gt=0)
    currency: Literal["VND", "USD"] = "VND"
    items: list[OrderLine] = Field(min_length=1)

def create(payload: dict, repo: OrderRepository) -> Order:
    dto = CreateOrder.model_validate(payload)        # 422 comes for free
    return repo.save(Order.from_dto(dto))
```

- Inside the domain there is **no** `if data is None` — the type already guarantees it.
- `Optional[T]` appears only at boundaries (DB/HTTP) and where "absent" is a legitimate
  state (`coupon: Optional[Coupon]`).
- Never let `dict[str, Any]` cross layers: that is deleting the type system and asking tests
  to patch it afterwards.
- Convert once, at the edge, into a domain type; validate invariants in the constructor so an
  invalid object cannot exist (see `../clean-code/references/06-oop-data-structure.md`).

## 5. Map failures to the outside world in exactly one place

| Failure kind | HTTP | Behaviour |
|---|---|---|
| `ValidationError`, `ParseError` | 400/422 | field-level message, no stack, no internals |
| `Unauthorized` / `Forbidden` | 401/403 | never leak whether the record exists |
| `*NotFound` | 404 | a missing id is **normal** → log at info, not error |
| `InsufficientStock`, `Duplicate`, `PaymentDeclined` | 409/422/402 | machine-readable `code` so the client can react |
| `ProviderTimeout`, `ProviderUnavailable` | 503 + `Retry-After` | log warn, metric, let the caller retry |
| anything else | 500 | log **error + stack + requestId**; return a generic message |

```ts
if (err instanceof NotFoundError) return { status: 404, body: { code: err.code, id: err.id } };
logger.error({ err, requestId }, "unhandled");                  // the only place that logs
return { status: 500, body: { code: "INTERNAL", requestId } };  // generic to the client
```

`requestId` in the response body is what turns "customer says it failed" into a 30-second
lookup. Attach it in middleware, not in each handler.

## 6. Partial failure: when one step of several must not corrupt the rest

```text
order saved → payment charged → email sent
```

Any of the last two can fail. Choose deliberately and write it in the code comment:
1. **Compensate** (saga): reverse the earlier steps — needs an explicit `refund()` path and
   a test for "refund failed twice".
2. **Persist intent, retry later** (outbox): the DB write and the "to do" row commit
   atomically; a worker delivers. This is the default when there is a database.
3. **Accept, and alarm**: only when a human will fix it and the loss is bounded.

What is never acceptable: an ordinary `try/catch` around step 3 that logs "email failed" and
leaves the order in a state the next reader cannot interpret. See
`../clean-code/references/13-architecture-patterns.md` for the outbox/idempotency contract.

## 7. Tests for the error path (minimum for each `catch` you add)

```ts
it("provider timeout -> 503, retryable, half-order never written", async () => {
  const repo = fakeRepo();
  const gateway = fakeGateway({ throwFirst: new TimeoutError() });
  await expect(placeOrder(input, { repo, gateway }))
    .rejects.toBeInstanceOf(PaymentUnavailable);
  expect(repo.saved).toHaveLength(0);                 // no half state, ever
});
```

Also worth one test each: retry gives up after `MAX_ATTEMPTS` (assert the count, not only the
type), a 4xx is **not** retried, and the cause chain survives to the log. A `catch` block with
no test is a `catch` block that will be deleted "to fix a flake" within a year.

## 8. Machine enforcement (turn these on)

```bash
python3 tools/cc-scan.py . --json | jq '[.findings[] | select(.rule=="EMPTY_CATCH")]'   # error level
npx eslint . --rule '{"no-empty":["error",{"allowEmptyCatch":false}],"@typescript-eslint/no-floating-promises":"error"}'
ruff check --select E722,TRY,S110,EM,LOG004 .
golangci-lint run --enable errcheck,wrapcheck,nilerr,bodyclose ./...
```

`EMPTY_CATCH` is one of the 20 `cc-scan` rules and is scored at **error** (-4 points), because
it is the only smell in this pack that can silently destroy money.

## 9. Three fixes that appear in almost every repo

```py
# ❌ except Exception: print(e)
   ✅ except ProviderTimeout as err:
          logger.warning("tax provider timeout", exc_info=True)
          raise ProviderUnavailable(order_id, cause=err) from err

# ❌ return None on failure            (caller cannot tell "empty" from "broken")
   ✅ raise NotFound(order_id)        # or return Result.failure(NOT_FOUND)

# ❌ catch (Exception e) { e.printStackTrace(); }
   ✅ throw new InvoiceSyncFailed(orderId, e);
```

## 10. Definition of done for an error-handling PR

- [ ] Every outbound call has a timeout; every retry has a cap, backoff and an idempotency key
- [ ] No empty catch anywhere in the diff (`cc-scan` `EMPTY_CATCH` = 0 on changed files)
- [ ] Each new failure has a named type with `code`, numbers and an action in the message
- [ ] Cause preserved; logs carry `requestId` and are written in one layer only
- [ ] Boundary parsing converts to domain types; no `dict[str, Any]` / `Map<String,Object>` across layers
- [ ] Error and boundary branches have tests, including "no half-written state"
- [ ] 5xx messages leak nothing internal; 404 is logged at info, not error
