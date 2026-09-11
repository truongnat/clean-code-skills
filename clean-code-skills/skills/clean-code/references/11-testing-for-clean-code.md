# 11 · Testability — tests are what *allow* you to keep code clean

> Without tests, clean code is a good intention. Every refactoring needs a safety net, and that net
> must run in under five seconds for one module or people will stop running it.

## 1. A test is a design review

| Design that is easy to test | What it forces on production code |
|---|---|
| dependencies arrive through the constructor/parameter | no `new SmtpClient()` in the middle of logic |
| pure functions for computation | tests need no DB, network or wall clock |
| a clear boundary (domain vs infrastructure) | fakes only at the edge, never inside a rule |
| one job per function | one test verifies exactly one decision |
| value objects with validation in the constructor | impossible states are unrepresentable, so untestable branches disappear |

If you **cannot write a test** for a function, it is almost certainly doing one of these:

| Blocker you feel | What the code is doing | The fix |
|---|---|---|
| "I have to start Postgres" | logic reaches for I/O directly | inject a port; keep the rule pure (`06` §5, `12`) |
| "I have to sleep 200 ms" | time is read inside the function | inject `Clock`, use a fake timer |
| "I have to mock 6 module singletons" | dependencies are imported, not passed | constructor params / function args |
| "The only assertion I can make is on a log line" | the function returns nothing and mutates | return a value; assert on the outcome |
| "To test the discount I must also build a user, an order and a cart" | the concept is tangled | extract the policy, give it its own small input |

That is not "testing is hard". That is a design bug with a reliable detector, and it is why this
chapter is last in the sequence: **testability is the sum of the other eight chapters.**

## 2. The shape of a good test

```ts
// Arrange (build data with a builder, not a 14-field literal)
// Act    (exactly ONE action)
// Assert (verify the behaviour, not the implementation)
it("shipping is free from 500k", () => {
  const order = anOrder().withSubtotal(Money.vnd(500_000)).build();

  const fee = shippingFeeOf(order);

  expect(fee).toEqual(Money.zero("VND"));
});
```

Five laws:
1. **One behaviour per test.** If the name needs "and", split it. (Several assertions are fine when
   they describe one outcome: total + currency + line count of *one* priced order.)
2. **Assert through the public API.** Calling a private method binds the test to the implementation,
   and then the test is what blocks the refactoring.
3. **Do not assert on logs, rendering or internals** — unless the log *is* the contract (audit
   trails), in which case test the logger explicitly and say so in the name.
4. **No sleep, no randomness, no wall clock**: inject `Clock`/`Random(seed)`, freeze time, and make
   the suite re-runnable in any order.
5. **The name is the specification.** A reader of the test list should learn what the system
   guarantees, without opening the source. If your report reads `test1, test2, testPlaceOrder`,
   you have executable code and no documentation.

Given/When/Then is the same skeleton with more words — use it when the arrangement is long
(`given a VIP customer with two pending orders, when the nightly job runs, then …`), and plain AAA
for the small pure cases where the extra ceremony only adds height.

## 3. A pragmatic pyramid for a modern backend + front end

```text
        E2E (Playwright / instrumented)                5-10%  slow, brittle -> the few lifelines only
      Integration (repository + Testcontainers)        15-20%  real DB/queue; do not mock what you do not own
    Unit (domain, policies, pure functions)            70%     millisecond-level; the lane you refactor inside
```

Two inversions to avoid:
- **inverted pyramid** (mostly E2E): you cannot refactor, because a red test tells you nothing about
  which layer broke, and the suite costs 40 minutes so it runs only in CI;
- **no integration lane at all**: every green unit test is an illusion about your schema, your
  driver and your serialisation. Mocking the database tests your mock.

Where the middle lane is expensive (many services), add **contract tests** between them: they buy
integration confidence at unit speed and they fail with a readable diff (`13-architecture-patterns.md`).
Budget the speed: the unit lane must finish in ~2 minutes or developers stop running it locally, and the
feedback arrives when the author has already moved to another task, which is when it stops
correcting behaviour.

## 4. Error paths and boundaries — where clean code shows its worth

