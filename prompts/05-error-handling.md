# 05 · Error handling designer — design the failure paths

```text
PROMPT
───
Design or repair the error handling for the code I paste. Language: [TS|Python|Java|Go].

Step 1 — Map the failures (print the table):
| call site | failure that can happen | kind (business/system/bad data) | what the caller does | handled correctly today |

Step 2 — Apply the 8 rules, point at each violation + the fix:
1 a specific domain exception, with data in the message (id, quantity) — never `Error("lỗi")`
2 never swallow: a catch must log / wrap with the cause / fall back + emit a metric / rethrow —
  pick one and say which
3 never catch bare Exception/Throwable; no `except: pass`; in Go no `_ = err`
4 preserve the cause EVERYWHERE you wrap (`{cause}` / `from err` / `new X(msg, e)` / `%w`)
5 keep `try` small, around the part that can actually fail; the happy path reads straight through
6 separate retryable from not: business 4xx does NOT retry; timeouts and 5xx DO (with a ceiling,
  backoff and jitter)
7 an idempotency key for every write that can be retried
8 map errors to HTTP/exit codes in EXACTLY ONE place (the adapter); 4xx = your fault,
  5xx = my fault + a requestId

Step 3 — Return:
- The exception classes to create (name + fields + a machine-readable code)
- A diff per commit (XS/S), each one ≤ 40 lines, with NO change to the public API
- Tests for the failures: one test per catch (timeout, 4xx, garbage payload, idempotency),
  in AAA form
- The places you CHOSE to let the error surface (fail-fast) and why that is safer than catching

If you find catch-then-ignore in the existing code: propose two options — (a) handle it properly,
(b) log + metric + TODO(ticket) — and state the risk of (b). Do not silently pick (b).

CODE:
[PASTE THE CODE]
───
```

## Minimum input

- the code **including the calls that can fail** — the boundary functions, not just the one you
  suspect. Step 1's table is built from call sites;
- **what the caller can do** about each failure (retry, show a message, give up). Error design is
  decided by the caller's options, not by the throw site;
- whether the errors are **already parsed by someone** — a client matching on `error.code` or on a
  message string. This is the constraint that turns "rename the exception" from XS into L;
- the **transport** (HTTP API, queue consumer, CLI, cron job), because rule 8 maps to a different
  target in each.

## Output acceptance criteria

- [ ] the table has a row per call site that can fail, including the ones already correct;
- [ ] every catch in the result does exactly one of: log, wrap-with-cause, fall back + metric,
      rethrow — and the answer says which;
- [ ] no `catch` was deleted to make a warning disappear;
- [ ] the cause is preserved at every wrap — grep the diff for `{ cause`, `from err`, `%w`;
- [ ] retryable and non-retryable are separated, and every retry has a ceiling;
- [ ] one test per new catch, asserting the **error type**, not a message string;
- [ ] the public API's error behaviour is unchanged, or the change is listed explicitly.

## Keeping it from inventing symbols

```text
Rules on evidence:
- Only map failures for call sites present in the pasted code. Quote the line for each row of the
  table.
- Do not invent error codes, exception classes or HTTP mappings that already exist elsewhere in my
  repo. If you propose a new exception, say so explicitly and tell me to run
  `rg -n 'class .*Error|class .*Exception' src` to check for a duplicate first.
- Do not assume a library's retry/timeout API. If the fix needs one, write the intent and mark the
  call `// API SHAPE UNVERIFIED — check the client docs`.
- Do not attribute a status code or an error contract to "the spec" unless I pasted it.
- End with: "Error paths quoted from the paste: N. New exception classes proposed: M (all marked)."
```

## Verifying the output (mandatory)

```bash
python3 ../tools/cc-scan.py . --json | jq '[.findings[] | select(.rule=="EMPTY_CATCH")]'   # must be []
npx eslint . --rule '{"@typescript-eslint/no-floating-promises":"error"}'
ruff check --select E722,TRY,S110,EM .
golangci-lint run --enable errcheck,wrapcheck,nilerr
```

The biggest risk with model-written error handling: it **removes** the `catch` to silence the
warning, or it changes an exception an external client is parsing. Make it list "which APIs changed
their error behaviour" and have it grep `throw|raise|errors.New` in the old code to compare.

Related: `../skills/clean-code-error-handling/SKILL.md` ·
`../skills/clean-code/references/07-error-handling.md` · `00-code-reviewer.md`
