# Clean code playbook — 12 sessions of 45 minutes, plus two appendices

> This is the **curriculum and team policy**, not the quick reference. Lookups live in
> `../skills/clean-code/references/`. The playbook exists to onboard people, to agree the standard
> *before* CI starts blocking, and to be the document a new joiner reads in their first week.

## How to use it

| Role | How |
|---|---|
| Tech lead | read 01 + 09 → set the thresholds and the ratchet plan → turn on `configs/` + CI |
| New developer | read 01 → 08, one session per week; each week submit the exercise as a **refactor-only PR** |
| Reviewer | keep `../skills/clean-code/checklists/code-review.md` open; cite the session number instead of giving an opinion |
| PM / BA | read 01 (why it is worth paying for) and the "team standard" table of each session |
| Anyone short of time | the "if you only have 15 minutes" line at the end of each session |

Each session has the same shape: **goal → team standard (the hard, checkable list) → wrong/right →
exercise → closing check → the policy line that goes into `CONTRIBUTING.md` → materials**. Items
marked 🔧 are decisions to settle **once** with the team and then never re-open; leaving them vague
is what turns a standard into an argument.

## Part I — sessions 1–9 (code level) · Part II — sessions 10–12 (system level)

| # | Session | Measurable outcome of the session |
|---|---|---|
| 1 | [What clean code means](01-what-clean-code-means.md) | the four properties agreed; four metrics chosen, each with an owner |
| 2 | [Naming](02-naming.md) | a 20–40 line domain glossary exists; zero new `Manager/Util/Data` names |
| 3 | [Functions](03-functions.md) | `max-lines-per-function` + `max-params` enabled in CI at the agreed (ratcheted) values |
| 4 | [Comments](04-comments.md) | zero commented-out code in the module you own; every TODO has a ticket |
| 5 | [Formatting](05-formatting.md) | formatter + `.editorconfig` + hooks live; style comments banned in review |
| 6 | [Objects and data structures](06-objects-and-data-structures.md) | no new `a.b().c().d` chains; invariants live in the type |
| 7 | [Error handling](07-error-handling.md) | zero `catch {}`; every wrap keeps its cause; error branches tested |
| 8 | [Design principles (SOLID/DRY/KISS/YAGNI)](08-design-principles.md) | an ADR for the last two abstraction decisions, including the rejected option |
| 9 | [Code health and workflow](09-code-health-and-workflow.md) | quality CI green with a baseline that shrinks each quarter |
| 10 | [Clean architecture](10-clean-architecture.md) | `arch-scan --fail-on error` blocks new upward edges and cycles; one ring and one leak broken and merged |
| 11 | [Architecture patterns](11-architecture-patterns.md) | one ADR with a cost table and a revisit trigger for an open decision |
| 12 | [Design patterns](12-design-patterns.md) | one flag/`switch` → policy; one dead abstraction deleted or justified by name |
| A | [Appendix A: onboarding quiz](appendix-a-onboarding-quiz.md) | 34 questions with explained answers; target >= 30/34, and a per-block map back to the session to re-run |
| B | [Appendix B: maturity model](appendix-b-maturity-model.md) | the team's current level, and the one concrete step to the next |

## Three policies to agree before session 1 (without them, the rest backfires)

1. **Who decides formatting — the machine or the human?** The machine. Prettier/Black/gofmt are the
   law, and reviewers are **not allowed** to comment on style. The reason is not purity: it frees
   roughly a third of review time for design.
2. **Does a violation block a merge?** In phase 1, only **new** violations (baseline); from the second
   quarter, per-rule blocking as announced. Never "the whole repo must be clean by Friday".
3. **How may a standard be broken?** Explicitly, narrowly and readably: `cc-scan:allow` /
   `eslint-disable-next-line` with a reason, and an ADR if the exception matters. A silent exception is
   how a standard dies — quietly, one file at a time.

## Rules for every session

- Each session ends with **one real PR**, however small, from the session's own content. Training that
  produces no PR changes nothing; the PR is the artefact that proves the team agreed.
- No more than 10 minutes of slides. Open the **team's** repo, find a hotspot, fix it together.
- Everybody takes a turn opening their own file for the room to read. A culture where code is looked
  at — and where good parts are named out loud — matters more than any rule in this pack.
- One session per week, never two in a row: the practice has to land in real PRs between them.
- If a session's exercise cannot be completed in the time given, the scope is wrong, not the team.
  Shrink the exercise (the "15 minutes" variant) and keep the policy line.

## Scheduling variants

| Situation | What to run |
|---|---|
| New team / new project | 1 → 9 in order, one per week, then 10 → 12 before the first service split |
| Legacy repo, no time | 1, 3, 7, 9 + the ratchet plan — the four that change the most money |
| After an incident | 7 (errors) + 11 (boundaries), with the incident as the case study |
| Frequent new joiners | 2 (naming + glossary) + 6 + the Appendix A quiz as a self-check |
| Preparing a split | 8, 10, 11, 12, and Appendix B to decide whether you are really ready |

Materials every session assumes: `../tools/cc-scan.py`, `../tools/arch-scan.py` (from session 10),
`../skills/clean-code/references/` for depth, and the `../configs/` you are about to install — running
the real tool on the real repo is the entire method.
