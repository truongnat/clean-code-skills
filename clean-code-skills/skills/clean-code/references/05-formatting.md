# 05 · Formatting & layout — a debate that must be closed by a tool

> Every argument about tab/space, 2/4, semicolons is review time burning. This chapter exists so
> you **configure once and never discuss it again**.

## 1. Three dimensions of formatting

### 1.1 Horizontal

- **Hard limit**: 120 characters (JS/TS/Java/Go/C#), 88 in Python (Black's default).
- The real reason: diffs render side-by-side on GitHub/GitLab, and a 13" laptop puts the editor next
  to a terminal. Exceeding the width does not just look bad — it hides the second half of your line
  from the reviewer, which is usually the interesting half.
- Wrap with **one indent level**. The most common shape (JS/Java/Go):

```ts
// ✅ one parameter per line, closing bracket aligned
const shipment = await createShipment({
  orderId,
  address,
  carrier: Carrier.DHL,
  insurance: Insurance.none,
});

// ✅ long text: a multi-line template literal, not six concatenations
const message = `
  Order ${orderId} needs approval because the total of ${(amountVnd / 1_000_000).toFixed(2)}m
  is above ${formatVnd(APPROVAL_THRESHOLD_VND)}.
`;

// ❌ one line of 180 characters - or half-hearted wrapping across three indent levels
const shipment = await createShipment(orderId, address, Carrier.DHL, Insurance.none, PaymentMethod.COD, note);
```

Three shapes that fix 90% of over-wide lines:

```ts
// (a) a long condition -> name it, and the line becomes a sentence
if (order.status === OrderStatus.PAID && !order.isFullyShipped && order.paidAt < SHIPPING_CUTOFF) { … }
const canStillShip = (o: Order) => o.status === OrderStatus.PAID && !o.isFullyShipped;
if (canStillShip(order) && order.paidAt < SHIPPING_CUTOFF) { … }

// (b) a long chain -> one link per line, aligned left
const names = users.filter(isActive).map(u => u.name).sort();
const names = users
  .filter(isActive)
  .map((user) => user.name)
  .sort();

// (c) a long literal (SQL, JSON, regex) -> move it to where it reads well
const rows = await db.query(`
  SELECT id, amount_minor FROM orders
  WHERE status = 'PAID' AND created_at > $1
  ORDER BY created_at DESC LIMIT 50
`, [since]);
```

Do not hand-align columns with spaces to make `=` line up: the alignment is destroyed by the next
edit, and the diff of that edit now contains three unrelated lines. If alignment is information
(a truth table, a matrix), put it in a table literal with `// dprint-ignore` and a reason (§4).

### 1.2 Vertical — the part people skip, and the one that matters most

- **Blank lines are punctuation.** No blank lines and the function is a wall; too many and the
  relationships vanish. One blank line = "this is a step"; two = "this is a new area". Most
  formatters preserve one and collapse two — that is not a coincidence, it is the convention.
- **Keep related code adjacent.** A caller and the single-use helper below it read as one unit; a
  helper placed 200 lines away is a document with footnotes only. Same for `Money` next to
  `MoneyFormatter`, and for a test file mirroring the source path.
- **Declare once, in one place.** Module constants at the top; imports in one block; no
  mid-file imports, no "constants" scattered where they happen to be used first.
- **Files ≤ ~400 lines.** Past that, you are usually holding two modules that share a file, and
  the "order-down" reading (§2) stops working.

```py
# ❌ eighteen uninterrupted lines: the eye finds no step boundary
def sync_invoice(order):
    payload = build_payload(order)
    signed = sign(payload)
    try:
        resp = http.post(ENDPOINT, json=signed, timeout=TIMEOUT_SECONDS)
    except TimeoutError:
        metrics.increment("sync.timeout")
        raise InvoiceSyncTimeout(order.id) from None
    if resp.status_code >= 500:
        metrics.increment("sync.server_error")
        raise InvoiceSyncUnavailable(order.id, resp.status_code)
    if resp.status_code >= 400:
        raise InvoiceRejected(order.id, resp.text)
    receipt = Receipt.parse(resp.json())
    invoices.attach(order.id, receipt)
    return receipt

# ✅ the same code, with rhythm, and the block noise given names
def sync_invoice(order: Order) -> Receipt:
    """Pushes the invoice to the partner. Business failures -> specific exceptions;
    system failures -> the caller retries."""
    payload = sign(build_payload(order))

    response = post_or_wrap(order, payload)

    receipt = Receipt.parse(response.json())
    invoices.attach(order.id, receipt)
    return receipt
```

A useful self-test: **screenshot the function and squint.** What you can distinguish without
reading is the structure. If the blur is uniform, the function has no paragraphs, and paragraphs
are what make a 40-line function readable while a 20-line one is not.

### 1.3 Indentation and characters

| Decision | This pack's standard | Note |
|---|---|---|
| tab or space | **spaces** for JS/TS/Python/Java/C#; **tabs** for Go (gofmt) | do not fight gofmt, you will lose |
| size | 2 (JS/TS/CSS/YAML), 4 (Python/Java/C#/C++) | follow the language's formatter default |
| semicolons | whatever the language's formatter does (Prettier: yes; `standard`: no) | choose one, commit the config, stop debating |
| quotes | Prettier `singleQuote: false` for JS/TS; single quotes in Python | consistency beats taste |
| final newline | always | `end-of-file-fixer` handles it |
| LF vs CRLF | LF (`core.autocrlf=input` + `.editorconfig`) | even Windows-only repos |
| trailing whitespace | forbidden | `trim_trailing_whitespace` |

The floor for all of the above is `.editorconfig`, because it works in every editor and needs no
install; the formatter is the enforcer, and the CI check is the witness.

## 2. Source-file layout: a sequence a reader can follow

```text
1. (2-5 lines) module docstring: what THIS file is, and its scope.
2. imports, grouped: stdlib -> third-party -> internal (no star imports, no wildcards in Java).
3. module-level constants (UPPER_SNAKE) - the vocabulary of the file.
4. types / interfaces (define the data before the behaviour that reads it).
5. public functions and classes, highest abstraction first ("order-down rule").
6. private helpers directly under the place that uses them.
7. exports, if the language declares them at the end.
```

**Order-down**: parent above, children below, so the file reads top-to-bottom like a document.
That is also why files should be short — nobody reads a 900-line document from the top.

Two extras that pay: (a) if you feel the need for `// ─── Fees ───` section banners, the honest
move is usually two files, and the banner is the *diagnosis*, not the cure; (b) tests mirror the
source path (`src/billing/pricing.ts` → `test/billing/pricing.test.ts`) so a rename moves both.

## 3. Per-stack configuration (copy-pasteable)

| Stack | Formatter | Linter | Config shipped with the skill |
|---|---|---|---|
| JS/TS | Prettier (`printWidth: 120`) | ESLint 9 flat config | `configs/js/.prettierrc.json`, `configs/js/eslint.config.js` |
| Python | ruff-format or Black (`line-length = 88`) | ruff (`E,W,F,I,UP,SIM,RET,PL,C901,ERA,T20,…`) | `configs/python/pyproject.toml` |
| Java | spotless / prettier-java | Checkstyle | `configs/java/checkstyle.xml` |
| Kotlin | ktlint `-F` | detekt | `ktlint -F`, `detekt --config` |
| Go | gofmt + gofumpt | golangci-lint | `configs/go/.golangci.yml` |
| C# | `dotnet format` | StyleCop / `.editorconfig` | `.editorconfig` already included |
| polyglot | **dprint** if you want one tool everywhere | — | `.editorconfig` remains the common floor |

Editor settings that make this automatic (`.vscode/settings.json`, committed with the repo):

```json
{
  "editor.formatOnSave": true,
  "editor.rulers": [88, 120],
  "editor.insertSpaces": true,
  "files.eol": "\n",
  "prettier.enable": true,
  "editor.codeActionsOnSave": { "source.fixAll.eslint": "explicit" }
}
```

```bash
# once per repo: format everything, in its own commit ("style: format whole repo")
npx prettier --write . && npx eslint . --fix
ruff format . && ruff check --fix .
gofmt -w . && gofumpt -w .
```

**The format commit is never mixed with a feature PR.** Mixed, `git blame` dies and the reviewer
sees 900 indent changes instead of your logic. Follow it immediately with:

```bash
git rev-parse HEAD >> .git-blame-ignore-revs          # right after the format commit
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

Tell the team to run that one `git config` line once; otherwise `.git-blame-ignore-revs` silently
does nothing and someone will "fix" the file a second time.

## 4. When the formatter looks wrong, and what to do

| Symptom | Real cause | Correct response |
|---|---|---|
| Prettier splits a long SQL string into five unreadable lines | the SQL should live in a `.sql` file or a query builder | move the SQL; do not disable the formatter |
| A matrix/coordinate table is ragged | the formatter does not know the alignment is the meaning | `// prettier-ignore` + a one-line reason, or a `dprint` align plugin |
| Auto-format touches files you did not edit | whole-repo formatting inside a feature PR | `lint-staged` (staged files only); a separate `style:` commit |
| One file needs 60 ignores | the file is generated | mark the folder in the ignore config, not the file with comments |
| Teammate switches the editor off | the config is not committed | commit `.editorconfig` + the formatter config; put `--check` in CI |

An ignore is legitimate when it is **narrow, reasoned and rare**. Ten of them means the standard is
wrong, and changing the standard is cheaper than arguing per file.

## 5. Machine-checked (put it in CI)

```bash
python3 tools/cc-scan.py . --json \
  | jq '[.findings[] | select(.rule|test("LINE_TOO_LONG|MIXED_INDENT|TRAILING_WHITESPACE"))] | length'
npx prettier --check .          # exit 1 if anything is unformatted
ruff format --check .
test -z "$(gofmt -l .)" || echo "gofmt: $(gofmt -l . | wc -l) files off"
```

`LINE_TOO_LONG`, `MIXED_INDENT` and `TRAILING_WHITESPACE` in `cc-scan` exist mainly to catch code
that **slipped past the formatter** (an unformatted file, an editor with the plugin disabled, a
hand-resolved merge). With `prettier --check` in CI they sit at zero forever — that is the goal,
not the assumption.

## 6. Exercises

**Five minutes, alone**
1. Run your formatter with `--check` and count the files that fail.
2. If the count is > 0: make one `style:` commit, then add the `--check` to CI.
3. Open the longest file: should it be two? **Write the two file names down before you split.** If
   you cannot name both capabilities, do not split it yet.

**Thirty minutes, with the team**
1. Turn on `formatOnSave` + `.editorconfig` for everyone; fix only what the formatter complains
   about (one PR, no logic).
2. Add the CI check and the `.git-blame-ignore-revs` line to the onboarding doc.
3. Set the ratchet: `printWidth`/`line-length` and the `editor.rulers`, then agree in one sentence
   that **formatting comments are banned in review** — "the bot will handle it" is the only allowed
   reply to a style comment. After a month, count how many review comments were about style: it
   should be zero, and that number is the deliverable of this chapter.

## 7. Definition of done for the formatting work

- [ ] `.editorconfig` + one formatter config + one linter config committed, per language in use
- [ ] `format --check` (or `--lint-only`) runs in CI and blocks
- [ ] the repo-wide format commit is isolated and in `.git-blame-ignore-revs`
- [ ] hooks format staged files only; the hook is under ~3 s
- [ ] every ignore in the repo names a rule and a reason, and there are fewer than ~10 of them
- [ ] zero style comments in review for one full sprint
