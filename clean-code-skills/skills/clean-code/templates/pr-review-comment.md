# Review comment templates (copy, paste, adjust the names)

> Purpose: say what needs saying **without creating an adversarial mood**. The shared frame is
> `Observation → Consequence → Proposal (or question)` plus a severity label.

## Severity labels (agree them with the team, use them consistently)

| Label | Meaning | Must the author fix it? |
|---|---|---|
| `blocker:` | wrong, unsafe, lossy, secret leaked, or a violation of a standard CI already commits to | yes |
| `should:` | worth fixing for a stated reason; if you skip it, say so in one line | preferably |
| `nit:` | small preference, take it or leave it | no, and no answer owed |
| `question:` | you do not understand; the author explains | answer required |
| `praise:` | good work worth copying elsewhere in the repo | — |
| `FYI:` | context, no action | no |

Two promises that make the labels worth having: a `nit` never blocks a merge, and a `blocker` always
names the damage. If you cannot name the damage, relabel it. Review turnaround you can rely on beats
review you can fear: a common team norm is "first response within one working day, `blocker` resolved
before merge, everything else is negotiable in the thread".

## 1. Inline comments

```md
**blocker:** the `catch` on line 42 swallows `TimeoutError`. Consequence: when the tax gateway is
slow, the order is still created with `tax = 0` and there is no log — we find out from a complaint.
Proposal: `throw new TaxProviderTimeout(provider, { cause: err })` so the caller retries, plus one
test `fails fast when the provider times out`.
Ref: `skills/clean-code/references/07-error-handling.md` §3 (anti-patterns)
```

```md
**should:** `calculateFee(order, type, amount, currency, isVip, gift)` — 6 parameters, and the four
call sites pass them in different orders (`rg calculateFee` shows four different shapes).
Consequence: a swapped pair is a silent bug. Proposal: a `FeeRequest` parameter object, and turn
`isVip` into `discount: DiscountPolicy`.
Ref: `references/03-functions.md` (section 2.5)
```

```md
**blocker (structure):** `src/domain/pricing/taxPolicy.ts` now imports `db/postgres.ts`, so
`arch-scan` reports `UPWARD_DEPENDENCY` on the new edge. Consequence: pricing cannot be tested
without a database, and it will keep growing I/O. Proposal: declare `TaxProvider` as a port in the
domain and move the client into `infrastructure/`.
Ref: `references/12-clean-architecture.md` · `tools/arch-scan.py src --fail-on error`
```

```md
**should (tests):** the new `refund()` branch has no test for the failure path, so a swallowed
provider error would go unnoticed. Proposal: one test with a fake gateway that times out, asserting
`repo.saved` stays empty. Ref: `references/11-testing-for-clean-code.md` §4
```

```md
**nit:** `res` → `response`: easier to grep, and `res` already means something else on line 88 in the
same file. Ignore if it reads clearly to you.
```

```md
**question:** line 15 uses `<=` with `FREE_THRESHOLD`, but `invoice.ts:60` uses `<`. Which convention
are we following — is the threshold value on the free side or the paid side? If it is settled, a link
to the ADR or ticket would save the next person asking 🙂
```

```md
**praise:** separating `orderPricingPolicy` from I/O means the tests need no DB mock and run in 8 ms.
That is exactly the direction I want for the other modules. Copy this shape into billing.
```

```md
**FYI:** `Promise.all` here has no concurrency cap; with 200 lines it opens 200 sockets. Not for this
PR — I opened `PERF-88` with the number so we decide it once, with data.
```

## 2. The PR summary (last, always)

