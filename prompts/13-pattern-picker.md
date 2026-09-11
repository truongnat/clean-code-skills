# 13 · Pattern picker — the shape, with its price tag

```text
PROMPT
───
I have a problem, not a pattern. Pick the smallest shape that solves it and price it honestly.
Do not recommend microservices, CQRS, event sourcing, a DI framework, or "a clean architecture
rewrite" unless the constraints below force them — and if they do, lead with the damage.

Input: problem statement, scale (users/sec, data size, team size), team experience, existing stack,
what must stay available when a dependency is down, deploy constraints, deadline.

Answer in this exact structure:

1. **Problem restated** in one sentence + the 2 constraints that actually decide the shape.
2. **Shortlist** — the 3 shapes that fit, each as a single line: one-line mechanism · what it
   buys · what it costs forever · how reversible it is (high/med/low).
3. **Recommendation** — one choice, and the sentence "we chose X over Y because Z, and we accept
   [cost]". Then what has to be true for this to stay right.
4. **What we will regret** — the 3 concrete failure modes of the chosen shape for OUR scale, and
   the early-warning signal for each (metric or smell).
5. **Module-level consequences** — which layers/modules exist as a result, which imports become
   illegal, and what must be a port (name it). Give the `arch-scan.config.json` snippet.
6. **First slice** — the smallest end-to-end vertical we can ship in ≤ 1 sprint to prove the shape,
   including what we deliberately keep monolithic/in-process while proving it.
7. **Reversal plan** — if this is wrong in a year, what is the exit, and what does it cost?
8. **Rejected** — each shortlisted-but-rejected option with one line of reason.

Rules of thumb you must apply explicitly:
- a synchronous call chain > 3 hops at request time → propose async/event and say what idempotency
  work that creates (dedupe key, outbox, retry policy);
- "we need it to scale" without a number → ask for the number, answer the number you get;
- 2+ teams touching the same folder weekly → boundary first, service later, always in that order;
- read/write shapes diverging but same data → CQRS-lite (separate query objects) before any
  replication story;
- framework in the domain layer is a smell no pattern justifies; put the adapter there instead.

If the honest answer is "your current modular monolith is fine, refactor the inside", answer that,
and name the 3 module-level changes to make instead.

MY CONSTRAINTS: [paste]
───
```

## How to use

Put the **number** in, even roughly: requests/min, rows, team size, deploy frequency. Patterns are
chosen by scale and team shape; without numbers the model defaults to the most impressive answer,
which is the wrong answer about 70 % of the time.

## Minimum input

The prompt's `Input:` line lists what it wants; these four are the ones without which the answer is
decoration:

- **one number for scale** (requests/min, rows, GB) — even an order of magnitude;
- **team size and how many teams** touch this code weekly, which decides rule 3 outright;
- **what must stay up** when a dependency is down;
- **the deadline**, because reversibility is only worth paying for when there is time to reverse.

## Output acceptance criteria

- [ ] all 8 sections present, including 7 (reversal) and 8 (rejected) — those are the two a model
      drops when it is selling you something;
- [ ] the recommendation names a cost you will pay forever, not just benefits;
- [ ] section 5 produces a pasteable `arch-scan.config.json` snippet. No check, no architecture;
- [ ] section 4's warning signals are metrics or smells you can actually observe;
- [ ] the first slice fits one sprint and says what stays in-process while proving the shape;
- [ ] if your numbers are small, the answer says "the monolith is fine". A recommendation that
      scales up regardless of the numbers ignored them.

## Keeping it from inventing symbols

```text
Rules on evidence:
- Use only the numbers and constraints I gave you. Never estimate my traffic, data size, team size
  or deploy frequency — write "UNKNOWN, and here is why it decides the answer" and ask.
- Do not cite a company's engineering blog, a benchmark or a "typical" figure as justification.
- Name modules, services and layers only with names from my stack description; anything new must be
  marked NEW.
- Every config snippet must use options that exist in the tool (`arch-scan`, dependency-cruiser,
  import-linter). If you are unsure a key exists, say so instead of inventing it.
- End with: "Decisions supported by my numbers: N. Assumptions: list them."
```

## Verification

- The chosen shape must be expressible as a check. If the answer cannot produce an
  `arch-scan`/dependency-cruiser rule, it is a preference, not an architecture.
- Write the outcome as an ADR (`../skills/clean-code/templates/adr-template.md`) with a revisit
  trigger — an ADR without one becomes a tombstone.

Related: `../skills/clean-code/references/13-architecture-patterns.md` · `04-solid-audit.md`
