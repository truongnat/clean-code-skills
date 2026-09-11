# Session 10 · Clean architecture — layers that a machine can check

**Duration:** 60 min · **Output:** a layer map the team agrees on, `arch-scan` running in CI, one ADR
> Part II (sessions 10–12) is the system-level half of this playbook. Sessions 1–9 make a module
> readable; these make the codebase *changeable* across modules. Reference material:
> `../skills/clean-code/references/12-clean-architecture.md`.

## 1. Why readability is not enough

Two codebases. Both have 20-line functions, honest names, no magic numbers.

- A: to change the shipping fee you edit one file and run 4 unit tests. Takes 20 minutes.
- B: to change the shipping fee you edit `ShippingService`, which imports `OrderController` which
  imports `StripeClient`, and the test needs a Postgres container. Takes two days, "because of
  the coupling".

B is a **dependency** failure, not a code failure. No amount of renaming saves it. The whole of
session 10 is one sentence plus enforcement:

> Source code dependencies point inwards, towards the business rules.

## 2. The team standard (hard checklist)

🔧 Decide once, write into `CONTRIBUTING.md` and `arch-scan.config.json`:

- [ ] Four layers with ranks: `domain` 0, `application` 1, `infrastructure` 2, `interface` 3
      (rename them to what our folders already are — but keep rank semantics).
- [ ] A file may import layers of rank ≤ its own. No exceptions without a ticket.
- [ ] `domain` + `application` import **no** driver, ORM, web framework (`frameworkPackages` list).
- [ ] Everything the use case needs from the world is a **port declared in the use case's layer**.
- [ ] A feature is reachable only through its published module (`features/x/index.ts`, `api.py`, …).
- [ ] `python3 tools/arch-scan.py src --fail-on error` is red in CI for new violations only
      (freeze existing ones in the baseline / an `arch-scan:allow … — ticket` line with a date).
- [ ] Adding a layer or a boundary requires an ADR; adding a file to an existing layer does not.

## 3. Bad → Good, in one sitting

The exercise everyone remembers, because it turns "architecture" into a 10-minute diff.

```python
# BAD — app/domain/order.py: the rules need a database to be tested
from sqlalchemy import select
from app.infrastructure.db import session


def mark_paid(order_id: int) -> None:
    with session() as s:
        row = s.execute(select(OrderRow).where(OrderRow.id == order_id)).one()
        if row.status != "awaiting_payment":
            raise ValueError("cannot pay")
        s.execute(OrderRow.__table__.update().where(OrderRow.id == order_id).values(status="paid"))
```

```python
# GOOD — app/domain/order.py: the rule, in the domain's language
class Order:
    def mark_paid(self) -> None:
        if self.status is not OrderStatus.AWAITING_PAYMENT:
            raise OrderNotPayableError(order_id=self.id, status=self.status)
        self._transition_to(OrderStatus.PAID)
```

```python
# GOOD — app/application/pay_order.py: the use case owns the port
class PayOrder:
    def __init__(self, orders: OrderRepository) -> None:
        self.orders = orders

    def run(self, order_id: int) -> None:
        order = self.orders.require(order_id)
        order.mark_paid()
        self.orders.save(order)
```

```python
# GOOD — app/infrastructure/sql_orders.py: the adapter is the only place SQL exists
class SqlOrderRepository(OrderRepository):
    def require(self, order_id: int) -> Order:
        with self._session() as s:
            return to_domain(s.execute(select(OrderRow).where(OrderRow.id == order_id)).one())
```

Now the domain test has no imports to fake, and swapping the storage is a new adapter, not a hunt.
Measured version of this exact shape, with both checkers wired: `configs/architecture/demo/python`.

## 4. Exercises (each is a PR)

1. **Census (30 min, solo).** Run `python3 tools/arch-scan.py src --fail-on none`. Paste the layer
   census + dependency matrix into the team channel. Answer: which pair of layers has the most
   edges? Is `domain` importing anything outward — and if so, what did it cost to notice?
2. **Break the ring (1 PR).** Pick the worst `UPWARD_DEPENDENCY`. Invert it: declare the port in
   the inner layer, move the implementation into `infrastructure`. Do **not** change behaviour.
   Reviewers check only the direction, not the logic.
3. **Seal a feature (1 PR).** Find a `BOUNDARY_LEAK`. Either promote the target to the feature's
   public module, or move the shared piece into a kernel with a named owner. Write the one-line
   rule into `ARCHITECTURE.md`.
4. **Prove testability (1 PR).** Add a unit test for one use case with **zero** infrastructure
   imports and no container/DB. If it needs one, the design is not done; say so in the PR.
5. **Config drift drill (15 min).** Delete a layer folder from the repo but leave it in the config
   → `LAYER_UNUSED`. Add a new top-level folder not in the config → `UNCLASSIFIED_FILES`. Both are
   *meant* to be noisy: a config that nobody corrects is a diagram on a wall.

## 5. Quiz (answers at the bottom)

1. A use case needs the current time. Where does `datetime.now()` go?
2. `OrderController` imports `Order`. `Order` imports `OrderRow` (SQLAlchemy). How many rules does
   this break, and which one first?
3. Two features both need the same tax calculation. Name three options and pick one, with the cost.
4. `arch-scan` says the layering is clean. Does that prove the design is good? What does it prove?
5. Which single change makes "split this module into a service later" a file move instead of a rewrite?

## 6. DoD for this session

- [ ] `arch-scan.config.json` in the repo root, describing **real** folders
- [ ] CI runs `arch-scan --fail-on error`; the red list is empty or ticketed with dates
- [ ] `ARCHITECTURE.md` at the root, ≤ 120 lines (template: `../configs/architecture/ARCHITECTURE.md`)
- [ ] At least one use case tested with no infrastructure imports
- [ ] One ring or leak actually broken and merged (not planned — merged)

**Answers:** (1) behind a `Clock` port injected into the use case; read at the edge.
(2) two: `DOMAIN_FRAMEWORK_IMPORT` (ORM in the domain) and the model leaking persistence types;
fix the ORM one first, the controller import is legal (outer → inner). (3) promote to
`pricing`'s public API (cheap, couples both to a contract); move to a shared kernel with an owner
(neutral party, becomes load-bearing); duplicate until the second real user appears (YAGNI, keeps
features independent — the right answer while it is *coincidental* duplication). (4) No: it proves
the declared directions hold. Placement decisions, cohesion, and "is this the right boundary" are
still human. (5) making its imports legal and its data access go through its own ports.

## 7. Links

Reference: `../skills/clean-code/references/12-clean-architecture.md` · sub-skill:
`../skills/clean-architecture/SKILL.md` · tool: `../tools/arch-scan.py` (+ `../tools/tests/run_arch_checks.py`)
· configs & demos: `../configs/architecture/` · prompt: `../prompts/11-architecture-review.md`
· next session: `11-architecture-patterns.md`
