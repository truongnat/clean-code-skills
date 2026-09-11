# CHANGELOG

## 1.1.0 — 2026-09-10 · Clean architecture, patterns, and the move to English

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
- Still pending: `prompts/00..10` + its README, comments inside `tools/tests/fixtures` and
  `tools/demo`, `tools/SELF_REVIEW.md`'s older half, and this file's 1.0.0/1.0.1 entries (631 lines
  total, listed in §*Pending* below). No rule, threshold or command changes in that pending set.

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
- Everything quoted below was re-run on the release date; the toolchains used are ruff 0.16.6,
  black 26.5.1, mypy 2.3.1, import-linter 2.15, ESLint 10.10.0 + Prettier 3.6.2,
  Checkstyle 10.21.4 on OpenJDK 11, and ArchUnit 1.3.0.
- `python3 tools/cc-scan.py .` from the pack root scans 32 code files in ~0.15 s (before the fix in
  §"Fixed" of 1.0.1 it crawled `configs/js/node_modules`: 2163 files, 50 s).
- `python3 tools/arch-scan.py configs/architecture/demo/python` → `82.0/100`, 3 errors; the same
  folder under import-linter → 2 contracts BROKEN. Both tools report the same two edges.

### Pending — English conversion (tracked, no behaviour change)

Converted so far: root `README.md`, `INSTALL.md`, `tools/README.md`, `tools/cc-scan.py` (20 rule
descriptions, every message and hint, CLI help), `tools/check_links.py`, `tools/tests/run_checks.py`
(60 labels), **all 5 sub-skills** (`clean-code-naming`, `-refactoring`, `-review`,
`-error-handling`, `-formatting-hooks`) rewritten in English **and expanded**, `references/01–11`
(all nine chapters plus smells and tests - translated **and** expanded: rule-to-enforcement tables, worked refactors, per-language recipes,
a value-object cookbook, an error taxonomy, an anti-pattern table with the tool that catches each
one, and exercises), `configs/js` (ESLint messages
included), `configs/python`, `configs/java` (Checkstyle messages + README), `configs/ci` (comments and
CI step names), `configs/go` (README + demo comments).

Remaining, next passes, in this order (32 files · 631 lines):

| Group | Files | Lines |
|---|---|---|
| prompts (00–10 + README) | 12 | 409 |
| tools: fixtures, demo comments, SELF_REVIEW | 16 | 139 |
| CHANGELOG 1.0.0 / 1.0.1 entries | 1 | 78 |
| intentional Vietnamese examples (glossary, bad code) | 3 | 5 |

Nothing in the pending set changes a rule, a threshold or a command; it is prose only. Numbers
quoted inside those files were re-checked and corrected anyway (57/57 → 60/60 checks, Checkstyle
"7 violations" → 8 audit messages with its severity split, link count 184 → 202).

---

## 1.0.1 — 2026-09-10 · Sửa lỗi escape hatch + tự kiểm tài liệu

### Sửa (lỗi thật, tìm thấy khi test tài liệu)
- **`cc-scan:allow` không áp dụng cho rule cấp dòng.** Tài liệu hứa "đặt comment ở dòng ngay
  trước vi phạm" nhưng code chỉ làm vậy với rule cấp hàm — nên `// cc-scan:allow MAGIC_NUMBER`
  ở dòng trên vẫn bị báo. Nay `allow` áp dụng cho **mọi rule**, phạm vi **dòng chứa comment +
  dòng ngay sau**, không lan toàn hàm (hàm `add()` trong `scan_file`).
- Xoá `configs/js/prettier.config.mjs` — trùng với `.prettierrc.json`, hai nguồn cấu hình cùng
  tồn tại là cách nhanh nhất để formatter của mỗi người một khác.
- `README.md`/`tools/README.md`: bỏ cam kết chưa kiểm chứng (bước CI "đã chạy") — giờ ghi rõ
  YAML được parse, còn lệnh bên trong chưa execute vì sandbox không có runner.

