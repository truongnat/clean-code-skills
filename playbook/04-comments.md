# Session 4 · Comments — code explains *what*, comments explain *why*

**Duration:** 30 minutes (the shortest session that changes review behaviour the most) ·
**Pre-work:** each person pastes three comments from their own module into the meeting doc.
**Output:** two CI rules (`COMMENTED_CODE`, and "a TODO must carry a ticket") plus a comment budget.

## 1. Team standard

```text
ALLOWED / ENCOURAGED
  • why, constraints, trade-offs, a link to the ADR or ticket
  • warnings about consequences ("the order of these lines matters", "do not change this
    function - three batch jobs depend on its side effect")
  • TODO(<ticket>, <owner>): what is missing and when it comes out
  • docstrings / JSDoc for public APIs - that is a CONTRACT (@param, @throws), not a comment

FORBIDDEN
  • narrating the code (`// loop over items`)
  • commented-out old code (`// old impl`) - Git keeps it, you do not have to
  • restating a signature (`@param id id`)
  • ASCII divider banners (`//===== TAX =====//`) - replace with a file or function split
  • apology comments (`// temporary hack`) - fix it, ticket it, or say nothing
```

## 2. Three cures, practised for 15 minutes

```py
# (1) a comment explaining the code  ->  rename the function
# ❌ if u.a > 18 and not u.b: ...        # old enough and has not voted yet
✅ if voter.can_receive_ballot(): ...

# (2) "why is the comparison <=" ->  keep it, but state the CONSTRAINT and the SOURCE
✅ # the threshold is inclusive (business definition, ADR-0007): an order of exactly 500k ships free
if subtotal >= FREE_SHIPPING_THRESHOLD_MINOR_VND: ...

# (3) an 8-line block comment describing the algorithm -> 2 lines + a link
# ✅ stock is balanced FIFO; the derivation and edge cases live in docs/algorithms/stock-balance.md
```

Drill that makes it stick: for each of the three pre-work comments, its author says which cure applies
and the room has 20 seconds to object. Comments that survive the 20 seconds are keepers; most that
don't are narration.

## 3. Public docstring: the four-part frame (enough, never more)

```ts
/**
 * Converts an amount into the currency's minor unit so no float arithmetic is involved.
 *
 * @throws InvalidAmountError when `amount` is negative, NaN, or beyond MAX_PRECISION_DIGITS.
 * @see docs/adr/0007 - why the domain layer does not use Decimal
 */
```

Enough: **one sentence of job** + **failure modes** + **the constraint a caller could break**. Never
restate parameter names as their own description, and never put algorithm derivation here (that is a
docs page). Per language: TSDoc/JSDoc for TS, Javadoc for Java, Google-style or reStructuredText for
Python (pick one and hold it in config), and Go's idiom where the comment begins with the name.

## 4. Why commented-out code is a hard rule (risk, not taste)

It is **dead code that looks alive**: the reader cannot tell whether it is still correct, whether
something else depends on it, or whether it should be updated too. Every such line adds about a minute
of doubt per read; a few hundred of them are hours a week for the team, spent on questions nobody will
ever answer. `git log` is where deleted code belongs.

The same argument covers `// temporary`: it hands the cost to the next person and leaves no trace to act
on. A ticket does both.

## 5. Machine-ify the easy half (do not spend humans on it)

| Tool | Rule | Catches |
|---|---|---|
| `cc-scan` | `COMMENTED_CODE`, `TODO_MARK`, `BLOCK_COMMENT` | dead code, TODOs, long block comments |
| ESLint | `no-warning-comments` | `// TODO`, `// FIXME` |
| ruff | `ERA001` (commented-out code), `FIX002` (TODO) | as above |
| Checkstyle | `TodoComment` | TODO/FIXME — our own `tools/check_links.py` reports one when the marker sits on code |
| CI | a `TODO` without `\b[A-Z]+-\d+\|#\d+` fails the build | debt with no owner |

```bash
# CI: every TODO must carry a ticket
rg -n "TODO" src --glob '!**/*.md' | rg -v "TODO[(: ]*([A-Z]+-[0-9]+|#[0-9]+)" && {
  echo "a TODO needs a ticket: TODO(AC-1234, owner): what"; exit 1; } || true

# what the pack's scanner sees in your module right now
python3 ../tools/cc-scan.py . --json | jq '[.findings[] | select(.rule|test("COMMENTED_CODE|TODO_MARK|BLOCK_COMMENT"))]'
```

## 6. Audit drill: the 20-minute comment sweep

One module, three buckets, counted out loud:

| Bucket | Action | Typical share |
|---|---|---|
| narration (what) | delete it, or rename the code until the comment is unnecessary | ~60% |
| the why / warning / constraint | keep; make sure it cites a ticket or an ADR | ~25% |
| stale (describes an older design) | **fix the code or the comment, never both, in this commit** | ~15% |

The number that matters is the last one: stale comments are worse than none, because they are
authoritative-looking lies. A module with more than a handful of them needs names and tests, not more
comments. The three percentages are a *starting expectation* for a first pass, not a measurement from
this pack — run §6 and count your own, then write the number in the retro notes; the value is in
counting, and an agreed target would only invite people to delete useful comments.

## 7. Closing check

1. Which comment in your code should have been code all along? (usually the one explaining a condition)
2. Which comment belongs in an ADR or README instead? (the history of an architectural choice)
3. If you deleted every comment in the file you last reviewed, would a newcomer misunderstand it? If
   yes, the fault is in the code, not in the comment count.

**Policy line for `CONTRIBUTING.md`:** *"Comments state why, never what; commented-out code does not
exist; every TODO has a ticket id and an owner; public APIs have docstrings with failure modes.
Reviewers may not ask for a comment where a rename or an extraction would do the job."*

**If you only have 15 minutes:** run §6 on one file and switch on the TODO-with-ticket check. Both are
ten-minute changes, and they are the two reviewers notice in week one.

Materials: `../skills/clean-code/references/04-comments.md`
