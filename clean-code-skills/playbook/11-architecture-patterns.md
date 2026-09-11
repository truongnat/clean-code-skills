# Session 11 · Architecture patterns — picking the shape and paying for it on purpose

**Duration:** 45 min workshop · **Output:** one signed ADR choosing (or rejecting) a shape for a real
problem the team has right now. Catalogue: `../skills/clean-code/references/13-architecture-patterns.md`.

## 1. The rule for this session

> Choose the **reversible** shape that meets today's requirement, and keep the seams clean enough
> that the next step is a move, not a rewrite.

Microservices are the only entry in the catalogue you cannot undo inside a quarter. Modular monolith
is the default because it is the only option that buys most of the isolation at ~none of the
operational cost, and it converts into services later **if** the boundary held.

## 2. The cost sheet (fill it in before choosing)

| | Layered | Modular monolith | + Events | CQRS | Microservices | Serverless |
|---|---|---|---|---|---|---|
| Pipelines to own | 1 | 1 | 1 | 1–2 | 1 per service | 1 |
| On-call rotations | 1 | 1 | 1 | 1 | 1 per service | shared |
| Local dev story | trivial | trivial | needs broker/emulator | 2 models to sync | per-service stubs | per-provider emulator |
| Latency added | 0 | 0 | ms–s (async) | ms | 5–50 ms per hop | cold start |
| Idempotency burden | no | no | **yes, every consumer** | yes on writes | yes on every edge | yes (retries) |
| Ordering burden | no | no | **yes** | yes | yes | no |
| Schema contract burden | no | internal only | **yes, versioned** | read model + events | yes, public | no |
| Reversibility | high | **high** | medium | low | **low** | medium |

Write this table into the ADR with your own numbers (how many pipelines exist today, what an
incident costs per hour). An ADR whose "cost" column is empty is a wish.

## 3. Decision drill (the whole session, 25 min)

Take one real requirement from the backlog — e.g. "when an order is placed, notify the warehouse,
bill the customer, and update the loyalty balance". Each team member answers on paper:

1. Which pattern? 2. Which layer does each piece live in? 3. What breaks if the warehouse is down?
4. What does it cost us per month, forever?

Then compare. The interesting part is not the answer, it is disagreement #3: whoever chose
"one transaction, three writes" has assumed the warehouse is always up. Whoever chose "events" must
now say what they do about **duplicate delivery** and **out-of-order** delivery. If nobody can
answer those two, the team is not ready for events — ship the modular monolith with a synchronous
call plus a retry queue, and revisit at the next scale step.

## 4. Non-negotiables once a shape is picked

- **Events**: transactional **outbox** (never "write then publish"); idempotent consumers
  (`dedupe_key` + unique index); `docs/events.md` catalogue (producer, consumers, payload,
  retention); one contract test per event; trace id crosses the queue.
- **Services**: a timeout on every edge (a client with no timeout is a bug); retry only idempotent
  calls; circuit breaker + bulkhead on shared dependencies; consumer-driven contract tests;
  a named owner and an SLO per service, or it does not ship.
- **CQRS**: an answer for "user saves, reloads, sees stale data" (return the write version, or
  refresh that one projection in-request).
- **Serverless**: business rules in a library, handler ≤ ~10 lines (decode → use case → encode).
- **Everything**: `arch-scan`/import-linter/ArchUnit still applies — a distributed shape does not
  excuse a module inside it from the dependency rule.

## 5. Migration mechanics (how to arrive without a freeze)

1. **Strangler fig**: facade routes per operation; move one route; keep the old path warm for a
   stated window; metrics gate before cutover — same response class mix, p95 within budget, equal
   error rate.
2. **Branch by abstraction**: interface in front of the legacy implementation → all callers moved →
   implementation swapped in a separate PR.
3. **Expand → backfill → contract** for every storage change; never drop a column in the release
   that stops writing it.
4. **Parallel run** for anything that touches money: shadow-execute, compare, alert, serve nothing.
5. Before splitting any module, make its imports legal (`arch-scan` green): then the split is a file
   move plus a pipeline.

## 6. Exercises

1. Write the ADR from §3 for your current real decision: options, cost, **revisit trigger**
   ("at 25 engineers", "when a module needs its own DB", "when two teams queue on this deploy").
   Template: `../skills/clean-code/templates/adr-template.md`.
2. Add one reliability shape to a call that has none: timeout + retry with backoff + jitter, and
   prove it in a test with a fake gateway that fails twice.
3. Draw the event flow of one existing synchronous chain on paper, then answer: if the third
   consumer is down for 20 minutes, what does the user see? Write the answer in `ARCHITECTURE.md`.
4. Find a "distributed monolith" in a system you know (deploy-together services, shared DB, sync
   chains). Name the boundary that should have been a module instead.

## 7. Quiz

1. Two services share one database schema. What did you actually build?
2. Why does an outbox beat "publish after commit" in every talk you will ever give?
3. A consumer must not react twice. Two mechanisms, with their trade-off.
4. When is CQRS-lite (same table on both sides) worse than no CQRS?
5. What is the smallest reversible step towards services, and what does it cost?

**Answers:** (1) a distributed monolith with latency: you took the operational cost and none of the
independent deployability. (2) "write then publish" loses the event when the process dies between
the two — same transaction removes that window; at-least-once delivery then only needs idempotency.
(3) `dedupe_key` + unique index (exact-once effect, needs storage) vs a processed-id cache with TTL
(cheap, wrong after TTL or a replays-older-than-TTL incident). (4) when both sides read the same
table: no scaling benefit, no read-model benefit, all of the consistency cost. (5) a module with
enforced boundaries in a monolith — one config file plus a CI job; and it is the same work you need
for a later split anyway.

## 8. Links

Catalogue & matrix: `../skills/clean-code/references/13-architecture-patterns.md` · sub-skill §4:
`../skills/clean-architecture/SKILL.md` · CI templates: `../configs/ci/` · prompt:
`../prompts/13-pattern-picker.md` · previous: `10-clean-architecture.md` · next: `12-design-patterns.md`
