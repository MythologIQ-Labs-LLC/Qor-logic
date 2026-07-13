# Plan: Phase 180 - Reconcile links off the last validly hashed entry (GH #234)

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

(none)

## Origin

Research brief docs/research-brief-reconcile-deferred-tail-2026-07-13.md (ledger entry #438, session `2026-07-13T0739-248dc8`); GH #234. Targeted parse fix; forward-only semantics unchanged.

## Locked Decisions

- **LD-1: the fix is a backward-walk fallback inside `_last_chain_hash`.**
  `grep -nE 'def _last_chain_hash' qor/scripts/reconcile.py -> 69`; raise at 82. When `entries[-1]` yields no CHAIN_HASH_RE / SESSION_SEAL_RE match, iterate `reversed(entries[:-1])` with the same two patterns; raise (message renamed to name the true condition: "no validly chain-hashed entry found to link off") only when NO entry anywhere matches. Genesis behavior (`"0" * 64` on empty) unchanged. No signature change; sole caller `append_reconciliation_entry` untouched.
- **LD-2: acceptance is the full authorize path on a synthetic deferred tail.**
  Existing tests construct valid-tail ledgers only (tests/test_reconcile.py; zero deferred-tail coverage). New tests build a chain-DIRTY tail (valid entries then hash-less deferred entries with prose Previous Hash lines), run `build_proposal` -> `append_reconciliation_entry` (dry-run AND wet), and assert the appended entry's Previous Hash equals the LAST VALID entry's chain hash -- plus the no-hash-anywhere raise is regression-locked.

## Phase 1: Fix + regression tests (TDD first)

### Affected Files

- tests/test_reconcile.py - deferred-tail test group appended
- qor/scripts/reconcile.py - `_last_chain_hash` backward-walk fallback

### Changes

`_last_chain_hash`: extract the two-pattern probe into a small local helper; probe `entries[-1]`, then `reversed(entries[:-1])`; raise the renamed error when nothing matches. (~10 lines net.)

### Unit Tests

- tests/test_reconcile.py::test_authorize_succeeds_on_deferred_merkle_tail - synthetic DIRTY-tail ledger: build_proposal identifies the residual, append_reconciliation_entry (wet) succeeds, and the RECONCILIATION entry's `**Previous Hash**` equals the last valid entry's chain hash (GH #234 acceptance)
- tests/test_reconcile.py::test_authorize_dry_run_on_deferred_tail_writes_nothing - dry-run on the same ledger computes the entry and leaves the file byte-identical
- tests/test_reconcile.py::test_last_chain_hash_raises_when_no_entry_has_hashes - a ledger whose entries ALL lack hash markup still raises (fail-closed lock; message names the true condition)

## Feature Inventory Touches

(empty -- governance tooling)

## Definition of Done

### Deliverable: reconcilable deferred tails

- **D1**: A ledger in the no-fabrication deferred-Merkle state -- the state reconcile exists to repair -- can be reconciled without manual surgery (GH #234).
- **D2**: `_last_chain_hash` backward-walk per LD-1; renamed fail-closed error; zero caller changes.
- **D3**: Ledger entries for plan/audit/implement/seal; GH #234 disposition notes the #271-parser subsumption path.
- **D4**: `test_authorize_succeeds_on_deferred_merkle_tail` observes the acceptance (red against the current tail-only parse); `test_last_chain_hash_raises_when_no_entry_has_hashes` locks the fail-closed boundary.

## CI Commands

- `python -m pytest tests/test_reconcile.py tests/test_cli_reconcile.py tests/test_ledger_hash_reconciliation.py -q` - focused suite (run twice for determinism)
- `python -m pytest -q` - full suite
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - ledger chain integrity across the phase's entries
