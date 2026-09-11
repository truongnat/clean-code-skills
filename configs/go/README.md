# Go configuration (golangci-lint)

`.golangci.yml` maps the `clean-code` skill sections onto linters:

| Skill concern | Linter |
|---|---|
| functions stay short (section 3) | `funlen` (60 lines / 40 statements) |
| few branches (section 3, 8) | `cyclop`, `gocognit` (12) |
| guard clauses instead of nesting (section 3) | `nestif` |
| naming, no stutter (section 2) | `varnamelen`, `revive`, `stylecheck` |
| no swallowed errors (section 7) | `errcheck`, `wrapcheck`, `nilerr`, `bodyclose` |
| no magic values (section 2, 8) | `mnd` |
| layout (section 5) | `gofmt`, `gofumpt`, `wsl` |
| **layer direction (references/12)** | **`depguard`** — bans `internal/domain` → `infrastructure`, `domain` → `interfaces`, `domain` → `sql`/`gorm` |

## Run

```bash
brew install golangci-lint        # or: go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
golangci-lint run ./...

# use the skill's config from another repo
golangci-lint run -c "$PACK/configs/go/.golangci.yml" ./...

# suggested Makefile target
lint:
	gofmt -l . && test -z "$$(gofmt -l .)"
	golangci-lint run --timeout 3m
```

## Demo

```bash
cd demo && gofmt -l .            # bad.go is already unformatted
golangci-lint run ./...          # bad.go is expected to light up ~15 issues; good.go stays clean
```

The `~15` figure is **an expectation, not a measurement** — see the box below. What *is*
measured here is the language-independent scan of the same two files:

| Command (run from the pack root) | Result |
|---|---|
| `python3 tools/cc-scan.py configs/go/demo --fail-on none` | **90.5/100 (A)** · 1 error, 5 warnings, 2 info |
| `python3 tools/arch-scan.py configs/go/demo --fail-on none` | 95.0/100 (A), 0 errors, 5 info — the demo is a flat two-file folder, so most files are `UNCLASSIFIED_FILES` by design |
| `python3 tools/tests/run_arch_checks.py` (fixture `tools/tests/fixtures/layers/go`) | 30/30 — Go `import ( … )` blocks and module paths resolve through `rootPackages` |

## One finding `cc-scan` raises on the *good* demo, and why

`python3 tools/cc-scan.py configs/go/demo/good.go --fail-on none` → **98.8/100**, one warning:

```
14  warn  MAGIC_NUMBER   Magic number `0.9` in: `vipRate          = 0.9`
```

That is a **known limit of the heuristic, not a bug in the file**: `cc-scan` treats an assignment
to `UPPER_SNAKE` as "already named", and Go writes unexported constants in `camelCase`, so a
perfectly named Go constant still looks like a magic number. Two honest answers, pick one and
write it down:

```go
const vipRate = 0.9 // cc-scan:allow MAGIC_NUMBER — camelCase const; Go idiom, see configs/go/README.md
```

or add `"0.9"` to `magicNumbersAllowed` in your `clean-code.config.json` — repo-wide, visible in
`git log`, which is the better choice if this pattern repeats. Do not rename the constant
`VIP_RATE` just to please the scanner; that breaks Go style for a metric.

## Verification status — read this before trusting the file

This pack was authored in a sandbox **without a Go toolchain** (`go: command not found`), so
`.golangci.yml` and the two demo files were **never executed** here. Unlike JS (ESLint 9 +
Prettier 3 run), Python (ruff + Black + mypy run) and Java (Checkstyle 10.21.4 run), the Go
config is only structurally validated:

- verified: the YAML parses (`yaml.safe_load`), 36 linters enabled, 2 `depguard` rule sets, the
  two `issues.exclude-rules` entries intact;
- verified: `cc-scan`/`arch-scan` behaviour on the same `.go` files (rows above);
- **not** verified: that every linter name and setting matches your installed golangci-lint.

Linters and keys follow the golangci-lint **v1** schema. On v2 run `golangci-lint migrate`
against a copy and diff the result, or ignore the config and use `cc-scan`, which needs no Go
toolchain at all. If a name is unknown, golangci-lint fails loudly at startup
(`unknown linter: "x"`) rather than silently skipping — that is the check to watch for.
