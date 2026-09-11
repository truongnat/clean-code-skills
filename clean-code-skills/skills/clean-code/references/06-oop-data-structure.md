# 06 · Objects and data structures

> The goal: **each business concept lives in exactly one place**, and the people using it do not
> have to know how it is stored.

## 1. Encapsulation hides *decisions*, not numbers

A getter and a setter for every field is not encapsulation — it is a public field wearing a helmet.

```java
// ❌ nine places re-implement the tax and shipping rules, each slightly different
public class Order {
    public double getAmount() { return amount; }
    public String getStatus() { return status; }   // "PAID" | "REFUNDED" | ...
}
if ("PAID".equals(order.getStatus()) && order.getAmount() > 500_000) { ship(order); }

// ✅ the data and the behaviour on that data sit together; the invariant is guarded
public final class Order {
    private Money amount;                    // Money validates and rounds by itself
    private OrderStatus status;              // an enum, not a String

    public boolean isShippable() {
        return status == OrderStatus.PAID && amount.isGreaterThan(ShippingPolicy.FREE_THRESHOLD);
    }
    public void markShipped(TrackingNumber tracking) {
        if (status != OrderStatus.PAID) throw new IllegalOrderTransition(status, OrderStatus.SHIPPED);
        this.tracking = tracking;
        this.status = OrderStatus.SHIPPED;
    }
}
```

```ts
// ❌ a setter that cannot hold the invariant - the bug moves to every caller
class Cart { setItems(items) { this.items = items; } getTotal() { return this.items.reduce(...); } }

// ✅ the API is intent, not a pointer into the fields
class Cart {
  #items: readonly CartLine[] = [];
  add(productId: string, quantity: number) { /* stock check, merge duplicate lines, return a new Cart */ }
  removeLine(lineId: string) { ... }
  get subtotal() { ... }
}
```

```py
# ✅ Python: frozen dataclass + a derived property - encapsulation without boilerplate
@dataclass(frozen=True)
class LineItem:
    unit_price: Decimal
    quantity: PositiveInt = 1

    @property
    def amount(self) -> Decimal:
        return self.unit_price * self.quantity
```

```go
// ✅ Go: unexported fields + a constructor that returns an error is the idiomatic invariant gate
type Order struct {
	amount MinorVND
	status OrderStatus
}

func NewOrder(amount MinorVND, status OrderStatus) (Order, error) {
	if !amount.IsPositive() {
		return Order{}, fmt.Errorf("new order: amount must be positive, got %d: %w", amount, ErrInvalid)
	}
	return Order{amount: amount, status: status}, nil
}
```

**The test of real encapsulation**: delete one public field/getter and look at the compiler. Errors
in **one** place = the concept was already local. Errors in eight = you have no encapsulation, you
have a struct with a prefix.

A "data-only object" is legitimate when the thing **is** data: a DTO, a value object, a DB row, an
event payload. Then use `record` / `struct` / `@dataclass(frozen=True)` / a TS `type` — and do not
stuff business rules into it: those belong to the policy or service that consumes it. Validate in
the constructor (or the factory) so an invalid instance cannot exist; a "check later" method is how
the invalid state escapes.

## 2. Law of Demeter: at most one hop

> "Talk to your friends, not to their pockets."

```ts
// ❌ a train wreck: the caller knows the internals of three objects
const city = order.customer.addresses.find(a => a.kind === "BILLING")?.city;

// ✅ the order owns the meaning of "billing city"
const city = order.billingCity();
```

Practical rules:
- `a.b()` ✅ · `a.b().c()` ⚠️ — fine when the chain is a **fluent builder of the same type**
  (`Promise`, stream/LINQ, `Money.add().add()`), because it is one expression of one concept.
- `a.b.c().d` ❌ — mixing navigation with behaviour means the encapsulation is already broken.
- Creating your own collaborators inside a factory/constructor is fine: that is where friends are made.
- A **delegate** (`order.customerName()` calling `customer.name()`) is not a Demeter violation;
  it is you paying for a small concept so callers do not have to.

A long getter chain is usually a missing abstraction:

| The chain | The concept that is missing |
|---|---|
| `user.address.city` | `user.shippingCity()` |
| `order.items.filter(i => i.qty > 0).length` | `order.lineCount()` |
| `req.user.roles.find(r => r.name === 'admin')` | `req.user.isAdmin()` |
| `order.lines.map(l => l.price * l.qty).reduce(...)` | `order.subtotal()` |

