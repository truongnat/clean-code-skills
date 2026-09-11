# Session 2 · Naming — where 80% of readability is decided

**Duration:** 45 minutes · **Pre-work:** each person brings one name in the repo they are not proud of
(anonymous is fine — it is about the name, not the person). **Output:** a domain glossary in
`docs/domain-glossary.md` and the naming rules switched on in config.

## 1. Team standard (🔧 decide once, commit it, never re-litigate)

| Decision | Playbook default |
|---|---|
| casing per language | TS/Java/Go exported: PascalCase · locals and functions: camelCase · Python: snake_case · constants: UPPER_SNAKE |
| money and units | unit as a **suffix**, and minor units for money: `amountMinorVnd`, `timeoutMs`, `weightKg` |
| booleans | `is / has / can / should / needs`, affirmative only — `isNot…` is forbidden |
| files | kebab-case (TS), snake_case (Python/Go), PascalCase (Java/Kotlin) |
| tests | `subject_condition_expectedBehaviour`, e.g. `placeOrder_stockEmpty_throwsInsufficientStock` |
| plurals | collections plural, single values not: `orders`, `order` — never `orderList` |
| abbreviations | only ones the language owns (`id`, `url`, `http`, `vnd`); everything else in full words |

Write the table into `CONTRIBUTING.md` verbatim. The value is not in the choices (they are arbitrary)
but in there being **one** answer.

## 2. The five questions for every name (use them in review)

1. Does it state **intent** or only mechanism? (`daysSinceLastLogin` vs `d`)
2. Read aloud — does it mean something? (`usrPrflNm` does not)
3. Is `rg <name>` a **readable** result? (`d` returns the whole repo)
4. Is the unit or type present where it matters? (`timeout` → `timeoutMs`)
5. Does it repeat context the receiver already gives? (`Order.orderTotal` → `Order.total`)

## 3. Wrong → right, worked on the spot (10 minutes)

```ts
// ❌                                       // ✅
function calc(d, t, f) { … }               function invoiceTotalWithVat(invoice: Invoice, cfg: TaxConfig): Money
const arr = [];                            const chargeableLines: CartLine[] = [];
let n = 0;                                 let unpaidInvoiceCount = 0;
const flag = x.a > 18 && !x.b;             const canReceiveBallot = age > MIN_VOTING_AGE && !hasVoted;
if (!order.isNotPaid) ship(order);         if (order.isPaid) ship(order);
class OrderManager { … }                   class OrderPricingPolicy { … }   // + OrderLifecycle { … }
// 500000                                  const FREE_SHIPPING_THRESHOLD_MINOR_VND = 50_000_000;
```

Number rule: **every literal inside logic must have a name**; a literal on a `const UPPER = …`
declaration line is not a violation — that line *is* the fix. `cc-scan`'s `MAGIC_NUMBER` therefore
skips constant-declaration lines (`is_constant_line` in `tools/cc-scan.py`), `case`/`default` labels
and dict values such as `{"maxLineLength": 120}`. One caveat to state when you enable it on a Go repo:
the exemption looks for `UPPER_SNAKE`, so a Go `const vipRate = 0.9` in camelCase still gets reported
— documented with its workaround in `configs/go/README.md`.

## 4. The blocked-suffix drill (10 minutes, whole room)

```bash
rg -n -i "\b(\w+)(Manager|Handler|Util|Utils|Helper|Common|Base|Data|Info|Object|Obj|Processor|Service)\b" src \
  -g '!*.test.*' | awk -F: '{print $1}' | sort | uniq -c | sort -rn | head -20
```

For each hit, one question, out loud: **"who would ask for this file to change?"** Two different
owners → two modules. Do not rename during the session; write the proposed name into the backlog line.
Typical outcome in a mid-size repo: 15–25 hits, a handful genuinely mis-shaped, and one or two
`*Manager` classes that are really two services wearing one name.

Exemptions go in the config, not into an argument: the framework's own names (`ApplicationContext`,
`HandlerInterceptor`, a React `Context`), and a `Service` that genuinely orchestrates one use case.

## 5. Glossary ritual (the part that outlives the session)

1. Write a 20–40 line `docs/domain-glossary.md`: `Đơn hàng = Order` (not `Sale`),
   `Hoá đơn = Invoice`, `Bên vận chuyển = Carrier` (not `Shipper`).
2. Two words for one concept → exactly one survives. Decide with the domain expert, not by vote.
3. The glossary is **code-reviewed**: a PR introducing a domain term with no glossary line is
   incomplete. That single rule is what keeps the document true instead of archaeological.
4. Re-read it during incident reviews: a surprising share of "the code is wrong" is really "two teams
   used one word for two things".

## 6. Safe rename when the name is a public API

```text
1) add the new name   2) old name -> delegates + @deprecated   3) migrate callers in small PRs
4) delete the old name in the next release                 # expand-contract; never a big-bang flip
```

And never mix a rename with a behaviour change in one commit:
`refactor: rename usrPrflNm -> userProfileName (no behaviour change)` is something a reviewer can skim
in ten seconds, which is the entire point.

## 7. What a machine can carry for you

```bash
python3 ../tools/cc-scan.py . --json | jq '[.findings[] | select(.rule|test("MAGIC_NUMBER|NEGATIVE_CONDITIONAL"))] | length'
npx eslint . --rule '{"no-restricted-syntax":"error","@typescript-eslint/naming-convention":"warn"}'
ruff check --select N,PLR2004,ERA .
rg -n "var-naming" ../configs/go/.golangci.yml        # revive:var-naming covers Go
```

The ESLint config in this pack already blocks the suffix list with an English message, so the tool does
the arguing for you. Measured on `configs/js/samples/*.ts`: **10 problems (4 errors, 6 warnings)**, and
the error text is exactly what you can paste into a PR —
`No Data/Info/Manager/Util/Object names - they carry no meaning.`

## 8. Closing check

1. Why is `isNotActive` worse than `isActive`, beyond "two negatives"? (the reader has to solve an
   equation when the condition inverts, and the state logic fragments: some places name it, some don't)
2. Which standard does `Order.orderCustomerName` break? (context repetition)
3. When is a "too long" name correct? (when it replaces a comment or an entire function: 27 characters
   is cheaper than ten minutes of guessing)

**Policy line for `CONTRIBUTING.md`:** *"Names follow §1; a new domain term needs a glossary line in the
same PR; `Manager/Util/Data/Helper/Common` are blocked by lint; an exception must name the rule and the
reason in one comment line."*

**If you only have 15 minutes:** run §4 on one folder, write a ten-term glossary stub, and enable
`no-restricted-syntax`. Everything else is in `02-naming` in the skill references.

Materials: `../skills/clean-code/references/02-naming.md` · skill `clean-code-naming`
