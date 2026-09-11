# Refactoring plan: <module> — use this template when the work is more than a day

> Refactorings die for two reasons: (1) no safety net, (2) no stopping point. This template forces
> you to declare both **before** you start, in writing, where a PM can read it.

## 0. Why now (say it to the PM in numbers)

| Question | Answer |
|---|---|
| What is slow or expensive today? | one new fee kind takes 5 days, 7 files, and caused 2 regressions |
| Evidence? | `cc-scan` 54/100; the repo's #1 hotspot (47 commits in 6 months); incidents INC-118, INC-141 |
| What if we do nothing? | +8–10 days per quarter for the same kind of change; wrong-invoice risk stays |
| Measurable benefit after? | a fee-kind change ≤ 1 day; `cc-scan` ≥ 85; zero billing incidents for two quarters |

**Time commitment:** N days in M steps, with a stop allowed at **any** step (every step is green and
deployable). If you cannot promise that, the plan is not a plan — it is a wish.

## 1. Scope

- **In:** `src/billing/**`, `src/domain/pricing/**`, the 4 call sites in `checkout`
- **Out (deliberately):** `legacy-tax.js` (strangler later), the UI, the monthly report
- **Must not change:** the `/v2/orders/*` contract, the DB schema, anything the customer sees
  except the intended rule change
- **What we will explicitly not fix:** <list the smells you noticed and are leaving alone>

That last line is the one people skip and the one that saves the schedule. Write the temptations
down, with the issue id you are parking them under.

## 2. Safety net (build it BEFORE editing anything)

- [ ] `python3 tools/cc-scan.py . --update-baseline` — freeze the current state so CI cannot block
      you for pre-existing debt
- [ ] characterization tests for the 6 entry points: fixed inputs → **photograph** today's output
      (bugs included; mark them `// KNOWN-BUG(AC-1250)` and do not fix them in this plan)
- [ ] property tests for pricing, where the shape allows it: `total >= 0`,
      `sum(lineTotals) == subtotal`, `fee is independent of line order`
- [ ] feature flag: `pricing.policy.v2` (off in production, on in staging)
- [ ] reconciliation dashboard: `invoice.mismatch.rate`, `vat.amount.delta`, per hour
- [ ] **shadow / dual-run**: both paths execute on staging, diff 1,000 sample orders, expected
      mismatch = 0 except the documented `KNOWN-BUG` cases
- [ ] a written rollback that someone other than you can execute in under 5 minutes

```python
# the shadow diff, as a runnable script rather than a slide
def shadow_diff(legacy, new, orders):
    bad = [(o.id, legacy(o), new(o)) for o in orders if legacy(o) != new(o)]
    known = {KNOWN_BUG_IDS}
    unexpected = [row for row in bad if row[0] not in known]
    print(f"orders={len(orders)} mismatch={len(bad)} unexpected={len(unexpected)}")
    return unexpected            # must be empty before step 4 flips anything
```

## 3. Steps (each step = one PR, green, mergeable)

| # | Step | PR | Risk | Rollback |
|---|---|---|---|---|
| 1 | renames + function extraction, **no** behaviour change | #561 | low | revert |
| 2 | move the invariant into the `Money` value object | #562 | medium (12 sites) | revert |
| 3 | introduce `PricingPolicy` + a port/adapter for `TaxProvider` | #563 | low | flag off |
| 4 | migrate the 4 call sites to the policy (with shadow diff) | #564 | **high** | flag off → old policy |
| 5 | delete dead code: `LegacyTax`, `// old impl`, 3 flags | #565 | low | revert |
| 6 | ratchet: `MAGIC_NUMBER` + `LONG_FUNCTION` = error for `src/billing` | #566 | low | revert the config |

Rules: a refactor step contains **no** behaviour change; behaviour changes only in step 4, behind a
flag, with the reconciliation metric watched. And after step 3, run `arch-scan` — the seam you just
created should be visible as a layer edge (`domain → port ← adapter`), not as a new cycle.

## 4. Definition of "done"

```bash
python3 tools/cc-scan.py src/billing --json | jq '{score, error: .counts.error, warning: .counts.warning}'
python3 tools/arch-scan.py src --fail-on error            # target: 0 errors, no new cycle
# goals: score >= 85, error = 0, warning < 10, and the baseline for this folder is empty
```

- [ ] every function ≤ 40 lines / ≤ 3 params (or `cc-scan:allow` with a reason)
- [ ] zero magic numbers in `src/domain` (rates live in `PricingConfig`)
- [ ] zero swallowing `catch`; every wrapped error keeps its `cause`
- [ ] coverage in `src/billing` ≥ 90%, error branches ≥ 80%
- [ ] `invoice.mismatch.rate` = 0 for 7 consecutive days in production
- [ ] the characterization tests **deleted or converted** into real behaviour tests (they are a
      scaffold; leaving them forever pins the old bugs in place)
- [ ] `ARCHITECTURE.md` + the glossary updated; ADR-0021 records the decision and its trade-off
- [ ] the module's own `Makefile`/lint target enforces the new thresholds, so the shape survives

## 5. Timeline and gates

| Milestone | Content | Date |
|---|---|---|
| M0 | safety net in place, CI green | T+3 days |
| M1 | PR 1–3 merged, flag off, behaviour identical (shadow diff = 0) | T+1 week |
| M2 | shadow diff = 0 over 1,000 staging orders for 24 h | T+2 weeks |
| M3 | flag at 100% in production, metrics watched 3 days | T+3 weeks |
| M4 | old code deleted, rules ratcheted, plan closed | T+4 weeks |

Each milestone has a **gate**, not a date alone: M3 does not start until M2's number is zero.
A plan with dates but no gates slips silently; gates are what make the slip loud.

## 6. Kill criteria (agreed in advance, so "stop" is not a personal failure)

- the module's score is ≥ 85 → stop; the rest becomes issues, not momentum;
- making the refactor "complete" would require a schema or contract change → **stop**, escalate it as
  a separate project with its own scope and PM approval;
- one step costs more than 2 days without reducing the place that changes most → stop, choose a
  smaller target;
- the mismatch metric exceeds its threshold (e.g. `> 0` unexpected, or `> 0.1%` for a data
  migration) → flag off immediately, then investigate as an incident, not as a to-do;
- a team member is pulled into an incident for more than two days → decide: re-baseline the plan or
  shrink its scope. Do not let it drift by default.

Write the kill criteria **with** the PM in section 0. The difference between a controlled stop and a
failed project is usually only whether the exit was pre-agreed.

## 7. Communication while it runs

- a 2-line update per day in the ticket: what changed, current metric, next step — this is what keeps
  a multi-week refactor from being perceived as "nothing is happening";
- every PR names its step number, so anyone can see the plan's progress by filtering the log;
- when a step is cut, say it out loud and record it in the ADR — silent scope loss is how a "3-week
  cleanup" becomes a 3-month rumour.

## 8. Notes when AI participates in the code

- the prompt used to generate code must contain **no** secret or PII; use the prompts in this pack
  (`prompts/`), which are designed around the snippet you paste, not the whole repo;
- model output goes through the same tests and checklist as human code — a diff written by a machine
  does not reduce the responsibility of whoever merges it;
- never "AI, refactor the whole module": one step per PR, ≤ 400 lines, with tests. The specific
  failure mode is a plausible, well-named rewrite whose snapshot of old behaviour nobody pinned —
  then step 4 flips and only the customers know.
- ask for the *characterization test first*, the code second. If a model writes the refactor before
  the net, reject the PR and restart from step 2 of this plan.
