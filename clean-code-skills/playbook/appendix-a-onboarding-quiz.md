# Appendix A · Onboarding quiz (34 questions, with answers)

> Use: a new joiner works through it before taking their first task; target **≥ 30/34**. Every answer
> has an explanation, and the explanation matters more than the score — this is a conversation
> starter, not an exam you can cram for.

## Scoring

| Block | Points | How it is graded |
|---|---|---|
| 1–20 | 1 each | self-mark against the answers, then a 10-minute walk-through with a senior |
| 21–27 | 2 each | short essay; the mentor reads and replies in writing (this is the part that predicts how they will review) |
| 28–30 | 1 each | practical, on the real repo — a commit link is the answer |
| 31–34 | 2 each | architecture; answered by pointing at a file or an ADR, not by definition |

Interpreting the result: weak in **A/B** → re-run sessions 1–2 with them; weak in **C/D** → session 3–5;
weak in **E/F** → sessions 6–7, and pair them on the next error-handling PR; weak in **G/H/I** → they
should not be reviewing structure yet, and someone should sit with them through session 8 and 10.

## A. Meaning and mindset (1–4)

1. Why is "testable" the **cause** of clean code rather than its result?
2. The clean-code score rose, but the number of files you must read to understand one flow did not
   fall. What is your conclusion?
3. "Write it fast, refactor later" fails by what *mechanism* (not morality)?
4. In a **three-day prototype**, which of the four properties may you partially sacrifice, and where
   must that be written down?

<details><summary>Answers</summary>

1. Being testable ⇒ you dare to refactor ⇒ you can keep it clean. Without tests only stacking is
   allowed, so the module grows monotonically.
2. You relocated lines instead of removing knowledge. The reader's cost did not drop.
3. Dirty code makes the *next* person patch from the outside rather than fix the right place; each
   patch adds a layer, so the slowdown is **cumulative**, not one-off.
4. Readability can be partly traded (do not build a one-letter-name shrine to it); mark it at the top
   of the file: `// SPIKE - not for production, delete after AC-1234`, and the ticket is the promise.
</details>

## B. Naming (5–8)

5. Rename, in a sales domain: `data`, `result`, `flag`, `n`, `usrPrflNm`.
6. Why is `isNotActive` worse than `isActive`?
7. What is wrong with `Order.orderCustomerName`? Rewrite it.
8. Units: `timeout=1500`, `size=2`, `rate=0.1` — rename them in JS, and say which of the three should
   become a **type** rather than a better name.

<details><summary>Answers</summary>

5. `createOrderRequest`, `pricedInvoice`, `hasDiscountApplied`, `unpaidInvoiceCount`, `userProfileName`.
6. Double negation whenever the condition inverts (`!isNotActive`), and state named by exclusion means
   the on/off logic lives in several places at once.
7. It repeats context the receiver already gives → `Order.customerName`.
8. `timeoutMs = 1500`, `pageSize = 2`, `VAT_RATE = 0.1`; the rate should be a `TaxRate` type or a
   config value, and an amount must be `Money` (a value object) — a name cannot stop a unit mix-up, a
   type can.
</details>

## C. Functions (9–13)

9. List four signs a function has outlived its size limit — numeric and semantic.
10. Which rule does `if (cache.getOrLoad(k))` break? Give two fixes.
11. Write only the **signature** of the place-order function, meeting ≤ 3 parameters and no flags.
12. When does extracting a function make code **worse**? Give an example.
13. Add guard clauses: `if (o) { if (o.items) { if (o.items.length) {…} } }`.

<details><summary>Answers</summary>

9. Over 40 lines; over 3 parameters; nesting of 3+ levels; a one-sentence description that needs the
   word "and"; a function name containing "and".
10. CQS — a query that changes state. (a) split into `load(k)` then `cache.put(k)`; (b) or a name that
    admits both: `loadIntoCacheReturningHit(k)`.
11. `placeOrder(cmd: PlaceOrderCommand): Promise<PlaceOrderResult>` — the command is a
    `record`/`@dataclass(frozen=True)`, computation stays pure and side effects sit in the service.
12. When the parts cannot be understood independently (a single continuous algorithm) or the new names
    state no rule (`step1`, `step2`): you added hops and removed nothing.
13. `if (!o?.items?.length) throw new EmptyCartError(orderId);` — one line, and the happy path is
    unindented.
</details>

## D. Comments and format (14–16)

14. Classify these four comments — keep / fix / delete, and say why:
    `// iterate the items` · `// threshold is INCLUSIVE of 500k, ADR-0007` · `// total = total*1.1` ·
    `// TODO: fix later`
15. Why must the format commit be separate, and which command keeps `git blame` alive?
16. Is `prettier-ignore` allowed? When?

<details><summary>Answers</summary>

14. delete (narration — rename the code) · keep (constraint + source) · delete (it restates the line;
    extract `withVat(total)` instead) · fix (a TODO needs a ticket id and an owner, else it is an
    issue).
15. A mixed commit kills blame and hides the real diff under 900 indent changes; follow it with
    `git rev-parse HEAD >> .git-blame-ignore-revs` and each person runs
    `git config blame.ignoreRevsFile .git-blame-ignore-revs`.