```py
# ✅ one line of data per case - adding a case never edits the logic
@pytest.mark.parametrize("amount,expected_fee", [
    (Decimal("0"), Decimal("0")),
    (Decimal("499999"), FLAT_SHIPPING_FEE),
    (Decimal("500000"), Decimal("0")),
    (Decimal("500001"), Decimal("0")),
])
def test_shipping_fee_boundary(amount, expected_fee):
    assert shipping_fee_for(subtotal=amount) == expected_fee

def test_charge_when_gateway_times_out_wraps_as_unavailable_and_is_retryable():
    gateway = FakeGateway(failures=[TimeoutError()])
    with pytest.raises(GatewayUnavailable) as exc:
        charge(order_with(Decimal("10.00")), gateway)
    assert exc.value.retryable is True
    assert "timeout" in str(exc.value.__cause__)        # the chain survived the wrap
```

```go
// table-driven is the same idea, natively: cases are data, the loop is the harness
cases := []struct{ name string; subtotal int64; wantFee int64 }{
    {"below threshold", 499_999, flatFee},
    {"at threshold", 500_000, 0},
    {"zero", 0, 0},
}
for _, c := range cases {
    t.Run(c.name, func(t *testing.T) {
        if got := shippingFee(c.subtotal); got != c.wantFee {
            t.Fatalf("shippingFee(%d) = %d, want %d", c.subtotal, got, c.wantFee)
        }
    })
}
```

The minimum case list for **every** business function:
- [ ] the ordinary value (happy path)
- [ ] boundaries: `0`, threshold `-1 / +0 / +1`, empty list, one element, unicode and Vietnamese
      diacritics in strings (they break naive length checks)
- [ ] junk input: `null`/`undefined`, `NaN`, negatives, `31/02`, oversized payload
- [ ] third-party failure: timeout, 5xx, wrong-shape payload, slow response
- [ ] idempotency: call it twice — does it create two results?
- [ ] order sensitivity: if the function cares, swap two inputs and assert the difference
- [ ] one **property** case: `|fee| <= subtotal`, or "pricing never depends on map iteration order"
      (fast-check / hypothesis find the input you would not have typed)

## 5. Builders instead of copy-pasted 20-line objects

```ts
// ❌ every test carries a 20-line literal; changing one field means touching 40 files
const order = { id: "1", status: "PAID", amount: 100, currency: "VND", items: [...], /* … */ };

// ✅ a test declares only what makes it different - which is the behaviour under test
const order = anOrder({ status: "PAID", items: [aLine({ qty: 3 })] });
```

```py
@dataclass(frozen=True)
class OrderBuilder:
    total: Decimal = Decimal("100000")
    currency: str = "VND"
    items: tuple[LineItem, ...] = ()

    def with_total(self, total: Decimal) -> "OrderBuilder":
        return replace(self, total=total)

def an_order(**over) -> Order: return Order(**{**asdict(OrderBuilder()), **over})
```

Builder discipline, or this becomes its own smell:
- defaults must produce a **valid** object; a builder that can assemble an impossible state has
  moved the bug into the test;
- a `with*` method per axis the tests actually vary — not 30 setters (that is the anemic entity
  again, in test clothes);
- no conditional logic in the builder (`if self.currency == …`). Tests need to be dumb to be
  trustworthy; two near-duplicate builders beat one clever one;
- put builders in `test/support/`, not in production source, and let the linter see them as test
  code (looser thresholds, no coverage requirement).

## 6. Against fake tests (and how to measure them)

```bash
# 1) do the tests actually exercise the code? -> mutation testing
npx stryker run src/billing                      # JS/TS
mutmut run --paths-to-mutate=src/billing         # Python

# 2) is the lane fast enough to be used? (a module's unit suite should stay well under 5s)
pytest -q --durations=10
npx vitest run --reporter=json | jq '.testResults | map(.assertionResults | length) | add'

# 3) ratio of test files to source files (cc-scan's LOW_TEST_RATIO info rule)
python3 tools/cc-scan.py . --json | jq '.findings[] | select(.rule=="LOW_TEST_RATIO")'

# 4) coverage on what you actually changed (the only coverage number worth gating)
npx vitest run --coverage && diff-cover coverage.xml --compare-branch=origin/main
```

Reading the numbers:
- **mutation score < 40%** on a critical module means the tests mostly execute code without
  constraining it. Aim higher where it matters (policies, money, auth) and ignore it in glue;
