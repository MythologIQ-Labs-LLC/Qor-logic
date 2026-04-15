# Doctrine: Test Discipline

**Source**: Phase 12 v1+v2 audit lessons (Ledger #22, #23; Shadow Genome #7, #8). Surfaced after the Governor wrote tests after code, then introduced flaky test (collision-resistant), then hardcoded a test against live ledger Entry #20.

**Goal**: Tests are honest; tests are first; tests are reliable. A green test suite means something only when these three properties hold.

## Rule 1 — Tests before code

**TDD is the default.** Write the failing test first, run it (red), then write minimum code to make it green.

**Allowed exception: regression coverage backfill.** When testing modules that pre-exist the test infrastructure (e.g., `ledger_hash.py` written in Phase 1.5; tests added in Phase 12), classify explicitly:

> Track classification: regression coverage backfill (not TDD; module pre-existed Phase X).

The classification must appear in the plan AND in the commit message. Without it, "I'll write the test after" is the failure mode this rule prevents.

## Rule 2 — Definition of done = green tests

A piece of work is done when:

1. The tests for the new behavior exist
2. The tests are running in the suite
3. The tests pass
4. The tests have been run **at least twice in a row** locally (to confirm determinism)

If any of (1)-(4) is missing, the work is **not done** — it's a draft. Drafts can be committed (work in progress) but must not be claimed as complete.

For workflow bundles and skills (markdown-only): the doctrine compliance test (`tests/test_skill_doctrine.py`) is the test. Updating a SKILL.md without re-running this test is incomplete.

## Rule 3 — Tests must be reliable

A test is **reliable** when:

- **Deterministic**: same inputs produce the same outputs across runs. No `random.random()` without `random.seed()`. No `datetime.now()` without an injected clock.
- **No live-state coupling**: tests don't assert against the contents of files that change outside the test (e.g., the real `docs/META_LEDGER.md` Entry #20 chain hash). Use synthetic inputs with computed expected values.
- **No external network**: tests don't call out to `gh`, `git push`, `curl`, etc. without mocking. Subprocess calls must be patched in tests.
- **No order dependency**: a test must pass when run alone (`pytest tests/test_X.py::test_Y -v`) and as part of the full suite. No relying on side-effects of other tests.
- **Probabilistic asserts use safety margins**: birthday-paradox style assertions (e.g., collision resistance) must allow for the actual statistical distribution. "Zero collisions in 10,000 24-bit draws" is wrong; "≤ 1 collision in 500 draws" matches the math.

## Anti-patterns (verified instances)

| Anti-pattern | Where seen | Lesson |
|---|---|---|
| Hardcoded live-state coupling | `test_chain_hash_recomputable_for_entry_20` (Phase 12 v1) | Never assert against a specific ledger entry; compute expected via the algorithm with synthetic inputs |
| Tight birthday-paradox assertion | `test_session_id_collision_resistant` original (Phase 3) | Probabilistic asserts need safety margins matching the actual distribution |
| Misnamed atomicity test | `test_write_manifest_atomic_write` (Phase 12 v1) | If the test only verifies a function is called, name it that way; "atomic" implies behavior, not invocation |
| Combined-assertion test name | `test_workflow_dir_optional_or_compliant` (Phase 12 v1 V-4) and `test_verify_handles_malformed_entry_header` (Phase 12 v2 V-B) | One test, one assertion subject. If the docstring needs "OR" or "AND", split |
| Default-arg captured at definition | `shadow_process.append_event(log_path=LOG_PATH)` (Phase 4) and `session.current(marker=MARKER_PATH)` (Phase 10) | Default args are bound at function-definition time; monkeypatching the module attribute later doesn't take effect. Use `marker=None` + resolve dynamically |
| Test written after the code | Phase 12 Track B (regression coverage backfill — acceptable but classify explicitly) | If it's not TDD, say so |

## Verification mechanisms

- **Doctrine tests** (`tests/test_skill_doctrine.py`) catch documentation-side drift
- **Reliability runs**: before committing a new test, run `pytest <new_test_file> -v` twice. Both must pass identically.
- **Order isolation**: occasionally run `pytest tests/ --random-order` (requires `pytest-randomly`) to catch order dependencies. Not in default CI; periodic check.
- **Coverage**: `pytest --cov=qor.scripts` shows untested branches. Critical infra (`ledger_hash`, `gate_chain`, `session`, `shadow_process`) should approach 90%+ coverage.

## Failure recovery

When a test goes flaky in CI:

1. Reproduce locally with the same seed (if applicable)
2. Don't `pytest --rerun-failures` to mask it
3. Find the source of nondeterminism (random, time, file system order, network)
4. Either eliminate (preferred) or quarantine with `@pytest.mark.flaky` + a tracking issue

When a test starts hardcoded-coupling another module's state:

1. Identify what live-state the test depends on
2. Replace with synthetic input + computed expected
3. If the test was specifically meant to validate the live state (e.g., "verify ledger Entry #20 didn't change"), move it to a separate `tests/integration/` suite that's opt-in

## Update protocol

When new test failure modes emerge, append to the Anti-patterns table with where-seen citation. The doctrine grows with the project's failure history; it does not shrink.
