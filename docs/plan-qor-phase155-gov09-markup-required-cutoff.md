# Plan: Phase 155 -- verify() fails a modern missing-markup entry (GAP-GOV-09)

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

None. Closes the GAP-GOV-09 half of GH #210 (audit Sprint A). `ledger_hash.verify()` silently `skipped += 1`
on any entry lacking canonical Content/Previous/Chain markup (and no Session-Seal fallback) and still
returns 0 -- so a modern chain entry written without its hashes would pass unnoticed. Research grounded
the real skipped set: 32 historical entries, numbers #1-11 and #68-122 (GENESIS / early AUDIT / GATE
TRIBUNAL / IMPLEMENTATION, pre-canonical-markup). Every entry above #122 already carries canonical markup,
so the modern convention is uniform (all entries chain-linked) -- no per-entry-type logic is needed.
Operator decision settled: a skipped (no-markup) entry numbered **>= 123** is a FAIL (binding), while
entries <= 122 stay grandfathered. Safe: the real chain still verifies clean (no current entry >122 is
missing markup); the floor only catches a FUTURE modern entry written without its hashes.

## Phase 1: markup-required cutoff in verify()

### Affected Files

- `qor/scripts/ledger_hash.py` - `verify()` gains `markup_required_cutoff: int = 123`; the skip branch FAILs at/after it.
- `tests/test_ledger_hash_markup_cutoff.py` (NEW).

### Changes

`verify(..., markup_required_cutoff: int = 123)`. In the orchestrator loop, the existing
`resolved = _resolve_recorded(body); if resolved is None: skipped += 1; continue` becomes:

```python
if resolved is None:
    if num >= markup_required_cutoff:
        print(f"FAIL Entry #{num}: missing canonical hash markup "
              f"(required at/after entry #{markup_required_cutoff})", file=sys.stderr)
        errors += 1
        last_failed = num
    else:
        skipped += 1
    continue
```

A modern (>= cutoff) markup-less entry now FAILs (and taints downstream, consistent with the other FAIL
branches); historical (< cutoff) entries still record as "Skipped ... non-verifiable markup". `verify()`
return code is unchanged for the real ledger (no entry >122 lacks markup). The CLI passes the default
(no new flag).

### Unit Tests

- `tests/test_ledger_hash_markup_cutoff.py`:
  - `test_modern_missing_markup_fails` - a synthetic ledger whose entry #123 carries no canonical hash markup makes `verify()` return 1 with a `FAIL Entry #123: missing canonical hash markup` line.
  - `test_historical_missing_markup_skipped` - the same markup-less entry numbered #100 (< cutoff) is skipped, not failed; `verify()` returns 0 (no other errors) and prints the "Skipped" summary.
  - `test_real_ledger_clean` - `verify(docs/META_LEDGER.md)` returns 0 (regression: the 32 historical skips stay grandfathered; no modern entry is missing markup).
  - `test_cutoff_boundary` - an unmarked entry exactly at `markup_required_cutoff` FAILs; one at `cutoff - 1` skips (off-by-one guard).

## Definition of Done

### Deliverable: D-markup-cutoff

- **D1**: a modern (>= cutoff) ledger entry without canonical hash markup can no longer pass `verify()` unnoticed; historical entries stay grandfathered.
- **D2**: `verify()` carries `markup_required_cutoff=123`; the skip branch FAILs at/after it; output + exit code unchanged for the real chain.
- **D3**: ledger SEAL records GAP-GOV-09 closed; #210 remainder is now GOV-05 + GOV-03.
- **D4**: `test_modern_missing_markup_fails` (exit 1 + named line) + `test_historical_missing_markup_skipped` (skip, exit 0) + `test_real_ledger_clean` + `test_cutoff_boundary`.

## CI Commands

- `python -m pytest tests/test_ledger_hash_markup_cutoff.py tests/test_ledger_hash.py tests/test_ledger_hash_validation.py tests/test_session_seal_markup_recognition.py -q` -- new + chain-verifier net (run twice).
- `python -m pytest -q` -- full suite green.
