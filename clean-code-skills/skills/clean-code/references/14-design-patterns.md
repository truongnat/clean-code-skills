# 14 · Design patterns — the vocabulary, with a warning label

Patterns are names for shapes you will otherwise describe in a code review with hand gestures.
They are **not** goals. The machine checks in this pack (`cc-scan`) flag the anti-patterns more
often than the patterns: `DUPLICATE_BLOCK`, `LONG_FUNCTION`, `MAGIC_NUMBER`, `BOOLEAN_PARAM`,
`HUGE_FUNCTION`, `DEEP_NESTING` are exactly what appears when a pattern is forced or skipped.

> Use a pattern when the *problem* it solves is present. If you cannot name the cost you are
> paying to buy it, you are not applying the pattern — you are decorating.

## 1. The ones that earn their keep

### Strategy — replace a switch on a flag with interchangeable behaviour

The single most valuable pattern for the `BOOLEAN_PARAM` / `if (type == …)` smell.

```ts
// BAD: every new discount kind edits (and re-tests) this function
function price(items: Item[], isVip: boolean, isHoliday: boolean): number {
  let total = sum(items);
  if (isVip) total *= 0.9;
  if (isHoliday) total *= 0.95;
  return round(total);
}

// GOOD: one policy type, one implementation per behaviour, closed for edits
type DiscountPolicy = { rate: number; appliedTo: (order: Order) => boolean };

const VIP: DiscountPolicy = { rate: 0.9, appliedTo: (o) => o.isVip };
const HOLIDAY: DiscountPolicy = { rate: 0.95, appliedTo: (o) => o.isHoliday };

export function price(order: Order, policies: readonly DiscountPolicy[]): number {
  return round(policies.reduce((total, p) => (p.appliedTo(order) ? total * p.rate : total), sum(order.items)));
}
```

`priceOrder(order, [VIP, HOLIDAY])` reads as the business rule, each policy is a one-line test,
and adding `BUNDLE10` is a new file, not a diff in a shared function. If the strategies grow
branches and shared steps, that is the signal for **Template Method** below — or for a plain
enum + exhaustive `switch` in one place, which in Go and Rust is the *idiomatic* strategy.

### Factory function (not the GoF class) — creation with invariants

Anything that needs validation, defaults, or a non-trivial constructor belongs to one function
that cannot return an invalid object.

```python
# BAD: half-built objects float around; callers guess the order of setters
o = Order()
o.items = items
o.total = compute_total(items)          # someone forgets this line on a rainy day

# GOOD
def create_order(items: list[Item], currency: Currency) -> Order:
    if not items:
        raise EmptyCartError("an order needs at least one line")
    return Order(items=items, total=total_of(items), currency=currency, placed_at=clock.now())
```

In TS/Python a named function returning the type is enough; keep `class Factory` for when the
creation itself needs collaborators.

### Adapter — translate a foreign shape into the interface your layer owns

This is the mechanism behind every port in `12-clean-architecture.md`, and it is where a
`BOUNDARY_LEAK` gets fixed. Keep adapters dumb: mapping, retrying, serialising. A decision in an
adapter is a decision in the wrong layer.

### Decorator — add a cross-cutting behaviour without touching the code being crossed

```go
// the use case does not know about timing, retries or logging
type TimedRepo struct{ inner OrderRepository; log *slog.Logger }

func (r TimedRepo) Save(ctx context.Context, o Order) error {
    start := time.Now()
    err := r.inner.Save(ctx, o)
    r.log.Info("order.saved", "ms", time.Since(start).Milliseconds(), "err", err != nil)
    return err
}
```

Circuit breaker, retry, cache, rate limiter, metrics, auth wrapper — all decorators. The tell that
you have gone wrong: the decorator has an `if` about the payload's business meaning.

### Facade — one honest entry point for a subsystem

A `checkout` module exporting `placeOrder(cmd)` instead of 11 exported helpers is what makes
`BOUNDARY_LEAK` possible to enforce. A facade with no rules inside (pure pass-through) is the
layered-architecture smell from `13-architecture-patterns.md` §1.

### Observer / event — decouple "something happened" from "who reacts"

Use inside a process for genuinely independent reactions; use a queue (chapter 13) across
processes. The trap is invisible coupling: order placed → email → analytics → inventory, and one
of them throws. Keep handlers idempotent, ordered-by-key where needed, and never let a subscriber
block the publisher's transaction.

### Command — bundle intent, so it can be validated, logged, retried, queued

`placeOrder(cmd: PlaceOrderCommand)` (see `tools/demo/src/order-service.ts`, the refactored demo)
beats `placeOrder(userId, items, address, coupon, ip, isGift)` on `HARD_PARAMS`, testability, and
the ability to serialise the intent. One command type per business action; no setters; validation
in the constructor/factory.

### Repository — for the *aggregate*, not for every table

`OrderRepository` with `find(id) / save(order)` is a port. `OrdersTableRepository.findByStatusAndDate`
with 6 arguments is a query object in a repository costume — put read queries next to the read
model (or in a `queries/` module) instead of stuffing them into the write-side abstraction.

