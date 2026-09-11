# Snippets: wrong → right (copyable, four languages)

> Each block maps to one section of the clean-code tree. Use it for a fast team demo,
> or whenever you want to *see* a rule instead of reading a description of it.

---

## 1 · Naming — the name is the documentation

```ts
// ❌ WRONG
function p(u: any, t: number, f: boolean) {
  const d = u.d, r = [];
  for (let i = 0; i < d.length; i++) { if (d[i].a > t && !d[i].b) r.push(d[i]); }
  if (f) return r.slice(0, 10);
  return r;
}

// ✅ RIGHT
function eligibleInvoices(user: User, minAmountMinor: number, limit: PreviewLimit | null): Invoice[] {
  const eligible = user.invoices.filter((inv) => inv.amountMinor > minAmountMinor && !inv.voided);
  return limit ? eligible.slice(0, limit.value) : eligible;
}
```

```py
# ❌ WRONG
def get_data(x, y, z):
    a = [i for i in x if i["s"] == 2 and i["v"] > y]
    if z: a = a[:10]
    return a

# ✅ RIGHT
PAID = OrderStatus.PAID
PREVIEW_SIZE = 10

def paid_orders_over(orders: list[Order], min_value: Decimal, preview: bool) -> list[Order]:
    paid = [o for o in orders if o.status is PAID and o.value > min_value]
    return paid[:PREVIEW_SIZE] if preview else paid
```

```java
// ❌ WRONG  ->  ✅ RIGHT   (Java: unit suffixes, no abbreviations)
double amt(List<O> l)                                  → double totalAmountVnd(List<Order> orders)
String nm                                            → String customerDisplayName
int n                                                → int unpaidInvoiceCount
```

```go
// ❌ WRONG: stutter + single letters outside a short loop
func (o *Order) OrderTotal() float64 { t := 0.0; for _, x := range o.L { t += x.P } ; return t }

// ✅ RIGHT: the method name does not repeat the type; every name means something
func (o *Order) SubtotalVND() float64 {
	var subtotal float64
	for _, line := range o.Lines {
		subtotal += line.Price
	}
	return subtotal
}
```

---

## 2 · Magic number -> a named constant

```ts
// ❌ WRONG
if (seconds > 86400) return "stale";
const rate = 0.1;
setTimeout(cb, 1500);

// ✅ RIGHT
const STALE_AFTER_SECONDS = 60 * 60 * 24;
const VAT_RATE = 0.1;
const RETRY_JITTER_MS = 1_500;
if (ageSeconds > STALE_AFTER_SECONDS) return "stale";
setTimeout(cb, RETRY_JITTER_MS);
```

```go
// ❌ if total > 500000 { free = true }
// ✅ RIGHT
const freeShippingThresholdVND = 500_000
if total > freeShippingThresholdVND { free = true }
```

> Note: `cc-scan` does **not** report a number on a constant-declaration line
> (`const VAT_RATE = 0.1`, `VAT_RATE: Final[float] = 0.1`) - that line is the solution.

---

## 3 · Functions - small, one job, command and query apart

```py
# ❌ WRONG: 60 lines, 3 jobs - computes, writes and sends mail
def handle_order(order, user, items, ship, notify): ...

# ✅ RIGHT: an orchestrator + 3 independent steps, each one testable
def place_order(cmd: PlaceOrder) -> PricedOrder:
    priced = price_order(cmd.order, cmd.items)        # pure, no I/O
    orders.save(priced)                               # command
    if cmd.wants_shipping: shipments.schedule(priced.id)
    if cmd.wants_notify:   notifier.receipt(priced.id, cmd.email)
    return priced
```

```ts
// ❌ WRONG: flag argument + a hidden side effect
function render(doc: Doc, isPrint: boolean) { db.touch(doc.id); return isPrint ? printLayout(doc) : screenLayout(doc); }

// ✅ RIGHT
function renderForScreen(doc: Doc): string { return paint(doc, screenLayout(doc)); }
function renderForPrint(doc: Doc): string  { return paint(doc, printLayout(doc)); }
function markRendered(doc: Doc): Promise<void> { return db.touch(doc.id); }   // the chore is separate
```

```java
// ❌ 4 parameters + 1 boolean: nobody remembers the order
void charge(String userId, double amount, String currency, Card card, boolean retry) { … }

// ✅ Parameter Object (record) + policy
record ChargeRequest(UserId userId, Money amount, Card card, RetryPolicy retry) {}
void charge(ChargeRequest request) { … }
```

---

## 4 · Comments - say why, not what

```ts
// ❌ WRONG
// check whether the user is valid
if (u.age > 18 && !u.banned) { … }     // send mail
sendMail(u);
// total = total * 1.1;

// ✅ RIGHT
// Age is computed from the birth date in the customer's timezone (AC-311): the UTC+14 edge case.
if (voter.canReceiveBallot()) {
  dispatchBallot(voter);
}
```

```py
# ❌ WRONG
def f(x):   # f(x) = x * 1.1
    return x * 1.1

# ✅ RIGHT
VAT_RATE = Decimal("0.10")   # 10% VAT per Decree NN-2026; a change is one PR plus tests

def gross_of(net: Decimal) -> Decimal:
    """Adds VAT to the net price. Net is already in minor units, so no rounding here."""
    return net * (Decimal(1) + VAT_RATE)
```

---

## 5 · Formatting - let the machine decide

