# 11 · Architecture review — is the shape defensible?

```text
PROMPT
───
You are reviewing the STRUCTURE of this codebase, not its style. Do not comment on naming,
line length or formatting; another tool already does that. Diagnose + propose the smallest
reversible change. Do not rewrite code in the answer.

Input you get: the folder tree, the import graph (or enough files to infer it), and the
team's constraints. If a piece of input is missing, ASK once, then state your assumption.

Report in exactly this order:

1. **Layer census** — which folders correspond to domain / application / infrastructure /
   interface (rank 0..3)? Files that fit none: list them and say what that implies.
2. **Dependency rule violations** — every edge that points outward
   (inner importing outer). For each: file:line, the two layers, and the fix as
   "declare port X in <inner layer>, move implementation into <outer layer>" — never
   "move the code to the outer layer" unless the rule genuinely belongs there.
3. **Cycles** — any ring between layers or packages. For each, name which single edge to
   cut and how (invert with a port, or publish an event).
4. **Boundary leaks** — feature A importing feature B's internals. Classify the shared
   piece: (a) publish it in B's public API, (b) move it to a kernel with a named owner,
   (c) duplicate it on purpose because it only *looks* shared. Pick one and give the cost.
5. **Framework reach** — where do ORM/HTTP/queue types appear outside infrastructure/
   interface? Count the files that would need to change if the framework were replaced.
6. **Placement errors** — business rules sitting at the edge (controllers computing money,
   cron jobs holding invariants) or infrastructure logic in the domain.
7. **Testability verdict** — can one use case be tested with no DB/network/container?
   Answer yes/no and name the first blocker file.

Constraints for every recommendation:
- tag size: XS (1 import moved) · S (1 file created) · M (1 module reorganised) ·
  L (needs an ADR) ;
- never propose a new layer, a new framework, or a service split without writing the cost
  and the trigger that would justify it;
- prefer making the current structure *legal* over making it *ideal*;
- if the architecture is fine and the problem is only module-level quality, say so and stop.

Finish with: "3 changes to make this quarter (XS/S, on the path we already walk)" and
"what I am NOT recommending and why".

TEAM CONTEXT: [domain · which module changes most · deployed services · public APIs frozen ·
what we are allowed to break]
EVIDENCE: [tree, arch-scan output, madge/import-linter output, key files]
───
```

## Tips

Feed it real data — the model is much less likely to invent abstractions when the import graph is
in the prompt:

```bash
python3 tools/arch-scan.py src                       # paste the census + matrix
python3 tools/arch-scan.py src --json -o arch.json   # and attach the findings list
npx madge --circular src                              # JS/TS
lint-imports                                          # Python
```

If the answer is "adopt clean architecture from scratch", push back with one question: *"which of
these violations can we make red in CI this week?"* A review that ends without an enforceable check
was a lecture.

## Minimum input

- the **folder tree** and the **import graph** — the prompt's own `Input you get:` line says this,
  and every one of the seven report sections is derived from it. `arch-scan --json` is the cheapest
  way to supply both;
- which **layer each top-level folder is meant to be**, if your names are not the conventional
  ones. Otherwise section 1 spends its effort guessing your intent;
- **what is frozen** (a published API, a deployed service boundary, a schema), which is the ceiling
  on every recommendation;
- the module that **changes most often** — an architecture review that does not know where the
  change pressure is will rank its findings by aesthetics.

## Output acceptance criteria

- [ ] all 7 sections present, each one answered even when the answer is "no violations";
- [ ] every violation cites `file:line` from the data you pasted;
- [ ] each dependency-rule fix is phrased as "declare port X inward, implement it outward", not
      "move the code";
- [ ] every recommendation has an XS/S/M/L tag, and no new layer or service appears without a cost
      and a trigger;
- [ ] section 7 gives a yes/no and names the first blocking file;
- [ ] the closing list has 3 items, all XS or S, plus an explicit "what I am not recommending".

## Keeping it from inventing symbols

```text
Rules on evidence:
- Every edge, cycle and leak you report must be traceable to a line in the tree, the import graph
  or the arch-scan output I pasted. Quote it.
- Do not infer an import you cannot see. If a verdict depends on a file I did not provide, list it
  under "Files I need to confirm this" and stop at the hypothesis.
- Do not invent folder names, module names or port names as if they existed; mark anything new NEW.
- Do not quote a score, a file count or a percentage you did not compute from my data.
- End with: "Findings traceable to pasted evidence: N. Findings needing data I do not have: M."
```

## Verification after applying the advice

```bash
python3 tools/arch-scan.py src --fail-on error            # edges now legal
python3 -m pytest tests/unit -q                           # domain tests without a DB container
npx vitest run src/application 2>/dev/null || true
```

Related: `../skills/clean-code/references/12-clean-architecture.md` ·
`../skills/clean-architecture/SKILL.md` · `13-pattern-picker.md`
