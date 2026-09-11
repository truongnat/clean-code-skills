# CHANGELOG

## 1.3.0 — 2026-09-11 · Global install, one source of truth

### Added
- **`INSTALL.md` §1b — global install for every provider**, and this one was *executed*, not
  transcribed. One hub (`~/.agents/skills`) symlinked to the clone, then each provider's global
  skills directory symlinked to the hub, then the scanners on `PATH`. `git pull` in the clone now
  updates all five providers at once; a `cp`-based install would give five divergent copies.
- **Scanner-path note in all 7 `SKILL.md` files.** The skills issue 26 commands of the form
  `python3 tools/cc-scan.py`, which is correct for a per-repo install and **broken for a global
  one** — an arbitrary repo has no `tools/` folder. Each skill now states the fallback up front:
  use `cc-scan` / `arch-scan` from `PATH`, and if neither exists, ask for the report rather than
  inventing numbers.

### Measured on the machine this was installed on
- All five providers were already present (`~/.claude`, `~/.codex`, `~/.grok`, `~/.cursor`,
  `~/.gemini`), and the existing convention was discovered by inspection rather than assumed: the
  machine already used `~/.agents/skills` as a hub with 50/65/8/49 symlinks into it from Claude
  Code / Codex / Grok / Cursor respectively. The install follows that convention instead of
  inventing a parallel one.
- **7/7 `SKILL.md` files readable through the two-hop symlink chain in all 5 directories** (35
  paths checked). `cc-scan --version` → 1.0.1 and `arch-scan --version` → 1.0.0 from `/tmp`, i.e.
  outside the repo. The seven skills then appeared in a live agent session, which is the only
  end-to-end proof that matters.
- **`~/.agents/skills` is also Antigravity's global skills directory**, so the hub and Antigravity's
  own location are the same folder — no separate step.
- `~/.grok/skills` and `~/.cursor/skills` are **not documented by their vendors** as far as this
  pack's research reached; they were found by inspecting an installed machine. Recorded as observed,
  not promised.

### Deliberately not done
- **`AGENTS.md` is not installed globally.** It is written for *a* repo and names paths such as
  `tools/cc-scan.py`; loaded into every session on the machine it would point agents at files that
  do not exist. Skills are the correct global unit because their `description` gates them — they
  load only when the task matches. `AGENTS.md` stays per repo.
- One consequence is documented rather than engineered away: if the clone moves or is deleted, all
  five providers break at once. That is the price of a single source of truth.

---

## 1.2.1 — 2026-09-11 · Published: flattened layout, no vendored binaries

### Changed
- **The pack moved to the repo root.** It used to sit in a nested `clean-code-skills/` folder, which
  meant a GitHub landing page with no README. Every install command now uses a `$PACK` variable set
  once at the top of `INSTALL.md`, so it no longer matters where you clone to, and the *Acceptance*
  block runs verbatim from the repo root (re-run after the move: **61/61**, **30/30**,
  **291 references 0 broken**, demo **72.0/100**, python arch demo **82.0/100**).
- **The three verification JARs are no longer vendored** (`checkstyle.jar` 19M, `archunit-1.3.0.jar`
  4.4M, `slf4j-api-2.0.13.jar` 68K = 23.4M). They are third-party binaries under LGPL-2.1/Apache-2.0
  and nothing in the pack needs them at install time. `javalib/` and `*.jar` are now ignored, and the
  two `curl` commands that fetch them live next to the measurements they reproduce
  (`configs/java/README.md`, `configs/architecture/demo/java/README.md`). Largest tracked file is now
  56 KB. Note: the blobs remain in commit `048086a`, so a clone still pays for them in history until
  someone rewrites it.

### Fixed
- **`AGENTS.md` was never committed** in 1.2.0, despite the commit message saying so: a machine-wide
  `AGENTS.md` pattern in `~/.gitignore_global` made `git add -A` skip it silently. Force-added, and
  `.gitignore` now carries `!AGENTS.md` — a repo rule outranks the global one, so it cannot happen
  again to anyone sharing that pattern. The lesson is in the file: a commit message is not evidence;
  `git show --stat` is.