### Unit of work / transaction script — pick deliberately

For simple CRUD, transaction script (one function per action, one transaction) is *correct*, not
amateurish. Reach for a unit of work when several aggregates must move together, or when a use
case issues many writes.

## 2. The ones people reach for too early

| Pattern | When it is right | What it looks like when forced |
|---|---|---|
| **Singleton** | a process-wide resource with a documented lifetime: connection pool, logger, metrics registry | hidden global state, tests that pass in one order, `Class.instance()` inside domain code. Pass the collaborator in. |
| **Abstract factory / builder** | many valid combinations, expensive construction, or an object that must be immutable | `OrderBuilder.setA().setB()…` where a 4-parameter constructor was honest |
| **Template method** (inheritance) | 2+ subclasses genuinely share a 5-step flow | a base class with 9 hooks, half overridden; a "spaghetti inheritance" tree. Prefer composition + strategy. |
| **Chain of responsibility** | ordered rules of unknown length: validation pipeline, middleware | a `Rule` interface where the real order is a hard-coded `if` in the caller |
| **Mediator** | N x M interactions collapse into one place (state machines, workflow engines) | a `SomethingManager` that becomes the biggest file in the repo — that is a god object with a pattern name |
| **Specification** | filters must compose and be reusable across DB/in-memory/validation | a 400-line DSL to express `status == OPEN and total > 100` |
| **Visitor** | stable set of types, frequently new operations over them (compilers, codegen) | adding one field requires touching 7 visitors; in that case use a `switch` on an exhaustive enum |
| **Service locator / DI container as a global** | bootstrapping wiring in one composition root | `container.get("orderService")` in business code: no types, no explicit dependencies, hidden cycles |
| **DTO per everything** | boundaries, public APIs, versioned contracts | 3 identical DTOs and 4 mappers for one screen — copy-paste with extra steps |

## 3. Anti-patterns this pack's scanner can see

| Anti-pattern | Shape | Detected by |
|---|---|---|
| God object / Manager | one class with 20 public methods and no theme | `HUGE_FUNCTION`, `LONG_FUNCTION`, file size, review |
| Flag argument | `run(force, verbose, async)` | `BOOLEAN_PARAM` |
| Primitive obsession | `price(total: float, kind: str)` where `Money`/`OrderKind` exist | review; `MAGIC_NUMBER` if the string is compared to literals |
| Anemic domain model | `Order` with 14 getters + `OrderService` with all the rules | review; `DEEP_NESTING`/`LONG_FUNCTION` cluster in the service |
| Duplicate-by-copy | the same 12 lines in 3 handlers | `DUPLICATE_BLOCK` |
| Dead abstraction | an interface with exactly one implementation, never substituted | review + `--list-rules` on arch scan for orphans |
| Layered pass-through | a controller that only forwards to a service that only forwards to a repo | review; `COMPLEXITY` of 0 per layer |
| Circular layer deps | `domain ⇄ infrastructure` | `LAYER_CYCLE` (arch-scan) |

"Dead abstraction" is a judgement call with a rule attached to it: **an interface you never
implement twice is a comment**. Keep it if it crosses a deployable or team boundary, delete it if
it only crosses a folder.

## 4. Patterns that pay for themselves in test code

| Need | Pattern | Test you get |
|---|---|---|
| Time | injected `Clock` port | a frozen clock, deterministic "expires at midnight" tests |
| Randomness | injected `Rng` / seeded generator | reproducible fuzz + property tests |
| External API | adapter behind a port + a `FakeGateway` | no HTTP in unit tests; failure paths assertable |
| Retry policy | decorator around the adapter | assert "3 attempts, exponential, gives up" without a live server |
| Idempotency | `dedupe_key` + unique index, wrapped by a decorator | run the same event twice, assert one effect |
| Feature flags | flag values read at the edge, passed as data | both branches of every gated path are unit-testable |

If a pattern is only useful for looking sophisticated in a design doc, it is a liability. If it
buys a test that used to need a running system, it is an asset.

## 5. How to introduce a pattern in a live codebase

1. **Name the problem first**, in the incident/review language: "adding a discount type touches 4
   files", "one failing subscriber loses the email".
2. Write the ADR (`templates/adr-template.md`) with the cost you accept, in one paragraph.
3. Convert **one** call site; keep the old shape until the new one has a test and a name everyone
   recognises. This is "one step of Red-Green-Refactor" at module scale (`09-code-health-workflow.md`).
4. Make it mechanical: add the lint/arch rule or the review checklist item, otherwise the next
   contributor copies the old shape. `checklists/code-review.md` already carries the lines for
   strategy/port/adapter.

## 6. Read next

- `12-clean-architecture.md` · `13-architecture-patterns.md`
- `10-code-smells-refactorings.md` — the same list from the "what goes wrong" side.
- Playbook: `playbook/12-design-patterns.md`.
- Prompt: `prompts/13-pattern-picker.md` (pick a shape for a named problem, with its cost).
