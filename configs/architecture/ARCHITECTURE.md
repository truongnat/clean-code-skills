# ARCHITECTURE.md — the one-page map a stranger needs

Put this file at the repo root, keep it under 120 lines, and treat it as code: a pull request
that changes the shape of the system changes this file in the same commit.

## What this system is

> One paragraph. Who uses it, what it decides, what it must never lose.

## Shape

    HTTP / CLI  ->  application (use cases)  ->  domain (rules)
                          ^                          |
                    ports implemented by  ->  infrastructure (db, queues, APIs)

- **Layers:** domain (rank 0) / application (1) / infrastructure (2) / interface (3).
- **Dependency rule:** imports point inward. Nothing in domain imports anything outward.
- **Machines that enforce it:** `arch-scan.py` (CI), `dependency-cruiser` (JS),
  `import-linter` (Python), ArchUnit (Java), `go-arch-lint`/depguard (Go).

## Bounded contexts / features

| Context | Owns | Talks to others via |
|---|---|---|
| checkout | cart, order placement | `features/checkout/index.ts`, `OrderPlaced` event |
| pricing  | discounts, fees   | `features/pricing/index.ts` (pure function) |

## Where the messy parts live

| Concern | Home | Note |
|---|---|---|
| Validation | `domain/rules.py` | pure, no framework types |
| DB sessions | `infrastructure/db.py` | never leak a session into a use case |
| Retries / timeouts | `infrastructure/http.py` | transport only |
| Feature flags | `interface/flags.py` | read once at the edge, pass down as data |

## Decisions that are not obvious

- Why a modular monolith instead of services: `docs/adr/0007-…`.
- Why `orders` publishes events instead of calling `billing`: `docs/adr/0011-…`.

## What we deliberately allow

- `infrastructure` may import `application` (implementing ports).
- `interface` may import everything except a database driver directly.
- Until 2026-12-31: 4 files in `domain/legacy/` import SQLAlchemy — tracked in `ARCH-142`,
  blocked from growing by `.clean-code-baseline.json`.

## How to check it

    python3 tools/arch-scan.py src --fail-on error
    npx dependency-cruiser src --config .dependency-cruiser.cjs   # JS/TS
    lint-imports                                                   # Python
