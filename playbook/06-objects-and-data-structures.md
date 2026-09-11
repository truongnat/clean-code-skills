# Session 6 · Objects and data structures — encapsulation and boundaries

**Duration:** 60 minutes · **Pre-work:** each person names one class they would not want a stranger to
read. **Output:** one ADR + import rules enforced by a tool, not by promise.

## 1. Three hard standards for the team

```text
1) Data and the behaviour on that data live in ONE PLACE. A concept's invariant is held by that
   concept - never scattered across services and controllers.
2) Law of Demeter: one hop. `a.b().c()` is fine only as a fluent chain (builder/stream/Promise)
   returning the same type. `a.b.c().d` means the encapsulation is already broken.
3) The domain imports no framework and no transport. `domain` importing express/prisma/requests is
   a review blocker, not a discussion.
```

A fourth, from the architecture track, is worth stating here too: **the owner of a concept owns its
interface.** If `infrastructure` declares the port and `domain` imports it, the dependency still
points outward and rule 3 is decorative.

## 2. Spot the violations with three commands

```bash
# (1) anemic domain: classes that are only fields plus accessors
rg -n -U --multiline-dotall "class\s+\w+\s*\{(?:\s*(private|public)[^\n]*;)+\s*\}" src | head

# (2) train wrecks: long getter chains
rg -n "\.\w+\(\)\.\w+\(\)\.\w+" src | head -20

# (3) a leaking domain
rg -n "^import .*(express|prisma|sequelize|requests|axios|jdbc)" src/domain

# Go and Python versions of (3)
rg -n '"(net/http|database/sql|github.com/gin|github.com/gorm)' internal/domain
rg -n "^\s*(from|import)\s+(flask|django|fastapi|sqlalchemy|requests)" src/domain
```

Run these on your repo *before* the session and put the three counts on the board. In a typical
mid-size repo the surprise is not that the numbers are big — it is that (1) is larger than (3): teams
worry about framework leakage while the real rot is behaviourless data classes.

## 3. Three short fixes, done live

```java
// EXERCISE 1 - the train wreck
// ❌ city = order.getCustomer().getAddresses().stream().filter(Address::isBilling).findFirst().map(Address::getCity)
// ✅ order.billingCity()                    // name the missing concept: "what is a billing address"

// EXERCISE 2 - primitive obsession
// ❌ String status + double amount
// ✅ OrderStatus status; Money amount;      // Money = (minorUnits, currency), validates and rounds itself

// EXERCISE 3 - tell, don't ask
// ❌ if (order.getStatus() == PENDING && order.getCreatedAt().plusDays(3).isBefore(now)) order.cancel();
// ✅ order.autoCancelIfStale(AUTO_CANCEL_AFTER);

// EXERCISE 4 - the one everyone forgets: can you build an invalid one?
// ❌ new Order(); o.setStatus("SHIPPED");   // a shipped order with no total: constructible!
// ✅ new Order(id, amount, status)         // or a factory; an invalid instance must not compile
```

Twenty minutes for all four, then tests, then a commit each: `refactor: <what>`. Exercise 4 is the
one that changes how people write code, because it reframes the question from "did I check?" to "could
anyone forget to check?".

## 4. Choosing a data structure or an object — the decision table

| Situation | Choose | Why |
|---|---|---|
| transport between layers (API, DB row, queue payload) | `record` / `struct` / `@dataclass(frozen=True)` | no invariant, needs serialising, adding a field must be cheap |
| a concept with rules and a lifecycle (`Order`, `Wallet`) | a class with behaviour | the invariant has to be blocked at the constructor |
| a finite set of variants (fee kind, order kind) | `sealed` / union enum + `match` | the compiler forces every new branch to be handled |
| you need a stand-in in tests | an interface/port **at the boundary** | mock only what you do not own |

The mistake to name out loud: having public fields **and** type switches everywhere at once. That is
the worst of both, and it is how a module ends up with nine places computing VAT.

## 5. Dependency inversion, pragmatically (no religion)

```ts
// the domain declares only what it needs
interface TaxProvider { vatOf(amount: Money, at: Date): Promise<Money>; }

// the application service receives it
class PlaceOrder {
  constructor(private readonly taxes: TaxProvider, private readonly orders: OrderRepository) {}
}

// the composition root (main.ts) - the ONLY place that knows Prisma/Axios exist
new PlaceOrder(new VatApiTaxProvider(config.taxApi), new PrismaOrderRepository(db));
```

When to introduce the interface: the implementation is (a) I/O, (b) has ≥ 2 real variants — counting
the test fake — or (c) is scheduled to be replaced. Otherwise use the class directly. YAGNI still
applies inside a boundary.

## 6. Enforce the boundary with a machine, not a promise

| Stack | Tool | What it enforces | Verified in this pack |
|---|---|---|---|
| any | `python3 ../tools/arch-scan.py src --fail-on error` | layer direction, cycles, domain-framework imports, boundary leaks | the demo `configs/architecture/demo/python` reports **82.0/100 with 3 errors**, and the java demo **99.0/100 with 0** |
| Python | **import-linter** (exact contracts) | "domain must not import infra", independence | the demo flips **2 contracts BROKEN → 2 kept, 0 broken** by deleting one file |
| JS/TS | dependency-cruiser (`.dependency-cruiser.cjs`) | forbidden import paths, no cycles | config shipped, sample in `configs/architecture/` |
| Java/Kotlin | **ArchUnit** in a test | layer rules as unit tests | `configs/architecture/demo/java`: **3 rules BROKEN → KEPT** |
| Go | `depguard` in golangci-lint | package allow-lists | `configs/go/.golangci.yml` |

Install one of them *during* the session on the real repo. The reason is practical: a rule that only
exists in this document is enforced by whoever remembers it, and memory is the weakest gate in your
pipeline.

## 7. Homework (submitted as a PR — a plan, not code)

Pick one class over 400 lines. For each cluster of fields and methods, **name the concept**
(`PricingPolicy`, `ShippingScheduler`, `InvoiceRenderer`). Propose the split and the PR order
(expand → contract) in `../skills/clean-code/templates/refactor-plan.md` form; present it for five
minutes at the retro. Writing the plan is the exercise: a split you cannot name is a split you should
not do.

## 8. Closing check

1. Do 20 getters and setters mean encapsulation? (no — that is a public field wearing a helmet)
2. Why does `order.getCustomer().getAddress()` cost you six files when the customer schema changes?
   (the structure became the callers' knowledge)
3. Is `users.filter(…).map(…).sort()` a Demeter violation? (no: a fluent chain of the same kind)
4. Which of today's three grep counts do you expect to still be non-zero in a month, and what is the
   gate that shrinks it? (if nobody can answer, the session produced enthusiasm instead of a control)

**Policy line for `CONTRIBUTING.md`:** *"Invariants live in the type; the domain imports no framework
or transport; layer direction is checked by the tool in §6 and blocks the PR; a deliberate exception
needs `arch-scan:allow` with a reason and an ADR."*

**If you only have 15 minutes:** run §2's grep (3) on `src/domain`, fix whatever it finds today, and
add the `arch-scan` step to CI. Two structural gates are worth more than twenty slides about
encapsulation.

Materials: `../skills/clean-code/references/06-oop-data-structure.md` · `../skills/clean-architecture/SKILL.md`