### Still not verified
- The Java rows (Checkstyle, ArchUnit) could not be re-run after the move — there is no JDK in this
  sandbox, same as `golangci-lint`. The relative classpath in the ArchUnit demo was updated to
  `../../../../javalib/…` by path arithmetic, not by execution. Marked here so nobody mistakes it
  for a measured result.

---

## 1.2.0 — 2026-09-11 · Five providers, one standard

### Added
- **`AGENTS.md` at the pack root** — one portable page of standing instructions (the rules in cost
  order, the hard constraints on agent output, the definition of done). Codex, Cursor, Grok and
  Antigravity all read `AGENTS.md`; Claude Code reads `CLAUDE.md` and is pointed at it with one
  line. It is deliberately short, because it is loaded into every session.
- **`INSTALL.md` §1 rewritten as a provider matrix** covering **Claude Code · Codex (ChatGPT) ·
  Cursor · Grok (xAI) · Antigravity (Google)**: the standing-instructions file, the skills path, the
  command that verifies the install, and a **Status** column saying which row was executed here.
  The lazy win documented explicitly: Claude Code, Grok and Antigravity consume the *same*
  `SKILL.md` format, so one folder shape serves three providers (Grok reads `.claude/` directly;
  Antigravity uses `.agents/skills/`, legacy `.agent/skills/`).

### Fixed
- **The Cursor install was a silent no-op.** `INSTALL.md` said
  `cp skills/clean-code/SKILL.md .cursor/rules/clean-code.mdc`, but Cursor keys off
  `description` / `globs` / `alwaysApply` frontmatter, which a `SKILL.md` does not carry — the rule
  could never activate, and the user would conclude the pack was broken. Replaced with a generator
  that writes the `.mdc` frontmatter and strips `SKILL.md`'s own frontmatter block
  (`awk 'n>=2; /^---$/ && n<2 {n++}'`) instead of `tail -n +2`, which left `name:`/`description:`
  loose in the body. **Run here**: the generated file is 201 lines with exactly one frontmatter
  block and no leaked key.
- `README.md`'s tree and install block said "Claude Code / Cursor / Codex"; both now name all five
  and point at `AGENTS.md`.
- The `Uninstall` section left residue: it now also removes `AGENTS.md`, `.agents/skills/clean-*`
  and `~/.codex/skills/clean-*`.

### Notes on measurement
- Only the **Claude Code** row was executed (7 skills discovered under `.claude/skills/`), plus the
  Cursor `.mdc` generator. The Codex, Grok and Antigravity paths are transcribed from vendor
  documentation and are marked **not run** in both `README.md` and `INSTALL.md` §1 — the same rule
  the `golangci-lint` row has followed since 1.0.0. Provider paths move between versions, so every
  row carries a Verify command (`/skills`, `codex --print-instructions`, `grok inspect`) and that
  command outranks the table.
- Direct fetches of the vendor docs failed in this sandbox (DNS blocked); the paths come from search
  results, which is a weaker source than the doc itself. Treat the four unexecuted rows as a
  starting point to confirm, not as tested fact.
- `tools/check_links.py` → **291 references, 0 broken** (was 264; `AGENTS.md` adds 8).
  `run_checks.py` **61/61**, `run_arch_checks.py` **30/30**, both unchanged by this release.

---

## 1.1.0 — 2026-09-11 · Clean architecture, patterns, and the move to English

### Added — architecture & patterns (new, written in English)
- **`tools/arch-scan.py` v1.0.0** — dependency-direction scanner, stdlib only, 6 rules
  (`UPWARD_DEPENDENCY`, `LAYER_CYCLE`, `DOMAIN_FRAMEWORK_IMPORT`, `BOUNDARY_LEAK`,
  `UNCLASSIFIED_FILES`, `LAYER_UNUSED`). Understands Python/JS-TS/Java-Kotlin/Go imports, prints a
  layer census and a dependency matrix, `--json`, `-o`, `--fail-on`, `--explain`, `--list-rules`,
  and its own `arch-scan:allow` escape hatch.
- **`tools/tests/run_arch_checks.py`** — 30 assertions on new fixtures: `layers/dirty` (all four
  error rules + exact line + score band), `layers/clean` (**100.0/100, 0 findings**), `layers/java`
  and `layers/go` (dotted and module-path imports via `rootPackages`), allow-comment scope, config
  fallback, CLI surface, drift on an unknown layout.
