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

1. **Naming** — names state intent. No `Data/Info/Manager/Util`. Booleans positive (`isEligible`,
   never `isNotEligible`). Carry the unit: `timeoutMs`, `totalMinorVnd`.
2. **Functions** — ≤ 40 lines, one job, ≤ 3 parameters, no boolean flag arguments, no hidden side
   effects, command separated from query.
3. **Magic values** — every literal inside logic gets a name; state strings become enums.
4. **Comments** — explain *why*, never *what*. No commented-out code. Every TODO carries a ticket
   and an owner.
5. **Formatting** — the formatter owns it. Raise it only with a number (line > 120, file > 400).
6. **Objects & data** — encapsulate, respect the Law of Demeter, no anaemic domain, no primitive
   obsession.
7. **Errors** — a specific exception type with data in the message; preserve the cause on every
   wrap; never swallow a catch; retries have a ceiling; map to HTTP/exit codes in exactly one place.
8. **Design** — SRP by reason-to-change, OCP only when a second variant actually exists, real DRY
   (not coincidental duplication), YAGNI, KISS.
9. **Hygiene & tests** — no leftover debug logs or dead code; tests assert behaviour and cover every
   new error branch; no `sleep`, no `random`, no mocking what we own.
10. **Architecture** — dependencies point inward (domain → application → infrastructure/interface),
    no cycles, no framework types in the domain, no feature reaching into another's internals.

## Hard constraints on your output

- **Never invent a symbol.** Cite only identifiers, files and line numbers that exist in what you
  were given. If a fix needs a file you cannot see, say which one and stop at the hypothesis.
- **No behaviour change inside a refactor.** If behaviour must change, that is a separate commit,
  announced as such.
- **No new abstraction with one implementation.** If you add one anyway, write the cost and the
  trigger that justified it (`skills/clean-code/templates/adr-template.md`).
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
