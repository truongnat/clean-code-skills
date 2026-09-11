---
name: clean-architecture
description: >-
  Design and review the shape of a system: layers and the dependency rule, ports and adapters,
  bounded contexts and feature boundaries, modular monolith vs microservices vs event-driven vs
  CQRS vs serverless, choosing design patterns without over-engineering, and enforcing all of it
  in CI with import checks. Use when the user asks "how should I structure this", "where does this
  code belong", "monolith or microservices", "should we use events/CQRS", "which pattern fits",
  "our modules are coupled", "enforce architecture", "clean architecture / hexagonal / DDD
  boundaries", or before splitting a service, adding a framework, or opening a module boundary.
metadata:
  version: "1.1.0"
  pairs-with: "clean-code (module-level quality) — this skill is the system-level half"
  sources: "Robert C. Martin – Clean Architecture; Alistair Cockburn – Hexagonal Architecture; Eric Evans / Vaughn Vernon – DDD; Simon Brown – Software Architecture for Developers; Chris Richardson – Microservices Patterns"
---

# Clean architecture — sub-skill

Parent skill: `../clean-code/SKILL.md`. Deep material: `../clean-code/references/12-clean-architecture.md`,
`13-architecture-patterns.md`, `14-design-patterns.md`. Tooling: `tools/arch-scan.py` +
`configs/architecture/`.

## 0. Trigger table

| Ask | Do this |
|---|---|
| "Review the structure of this repo" | §1 census → §2 dependency rule → report with the vocabulary of §5 |
| "Where does this code belong?" | §3 placement test, 4 questions |
| "Should we split into services / use events / CQRS?" | §4, in that order, with the reversibility column of `references/13` |
| "Which pattern for this problem?" | `references/14-design-patterns.md` §1–§2; if no pattern's *problem* is present, the answer is "none" |
| "Enforce it" | §6: config file + CI job + baseline, 30 minutes of work |

## 1. Census first, opinions second (5 minutes)

```bash
# what does the repo actually look like?
python3 tools/arch-scan.py src --fail-on none          # layers, cycles, leaks, drift
find src -type d -maxdepth 2 | sort                    # declared vs real structure
git log --since='90 days ago' --name-only --pretty=format: -- src | sort | uniq -c | sort -rn | head -20
```

The `git log` line is the one that settles arguments: folders that change in the same commit belong
together; folders that never co-occur should not import each other. Boundaries drawn from
*change coupling* survive; boundaries drawn from nouns in the domain model do not.

## 2. The only two hard rules

1. **Dependency rule** — source code dependencies point inwards (rank 0 = domain). Outer knows
   inner; inner never knows outer. If the inner layer needs the outer, it declares a port and the
   outer implements it. → `UPWARD_DEPENDENCY`, `LAYER_CYCLE`.
2. **Boundary rule** — a feature is reached only through what it publishes (public module,
   command, event). → `BOUNDARY_LEAK`.

Everything else in this field is a trade-off, and trade-offs get an ADR
(`../clean-code/templates/adr-template.md`), not a fight in review.

## 3. Placement test — where does this file belong?

| Question | If yes |
|---|---|
| Does it encode a business rule/invariant, with no I/O? | `domain` — plain types, no framework imports (`DOMAIN_FRAMEWORK_IMPORT` blocks the shortcut) |
| Does it orchestrate a business action and own its collaborators? | `application` — use case + the ports it needs |
| Does it talk to a database/queue/HTTP API and translate shapes? | `infrastructure` — adapters |
| Does it decode a request, call one use case, encode a response? | `interface` — handler/controller/CLI; keep it ~10 lines |
| Does it do two of the above? | Split it before you place it |

Tells that it landed in the wrong place: a use case with SQL in it; a controller with a `for` loop
that computes money; a domain object whose constructor opens a session; `datetime.now()` inside a
rule (untestable at midnight — inject a `Clock` port instead).

## 4. Choosing the shape (the short version of `references/13`)

```
1 deployable, ≤ 8 engineers            → layered + hexagonal inside. Stop.
2–5 domains, 5–50 engineers            → modular monolith: features + enforced boundaries.
   (this is the answer ~80% of the time)
consumers must react independently     → + events (outbox, idempotency, catalogue). Do not split the deployable yet.
read/write shapes diverge hard          → CQRS (no ES unless audit/time-travel is the requirement).
teams must deploy independently,
each owning its data, at 40+ people     → microservices, one at a time, via strangler fig.
spiky glue work, per-event cost         → serverless with the rules in a library, handlers ~10 lines.
```

Say the cost out loud when you recommend one: "modular monolith costs us one shared DB and CI
enforcement; it buys per-module isolation today and a clean seam if we ever split". A pattern
proposed without its price tag is a fashion statement.

## 5. Review vocabulary — name the failure, not the person

| What you see | Say this | Fix |
|---|---|---|
| domain imports a driver | "the domain can't be tested without the DB now" | port + adapter |
| two layers import each other | "this ring blocks us from replacing either" | invert one edge / publish an event |
| `features/a` imports `features/b/internal` | "boundary leak: their refactor becomes our incident" | public API, event, or move the shared part down |
| 4 pass-through layers | "these layers add no decision" | delete the empty ones |
| everything in `shared/utils` | "shared is where boundaries go to die" | give it an owner, or duplicate until the second user appears |
| one interface, one implementation, no reuse | "dead abstraction" | inline it, or name the second implementation you expect |
| handler with 80 lines of logic | "logic at the edge is untestable and unreusable" | move into a use case, keep mapping at the edge |

## 6. Enforcement recipe (do this once, per repo)

```bash
cp configs/architecture/arch-scan.config.json .          # edit layer names/globs to match reality
python3 tools/arch-scan.py src --fail-on error           # first run: expect a red report
python3 tools/arch-scan.py src --json -o arch.json       # keep it as the freeze point in the PR
# add the language-native exact check too (they disagree sometimes; the exact one wins):
#   JS/TS:  npx dependency-cruiser src --config .dependency-cruiser.cjs
#   Python: pipx install import-linter && lint-imports
#   Java:   ArchUnit test — see configs/architecture/demo/java
```

Then add the CI job (`configs/ci/github-actions-clean-code.yml` → `arch-scan` step) and, if the repo
is legacy, freeze the current violations in a baseline/`allow` comment with a ticket, so the gate
blocks **new** edges instead of being turned off in a week.

For a working, measured example of both a broken and a clean layering, see
`configs/architecture/demo/python` (import-linter: 2 contracts BROKEN → KEPT after removing one
file; `arch-scan`: 82.0 → 100.0) and `configs/architecture/demo/java` (ArchUnit, exit 1 → 0).

## 7. What "good" looks like after 90 days

- `arch-scan` and the language-native checker are red-blocking in CI, and the red list is empty or
  carries ticketed exceptions with dates;
- `ARCHITECTURE.md` at the root matches the folder tree (a stranger can place a new file without asking);
- a new use case can be unit-tested with fakes, and the test suite for the domain needs no DB;
- at least one module was moved or replaced **without** touching another module's internals —
  that is the only real proof the boundaries are load-bearing.

## 8. Anti-goals

- Do not "clean-architect" a codebase you are about to delete; ask what the code must survive.
- Do not require an ADR for adding a file to an existing layer; require one for adding a layer or a
  boundary.
- Do not chase a diagram over a dependency test. The diagram is a by-product of the check.