- **`configs/ci/.pre-commit-config.yaml` không parse được** (YAML `mapping values are not
  allowed here`, dòng 52): hai hook `bash -c '...'` nhiều dòng nhúng trong plain scalar. Thay
  bằng **một** hook `hygiene` gọi `hooks/check-hygiene.sh` — script này vốn đã phủ cả ba việc
  (log debug/.only, conflict marker, `System.out`/`fmt.Print`), giữ logic trong shell là cách
  duy nhất để local và CI dùng chung một hàng rào.
- Đường dẫn hook giờ tính từ gốc repo → mọi hướng dẫn cài (`INSTALL.md`, `playbook/05`,
  skill `clean-code-formatting-hooks`) đều thêm `cp -r configs/ci/hooks .`.

- **Quét nhiều path thì `ignoreDirs` bị mất hiệu lực.** `load_config()` dò file config trong
  *mọi* path được truyền, nên `cc-scan skills playbook prompts tools configs` nạp
  `tools/clean-code.config.json` (chỉ khai báo `ignoreDirs: ["fixtures","demo"]`) và **thay thế**
  danh sách mặc định → tool bò vào `configs/js/node_modules`, quét 2163 file trong 50 giây thay vì
  32 file trong 0.14 giây. Hai sửa: (1) `ignoreDirs` giờ được **nối** vào mặc định,
  (2) `ALWAYS_IGNORE_DIRS` là sàn không config nào gỡ được, (3) config chỉ nạp từ thư mục quét.
- **`cc-scan … | head` in traceback `BrokenPipeError`.** CLI đúng nghĩa thì phải im lặng như
  `grep`: khôi phục `SIGPIPE` mặc định ở đầu `main()` (POSIX; Windows bỏ qua).

### Đã kiểm chứng thêm
- 4 file YAML trong `configs/ci/` + `configs/go/` parse bằng `yaml.safe_load` → OK.
- `check-hygiene.sh` chạy thật trong git repo tạm: file bẩn (console.log + `<<<<<<<`) → **exit 1**
  và in đúng 2 dòng báo lỗi; file sạch → **exit 0**.
- `cc-scan.py` phiên bản 1.0.1; `tools/check_links.py` → 99 tham chiếu, 0 liên kết hỏng.

### Thêm
- `tools/check_links.py` (viết lại theo guard clause để đạt **100.0/100** khi `cc-scan` soi chính nó): — kiểm **92 tham chiếu tương đối** giữa các tài liệu (link `[..](..)`
  và đường dẫn trong backtick); exit 1 nếu có liên kết hỏng.
- `tools/tests/run_checks.py`: 7 test mới — phạm vi `cc-scan:allow` (cùng dòng / dòng liền
  trước / không lan / chỉ tắt đúng rule) và phạm vi `ignoreDirs` + config (3 test) → **60/60 PASS**.
- Fixture `suppressed.ts` viết lại hàm `mixed()` để chứng minh cả hai cách đặt comment.
- `.gitignore` ở gốc pack (node_modules, cache, report; ghi chú rõ baseline *nên* commit).
- Sửa 3 liên kết hỏng: reference về code smells trong `SKILL.md` (tên cũ `07-code-smells`, nay là `references/10-code-smells-refactorings.md`),
  tên file playbook trong `templates/adr-template.md` và `configs/java/README.md`.
- Sửa 7 chỗ lẫn ký tự CJK vào câu tiếng Việt (lỗi gõ nhanh) — giờ có test tự động chặn.

## 1.0.0 — 2026-09-10 · Phát hành đầu tiên

### Thêm
- **6 skills** (`skills/`): `clean-code` (chính) + `clean-code-review`, `clean-code-naming`,
  `clean-code-refactoring`, `clean-code-error-handling`, `clean-code-formatting-hooks`.
 frontmatter `name`/`description` theo chuẩn Agent Skills; skill chính kèm **11 references**,
  2 checklists, 3 templates, 1 file snippets "Sai → Đúng" (4 ngôn ngữ).
- **`tools/cc-scan.py` v1.0.0** — máy quét Clean Code, Python stdlib, **20 rule**,
  hỗ trợ TS/JS/Python/Java/Kotlin/Scala/C/C++/C#/Go/Rust/PHP/Swift/Ruby;
  output text/JSON, exit code cho CI, baseline, `cc-scan:allow`, config file.
