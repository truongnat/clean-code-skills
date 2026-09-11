---
name: clean-code-naming
description: >-
  Rename variables, functions, classes and files for clarity and consistency: kill hard
  to read abbreviations, kill Data/Info/Manager/Util names, remove magic numbers and
  magic strings, and keep one ubiquitous language across code, API and database. Use when
  the user says "rename", "name this", "pick a better name", "this code is hard to read
  because of names", or when a reader has to open a function body to understand what a
  name means.
metadata:
  version: "1.1.0"
  companion: "clean-code"
---

# Naming & magic-value refactoring

Renaming is the **riskiest** refactoring for a junior (public API breaks) and the
**highest-yield per minute** of any of them (no behaviour can change). This skill is the safe
procedure plus the vocabulary.

## 1. The safe rename procedure (never hand-edit + search/replace)

1. **Scope it.** Is the name public? `rg -n "\boldName\b" | wc -l` — the count is the size of
   the change, before you start.
2. **Find the intent.** Read the body and answer one question: *what does this actually do?*
   That sentence is the new name. If you cannot answer it in one sentence, the problem is not
   the name — use `clean-code-refactoring` first.
3. **Rename with the IDE/LSP** (declaration + references + tests + doc comments), not `sed`.
   For a **public** API use **expand–contract**: add the new name → alias/deprecate the old one
   → migrate callers → delete the old name in a separate PR.
4. Run the tests → commit `refactor: rename getData -> fetchPendingOrders (no behaviour change)`.

```bash
# before and after: count the blast radius so nothing is left behind
rg -n --count-matches "\b(getData)\b" src | sort -t: -k2 -rn | head
```

## 2. Name shape (choose one per language, keep it for the whole repo)

| Role | JS/TS | Python | Java/Kotlin | Go |
|---|---|---|---|---|
| function | `verbNoun` camelCase | `verb_noun` | `verbNoun` | `VerbNoun` / `verbNoun` |
| type/class | `Noun` PascalCase | `Noun` PascalCase | `Noun` | `Noun` |
| field | `camelCase` | `snake_case` | `camelCase` | `camelCase` |
| constant | `UPPER_SNAKE` (or `PascalCase` at module level) | `UPPER_SNAKE` | `UPPER_SNAKE` | `camelCase` unexported / `PascalCase` |
| file | `kebab-case.ts` | `snake_case.py` | `PascalCase.java` | `snake_case.go` |
| boolean | `is/has/can/should…` | as JS | as JS | `isReady` (never `isBReady`) |

Go-specific: **no stutter** — `order.Order` → `order.Info`, `user.UserClient` → `user.Client`.
Python-specific: a leading `_` means "internal", and a module named `utils`/`common` is a
smell in every language.

## 3. Most-used rename table

| Old name (the problem) | New name (the intent) |
|---|---|
| `data`, `payload`, `result`, `info` | `createOrderRequest`, `pricedInvoice`, `taxBreakdown` |
| `flag`, `check`, `status` (boolean) | `hasDiscountApplied`, `isAwaitingPayment` |
| `tmp`, `new`, `val2`, `o2` | name the **role**: `draftOrder`, `confirmedOrder` |
| `manager`, `handler`, `util`, `common`, `helper` | name the decision: `PricingPolicy`, `InvoiceRenderer`, `RetryScheduler` |
| `list`, `arr`, `items` | `pendingShipments`, `cartLines` |
| `process`, `handle`, `doX`, `execute` | the specific verb: `charge`, `reconcile`, `voidInvoice` |
| `time`, `delay`, `amount`, `size` | `timeoutMs`, `retryDelaySeconds`, `amountMinorVnd`, `bodyBytes` |
| `usr`, `cust`, `txn_amt`, `prc` | `user`, `customer`, `transactionAmountMinor`, `price` |
| `data1`/`data2`, `res1`/`res2` | name what differs: `rawResponse`, `decodedResponse` |
| `tempVar`, `foo`, `bar` (in production) | delete the variable, or name the step it represents |

**Suffix names are not names.** `Manager`/`Handler`/`Util`/`Common`/`Data` describe the author's
lack of an idea, and they are the reason a class grows to 500 lines: nothing can object to
"one more thing in Util". `configs/js/eslint.config.js` blocks thirteen such suffixes
(`Data`, `Info`, `Manager`, `Handler`, `Processor`, `Util(s)`, `Object`, `Obj`, `Thing`, `Stuff`, `Foo`, `Bar`) through `no-restricted-syntax`; verified on the pack's own samples — it reports `No Data/Info/Manager/Util/Object names - they carry no meaning` on `bad-structure.ts`, while `good-example.ts` stays at 0 problems.

