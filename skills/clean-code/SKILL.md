---
name: clean-code
description: >-
  Apply clean-code and clean-architecture standards when writing, refactoring or reviewing
  code: meaningful naming, short single-purpose functions, no magic numbers, comments that
  explain why, formatting decided by tooling, error handling that never swallows,
  encapsulation and Law of Demeter, SOLID/DRY/KISS/YAGNI, layering and dependency direction,
  architecture and design pattern selection, plus CI quality gates and refactoring workflow.
  Use when the user asks for "clean code", "refactor", "code review", "improve code quality",
  "explain/read this code", "code smells", "extract function", "set up lint/prettier/ruff",
  "design this module", "should we use microservices / a monolith / events / CQRS",
  "which pattern fits", "enforce architecture in CI", when creating a new module/class/function
  in a long-lived project, or when defining team standards and gates. Language-agnostic:
  TypeScript/JavaScript, Python, Java/Kotlin, Go, C#.
metadata:
  version: "1.1.0"
  language-agnostic: true
  sources: "Robert C. Martin – Clean Code & Clean Architecture; Kent Beck – Extreme Programming; Joshua Kerievsky – Refactoring to Patterns; Martin Fowler – Refactoring (2nd); Alistair Cockburn – Hexagonal Architecture; Eric Evans – Domain-Driven Design"
---

# Clean code & clean architecture — the field ruleset

> **Scanner path:** commands below assume `tools/cc-scan.py` / `tools/arch-scan.py` are in the
> repo. If they are not, the same scanners may be on `PATH` as `cc-scan` / `arch-scan` (identical
> flags) — see `INSTALL.md` §1b. If neither exists, ask for the report instead of guessing numbers.

## 0. When this skill activates

| Situation | What to do |
|---|---|
| Writing a new module/function for code that will outlive a sprint | §1 + §2, then self-check with §6 |
| "Refactor this function/file" | §1 → apply the rule → **keep behaviour identical** → run tests |
| Reviewing a PR | `checklists/code-review.md`, comment with `templates/pr-review-comment.md` |
| Setting the standard for a team | `playbook/` + copy `configs/` into the repo + wire `tools/cc-scan.py` and `tools/arch-scan.py` into CI |
| Code works but feels dirty | §4 (hygiene) first, refactor second |
| "How should this be structured / which pattern / monolith or services?" | §3 + `references/12..14-*.md`, decide in an ADR |

The one principle every rule below is derived from: **code is read far more often than it is
written**. Each rule shortens the next reader's time and cost — and where a rule does not, the
exception process (§7) exists on purpose.

## 1. Before you write (5 questions, 60 seconds)

1. What **problem** does this function/class solve for the business? One sentence, no "and".
2. Who **owns** the concept being coded? Data and the behaviour over that data live together (§2.5).
3. Does calling it **change state**? Then it must not also return data (CQS).
4. What test would prove it correct? If you cannot write one, the design is wrong — usually global
   I/O is leaking in.
5. Am I **guessing at the future**? Not needed yet → YAGNI; no interface "for later".
6. Which **layer** does this file belong to, and is it allowed to import what I am about to import?
   (`references/12-clean-architecture.md`)

## 2. Core rules (checked while coding, not while reading books)

### 2.1 Naming
- Name the **intention**, not the mechanism: `daysSinceLastLogin` > `d`; `canEdit` > `checkPerms`.
- Banned empty names: `data`, `info`, `obj`, `tmp`, `val`, `result`, `manager`, `util`, `helper`, `common`.
- Numbers carry units: `timeoutMs`, `maxRetries`, `balanceVnd` > `timeout`, `max`.
- Constants UPPER_SNAKE at module level, never inline in logic: `MAX_INLINE_ITEMS = 5`.
- Do not repeat the context inside member names: `Order.customerName` > `Order.orderCustomerName`.
- Booleans are affirmative: `isBlocked`, not `isNotActive` (to negate, name the positive: `isOpen`).
- `i`/`j` only when the loop body is ≤ 3 lines; otherwise `itemIndex`, `page`.
- Follow platform convention: `camelCase` (JS/TS/Java), `snake_case` (Python/Rust), `PascalCase` for types/classes, Go: exported = PascalCase, short receiver names.

### 2.2 Functions
- **Unreasonably short**: recommended ≤ 20 lines, warn > 40, must split > 70.
- **One level of abstraction per function**: `processOrder()` calls `validate() → charge() → notify()`; no 15-line nested loop in between.
- **Single responsibility for the function**: if a comment is needed to say "and this part…", split it.
- **Parameters**: 0–2 good, 3 soft limit, ≥ 4 becomes an Options/Command object.
  `updateProfile({ email, phone, address, notify })` beats four positional arguments.
