# 03 · Functions — the smallest unit of design

> Rule 1: **functions must be small**. Rule 2: **smaller than you think**. Not for tidiness: so a
> reader holds the whole function in their head at once, and so each step can be tested alone.

## 1. The standard (these numbers are the CI thresholds)

| Criterion | Recommended | Warning | Must split |
|---|---|---|---|
| body lines | ≤ 20 | > 40 | > 70 |
| parameters | 0–2 | 3–4 | ≥ 5 |
| branch complexity (`if`/`for`/`case`/`&&`) | ≤ 6 | > 10 | > 15 |
| nesting depth | ≤ 2 | > 3 | — |
| jobs done | 1 | 2 | — |

Why these bands: working memory is small - the classic figure is 7 ± 2 chunks and the modern
estimate is closer to 4. A 40-line function with 3
branches at depth 3 is already at the limit before you added the business rule. The thresholds are
not taste, they are a budget for attention — and they ratchet (`maxFunctionLines` 40 → 30 once the
team is comfortable).

### Rule ↔ machine enforcement

| Rule this chapter teaches | `cc-scan` rule | Level | The fix |
|---|---|---|---|
| ≤ 40 lines, split above 70 | `LONG_FUNCTION` / `HUGE_FUNCTION` | warn / error | extract by business step |
| ≤ 3 params, hard fail ≥ 5 | `TOO_MANY_PARAMS` / `HARD_PARAMS` | warn / error | parameter object (§2.5) |
| flag argument | `BOOLEAN_PARAM` | info | two functions, or an enum |
| ≤ 10 branches, hard fail > 15 | `COMPLEXITY` / `HARD_COMPLEXITY` | warn / error | guard clauses, table-driven |
| ≤ 3 nesting levels | `DEEP_NESTING` | warning | invert + early return |
| no side effect in a query | *(human review)* | — | CQS (§2.2) |

Same rules elsewhere: ESLint `max-lines-per-function`, `max-params`, `complexity`, `max-depth`;
ruff `C901`, `PLR0913`, `PLR0912`, `PLR0915`; Go `funlen`, `cyclop`, `nestif`; Checkstyle
`MethodLength`, `ParameterNumber`, `CyclomaticComplexity`, `NestedIfDepth`.

**What the scanner miscounts** (so you know when to overrule it): brace-balanced function bodies
include nested closures, so a big arrow-function chain inside one function counts as one; Go
functions returning `(T, error)` look "long" because error handling is explicit — that verbosity is
idiomatic, so `funlen` for Go is set at 60, not 40; generators, decorators and `switch` expressions
are counted by line, not by thought. When the tool is wrong, use
`// cc-scan:allow LONG_FUNCTION — <reason>` on the declaration line rather than editing the config.

## 2. Seven rules, one repair each

### 2.1 One function, one level of abstraction

Mixing "orchestrate the order import" with "parse a CSV row" forces the reader to jump contexts
mid-line.

```ts
// ❌ three abstraction levels in one function
function importOrders(path: string) {
  const raw = fs.readFileSync(path, "utf8");
  const rows = raw.split("\n").slice(1);
  const orders: Order[] = [];
  for (const row of rows) {
    const cells = row.split(",");                 // level: parsing
    if (cells.length !== 4) continue;
    const order = { id: cells[0], amount: Number(cells[1]) * 100, currency: cells[2], status: cells[3] };
    if (order.amount <= 0) continue;              // level: validation
    orders.push(order);
  }
  db.order.createMany({ data: orders });          // level: I/O
  return orders.length;
}

// ✅ the orchestrator reads like an outline; every step is testable on its own
function importOrders(path: string): number {
  const orders = parseOrderCsv(readFileOrThrow(path)).filter(isImportable);
  return saveOrders(orders);
}

const readFileOrThrow = (path: string): string => {
  try { return fs.readFileSync(path, "utf8"); }
  catch (cause) { throw new OrderImportError(`cannot read ${path}`, { cause }); }
};

function parseOrderCsv(raw: string): Order[] {
  return raw.split("\n").slice(1).filter(hasFourCells).map(toOrder);
}

const hasFourCells = (row: string) => row.split(",").length === CSV_COLUMN_COUNT;
const toOrder = (row: string): Order => { const [id, amount, currency, status] = row.split(","); return { id, amountVnd: Number(amount) * CENTS_PER_VND, currency, status } as Order; };
const isImportable = (order: Order) => order.amountVnd > 0;
const saveOrders = (orders: Order[]) => db.order.createMany({ data: orders }).then(() => orders.length);
```

