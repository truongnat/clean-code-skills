# 08 · Design principles: SOLID · DRY · KISS · YAGNI

> Principles are not traffic laws — they are **tools for predicting the cost of change**. Applied
> wrongly they are worse than not applied at all: they manufacture abstractions nobody needs.

## 0. The one-page version

| Principle | Ask this | Violation reads like | Machine hint |
|---|---|---|---|
| **S**RP | How many actors force me to edit this class? | `Paycheck` that computes, prints and saves | `LONG_FUNCTION`, `HUGE_FUNCTION`, `wc -l > 400` |
| **O**CP | Can I add a variant by adding a file/table row? | a `switch` touched in 4 places per new type | `COMPLEXITY`, `DUPLICATE_BLOCK` |
| **L**SP | Do the parent's tests pass on the child? | `UnsupportedOperationException`, `isinstance` in the parent | test suite + review |
| **I**SP | Does every implementer use every method? | `interface Worker { work; eat; sleep; kpi; }` | review; Go `go vet` won't help |
| **D**IP | Which side declares the interface? | domain importing `prisma`, `sqlalchemy`, `RestTemplate` | **`arch-scan` `UPWARD_DEPENDENCY`, `DOMAIN_FRAMEWORK_IMPORT`** |
| DRY | Is it the same *knowledge* or the same *lines*? | one `utils.ts` imported from 12 places for 5 reasons | `DUPLICATE_BLOCK` (a hint, not a verdict) |
| KISS | Is the boring thing enough? | a plugin system for three variants | `BLOCK_COMMENT`, `COMPLEXITY` |
| YAGNI | Does the second variant exist yet? | `AbstractXxxFactoryProvider` with no implementation | `LAYER_UNUSED`, unused-export lint |

Read the table bottom-up when arguing: **KISS and YAGNI decide whether the abstraction should
exist; SOLID decides how it looks once it must.**

## 1. S — Single Responsibility (one *reason to change*)

Not "a class does one thing" literally: **a class serves one actor/concept**. If three different
people can require the same class to change, it has three responsibilities.

```java
// ❌ one class, three reasons to change: pay rules, print layout, persistence
class Paycheck {
    double gross() { ... }                      // changes when labour law changes
    void print()   { System.out.println(...); }  // changes when the slip template changes
    void save()    { db.exec("INSERT ..."); }    // changes when the schema changes
}

// ✅ split by reason for change
class PaycheckPolicy { double gross(Money base, List<Allowance> a) {...} }   // domain
class PaycheckSlip   { String render(Paycheck p) {...} }                      // presentation
interface PaycheckRepository { void save(Paycheck p); }                        // persistence

class PaycheckService {
    PaycheckService(PaycheckPolicy policy, PaycheckSlip slip, PaycheckRepository repo) {...}
}
```

Detection question: **"who would make me edit this class?"** Two or more distinct answers (Legal,
Design, DBA) means split. A useful corollary: **co-location is also SRP** — a class that changes
when *one* thing changes should contain everything that changes with it; scattering a rule across
seven files is not "separation", it is shotgun surgery (see `10-code-smells-refactorings.md`).

## 2. O — Open/Closed (open for extension, closed for modification)

```ts
// ❌ adding a fee kind = editing this function + 4 other places + tests in the same file
function feeOf(order: Order): Money {
  if (order.kind === "NORMAL") return Money.zero;
  if (order.kind === "EXPRESS") return EXPRESS_FEE;
  throw new Error("unsupported kind");
}

// ✅ a strategy table: adding a fee kind = one new row, no logic edit
type FeeRule = (order: Order, ctx: PricingContext) => Money;

const FEE_RULES: Record<OrderKind, FeeRule> = {
  NORMAL: () => Money.zero,
  EXPRESS: (_order, ctx) => ctx.config.expressFee,
  FRAGILE: (order, ctx) => ctx.config.fragileBase.add(ctx.config.perKg.multiply(order.weightKg)),
};

const feeOf = (order: Order, ctx: PricingContext): Money =>
  FEE_RULES[order.kind]?.(order, ctx) ?? (() => { throw new UnsupportedOrderKind(order.kind); })();
```

