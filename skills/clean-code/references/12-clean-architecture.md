# 12 · Clean architecture

Rule IDs enforced by tooling: `UPWARD_DEPENDENCY`, `LAYER_CYCLE`, `DOMAIN_FRAMEWORK_IMPORT`,
`BOUNDARY_LEAK`, `UNCLASSIFIED_FILES`, `LAYER_UNUSED` (`tools/arch-scan.py`).

Chapters 1–9 of this pack make a module readable. This chapter is about the thing that kills
systems anyway: **who is allowed to know about whom**. A 20-line function inside a module that
imports the database, the HTTP framework and eleven other features is still untestable, and a
"readable" mess is still a mess.

## 1. The one rule

> **Source code dependencies must point inwards, towards the domain.**
> — the dependency rule (Robert C. Martin, *Clean Architecture*)

Everything else in this chapter is bookkeeping around that sentence:

| Question | Answer |
|---|---|
| What is "inwards"? | The layer holding the business rules: entities, value objects, invariants. |
| What is "outwards"? | Controllers, DB drivers, queues, UI, frameworks, main(). |
| May outer know inner? | Yes — that is the whole trick. |
| May inner know outer? | Never. Not even "just the type". |
| What if inner needs the outer? | **Declare an interface in the inner layer**, let the outer layer implement it. The dependency is inverted, the arrow still points in. |

The inversion is not decoration. It is what buys you:

- **testability**: `python3 -m pytest tests/unit -q` runs in 0.8 s with no database, because the
  use case talks to `OrderRepository` — an interface it owns — not to SQLAlchemy;
- **replaceability**: swap Postgres for Dynamo, REST for gRPC, and the diff touches one adapter;
- **survival of the rules**: the framework dies in five years, the pricing rules still make money.

## 2. The four layers this pack's tooling assumes

`arch-scan` and every config in `configs/` use this vocabulary. Rename it freely — but then keep
the **rank** semantics: `rank 0` = innermost, and a file may import layers of rank ≤ its own.

```
rank 3  interface        main.go, controllers, routes, CLI, GraphQL resolvers, consumers
rank 2  infrastructure   repositories, ORM, HTTP clients, queue publishers, filesystem
rank 1  application      use cases (one per business action), the ports they need, orchestration
rank 0  domain           entities, value objects, invariants, policies — plain language types
```

What belongs where (and the tell that it is in the wrong place):

| Layer | Lives there | Smell that means "wrong layer" |
|---|---|---|
| Domain | `Order`, `Money`, `discountPolicy()`, "a order cannot ship before it is paid" | the file imports a driver, reads a config, or takes a `Context` |
| Application | `PlaceOrderUseCase`, `OrderRepository` (interface), transactions, idempotency | the file contains an `if` about a business rule that belongs to the domain |
| Infrastructure | `SqlOrderRepository`, `StripeGateway`, migrations | the file decides anything; it should only translate |
| Interface | `POST /orders`, request DTOs, mapping HTTP ↔ use-case input | the file contains a `for` loop over rows building a total |

`arch-scan` will report the first row of each smell as `DOMAIN_FRAMEWORK_IMPORT`; keep that list
in the config short and honest (drivers, web frameworks, ORMs) — it is the cheapest architecture
gate you can own.

## 3. Boundaries: the horizontal cut

Layers are vertical depth. Features (bounded contexts in DDD language) are the horizontal cut:
`checkout`, `pricing`, `shipping`, `identity`. Both axes are needed, and each has its own failure:

- layers without features → a 40-file `application/` folder where checkout edits break pricing;
- features without layers → five copies of "connect to the database", none of them tested.

The rule between features is stricter than the one between layers:

> A feature may be reached **only** through what it publishes: a public module, a command, an
> event. Never `features/pricing/internal/discount_math.ts`.

That is `BOUNDARY_LEAK`. Why it earns an error in CI: reaching into internals makes the other
team's refactor **your** incident. Two ways out, and they are opposite in cost:

1. promote the shared piece to the published API (cheap, do this first);
2. move the shared piece down into a kernel/domain layer both features own (expensive, needs an
   owner — see `templates/adr-template.md`).

Publishing an event instead of calling is the third way: `checkout` emits `OrderPlaced`,
`shipping` reacts. Now nobody imports anybody, and the coupling becomes a schema you version.

## 4. Ports and adapters, in code

Everything a use case needs from the world is described in the use case's own vocabulary.

```python
# app/application/price_order.py  — rank 1, imports only rank 0 and its own port
from dataclasses import dataclass
from typing import Protocol

from app.domain.money import Money
from app.domain.order import Order, total_of


class OrderRepository(Protocol):
    def save_total(self, order: Order, money: Money) -> None: ...


class Clock(Protocol):
    def now(self) -> int: ...


@dataclass
class PriceOrder:
    repo: OrderRepository
    clock: Clock

    def run(self, order: Order) -> Money:
        money = total_of(order, self.clock.now())   # rule lives in the domain
        self.repo.save_total(order, money)          # side effect behind a port
        return money
```

