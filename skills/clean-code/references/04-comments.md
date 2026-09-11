# 04 · Comments — write few, write them where they pay

> A comment does not make code cleaner; it is only **cheaper** than making the code self-explanatory.
> Every comment you write is either evidence that the code failed to explain itself, or information
> that *cannot* live in code: the why, the constraint, the history.

## 1. Triage: keep / repair / delete

| Kind | Example | Verdict |
|---|---|---|
| **The "why"** | `// <= rather than < because the boundary is already exclusive on the partner API (AC-402)` | ✅ **Keep** — knowledge that is not in the code |
| **Consequence warning** | `// ORDER MATTERS: clear the cache before the commit; the reverse is a race` | ✅ Keep |
| **Library workaround** | `// axios 1.6 adds a header that breaks the S3 signature - drop when we move to 1.7 (AC-511)` | ✅ Keep, with the condition for removal |
| **Public API contract** (docstring / JSDoc / Javadoc) | `/** @throws UserNotFound when the id does not exist */` | ✅ Keep — a **contract**, not an explanation |
| **TODO** | `// TODO(AC-512, minh): switch to batch once the partner raises the rate limit` | ✅ Keep if it has a ticket **and** an owner; otherwise open the issue and delete the line |
| Explaining the code | `// loop over items and add to total` | 🔧 **Fix the code**: name it `sumItemTotals()` |
| Restating the signature | `/** @param id the id of the user */` | ❌ Delete |
| Dead code | `// const oldCalc = ...` | ❌ Delete — Git has the history |
| Banner separators | `//========= FEES =========//` | 🔧 Replace with a real boundary, or better: split the file |
| Work status | `// add next sprint`, `// temporary for now` | 🔧 Move to an issue with a date |
| Apology | `// I know this is bad` | 🔧 Fix it, ticket it, or delete the comment — an apology is not a plan |

## 2. Three situations where you *should* comment (and generously)

1. **Boundaries and arithmetic**: inclusive vs exclusive indexes, rounding rules, evaluation
   order, an invariant that spans two fields (`end >= start`), a unit conversion at an edge.
2. **Architecture decisions**: why the boring option won, what was rejected and why. Put the text
   in an ADR and leave one pointer in the code: `// see docs/adr/0012`.
3. **Behaviour a reader cannot see**: "this handler is idempotent, retrying is safe", "runs on a
   2-thread pool - do not block here", "this order is load-bearing for the CSV export format".

Also legitimate, and often skipped: **why a limitation exists** (`// single-process only: the lock
is in-memory; needs Redis before scaling`), which is the same sentence a future on-call engineer
needs at 2 a.m.

## 3. Turn comments into code

```ts
// ❌ the comments are carrying what the code refuses to say
if (u.a > 18 && !u.b) {          // old enough and has not voted
  send(u);                       // dispatch the ballot
}

// ✅ the code says it; the comments are gone
if (voter.canReceiveBallot()) {
  dispatchBallot(voter);
}
```

```py
# ❌ a comment narrating an algorithm
# if the balance is below the fee, skip - unless the account is VIP, then charge anyway
def charge_fee(account):
    if account.balance < FEE or (account.tier != Tier.VIP):
        return
    ...

# ✅ name the condition; the comment now holds only the "why"
def fee_applies_to(account: Account) -> bool:
    """VIPs are always charged, to keep the price contract with the partner (AC-317)."""
    return account.balance >= FEE or account.tier is Tier.VIP
```

```java
// ❌ the comment is an apology for a bad name
// checks if the user can do the thing
if (userService.checkAccess(user, action)) { ... }

// ✅ the name is the comment
if (user.isAllowedTo(action)) { ... }
```

The general move: a comment that explains **what** is a specification for a better name or a
extracted function. A comment that explains **why** is content no naming can carry.

## 4. Rules for the comments you keep

- **Prefer a line above the code.** Trailing comments break as soon as the formatter wraps the
  line, and they are the ones that rot silently.
- **Talk about the decision, never about syntax.** The reader knows what `for` means.
- **Update it in the same commit as the code.** A wrong comment is worse than none: it lies with
  authority, and the reader believes it until the behaviour contradicts it — usually at the worst
  moment of the debugging session.
- **One language per repo** (this pack: English). Mixed-language comments in one module hurt
  search, hurt onboarding, and hurt the person who joins in two years. Record it in `CONTRIBUTING`.
- **No narration of your process** ("changed this to fix the bug", "as discussed with Tuan").
  The first belongs in the commit message, the second in the ticket.
