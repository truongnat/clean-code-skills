# 12 · Boundary designer — cut the seams where they will hold

```text
PROMPT
───
Help me draw module/feature boundaries for this codebase. Your output is a PROPOSAL with
evidence, not a diagram for its own sake. I will implement it as folders + enforced imports.

Evidence I give you: folder tree, `git log` coupling (provided below), the file list, and the
current import graph. Base every boundary on change coupling and data ownership, NOT on the
nouns in the domain model. If my data is not enough to decide, say which command you need run.

Deliver, in order:

1. **Candidate boundaries** — 3 to 7, each with: name, the concepts inside, the data it owns,
   and the "one sentence of responsibility" a new engineer could repeat correctly.
2. **Why each cut holds** — for every boundary, cite the evidence: which files change together,
   which change alone, which data it owns exclusively.
3. **What must NOT be a boundary** — pairs of folders people often split that would need to
   transact together on every write. Say so explicitly; a wrong boundary costs more than none.
4. **Contracts** — for every pair that must talk: synchronous call or event? If event, name it,
   list the payload fields, and state who is allowed to add a field and how consumers tolerate
   the old shape for one release.
5. **Shared parts** — for each piece two boundaries want: publish in the owner's API / move into
   a kernel with an owner / duplicate deliberately. One line of cost each, then pick.
6. **Enforcement** — paste-ready config: `arch-scan.config.json` layer+boundary entries, and the
   language-native rules (dependency-cruiser / import-linter / ArchUnit) expressing the same
   contract. The two must not disagree; if they can, say which one wins (the exact tool).
7. **Migration in ≤ 4 PRs** — no big-bang. Each PR must keep CI green and be reversible.
8. **Failure report** — how this design usually rots in 6 months, and the metric that shows it
   starting (e.g. a file that appears in >40% of commits, >1 new edge per month, "shared" growing).

Constraints:
- never propose a separate deployable as the answer to an internal coupling problem;
- never create more than 7 top-level boundaries for a team under 15 people;
- every "shared" module needs a named owner or it becomes a dumping ground — say so;
- if the honest answer is "one module, no boundaries yet", answer that.

TEAM CONTEXT: [domain, team size, deploy cadence, DB topology, what is frozen]
EVIDENCE: [tree, git coupling output below, import graph, recent PR titles]

COUPLING DATA (run these and paste the output):
  git log --since='90 days ago' --name-only --pretty=format: -- src | sort | uniq -c | sort -rn | head -20
  python3 tools/arch-scan.py src --json -o arch.json && cat arch.json
───
```

## Notes

- The most useful thing this prompt produces is item 3 — the cuts you explicitly reject. Those are
  the arguments that end boundary debates in review.
- Item 6 is why the output is worth pasting into the repo: a boundary nobody can check is a folder
  rename with extra steps.

## Minimum input

- the **change-coupling output**. The prompt gives you the exact `git log` command; without it every
  boundary in the answer is drawn from domain nouns, which is the failure this prompt exists to
  avoid;
- **who owns which data** today — which module writes which tables. Boundaries follow write
  ownership before anything else;
- **team size and count**, because rule 2 caps the number of boundaries by it;
- **what is frozen**: deployed services, published events, the DB topology (one database or
  several).

## Output acceptance criteria

- [ ] every boundary cites the coupling evidence for it, naming files that appear in your `git log`
      output;
- [ ] item 3 is non-empty — the rejected cuts are the most useful part of the answer;
- [ ] every cross-boundary pair has a named contract, and each event lists its payload fields and
      its compatibility rule;
- [ ] every shared piece has a decision *and* a named owner, or it is deliberately duplicated;
- [ ] item 6's config is pasteable and the two enforcement tools agree, with a stated tie-breaker;
- [ ] the migration is at most 4 PRs, each keeping CI green;
- [ ] if your numbers are small, "one module, no boundaries yet" is an acceptable answer and the
      model should be willing to give it.

## Keeping it from inventing symbols

```text
Rules on evidence:
- Cite only files, folders and modules that appear in the tree, the import graph or the coupling
  output I pasted. Quote the evidence line under each boundary.
- Do not claim two files change together unless they appear together in the coupling data I gave
  you. If you need more data, name the exact command to run.
- Event names, payload fields and table names must come from my input; anything you propose is
  marked NEW.
- Config snippets may only use keys that exist in arch-scan / dependency-cruiser / import-linter.
  If unsure, say so rather than inventing an option.
- End with: "Boundaries supported by coupling evidence: N/M. Assumptions: list them."
```

## Verification

```bash
python3 tools/arch-scan.py src --fail-on error     # the proposal is now a gate
python3 tools/cc-scan.py src --fail-on error       # module quality, unchanged by this work
```

Related: `11-architecture-review.md` · `../skills/clean-code/references/12-clean-architecture.md` §3
