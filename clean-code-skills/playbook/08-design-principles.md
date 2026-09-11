# Session 8 · SOLID · DRY · KISS · YAGNI — principles as cost prediction

**Duration:** 60 minutes · **Pre-work:** each person brings one abstraction they are unsure was worth
it. **Output:** one ADR titled "why we did **not** abstract here" — the unusual direction is the point.

## 1. How to run this session (unlike the slides you have seen)

Do not ask "is this SRP?". Ask:

> **To change X, how many files must I edit?**

| Question | Good answer | Bad answer |
|---|---|---|
| add a new fee kind | one row in a table | edit five `if`s in three files |
| change the customer email layout | one template | four `send(...)` call sites |
| drop the DB from a unit test | the domain imports no DB | `new PrismaClient()` inside the domain |
| change the free-shipping threshold | one policy + one test | `rg` returns seven hits |

Those four questions are S, O, D and DRY in working clothing, with no acronyms — and every answer is a
number someone in the room can verify in 30 seconds, which is why it persuades where "the principles
say" does not.

## 2. Five principles: the violation signal (greppable) and the medicine

| Principle | Violation signal | Medicine | When **not** to take it |
|---|---|---|---|
| **S**RP | a class name with ≥ 3 big verbs (`create + send + calculate`) | `Extract Class` by **reason for change** | a 60-line class doing two tightly-coupled things |
| **O**CP | `switch (kind)` in ≥ 3 places | a table, polymorphism, or a sealed union | only one variant exists → an `if` beats four files |
| **L**SP | a child overriding to `throw Unsupported…`, or `isinstance` in the parent | fix the contract, or use composition | inheriting only to "steal code" (`extends BaseService`) |
| **I**SP | three implementers carrying `UnsupportedOperationException` | split interfaces by capability | one-method interfaces per client: fragmentation, not segregation |
| **D**IP | the domain imports `axios` / `prisma` / `requests` | port in the domain, adapter in infra, wired in the composition root | interface-ifying everything → 40 files, one implementation |

Say the limits of this table out loud: **only the DIP row has a machine gate** (`arch-scan`
`DOMAIN_FRAMEWORK_IMPORT`, `UPWARD_DEPENDENCY`), and OCP shows up indirectly through
`COMPLEXITY`/`HARD_COMPLEXITY`. SRP, LSP and ISP are review habits — which is why the DoD and the
checklist, not the config, are where they survive.

## 3. DRY — knowledge duplication versus accidental similarity

```py
# KNOWLEDGE (merge it): the VAT formula in a service + a stored procedure + the frontend
# ACCIDENTAL (leave it): the UI label and the audit line both use f"{first} {last}"
```

Exercise: take two similar blocks from the team's repo and let the room vote — **knowledge or
coincidence?** — with a spoken reason. Then run the tool and compare instinct with data:

```bash
python3 ../tools/cc-scan.py . --json | jq '[.findings[] | select(.rule=="DUPLICATE_BLOCK")]'
```

The scanner is a suggestion engine here; the decision is human, and **merging wrongly costs more than
failing to merge**: two copies can drift and be caught by a test, while one shared thing with two
owners becomes a hostage situation. Say that in every session; it is the sentence that prevents the
worst clean-code reflex.

## 4. KISS — the "least exciting thing that works" exercise

Rewrite `PricingEngine` (assume it currently uses five design patterns) into **one dict of functions
plus one loop**, keeping the tests green. Then answer three questions:

- how much faster is it to read? (time it, once, honestly)
- debugging a wrong amount: six files open before, how many now?
- what did you lose? (the "extend without editing" property) — and **does anyone actually need it?**

The last question is where the room splits, and the split is the lesson: record the answer as one line
in the ADR, because the next person will "improve" it back into patterns otherwise.

## 5. YAGNI — both edges of the blade

```text
❌ Writing a factory/provider/strategy for ONE implementation - the abstraction rents space.
❌ Deleting an abstraction at a REAL boundary (a public API, a DB schema, a published event) -
   the cost of changing it later is external and permanent. Investing here is correct.
```

The three-question cut:
1. does a **second real variant** exist? (no → not yet)
2. if we do not split now, how long is the refactor later? (> 1 day, with outside callers → split)
3. does the abstraction have a **business name**? (no → it is indirection, not a concept)

## 6. Twenty minutes on the real repo (each person picks one)

1. find a `switch`/`if type` repeated in ≥ 2 places → propose a table-driven version, **write the test
   first**;
2. find a class whose name holds three verbs → sketch the two classes and their names (do not code);
3. find an interface with exactly one implementation **and** no test fake → propose `inline` it, and
   note what would bring the second implementation;
4. find one copied formula → merge it to a policy and write the one-paragraph ADR;
5. run the gates on the file before and after and put both numbers in the PR:
   `python3 ../tools/cc-scan.py <file> --json | jq .score`.

## 7. Lightning round (5 minutes, ends the session)

Read five snippets aloud; the room shouts the principle and the medicine. Deliberately include one
where the right answer is "no change needed" — the most expensive error in this chapter is a
refactoring nobody asked for.

## 8. Closing check

1. OCP says "closed for modification" — does fixing a bug in `PricingPolicy` violate it? (no: "closed"
   means a new *feature* must not force edits in old code, not "hands off")
2. When is 100 duplicated lines acceptable? (a hot path needing the extra loop, two places that change
   for two reasons, generated code) — and where must that be written? (an ADR plus one comment line,
   so the next reader does not "helpfully" merge them)
3. Why does "a service per anything" break KISS instead of serving SRP? (SRP is about reasons for
   change, not about file count; a reason-less split adds a hop and a name to learn)

**Policy line for `CONTRIBUTING.md`:** *"An abstraction needs a second real variant, a boundary that
is expensive to change, or an ADR. Reviewers ask 'how many files to change X?' before proposing a
split; a proposal that cannot answer it is a nit, not a blocker."*

**If you only have 15 minutes:** do exercise 3 (an interface with one implementation and no fake) and
delete one of them. Removal is the refactoring that most often makes the codebase better, and it is
the one nobody schedules.

Materials: `../skills/clean-code/references/08-design-principles.md` · `../skills/clean-code/templates/adr-template.md`
