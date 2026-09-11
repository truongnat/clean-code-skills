# INSTALL — 4 steps, 10 minutes

```bash
git clone https://github.com/truongnat/clean-code-skills.git
cd /path/to/your-project
PACK=/path/to/clean-code-skills      # every command below uses $PACK; set it once
```

Commands in §1–§3 run **from your project root**. The ones under *Acceptance* run **from inside the
clone**, because they test the pack itself.

## 1. Install into your agent

Two artefacts do all the work, and every provider takes at least one of them:

- **`AGENTS.md`** — one portable page of standing instructions. Codex, Cursor, Grok and Antigravity
  all read it; it is the [Agentic AI Foundation](https://agents.md) cross-tool convention.
- **`SKILL.md` folders** — the on-demand detail (`skills/clean-*`). Claude Code, Grok and
  Antigravity consume the *same* format, so one folder shape serves three providers.

| Provider | Standing instructions | Skills (`SKILL.md`) | Verify with | Status |
|---|---|---|---|---|
| **Claude Code** | `CLAUDE.md` | `.claude/skills/` (repo) or `~/.claude/skills/` (user) | `/skills` | **run here** |
| **Codex (ChatGPT)** | `AGENTS.md`, merged root→cwd | `~/.codex/skills/` | `codex --print-instructions` | from docs |
| **Cursor** | `AGENTS.md` + `.cursor/rules/*.mdc` | — (use the rules file) | the Rules pane lists the file | from docs |
| **Grok (xAI)** | `AGENTS.md` family + `.grok/rules/*.md`; also auto-reads `.claude/` | `.claude/skills/` — reused as-is | `grok inspect` | from docs |
| **Antigravity (Google)** | `AGENTS.md` / `GEMINI.md` per directory; `.agents/rules/` | workspace `.agents/skills/` · global `~/.gemini/config/skills/` · or a plugin (§1c) | ask it to list its skills | **run here** |

**Status** means what it says. The Claude Code row was executed in this sandbox; the other four are
transcribed from each vendor's documentation and were **not run** — same honesty rule as the
`golangci-lint` row in `README.md`. Paths move between versions: run the Verify command first and
trust it over this table.

```bash
# Every provider: the portable instructions page
cp $PACK/AGENTS.md .                     # then trim it to your repo

# (a) Claude Code — per repo (recommended: the standard is reviewed like code)
mkdir -p .claude/skills && cp -r $PACK/skills/clean-* .claude/skills/
# ...or per user, available in every repo:
mkdir -p ~/.claude/skills && cp -r $PACK/skills/clean-* ~/.claude/skills/
# Claude Code reads CLAUDE.md, not AGENTS.md:
printf 'See @AGENTS.md for the coding standard.\n' >> CLAUDE.md

# (b) Grok — no extra work: it reads .claude/ and the AGENTS.md family
grok inspect | grep -i -e skill -e agents      # confirm both were discovered

# (c) Antigravity — same SKILL.md folders, different directory
mkdir -p .agents/skills && cp -r $PACK/skills/clean-* .agents/skills/

# (d) Codex
mkdir -p ~/.codex/skills && cp -r $PACK/skills/clean-* ~/.codex/skills/

# (e) Cursor — a rules file, and its frontmatter is NOT the SKILL.md frontmatter
mkdir -p .cursor/rules
{ printf -- '---\ndescription: Clean Code standard - naming, functions, errors, SOLID, layers\nglobs:\n  - "**/*.{ts,tsx,js,py,java,go}"\nalwaysApply: true\n---\n'
  awk 'n>=2; /^---$/ && n<2 {n++}' $PACK/skills/clean-code/SKILL.md  # drop its frontmatter
} > .cursor/rules/clean-code.mdc
```

A plain `cp SKILL.md clean-code.mdc` is the one step that silently does nothing: Cursor keys off
`description` / `globs` / `alwaysApply`, which a `SKILL.md` does not carry, so the rule may never
activate. The `awk` is there for the same reason — it strips `SKILL.md`'s own frontmatter block
instead of leaving `name:` and `description:` loose in the body under your new header. Verified
here: the generated file is 201 lines and starts with exactly one frontmatter block.

Cursor also will not follow `references/` unless you `@file` them — keep `AGENTS.md` as the always-on
layer and pull a reference in when the conversation needs it.

Check (Claude Code): run `claude`, type `/skills` or ask *"list the skills you have"* — you must see
`clean-code`, `clean-architecture`, `clean-code-review`, `clean-code-naming`,
`clean-code-refactoring`, `clean-code-error-handling`, `clean-code-formatting-hooks`.

Frontmatter needs `name` + `description` (already there). `description` is what the model uses to
**decide whether to load the skill at all** — if you edit it, keep the keywords: *clean code,
refactor, code review, naming, error handling, magic number, architecture, layers, dependency rule,
quality gate*.

## 1b. Or install once, globally, for every provider

If you want the standard available in **every** repo without copying it into each one, use one
source of truth and symlink it. This is the recipe that was **executed on a real machine** with all
five providers installed — the skill folders resolve through a two-hop chain and every provider
picked them up:

```bash
REPO=/path/to/clean-code-skills          # the clone
HUB=$HOME/.agents/skills                 # single source of truth
SKILLS=(clean-code clean-architecture clean-code-review clean-code-naming \
        clean-code-refactoring clean-code-error-handling clean-code-formatting-hooks)

mkdir -p "$HUB"
for s in "${SKILLS[@]}"; do ln -sfn "$REPO/skills/$s" "$HUB/$s"; done

# every provider that reads a global skills dir points at the hub
for d in "$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.grok/skills" "$HOME/.cursor/skills"; do
  mkdir -p "$d"
  for s in "${SKILLS[@]}"; do ln -sfn "$HUB/$s" "$d/$s"; done
done

# the scanners on PATH, so a skill works in a repo that has no tools/ folder
ln -sfn "$REPO/tools/cc-scan.py"   "$HOME/.local/bin/cc-scan"
ln -sfn "$REPO/tools/arch-scan.py" "$HOME/.local/bin/arch-scan"
chmod +x "$REPO/tools/cc-scan.py" "$REPO/tools/arch-scan.py"
```

Why symlinks and not `cp`: `git pull` in the clone then updates all five providers at once. A copy
gives you five divergent versions and no way to tell which repo is on which.

Verify (adjust the provider you use):

```bash
for d in ~/.claude/skills ~/.codex/skills ~/.grok/skills ~/.cursor/skills ~/.agents/skills; do
  printf '%-24s ' "$d"; /bin/ls -A "$d" | grep -c '^clean'          # -> 7 each
done
cc-scan --version && arch-scan --version                             # -> 1.0.1 / 1.0.0
cd /tmp && cc-scan . --no-baseline | sed -n 2p                       # works outside the repo
```

Then ask your agent *"list the skills you have"* — the seven `clean-*` entries must appear.

Notes that cost something to learn:

- **Antigravity's global directory is `~/.gemini/config/`, not `~/.agents/`.** `.agents/` is
  Antigravity's *workspace* root (it walks up from your cwd to the repo root). An earlier version of
  this file claimed `~/.agents/skills` was the global location — that was inferred from one machine's
  layout, not read from the docs, and it was wrong. The authoritative source ships with the product:
  `~/.gemini/antigravity-ide/builtin/skills/agy-customizations/docs/skills.md`. Its global skills
  path is `~/.gemini/config/skills/<name>/SKILL.md`; see §1c for the tidier plugin route.
- Why the hub install reached Antigravity anyway on the machine this was tested on:
  `~/.gemini/config/skills` was *itself* already a symlink to `~/.agents/skills`, set up months
  earlier. So installing into the hub reached Antigravity through a machine-local symlink, not
  because `.agents/` is a global path. If your `~/.gemini/config/skills` is a real directory,
  symlink the seven skills into it (or use the plugin in §1c) — the hub alone will not be found.
- **Do not install `AGENTS.md` globally.** It is written for *a* repo and names paths like
  `tools/cc-scan.py`; loaded into every session on the machine it would point agents at files that
  do not exist. Skills are the right global unit precisely because their `description` gates them —
  they load only when the task matches. Keep `AGENTS.md` per repo.
- If the clone moves or is deleted, all five providers break at once. That is the cost of one source
  of truth; keep the clone somewhere permanent, not in a scratch folder.
- `~/.grok/skills` and `~/.cursor/skills` are undocumented by their vendors as far as this pack's
  research went — they were found by inspecting a machine where both are installed. Treat them as
  observed, not promised.

## 1c. Antigravity: install the whole pack as one plugin

Antigravity treats this repo as a **plugin** if it finds a `plugin.json` at the root — which it now
ships. A plugin is a bundle of skills, rules, hooks and MCP configs, and discovery is automatic in
any customization root, so the install is one symlink instead of seven:

```bash
mkdir -p ~/.gemini/config/plugins
ln -sfn /path/to/clean-code-skills ~/.gemini/config/plugins/clean-code-skills
```

The repo's existing `skills/clean-*` folders are ingested as the plugin's skills. Per project
instead of per machine: put it under `<repo>/.agents/plugins/` (or commit it as a submodule) so the
team gets it from version control.

**Pick one route, not both.** Symlinking the seven skills into `~/.gemini/config/skills/` *and*
enabling the plugin registers the same seven skills twice. The vendor docs promise namespacing for
collisions and deduplication for *rules*; they do not promise skill deduplication, so do not rely
on it.

### Why there is no `/clean-code` slash command

There isn't one, and that is by design — not a broken install. Antigravity's customization system
has exactly five types (Rules, Skills, Plugins, Hooks, MCP Servers) and none of them is a command.
Skills load by **progressive disclosure**, quoting the shipped docs:

> Skills are not loaded into the context window by default. Only their names and descriptions are
> injected. The full content of a skill is only loaded if the model (or the user) explicitly decides
> to activate it.

So you invoke a skill by describing the task, or by naming it — that naming *is* the documented
"or the user explicitly decides":

```
use the clean-code-review skill on this diff
```

The `description` field is therefore the whole activation mechanism on every provider. If a skill
never fires, rewrite its description before touching anything else.

## 2. Put the scanners in your repo (the skills reference these paths)

```bash
mkdir -p tools
cp $PACK/tools/cc-scan.py $PACK/tools/arch-scan.py tools/
python3 tools/cc-scan.py . --fail-on none | head -2     # prints your current score
python3 tools/arch-scan.py . --fail-on none | head -8   # layer census + dependency matrix
```

Want the skills to always find the scripts, even in a repo without `tools/`? Two options — do
either, not both:

```bash
# (a) per repo: the skill carries its own copy
mkdir -p .claude/skills/clean-code/tools
cp $PACK/tools/{cc-scan.py,arch-scan.py} .claude/skills/clean-code/tools/

# (b) once per machine: the scanners on PATH, usable from any repo. Do this if you followed §1b
mkdir -p ~/.local/bin
ln -sfn "$PACK/tools/cc-scan.py"   ~/.local/bin/cc-scan
ln -sfn "$PACK/tools/arch-scan.py" ~/.local/bin/arch-scan
chmod +x "$PACK/tools/cc-scan.py" "$PACK/tools/arch-scan.py"
cc-scan --version && arch-scan --version        # -> 1.0.1 / 1.0.0
```

`~/.local/bin` must be on your `PATH` (`echo $PATH | tr : '\n' | grep local/bin`); add
`export PATH="$HOME/.local/bin:$PATH"` to your shell rc if it is not. Every `SKILL.md` states this
fallback, so an agent working in a repo with no `tools/` folder will reach for `cc-scan` instead of
reporting the command as missing.

`arch-scan` needs one thing `cc-scan` does not: a **declared layer map**. Without a config it still
works (it reports `UNCLASSIFIED_FILES` rather than pretending), but you should copy the template:

```bash
cp $PACK/configs/architecture/arch-scan.config.json .   # edit layers to your folder names
```

## 3. Copy the config for your stack

| Stack | Command |
|---|---|
| JS/TS | `cp $PACK/configs/js/.prettierrc.json $PACK/configs/js/eslint.config.js .` then `npm i -D prettier eslint @eslint/js typescript-eslint husky lint-staged` |
| Python | `cp $PACK/configs/python/pyproject.toml .` · `pipx install pre-commit && pre-commit install` · `cp $PACK/configs/ci/.pre-commit-config.yaml . && cp -r $PACK/configs/ci/hooks .` · `bash $PACK/configs/python/lint.sh` |
| Python + contracts | `cp $PACK/configs/architecture/.importlinter .` · `pipx install import-linter && lint-imports` |
| Java | `cp $PACK/configs/java/checkstyle.xml build-tools/` + enable the plugin (see `configs/java/README.md`); for layers: ArchUnit — `configs/architecture/demo/java` |
| Go | `cp $PACK/configs/go/.golangci.yml .` (contains `depguard` rules for the layer ban) |
| Node/TS boundaries | `cp $PACK/configs/architecture/.dependency-cruiser.cjs .` |
| EditorConfig | `cp $PACK/configs/ci/.editorconfig .` |
| CI | `mkdir -p .github/workflows && cp $PACK/configs/ci/github-actions-clean-code.yml .github/workflows/clean-code.yml` (GitLab: `configs/ci/gitlab-ci-clean-code.yml`) |

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
python3 tools/tests/run_checks.py | tail -1      # → 61/61 checks passed
python3 tools/tests/run_arch_checks.py | tail -1 # → 30/30 arch checks passed
python3 tools/check_links.py | tail -1           # → 294 references, 0 broken links
python3 tools/cc-scan.py tools/demo/src/legacy-order-service.ts \
        tools/demo/src/legacy-renderer.ts --no-baseline | sed -n 2p
                                                                    # → 72.0/100 (grade C)
python3 tools/arch-scan.py configs/architecture/demo/python | sed -n 2p
                                                                    # → 82.0/100 · error=3
cd configs/python && bash lint.sh                # → exit 0
cd ../js && npx eslint samples/good-example.ts && echo OK   # → OK
```

Scripts are invoked with `bash` on purpose: `cp -r` and zip extraction do not always keep the
executable bit, and `lint.sh` / `check-arch.sh` then die with exit 126 before reporting anything.
A `git clone` of this repo keeps the bit; a copied folder may not.

## Uninstall

```bash
# per repo
rm -rf .claude/skills/clean-* .agents/skills/clean-* .cursor/rules/clean-code.mdc
# global (symlinks only - the clone itself is untouched)
rm -f ~/.claude/skills/clean-* ~/.codex/skills/clean-* ~/.grok/skills/clean-* \
      ~/.cursor/skills/clean-* ~/.agents/skills/clean-* \
      ~/.local/bin/cc-scan ~/.local/bin/arch-scan
rm -f AGENTS.md tools/cc-scan.py tools/arch-scan.py .clean-code-baseline.json arch-scan.config.json
```

`configs/` is only config — delete the lines you pasted into `package.json`/`pyproject.toml`, and the
job from `.github/workflows`.

## FAQ

**Do the skills run `cc-scan.py` themselves?**
Yes, when the agent may execute commands — Claude Code, Codex CLI, Grok and Antigravity's agent
manager all can, subject to their own approval prompts. Cursor's rules layer and any sandbox without
exec cannot: run `python3 tools/cc-scan.py .` yourself and **paste the output** into the chat —
every prompt in `prompts/` is written to consume exactly that report.

**My provider is not in the table.**
Give it `AGENTS.md`. That is the whole point of the file: it is the
[Agentic AI Foundation](https://agents.md) convention, so any agent that follows it gets the
standard without a provider-specific recipe. If it also loads `SKILL.md` folders, point it at
`skills/`; if not, `AGENTS.md` alone is a working install and `prompts/` covers the rest by paste.

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
