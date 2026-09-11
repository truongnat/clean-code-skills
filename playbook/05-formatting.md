# Session 5 · Formatting — the one topic that must be over after 20 minutes

**Duration:** 20 minutes (deliberately the **shortest** session: the subject does not deserve more) ·
**Output:** formatter + `.editorconfig` + hooks installed, and style comments banned in review.

## 1. Team decisions (🔧 commit them, then stop discussing them)

| Question | Playbook answer |
|---|---|
| who decides formatting? | the **formatter**, not a human: Prettier / ruff-format or Black / gofmt+gofumpt / ktlint |
| line width | JS/TS/Java/Go: **120**; Python: **88** (the toolchain default); Markdown: unlimited |
| tabs or spaces | spaces for JS/TS/Python/Java/C# (2 or 4 per language); **tabs for Go**, because gofmt |
| style comments in review? | **forbidden**. The only permitted reply is "the formatter decides" |
| where does auto-fix run? | on staged files only (husky + lint-staged, or pre-commit) + a blocking CI `--check` |
| when is `prettier-ignore` legitimate? | numeric tables and coordinate arrays, where the alignment is the meaning — with a one-line reason |
| what about files nobody can format? | generated code is excluded in the config (visible in `git log`), never with in-file comments |

## 2. Install it in one evening (do it for real, not as a demo)

```bash
# the common floor for every editor
cp ../configs/ci/.editorconfig .

# JS/TS
cp ../configs/js/.prettierrc.json ../configs/js/eslint.config.js .
npm i -D prettier eslint @eslint/js typescript-eslint husky lint-staged
npx husky init && echo 'npx lint-staged' > .husky/pre-commit

# Python
cp ../configs/python/pyproject.toml .                 # ruff + black + mypy
pipx install pre-commit && pre-commit install
cp ../configs/ci/.pre-commit-config.yaml . && cp -r ../configs/ci/hooks .

# Go
cp ../configs/go/.golangci.yml . && go install mvdan.cc/gofumpt@latest
```

```bash
# 1) format the whole repo - its OWN commit, never mixed with a feature
npx prettier --write . && npx eslint . --fix
# 2) so that git blame survives it
git rev-parse HEAD >> .git-blame-ignore-revs
git config blame.ignoreRevsFile .git-blame-ignore-revs
# 3) block regressions in CI
npx prettier --check .
```

**The format-commit ceremony** — this is what makes it a non-event: announce it 24 h ahead, ask
everyone to merge or rebase first, run it as a single commit, push, then freeze merges for 30 minutes
while open branches rebase. Skipping the announcement is how a five-minute task becomes a day of
conflicts, and a day of conflicts is how a formatter gets uninstalled.

Note the `git config` step is per-clone: tell people to run it, or `.git-blame-ignore-revs` does nothing
and someone will "fix" the file a second time.

## 3. Vertical formatting — the part no machine will ever own

A formatter cannot know **what belongs together**. That part is yours:

```ts
// ❌ related functions 200 lines apart; helpers dumped at the bottom of the file
// ✅ file docstring -> imports -> constants -> types -> public (top) -> private helpers
//    (each helper directly under the one place that calls it)
```

1. **callers and callees stay adjacent** — the file reads top-down like a document ("order-down");
2. one blank line = one step, two = one area; five blank lines to "breathe" is a lost relationship;
3. declare a variable near its first use — a 60-line lifespan is a signal to split the function;
4. a file over ~400 lines is usually two modules sharing a name: **write the two file names down before
   you split**, and if you cannot name both capabilities, do not split it yet.

## 4. Exercise — 5 minutes

```bash
npx prettier --check .            # count the failing files
python3 ../tools/cc-scan.py . --json | jq '[.findings[]
  | select(.rule|test("LINE_TOO_LONG|MIXED_INDENT|TRAILING_WHITESPACE"))] | length'
```

If the second number is above zero **after** formatting, someone's editor is not honouring the config
(trailing whitespace, tabs mixed with spaces). The fix is the plugin plus a word in the retro, not a
rule change. Then check the hook budget: time `git commit` on a file with no changes — it should be
about a second, and if the hook takes more than three, people will start using `--no-verify`, which
costs more than any rule it enforces.

## 5. Closing check

1. Why must the format commit be separate? (blame dies, and the reviewer sees 900 indent lines instead
   of your change)
2. What does a 120-column limit fix *specifically* on GitHub? (side-by-side diffs, and a 13" laptop
   next to a terminal — the interesting half of your line is the part that gets hidden)
3. May you skip the formatter because "this block reads better as is"? No: `prettier-ignore` with a
   reason, or propose changing the rule **for the whole team** in a config PR. Individual opt-outs are
   how a standard becomes a suggestion.

**Policy line for `CONTRIBUTING.md`:** *"Formatting is decided by the committed formatter; review
comments about style are out of scope and get answered with a link to this section; exceptions are
`prettier-ignore` / `dprint-ignore` with a reason on the line above."*

**If you only have 15 minutes:** commit `.editorconfig` + the formatter config and turn on the CI
`--check`. That ends the debate; hooks and blame-ignore can follow next week.

Materials: `../skills/clean-code/references/05-formatting.md` · skill `clean-code-formatting-hooks`