- **Fixtures**: `tools/tests/fixtures/layers/{dirty,clean,java,go}` — 24 files, including a
  deliberately correct layered app used as the false-positive guard.
- **References**: `12-clean-architecture.md` (dependency rule, four layers, ports & adapters,
  boundary rules, choosing seams by change coupling, the over-engineering ladder),
  `13-architecture-patterns.md` (layered · hexagonal · modular monolith · event-driven · CQRS/ES ·
  microservices · serverless · pipe-and-filter · plugin; selection matrix with reversibility;
  outbox/idempotency/contract-test non-negotiables; strangler and branch-by-abstraction),
  `14-design-patterns.md` (the five that earn their keep, the eight people reach for too early,
  anti-pattern table, rule of three).
- **Playbook Part II**: `10-clean-architecture.md`, `11-architecture-patterns.md`,
  `12-design-patterns.md` — sessions with exercises, quiz + answers, DoD.
- **Prompts**: `11-architecture-review.md`, `12-boundary-designer.md`, `13-pattern-picker.md`.
- **Sub-skill** `skills/clean-architecture/SKILL.md` — routing for structure questions, census
  commands, placement test, review vocabulary, enforcement recipe.
- **`configs/architecture/`** — `arch-scan.config.json` (worked example), `ARCHITECTURE.md`
  template, `.dependency-cruiser.cjs`, `.importlinter`, plus **runnable demos**:
  `demo/python` (import-linter 2.15: 2 contracts BROKEN → KEPT, exit 1 → 0) and
  `demo/java` (ArchUnit 1.3.0 on JDK 11: 3 rules BROKEN → KEPT).
- **CI**: `arch-scan` wired into `github-actions-clean-code.yml` (step), `gitlab-ci-clean-code.yml`
  (job + artifact), `.pre-commit-config.yaml` (hook calling `hooks/check-arch.sh`, quiet when a repo
  declares no layers). `configs/go/.golangci.yml` gained `depguard` rules and `forbidigo`.

### Changed — language, and the docs guard that protects it
- Documentation language is now **English**, throughout: prose, tool output, lint messages and code
  comments. Converted in this release: root `README.md`, `INSTALL.md`, `tools/README.md`,
  `tools/cc-scan.py` (rule catalogue, every message and hint, CLI help), `tools/check_links.py`,
  `tools/SELF_REVIEW.md`, `tools/tests/run_checks.py` (61 labels), the router skill, all **six**
  sub-skills, `references/01..14`, `checklists/`, `templates/`, `snippets/`, the whole `playbook/`
  (12 sessions + both appendices) and every `configs/*` file, including ESLint/Checkstyle message
  text and the GitHub Actions step names.
- **`playbook/` sessions renamed to English** in the same pass as their translation —
  `01-what-clean-code-means.md` … `09-code-health-and-workflow.md` — and every reference to them
  across the pack rewritten in the same commit (`check_links.py` verifies all 223 of them).
- Translated **and expanded**, not just converted: each reference and session gained a
  rule-to-enforcement table, a per-language recipe, a "when the tool is wrong / when to stop" table,
  worked refactors with measured numbers, and a policy line to paste into `CONTRIBUTING.md`; the
  appendices gained a 10-minute-per-level verification block and Appendix A was renumbered to 34
  questions with an architecture block.
- New check in `tools/tests/run_checks.py` (**61 checks**, was 57): *docs guard* — every markdown file
  under `skills/` and `playbook/` must have an ASCII H1. It exists because a rename silently restored
  a translated session with its old Vietnamese file during this release; the guard caught two more
  stale files the first time it ran.
- **The conversion is complete.** The last pass took `prompts/00..10` + its README, the comments
  inside `tools/tests/fixtures` and `tools/demo`, `tools/SELF_REVIEW.md`'s older half, the remaining
  `configs/ci` + `configs/python` + `configs/js` comments, `.gitignore`,
  `tools/clean-code.config.json`, and this file's 1.0.0/1.0.1 entries. The only Vietnamese left is
  deliberate: 7 lines in 5 files (see §*Intentional Vietnamese* below).