Three ways to be closed, in increasing commitment:
1. **table/map of lambdas** — best when the variants are data (fees, rates, formats);
2. **sealed union + exhaustive match** (Kotlin/TS `never`/Python `match`) — the compiler is the
   reviewer: adding a variant **fails the build** until every site is updated, which is the opposite
   of the "silent default branch" you get with an `if`-chain;
3. **polymorphism/strategy objects** — when each variant also has state or several operations.

Cost warning: every abstraction is paid by readers (file hopping, worse stack traces) and only
saved once by writers. Close the class **where there are already ≥2 real variants or a high change
frequency**. Two variants do not justify a plug-in architecture; three do justify a table.

Registry-with-self-registration (a module that registers itself on import) buys option 1's
extensibility without the edit-in-the-middle, but it costs explicitness — the list is no longer
greppable. Take it only when third parties genuinely add variants; otherwise keep the table in one
file and let the compile break be the checklist.

## 3. L — Liskov Substitution (children must not betray parents)

```java
// ❌ the classic: Square extends Rectangle and changes setWidth's semantics
class Rectangle { void setWidth(int w); void setHeight(int h); int area(); }
class Square extends Rectangle {
    @Override void setWidth(int w) { side = w; }     // setWidth then setHeight -> wrong area
    @Override void setHeight(int h) { side = h; }
}

// ✅ model the *behaviour*, not the fields
interface Shape { int area(); }
record Rectangle(int width, int height) implements Shape { public int area() { return width * height; } }
record Square(int side) implements Shape { public int area() { return side * side; } }
```

Everyday signs of a broken LSP:

```python
def area(shape: Shape) -> int:
    if isinstance(shape, Square):        # <- the parent now knows about a child: contract broken
        return shape.side ** 2
    return shape.width * shape.height

class JsonConfig(Config):
    def get(self, key: str, default=None, *, indent=2):   # <- extra required kwarg: callers of
        ...                                               #    Config now break -> LSP broken
```

Fixes: put `area()` on each type (double dispatch), or use a sealed union + exhaustive match. On
the Python/TS side: a subclass may **widen** what it accepts and **narrow** what it returns — never
the reverse; strengthen not the precondition, weaken not the postcondition.

Fast test: **the parent's tests must pass unchanged on the child.** If you have to override a test,
the design is wrong, not the test. A second fast test: does anyone call it through the parent type
correctly without knowing the concrete class? If not, inheritance is being used for code reuse —
use composition.

## 4. I — Interface Segregation (do not force anyone to use what they don't need)

```java
// ❌ one god-interface: three implementers must write UnsupportedOperationException
interface Worker { void work(); void eat(); void sleep(); void reportKpi(); }

// ✅ small capabilities, composed as needed
interface Workable   { void work(); }
interface Reportable { void reportKpi(); }
class Robot implements Workable {...}              // no need to pretend to eat
class Human implements Workable, Reportable {...}
```

