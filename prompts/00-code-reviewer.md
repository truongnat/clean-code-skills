# 00 · Code reviewer — the default prompt

**Use when:** you have a diff/PR/file and want it read against the Clean Code standard before merge.

```text
PROMPT
───
You are a senior engineer reviewing code against my team's Clean Code standard.
Your job: find problems IN ORDER OF COST, not to hunt for style.

Constraints:
- Do not comment on formatting/indentation/quotes — the formatter already owns those.
- Every comment carries: file:line, the rule broken, the concrete consequence, a fix
  (with code if under 15 lines).
- If you cannot tell whether something is a defect or an intention, ask (label `question:`)
  instead of concluding.
- At most 8 comments, ordered by damage. Roll trivial `nit`s into one closing line.
- If the code is good, say what is good and worth copying (label `praise:`).

Checklist to scan (numbered as in the standard):
1 Naming: names state intent, no `Data/Info/Manager/Util`, booleans phrased positively,
  units in the name (`Ms`, `MinorVnd`).
2 Functions: ≤40 lines, one job, ≤3 parameters, no boolean flags, no hidden side effects,
  command and query separated.
3 Magic values: every literal inside logic has a name; state strings are enums.
4 Comments: no commented-out code, no comment explaining "what", every TODO has a ticket.
5 Formatting: report only when it REDUCES readability (line >120, file >400 lines,
  related code far apart).
6 Objects & data: encapsulation, Law of Demeter (`a.b().c().d`), anaemic domain,
  primitive obsession.
7 Errors: no swallowed exception, specific exception type + cause preserved, timeout and
  retry with a ceiling, never swallow "so it does not crash".
8 Design: SRP (count the reasons to change), OCP (count the edits one new variant costs),
  real DRY vs coincidental duplication, YAGNI (an abstraction with one implementation),
  KISS (can it be read in one pass).
9 Hygiene & tests: leftover debug logs, dead code, tests that prove BEHAVIOUR and cover every
  new error branch, tests that do not mock everything, no sleep/random.

Output format:
## Verdict: <APPROVE | COMMENT | REQUEST CHANGES> — <one sentence>
## Blockers (must fix)
1. `file.ts:42` **EMPTY_CATCH** — Observation → Consequence → Fix
## Should fix
…
## Question / nit / praise
…
## Numbers
- If I pasted a `cc-scan` report: compare the score before/after and list the rules that are new.

TEAM CONTEXT: [language/framework · which layer · is the API published · what must not change]
EXISTING TESTS: [yes/no, the command to run them]
CODE/DIFF:
[PASTE THE CODE — if over 400 lines, paste file by file and hold the verdict until the last one]
───
```

## Minimum input

Without these, the answer is guesswork dressed as review:

- the **code or diff itself**, with real file names — not a retyped summary;
- **which layer** it lives in (domain / application / infrastructure / interface), because rule 7
  and rule 8 grade the same code differently at the edge and in the core;
- **whether tests exist** and how to run them — no tests means every refactor suggestion is a bet;
- **one frozen constraint** if you have one (`"OrderStatus is serialised into events"`).

Missing everything but the code? Say so in the prompt: *"I have no tests and cannot change the
public API — rank your findings accordingly."* A stated gap beats a silent one.

## Output acceptance criteria

The answer is usable when all of these hold; otherwise re-prompt rather than start editing:

- [ ] every comment points at a `file:line` **that exists in what you pasted**;
- [ ] every comment names a rule from the checklist, not a personal preference;
- [ ] each one states a consequence in terms of cost (a bug class, a future edit, a debug session),
      not "this is not clean";
- [ ] the verdict line matches the body — no `APPROVE` sitting above three blockers;
- [ ] nothing about formatting, unless it names a number (line length, file length);
- [ ] at least one `question:` or `praise:` on a non-trivial diff. An answer with neither is a model
      inventing findings to fill the shape.

## Keeping it from inventing symbols

The most expensive failure of this prompt is not a wrong opinion, it is a confident reference to a
function you do not have. Paste this after your code:

```text
Rules on evidence:
- Only cite identifiers, files and line numbers present in the text I pasted. Quote the exact line
  you are judging, on its own line, before each finding.
- If a finding depends on a file I did not paste (a caller, a base class, a config), do not guess:
  list it under "Files I need to confirm this" and stop at the hypothesis.
- Do not invent helper names, framework APIs or library functions to make a suggestion compile.
  Write the fix against what exists, or say which piece you would need.
- End with: "Findings supported by pasted code: N. Findings needing files I do not have: M."
```

Any finding whose quoted line you cannot find with a search is a hallucination — delete it and do
not argue with the model about it.

## Variants

**One section only** (when you care about a single area), add:
`Scan section 7 (errors) only. Skip every other section.`

**Self-review before opening the PR**, change the role to:
`You are me three weeks from now — reread this diff and list the 5 places you will have to ask
"what is this for".`

## Tips for avoiding a useless answer

- Paste the **tests** with the code. If the model cannot see tests, it proposes refactors you have
  no way to prove safe.
- State the constraints: `"OrderStatus is already serialised into events, it cannot become an enum"`
  — say nothing and it will rewrite it, and you lose 30 minutes reviewing what it caused.
- After the answer, run `tools/cc-scan.py` and compare: which rules did the model miss, which did it
  report falsely → write that back into the prompt so the team shares one calibrated version.

## Verification

```bash
python3 tools/cc-scan.py <the files you reviewed> --no-baseline   # score + the rules that fired
```

Related: `../skills/clean-code-review/SKILL.md` · `../skills/clean-code/checklists/code-review.md` ·
`01-name-finder.md`