```ts
// ❌ WRONG: one line of 168 characters, three decorative indent levels
const shipment = await createShipment(orderId, address, Carrier.DHL, Insurance.none, PaymentMethod.COD, note, locale, currency);

// ✅ RIGHT: prettier-friendly, one argument per line
const shipment = await createShipment({
  orderId,
  address,
  carrier: Carrier.DHL,
  insurance: Insurance.none,
  payment: PaymentMethod.COD,
  note,
  locale,
  currency,
});
```

```py
# ❌ WRONG: a 90-line function with no rhythm; ✅ RIGHT: steps apart, one blank line between
def sync_invoice(order: Order) -> Receipt:
    """Pushes the invoice to the partner; system errors are raised so the caller retries."""
    payload = build_payload(order)
    response = post_with_timeout(payload)          # only this part can fail on the network

    receipt = Receipt.parse(response.json())
    invoices.attach(order.id, receipt)
    return receipt
```

---

## 6 · Objects and data structures - do not dissect your neighbour

```ts
// ❌ WRONG (Law of Demeter): the caller knows the internals of order
const city = order.customer.addresses.find(a => a.kind === "BILLING")?.city;

// ✅ RIGHT: order owns the meaning of "billing address"
const city = order.billingCity();
```

```java
// ❌ WRONG: a POJO with 20 getters while every rule sits in the service (anemic)
public class Order { public String getStatus() {…} public double getAmount() {…} }
if ("PAID".equals(o.getStatus()) && o.getAmount() > 500_000) ship(o);

// ✅ RIGHT: data and behaviour together, the invariant defends itself
public final class Order {
    public boolean isShippable() { return status == PAID && amount.isGreaterThan(SHIPPING_FREE_THRESHOLD); }
    public void markShipped(TrackingNumber t) { /* state check + emit event */ }
}
```

---

## 7 · Exceptions - nothing swallowed, no error codes

```py
# ❌ WRONG
try:
    gateway.charge(order.total)
except Exception:
    pass                      # "so it does not crash"

# ✅ RIGHT
try:
    return gateway.charge(order.total)
except TimeoutError as err:
    metrics.increment("gateway.timeout")
    raise GatewayUnavailable(f"timeout while charging order {order.id}") from err
except CardDeclinedError as err:
    raise PaymentDeclined(f"order {order.id} declined: {err.reason}") from err
```

```java
// ❌ return -1 when nothing is found   ->   ✅ Optional or a specific exception
Optional<Order> found = orders.findById(id);
return found.orElseThrow(() -> new OrderNotFound(id));

// ❌ throw new RuntimeException(e)   ->   ✅ keep the type and the cause
throw new InvoiceSyncException(orderId, e);
```

```go
// ❌ WRONG: swallowing the error
result, _ := s.repo.Save(ctx, order)

// ✅ RIGHT: wrap with context, let the caller classify with errors.Is
if err := s.repo.Save(ctx, order); err != nil {
	return fmt.Errorf("save order %s: %w", order.ID, err)
}
```

```ts
// ❌ WRONG: throwing mid-body, uncatchable because it is inside a Promise
users.byId(id).then((u) => { if (!u) throw new Error("no user"); });

// ✅ RIGHT: await, with a specific type
const user = await users.byId(id);
if (!user) throw new UserNotFound(id);
```

---

## 8 · SOLID / DRY / KISS / YAGNI

```ts
// ❌ WRONG (OCP): adding a fee kind means editing this function + 4 other places
function feeOf(o: Order) { if (o.kind === "NORMAL") return 0; if (o.kind === "EXPRESS") return 25000; throw new Error("bad"); }

// ✅ RIGHT: a rule table - open to add, closed to edit
const FEE_RULES: Record<OrderKind, (o: Order, ctx: PricingContext) => Money> = {
  NORMAL: () => Money.zero,
  EXPRESS: (_o, ctx) => ctx.expressFee,
};
const feeOf = (o: Order, ctx: PricingContext) => FEE_RULES[o.kind]?.(o, ctx) ?? (() => { throw new UnsupportedKind(o.kind); })();
```

```py
# ❌ WRONG (fake DRY): merging two places that look alike but change for different reasons
def format_name(user): return f"{user.first} {user.last}"
audit_line = f"{format_name(user)} | {ip}"        # legal record: tomorrow it must read "last, first (id)"
menu_label = format_name(user)                     # UI

# ✅ RIGHT: two functions with honest names - *accidental* duplication is not a DRY violation
def user_menu_label(user: User) -> str: return f"{user.first_name} {user.last_name}"
def audit_identity(user: User) -> str:  return f"{user.last_name}, {user.first_name} (id={user.id})"
```

```java
// ❌ WRONG (YAGNI): an interface with one implementation and an abstract factory "for later"
interface OrderHandlerFactoryProvider { OrderHandlerFactory create(boolean async); }

// ✅ RIGHT: one class with a clear job; split when the second variant shows up
final class OrderHandler { void handle(Order order) { … } }
```

---

## 9 · Code health - tidy up before merge

```diff
- console.log("debug", order);
- // const oldTotal = subtotal * 1.21;
- // TODO: refactor sau
+ // TODO(AC-1240, minh): split the renderer from the calculator - issue filed, does not block this PR
+ if (!Number.isFinite(totalVnd)) { throw new InvalidAmount(order.id, totalVnd); }
```

```bash
# the three commands to run before clicking Create pull request
python3 tools/cc-scan.py . --fail-on error
npx prettier --check . && npx eslint . --max-warnings=0
rg -n "console\.(log|debug)|debugger|TODO(?!\()" src | head
```