Notice what **disappeared**: the nested `try/catch`, the sprinkled `continue`, the `total`
variable that mutated through four stages. What **appeared**: names. That is the entire trade.

### 2.2 Command–Query Separation

A function either **returns data** or **changes state** — not both.

```java
// ❌ queries that mutate: the caller cannot tell whether the DB was written
if (user.checkAndMarkActive()) { ... }

// ✅ an honest query and an explicit command
if (user.isActive()) { activationLog.record(user.id()); }
```

```go
// ❌ Go version of the same trap: "Get" with a write inside
func (c *Cache) GetOrLoad(key string) Value   // silently inserts

// ✅ the insert is visible in the name of a second call
v, ok := c.Get(key)
if !ok { v = load(key); c.Put(key, v) }
```

Deliberate exceptions are allowed when the **name shouts it**: `pop()`, `next()`,
`Optional.orElseGet()`, `Reader.read()`. If the name says "take/next", a return value with a side
effect is honest. If the name says "get/find/compute", it is not.

### 2.3 No hidden side effects

```py
# ❌ a "get" that mutates a global and prints: untestable, and calling it twice is not safe
def get_discount(user):
    CACHE[user.id] = user.tier
    print("computing discount")
    return TIER_RATE[user.tier]

# ✅ pure input -> output; the chores move to a caller or to a command with an honest name
def discount_rate_for(user: User) -> Decimal:
    return TIER_RATE[user.tier]

def cache_user_tier(cache: TtlCache, user: User) -> None:
    cache[user.id] = user.tier
```

The practical test: **can I call this function twice in a test with the same input and assert the
same output?** If no, it has a side effect that belongs in the name.

### 2.4 A boolean flag argument is two functions wearing one trench coat

```ts
// ❌ every caller has to remember what true means
render(document, true)

// ✅ the names explain themselves; the shared part lives underneath
renderForScreen(document)
renderForPrint(document)
```

When the shared part is long, pass the *varying* piece instead of branching inside:

```ts
function renderWith(document: Doc, layout: LayoutStrategy) {
  const blocks = layout(blockSizes(document));
  return paint(document, blocks);
}
```

Two flags → you need an options object or an enum. Three flags → you are writing an API whose
documentation lives in other people's memory. Where the flag comes from config, let the **caller**
choose the function at the boundary and pass behaviour down (§2.7).

### 2.5 Parameters: 3 is the boundary, ≥5 is a design failure

```go
// ❌ six parameters; nobody is sure of the order
func Charge(order Order, amount float64, currency string, card Card, idempotencyKey string, retry int) error

// ✅ parameter object - compile-time safety, and a new field costs nothing later
type ChargeRequest struct {
	Order          Order
	Amount         Money          // the unit lives in the type, not in the reader's head
	Card           Card
	IdempotencyKey string
	MaxRetry       int            // default set in NewChargeRequest()
}

func Charge(req ChargeRequest) error { ... }
```

