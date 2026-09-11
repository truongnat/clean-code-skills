# 06 · Comment cleaner — bin the noise, keep the "why", write the docstring

```text
PROMPT
───
Clean up the comments in the code I paste. Do NOT change a line of code (unless I allow step 3).

Step 1 — Classify EVERY existing comment (print the table):
| line | comment | kind | action |
kind: `why` (keep) · `what` (delete + rename the code) · `redundant-signature` (delete)
      · `dead-code` (delete, remind me to commit it separately) · `todo-no-ticket` (propose a ticket)
      · `api-contract` (keep / rewrite as a docstring) · `noise-separator` (delete)

Step 2 — For every `what` comment, propose ONE of three ways to turn it into code:
(a) rename a variable/function · (b) extract a predicate function (`isEligibleForX`) ·
(c) a value object or enum.
Give a diff of ≤ 10 lines for each, and mark which I **should** do now and which belongs in a
later PR.

Step 3 — Write the docstring/JSDoc for the public API, in this shape:
  one sentence of purpose + `@param` only where the unit is not obvious + `@throws` +
  the constraint/trade-off + `@see docs/adr/…` if I supplied one.
  Banned: restating the signature, "TODO", author + date (git already knows).

Step 4 — Conclude: how many comments remain, and **if any `why` comment is longer than 3 lines**
→ propose moving it to an ADR/README and leaving a one-line link behind.

CODE:
[PASTE THE CODE]
PUBLIC API LIST (needs docstrings): [list them, or "infer from the exports"]
───
```

## Sample output

```text
| 12 | // check the user is valid          | what  | delete → `if (user.canVote())` |
| 18 | // <= because the threshold is inclusive | why | KEEP — this is a business constraint |
| 24 | // const oldTotal = subtotal*1.21;  | dead  | delete (commit `chore: remove dead code`) |
| 31 | // TODO fix later                   | ticket| → `// TODO(AC-1240, minh): split renderer from calculator` |
| 40 | /** @param id id */                 | red.  | delete |
```

## Minimum input

- the code **with its comments intact** — obvious, and the most common mistake is pasting a
  cleaned-up version;
- which symbols are **public API**, or the instruction to infer it from the exports. Docstrings on
  private helpers are the noise this prompt is supposed to remove;
- the **ticket prefix** your tracker uses (`AC-`, `PROJ-`) if you want step 1's TODO rewrites to be
  pasteable;
- where ADRs live, if you have them, so step 4 can point somewhere real.

## Output acceptance criteria

- [ ] every comment in the paste appears in the table exactly once, kept ones included;
- [ ] the comment count after is **≤** the count before;
- [ ] no `why` comment was deleted — those are the only ones that carry information the code
      cannot;
- [ ] every `what` deletion comes with the code change that makes the comment unnecessary;
- [ ] docstrings state purpose, not the signature — a docstring that lists parameter types your
      types already declare is the same noise in a new place;
- [ ] every TODO left in the code has a ticket and an owner.

## Keeping it from inventing symbols

```text
Rules on evidence:
- Table only the comments present in the pasted code, quoted verbatim with their line numbers.
  Do not paraphrase a comment into something clearer and then judge your paraphrase.
- Never invent a ticket id, an ADR number, a spec section or an owner's name. If a TODO needs one,
  write `TODO(<TICKET?>, <owner?>)` with the placeholders visible and list it under "I need from
  you".
- A `@throws` entry may only name an exception the pasted code actually throws or propagates.
- Do not add a "why" comment explaining a decision I never told you about — if the reason is
  unknown, ask.
- End with: "Comments before: N. Comments after: M (M ≤ N). Invented tickets/ADRs: 0."
```

## Tips

- Do not let the model "clean up" by **adding** comments. Pin the constraint:
  `"The comment count afterwards must be ≤ the count before; if you add a comment you must delete
  2 lines of code."`
- Run the machine check afterwards to be sure:
  `python3 ../tools/cc-scan.py <file> --json | jq '[.findings[]|select(.rule|test("COMMENTED_CODE|TODO_MARK|BLOCK_COMMENT"))]'`

Related: `../skills/clean-code/references/04-comments.md` · `01-name-finder.md` ·
`00-code-reviewer.md`
