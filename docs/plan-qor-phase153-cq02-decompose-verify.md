# Plan: Phase 153 -- decompose ledger_hash.verify() (GAP-CQ-02)

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

None. Follow-on to GH #210 (audit Sprint A). `ledger_hash.verify()` is ~118 lines (the audit's
largest-function / Section-4-Razor finding) with interleaved concerns: entry parsing, hash-markup
resolution (canonical fields vs Session-Seal fallback), placeholder detection, chain math, taint
propagation, and three tolerance branches (grandfathered / reconciled / legacy-math). This is a
**behavior-preserving refactor**: the same stdout/stderr lines and the same return code are produced.
The safety net is the 42 existing `verify()` assertions across 5 test files
(`test_ledger_hash` / `_reconciliation` / `_validation` / `placeholder_pattern_detection` /
`session_seal_markup_recognition`); no behavior change, so no tolerance/contract changes.

## Phase 1: extract resolution + classification helpers

### Affected Files

- `qor/scripts/ledger_hash.py` - extract two pure helpers from `verify()`; `verify()` becomes a thin orchestrator.
- `tests/test_ledger_hash_verify_helpers.py` (NEW) - direct unit tests for the extracted classification.

### Changes

Extract from `verify()`:

```python
def _resolve_recorded(body: str) -> tuple[str, str, str] | None:
    """Return (content_val, previous_val, recorded_chain) for an entry body, or
    None when it carries neither canonical Chain/Content/Previous markup nor a
    Session-Seal fallback (the 'skipped, non-verifiable' case)."""

def _classify_entry(num, content_val, previous_val, recorded, *, grandfathered, reconciled,
                    last_failed) -> tuple[str, bool, bool]:
    """Return (message, to_stderr, is_error) for one resolved entry: placeholder
    -> FAIL; prior failure -> TAINTED; chain-math OK -> OK; grandfathered /
    reconciled -> DISCLOSED_*; else FAIL. Pure (no I/O)."""
```

`verify()` keeps its parse loop and the `grandfathered`/`reconciled` set construction, then per entry
calls `_resolve_recorded` (skip + `skipped += 1` on None) and `_classify_entry`, printing `message` to
stdout/stderr per `to_stderr`, incrementing `errors` and updating `last_failed` when `is_error`. Output
bytes and the `return 1 if errors else 0` are unchanged.

### Unit Tests

- `tests/test_ledger_hash_verify_helpers.py`:
  - `test_resolve_recorded_canonical` - a body with canonical Content/Previous/Chain markup returns the three hex values; a body with neither markup nor a Session-Seal line returns None.
  - `test_classify_ok_and_fail` - a chain-consistent entry classifies OK (not stderr, not error); a math-mismatch entry classifies FAIL (stderr, error).
  - `test_classify_taint_after_failure` - with `last_failed` set, an otherwise-OK entry classifies TAINTED (stderr, error).
  - `test_classify_grandfathered_and_reconciled` - a math-failing entry in the grandfathered set -> DISCLOSED_GRANDFATHERED (not error); in the reconciled set -> DISCLOSED_RECONCILED (not error).

## Definition of Done

### Deliverable: D-verify-decompose

- **D1**: `verify()` reads as a thin orchestrator; the resolution + classification logic live in named, individually-testable helpers; behavior (output + exit code) is unchanged.
- **D2**: `_resolve_recorded` + `_classify_entry` exist as pure functions; `verify()` calls them; each helper is under the Razor limit.
- **D3**: ledger SEAL records GAP-CQ-02 closed; #210 advanced (remainder GOV-09/05/03).
- **D4**: the 4 new helper tests pass AND the 42 existing `verify()` assertions across the 5 ledger-hash test files stay green (behavior preservation).

## CI Commands

- `python -m pytest tests/test_ledger_hash_verify_helpers.py tests/test_ledger_hash.py tests/test_ledger_hash_reconciliation.py tests/test_ledger_hash_validation.py tests/test_placeholder_pattern_detection.py tests/test_session_seal_markup_recognition.py -q` -- new + the full behavior-preservation net (run twice).
- `python -m pytest -q` -- full suite green.