Go already enforces this culturally (`io.Reader` is one method; "the bigger the interface, the
weaker the abstraction"); in Python use a small `Protocol`:

```py
class SupportsClose(Protocol):
    def close(self) -> None: ...
```

In TS, split with **types** rather than fat interfaces, and accept parameters typed by the
capability they actually use (`function save(w: { write(s: string): void })` — the caller's logger,
file or socket all satisfy it, and your test needs no mock class).

The smell to watch is the opposite mistake: **an interface per method**. `Workable`/`Eat``/Sleep`
splits are not segregation, they are a directory full of one-line files. Segregate along *clients'*
needs, and if all clients use all methods, that is one honest interface.

## 5. D — Dependency Inversion (depend on the abstraction, not the detail)

```ts
// ❌ the domain imports the library: tests must mock a module, swapping the DB edits the domain
import { prisma } from "../db";
class OrderService { async ship(id: string) { await prisma.order.update({ where: { id }, data: { status: "SHIPPED" } }); } }

// ✅ the domain declares the PORT, infrastructure supplies the ADAPTER, the composition root wires them
interface OrderRepository { markShipped(id: OrderId, at: Date): Promise<void>; }

class OrderService {
  constructor(private readonly orders: OrderRepository, private readonly clock: Clock) {}
  async ship(id: OrderId) { await this.orders.markShipped(id, this.clock.now()); }
}

// main.ts - the ONLY place that knows Prisma/Postgres exist
new OrderService(new PrismaOrderRepository(prisma), new SystemClock());
```

Measured benefit: `OrderService` tests run with **no DB and no module mocking** (the fake is an
object literal). Cost: one interface + one adapter. It is worth it — and this is the principle that
turns into a machine gate: the dependency rule in `references/12-clean-architecture.md`, checked by
`arch-scan` (`UPWARD_DEPENDENCY`, `DOMAIN_FRAMEWORK_IMPORT`, `LAYER_CYCLE`) and, in a real project,
by import-linter/ArchUnit/`depguard`.

Two nuances people get wrong:
- **The owner of the concept owns the interface.** If infrastructure declares the port and the
  domain imports it, the dependency still points outward — that is not DIP, that is renaming.
- **Inject collaborator behaviour, not data.** `Money`, `OrderId`, config values are arguments of
  the call; `Clock`, `Mailer`, `OrderRepository` are collaborators. A constructor with 14 injected
  `Config` fields is a god object in a tie.

## 6. DRY — do not duplicate *knowledge*, not *lines*

```py
# ❌ "DRY-ing" two coincidentally identical places creates a false coupling
def format_user_name(u): return f"{u.first} {u.last}"
user_menu_label = format_user_name(u)     # UI copy
audit_log_line  = format_user_name(u)     # legal log: may need "last, first (id)" tomorrow
```

Same text, **different reasons to change** → not a DRY violation. Merging them means the legal log
changes when a designer tweaks a label. That is the most common DRY mistake, and it is the reason
`DUPLICATE_BLOCK` in `cc-scan` is a *warning with a hint*, not an error: the tool sees lines, only
you can see intent.

Real DRY violations (one rule living in two places):
- a tax formula copied into a service and into a stored procedure;
- the same phone regex in the front end and the back end;
- the magic number `86400` in three files;
- the same status transition table in the client, the API and the DB check constraint.

```py
# ✅ one source of truth, everything else derives from it
TAX_RATE = Decimal("0.10")            # src/billing/policy.py - the only definition
# the FE fetches /pricing/config, which returns this rate - it never hard-codes one
# the reporting view reads the config table this policy generates
```

**Single source of truth beats DRY**: do not merely merge code, merge the *place where the fact is
decided*. Three flavours, in ascending value: (1) shared function (removes copy-paste), (2) shared
type/enum (removes drift in shape), (3) shared authority — one config row, one policy object, one
generated artefact (removes drift in **behaviour**). If you cannot say which of the three you are
doing, you are probably doing (1) and will regret it.

## 7. KISS — simple means *fast to read*, not *few lines*

```ts
// ❌ one line, but the reader must pause and evaluate
const r = arr.filter(x => x.a && !x.b ? x.c > 0 : x.d < 5).map(({c}) => c).reduce((p,v)=>p+v,0) || 0;

// ✅ more lines, one continuous read
const chargeable = arr.filter(line => line.hasAmount && !line.blocked);
const totals = chargeable.map(line => line.amountVnd);
const totalVnd = totals.reduce(sum, 0);

function sum(acc: number, value: number) { return acc + value; }
```

The "boring enough" ladder — pick the first row that solves today's measured problem:

| Need | Don't | Do |
|---|---|---|
| 3 variants | a plug-in system, reflection | a `switch` + table, or a union type |
| caching | hand-written LRU with eviction | a `Map` with a TTL → Redis **when a measurement justifies it** |
| validation | your own mini-DSL | an existing schema validator (zod / pydantic / Bean Validation) |
| state machine | a framework your team invented | a 10-line transitions object, or a library **plus tests of the transitions** |
| concurrency | four Promise layers and a queue | call it in sequence; measure; then optimise the one hot path |
| configuration | a YAML file with anchors and templates | code with types, defaults and tests |
| extensibility by outsiders | an SPI + classloader | a documented port + a contribution guide |

KISS has a second, rarer meaning worth honouring: **the smallest thing that is honest**. A function
that silently catches everything is "simpler" than one that returns `Result<_, Error>` and is a
liability. Simplicity is measured in reader-seconds, not in symbols.

## 8. YAGNI — you aren't going to need it

```java
// ❌ "for convenience later": three dead files, no tests, still read by everyone refactoring
abstract class AbstractOrderHandler implements OrderHandler { /* 40-line template method */ }
interface OrderEventPublisherFactoryProvider {...}
class OrderHandlerRegistryBuilder {...}

// ✅ today: one class, clear method. When variant #2 shows up - then split.
class OrderHandler { void handle(Order order) {...} }
```

Three questions that cut YAGNI dead:
1. Does the second variant **exist**, or did you imagine it? (imagined → do not write it)
2. If we do not abstract now, what does the refactor cost later? (10 minutes → stop designing)
3. Is there a **signal** (a ticket, a contract, a count of past changes) that it is coming?

**The exceptions to YAGNI** — places where paying early is correct, because the cost of changing
later is external and permanent: the published **API shape**, a **DB schema** (migrations are
one-way doors), **file/event formats** already on the wire, **security boundaries**, and the
**layer boundary** between domain and infrastructure (`references/12-clean-architecture.md`). Note
what these have in common: they are all *contracts with someone who is not in this repo*.

## 9. Where the principles conflict — and the resolution

| Conflict | Resolution |
|---|---|
| DRY vs SRP ("put it all in one class to avoid duplication") | DRY at the level of **knowledge**, SRP at the level of **responsibility**: separate classes, one shared policy/function |
| OCP vs YAGNI (abstract early) | Abstractions come from **repetition that exists** (rule of three), not from imagination |
| KISS vs DIP (DI looks "complex") | In a small module, a function taking its collaborator as a parameter **already is** DI; you need no six-file container |
| SRP vs file count | Splitting a file never cleans code by itself; if the name does not state the reason for the split, the split is not finished |
| DRY vs KISS (a shared abstraction with 5 flags) | A general thing with switches inside is *both* duplicated knowledge and unreadable: keep two simple copies and a test that pins them equal |
| ISP vs DIP (many tiny ports) | One port per **aggregate the use case owns**, not one per method; extra ports are adapters' business |

A procedure when two principles point opposite ways: name the **change you expect**, its
**frequency**, and the **reversal cost**. Expected-but-reversible → take the simple branch now.
Expected-and-irreversible (a published contract, a schema) → pay for the abstraction now. Not
expected → YAGNI wins, full stop.

Someone quoting "but SOLID says…" at you in review is answerable with the same three questions:
*which change does this design serve, how often does it arrive, and what does removing the
abstraction cost?* If nobody can answer, the abstraction is decorative — `should`-level finding,
open an issue or delete it.

## 10. Three-minute class diagnosis

1. List **three things** that would force this class to change. How many distinct owners? (SRP)
2. Find every `if (type === …)` / `switch` on a type. Is there already a second variant? (OCP/YAGNI)
3. Does any subclass override a method only to `throw new UnsupportedOperationException()`? (LSP/ISP)
4. Any `new XxxClient()` inside the class? Is the dependency inverted yet? (DIP)
5. Any block copied from somewhere else? Same knowledge or different? (DRY)
6. Run the gates on the module and read the numbers, not the vibes:
   `python3 tools/cc-scan.py src/<mod> --json | jq '{score, counts}'` and
   `python3 tools/arch-scan.py src --fail-on none | sed -n '1,12p'`.

## 11. Exercise (15 minutes, pairs)

Take the class with the highest churn in your repo. For each principle S-O-L-I-D, spend **two
minutes** deciding: satisfied / violated / not applicable — and write one sentence of evidence for
each verdict (`"violated: Legal and Design both edit this file; 14 commits from 3 authors"`). Then
propose **one** change, with the expected cost of *not* doing it. Two rules: you may not propose more
than one change, and you may not propose an abstraction whose second variant you cannot point to in
the code or in a ticket. That constraint is this whole chapter in one sentence.
