# 02 · Naming — 80% of "readable" lives here

> A name is an API. Get it wrong and no comment and no short function will save the reader.
> Machine-checkable: `cc-scan` plus `no-restricted-syntax` / `varnamelen` / `naming-convention`
> (see §7). Companion skill: `clean-code-naming`.

## 1. Five questions for every name

1. Does it say the **intent** (why it exists) and not only the **mechanism** (how it does it)?
2. Can you say it out loud and be understood, or does the reader have to decode
   (`usrPrflNm` → `userProfileName`)?
3. Is it greppable? `rg "\bdata\b"` in a mid-size repo returns hundreds of hits — a name nobody
   can search is a name nobody can follow.
4. Does it carry the **unit or type** where that matters (`timeout` → `timeoutMs`,
   `amount` → `amountMinorVnd`)?
5. Does it repeat context the caller already knows? `Order.orderTotal`, `user.userName`,
   `CustomerData` — the reader already has the noun; keep it in one place.

## 2. Name shape by role

| Role | Pattern | Good | Bad |
|---|---|---|---|
| value holder | noun + (kind/unit) | `unpaidInvoiceCount`, `balanceMinorVnd` | `n`, `amount2`, `tmp` |
| boolean | `is/has/can/should/was/needs` + positive form | `isExpired`, `hasDiscountApplied` | `flag`, `status`, `isNotActive` |
| command | verb + object | `chargeCard`, `resolveShippingZone` | `process()`, `handleData()`, `doPay()` |
| query | `find*/select*/compute*`, or a noun | `vatOf(order)`, `latestShipmentFor(order)` | `checkAndGetOrder()` (query *and* command) |
| filter predicate | state verb | `items.filter(isSellable)` | `items.filter(check)` |
| conversion | `to*/from*/as*` | `toMoneyMinor()`, `Money.fromCents()` | `convert()` |
| callback | `on<Event>` (registration) / `handle<Event>` (logic) | `onSubmit`, `handlePaymentFailed` | `submitFunc`, `myHandler2` |
| class owning a concept | business noun, never `Manager/Util/Helper` | `PricingPolicy`, `InvoiceRenderer` | `OrderManager`, `CommonUtils` |
| constant | `SCOPE + MEANING + UNIT` | `MAX_INLINE_ITEMS`, `VAT_RATE_PERCENT` | `LIMIT`, `TAX` |
| file / module | a capability, in the platform's case style | `pricing-policy.ts`, `shipping_rates.py` | `utils.ts`, `new.ts`, `final_v2.ts` |
| error type | `<WhatWentWrong>Error` | `InsufficientStockError` | `AppError("failed")` |
| event / past fact | past tense | `OrderShipped`, `payment_captured` | `OrderShipEvent`, `paymentDo` |

**Booleans have a trap.** `isNotActive` forces double negation at the call site
(`if (!user.isNotActive)`). Keep booleans positive and, when both states are meaningful, use an
enum instead — see §3.2.

## 3. The four common traps, each with its cure

### 3.1 The "-Manager" name — where everything gets dumped

`OrderManager` does not say what it decides, which is why it grows into a God class: nothing can
object to "one more thing in the manager". Name the decision instead: `OrderPricingPolicy`,
`ShipmentScheduler`, `InvoiceRenderer`. If you cannot pick one, the class has more than one job
(→ `08-design-principles.md`, Single Responsibility).

### 3.2 Negated names — the enemy of conditions

```ts
// ❌ two negations: the reader has to solve an equation
if (!order.isNotPaid) { ship(order); }

// ✅ positive name; do the negating once, at the point of use
if (order.isPaid) { ship(order); }
```

```py
# ❌ a boolean flag with two meanings          # ✅ name the states
if not is_test_mode:                            if mode is ExecutionMode.PRODUCTION:
    charge()                                        charge()
```

### 3.3 Generic names that swallow behaviour

`data`, `info`, `result`, `items`, `payload`, `obj`, `val` are only true within about three
lines. `processOrder(order)` is fine; `processOrder(data)` sends the reader into the body.

### 3.4 Abbreviations and private dialect

