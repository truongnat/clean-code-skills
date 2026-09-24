# AGENTS.md — Clean Code standard for this repo

Portable agent instructions. Copy this file to your repo root: Codex, Cursor, Grok and Antigravity
all read `AGENTS.md`; Claude Code reads `CLAUDE.md` (point it here with one line, or copy this file
under that name). Keep it short — it is loaded into every session.

## What to do before writing code

1. Read the skill that matches the task, do not work from this summary alone:
   `skills/clean-code/SKILL.md` (the router) · `skills/clean-architecture/SKILL.md` (structure) ·
   `skills/clean-code-review/SKILL.md` · `skills/clean-code-naming/SKILL.md` ·
   `skills/clean-code-refactoring/SKILL.md` · `skills/clean-code-error-handling/SKILL.md` ·
   `skills/clean-code-formatting-hooks/SKILL.md`.
2. Run the scanners on what you are about to touch, so the conversation starts from a number:
   `python3 tools/cc-scan.py <paths> --no-baseline` and, for structural work,
   `python3 tools/arch-scan.py src`.
3. State which rule you are applying and why. "It is cleaner" is not a reason; a reading cost or a
   change cost is.

## The rules, in the order they cost money

1. **Naming & Intent** — names state business intent. No `Data/Info/Manager/Util`. Booleans positive (`isEligible`,
   never `isNotEligible`). Carry the unit: `timeoutMs`, `totalMinorVnd`.
2. **Cognitive Complexity over Line Count** — keep cognitive complexity low (≤ 10 per function). Guard clauses
   at top, flat control flow. Linear transformations/JSX can exceed 40 lines; branch storms and deep nesting (>3 levels) cannot.
3. **Cohesion over Micro-Fragmentation** — do NOT extract single-use 3-line helper functions that break reading flow.
   Keep cohesive business logic together.
4. **Magic values** — every literal inside logic gets a name; state strings become enums.
5. **Comments** — explain *why*, never *what*. No commented-out code. Every TODO carries a ticket
   and an owner.
6. **Formatting** — the formatter owns it. Raise it only with a number (line > 120, file > 400).
7. **Objects & data** — encapsulate, respect the Law of Demeter, no anaemic domain, no primitive
   obsession.
8. **Errors** — a specific exception type with data in the message; preserve the cause on every
   wrap; never swallow a catch; retries have a ceiling; map to HTTP/exit codes in exactly one place.
9. **Pragmatic Design** — SRP by reason-to-change, OCP only when a second variant actually exists, real DRY
   (not coincidental duplication), YAGNI, KISS. Colocate code by feature (Vertical Slice) before layer-splitting.
10. **Hygiene & tests** — no leftover debug logs or dead code; tests assert behaviour and cover every
    new error branch; lock behavior before refactoring; no `sleep`, no `random`, no mocking what we own.
11. **Architecture** — dependencies point inward (domain → application → infrastructure/interface),
    no cycles, no framework types in core domain, no feature reaching into another's internals.

## Hard constraints on your output (Negative Constraints)

- **Never invent a symbol.** Cite only identifiers, files and line numbers that exist in what you
  were given. If a fix needs a file you cannot see, say which one and stop at the hypothesis.
- **No behaviour change inside a refactor.** Lock behaviour with tests first. If behaviour must change, that is a separate commit,
  announced as such.
- **No speculative abstractions.** Never create an Interface, Abstract Class, Adapter, or Port with only one implementation.
- **No shotgun surgery helpers.** Do not split a readable linear function into fragmented micro-functions used only once.
- **No anemic mapper chains.** Do not add 4 layers of DTO mappings for straightforward operations unless crossing architectural boundaries.
- **Exceptions must be visible**: `cc-scan:allow <RULE> — <reason>` / `arch-scan:allow <RULE> —
  <ticket>` on the line, never a silently disabled rule.
- **Prove it before you claim it.** Run the command and paste the output; do not assert a score, a
  test count or a coverage number you did not measure.

## Definition of done

```bash
python3 tools/cc-scan.py <changed paths> --fail-on error
python3 tools/arch-scan.py src --fail-on error      # when the change touches structure
<your test command>                                  # green, and it covers the new error branches
```

Full curriculum in `playbook/`, copy-paste prompts in `prompts/`, working linter and CI config in
`configs/`.