```python
# app/tests/unit/test_price_order.py — no db, no mocks library, 3 milliseconds
class RecordingRepo:
    def __init__(self): self.saved = []
    def save_total(self, order, money): self.saved.append((order, money))


def test_total_is_persisted_once():
    use_case = PriceOrder(repo=RecordingRepo(), clock=FixedClock(1_700_000_000))
    money = use_case.run(order_with(items=[10_000, 5_000]))
    assert money == Money(15_000)
```

Verified on this pattern: `configs/architecture/demo/python` runs clean through **both**
`arch-scan` (100.0/100 once the deliberate bad file is removed) and import-linter
("Contracts: 2 kept, 0 broken"), and the same three rules exist for Java as an ArchUnit test
(`configs/architecture/demo/java`, exit 1 → exit 0).

Note what `PriceOrder` does **not** import: no `sqlalchemy`, no `fastapi`, no `datetime`. The
`Clock` port is the tell of a testable system — a use case that calls `datetime.now()` cannot be
tested at Tuesday 00:00 without monkeypatching.

## 5. Where the framework is allowed to touch you

Frameworks are not banned; they are **contained**. The cost of a framework is proportional to how
far its types travel.

| Type of framework contact | Allowed in | Never in |
|---|---|---|
| HTTP request/response shape | interface | application, domain |
| ORM entity as your domain model | prototype, and 2 more years of your life | anything that has rules |
| Query/mutation functions | infrastructure | domain |
| `Response`/`Request` in a use case signature | — | always a smell |
| Validation library in the domain | — | encode the invariant as a method/`from_raw()` instead |

"Impedance" argument (mapping an ORM row to a domain object costs a function) is real and worth
paying: the alternative is your business rules living inside a class whose constructor issues SQL,
and then a unit test needs a database.

## 6. Choosing boundaries by change coupling, not by nouns

The classic mistake: draw boxes from the domain nouns (`Order`, `Customer`, `Product`) and end up
with every use case touching every box — a distributed monolith inside one process.

Draw them by **what changes together**:

```bash
# 90 days of history: which folders change in the same commit?
git log --since='90 days ago' --name-only --pretty=format: -- src \
  | sort | uniq -c | sort -rn | head -20
git log --since='90 days ago' --pretty='%h' \
  | while read c; do git show --name-only --pretty=format: "$c" \
      | grep '^src/' | cut -d/ -f1-3 | sort -u | paste -sd' '; done \
  | sort | uniq -c | sort -rn | head -10
```

Two folders that appear in the same commit list over and over belong to one boundary. Two folders
that never co-occur should not import each other — and now you can write that down as a
`BOUNDARY_LEAK` case and enforce it.

## 7. What "over-engineered" means here

Clean architecture has a real failure mode: a `Hello World` with 14 files, 6 interfaces and a
container. Guard against it with the ladder — stop at the first rung that carries your load:

1. one file;
2. one folder per feature, functions in it (`playbook/02`–`03` rules already apply);
3. features + a `shared/` kernel;
4. layers inside each feature (`checkout/domain`, `checkout/application`, …);
5. module boundaries enforced in CI (this chapter);
6. separate deployables (only when 5 is solid — see `13-architecture-patterns.md`).

If you cannot name the day a rung pays for itself, do not build it. ADR required for rungs 4 and
above; `templates/adr-template.md` exists for exactly this argument.

## 8. Machine checks, and what they still miss

| Question | Tool | Gap you must cover in review |
|---|---|---|
| Import direction | `arch-scan`, dependency-cruiser, import-linter, ArchUnit, depguard | runtime reflection, DI containers, string-based imports |
| Layer cycles | same | cycles through the DI graph, not imports |
| Framework in the domain | same, plus `frameworkPackages` config | transitive: domain → helper → driver |
| Feature isolation | `BOUNDARY_LEAK` | shared mutable state, DB tables read cross-feature |
| "Is a use case in the right layer?" | nothing | a reviewer, using §2's smell table |

Enforcement is set up in `configs/architecture/` and wired in `configs/ci/` (`arch-scan` job).
Start with `--fail-on error` on **new code only** (baseline), then ratchet — same recipe as
chapter 9 for linters.

## 9. Read next

- `13-architecture-patterns.md` — which shape around these layers: modular monolith, events, CQRS, services.
- `14-design-patterns.md` — the small-scale vocabulary the layers are built from.
- Playbook: `playbook/10-clean-architecture.md` (exercises, quiz, rollout).
- Prompts: `prompts/11-architecture-review.md`, `prompts/12-boundary-designer.md`.
