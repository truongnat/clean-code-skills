# Architecture enforcement configs

Clean code governs the inside of a module. These files govern the outside: which module may know
about which. Same philosophy as the rest of the pack — a rule nobody can check is a suggestion.

| Tool | Stack | File | Checked in this repo? |
|---|---|---|---|
| `arch-scan.py` (this pack) | all languages | `tools/arch-scan.py` + `arch-scan.config.json` | **yes** — `python3 tools/tests/run_arch_checks.py` → 30/30 |
| import-linter | Python | `.importlinter` | **yes** — v2.15 run on `demo/python`, 2 contracts BROKEN → KEPT |
| ArchUnit | Java/JVM | `demo/java/src_check/ArchitectureCheck.java` | **yes** — compiled with JDK 11, exit 1 → exit 0 |
| dependency-cruiser | JS/TS | `.dependency-cruiser.cjs` | config parses as JS (`node --check`); the tool itself was **not** run here (no npm install of it) |
| go-arch-lint / golangci-lint depguard | Go | `../go/.golangci.yml` (`depguard` block) | **not run** — no Go toolchain in this sandbox |
| `ARCHITECTURE.md` | all | `ARCHITECTURE.md` (copy to repo root) | prose only; the CI checks above are what enforce it |

## Start here

```bash
# 1. describe your layers (or accept the defaults: domain / application / infrastructure / interface)
cp configs/architecture/arch-scan.config.json .

# 2. run it
python3 tools/arch-scan.py src --fail-on error

# 3. add the exact tool for your language to CI (see demo/ folders for a working example)
```

## What the layer ranks mean

`rank` is depth from the outside world: 0 = domain, higher = further out. A file may import a
layer of **rank ≤ its own** and nothing else. That single sentence is the dependency rule of
clean architecture, and `arch-scan` turns it into an exit code.

## When the tool disagrees with you

- **Framework import in the domain** that is genuinely a type-only/interface import (e.g.
  `fastapi.APIRouter` in a router in `interface/`): the guard only applies to layers named in
  `frameworkPackages` — usually `domain` and `application`.
- **Two tools, two verdicts**: the exact one (ArchUnit/import-linter) wins; `arch-scan` is a
  fast pre-compile heuristic over import lines. See its [known limits](../../tools/README.md).
- **Legacy that must stay**: `# arch-scan:allow UPWARD_DEPENDENCY — ticket ARCH-142`, one line,
  scoped to that import, and visible in review.