16. Yes, narrow and reasoned: aligned numeric tables and coordinate arrays where the whitespace is the
    meaning — with the reason on the line above. Ten of them means the rule is wrong, not the code.
</details>

## E. Objects and data (17–19)

17. `user.addresses.find(a => a.kind === "BILLING").city` — name **two** problems and rewrite it.
18. "A POJO with 20 getters while every rule lives in `OrderService`" — name the syndrome and give two
    consequences.
19. What does a `Money` value object give you that `double + String currency` cannot? Three things.

<details><summary>Answers</summary>

17. A Law of Demeter violation, and business meaning ("what is a billing address") living in the
    caller. → `user.billingCity()`.
18. An **Anemic Domain Model**. (a) invariants are scattered, so two callers implement two versions of
    the rule; (b) testing one small rule requires building the whole service.
19. No unit mix-ups (the type carries the currency); rounding and validation in one place instead of
    four; and an invalid pair (`amount` with the wrong `currency`) becomes unconstructible. Bonus:
    equality and comparison are meaningful.
</details>

## F. Exceptions (20–22)

20. `catch (e) {}` · `except Exception: pass` · `res, _ := call()` — what does each one specifically
    cost you?
21. When must you **not** retry, and when is retry mandatory?
22. Why is "log and rethrow" a smell?

<details><summary>Answers</summary>

20. Total loss of trace (the incident never happened, as far as the data goes) / business failures and
    real programming bugs are hidden together / in Go the error disappears so the caller believes it
    succeeded and continues with a zero value.
21. Never retry: 4xx, business rejections (out of stock, card declined), and non-idempotent writes.
    Retry: timeouts, connection resets, and 5xx whose operation is idempotent — with a cap, backoff and
    jitter.
22. The same incident prints N times, and by the time it reaches the top layer the original
    classification is gone, so nobody can route it.
</details>

## G. Design (23–27 · 2 points each, written answers)

23. "An interface with exactly one implementation and no test fake." Keep or delete? Name three facts
    you need before answering.
24. Two blocks of code are identical for eight lines. List the questions that decide whether it is a
    DRY violation.
25. Adding a fourth fee kind means touching five files. Is the root cause S, O, D or DRY? Justify.
26. Why does "one service per method" break KISS even though it looks like SRP?
27. When should refactoring at a **public API boundary** stop and accept duplication instead?

<details><summary>What a good answer contains</summary>

23. Does anything outside this module implement or fake it? Is there a scheduled replacement or a
    second adapter? Does deleting it force a test to reach into I/O? Delete when all three are no.
24. Same reason to change? Same owner? Would one change without the other? Are they the same business
    rule or the same *text*? Only the first two being yes makes it a real DRY violation.
25. Mostly **OCP** (adding a variant requires editing existing code) with an SRP tail (the switch lives
    in the wrong class); DRY is a symptom, DIP is not involved.
26. SRP counts reasons for change, not files; a split without a reason adds a hop, a name, an import
    and a review burden — a reading tax with no benefit.
27. When the boundary is a published contract (or a schema) whose change is externally costly: keep
    the local copy, add a test that pins both to the same fixture, and record the choice in an ADR with
    a revisit trigger.
</details>

## H. On the real repo (28–30 · 1 point, submit a commit link)

28. Run `python3 tools/cc-scan.py . --json`, pick a rule with ≥ 5 violations, fix **three** sites, and
    commit them as a separate `refactor:`.
29. Find one swallowing `catch`/`except`, fix it and add one test proving the new behaviour. Submit a
    diff of ≤ 40 lines.
30. Propose one rule to add to `tools/clean-code.config.json`, with today's counts and a noise estimate,
    as a comment on the `CLEAN-CODE-ONBOARD` issue.

<details><summary>What the mentor is looking for</summary>

28. A `refactor:` commit with no behaviour change and a before/after score in the message.
29. The test asserts the *action* taken (retry count, saved state unchanged, metric moved), not that a
    log line appeared.
30. An explicit "what this will cost us" line — a proposal without a noise estimate is how a rule gets
    switched off in week two, and the team learns nothing from that.
</details>
## I. Structure and architecture (31–34 · 2 points each)

31. Where does a port's interface live, and why is that the whole of DIP?
32. Which command tells you a `domain → infrastructure` edge exists, and what does it print?
33. Two services each read and write the same table. Name one risk and the cheapest structure that
    removes it.
34. Give one case where a modular monolith is the *right* answer over microservices, stated as a
    constraint, not a preference.

<details><summary>Answers</summary>

31. In the layer that **owns the concept** (domain/application), with the adapter implementing it in
    infrastructure. If infrastructure declares it, the arrow still points outward and the dependency
    rule is decorative.
32. `python3 tools/arch-scan.py src --fail-on error` — it prints a `LAYER  FILE:LINE  MESSAGE` row
    with the edge, and a hint; on failure it appends the CI block to use as a fix TODO.
33. Two schemas drifting and a lost update (no single owner). Cheapest fix: one module owns the table;
    the other calls its port (or an event), i.e. a boundary and a vertical slice, not a new service.
34. e.g. "one team of six deploys weekly, transactional consistency across order and inventory
    matters, and the scaling need is inside one component" → modular monolith with enforced
    boundaries; the split is deferred and the seams are named now.
</details>

