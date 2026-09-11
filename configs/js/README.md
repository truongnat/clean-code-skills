# JS/TS configuration (ESLint 9 + Prettier 3)

`eslint.config.js` maps the `clean-code` sections onto rules; `.prettierrc.json` owns layout.
The split is deliberate: **Prettier decides how it looks, ESLint decides how it is built.**

| Skill concern  | Rule                                                                                           | Setting here                                                                                                                      |
| -------------- | ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| 3 · functions  | `max-lines-per-function` / `max-params` / `complexity` / `max-depth`                           | 40 / 3 / 10 / 3 (`skipBlankLines`, `skipComments` on; `IIFEs: false`)                                                             |
| 3 · one job    | `max-statements`                                                                               | 20                                                                                                                                |
| 2 · naming     | `no-restricted-syntax` selectors                                                               | no 1-letter names; no `Data Info Manager Handler Processor Util(s) Object Obj Thing Stuff Foo Bar` suffixes; no `isNotX` booleans |
| 4 · comments   | `no-commented-out-code`-style via `cc-scan`, `capitalized-comments` off                        | see `cc-scan`                                                                                                                     |
| 5 · formatting | delegated entirely to Prettier                                                                 | `printWidth: 120`, `singleQuote: false`, `trailingComma: "all"`                                                                   |
| 6 · structure  | `@typescript-eslint/no-floating-promises`, `consistent-type-imports`, `no-explicit-any` (warn) | needs type info                                                                                                                   |
| 7 · errors     | `no-empty` (catch not allowed), `require-atomic-updates`, `no-useless-catch`                   | —                                                                                                                                 |
| 9 · hygiene    | `no-console` (warn), `no-debugger`, `no-warning-comments`, `no-nested-ternary` (error)         | TODO without a ticket is a warn                                                                                                   |
| 11 · tests     | overrides relax `max-lines-per-function` and `max-params` for `*.test.ts`                      | clarity beats brevity in a test                                                                                                   |

## Install and run

```bash
cp eslint.config.js .prettierrc.json /path/to/your/repo/
npm i -D prettier eslint @eslint/js typescript-eslint globals
npx eslint . --max-warnings=0        # the config is flat-config, ESLint 9+
npx prettier --check .
```

`node_modules` is **not** part of this pack (it never should be): if you copied the folder instead of
cloning it, run `npm ci` here first — the sample check below needs `@eslint/js` and
`typescript-eslint` present. The same applies to `configs/python`: `bash lint.sh` builds its own venv
when the tools are missing.

## Verified samples (run in this folder)

```bash
npx prettier --check .          # -> All matched files use Prettier code style!
npx eslint samples/good-example.ts                       # -> 0 problems
npx eslint samples/*.ts         # -> 10 problems (4 errors, 6 warnings)
```

| File                       | Purpose                                                                  | Measured                                                                                                                                   |
| -------------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `samples/good-example.ts`  | the compliant shape: small functions, guard clauses, unit-suffixed names | **0 problems**                                                                                                                             |
| `samples/bad-example.ts`   | long function, params, nesting, `console.log`, `any`, over-wide line     | **6 problems** (3 errors, 3 warnings): `max-params`, `max-depth`, `no-console`, `no-restricted-syntax`, `no-explicit-any`, `max-len`       |
| `samples/bad-structure.ts` | the design smells a size scanner cannot see                              | **4 problems** (1 error, 3 warnings): `no-restricted-syntax` on `BadDataManager`, `max-params` (4), `max-statements` (32), `max-depth` (4) |

Total across the three samples: 10 problems (4 errors, 6 warnings) — and the error message text is
English, so it is pasteable into a PR: `No Data/Info/Manager/Util/Object names - they carry no meaning.`

Note: this pack's ESLint config needs `projectService` for the type-aware rules (already configured).
If you move the config into a repo without a `tsconfig.json` covering `src/`, those rules degrade to
silence — that is the first thing to check when "the type rules are not firing".

## Definition of done for a JS/TS setup

- [ ] `eslint.config.js` + `.prettierrc.json` committed at the repo root, not per-package
- [ ] `formatOnSave` + `.editorconfig` so the editor agrees with CI
- [ ] `lint-staged` runs `prettier --write` + `eslint --fix` on staged files only (sub-second hook)
- [ ] CI: `prettier --check .` and `eslint . --max-warnings=0`, both blocking
- [ ] `--max-warnings=0` reached by config, not by adding `eslint-disable` lines; any exception names
      the rule and the reason, and lives on one line