- No abbreviations only you understand: `usrPrfl`, `txnAmtVnd`. Keep the ones the industry
  already fixed: `id`, `url`, `http`, `vat`, and `qty` if the whole domain says "qty".
- **Ubiquitous language**: use the customer's words. If the PM says "sales order", the class is
  `SalesOrder` — not `SellRequest` + `OrderDTO` + `OrderModel` (three names, one concept, three
  chances to drift apart). See §6.

## 4. Words that should not appear in your repo

`do` · `what` · `ever` · `process` · `handle` · `perform` · `util(s)` · `common` · `misc` ·
`helper` · `manager` · `handler` (as a suffix for a class that owns data) · `data` · `info` ·
`obj` · `thing` · `item` (as a plural-only name) · `new` · `improved` · `v2` · `final` · `temp` ·
`tmp` · `foo`.

Exception: `Handler` *is* legitimate when the framework names the concept that way (HTTP request
handler, event handler) — the type has one entry point and no state. The test: does the name tell
me **what decision** lives there? ("Yes" → keep it.)

## 5. Bad → Good, in four languages

### TypeScript / JS

```ts
// ❌ the name tells you nothing; the units are in someone's head
export function calc(d: any, t: number, s: boolean) {
  const arr = [];
  for (let i = 0; i < d.i.length; i++) {
    const o = d.i[i];
    if (o.p > 0 && !o.b) arr.push(o.p * o.q);
  }
  let r = arr.reduce((a, b) => a + b, 0);
  if (s) r = r - 100000;
  return r * (1 + t);
}

// ✅ the names are the documentation; every name answers "what is it, in what unit"
export interface Cart { readonly items: readonly CartLine[] }
interface CartLine { priceVnd: number; quantity: number; blocked: boolean }

export function subtotalVnd(cart: Cart, taxRate: number, isVip: boolean): number {
  const gross = sellableLines(cart)
    .map(lineTotalVnd)
    .reduce((sum, lineTotal) => sum + lineTotal, 0);
  const vipDiscountVnd = isVip ? VIP_DISCOUNT_VND : 0;
  return (gross - vipDiscountVnd) * (1 + taxRate);
}

const sellableLines = (cart: Cart) => cart.items.filter((line) => !line.blocked && line.priceVnd > 0);
const lineTotalVnd = (line: CartLine) => line.priceVnd * line.quantity;
```

### Python

```py
# ❌ who is "u"? what is "f"? and the dict keys are a second, invisible schema
def get_x(u, f):
    r = []
    for i in u:
        if i["a"] > 18 and not i["b"]:
            r.append(i)
    if f:
        return r[:10]
    return r

# ✅ types + named constants + a docstring that states the one non-obvious rule
from dataclasses import dataclass

MIN_VOTING_AGE = 18
PREVIEW_SIZE = 10

@dataclass(frozen=True)
class Voter:
    age: int
    has_voted: bool

def eligible_voters(voters: list[Voter], limit: int | None = None) -> list[Voter]:
    """Voters who are old enough and have not voted yet; `limit` truncates for the preview page."""
    eligible = [v for v in voters if v.age >= MIN_VOTING_AGE and not v.has_voted]
    return eligible[:limit] if limit else eligible
```

### Java / Kotlin

```java
// ❌ (three smells at once: parameter-as-data name, magic numbers, generic verb)
public double p(List<Order> l, int m, boolean f) {
    double s = 0;
    for (Order o : l) { if (o.getStatus() == 2) s += o.getAmount(); }
    if (f) s = s * 0.9;
    return s;
}

// ✅ the status is a name, the discount is a policy, the units are in the names
enum OrderStatus { DRAFT, PAID, CANCELLED }

record PricingRequest(List<Order> orders, DiscountPolicy discount) {}

static double paidAmountOf(PricingRequest request) {
    double subtotal = request.orders().stream()
            .filter(order -> order.status() == OrderStatus.PAID)
            .mapToDouble(Order::amount)
            .sum();
    return request.discount().applyTo(subtotal);
}
```

### Go