- **No hidden side effects**: `getFoo()` that writes to the DB is lying.
- **Command–Query Separation**: queries change nothing; commands return nothing meaningful.
- **A boolean flag is two functions in a trench coat**: `render(doc, isForPrint)` → `renderForScreen(doc)` + `renderForPrint(doc)`.
- **Errors are exceptions, not `null`/`-1`/error codes** (§2.5).
- `try` wraps only what can fail; return `Optional`/`Result` when "not found" is a normal outcome.
- Guard clauses at the top: `if (invalid) return;` instead of wrapping the body in `if (valid) { … }`.

### 2.3 Magic numbers & strings
- Every literal **in logic** gets a name: `status == 3` → `status == OrderStatus.AWAITING_PAYMENT`.
- A literal repeated ≥ 3 times becomes a constant or enum, strings included (`"enqueue-topic-orders"`).
- A literal **declared** on a line assigning an ALL_CAPS name is the solution, not the violation.
- `0`, `1`, `-1`, `2` in indices/math are fine; `1000` meaning "ms" must become `MS_PER_SECOND` or a renamed variable.

### 2.4 Comments
- Default: **the code explains itself**. A comment describing *what* it does means the code is blind.
- Worth writing: **why**, constraints, trade-offs, ADR/ticket links, warnings about consequences, workarounds for library bugs.
- A TODO needs an ID: `TODO(AC-123) who, what, when` — otherwise open the issue and delete the comment.
- Banned: commented-out code, `// set name to name`, `// begin loop`, JSDoc restating the signature.
- Public API docs (docstring/JSDoc) are the exception: there the comment **is** the contract.