- **Never put commented-out code in a commit.** Deleting it is the fix; Git is the archive.
- Exempt, and not to be "cleaned": license headers, generated-code banners, and marker comments a
  tool needs (`// eslint-disable-line` and friends — these must name the rule and the reason).

## 5. "If you are about to write this, write that instead"

| You are about to write | Do instead |
|---|---|
| `// handles the edge case where cart is empty` | `if (cart.isEmpty()) return emptyReceipt();` — no comment |
| `// step 1 … step 2 … step 3` | three extracted functions named after the steps |
| `// returns -1 if not found` | return a `Result`/`Optional`; delete the comment |
| `// don't delete, needed by X` | a test that proves X needs it, or a comment naming X **and** the ticket |
| `// FIXME this is slow` | an issue with the measurement attached, and `// see PERF-118` here |
| `/* big commented-out block */` | delete it. Yes, all of it. |
| a 12-line comment explaining a formula | a named function + a reference (`// VAT law 2024 §10, rounding: half-up`); the explanation belongs in docs, not in the file |

## 6. Documentation on a public API: what belongs there

```ts
/**
 * Converts an amount to the currency's minor unit (cent/sat) to avoid float error.
 *
 * @throws InvalidAmountError when `amount` is negative, NaN, or exceeds `MAX_PRECISION_DIGITS`.
 * @see docs/adr/0007 - why Decimal is not used in the domain layer
 *
 * @example
 * toMinorUnits("12.345", { currency: "VND", maxDigits: 0 }) // -> InvalidAmountError
 */
export function toMinorUnits(amount: string, opts: CurrencyOptions): number { ... }
```

Enough is: **one sentence of purpose** + **failure modes** + **constraints/units** + an example for
the surprising case. Do not restate parameter names; do not describe private internals (they are
readable); do not write a docstring you would be embarrassed to be held to — in this pack docstrings
are contracts, and `11-testing-for-clean-code.md` shows the test that pins each documented claim.

Per-language conventions to follow so tooling can read them: TSDoc/JSDoc (TS), Javadoc `@param`
only when non-obvious (Java), Google- or NumPy-style docstrings with `ruff`'s `D` rules (Python),
and Go's rule that a doc comment **starts with the identifier** and ends with a period
(`// SumPaidAmount totals the orders that have been paid.`).

## 7. Machine help (what can actually be gated)

```bash
python3 tools/cc-scan.py . --json \
  | jq '[.findings[] | select(.rule=="COMMENTED_CODE" or .rule=="TODO_MARK")]
        | group_by(.rule) | map({rule: .[0].rule, n: length})'

npx eslint . --rule '{"no-warning-comments":"warn","spaced-comment":"warn"}'
ruff check --select D,ERA001,T20,EM .
checkstyle -c configs/java/checkstyle.xml src/main/java     # TodoComment + SuppressionCommentFilter
```

| Signal | Tool | Level | Meaning |
|---|---|---|---|
| `COMMENTED_CODE` | `cc-scan` | warn | dead code parked in comments |
| `TODO_MARK` | `cc-scan` | info | a TODO without a ticket id in the text |
| `BLOCK_COMMENT` | `cc-scan` | info | a long comment block that belongs in docs |
| `ERA001` | ruff | error | commented-out code |
| `D` | ruff | — | missing/short docstrings on public API |
| `TodoComment` | Checkstyle | info | the JVM equivalent; fires on `TODO/FIXME/XXX/HACK` |

That combination is deliberate: **you cannot leave debt in a comment without CI noticing.** Where a
long block is genuinely warranted (a legal formula, a protocol table), keep it and silence the
warning on the range with a reason, rather than deleting the knowledge:
`# cc-scan:allow BLOCK_COMMENT — statutory formula quoted verbatim, see ADR-0021`.

## 8. Sixty-second self-check

1. Delete every comment in the file you just changed. Can you still read it? If yes, do not put them
   back.
2. Of the comments that must stay, which do **not** answer "why this way"? → delete or convert to code.
3. Every TODO: ticket + owner, or open the ticket now and delete the line.
4. Public API: does the doc state the constraints and the failure modes, without restating types?
5. One drill worth 10 minutes with the team: take the file with the most comments and delete them
   one at a time — for each, either prove the code is clearer without it, or name what code change
   would make it unnecessary. Typical result: 60% deletable, 20% become functions, and the 20% left
   become the file's real documentation.
