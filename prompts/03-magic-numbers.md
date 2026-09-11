# 03 · Magic numbers & strings → named constants

```text
PROMPT
───
Task: remove the magic numbers and strings from the code I paste, under these rules:

1. For EVERY literal, classify before changing anything and print the table:
   | line | literal | kind | action |
   kind ∈ {business threshold, rate/unit, state/type, index/arithmetic, format,
   config default, test-only value}
2. DO NOT change: indices, 0/1 in arithmetic, numbers inside tests (where they are the
   expectation), values already on an UPPER_SNAKE declaration line.
3. Business thresholds → name them `SCOPE + MEANING + UNIT`, e.g.
   `FREE_SHIPPING_THRESHOLD_MINOR_VND`. Put the constant at the top of the module (or in a shared
   constants file), and **tell me which module it should live in** → one line of reasoning.
4. Rates/units → state the source (spec/ADR/ticket) as a comment `// per …`; if I did not give you
   a source → ASK, do not invent the comment.
5. States/types → enum or union; list the other places in the repo (that I pasted) using the same
   string, so it can be changed once.
6. Config defaults → lift to a parameter keeping the default, and name the callers that should
   pass it explicitly.
7. If two places use the SAME number for TWO different reasons → do NOT merge them into one
   constant, and explain why (false DRY).

Output: the classification table → a diff per group → the boundary tests you suggest (threshold
−1 / = / +1) → the list of literals you CHOSE not to change, with reasons.

Language: [TS | Python | Java | Go]  ·  I DO/DO NOT want a separate constants file.
CODE:
[PASTE THE CODE]
───
```

## Example (abridged)

```text
| line | literal | kind               | action |
|  12  | 500000  | business threshold | const FREE_SHIPPING_THRESHOLD_VND = 500_000 — but is this
|      |         |                    | VND or minor units? ASK before naming it *_MINOR_VND |
|  14  | 0.1     | rate               | const VAT_RATE = 0.1  // source not supplied → I ASK |
|  21  | "paid"  | state              | enum OrderStatus.Paid — also at orders.dto.ts:8, report.ts:44 |
|  33  | 1500    | config default     | param `timeoutMs = DEFAULT_TAX_TIMEOUT_MS`; the job caller
|      |         |                    | should pass it explicitly |
|  40  | 0       | index/arithmetic   | LEAVE AS IS |
|  47  | 2       | test expectation   | LEAVE AS IS (inside a test, it is the expectation) |
```

```py
# ❌ if total > 500000: free = True
# ✅ (the unit is in the name and in the type)
FREE_SHIPPING_THRESHOLD_VND = 500_000

def shipping_fee_for(subtotal_vnd: int) -> int:
    """Free shipping from the threshold up (threshold INCLUSIVE — spec §4.2, ADR-0007)."""
    return 0 if subtotal_vnd >= FREE_SHIPPING_THRESHOLD_VND else FLAT_SHIPPING_VND
```

## Minimum input

- the code **with its line numbers intact** — the table's first column is useless otherwise;
- the **unit** of any money/time/size literal you already know (VND or minor units, ms or s). This
  is the single most common source of a wrong constant name;
- **every place a state string appears**, if you want rule 5 to be worth anything — paste the
  `rg -n '"paid"' src` output alongside the code;
- whether a constants file already exists, and where.

## Output acceptance criteria

- [ ] the table covers **every** literal in the pasted code, including the ones left alone;
- [ ] each kept literal has a reason, not just "fine";
- [ ] every new name contains a scope, a meaning and (for quantities) a unit;
- [ ] no comment states a source you did not supply — an invented `// per Decree 2026` is worse
      than no comment;
- [ ] boundary tests are proposed at −1 / = / +1 of each threshold, and the test says whether the
      threshold is inclusive;
- [ ] identical values used for different reasons stayed as separate constants.

## Keeping it from inventing symbols

```text
Rules on evidence:
- List only literals that appear in the pasted code, each with the line number and the full line
  quoted. Do not extrapolate to literals "probably elsewhere in the codebase".
- Never write a source comment (spec section, ADR number, decree, ticket) unless I gave you that
  source verbatim. If the source is unknown, write `// source: UNKNOWN — ask` and list it under
  "Questions".
- For rule 5, cite only occurrences present in what I pasted. Other call sites go under
  "Run this to find the rest: rg -n '<literal>' src".
- End with: "Literals classified: N (all quoted from the paste). Source comments invented: 0."
```

## Machine check (always run afterwards)

```bash
python3 ../tools/cc-scan.py <file> --json | jq '[.findings[] | select(.rule=="MAGIC_NUMBER")] | length'
npx eslint . --rule '{"no-magic-numbers":["warn",{"ignore":[0,1,-1,2],"ignoreDefaultValues":true}]}'  # if the team enables it
rg -n "\"paid\"|'paid'" src          # a state string should have 0 hits outside the enum/mapping
```

## Tips

- The incantation for when the model merges two constants into one: **"if one changes, must the
  other change too?"** If not → two constants, however equal they look today.
- For numbers **inside SQL or a query builder**, do not hoist them into a constant if it makes the
  query harder to read; bind the threshold instead (`WHERE :threshold`) — ask the model for both
  options.

Related: `../skills/clean-code-naming/SKILL.md` · `01-name-finder.md` · `00-code-reviewer.md`