- **coverage ≥ 80% on new code**, not on the repo — a 100%-coverage target on legacy buys tests for
  constructors and a fake sense of safety;
- **any test that passes when you delete the implementation** is not a test: make "delete the body
  and see what fails" a 5-minute monthly ritual on one module, and write down what slipped.

Flakes have a policy, not a prayer: quarantine with an expiry (`@pytest.mark.flaky` behind a ticket,
`test.skip('FLAKE-123, remove by 2026-10-01')`), fix within three working days, and never re-run a
suite until it happens to pass — an ignored flake becomes a culture where red means nothing.

## 7. Layout and naming of the suite

```text
src/billing/pricing.ts              test/billing/pricing.test.ts          <- mirror the path
src/domain/money.py                 tests/unit/test_money.py
internal/order/pricing.go           internal/order/pricing_test.go         <- same package, white-box allowed
```

- one test file per production file, in the mirrored folder — "where is the test for X?" must be
  answerable without searching;
- test names are sentences about behaviour; a report that reads as a specification is the goal;
- no `test2`, no `_again`, no `_2`; a second case gets a name that says what differs;
- factories live in `test/support`, fixtures in `test/fixtures/data/*.json` and are **production
  shaped** (50 anonymised real orders, not three invented ones);
- snapshot files are committed (a snapshot diff is a reviewable artefact), but no snapshot for
  anything the author cannot describe in a sentence.

## 8. Making the suite someone wants to run

- **fast and offline**: no network in unit tests, no sleep, no full-stack boot; if the whole unit
  lane exceeds 2 minutes, that is a refactoring ticket like any other;
- **deterministic**: fixed seeds, frozen clocks, randomised *order* enabled — a test that depends on
  its neighbour is a bug in the test;
- **readable failures**: assert on whole values where the diff helps (`toEqual(receipt)`), include the
  input in the failure message (`t.Fatalf("shippingFee(%d) = %d, want %d", …)`);
- **watch mode by default** in docs and onboarding (`vitest --watch`, `pytest-watch`, `go test -run`
  with a package pattern) — the loop that changes behaviour most is the one with the shortest delay;
- **no "helpful" output noise**: a green suite prints almost nothing; a red one prints exactly the
  failing cases. If people scroll past your test output, it has stopped teaching.

## 9. Testing this pack itself (and the lesson for your repo)

The tools enforce the standard, so they are held to it — and they are tested by **behaviour, on real
files, with no mocks and no re-implemented logic**:

```bash
python3 tools/tests/run_checks.py | tail -1       # → 60/60 checks passed
python3 tools/tests/run_arch_checks.py | tail -1  # → 30/30 arch checks passed
python3 tools/cc-scan.py tools/tests/fixtures/clean --fail-on error   # must exit 0 - the FP guard
```

`run_checks.py` runs the real binary over `tests/fixtures/messy` (all 20 rules must fire) and
`tests/fixtures/clean` (**zero** findings — the false-positive guard), then checks baseline,
config scoping, the allow-comment's exact range and the CLI surface. `run_arch_checks.py` does the
same for the six structure rules on four fixture trees.

The lesson transfers directly: **a rule with no fixture dies within two weeks of false positives.**
If you want a rule to survive in your repo, give it (1) a file that must violate it, (2) a file
that must not, and (3) an assertion on the count. Those 15 lines of test are the reason the rule is
still enabled in a year — and the reason someone can prove the tool, not their mood, made the call.
A third lesson from writing them: the *clean* fixture is what earns the right to trust the dirty
one's numbers. A checker that only ever reports problems is unfalsifiable, and people correctly
ignore unfalsifiable things.

## 10. Definition of done for tests (a rubric)

| Level | You are here when |
|---|---|
| **Bronze** | the new code runs in at least one test; the suite is green and fast |
| **Silver** | each new behaviour and each new error branch has a named test; boundaries tested; no sleeps, no real clock, no network; asserts go through the public API |
| **Gold** | break the implementation deliberately and watch the right test fail (mutation-lite); the test names read as the module's specification; a new joiner can run one lane in < 2 s and knows exactly where to add the next case |

Aim Silver on every PR, Gold on the modules that move money or data. Bronze is not a destination —
it is the state in which the next person's refactor becomes dangerous.