- **`prompts/` translated and expanded** — every one of the 14 prompts (00–13, not only the
  untranslated ones) gained three sections: **Minimum input** (what must be pasted before the answer
  stops being guesswork), **Output acceptance criteria** (a checklist to run before you start
  editing code), and **Keeping it from inventing symbols** (a paste-in block forbidding invented
  identifiers, files, line numbers, tickets and sources, and requiring the model to count its own
  unsupported claims). `prompts/README.md` documents the shape once. Prompt 01's placeholder title
  typo (`ĐỊNH DẦN`) and prompt 03's inconsistent `500000` → `500_000_000` example were fixed in the
  same pass.
- **Second pass: unaccented Vietnamese.** The first sweep searched for Vietnamese *diacritics*, so
  ASCII-transliterated Vietnamese survived it — the kind people type without a Vietnamese keyboard.
  A dictionary-based sweep (`/usr/share/dict`, tokens absent from English, word-boundary matched)
  found 14 more spots and they are now English: the `HOA DON` invoice labels in
  `fixtures/messy/{order-service.ts,invoice-render.ts}` (changed identically so the
  `DUPLICATE_BLOCK` pair still matches), `suppressed.ts`'s exception-reason header,
  `worker.go`'s and `ReportGenerator.java`'s TODO/FIXME text, `checkout.py`'s prints and its
  `dong` → `vnd` variable, `configs/go/demo/bad.go` + `configs/java/demo/OrderTotalsBad.java`
  ("tach ham nay ra, viet tu 2019"), `configs/python/src/orders_bad.py`'s exception message,
  `configs/python/pyproject.toml`, `configs/ci/hooks/check-hygiene.sh`, and four spots in
  `tools/tests/run_checks.py` (two check labels, a temp-dir name, and the `viet` variable →
  `non_ascii`). Line counts and line numbers were preserved throughout, so every fixture assertion
  still lands: **61/61**, **30/30**, demo still **72.0/100 (4 errors)**.
- The 1.0.0/1.0.1 entries were translated **without touching their numbers** — `53/53`, `92
  references`, `99 references` and `20 rules` are what was true at those releases; the deltas are
  documented in this entry instead. One truncated sentence was repaired: `COMMENTED_CODE` … `→ si
  phạm vi` now reads "the scope was narrowed to the comment".

### Fixed
- `arch-scan` only recognised `interface/`, so a tree using the hexagonal spelling `interfaces/`
  reported `LAYER_UNUSED` + `UNCLASSIFIED_FILES` on correctly layered code. Added `**/interfaces/**`
  and `**/entrypoints/**` to the defaults and to `configs/architecture/arch-scan.config.json`:
  `configs/architecture/demo/java` now scores **99.0/100 (A), 0 errors** (the single remaining info
  is the build-time `src_check/ArchitectureCheck.java`, which is not a layer file).
- Scanning the pack root reports 45.0/100 (E) with 9 errors **by design** — `tools/tests/fixtures/layers/dirty`
  is a deliberately broken tree. Point the tool at `src`, not at the pack root, or ignore
  `tools/tests/fixtures` in `ignoreGlobs` if you copy this layout.
- `configs/go/.golangci.yml`: an earlier scripted edit duplicated `linters-settings:` and swallowed
  the `_test.go` exclusion line, which made the YAML unparseable. Rewritten in English, verified by
  `yaml.safe_load`: 4 top-level keys, 36 linters, 2 depguard rule sets, 2 exclusions.
- `cc-scan.py` — the 5 CLI `help=` lines lost their closing parenthesis during the translation
  (caught by `ast.parse`, fixed); a comment `# return type` was itself reported as
  `COMMENTED_CODE` by the tool — reworded, dogfood test green again.

### Notes on measurement
- Everything quoted below was re-run on 2026-09-11, the release date; the toolchains used are ruff 0.16.6,
  black 26.5.1, mypy 2.3.1, import-linter 2.15, ESLint 10.10.0 + Prettier 3.6.2,
  Checkstyle 10.21.4 on OpenJDK 11, and ArchUnit 1.3.0.
- `python3 tools/cc-scan.py .` from the pack root scans 75 code files in ~0.21 s (before the fix in
  §"Fixed" of 1.0.1 it crawled `configs/js/node_modules`: 2163 files, 50 s).
- `python3 tools/arch-scan.py configs/architecture/demo/python` → `82.0/100`, 3 errors; the same
  folder under import-linter → 2 contracts BROKEN. Both tools report the same two edges.

