# Session 12 · Design patterns — a vocabulary, not a checklist

**Duration:** 45 min, code-along format · **Output:** each person converts one real `switch`/flag into
a policy, and adds one review line to the team checklist. Catalogue:
`../skills/clean-code/references/14-design-patterns.md`.

## 1. Framing for the team

> A pattern is a **named solution to a recurring problem**. If the problem is not present, the
> solution is not a virtue — it is indirection with a resume benefit.

Two failure directions, both worth naming in review:

- **Pattern-missing**: the fifth `if (kind == …)` this quarter, a `Manager` class at 900 lines, a
  subscriber list built out of 11 direct calls. The scanner sees most of these
  (`DUPLICATE_BLOCK`, `LONG_FUNCTION`, `BOOLEAN_PARAM`, `DEEP_NESTING`).
- **Pattern-forced**: an abstract factory producing one object; an interface with one
  implementation and no second user; a builder for a 3-field record. Review line: *name the cost you
  paid and what it buys, or delete it*.

## 2. The five that carry their weight here

| Pattern | Problem it kills | This pack's link |
|---|---|---|
| Strategy (or enum + switch) | `BOOLEAN_PARAM`, `if (type == …)` growing forever | `snippets/bad-vs-good.md`, rule `BOOLEAN_PARAM` |
| Factory function | half-built objects, invariants enforced "somewhere" | `references/02-naming.md` (parse, don't validate) |
| Adapter | foreign shapes bleeding into the domain | `references/12-clean-architecture.md` §4, `DOMAIN_FRAMEWORK_IMPORT` |
| Decorator | retry/logging/timing/metrics copy-pasted at 8 call sites | `references/07-error-handling.md` |
| Command object | 6-parameter functions, no way to log/queue/validate intent | rules `HARD_PARAMS`, `TOO_MANY_PARAMS` |

## 3. Code-along (20 minutes, one repo, everyone types)

Start from the pack's own demo file, `tools/demo/src/legacy-order-service.ts`:
`placeOrder` has 6 parameters, two booleans, a nested `switch`, and a duplicated 8-line block.

Step 1 — **Command**: `placeOrder(cmd: PlaceOrderCommand)` (see `tools/demo/src/order-service.ts` for
the finished shape). Parameters 6 → 1; `HARD_PARAMS` clears.
Step 2 — **Flag → policy**: replace `skipStockCheck: boolean` with
`stockPolicy: "enforce" | "skip"`. `BOOLEAN_PARAM` clears and the call site reads as intent.
Step 3 — **Extract the rule**: pricing becomes a pure `priceCart(items, policies): Money` in the
domain; the service only orchestrates. `HUGE_FUNCTION` clears.
Step 4 — **Strategy**: `policies: readonly DiscountPolicy[]` instead of `if isVip / if isHoliday`.
Adding `BUNDLE10` is now a new file and one test, no edit in a shared function.
Step 5 — **Decorator**: timeouts/retries on the payment gateway call, outside the use case, so the
use-case test does not know about HTTP.

After each step: `python3 tools/cc-scan.py src/order-service.ts src/order-service.test.ts` and the
tests. Score should move 72.0 → 100.0 with the test suite green the whole way — that is the point of
the demo: **no behaviour change in the refactoring steps**.

## 4. Which abstraction at which count (the rule of three, made explicit)

| Occurrences | Do |
|---|---|
| 1 | write it inline, in the boring way |
| 2 | tolerate the duplication; note it in the PR description |
| 3 | extract — now you know what is common and what only looked common |
| 3, but they change for different reasons | keep them separate and say why in a comment (DRY is about **knowledge**, not text) |

This is the session's answer to "DRY vs YAGNI", and it is the line reviewers quote most.

## 5. Exercises

1. Convert one `switch` you own into policies, or into an exhaustive enum + `switch` in one place
   (Go/Rust style is fine — say in the PR why that reads better than a class per variant).
2. Find a `*Manager`/`*Util`/`*Helper` in the repo. Name its theme in one sentence. If you cannot,
   split it by caller or inline it into the one place that uses it.
3. Take one external API client. Add a decorator for timeout + retry with backoff+jitter, and a
   test with a fake that fails twice then succeeds.
4. Delete a "dead abstraction": an interface with one implementation and no expected second one.
   If someone objects, they must name the second implementation they are waiting for — that is the
   seed of the ADR.
5. Apply the rule of three in reverse: find an abstraction built at occurrence #1 and inline it.

## 6. Quiz

1. When does a `switch` on a type become a pattern problem instead of a style problem?
2. Why is "one implementation behind an interface" sometimes right, and what must be true?
3. A `BaseProcessor` with 9 protected hooks, half overridden in subclasses. Which pattern is
   actually needed?
4. Name the two things a Command object gives you beyond parameter count.
5. Which patterns must be *visible in the folder structure* for boundaries to be enforceable?

**Answers:** (1) when the set of branches is open — each new variant edits and re-tests shared code.
If the set is closed and small (3 transport types), a `switch` is the better engineering. (2) when
the seam is real: a second implementation exists in tests, or it crosses a deployable/team
boundary. (3) composition + Strategy — inheritance is being used to share code, not to express a
type. (4) a serialisable intent (queueable, loggable, replayable) and a validation point that cannot
be bypassed. (5) Adapter (infrastructure), Command/Handler (application), and the port interfaces
themselves — because `arch-scan` classifies by path, an invisible pattern is an unenforceable one.

## 7. DoD

- [ ] One `BOOLEAN_PARAM`/flag argument converted to a policy or enum, with tests green
- [ ] One dead abstraction deleted or justified in writing
- [ ] Team checklist gained: "problem named before pattern chosen"
- [ ] `cc-scan` score for the touched file(s) did not go down

## 8. Links

Catalogue + anti-pattern table: `../skills/clean-code/references/14-design-patterns.md` ·
smells & refactoring list: `../skills/clean-code/references/10-code-smells-refactorings.md` ·
worked demo: `../tools/demo/` · prompt: `../prompts/13-pattern-picker.md` ·
previous: `11-architecture-patterns.md` · appendices: `appendix-a-onboarding-quiz.md`,
`appendix-b-maturity-model.md`
