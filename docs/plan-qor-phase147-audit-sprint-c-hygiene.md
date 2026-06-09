# Plan: Phase 147 -- Audit Sprint C batch 1 (security + citation accuracy)

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

None. Implements the low-risk, high-value subset of Sprint C (GH #212) from the production-gap audit
(Entry #353, brief `docs/research-brief-deep-audit-production-gap-2026-06-09.md`). Scoped to security
hardening + documentation/citation accuracy. Deferred (logged in the decision record, continued in a
follow-on Phase 148 / Sprint A): GAP-CQ-02 (decompose `ledger_hash.verify()` -- risky chain refactor,
pairs with Sprint A), GAP-TEST-01/02/05-08 + GAP-TEST-10 (test-integrity hardening -- coherent
test-only cycle), GAP-CQ-04 (entry-heading regex centralization -- mechanical but touches 8 modules),
GAP-ARCH-01 (orphaned `pipeline_inversion_lint` -- a wire-or-remove decision, not a pure win),
GAP-ARCH-05 (README `--profile` example is valid; the unconstrained-namespace point is a design
question, not a doc bug), GAP-CQ-05/06/07 (cosmetic Razor extractions).

## Phase 1: session-id path-safety (GAP-SEC-04/05/07)

### Affected Files

- `qor/scripts/session.py` - add canonical `validate_session_id` (path-safety regex).
- `qor/scripts/orchestration_override.py` - validate before building `.qor/session/<sid>/`.
- `qor/scripts/cycle_count_escalator.py` - validate before reading `.qor/session/<sid>/escalation_suppressed`.
- `qor/scripts/check_shadow_threshold.py` - re-export the canonical validator (dedupe; keep its name).
- `tests/test_session_id_path_safety.py` (NEW).

### Changes

Add to `session.py`:
```python
_SESSION_ID_SAFE = re.compile(r"^[\w\-T:]+$")  # rejects '/', '\\', '.', traversal
def validate_session_id(session_id: str) -> None:
    if not session_id or not _SESSION_ID_SAFE.match(session_id):
        raise ValueError(f"invalid session_id (path-unsafe): {session_id!r}")
```
`orchestration_override._write_suppression_marker` and `record` call `session.validate_session_id(session_id)`
before building the path. `cycle_count_escalator._suppression_active` and `check` validate before the
marker path read. `check_shadow_threshold.validate_session_id` becomes `from qor.scripts.session import validate_session_id`
(behavior-preserving: the existing regex is identical).

### Unit Tests

- `tests/test_session_id_path_safety.py`:
  - `test_validate_rejects_traversal` - `validate_session_id("../evil")`, `"a/b"`, `"..\\x"`, `""` each raise `ValueError`; a real sid `"2026-06-09T0000-rsd351"` does not raise.
  - `test_record_rejects_traversal_sid` - `orchestration_override.record("../evil", ...)` raises `ValueError` and writes NO file outside `.qor/session/` (assert the traversal target does not exist after).
  - `test_suppression_active_rejects_traversal_sid` - `cycle_count_escalator._suppression_active("../evil", "ts")` raises `ValueError` (read-side).
  - `test_record_accepts_valid_sid` - a valid sid writes the marker under `.qor/session/<sid>/` and returns an event id (regression: the fix does not break the happy path).

## Phase 2: documentation + citation accuracy (GAP-CLI-02, GAP-ARCH-04, GAP-ARCH-03)

### Affected Files

- `docs/FEATURE_INDEX.md` - FX017 test path -> `tests/test_cli_module_dispatch.py`; FX013 source -> `qor/cli_handlers/compliance.py:107`.
- `README.md` - `verify-ledger [<path>]` -> `verify-ledger [--ledger <path>]`.
- `tests/test_feature_index_citations_resolve.py` (NEW).

### Changes

FX017 (`docs/FEATURE_INDEX.md:28`) currently cites `tests/test_skill_active_env.py` (which tests env
management, not module dispatch); correct to `tests/test_cli_module_dispatch.py` (the real behavioral
test, verified to exist). FX013 (`:24`) source `qor/compliance/enforce.py:73` points into the `enforce()`
body; correct to `qor/cli_handlers/compliance.py:107` (`do_enforce`, the actual `compliance enforce`
command handler). README `verify-ledger` takes `--ledger` (cli.py:185-188), no positional -- fix the example.

### Unit Tests

- `tests/test_feature_index_citations_resolve.py`:
  - `test_every_cited_test_path_file_exists` - parse FEATURE_INDEX rows; for each non-empty `Test path`, the file before any `::` resolves on disk. (Regression floor for the missing-file citation class; asserts a real property of the table, fails if a citation names a non-existent file.)
  - `test_every_source_file_exists` - each row's `file:line` source file resolves on disk.

## Definition of Done

### Deliverable: D-sprint-c-batch1

- **D1**: operator-supplied `session_id` cannot escape `.qor/session/` at any covered path-build site; FEATURE_INDEX/README citations resolve to reality.
- **D2**: `session.validate_session_id` raises on path-unsafe ids; `orchestration_override`/`cycle_count_escalator` call it before path construction; FX017/FX013/README corrected.
- **D3**: ledger SEAL records the Sprint C batch-1 closure (GAP-SEC-04/05/07, GAP-CLI-02, GAP-ARCH-04, GAP-ARCH-03); deferred items enumerated.
- **D4**: `test_record_rejects_traversal_sid` + `test_suppression_active_rejects_traversal_sid` (raise + no out-of-tree write); `test_record_accepts_valid_sid` (happy path); `test_every_cited_test_path_file_exists` + `test_every_source_file_exists` (citations resolve).

## CI Commands

- `python -m pytest tests/test_session_id_path_safety.py tests/test_feature_index_citations_resolve.py -q` -- new tests (run twice for determinism).
- `python -m pytest -q` -- full suite green.
