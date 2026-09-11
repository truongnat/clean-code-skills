# 08 · Legacy refactor plan — multi-step, safe, with a stopping point

```text
PROMPT
───
Write a refactor PLAN for the legacy module I describe. Do NOT write the full code. Each step is
at most one PR.

What I give you: [module description · line count · who uses it · tests or not · change frequency ·
related incidents]

Mandatory format:

## 0. Is it worth doing?
Give 3 pieces of evidence for / against refactoring **now** (hotspot: changed often × breaks
often; blocking a feature; caused an incident). If the evidence is weak → recommend "only fix it
when you touch it" and stop here.

## 1. Safety net (do this FIRST, it is always step 1)
characterization tests / a snapshot of real input, a feature flag, shadow-diff, a comparison
metric, `cc-scan --update-baseline` for that module.

## 2. The steps (table)
| # | step | refactor | size (XS/S/M/L) | risk | rollback | how we prove behaviour did not change |
Rules: step 1 is always a **rename/extract with no behaviour change**; behaviour changes go in the
last step, behind the flag. No step is larger than 400 lines.

## 3. Definition of done (measurable)
Thresholds: functions ≤ 40 lines, ≤ 3 parameters, 0 EMPTY_CATCH, 0 magic values in the domain,
coverage ≥ 80%, 0 files over 400 lines. Include the command to run for each (cc-scan/eslint/ruff/jest).

## 4. Where to stop
Two stopping conditions (the target is met / one step costs more than it returns) and what you are
**deliberately not doing** this round, to stop the scope drifting.

## 5. What I must decide before starting
3–5 questions for the most senior person on the team (may the API change? does this touch the DB
schema? who owns the business logic?). No answer → say which step is blocked.
───
```

## Minimum input

- **change frequency and incident history**, in numbers. Section 0 is the whole value of this
  prompt and it cannot be answered from source code alone:
  `git log --since='12 months ago' --format= --name-only -- <module> | sort | uniq -c | sort -rn | head`;
- **whether tests exist** and what they cover — this decides how large step 1 is;
- **who calls the module** (internal only, another team, a published API), because that sets the
  ceiling on every step;
- the **feature currently blocked** by this code, if any. "Refactor because it is ugly" and
  "refactor because the next feature cannot land" produce different plans, and only the second one
  gets scheduled.

## Output acceptance criteria

- [ ] section 0 argues both ways and is willing to conclude "not now";
- [ ] step 1 is the safety net, and the first code step changes no behaviour;
- [ ] every step has a rollback that is not "revert the merge commit and hope";
- [ ] every step has a *proof* column with a runnable command, not "review carefully";
- [ ] no step exceeds 400 lines, and the plan is at most ~6 steps. A 15-step plan is a rewrite
      wearing a costume;
- [ ] section 4 names something explicitly out of scope;
- [ ] section 5's questions are answerable by a person, not by reading the code.

## Keeping it from inventing symbols

```text
Rules on evidence:
- Base section 0 only on the numbers I gave you. Do not estimate a change frequency, a bug count
  or an incident you were not told about; write "UNKNOWN — I need: <the exact git command>".
- Name files and functions only as I named them. If a step needs a file whose existence you are
  assuming, write it as `<new file>` and mark it NEW.
- Do not cite a refactoring technique's name unless the step really is that technique, and do not
  invent a tool flag — every command in the plan must be one I can paste
  (`cc-scan`, `eslint`, `ruff`, `pytest`, `go test`) with flags that exist.
- Do not promise a coverage or score number as an outcome; state it as a target to be measured.
- End with: "Facts taken from my input: N. Assumptions I made: list them."
```

## Tips

- Paste `python3 ../tools/cc-scan.py <module> --json` alongside (top rules + score). With no data
  the model draws a beautiful architecture diagram for a module that is about to be deleted.
- If the model makes "rewrite it all" step 1, push back:
  `"No big-bang rewrite. Find a way to the same destination with expand–contract, 6 steps maximum."`
- Once the plan is approved, use `../skills/clean-code/templates/refactor-plan.md` to turn it into a
  real document in the repo and open a ticket per step.

## Verification

```bash
python3 tools/cc-scan.py <module> --no-baseline   # the definition-of-done thresholds, per step
git diff --stat                                    # no step drifted past 400 lines
```

Related: `../skills/clean-code-refactoring/SKILL.md` ·
`../skills/clean-code/templates/refactor-plan.md` · `02-extract-function.md`