## 4. Unit and scale belong in the name

Money, time and byte counts cause real incidents when the unit is only in someone's head.

```ts
- const amount = 50000;              // 50000 of what? VND? minors? a percentage?
+ const amountMinorVnd = 500_000_00;
- const delay = 5;
+ const retryDelaySeconds = 5;
- if (body.length > 1e6) …
+ if (byteLength(body) > MAX_REQUEST_BYTES) …
```

Money: store **minor units in an integer** (`amountMinorVnd`) or use a `Money` value object;
never `double`. A `float` for money is a naming problem and a type problem at once.

## 5. Magic values → names (sometimes this *is* the refactor)

```ts
// ❌                                              // ✅
if (u.t === 3) { … }                        if (u.tier === UserTier.PREMIUM) { … }
const t = 86400;                            const SECONDS_PER_DAY = 60 * 60 * 24;
if (x > 500000) …                           if (totalVnd > FREE_SHIPPING_THRESHOLD_VND) …
setTimeout(fn, 1500)                        setTimeout(fn, TAX_PROVIDER_TIMEOUT_MS)
"PAID" / "paid" / "Paid"                    enum OrderStatus { Paid = "PAID" }   // one spelling
```

**Strings are more dangerous than numbers**, because the compiler cannot help you: three
spellings of `"paid"` become three behaviours, and only one of them is tested. Collect them:
`as const` object + union type (TS), `StrEnum`/`Enum` (Python), `enum`/`sealed interface`
(Java/Kotlin), typed constants + `iota` (Go).

Where to put the constant: next to the thing it qualifies (module top, or inside the type that
owns it) — not in a global `constants.ts` that becomes the new `Util`.

## 6. Naming tests (a name is a specification)

```ts
it("rejects a coupon already redeemed by this customer", …)          // good: behaviour + case
it("returns 409 with code COUPON_REDEEMED when the same coupon is applied twice", …)

it("testPlaceOrder", …)      // ❌ says nothing
it("works", …)               // ❌
it("test1", …)               // ❌ - three tests named test1 in three files
```

One behaviour per test; the name states the condition and the outcome. `should`, `when`,
`and` are filler — prefer `deniesX when Y`. For parameterised tests include the case in the
name (`compute_tax: mixed cart, zero rating`), otherwise the failure line points at an index
and nobody knows which case broke.

## 7. Ubiquitous language (name with the domain's words)

1. Write a 20–40 line **glossary** in `docs/domain-glossary.md`: `Đơn hàng = Order` (not
   `Sale`), `Hoá đơn = Invoice`, `Bên vận chuyển = Carrier` (not `Shipper`). Two words for one
   concept = one of them is a lie.
2. One concept = **one word at every layer**: code, DB column, API field, Jira, the email the
   customer reads. `order` ↔ `orders` ↔ `sale` is three fake concepts and N real bugs.
3. When the product manager corrects a word ("it's not a Deposit, it's an Advance"), rename
   it in code **immediately**. That is the cheapest refactor you will ever do, and the only
   one that buys you the next requirement for free.
4. Do not translate the domain's English into your own shorthand: if the business says
   "partial shipment", the class is `PartialShipment`, not `pShip`.

## 8. Machine enforcement

```bash
python3 tools/cc-scan.py . --json \
  | jq '[.findings[] | select(.rule|test("MAGIC_NUMBER|NEGATIVE_CONDITIONAL"))] | length'
npx eslint . --rule '{"@typescript-eslint/naming-convention":"error"}'
ruff check --select N,ERA,PLR2004 .                 # PEP8 naming, commented-out code, magic values
checkstyle -c configs/java/checkstyle.xml src/main   # MagicNumber, AbbreviationAsWordInName
```

`NEGATIVE_CONDITIONAL` in `cc-scan` catches `if (!a && !b)`; the fix is a positive name —
`isBlockedOrVoided()` — which turns a double negative into vocabulary. A name that is a
question (`isValid`) beats a name that is a negation (`isNotInvalid`).

## 9. Definition of done for a rename PR

- [ ] No single-letter names outside loops of ≤ 3 lines
- [ ] No empty suffixes (`Manager`/`Util`/`Helper`/`Common`/`Data`/`Info`/`Object`)
- [ ] Every literal inside logic has a name; constants sit at the top of the module with their unit
- [ ] Glossary updated if a new domain word appeared
- [ ] Tests green **before and after**; the diff contains renames only (confirm with `git diff -w`)
- [ ] Public API: no breaking change, or a changelog entry + deprecation cycle
- [ ] `cc-scan` on the changed files reports no new `MAGIC_NUMBER` / `NEGATIVE_CONDITIONAL`