### Done — English conversion (closed in this release)

Everything is converted: root `README.md`, `INSTALL.md`, `tools/README.md`, `tools/cc-scan.py`
(20 rule descriptions, every message and hint, CLI help), `tools/arch-scan.py`,
`tools/check_links.py`, `tools/tests/run_checks.py` (61 labels), `tools/tests/run_arch_checks.py`,
`tools/SELF_REVIEW.md` (both halves), `tools/demo/` (README + all 4 source files),
`tools/tests/fixtures/` (comments in both the messy and the clean sets), the router skill and all
**six** sub-skills, `references/01..14`, `checklists/`, `templates/`, `snippets/`, the whole
`playbook/` (12 sessions + both appendices), every `configs/*` file (including ESLint/Checkstyle
message text, the GitHub Actions step names, `sonar-project.properties`, `.editorconfig`,
`.prettierignore` and the Python `Makefile`), `prompts/00..13` + README, `.gitignore`,
`tools/clean-code.config.json`, and this CHANGELOG.

Numbers quoted inside the last batch were re-measured rather than carried over:

| What | Was written | Re-measured on the release date |
|---|---|---|
| `tools/tests/run_checks.py` | 60/60 | **61/61** (the docs guard makes 61) |
| `tools/check_links.py` | 200 references | **291 references, 0 broken** |
| the same two figures in `INSTALL.md` §Acceptance and `tools/README.md` §6 | 60/60 · 200 references | **61/61 · 291 references** — the acceptance block was re-run line by line and now matches its own output |
| `tools/demo` legacy line numbers | 17 / 48 / 55, "5 levels", 1 TODO | **15 / 50 / 56, 7 levels, 2 TODOs** — the score is unchanged at **72.0/100 (4 errors)** |
| `cc-scan.py` self-review | 32.8/100, error=11 warning=23 info=1 | `tools/` (5 files) **0.0/100, error=18 warning=46 info=2**; `cc-scan.py` alone **35.8/100, error=11 warning=20 info=1**; raw defaults **0.0/100** |
| `cc-scan.py` accepted-debt counts | MAGIC_NUMBER 41, DEBUG_STATEMENT 20, DEEP_NESTING 15 | across `tools/`: **MAGIC_NUMBER 55, DEBUG_STATEMENT 46, DEEP_NESTING 32, HARD_COMPLEXITY 12, HUGE_FUNCTION 5** |
| pack-root scan | 32 code files, ~0.15 s | **75 code files, ~0.21 s** (the 1.1.0 architecture fixtures and demos are new files) |
| CI YAML file count | "all 5 YAML files" in `README.md` | **4** (`configs/ci/*.yml` ×2, `.pre-commit-config.yaml`, `configs/go/.golangci.yml`) — the 1.0.1 entry already said 4; the README row was wrong |

`arch-scan` is unchanged by this pass and was re-run to confirm it:
`configs/architecture/demo/python` → **82.0/100, 3 errors**, `demo/java` → **99.0/100, 0 errors**,
pack root → **45.0/100, 9 errors** (the deliberately broken `fixtures/layers/dirty`).

### Intentional Vietnamese (7 lines, 5 files — not a gap)

These stay in Vietnamese because they *are* the example:

| File | Line | Why |
|---|---|---|
| `skills/clean-code-naming/SKILL.md` | 126–127 | the domain-glossary example: `Đơn hàng = Order` (not `Sale`), `Hoá đơn = Invoice`, `Bên vận chuyển = Carrier` |
| `playbook/02-naming.md` | 67–68 | the same glossary exercise |
| `prompts/01-name-finder.md` | 31 | the glossary placeholder shown to the model (`Tạm ứng = Deposit`) |
| `skills/clean-code-error-handling/SKILL.md` | 30 | the bad example `Error("lỗi")` — a useless message is the point |
| `prompts/05-error-handling.md` | 12 | the same bad example inside rule 1 |

A translated glossary example would teach the opposite lesson: the glossary exists precisely to map
the business's own words onto code identifiers.

Not counted above: `minh` appears as the *owner's name* in the `TODO(AC-1240, minh)` examples in
`prompts/06-comment-cleaner.md`, `skills/clean-code/references/04-comments.md` and
`skills/clean-code/snippets/bad-vs-good.md`. A TODO needs a real-looking owner; a person's name is
not text to translate.

