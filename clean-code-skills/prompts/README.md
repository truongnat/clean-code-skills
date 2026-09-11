# Prompt pack — the Clean Code standard in one paste

For use with ChatGPT / Claude / Copilot / Cursor / any LLM. One file per task, each written as
`Role → Context → Constraints → Output format` so the model does not improvise.

| File | Use when |
|---|---|
| `00-code-reviewer.md` | **The default.** Review a whole diff/PR against the 9 sections of the standard |
| `01-name-finder.md` | Stuck on a name: rename a variable/function/file |
| `02-extract-function.md` | A function is too long and must be split without changing behaviour |
| `03-magic-numbers.md` | Turn magic numbers/strings into named constants and enums |
| `04-solid-audit.md` | Audit the design: SRP/OCP/LSP/ISP/DIP + abstractions that earn nothing |
| `05-error-handling.md` | Design or repair exceptions, retry, fallback |
| `06-comment-cleaner.md` | Bin the noise comments, keep the "why", write the docstrings |
| `07-testability.md` | Unlock code you cannot test (dependencies, boundaries) |
| `08-legacy-refactor-plan.md` | A multi-step refactor plan for a legacy module |
| `09-junior-mentor.md` | Learn instead of collecting answers — Socratic tutor mode |
| `10-pr-description.md` | Write a PR description a reviewer does not have to guess at |
| `11-architecture-review.md` | Review the structure: layers, dependency rule, cycles, boundary leaks, testability |
| `12-boundary-designer.md` | Cut boundaries by change coupling + enforcement config + migration in ≤ 4 PRs |
| `13-pattern-picker.md` | Pick the shape (monolith/events/CQRS/services) with its price and its way back |

## What every file contains

Beyond the prompt itself, each file carries the three things that decide whether the answer is
worth anything:

- **Minimum input** — what must be pasted. Below that line the model is guessing, and a confident
  guess costs more than no answer.
- **Output acceptance criteria** — a checklist for deciding the answer is usable *before* you start
  editing code. Failing it means re-prompt, not "fix it up as you go".
- **Keeping it from inventing symbols** — a block to paste after your code that forbids citing
  identifiers, files, line numbers, tickets and sources that are not in front of it, and makes the
  model count its own unsupported claims. This is the single highest-value paragraph in the pack:
  the expensive failure is never a wrong opinion, it is a fix written against a function you do not
  have.

## Quick start

```text
# ChatGPT/Claude: open the file, copy the ```PROMPT``` block, paste your code into [PASTE THE CODE]
# Cursor / Windsurf: add this whole folder to your rules
# Claude Code / CLI:  cp -r ../skills/clean-code* .claude/skills/   (the skills already carry these rules)
```

## Three rules that stop a prompt backfiring

1. **Give context, not just code.** Add the language, the framework, the constraints ("this API is
   published, the signature cannot change") and the **tests you already have**. The model knows
   nothing about your 40 callers unless you say so.
2. **Ask for small steps and no behaviour change.** Every prompt here carries that constraint —
   do not delete it. "Refactor this whole file to be clean" = 2000 lines nobody can review.
3. **Never paste secrets, PII or credentials.** This pack is designed for pasting a **function or a
   file**, not your `.env` or customer data. For a large repo: run `tools/cc-scan.py` (offline,
   entirely local) and give the model the **report** plus the relevant code.

## Verifying the model's output (mandatory)

```bash
python3 ../tools/cc-scan.py <file> --json      # did the score improve?
npx tsc --noEmit / ruff check / go build       # anything broken in types or lint?
npm test / pytest -q                            # are the tests still green?
git diff --stat                                 # is the diff far smaller or larger than you asked for?
```

**Confident** and **wrong** is the most common combination: it will delete a `catch` to clear a
warning, or rename an API that 5 other services call. The checklist at
`../skills/clean-code/checklists/code-review.md` applies exactly as it does to code written by a
person.
