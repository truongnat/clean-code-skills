# Session 1 · What clean code means — four properties, and how to measure them

**Duration:** 45 minutes · **Pre-work (facilitator, 10 min):** run `cc-scan` on the team repo and paste
the output into the meeting doc. **Output of the session:** four agreed properties + four tracked
metrics, written into `CONTRIBUTING.md`.

> Format rule for every session in this playbook: at most 10 minutes of slides. Open the team's real
> repo. If nobody is uncomfortable by minute 25, you ran a lecture, not a workshop.

## 1. Open with your own numbers (10 minutes)

```bash
python3 ../tools/cc-scan.py . --json -o /tmp/cc.json
jq '{score, grade, counts, top: ([.findings[].rule] | group_by(.) | map("\(length) \(.[0])")
    | sort | reverse)[:5]}' /tmp/cc.json
git log --since="6 months ago" --format= --name-only | sort | uniq -c | sort -rn | head -10
```

Write three numbers on the board: the **clean-code score**, the **top 3 rules violated**, the **five
most-edited files**. These are the patient's chart, not an opinion — nobody can argue with a number
their own repo produced, which is why the session starts here instead of with definitions.

Then one sentence, and stop selling: *"every hour we spend making this readable is an hour we do not
spend re-reading it; the question is which side of that trade we are on."*

## 2. Four properties (5 minutes each, always with a review question attached)

| Property | An operational definition | The question that proves it in review |
|---|---|---|
| **Readable** | someone else follows the main flow in under 10 minutes without hopping files | "this part needs a comment to be understood — is the code wrong, or the reader?" |
| **Maintainable** | changing one business rule touches 1–2 places | "grep the free-shipping threshold: how many files?" |
| **Extensible** | a new variant means adding code, not editing old code (OCP) | "how many `if`s must change to add a fourth fee kind?" |
| **Testable** | pure logic separated from I/O; a module's unit lane runs in seconds | "can you test this function without a DB mock?" |

The point of the whole session: **these four have one root** — code communicates clearly to a reader
and lowers the cost of change. It is not aesthetics, and it is not "nice code".

An exercise that makes it land: before any definition, ask the room "what does *readable* mean here?"
— answers will differ (short lines? comments? small functions?). That disagreement is the reason this
pack fixes meanings in one place instead of leaving them to taste.

## 3. Why dirty code is slow — mechanism, not morality

1. Reading 300 lines with five shared mutable variables costs ~40 minutes and produces fear → people
   patch from the outside → every patch adds a layer of debt.
2. No tests → nobody dares to refactor → only stacking is allowed → the module grows monotonically.
3. Every abstraction without a reason is a **reading tax**: everyone pays it, forever; only the author
   benefited once.
4. A PR full of format noise sits in review for days → merge conflict → it is rewritten twice.
5. Knowledge leaves the building: the person who understood `pricing` moved to another product, and
   their understanding was never written into a name or a policy object.

Say #5 slowly in a room of seniors. It is the one that lands.

## 4. Exercise — 15 minutes, in pairs

Pick one file from the top-5 hotspot list. In 15 minutes:
- [ ] rename three variables/functions that forced you to open the body to understand them
- [ ] split exactly one function over 40 lines into two, with no behaviour change
- [ ] run the tests, then `cc-scan` on that file; write down the before/after score

Each pair presents for 60 seconds. If the score did not go up, discuss why — usually you relocated
knowledge instead of reducing it: the number of lines needed to understand one flow must fall.

## 5. The four metrics the team will actually track

| Metric | Source | Starting threshold |
|---|---|---|
| score of the hottest module | `cc-scan --json` | rises month over month |
| new `error` findings per PR | CI | 0 |
| coverage on **new** code | `diff-cover` | ≥ 80% |
| PR open → merged time | `gh pr list` | < 1 day |

Write them into `CONTRIBUTING.md` with a **name** next to each one. A metric without an owner and a
cadence is decoration, and the team can tell — which is how the next initiative dies.

## 6. Talking to the PM (5-minute role-play)

Script: see `../skills/clean-code/references/01-why-clean-code.md`. Three principles: anchor to a
**cost already paid** ("this change took 5 days; the next one took 11"), name the **mechanism**
(duplicated logic, no tests), and ask for **one small bounded package** ("two days this sprint; in
exchange the same change costs us four days less per quarter"). Never offer "a refactor sprint" — it
has no scope and no measurable exit, and it will be declined.

Pair up and deliver it in 60 seconds while the other plays a PM squeezed by a committed release date.
The exercise is uncomfortable on purpose; the real conversation is worse.

## 7. Three misunderstandings to kill today

- "Clean code = more abstraction layers plus design patterns." No: clear communication and a low cost
  of change. Patterns are targeted medicine, and this pack deliberately lets KISS and YAGNI veto an
  abstraction that has no second variant.
- "We're on a deadline, so we have to write it dirty." Dirty does not make you faster, it **borrows**
  speed: a bit less this week, much more three weeks later, and the interest is charged to whoever
  touches the file next — often the same person.
- "The AI writes the code now, so standards do not matter." The opposite: models produce the average of
  their training distribution, quickly. Without a standard, tests and review you receive debt at an
  unprecedented rate. `clean-code-review` and the two scanners exist precisely for this.

## 8. Homework (one, submitted as a PR)

1. Propose one new rule for `clean-code.config.json`, with the current counts attached.
2. Refactor one function of 70+ lines in your module, tests unchanged, PR body per
   `../skills/clean-code/templates/refactor-plan.md` §0 (the "why now" table).
3. Write one ADR titled "why we did **not** abstract X", using `../skills/clean-code/templates/adr-template.md` — the
   rejected-option table is the point.

## 9. Closing oral check

1. Why is "testable" the *cause* of clean code rather than a result of it?
2. The score went up but the number of files you must read to understand one flow did not fall — what
   does that tell you?
3. Which is worse: a 900-line refactor PR, or a 30-line PR that leaves the debt unrecorded?

**Policy line this session adds to `CONTRIBUTING.md`:** *"Quality metrics for this repo are the four
listed above; they are posted weekly; a metric that does not move for two quarters is discussed at the
retro, not quietly dropped."*

Materials: `../skills/clean-code/references/01-why-clean-code.md` · `../tools/README.md`
