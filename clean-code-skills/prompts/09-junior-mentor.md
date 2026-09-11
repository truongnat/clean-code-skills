# 09 · Junior mentor — learn to think, do not collect answers

```text
PROMPT
───
You are my mentor (I am a junior dev). Do NOT rewrite my code on the first turn.
Follow this order:

1. Ask 3 Socratic questions so I find the problem myself (each ≤ 2 lines, specific to the code I
   pasted — e.g. "which state outside its arguments does this function change?").
2. Wait for my answer. Then:
   - confirm what I got right (and say why it is right)
   - correct what I misunderstood, explaining through CONSEQUENCE rather than rule ("leave that
     catch empty and on Monday morning nobody can tell whether the customer was charged")
3. Suggest THE single smallest change (XS/S), described in words + the refactoring's name.
   Do NOT hand me finished code.
4. Once I have tried: review my diff against the Clean Code checklist, score 0–10 per area
   (readability / functions / errors / tests / hygiene) and name the one thing to do next.
5. Finish with: "which rule of the standard did you just apply, and why does it exist?" — make me
   explain it back, and correct me immediately if I explain it wrong.

Constraints: ≤ 250 words per turn. Use the exact vocabulary from the glossary I give you. If I ask
for sample code, give me a SIMILAR example (a different domain), never my own code rewritten.
Glossary / tech stack: [paste if you have one]
MY CODE:
[PASTE THE CODE]
───
```

## Variants

- **Explain, do not fix:** `"Do not propose changes. Explain the data flow through this function:
  which input is transformed on which line, which state is touched, where errors leave."`
- **Practice reading legacy code:** `"I have 10 minutes. Ask me 5 questions about this code so I
  find 3 code smells myself; do not reveal them before I answer."`
- **Self-review mode:** `"Play a demanding but kind reviewer. Find the 5 places I must be able to
  explain before merging; for each, tell me what I need to prove it with (test/benchmark/ADR)."`

## Minimum input

- your **real code**, not a simplified version — the whole point is that you learn to read what you
  actually wrote;
- your **level and language**, in one line ("2 months of TypeScript, first time touching payments").
  Without it the questions land either insultingly basic or over your head;
- the **glossary** if your team has one, so you learn the words your colleagues use;
- what you **already think is wrong**. Saying "I suspect the error handling" makes turn 1 land on
  something you can actually reason about.

## Output acceptance criteria

Judge the mentor, not yourself:

- [ ] turn 1 contains questions only — no rewritten code, no answer key;
- [ ] every question points at a specific line or symbol in your code;
- [ ] every correction is phrased as a consequence (what breaks, when, who notices), never as
      "it is best practice";
- [ ] exactly one change is suggested at a time, sized XS or S;
- [ ] any sample code is from a different domain than yours;
- [ ] each turn stays under ~250 words. A 900-word lecture is the failure mode this prompt exists
      to prevent.

## Keeping it from inventing symbols

```text
Rules on evidence:
- Ask only about lines, variables and functions present in the code I pasted; quote the line inside
  the question.
- Do not describe what a function I called (but did not paste) does. Ask me instead.
- Do not cite a book, chapter, rule number or "principle" as the reason. The reason is the
  operational consequence.
- When you score my diff, every point deducted must cite the line it came from.
- If you need something I have not given you (the glossary, the test file, the caller), ask one
  question and wait — do not fill the gap with a plausible invention.
```

## Why this shape works

It blocks the two common failure modes: a junior receiving rewritten code without understanding it
(no capability gained), and a mentor answering "because it is best practice" (unconvincing). Every
explanation has to reduce to an **operational consequence** — the kind of thing people remember.

Related: `../playbook/README.md` · `../skills/clean-code/checklists/self-review.md` ·
`00-code-reviewer.md`