Recipe per language (Fowler's *Introduce Parameter Object*):

| Language | Use | Note |
|---|---|---|
| TS/JS | object literal + an `interface` | destructuring in the signature documents defaults inline |
| Python | `@dataclass(frozen=True, kw_only=True)` or keyword-only args `def charge(order, *, amount, card)` | keyword-only makes the call site self-documenting |
| Java/Kotlin | `record` (+ builder when there are > 6 optional parts) | a record is 1 line and gets `equals` for free |
| Go | one `struct` argument, or functional options for optional fields | `WithTimeout(2*time.Second)` reads better than four zero values |
| Rust | a struct + `#[derive(Builder)]` when optional | |

Two extras that are **not** parameter-object substitutes: `Map<String, Object> options` (an
untyped bag is how you delete the compiler), and `Config` classes with 40 fields that everyone
passes around whole (§ `08-design-principles.md`).

### 2.6 Return failures the right way

```ts
// ❌ codes and nulls: every caller must memorise the rule, and forgetting is silent
function findUser(id: string): User | null { ... }
const u = findUser(id); const name = u.name;   // 💥

// ✅ "absent" is a normal state -> Result/Option; "broken" -> throw
function requireUser(id: string): User {
  const user = users.byId(id);
  if (!user) throw new UserNotFound(id);        // exceptional: throw
  return user;
}
function findUser(id: string): User | undefined { return users.byId(id); }   // normal: undefined
```

Pocket rule: if the caller can do something useful here → return a `Result`; if they can only
stop or reroute → throw. Full treatment in `07-error-handling.md`.

### 2.7 The dense switch: pick one of three cures

```java
// ❌ adding a fee type means editing this function + three other places
double fee(Order o) {
    switch (o.kind) { case "NORMAL": return 0; case "EXPRESS": return 25000; case "FRAGILE": return 40000 + o.weightKg * 2000; default: throw new IllegalStateException(); }
}

// ✅ (1) table-driven: adding a fee type = adding a row, the logic never changes
private static final Map<DeliveryKind, FeeRule> FEE_RULES = Map.of(
        NORMAL, (order, config) -> 0.0,
        EXPRESS, (order, config) -> config.expressFee(),
        FRAGILE, (order, config) -> config.fragileBase() + order.weightKg() * config.fragilePerKg());

double fee(Order order, FeeConfig config) {
    return FEE_RULES.get(order.kind()).apply(order, config);
}
// ✅ (2) polymorphism when each kind also differs in validate/render/cancel
// ✅ (3) a strategy object when the rule is chosen at runtime (open-closed: 08-design-principles.md)
```

Do not over-correct: replacing three `if`s with twelve classes is also a defect. The ladder is
**table → polymorphism → strategy**, and you only climb when the variants genuinely vary in
behaviour (see `14-design-patterns.md`, "rule of three").

## 3. How to split: "extract until the name is obvious"

1. Find the seams at the **verbs you were about to comment**: `// validate the row`,
   `// compute the tax` — each one is a function waiting to exist.
2. Break the `if/else` structure first (guard clauses), then extract the statements inside.
3. Keep the public signature; the new functions start **private**. Small PR, no API break.
4. Pin the behaviour with a test **before** splitting. No test → write a characterization test for
   the current inputs first (`11-testing-for-clean-code.md`).
5. Test after every extraction, one commit per extraction. `git bisect` will thank you.

Naming pattern after the split: the orchestrator takes the **business** verb (`processRefund`),
the helpers take the **mechanism** verb (`buildRefundRequest`, `signPayload`, `toCsvRow`). When you
cannot name the extracted function, you have cut at a seam that is not real — pick a different one.

Three splitting heuristics that keep the result honest:
- **Don't create a function that is called once and is shorter than its name.** Inline it.
- **Don't extract for line count alone.** `step1/step2/step3` files have more lines and the same
  difficulty; the score must go up, not move (`clean-code-refactoring` §2).
- **Extract along the data, not the flow.** A helper that needs 6 parameters from its parent means
  the split is wrong — the data wants to travel together (introduce the object, then split again).

## 4. Signature review

| Good sign | Fix it |
|---|---|
| `vatOf(order): Money` | `calculate(o, t, x, y, z)` |
| `Money` carries amount **and** unit | `double amount` (the unit lives in the reader's head) |
| `throw new UserNotFound(id)` | returns `null`, `-1`, `"ERROR"` |
| `save(order): Promise<void>` | `save(order): Order` that also mutates its argument |
| `parse(input): Result<Order, ParseError>` | `parse(input, mode, strict, out)` |
| the last parameter is an injected dependency (test can replace it) | `new SmtpClient()` inside the body |
| `totalMinorVnd(...)` says the unit | `total(...)` — in which currency, in which scale? |
| idempotent on retry (`idempotencyKey` in the signature) | a charge function that assumes one call |

## 5. One complete refactor, in Python (the same shape applies to every stack)

**Before** — 62 lines in the original legacy version, 5 parameters, 3 jobs, 2 side effects:

```py
def handle_order(order, user, items, ship, notify):
    total = 0
    for it in items:
        if it.price > 0 and not it.blocked:
            total += it.price * it.qty
    if user.tier == "gold": total *= 0.9
    tax = total * 0.1
    order.total = total + tax
    db.save(order)
    if ship: shipping.send(order.id, order.address)
    if notify: email.send(user.email, f"order {order.id} created")
    return order.total
```

**After** — every function ≤ 8 lines, each testable alone, side effects only in the orchestrator:

```py
@dataclass(frozen=True)
class PricedOrder:
    order_id: str
    gross: Decimal
    vat: Decimal
    total: Decimal

def price_order(order: Order, items: Sequence[LineItem]) -> PricedOrder:
    """Pricing only - no DB, no network, so the test needs no mocks."""
    gross = subtotal(only_chargeable(items)) * discount_factor(order.customer)
    vat = gross * VAT_RATE
    return PricedOrder(order.id, gross, vat, gross + vat)

only_chargeable = lambda items: [i for i in items if i.price > 0 and not i.blocked]
subtotal = lambda items: sum((i.price * i.quantity for i in items), Decimal(0))
discount_factor = lambda customer: GOLD_MULTIPLIER if customer.tier is Tier.GOLD else Decimal(1)

# the application service - the one place allowed to have side effects
def place_order(cmd: PlaceOrder) -> PricedOrder:
    priced = price_order(cmd.order, cmd.items)
    orders.save(priced)
    if cmd.shipping is Requested.YES:
        shipments.schedule(priced.order_id)
    if cmd.notify is Requested.YES:
        notifier.receipt(priced.order_id, cmd.customer_email)
    return priced
```

**The measured difference** (not a feeling): one 62-line function → five functions ≤ 8 lines; side
effects concentrated in one place; `price_order` covered by 6 cases with no mock; adding a
"platinum" tier touches one table instead of the flow. The same pair of files in this pack
(`tools/demo/`) scores **72.0/100 before, 100.0/100 after**.

Note what the split also bought structurally: `price_order` has **no** import of `db`,
`shipping` or `email`. That is the seam `references/12-clean-architecture.md` turns into a rule —
the domain function is now testable and portable because it owns no infrastructure.

## 6. Recursion, loops and small exceptions to the numbers

- Prefer a loop when the recursion depth is bounded by user data (a tree of unknown height is a
  stack-overflow ticket). Prefer recursion when the structure is recursive by definition and the
  depth is small (`fs walk`, nested `AND/OR` predicates) — and write the base case first.
- A 25-line function that is **one** flat sequence of steps beats four 6-line functions whose
  names are `checkA`, `doB`, `thenC`. The metric is not the count of functions; it is whether the
  reader can stop thinking at each boundary.
- Data-transformation pipelines (`map/filter/reduce` chains) may exceed the line budget while
  staying single-purpose. That is what the allow-comment is for, honestly:
  `// cc-scan:allow LONG_FUNCTION — one declarative pipeline, see ADR-0012`.

## 7. Fifteen-minute exercise

1. Pick the longest function in your module. Write a **one-sentence** docstring for it.
   That sentence is the name of the orchestrator.
2. Underline the verb phrases in the sentence. Each one is a candidate sub-function.
3. Extract the first one, run the tests, commit. Repeat until the original is ≤ 20 lines.
4. Run `python3 tools/cc-scan.py . --max-fn-lines 20`. The score must go up; the diff must be
   renames and moves only (`git diff -w`).
5. Bonus, and the part teams skip: delete an extraction that did not earn its name — if inlining
   it makes the file clearer, inlining is the refactor.