**Tell, don't ask:**

```java
// ❌ the outside asks, then decides - so Order's rule now lives in six places
if (order.getStatus() == PENDING && order.getAge().toDays() > 3) { order.cancel(); }

// ✅ command the object; it knows its own rule
order.autoCancelIfStale(ORDER_STALE_AFTER);
```

The other cliff: `order.doEverything()`. Behaviour that needs **two aggregates** belongs to a
domain service (`TransferService`, `RefundPolicy`), not to either aggregate. If a method needs six
getters from another object to do its job, that is Feature Envy — move the method (see §6).

## 3. Data structure vs object: pick a side per boundary

| | Data structure (record / DTO / struct) | Object (domain / service) |
|---|---|---|
| public | **fields** | **behaviour** |
| adding an operation | touch every `switch`/map | add a method |
| adding a variant | add a field, logic untouched | ⚠️ may touch many classes — use `enum` + `sealed interface` |
| use it for | transport, persistence, values, event payloads | concepts with rules and a lifecycle |

The project-killer is having **both** at once: public fields *and* type switches sprinkled
everywhere. Choose one direction per boundary and flip it deliberately when the pain reverses
(this is the expression problem, and "I can add a new variant without touching logic" is the
usual thing you actually want):

```kotlin
// Kotlin/TypeScript let data and dispatch coexist without scattered if-else
sealed interface Fee { val amount: Money }
data class FlatFee(override val amount: Money) : Fee
data class WeightFee(val perKg: Money) : Fee
fun Fee.forWeight(kg: Int) = when (this) { is FlatFee -> amount; is WeightFee -> perKg * kg }
```

```ts
// TS: a discriminated union + exhaustive check (the compiler becomes the reviewer)
type Fee = { kind: "flat"; amount: MinorVND } | { kind: "weight"; perKg: MinorVND; kg: number };
const feeOf = (fee: Fee): MinorVND => {
  switch (fee.kind) {
    case "flat": return fee.amount;
    case "weight": return fee.perKg * fee.kg;
    default: { const _never: never = fee; throw new UnreachableError(_never); }
  }
};
```

A shape that resolves the tension in practice: **DTO in → domain objects inside → event out.**
The boundary types have public fields and no rules; the domain has rules and no public fields; the
events are immutable facts.

## 4. Boundaries: who is allowed to know whom

```text
API layer       : parse -> validate -> call the use case -> map failures to HTTP
Application     : orchestration (transaction, events); no detailed business rules
Domain          : entities + value objects + pure policies (imports no DB/HTTP/framework)
Infrastructure  : adapters implementing the ports the domain declares (DB, queue, mail, providers)
```

Three checks you can run by reading `import` statements — not the wiki diagram:
1. the domain imports **nothing** from frameworks or transport; if it does, business logic is in the
   wrong layer;
2. a layer imports only what is **below** it, or an interface it declares itself (DIP);
3. nobody imports from `common/utils` "the blind bag" — if it is needed, it needs a name.

```bash
python3 tools/arch-scan.py src --fail-on error        # direction + cycles + boundary leaks
npx madge --circular --extensions ts,tsx src
lint-imports                                          # exact contracts, Python (see configs/architecture/)
```

```py
# 10-second domain audit, any Python repo: who in domain/ touches a framework?
import ast, pathlib
BAD = ("flask", "django", "requests", "sqlalchemy", "fastapi", "pydantic")
for f in pathlib.Path("src/domain").rglob("*.py"):
    for node in ast.walk(ast.parse(f.read_text())):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", "") or ""
            if any(b in mod for b in BAD):
                print(f"{f}: domain must not depend on {mod}")
```

`arch-scan` encodes the same three laws as `layers[].rank`, `frameworkPackages` and `boundaries` —
the file above is the manual version; the config is the permanent one (`configs/architecture/arch-scan.config.json`).

## 5. Value-object cookbook (the four that pay immediately)

| Concept | Minimum viable type | What it kills |
|---|---|---|
| money | `MoneyMinorVND` (int minor units) + `add/multiply(rounding)` | `double`, rounding debates, unit mix-ups |
| percentage / rate | `Rate` (basis points or a decimal with `applyTo(Money)`) | `0.9` in five files meaning three things |
| date range | `DateRange(start, end)` validating `end >= start` in the constructor | `(from, to, tz)` data clumps |
| identifier | `OrderId` / `Email` / `PostalCode` | passing a `String` where the compiler cannot help |

