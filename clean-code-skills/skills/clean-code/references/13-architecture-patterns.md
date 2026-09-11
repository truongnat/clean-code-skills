# 13 · Architecture patterns — which shape, at what cost

No rule IDs here are enforced by `cc-scan`; the machine checks of this chapter live in
`arch-scan` (layer/boundary rules), CI job budgets, and the schema/contract tests you write for
whichever shape you pick. Read this together with `12-clean-architecture.md`: layers decide *who
imports whom*; patterns in this file decide *how work travels*.

## 0. The three questions before any pattern

1. **What changes independently?** Those are your candidate seams.
2. **What must stay available when something else is down?** That decides sync vs async.
3. **How big is the team touching the same code?** Below ~25 engineers, most of the cost of
   distributed shapes buys you nothing.

Answer those and 4 of the 9 patterns below are already out.

## 1. The catalogue

### Layered (n-tier)

```
UI → application → domain → persistence          (one direction, top to bottom)
```

- **Use when**: CRUD-ish product, small team, no independent scaling needs.
- **Cost**: everything is one process and one deployment; a slow report blocks a fast checkout.
- **Failure mode**: the "layer" becomes a *pass-through* — every request walks 4 files that only
  forward arguments. If a layer adds no decision, delete it (this is the architecture version of
  the "trivial delegating method" rule in `03-functions.md`).

### Hexagonal / ports & adapters

The shape described in `12-clean-architecture.md` §4: the core owns interfaces (ports), adapters
implement them; nothing points inwards except through a port.

- **Use when**: many entry points (HTTP, queue, CLI, tests) over the same rules; you want to test
  rules without infrastructure.
- **Cost**: one extra file per integration point, and a discipline tax: every shortcut ("just read
  the DB in the use case") re-tightens the knot.
- **Failure mode**: port explosion — an interface per method, 60 interfaces, no two alike.
  Rule of thumb: a port is the *vocabulary of a collaborator* (a repository, a clock, a gateway),
  not a mirror of a class.

### Onion / clean

Same as hexagonal with concentric rings and the dependency rule spelled out. Pick the vocabulary
your team already uses; the enforcement (`arch-scan`, import-linter) is identical.

### Modular monolith ← **the default answer for most teams**

One deployable, hard internal boundaries, machine-enforced:

```
src/checkout/  src/pricing/  src/shipping/     each with domain/application/adapters
        └── only through published APIs or events
```

- **Use when**: 2–50 engineers, several domains, you want service-like isolation without
  distributed-system costs.
- **Cost**: one shared database (usually fine), and boundary enforcement in CI — which is exactly
  what `BOUNDARY_LEAK`/dependency-cruiser/import-linter are for.
- **Failure mode**: boundaries drawn on paper. Without the CI check they dissolve in one quarter.
- **Numbers to quote to management**: you keep 1 pipeline, 1 on-call rotation, ~0 network
  failures; you can split a module out later with the strangler pattern (§3).

### Event-driven / pub-sub

Producers emit facts (`OrderPlaced`), consumers react. Consumers are unknown to producers.

- **Use when**: >1 team must react to the same fact; you need to add a consumer without touching
  the producer; temporary slowness of a consumer must not fail the user's action.
- **Cost you must budget for explicitly**:
  - **idempotency**: consumers run twice. `dedupe_key` column + unique index, or a processed-IDs
    set with TTL. A handler without idempotency is a corruption bug waiting for a redeploy.
  - **ordering**: not guaranteed. Design state machines that accept events out of order
    (`Order` transition table in `snippets/bad-vs-good.md`), or key by aggregate id to get
    per-key ordering on Kafka-like brokers.
  - **schema evolution**: events are an API. Version them (`order-placed@v2`), keep consumers
    reading old fields for a deprecation window, and add a **contract test** per event.
  - **debugging**: a trace id must cross the queue (propagate `traceparent`/correlation id).
- **Failure mode**: "event bus as duct tape" — teams publish internal state changes to avoid
  talking to each other, and nobody can tell which events are load-bearing. Keep a
  `docs/events.md` catalogue (producer, consumers, payload, retention) and treat it as code.
- **Outbox, always**: writing "DB row + published message" is two systems. Commit the event into
  an `outbox` table in the same transaction, then a relay publishes it. Without this you will
  lose events exactly when the broker hiccups.

### CQRS (+ event sourcing)

Separate write path (commands → model) from read path (queries → purpose-built projections).

- **Use when**: reads and writes have genuinely different shapes/scale (reporting over the same
  data users mutate; heavy read fan-out; complex UI projections).
- **Cost**: read model is eventually consistent — a user who saves and reloads may see the old
  value. Handle it deliberately: return the write version to the writer, or refresh the projection
  in-request for that one screen.
- **ES adds**: replay, temporal queries, audit for free; and schema migrations across events,
  snapshots, and a "can we still replay from 2019?" duty. **Adopt ES for a specific requirement**
  (audit trail, time travel), never as a generic persistence choice.
- **Failure mode**: CQRS-lite where the "command side" is a `UserDto` with 14 setters and the
  read side is the same table. Then you took the complexity and none of the benefit.

### Microservices

Independently deployable services around business capabilities, each owning its data.

- **Use when**: teams must ship independently (the scaling unit is *team*, not traffic), different
  languages/latency needs, or one component must scale 100x the rest.
- **Cost per service, honestly**: own DB, own pipeline, own on-call, contract tests, versioned
  APIs, retries+timeouts+idempotency on every edge, distributed tracing, and an
  availability target equal to the *product* of its dependencies' availabilities (4 hops at
  99.9% ≈ 99.6%).