```md
## Overall review

**Verdict:** 💬 Comment (not blocking) — except the `blocker` at #42, which needs fixing first.

**What is good**
- extracting `PricingPolicy` removes 3 copies of the tax formula (single source of truth, done right)
- the boundary tests at 499_999 / 500_000 assert behaviour, not implementation
- the refactor is its own `refactor:` commit, which made this fast to review

**Fix before merge**
1. `blocker` #42 — swallowed timeout (see the inline comment)
2. `should` #15 — make the `<=` threshold convention consistent, or note the ADR link

**Not blocking, filed as issues**
- `invoice.ts` is 480 lines; the renderer should split from the calculator → `AC-1240`, not this PR

**Numbers**
- `cc-scan`: 88/100 (base 74), no new error-level findings
- `arch-scan`: 100/100, no new edge
- billing coverage 91% → 88% (the new renderer is untested) → `AC-1241`

*Reviewed against the `clean-code` skill checklist. Format and lint are green, so nothing here is
about style.*
```

Three properties of a summary people actually act on: at most **five** blocking items ordered by
damage, the **good** things named specifically, and a **next step** ("fix 1 and 2; I will approve
without re-reading the rest"). Silence about what is good is what makes review feel like taxation.

## 3. When you are the author

```md
#42: agreed, fixed in `8f21c1` — wrapped as `TaxProviderTimeout` with two tests (timeout, 5xx).
Thanks for catching it; staging never reproduces it because that provider is fast there.

#15: intentional. The threshold is *inclusive* by definition (an order of exactly 500k ships free);
`invoice.ts` is the one that is wrong. I opened `AC-1242` to fix that side rather than mixing it in
here. Spec: docs/adr/0007-shipping-threshold.md

nit `res`: renamed.
```

Answer rules: no emotional self-defence, only data (spec, test, line count, link). If you were wrong,
say "right, fixing it" in one line — a five-line explanation reads as arguing and costs the reviewer
more time than the bug did. Answer every `question` in the thread, not in Slack: an answer that lives
outside the diff will be lost to the next reader.

## 4. Declining a suggestion politely (when you decide not to change it)

```md
Keeping it as is, for two reasons: (1) this block is a state-machine loop — splitting it into eight
one-line functions means eight jumps while debugging; (2) `cc-scan` flags `LONG_FUNCTION`, but
`COMPLEXITY` is 4, so the difficulty is not the line count. I marked it deliberately:
`// cc-scan:allow LONG_FUNCTION — state machine loop, see docs/adr/0012`.
If you still see a split worth doing, tell me where you would cut and I'll try it in the next sprint.
```

The structure is: reasons, the **narrow** exception marker, an invitation with a limit. What makes
this acceptable rather than stubborn is that the exception is recorded where the next person will find
it (in the file, in the ADR, in the PR thread) instead of living in your head.

## 5. Escalating a disagreement (the third option)

```md
We have gone two rounds on this and we are not converging, which usually means the trade-off is not
written down anywhere. Proposal: ADR-00xx with three lines each — what we each expect to cost, and
what would flip the decision. I'll draft it; ask [lead] to break the tie. Meanwhile this PR ships
without either change, since neither is a blocker.
```

Escalation is not defeat; the failure is relitigating the same point in four PRs. Three lines each,
one third reader, one ADR, one decision — that is the cheapest version of this argument available.

## 6. What does not belong in a review comment

- personal taste in naming, when the tool accepts it and the meaning is clear — stay silent
- anything a formatter or linter decides (Prettier / Black / gofmt made that call, not you)
- "you wrote it differently somewhere else" — a comparison of people; if consistency matters, propose
  **a rule in the config**, not a 40-file manual edit
- speculative performance ("this will be slow") without a number: measure, or open an issue with the
  measurement plan
- a typo in a comment, unless it changes meaning: `nit:` at most, author decides
- comments addressed to *who* wrote the code — including "the AI got this wrong". Review the code,
  not the authorship; the person who merges owns it either way
- a fifth `nit` after fifteen comments. Cap your output, keep the three that matter, and put the rest
  in a single collapsed "minor notes" block at the bottom

## 7. A closing line worth typing

After the verdict, one sentence that is not about the code: "this one was genuinely hard to reason
about and you made it readable — thanks". Teams do not keep good review cultures because the checklist
is thorough; they keep them because being reviewed feels like being helped.