```java
public record MoneyMinor(long amount) {
    public MoneyMinor { if (amount < 0) throw new IllegalArgumentException("negative money: " + amount); }
    public MoneyMinor plus(MoneyMinor other) { return new MoneyMinor(amount + other.amount); }
}
```

Rules that keep them boring and useful: make them **immutable**, put the rounding/validation in the
type (not in the service), give `equals/hashCode` for free (`record`, `dataclass`, `==` on a Go
struct of scalars), and refuse to let them grow behaviour that is not about the value.

## 6. Dependency injection: for testability, not for fashion

```ts
// ❌ untestable: the class builds its own dependencies and cannot be swapped
class InvoicePrinter {
  private db = new PrismaClient();
  private smtp = new SmtpClient("api key in the source");
}

// ✅ dependencies arrive through the constructor; tests pass fakes, the composition root passes real ones
class InvoicePrinter {
  constructor(private invoices: InvoiceRepository, private mailer: Mailer) {}
}
```

- **Being testable** is the reason; "we might swap Postgres for MySQL" is a side benefit that almost
  never happens on its own.
- Do **not** inject values (config, amount, currency) — those are data of the call, not collaborators.
- An interface with exactly one implementation that never changes is speculative generality (YAGNI).
  Interfaces appear when there are **≥ 2 real adapters** — a production one plus a test fake counts.
- Where the language has no constructor injection, the same rule applies with different syntax: a
  function taking the port as an argument (Go), a factory taking a `Deps` struct, a `from_di`
  provider (FastAPI). Put all the wiring in **one composition root**, never in a domain file.

## 7. Smell → refactoring (lookup table; the full catalogue is `10-code-smells-refactorings.md`)

| Smell | How you can read it | Refactoring | Machine hint |
|---|---|---|---|
| Feature Envy | a method uses another object's data more than its own | `Move Method` / `Extract Class` onto the owner | human review |
| Data Clumps | `(from, to, tz)` always travel together | `Introduce Parameter Object` (`DateRange`) | `TOO_MANY_PARAMS` |
| Primitive Obsession | `string status`, `double money`, `int phone` | value object / enum | `MAGIC_NUMBER` on the literals |
| Middle Man | a class that only forwards six calls | remove it, call the real thing | `LAYER_UNUSED`-style dead layer |
| Inappropriate Intimacy | two classes reach into each other's fields | `Hide Delegate`, or make the relation one-way | compiler after deleting a field |
| God Class | > 400 lines, ≥ 3 reasons to change | `Extract Class` **by reason for change**, not by size | `HUGE_FUNCTION`, `LONG_FUNCTION`, `wc -l` |
| Shotgun Surgery | one rule change touches 7 files | move the rule into one policy | `DUPLICATE_BLOCK` |
| Anemic Domain | everything is fields + getters, logic sits in `XxxService` | move invariants and rules into the type | `arch-scan` sees no domain behaviour |
| Refused Bequest | a subclass overrides most of what it inherits | replace inheritance with composition | review-only |
| Switch on Type | the same `switch (kind)` in 3+ places | table-driven, sealed types, polymorphism | `COMPLEXITY`, `HARD_COMPLEXITY` |
| Temporal Coupling | "call A before B or it corrupts" — in a comment | fuse into one command, or make the state a type | the comment itself (`BLOCK_COMMENT`) |
| Lazy Class | a class that does not justify its indirection | delete it, inline | `LAYER_UNUSED` if it is a whole layer |

## 8. Self-check

1. Delete an arbitrary public field or getter: does the compiler point at **one** place? If it
   points at eight, you are missing encapsulation, not missing getters.
2. Any chain longer than two hops (`a.b().c().d`)? Name the missing concept.
3. In `domain/`: any import of HTTP, DB or framework? (Run the script in §4.)
4. Is there a `utils.ts` imported from 10+ places for different reasons? Each cluster of reasons
   should become a named module (`money.ts`, `dateRange.ts`).
5. Can you construct an invalid domain object from a test? If yes, the invariant is in the wrong
   place — it is a *policy* the caller must remember, and callers forget.
6. One-hour audit with a colleague: pick the aggregate you touch most, list every file that reads
   its fields, and count how many of them make a decision from those fields. That count is the size
   of the missing behaviour on the type — and it is the honest number to quote when you propose the
   fix in a sprint.