```go
// ❌ unexported one-letter everything, no doc, magic 2
func P(o []*O, f bool) float64 {
	t := 0.0
	for _, x := range o { if x.s == 2 { t += x.a } }
	if f { t = t * 0.9 }
	return t
}

// ✅ exported names are full; short locals are fine only when the scope is <= 5 lines
type Status int

const (
	StatusPaid Status = iota + 1
)

// SumPaidAmount totals the orders that have been paid.
func SumPaidAmount(orders []*Order) (paid float64) {
	for _, order := range orders {
		if order.Status == StatusPaid {
			paid += order.Amount
		}
	}
	return paid
}
```

Go-specific rule: **no stutter**. `order.OrderManager` → `order.Manager` or better `order.Pricing`;
`user.UserClient` → `user.Client`. The package name is already in scope at the call site
(`order.Pricing` reads better than `order.OrderPricing`).

## 6. Ubiquitous language, and how to keep it honest

1. A 20–40 line glossary in `docs/domain-glossary.md`: `Order` (not `Sale`), `Invoice`,
   `Carrier` (not `Shipper`), `Payment` vs `Transaction` (different things — say which).
2. One concept = **one word at every layer**: code, DB column, API field, ticket, the email the
   customer receives. `order` ↔ `orders` ↔ `sale` is three fake concepts and N real bugs.
3. When the business corrects a word ("it is not a Deposit, it is an Advance"), rename in code
   **in the same sprint**. It is the cheapest refactor available and it keeps the glossary alive.
4. The glossary lives in `docs/`, not in a wiki nobody opens; a PR that introduces a domain word
   without a glossary line is incomplete (see `checklists/code-review.md`).

## 7. What a machine can catch (turn these on)

| Language | Rule | Catches |
|---|---|---|
| JS/TS | `@typescript-eslint/naming-convention` | camelCase / PascalCase / UPPER_CASE, type-parameter shape |
| JS/TS | `no-restricted-syntax` in `configs/js/eslint.config.js` | 1-letter names; suffixes `Data Info Manager Handler Processor Util(s) Object Obj Thing Stuff Foo Bar` → `No Data/Info/Manager/Util/Object names - they carry no meaning.` |
| Python | ruff `N`, `ERA001`, `PLC2401` | PEP8 violations, commented-out code, exotic identifiers |
| Java | Checkstyle `ConstantName`, `MethodName`, `AbbreviationAsWordInName` | convention drift, HTML-style capitals |
| Go | `revive var-naming`, `varnamelen` | stutter, 1-letter names in wide scopes |
| any | `cc-scan` | `MAGIC_NUMBER` (unnamed literal), `NEGATIVE_CONDITIONAL` (double negation) |

```bash
npx eslint . --rule '{"@typescript-eslint/naming-convention":"error"}'
ruff check --select N,ERA,PLC2401 .
python3 tools/cc-scan.py . --json | jq '[.findings[] | select(.rule=="MAGIC_NUMBER")] | length'
```

What no tool catches: a name that is **grammatically perfect and semantically wrong**
(`UserValidator` that also sends email). That is a review finding — and usually the signal that
two concepts share one type.

## 8. Safe rename (an operation, not an intention)

```bash
# 1) blast radius first
rg -n "\bcalc\b" --glob '!**/*.test.*'
# 2) IDE Shift+F6 / Rename Symbol - moves imports, tests and doc comments too; never hand-edit
# 3) public API? expand-contract: add the new name, @deprecated the old one, migrate callers,
#    delete in the next release (separate PR)
```

Then: tests green **before and after**, and `git diff -w` shows renames only.

## 9. Two-minute self-check on your last function

1. Is there a name a newcomer would need the body to understand?
2. Is a negated boolean standing inside an `if`?
3. Is there a number in the logic without a name (and a unit)?
4. Is there a `…Manager` / `…Util` / `…Data` that should be a capability name?

Four "no"s pass the chapter. One "yes" → fix it now in five minutes; it does not need its own PR.
Then, for practice: take the file at the top of your churn list and rename **only** — no logic
edit — and see how much of the file starts explaining itself.
