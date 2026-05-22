# Plan: Phase 82 — seal_entry_check honors re-anchored ledgers

**change_class**: hotfix

**doc_tier**: minimal

**Closes**: GH #88

## Open Questions

None. The replacement function (`ledger_hash.verify_post_anchor`) and the
acceptance criteria are prescribed by GH #88.

## Problem

`seal_entry_check.check()` (`qor/reliability/seal_entry_check.py:99`) runs a
defense-in-depth full-chain verification via the strict `ledger_hash.verify()`.
`verify()` carries Phase-66 taint propagation (GH #54): once it hits any
genuinely-broken entry it marks every subsequent entry `TAINTED` and returns
`rc=1` permanently, with no RE-ANCHOR reset.

`check()` is invoked by `/qor-substantiate` Step 7.7. On any re-anchored
consumer ledger that carries *disclosed* pre-anchor failures — the exact
ledgers `RE-ANCHOR` entries exist to tolerate — `verify()` returns `rc=1` and
`check()` aborts a structurally valid SESSION SEAL.

`ledger_hash.verify_post_anchor()` (`ledger_hash.py:270`, added Phase 66 / GH
#55) exists precisely for this: it classifies pre-boundary failures as
`DISCLOSED_PRE_ANCHOR` and fails only on post-boundary breaks. `seal_entry_check`
was never updated to consume it.

## Design note

Switching to `verify_post_anchor` is a deliberate semantic change to the
defense-in-depth step: a disclosed pre-anchor failure followed by a valid
SESSION SEAL now passes. The seal's own integrity is still fully guarded by
`check()`'s existing latest-entry checks — kind, phase number, and
chain-hash internal consistency (`seal_entry_check.py:79-96`) — which run
before the full-chain step and are unaffected. `verify_post_anchor`'s
auto-boundary absorbs a break with valid trailing entries into the
pre-anchor surface; this is the documented Phase-66 post-anchor contract,
not a regression introduced here.

## Phase 1: Consume verify_post_anchor in seal_entry_check

### Affected Files

- `tests/test_seal_entry_check.py` — rewrite one existing test to the
  post-anchor contract; add one genuine-post-anchor-break guard test.
- `qor/reliability/seal_entry_check.py` — `check()` calls
  `ledger_hash.verify_post_anchor()` instead of `ledger_hash.verify()`;
  update the failure-message string and the `check()` docstring to match.

### Unit Tests

Tests are authored and observed failing before the code change.

- `tests/test_seal_entry_check.py` — `test_check_tolerates_disclosed_pre_anchor_failure`
  (rewrite of the existing `test_check_fails_when_full_chain_verification_fails`).
  Builds a ledger: entry #100 with a genuinely-broken chain hash, then #101
  `IMPLEMENTATION` and #102 `SESSION SEAL` each internally consistent with
  their recorded predecessor (the re-anchored-ledger shape — a disclosed
  pre-anchor failure carried beneath a valid seal). Invokes
  `check(ledger, phase_num=47)` and asserts `result.ok is True` and
  `result.errors == []`. Confirms the disclosed pre-anchor failure is
  tolerated and the valid SESSION SEAL passes. This test FAILS against the
  current code (strict `verify` taints #101/#102, `rc=1`) and is the
  red-then-green TDD anchor for the fix. The existing test it replaces
  asserted the opposite verdict for the same fixture; that verdict is
  incorrect under the post-anchor contract, so the test is rewritten rather
  than kept.

- `tests/test_seal_entry_check.py` — `test_check_fails_on_genuine_post_anchor_break`.
  Builds a ledger: valid entries #100, #101, then a #102 `SESSION SEAL`
  whose `previous_hash` is a low-entropy placeholder pattern while its
  `chain_hash` is computed consistently from that placeholder (so `check()`'s
  latest-entry internal-consistency check at line 91-96 passes and the
  full-chain step is reached). Invokes `check(ledger, phase_num=47)` and
  asserts `result.ok is False` and that an error names the full-chain
  verification failure. `verify_post_anchor` classifies the seal as a
  post-boundary failure (placeholder detected; #102 is the highest entry so
  the auto-boundary falls on #101). Guards the other half of the contract —
  genuine post-anchor breaks are still caught — and would catch any future
  weakening of detection. Passes both before and after the code change by
  design; classified as guard coverage, not red-green TDD.

- `tests/test_seal_entry_check.py` — `test_check_passes_when_latest_entry_is_seal_for_current_phase`
  (existing, unchanged). A clean chain must still return `ok is True`:
  `verify_post_anchor` on a ledger with no failures returns `rc=0`. Named
  here as the explicit no-regression assertion.

### Changes

`qor/reliability/seal_entry_check.py`, in `check()`:

- Line 99: `rc = ledger_hash.verify(Path(ledger_path))` becomes
  `rc = ledger_hash.verify_post_anchor(Path(ledger_path))`.
- Line 101: the failure message `full chain verification failed
  (ledger_hash.verify rc={rc})` becomes `(ledger_hash.verify_post_anchor
  rc={rc})`.
- The `check()` docstring's "full chain verification passes" clause is
  amended to "post-anchor chain verification passes" for accuracy.

No other call site changes. `check_previous_hash_uniqueness` and the CLI
wrapper are untouched.

## Feature Inventory Touches

None. The plan touches `qor/reliability/` internal governance tooling and
`tests/`; it introduces no `src/` user-facing feature.

## CI Commands

- `python -m pytest tests/test_seal_entry_check.py -v` — the seal_entry_check
  behavioral suite, including the rewritten and new tests.
- `python -m pytest tests/test_substantiate_seal_entry_wiring.py -v` —
  confirms `/qor-substantiate` Step 7.7 wiring still consumes `check()`
  correctly after the switch.
- `python -m pytest tests/test_ledger_hash_validation.py -v` — confirms
  `verify` and `verify_post_anchor` own behavior is unaffected.
