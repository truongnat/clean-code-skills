# 10 · PR description writer — so the reviewer never has to guess

```text
PROMPT
───
From my diff and my messy notes, write the PR description in the 6-block shape. Constraints:
- Do NOT invent anything that is not in the diff; where information is missing leave
  `[NEEDS INPUT: …]`.
- Separate "refactor" from "behaviour change" — if the diff contains both, warn me to split the PR.
- Under 200 words total so a reviewer reads it in 60 seconds; write the risks plainly, do not
  soften them.

The shape:
## Why (1–3 lines: the business problem, the ticket, the motivation)
## What (bullets, by file/module; each bullet = the change + why it is there)
## What does not change (so the reviewer can stop worrying: API, schema, other behaviour)
## Risk & mitigation (flag? migration? data? feature off in prod?)
## Evidence (the commands you ran + results: tests, coverage-diff, cc-scan before/after, benchmark
   numbers, a screenshot if it is UI)
## Read this first (the 2–3 most important files/lines, with the question I want challenged)

If the diff contains a bulk reformat → name the separate formatting commit and mention
`.git-blame-ignore-revs`.
If the diff is a pure refactor → first line:
`REFACTOR ONLY — no behaviour change (tests green, git diff -w empty)`.

DIFF / STAT:
[PASTE `git diff --stat` + the diff (or a summary of the commits)]
MY NOTES: [messy is fine]
───
```

## Sample output

```md
## Why
AC-1234: the VAT formula was copied in 3 places → 2 incorrect invoices (INC-118). Consolidated into
`PricingPolicy`.

## What
- `src/domain/pricing/policy.ts` — VAT rate read from config, no longer hard-coded
- `checkout.ts`, `invoice.ts` — call the policy instead of computing by hand
- 6 boundary tests (499_999 / 500_000 / 0 / empty)

## What does not change
The `/v2/orders` API, the schema, the invoice format sent to customers.

## Risk & mitigation
Orders of 300–500k change their shipping fee → flag `pricing.free_ship_500k` (off in prod),
shadow-diff over 1000 staging orders: 0 differences (except 12 orders under KNOWN-BUG AC-1240).

## Evidence
`pnpm test` ✅ 214 · billing coverage 91% → 94% · `cc-scan` 74 → 88 (0 errors) · log requestId `cc-8842`

## Read this first
1. `policy.ts:30-58` — is any fee type missing?
2. `invoice.ts:112` — I changed `>` to `>=` to match the threshold definition; does that look right?
```

## Minimum input

- the **actual diff**, or at minimum `git diff --stat` plus the diff of the files that carry logic.
  From a stat alone the model can only paraphrase file names;
- the **ticket id and the reason** — the "Why" block cannot be derived from code, and a PR
  description with an invented motivation is worse than none;
- the **commands you ran and their output**. The Evidence block is the one block a reviewer trusts,
  and it must be transcribed, never generated;
- whether anything is **behind a flag** or needs a migration.

## Output acceptance criteria

- [ ] every bullet in "What" maps to a file that appears in the diff;
- [ ] "What does not change" is not empty — if the model cannot name one thing, it did not read
      the diff;
- [ ] every number in Evidence is one you actually ran. Any figure you do not recognise is an
      invention: delete it;
- [ ] risks are stated without softening, and a behaviour change is never filed under "refactor";
- [ ] missing information appears as `[NEEDS INPUT: …]` rather than being smoothed over;
- [ ] under 200 words, and the "Read this first" block asks a real question.

## Keeping it from inventing symbols

```text
Rules on evidence:
- Mention only files, functions and lines that appear in the diff I pasted. For each bullet, be
  ready to point at the hunk it came from.
- Never fabricate a number: test counts, coverage percentages, scores, benchmark figures,
  shadow-diff results. Use only what I pasted; otherwise write `[NEEDS INPUT: test output]`.
- Never invent a ticket id, an incident id, an ADR or a flag name. If the Why block has no ticket,
  write `[NEEDS INPUT: ticket]`.
- Do not claim "no behaviour change" unless the diff shows only renames, extractions and moves.
  If any condition, default, return value or ordering changed, say so under Risk.
- End with: "Numbers quoted from my input: N. Placeholders left for me to fill: M."
```

## Tips

- For a PR of 300 lines or more, add a closing line: `This PR has 3 commits — review commit by
  commit, do not read them merged.`
- Put the `../tools/cc-scan.py --json` output into the Evidence block: reviewers trust numbers more
  than prose.

## Verification

```bash
git diff --stat                                   # every bullet in "What" has a file here
git diff -w --stat                                # empty on a pure-refactor PR
python3 tools/cc-scan.py <changed files> --no-baseline
```

Related: `../skills/clean-code/templates/pr-review-comment.md` ·
`../skills/clean-code/checklists/self-review.md` · `00-code-reviewer.md`