No rule, threshold or command changed anywhere in this conversion.

---

## 1.0.1 — 2026-09-10 · Escape-hatch fix + the docs checked against themselves

### Fixed (real defects, found by testing the documentation)
- **`cc-scan:allow` did not apply to line-level rules.** The docs promised "put the comment on the
  line immediately above the violation", but the code only honoured that for function-level rules —
  so `// cc-scan:allow MAGIC_NUMBER` on the line above was still reported. `allow` now applies to
  **every rule**, scoped to **the line holding the comment + the line immediately after**, and does
  not spread across the whole function (the `add()` helper inside `scan_file`).
- Deleted `configs/js/prettier.config.mjs` — it duplicated `.prettierrc.json`, and two live config
  sources is the fastest route to everyone's formatter behaving differently.
- `README.md` / `tools/README.md`: removed an unverified claim (the CI step "was run") — it now says
  plainly that the YAML parses, while the commands inside it were not executed because the sandbox
  has no runner.

- **`configs/ci/.pre-commit-config.yaml` would not parse** (YAML `mapping values are not allowed
  here`, line 52): two multi-line `bash -c '...'` hooks embedded in a plain scalar. Replaced with
  **one** `hygiene` hook calling `hooks/check-hygiene.sh` — that script already covered all three
  jobs (debug logs/.only, conflict markers, `System.out`/`fmt.Print`), and keeping the logic in
  shell is the only way local and CI share one gate.
- Hook paths are now relative to the repo root → every install guide (`INSTALL.md`, `playbook/05`,
  the `clean-code-formatting-hooks` skill) gained `cp -r configs/ci/hooks .`.

- **Scanning several paths silently disabled `ignoreDirs`.** `load_config()` looked for a config
  file in *every* path passed, so `cc-scan skills playbook prompts tools configs` loaded
  `tools/clean-code.config.json` (which only declares `ignoreDirs: ["fixtures","demo"]`) and
  **replaced** the default list → the tool crawled into `configs/js/node_modules`, scanning 2163
  files in 50 seconds instead of 32 files in 0.14. Three fixes: (1) `ignoreDirs` is now **appended**
  to the defaults, (2) `ALWAYS_IGNORE_DIRS` is a floor no config can remove, (3) a config is only
  loaded from a directory being scanned.
- **`cc-scan … | head` printed a `BrokenPipeError` traceback.** A real CLI stays quiet like `grep`
  does: the default `SIGPIPE` handler is restored at the top of `main()` (POSIX; ignored on Windows).

### Additionally verified
- The 4 YAML files under `configs/ci/` and `configs/go/` parse with `yaml.safe_load` → OK.
- `check-hygiene.sh` run for real inside a temporary git repo: a dirty file (console.log +
  `<<<<<<<`) → **exit 1** printing exactly 2 error lines; a clean file → **exit 0**.
- `cc-scan.py` at version 1.0.1; `tools/check_links.py` → 99 references, 0 broken links.

### Added
- `tools/check_links.py` (written with guard clauses so it scores **100.0/100** when `cc-scan` reads
  it): checks **92 relative references** between the documents (both `[..](..)` links and paths in
  backticks); exits 1 on a broken link.
- `tools/tests/run_checks.py`: 7 new tests — the scope of `cc-scan:allow` (same line / the line
  above / no spreading / only the named rule) and the scope of `ignoreDirs` + config (3 tests) →
  **60/60 PASS**.
- The `suppressed.ts` fixture's `mixed()` function rewritten to demonstrate both comment placements.
- A `.gitignore` at the pack root (node_modules, caches, reports; with a note that the baseline
  *should* be committed).
- Fixed 3 broken links: the code-smells reference in `SKILL.md` (old name `07-code-smells`, now
  `references/10-code-smells-refactorings.md`), and the playbook filename in
  `templates/adr-template.md` and `configs/java/README.md`.
- Fixed 7 places where a CJK character had slipped into a Vietnamese sentence (fast typing) — there
  is now an automated test blocking it.

## 1.0.0 — 2026-09-10 · First release

