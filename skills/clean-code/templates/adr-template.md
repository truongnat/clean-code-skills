# ADR-NNNN: <the decision, stated affirmatively>

> An ADR is the place where the comment most worth writing lives. Code says *what* it does; the ADR
> says **why this, and what was rejected**. Link it from the code with one line
> (`// see docs/adr/0007`) instead of pasting ten lines of explanation into a source file.

- **Status:** Proposed / Accepted / Superseded by ADR-XXXX / Deprecated
- **Date:** YYYY-MM-DD
- **Decided by:** … · **Consulted:** … (the people who will maintain it, not only the people who are free)
- **Related:** AC-1234, PR #567, `ARCHITECTURE.md`
- **Scope of application:** which module / service / boundary

## Context

The business or technical problem, and the constraints that actually exist (deadline, team size,
legacy systems, cost, regulation, SLA). **Facts only — no solution language.** 5–10 lines. If a
reader two years from now cannot tell what was true at the time of the decision, the ADR failed.

> Example: "The VAT formula is duplicated in `checkout.ts`, `invoice.ts` and one stored procedure.
> Each time the partner changes the rate we edit three places; twice they drifted (order 03-2025,
> a 1.4% invoice difference)."

## Decision

What we will do, in active voice, short. Bulleted when more than one decision lives here — each
bullet is separately falsifiable.

- All tax rules move into `TaxPolicy` (domain, pure, no I/O).
- The public API returns a `taxPolicyVersion` so partners can tell which rule produced a number.
- The stored procedure **stops** computing tax; it receives an already-priced result.

## Alternatives considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| A. rates in a DB config table | no deploy to change | no types, no tests, no review on the change | a rule that cannot be reviewed will silently be wrong |
| B. `TaxPolicy` in code + tests | type-safe, CI-blockable, reviewable | needs a deploy when the law changes | **chosen** — the rate changes about twice a year |
| C. a separate tax service | isolation, own release train | +1 hop, +1 SLA, no on-call capacity | beyond what this team can operate |
| D. keep the copies, add a checklist | zero work | relies on humans being careful forever | rejections belong on paper too — write D down |

The value of this table is the *rejected easy option*: it is what stops someone from "simplifying"
back to it in six months.

## Consequences

**Positive:** one source of truth; a rate change is one PR with N tests; `rg "0.10" src/domain`
returns nothing.

**Negative / debt accepted knowingly:**
- a rate change needs a deploy (twice a year — acceptable, cost: one release slot);
- four legacy call sites still compute by hand → migration `AC-1240`, two sprints;
- one more abstraction (`Money`) → new joiners read playbook session 06; onboarding +30 minutes.

**New rule switched on alongside:** `cc-scan MAGIC_NUMBER` becomes `error` for `src/domain/**`
starting next sprint, and `0.10` disappears from the baseline.

**Reversal cost:** one-way or two-way door, and what it would take to undo this (for this ADR:
"two-way: the policy is a pure module; undoing is re-inlining it, ~1 day, plus deleting the version
field from the API — which is the one-way part").

## Verification

- [ ] which tests prove the decision? (`taxPolicy.test.ts` — 12 cases, incl. boundary and rounding)
- [ ] which metric proves it worked? (`invoice.mismatch.rate` < 0.2% for 30 days)
- [ ] which command shows the rule being broken? `rg -n "0\.1[05]" src/domain` must return 0 lines,
      and CI gates it: `python3 tools/cc-scan.py src/domain --fail-on error`
- [ ] if structure is involved: `python3 tools/arch-scan.py src --fail-on error` = 0 errors, and the
      new port shows up as `domain` declaring it

## Revisit trigger

Re-open this ADR when: the rate changes more than 4 times a year (→ option A's trade-off flips),
a second team needs the same rule (→ option C becomes real), or the deploy cost exceeds the
drift cost. Not "someday": one of these three, checked at the quarterly retro.

## Links

Code: `src/domain/pricing/tax-policy.ts` · PR: #567 · Issues: AC-1234, AC-1240 ·
Playbook: `playbook/08-design-principles.md` · Skill rule: `references/08-design-principles.md`
(section 6, DRY)

---

## Mini-ADR (for small decisions — 8 lines is enough)

```md
# ADR-0018: the free-shipping threshold is inclusive
Status: Accepted · Date: 2026-09-10
Context: two modules used `<=` and `<`, so invoices differed by one unit exactly at 500k.
Decision: the threshold belongs to the free side (an order of 500,000 ships free).
Consequence: fix `invoice.ts` (1 place); boundary tests in both modules.
Verification: `rg -n "FREE_SHIPPING" src -A1` — every comparison is `>=`.
Revisit: if finance defines the threshold as exclusive, this flips, and only the tests break.
```

## What deserves an ADR, and what does not

Worth one: anything crossing a boundary (API contract, schema, event format), a rejection of the
obvious option, a decision that will look strange to a newcomer, a **deliberate exception to the
standard** (and here the ADR is what makes the exception respectable rather than hidden), and any
choice whose reversal is expensive.

Not worth one: internal naming, a library swap with no interface change, anything reversible in one
commit, or a decision whose context you cannot state in three sentences — that means it is not a
decision yet, it is a preference in search of an argument.

## House rules that keep ADRs alive

1. Number them at creation (`0001`…); never renumber, never edit an accepted ADR — **supersede** it
   with a new one and a two-line link. The value of an ADR is that it is a record, not a document.
2. Store them in `docs/adr/` next to the code, so they move with the repo and appear in the same PR
   diff. A wiki page is a place where decisions go to stop existing.
3. The PR that implements a decision must reference it, and the review checklist has one line for it:
   *does this PR match the ADR it cites?* That single question is where "we decided X" becomes real.
4. Read them at onboarding, in order, for twenty minutes. If the team cannot explain its own oldest
   five decisions, either the ADRs are missing or the decisions are wrong — and both are fixable
   this sprint.