### 2.5 Data, structures & exceptions
- Fields private; expose **behaviour**, not raw getters/setters. Records/DTOs are fine when they *are* data.
- **Law of Demeter**: one hop. `order.customer.address.city` → `order.shippingCity()`.
- Do not dissect another object's internals: pass data, or ask for the answer.
- Throw **specific** exception types with an actionable message, keep `cause`. Never `throw new Exception("error")`.
- **Never** `catch { }` / `except: pass`. Catching means: log + a decision (retry / fallback / rethrow with context).
- Do not catch the root `Exception`/`Throwable` "to be safe".
- Small functions + one `try` at the boundary read better than seven `try` blocks scattered around.
- Validate at the **edge**, then trust the type inside (parse, don't validate).

### 2.6 Formatting
- Formatting is **not a review comment**: Prettier / Black / ruff-format / gofmt decide, CI blocks.
- ≤ 120 chars (JS/TS/Java/Go), ≤ 88 (Python). No horizontal scrolling in review.
- Related code near each other: caller above callee, declaration near use.
- Files ≤ 400 lines; beyond that there are usually two modules in one file.
- One concept in one place: constants at the top of the module or in `constants.ts`, not sprinkled mid-function.

## 3. Design: principles, layers, patterns

| Principle | Use it when | Don't when |
|---|---|---|
| **SOLID** | there are ≥ 2 real reasons to change, or ≥ 2 real implementations | one implementation and an interface already → speculative generality |
| **DRY** | the same **business knowledge** repeats | coincidental duplication: two places that look alike but change for different reasons |
| **KISS** | always; prefer the boring solution | when "simple" means skipping a boundary and producing a 60-line `if` |
| **YAGNI** | nobody asked for it yet | when the cost of changing later is huge (DB schema, public API) |
| **Dependency rule** | always, in CI | — (it is the one architectural rule that never becomes overhead) |

Detail + code for each SOLID letter: `references/08-design-principles.md`.
Smell → refactoring → order of operations: `references/10-code-smells-refactorings.md`.
Layers, ports & adapters, and what `arch-scan` checks: `references/12-clean-architecture.md`.
Choosing a shape (modular monolith, events, CQRS, services, serverless…): `references/13-architecture-patterns.md`.
Pattern catalogue + when each one is premature: `references/14-design-patterns.md`.

## 4. Hygiene sweep before opening a PR (§9 of the playbook)

```bash
# 1) team standard + architecture, both zero-dependency scripts
python3 tools/cc-scan.py . --fail-on error
python3 tools/arch-scan.py . --fail-on error

# 2) formatter + linter
npx prettier --check . && npx eslint . --max-warnings=0   # JS/TS
ruff check . && ruff format --check .                     # Python
gofmt -l . && golangci-lint run                            # Go

# 3) dead code and leftovers
rg -n "console\.(log|debug|info|trace)\(|debugger\b|System\.out\.print|fmt\.Print|TODO|FIXME|XXX|HACK" src

# 4) tests must run and must prove something
npx vitest run --coverage 2>/dev/null || pytest -q
```

Not deleting debug logs = pushing noise into the monitoring system. No tests = every later refactor
is a gamble. No lint = you are paying interest with your colleagues' time.

## 5. Safe refactoring (discipline beats memory)

1. **Lock the behaviour first**: tests exist (or write characterization tests for untested legacy).
2. Each refactoring step **preserves input→output**. Behaviour change = separate PR, said out loud.
3. Small steps: rename → extract function → move → inline. Tests between steps. Never "clean the whole
   file at once" — a 2 000-line diff cannot be reviewed.
4. Use the IDE's automated refactorings (safe rename, extract method, introduce parameter object). Do not
   search-replace public API names by hand.
5. `Red → Green → Refactor`: it must pass before it may be prettied.
6. Boy Scout rule: leave the file cleaner than you found it — **but not inside** a feature PR.

## 6. Definition of Done

Tick only what is true. Below 7/10, do not ask for review.

- [ ] Every function ≤ 40 lines, one job, ≤ 3 parameters
- [ ] No magic numbers/strings; business concepts have names
- [ ] No dead code, no debug logs, every TODO has a ticket ID
- [ ] Exceptions handled on purpose — no empty catch
- [ ] Tests cover error and boundary paths, not only the happy path
- [ ] `cc-scan` + `arch-scan` + linters + formatter clean (no `--no-verify`, no bare `# noqa`)
- [ ] File and term names match the domain's **ubiquitous language** (no `data2`, `flag`)
- [ ] **Imports point inward**: no `UPWARD_DEPENDENCY`, no `LAYER_CYCLE`, no `BOUNDARY_LEAK`
- [ ] Cross-module changes are described in `ARCHITECTURE.md` / an ADR when the shape moved
- [ ] Another engineer reads it without asking "what is this for?"

The 0–100 rubric and per-level thresholds: `checklists/self-review.md`; architecture maturity:
`playbook/appendix-b-maturity-model.md`.

## 7. When you are **allowed** to break a rule (and must say so out loud)

Allowed, provided the exception is written **in place** and **scoped**:

```ts
// table-driven: a loop + a value here reads better than 12 if-else (skill §2.3)
// cc-scan:allow-file LONG_FUNCTION — parserStateMachine is one state loop, see docs/adr/0012
// arch-scan:allow UPWARD_DEPENDENCY — temporary, tracked in ARCH-142, gone in Q4
```

- Hot path needing micro-optimisation → duplication allowed, **with a benchmark attached** in the PR.
- Spike/prototype → dirty is fine, but delete or rename it before merge, or label `// SPIKE — not production`.
- Generated code (protobuf, OpenAPI, Prisma client) → exclude from linting; never hand-edit.
- Big legacy → `cc-scan --update-baseline`: freeze the old debt, **block only new** violations. No big-bang rewrite.

The other direction also needs saying: no "functions under 20 lines" rule justifies cutting a coherent
algorithm into eight one-line functions that a reader has to bounce between. Line counts are a proxy,
not a goal. Same for architecture: a layer you cannot name a cost for is decoration.

## 8. Map of this skill's documents

| I want | Open |
|---|---|
| Bad/Good examples per topic (4 languages) | `references/01..09-*.md` |
| Smell → refactoring name → how | `references/10-code-smells-refactorings.md` |
| Testability as a design driver | `references/11-testing-for-clean-code.md` |
| Layers, ports & adapters, dependency rule | `references/12-clean-architecture.md` |
| Architecture pattern selection + costs | `references/13-architecture-patterns.md` |
| Design patterns, and when each is premature | `references/14-design-patterns.md` |
| PR review / self review checklists | `checklists/code-review.md`, `checklists/self-review.md` |
| PR comment wording that does not sting | `templates/pr-review-comment.md` |
| ADR & refactor-plan templates | `templates/adr-template.md`, `templates/refactor-plan.md` |
| Scanners and how to wire them | `tools/cc-scan.py`, `tools/arch-scan.py`, `configs/ci/`, `configs/architecture/` |
| Team training / onboarding | `playbook/` (read 01→12 in order) |
| Prompts for Copilot/Cursor/Claude | `prompts/` (00→13) |

## 9. The three most common mistakes with this skill

1. **Big-bang "clean the whole repo"** → 400 conflicts, two sprints frozen. Use baseline + scout +
   ratchet the rules one quarter at a time.
2. **Weaponised review**: demanding a rename while a logic bug ships. Whatever a machine can check,
   let the machine check — put humans on design and behaviour.
3. **Rules as religion**: 100 % coverage on code that will be deleted, 12 abstraction layers for a
   three-day feature. Standards exist to lower the cost of change, not to decorate the repo.
