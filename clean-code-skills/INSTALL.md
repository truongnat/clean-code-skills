# INSTALL — 4 steps, 10 minutes

## 1. Pick where the skills live

```bash
# (a) Claude Code / Arena agent — per USER (available in every repo)
mkdir -p ~/.claude/skills && cp -r clean-code-skills/skills/clean-* ~/.claude/skills/

# (b) Per REPO (recommended: the standard lives in the repo, gets reviewed, changes for everyone)
mkdir -p .claude/skills && cp -r clean-code-skills/skills/clean-* .claude/skills/

# (c) Cursor / Windsurf — a single rules file (it will not read references/ unless you @file them)
mkdir -p .cursor/rules
cp clean-code-skills/skills/clean-code/SKILL.md .cursor/rules/clean-code.mdc

# (d) Codex and other agents: keep the tree in the repo, symlink it
ln -s "$(pwd)/clean-code-skills/skills/clean-code" "$HOME/.codex/skills/clean-code"
```

Check (Claude Code): run `claude`, type `/skills` or ask *"list the skills you have"* — you must see
`clean-code`, `clean-architecture`, `clean-code-review`, `clean-code-naming`,
`clean-code-refactoring`, `clean-code-error-handling`, `clean-code-formatting-hooks`.

Frontmatter needs `name` + `description` (already there). `description` is what the model uses to
**decide whether to load the skill at all** — if you edit it, keep the keywords: *clean code,
refactor, code review, naming, error handling, magic number, architecture, layers, dependency rule,
quality gate*.

## 2. Put the scanners in your repo (the skills reference these paths)

```bash
mkdir -p tools
cp clean-code-skills/tools/cc-scan.py clean-code-skills/tools/arch-scan.py tools/
python3 tools/cc-scan.py . --fail-on none | head -2     # prints your current score
python3 tools/arch-scan.py . --fail-on none | head -8   # layer census + dependency matrix
```

Want the skills to always find the scripts, even in a repo without `tools/`:

```bash
mkdir -p .claude/skills/clean-code/tools
cp clean-code-skills/tools/{cc-scan.py,arch-scan.py} .claude/skills/clean-code/tools/
```

`arch-scan` needs one thing `cc-scan` does not: a **declared layer map**. Without a config it still
works (it reports `UNCLASSIFIED_FILES` rather than pretending), but you should copy the template:

```bash
cp clean-code-skills/configs/architecture/arch-scan.config.json .   # edit layers to your folder names
```

## 3. Copy the config for your stack

| Stack | Command |
|---|---|
| JS/TS | `cp clean-code-skills/configs/js/.prettierrc.json clean-code-skills/configs/js/eslint.config.js .` then `npm i -D prettier eslint @eslint/js typescript-eslint husky lint-staged` |
| Python | `cp clean-code-skills/configs/python/pyproject.toml .` · `pipx install pre-commit && pre-commit install` · `cp clean-code-skills/configs/ci/.pre-commit-config.yaml . && cp -r clean-code-skills/configs/ci/hooks .` · `bash clean-code-skills/configs/python/lint.sh` |
| Python + contracts | `cp clean-code-skills/configs/architecture/.importlinter .` · `pipx install import-linter && lint-imports` |
| Java | `cp clean-code-skills/configs/java/checkstyle.xml build-tools/` + enable the plugin (see `configs/java/README.md`); for layers: ArchUnit — `configs/architecture/demo/java` |
| Go | `cp clean-code-skills/configs/go/.golangci.yml .` (contains `depguard` rules for the layer ban) |
| Node/TS boundaries | `cp clean-code-skills/configs/architecture/.dependency-cruiser.cjs .` |
| EditorConfig | `cp clean-code-skills/configs/ci/.editorconfig .` |
| CI | `mkdir -p .github/workflows && cp clean-code-skills/configs/ci/github-actions-clean-code.yml .github/workflows/clean-code.yml` (GitLab: `configs/ci/gitlab-ci-clean-code.yml`) |

## 4. Onboard legacy code without paralyzing the team

```bash
python3 tools/cc-scan.py . --update-baseline
git add .clean-code-baseline.json && git commit -m "chore(ci): baseline clean-code"
```

From then on CI **blocks only new findings**. Shrink the baseline a little each sprint
(`tools/README.md` §4). If a rule must stay silent permanently for a folder, declare it in
`clean-code.config.json` under `skipRules` (see `tools/clean-code.config.json` as a worked example)
— with a reason, so the decision is visible in `git log` rather than hidden in a disable comment.

For architecture there is no baseline: either the declared direction holds or the PR stops. If a
layer must break for a while, put `# arch-scan:allow UPWARD_DEPENDENCY — ticket ARCH-142` on the
import line and give the ticket a deadline.

## Acceptance — run these, they must match

```bash
python3 clean-code-skills/tools/tests/run_checks.py | tail -1      # → 60/60 checks passed
python3 clean-code-skills/tools/tests/run_arch_checks.py | tail -1 # → 30/30 arch checks passed
python3 clean-code-skills/tools/check_links.py | tail -1           # → 200 references, 0 broken links
python3 clean-code-skills/tools/cc-scan.py clean-code-skills/tools/demo/src/legacy-order-service.ts \
        clean-code-skills/tools/demo/src/legacy-renderer.ts --no-baseline | sed -n 2p
                                                                    # → 72.0/100 (grade C)
python3 clean-code-skills/tools/arch-scan.py \
        clean-code-skills/configs/architecture/demo/python | sed -n 2p
                                                                    # → 82.0/100 · error=3
cd clean-code-skills/configs/python && bash lint.sh                # → exit 0
cd clean-code-skills/configs/js && npx eslint samples/good-example.ts && echo OK   # → OK
```

Scripts are invoked with `bash` on purpose: `cp -r` and zip extraction do not always keep the
executable bit, and `lint.sh` / `check-arch.sh` then die with exit 126 before reporting anything.
A `git clone` of this repo keeps the bit; a copied folder may not.

## Uninstall

```bash
rm -rf ~/.claude/skills/clean-* .claude/skills/clean-* .cursor/rules/clean-code.mdc
rm -f tools/cc-scan.py tools/arch-scan.py .clean-code-baseline.json arch-scan.config.json
```

`configs/` is only config — delete the lines you pasted into `package.json`/`pyproject.toml`, and the
job from `.github/workflows`.

## FAQ

**Do the skills run `cc-scan.py` themselves?**
Yes, when the agent may execute commands (Claude Code / agent mode). If your agent is sandboxed
without exec, run `python3 tools/cc-scan.py .` yourself and **paste the output** into the chat —
every prompt in `prompts/` is written to consume exactly that report.

**Do I have to install everything in `configs/`?**
No. Pick your stack. Enabling two formatters on the same files (Black + Prettier) is the fastest way
to get your team to switch CI off.

**Team of 6, 300k-line repo — where do I start?**
Step 4 (baseline) + playbook session 05 (formatting) + session 09 (CI). Those three alone change the
trajectory. Then session 10 (clean architecture) once the code is stable enough to talk about layers.
Do not try to enforce 20 rules in one week.

**Where do thresholds live?**
`tools/clean-code.config.json` (max function lines, max params, max line length, ignore dirs,
skipRules) and `arch-scan.config.json` (layers, framework packages, boundaries) — or
`--max-fn-lines 30` for a single run.