### Added
- **6 skills** (`skills/`): `clean-code` (the main one) + `clean-code-review`, `clean-code-naming`,
  `clean-code-refactoring`, `clean-code-error-handling`, `clean-code-formatting-hooks`.
  `name`/`description` frontmatter per the Agent Skills standard; the main skill ships **11
  references**, 2 checklists, 3 templates and 1 "Wrong → Right" snippets file (4 languages).
- **`tools/cc-scan.py` v1.0.0** — a Clean Code scanner, Python stdlib only, **20 rules**, covering
  TS/JS/Python/Java/Kotlin/Scala/C/C++/C#/Go/Rust/PHP/Swift/Ruby; text and JSON output, an exit code
  for CI, a baseline, `cc-scan:allow`, and a config file.
- **`tools/tests/run_checks.py`** — 53 checks run for real against fixtures (`messy/` 7 files,
  `clean/` 5 files), covering: rule coverage, false-positive resistance, line location, the
  baseline, the config, the exception mechanism, the CLI, and dogfooding.
- **`tools/demo/`** — the same business feature in 2 versions: `legacy-*` (72/100, 4 errors) vs
  `order-service.ts` + its tests (100/100, 0 findings) + a README analysing each violation.
- **`configs/`** — ESLint 9 flat config + Prettier + tsconfig (JS/TS); ruff/black/mypy
  `pyproject.toml` + `lint.sh` + `Makefile` (Python); Checkstyle `checkstyle.xml` + maven/gradle
  snippets (Java); `.golangci.yml` (Go); GitHub Actions + GitLab CI + pre-commit + lint-staged +
  `.editorconfig` + a Sonar quality gate (CI).
- **`playbook/`** — a 9-session curriculum following the standard's own tree (why clean code →
  naming → functions → comments → formatting → objects/data → errors → SOLID-DRY-KISS-YAGNI → code
  health & workflow) + appendix A (30 onboarding questions with answers) + appendix B (a 5-level
  maturity model, a 100-point rubric for a module, a 90-day plan).
- **`prompts/`** — a pack of 10 prompts (reviewer, name finder, extract function, magic numbers,
  SOLID audit, error handling, comment cleaner, testability, legacy plan, junior mentor, PR
  description) each with a way to verify the output.
- **`tools/SELF_REVIEW.md`** — the tool read by itself: 4 groups of declared debt with their reasons
  + the list of debt still open (AST, fuzzy duplicates, diff-aware scanning).

### Verified in this release
- `tools/tests/run_checks.py` → **53/53 PASS**.
- ESLint 9.39.5 + typescript-eslint 8 + Prettier 3 on `configs/js` → the good sample 0 problems,
  the bad samples 10 problems; `prettier --check .` clean.
- ruff 0.16.6 + black 26.5.1 + mypy 2.3.1 on `configs/python` → `orders_good.py` clean,
  `orders_bad.py` 39 errors; `lint.sh` runs end to end (exit 0/1 correct).
- Checkstyle 10.21.4 on `configs/java` → the config runs; bad 8 violations, good 0.
  (`AvoidCatchingThrowable` had to be dropped — the module does not exist in 10.x.)
- The YAML in `configs/ci/*.yml` parses.
- `golangci-lint` **not** run: no Go toolchain in the sandbox (stated in `configs/go/README.md`).

### Fixed while building it (lessons learned, now reflected in the docs)
- `COMMENTED_CODE` initially reported 279 lines falsely (it examined the code line, not just the
  comment part) → the scope was narrowed to the comment.
- `EMPTY_CATCH` initially treated `except X: print(e)` as swallowing the error, and ignored
  indentation (it used the stripped string) → `indent_of()` fixed, and `filler` reduced to
  `pass`/`...`/`noop`.
- `MAGIC_NUMBER` initially reported `const VAT_RATE = 0.1` and `{"maxLine": 120}` → constant
  declarations are now spared (UPPER_SNAKE, `static final`, Go `var/const`, dict keys).
- `NEGATIVE_CONDITIONAL` initially reported the guard clause `if (!a || b.length < MIN)` → it now
  only catches **double negation**.
- `DUPLICATE_BLOCK` reported the same block 3 times (sliding window) → overlapping windows are
  merged.
- `BLOCK_COMMENT` misfired on a regex containing `/*` inside a string → only lines starting with
  `/*` count.
