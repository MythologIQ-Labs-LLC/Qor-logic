# Plan: reconcile.py reads the dialect accessor instead of indexing its groups

**change_class**: hotfix

## Open Questions

None. Mechanical fix; scope and direction are fully specified by GH #477.

## Phase 1: Route reconcile.py through ledger_dialect.hash_value

### Affected Files

- `tests/test_reconcile.py` - regression coverage for the bare-line (third)
  hash-value form on both call sites this phase fixes.
- `qor/scripts/reconcile.py` - `detect_residual` (`:44`) and
  `_recorded_chain_hash` (`:73`) stop indexing `match.group(1) or
  match.group(2)` and call `ledger_dialect.hash_value(match)` instead, matching
  the pattern `ledger_hash.py` already uses at its own equivalent call sites.

### Changes

`qor/scripts/reconcile.py`:

- Add `from qor.scripts import ledger_dialect` to the existing
  `from qor.scripts import entry_id, ledger_fragment` import line's group.
- `detect_residual`: replace `ph.group(1) or ph.group(2)` with
  `ledger_dialect.hash_value(ph)`.
- `_recorded_chain_hash`: replace `xh.group(1) or xh.group(2)` with
  `ledger_dialect.hash_value(xh)`.

No other lines in the file reference `.group(` on a dialect match; the
`SESSION_SEAL_RE` match at `_recorded_chain_hash`'s `seal` branch already uses
`.group(1)` correctly (that pattern has exactly one capture group, is not
dialect-owned, and is out of this phase's scope).

### Unit Tests

- `tests/test_reconcile.py::test_detect_residual_groups_bare_line_previous_hash_with_backtick_form`
  - Two entries share one previous hash: one entry writes it in the
    backtick form, the other in the bare-line (fenced, no backticks) form.
    Asserts `detect_residual` returns ONE group of size 2 keyed on the real
    hash value, not two groups of size 1 (or a `None`-keyed group) — proving
    the bare-line form is read as the same hash, not dropped.
- `tests/test_reconcile.py::test_last_chain_hash_reads_bare_line_chain_hash_form`
  - A single entry whose `**Chain Hash**` is written in the bare-line form.
    Asserts `reconcile._last_chain_hash(text)` returns that recorded hash
    (not the `"0" * 64` genesis fallback and not a raised `ValueError`) —
    proving `_recorded_chain_hash` reads the third form instead of treating
    the entry as hash-less.

Both tests must be confirmed red against the current `group(1) or group(2)`
code before the fix (the bare-line form resolves to `None` at both call
sites) and green after.

## Definition of Done

### Deliverable: reconcile.py reads the dialect accessor

- **D1**: `detect_residual` and `_recorded_chain_hash` must resolve a hash
  value written in any of `ledger_dialect`'s three recognized forms
  (inline-backtick, `= <hex>`, bare-line), not just the first two, matching
  `ledger_hash.py`'s existing behavior at its equivalent call sites.
- **D2**: `qor/scripts/reconcile.py` `detect_residual` (`:44`) and
  `_recorded_chain_hash` (`:73`) call `ledger_dialect.hash_value(match)`
  instead of indexing `match.group(1) or match.group(2)`.
- **D3**: This plan file and the GH #477 closure reference document the
  fix; no ledger/doctrine surface beyond the standard GATE
  TRIBUNAL/SESSION SEAL entries is affected.
- **D4**: `tests/test_reconcile.py::test_detect_residual_groups_bare_line_previous_hash_with_backtick_form`
  and `tests/test_reconcile.py::test_last_chain_hash_reads_bare_line_chain_hash_form`
  confirmed red against the pre-fix `group(1) or group(2)` code and green
  after the fix, run twice for determinism.

## CI Commands

- `python -m pytest tests/test_reconcile.py -q`
- `python -m pytest tests/ -q` (full suite, run twice for determinism)
- `ruff check qor/ tests/`
