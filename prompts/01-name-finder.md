# 01 · Name finder — rename things to state their intent

```text
PROMPT
───
Help me RENAME things (no behaviour change, no change to a public signature).

For every identifier I paste:
1. Read the body and answer in one sentence: "what it ACTUALLY does / holds".
2. Propose 2–3 new names for [<TypeScript|Python|Java|Go>], each with:
   - why it is clearer (12 words max)
   - the risk of renaming (public API? serialised to a DB/event? reflection?)
3. Point out which names should **not** change just because I find them hard to read (when the
   name is a domain term) and tell me to add a docstring instead of renaming.
4. If no good name exists → say it plainly: "the problem is not the name", and propose the
   matching refactor (Extract Method / Move / Split Predicate).

Team conventions (mandatory):
- camelCase for variables/functions, PascalCase for types, UPPER_SNAKE for constants (TS/Java)
  · snake_case for Python and for unexported Go
- booleans: is/has/can/should + POSITIVE FORM (never isNotX)
- carry the unit: `Ms`, `MinorVnd`, `Kg`, `Bytes`
- banned empty suffixes: Manager, Util, Helper, Common, Data, Info, Object, Handler (unless it is
  a real pattern name, e.g. a framework's `RequestHandler`)
- do not repeat the class context: `Order.orderTotal` → `Order.total`

IDENTIFIERS TO RENAME:
[PASTE THE CODE]

DOMAIN CONTEXT (the business vocabulary, if you have one):
[PASTE THE GLOSSARY — e.g. "Tạm ứng = Deposit", "Lệnh bán = SalesOrder"]
───
```

## Expected output (abridged example)

```text
1) `calc` (line 3)
   Actually: totals the available line items, with VAT, minus the VIP discount.
   Candidates:
     • `invoiceTotalWithVat`  — states intent; risk: currently exported, needs expand–contract
     • `computeChargeableTotal` — states "filter + compute"; a little long
   Risk: called from `orders.ts` and 2 jobs (grep = 12 hits) → keep the old alias for one release.
2) `flag` (line 21)
   Actually: turns on the confirmation email.
   → `shouldSendConfirmation: boolean` … or split out `notifyConfirmation()` (flag argument smell).
3) `d` — no good name exists because it is a record sitting in the wrong layer;
   propose Extract `parseDraft()`.
```

## Minimum input

- the **whole file**, not the single line — a good name depends on what surrounds it;
- the **language**, because the convention table branches on it;
- the **domain glossary** if the project has one; without it the model invents English terms that
  contradict what your business people say;
- for anything exported: **how far it reaches** (paste a `grep -rn "<name>"` count). A rename with
  12 call sites and a rename with 2 are different decisions.

## Output acceptance criteria

- [ ] every candidate name contains a **business noun**, not just a verb and a type;
- [ ] every candidate carries a stated risk, including "none — this symbol is module-private";
- [ ] at least one identifier is left alone, or the model explains why all of them genuinely needed
      changing;
- [ ] no name uses a banned suffix, and no boolean is phrased negatively;
- [ ] anything serialised (DB column, event field, API key) is flagged as expand–contract, never as
      a straight rename.

## Keeping it from inventing symbols

```text
Rules on evidence:
- Rename only identifiers that appear in the code I pasted. Quote the declaring line for each one.
- Do not claim a call site you cannot see. If a rename's risk depends on callers outside this file,
  write the exact `grep`/`rg` command I should run and say the risk is unknown until I do.
- Do not invent domain terms. If the right name needs business vocabulary I have not given you,
  ask one question instead of picking a word that sounds plausible.
- End with: "Identifiers renamed: N (all present in the pasted code). Unknown-reach renames: M."
```

## Tips

- Paste the **file**, not one line — a good name depends on context.
- If the model comes back with `processInvoiceData`, paste the prompt again with the extra
  constraint: "banned words: data/info/process/handle/util, and every name must contain a
  **business noun**".
- After renaming: run `cc-scan` and the tests. Commit as `refactor: rename … (no behaviour change)`.

## Verification

```bash
rg -n "\bcalc\b|\bflag\b" src        # the old names are gone, or only the kept alias remains
python3 tools/cc-scan.py src --no-baseline
```

Related: `../skills/clean-code-naming/SKILL.md` · `03-magic-numbers.md` · `00-code-reviewer.md`