- **`tools/tests/run_checks.py`** — 53 kiểm tra chạy thật trên fixture
  (`messy/` 7 file, `clean/` 5 file), phủ: độ phủ rule, chống false positive, định vị
  dòng, baseline, config, cơ chế ngoại lệ, CLI, dogfood.
- **`tools/demo/`** — cùng một nghiệp vụ ở 2 phiên bản: `legacy-*` (72/100, 4 error)
  vs `order-service.ts` + test (100/100, 0 finding) + README phân tích từng vi phạm.
- **`configs/`** — ESLint 9 flat config + Prettier + tsconfig (JS/TS); ruff/black/mypy
  `pyproject.toml` + `lint.sh` + `Makefile` (Python); Checkstyle `checkstyle.xml` +
  maven/gradle snippet (Java); `.golangci.yml` (Go); GitHub Actions + GitLab CI +
  pre-commit + lint-staged + `.editorconfig` + Sonar quality gate (CI).
- **`playbook/`** — giáo trình 9 buổi bám đúng cây chuẩn (ý nghĩa → naming → hàm → comment
  → format → đối tượng/dữ liệu → ngoại lệ → SOLID-DRY-KISS-YAGNI → code health & quy trình)
  + phụ lục A (30 câu kiểm tra onboarding, có đáp án) + phụ lục B (maturity model 5 cấp,
  rubric 100 điểm cho module, kế hoạch 90 ngày).
- **`prompts/`** — 10 prompt pack (reviewer, name finder, extract function, magic numbers,
  SOLID audit, error handling, comment cleaner, testability, legacy plan, junior mentor,
  PR description) kèm cách kiểm chứng output.
- **`tools/SELF_REVIEW.md`** — tự soi tool bằng chính tool: 4 nhóm nợ được khai báo
  có lý do + danh sách nợ còn lại (AST, duplicate fuzzy, diff-aware).

### Đã kiểm chứng trong lần phát hành này
- `tools/tests/run_checks.py` → **53/53 PASS**.
- ESLint 9.39.5 + typescript-eslint 8 + Prettier 3 trên `configs/js` → good sample 0 problem,
  bad samples 10 problem; `prettier --check .` sạch.
- ruff 0.16.6 + black 26.5.1 + mypy 2.3.1 trên `configs/python` → `orders_good.py` sạch,
  `orders_bad.py` 39 lỗi; `lint.sh` chạy end-to-end (exit 0/1 đúng).
- Checkstyle 10.21.4 trên `configs/java` → config chạy được; bad 8 violation, good 0.
  (Đã phải bỏ `AvoidCatchingThrowable` — module không tồn tại ở 10.x.)
- YAML của `configs/ci/*.yml` parse hợp lệ.
- `golangci-lint` **chưa** chạy: sandbox không có Go toolchain (ghi rõ ở `configs/go/README.md`).

### Sửa trong quá trình xây dựng (rút kinh nghiệm, đã phản ánh vào tài liệu)
- `COMMENTED_CODE` ban đầu báo oan 279 dòng (xét cả dòng code thay vì chỉ phần comment) → si phạm vi.
- `EMPTY_CATCH` ban đầu coi `except X: print(e)` là nuốt lỗi và bỏ qua thụt lề (dùng
  chuỗi đã strip) → sửa `indent_of()`, `filler` chỉ còn `pass/.../noop`.
- `MAGIC_NUMBER` ban đầu báo cả `const VAT_RATE = 0.1` / `{"maxLine": 120}` → tha cho
  khai báo hằng số (UPPER_SNAKE, `static final`, Go `var/const`, dict key).
- `NEGATIVE_CONDITIONAL` ban đầu báo cả guard clause `if (!a || b.length < MIN)` → chỉ bắt
  **phủ định kép**.
- `DUPLICATE_BLOCK` báo 3 lần cho cùng một khối (sliding window) → gộp window chồng lấn.
- `BLOCK_COMMENT` bắt nhầm regex chứa `/*` trong chuỗi → chỉ tính dòng bắt đầu bằng `/*`.
