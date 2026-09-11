# 04 · SOLID/DRY/KISS/YAGNI audit — read the design

```text
PROMPT
───
Audit the DESIGN of the code I paste. Do not rewrite the code; diagnose and propose the smallest
fix.

For each class/module, answer in EXACTLY this shape:

**SRP** — List the "reasons to change" (who asks, and what changes). ≥2 → say how to split along
those reasons, NOT by line count. If there is only one reason: say "passes, do not split".
**OCP** — Point at every `switch`/`if-on-type`. For each: how many variants actually exist? How
often is one added? → recommendation (keep the if / table-driven / polymorphism) with the "cost of
each option" (files added, lines of abstraction).
**LSP** — Every place a parent must know about a child (`instanceof`, an override that throws
Unsupported, an empty method in the child). Propose fixing the contract or using composition.
**ISP** — Does any interface have a method implementers must "pretend" to support? Propose
splitting by capability.
**DIP** — List the dependencies `new`ed or imported directly inside business logic. For each: is it
a boundary (I/O, clock, randomness, time)?
→ Only the ones that genuinely are boundaries need a port/adapter; for the rest say "leave it".

**DRY** — Two kinds: (a) duplicated KNOWLEDGE (unify), (b) coincidental duplication (do not
unify). For every duplicated pair you find, declare (a) or (b) and state the deciding question.
**KISS** — Which part has to be read twice, or needs 3 files opened to follow one flow?
**YAGNI** — Which abstraction has exactly one implementation and no test fake? Count the lines it
occupies. Propose inlining/deleting it, plus "the signal that would make us write it again".

Constraint: every recommendation carries a **size** (XS: a rename · S: one function · M: one class ·
L: needs an ADR) and **the risk of doing it**. Close with: the 3 things to do THIS WEEK (XS/S, on
the path we already walk); everything else → propose an issue.

TEAM CONTEXT: [domain · which unit changes most · is the API published · what must not be touched]
CODE:
[PASTE THE CODE / the folder tree + imports]
───
```

## Minimum input

- more than one file. SRP and DIP are judged across a module — a single class in isolation makes
  the model guess at the reasons to change;
- **who asks for changes** in this area (one line: "pricing changes come from finance, the export
  format from ops"). This is the input that turns an SRP verdict from a guess into a finding;
- the **variant count** for anything you suspect of an OCP problem — how many payment providers /
  report formats / country rules exist *today*;
- what is **frozen** (published API, serialised event), because it sets the ceiling on every
  proposal.

## Output acceptance criteria

- [ ] every one of the eight headings is answered, including the ones that pass — an audit that
      lists only problems tells you nothing about where the design is fine;
- [ ] each SRP split is expressed as a reason-to-change, never as "this file is too long";
- [ ] each OCP recommendation quotes a variant count and a cost, and at least one says "keep the
      `if`" unless every switch genuinely warrants abstraction;
- [ ] every duplicated pair is explicitly labelled (a) or (b);
- [ ] every recommendation has a size tag and a risk;
- [ ] the closing list has at most 3 items, all XS or S. A "this week" list of 9 items is a wish.

## Keeping it from inventing symbols

```text
Rules on evidence:
- Judge only classes, methods and imports present in what I pasted. Quote the line for every
  finding (the switch statement, the `new`, the `instanceof`).
- Do not assume a subclass, implementer or caller you cannot see. If an LSP or ISP verdict needs
  one, say "unknown — run: rg -n 'implements <Interface>' src" and stop at the hypothesis.
- Do not invent a pattern name or library to justify a proposal, and do not cite a "common
  practice" as evidence. Cost in files and lines, or nothing.
- End with: "Findings quoted from the paste: N. Findings that need files I do not have: M."
```

## Tips

- Paste the output of `npx madge --circular src` and `python3 ../tools/cc-scan.py --json` alongside
  the code — given real data, the model abstracts for fun much less often.
- If it recommends building a framework, ask exactly one question back:
  **"which second variant is arriving in the next 6 months, and which requirement does it come
  from?"** If it cannot answer from the data you gave, make it withdraw the recommendation.

## Verification

```bash
python3 tools/cc-scan.py src --no-baseline      # DUPLICATE_BLOCK / COMPLEXITY moved?
python3 tools/arch-scan.py src --fail-on error  # the split did not create an illegal edge
```

Related: `../skills/clean-code/references/08-design-principles.md` · `11-architecture-review.md` ·
`13-pattern-picker.md`