- **Failure mode**: "distributed monolith" — services that must deploy together, share a DB, or
  call each other synchronously in a chain. If you cannot deploy one service on a Friday, it is
  not a microservice, it is a folder with latency.
- **Testability**: a service without a contract test against its consumers has no API, only a
  rumour. Use consumer-driven contracts (Pact-style) or a shared OpenAPI schema + CI check.

### Serverless / functions

- **Use when**: spiky or rare work (webhooks, thumbnail generation), glue between managed
  services, hard per-event cost sensitivity.
- **Cost**: cold starts, 15-minute limits (where applicable), no local parity unless you force it,
  and the architecture is invisible without tracing — budget for observability on day 1.
- **Failure mode**: business rules written inside the handler; then no unit test, no reuse, no
  portability. Keep handlers ~10 lines: decode → call a use case → encode. The use case is a plain
  function you can test in-process (this is the pattern behind `prompts/07-testability.md`).

### Pipe-and-filter / batch

`source → transform → transform → sink`, each stage a small unit with one contract.

- **Use when**: data pipelines, imports/exports, nightly reconciliation, media processing.
- **Wins**: each stage testable in isolation, resumable, parallelizable, replayable.
- **Failure mode**: stages that write to shared scratch state — now it is a distributed monolith
  with extra steps. Pass data forward, or write intermediate artifacts with a schema.

### Plugin / kernel-with-strategies

A stable core plus interchangeable providers behind one interface (payment gateways, tax
providers, notification channels, per-tenant rules).

- **Use when**: you have ≥3 near-identical `if provider == …` branches, or a partner/skills matrix.
- **Cost**: the registry, capability discovery, and one contract test suite run against every
  provider (that suite is the real deliverable).
- **Failure mode**: the interface records the *lowest common denominator* and each provider leaks
  specifics back into the core through `capabilities` flags. When flag-checking dominates, the
  abstraction is wrong — model the variants explicitly (enum + strategy, `10-code-smells`).

## 2. Selection matrix

| Pattern | Team size sweet spot | Independent deploys | Latency added | Ops cost | Failure isolation | Reversibility |
|---|---|---|---|---|---|---|
| Layered | 1–8 | no | none | low | none | high |
| Hexagonal / clean | 3–30 | no | none | low–med | none | high |
| Modular monolith | 5–50 | per module (PR), 1 pipeline | none | med | good | **very high** |
| Event-driven (inside mono) | 10–80 | yes, per consumer | ms–s | med–high | good | med |
| CQRS | 15–80 | maybe | ms | high | good | low |
| Microservices | 40+ | yes | 5–50 ms/hop | very high | best | **low** |
| Serverless | any, per feature | yes | cold start | med (no servers) | good | med |
| Pipe-and-filter | any, for data | n/a | batch | med | good | high |
| Plugin/kernel | 3–30 | no | none | med | good | high |

Read the last column as the warning label: microservices are the one shape you cannot undo in a
quarter. Choose the reversible option that meets today's requirement, and keep the seam clean so
the next step is a move, not a rewrite.

## 3. Getting there without a rewrite

- **Strangler fig**: put a routing facade in front of the legacy module; per feature, implement
  behind the facade, flip the route, delete the old path. Flip **one route at a time** and keep
  the old path warm for a defined window (metrics: same response class, p95 within X%, error
  rate equal).
- **Branch by abstraction**: introduce an interface *in front of* the legacy implementation,
  switch all callers to it, then replace the implementation in a separate PR. Two reviewable steps
  instead of one 4 000-line swap. This is also the pattern for `DUPLICATE_BLOCK`-scale dedup in
  `10-code-smells-refactorings.md`.
- **Seams before boxes**: before splitting anything, make the module's imports legal
  (`arch-scan` green) — the split is then a file move.
- **Parallel run for money paths**: shadow-execute the new path, compare results, alert, do not
  serve traffic from it until N days are clean.

## 4. Cross-cutting shapes you will need regardless

Named here because they are architecture, not style:

| Concern | Shape | One-line rule |
|---|---|---|
| Reliability | retry + timeout + circuit breaker + bulkhead | a client without an explicit timeout is a bug; retry only idempotent calls |
| Consistency | saga (orchestrated or choreographed) | each step needs a compensating action or the flow must be forward-only |
| Atomic side effects | transactional outbox | never "write then publish" |
| Readiness | health checks split liveness/readiness | liveness must not depend on a downstream DB |
| Migration | expand → backfill → contract | never drop a column in the release that stops writing it |
| Config | read at the edge, pass as data | no `getenv` inside domain functions |
| Time & randomness | injected clock/RNG | otherwise the test that fails on the 1st of the month is yours |

## 5. Deciding out loud: the ADR

Any pattern above is a decision with a cost. Write it down in 40 lines with
`templates/adr-template.md`: context, options (including "do nothing"), the cost you accepted,
and the trigger that would make you revisit ("revisit at 25 engineers, or when a module needs its
own DB"). An ADR without a revisit trigger becomes a tombstone.

## 6. Read next

- `12-clean-architecture.md` — the layer/boundary rules all of the above assume.
- `14-design-patterns.md` — the small-scale vocabulary inside each module.
- Playbook: `playbook/11-architecture-patterns.md` (worked trade-off, exercises).
- Prompts: `prompts/11-architecture-review.md`, `prompts/13-pattern-picker.md`.
