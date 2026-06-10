# Plan: Phase 162 — ledger base-currency gate + re-anchor helper (GH #231, Option 1, WARN-first)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**:
- term: ledger base currency
  home: qor/references/doctrine-ledger-concurrency.md
- term: provisional seal entry
  home: qor/references/doctrine-ledger-concurrency.md

**boundaries**:
- limitations:
  - V1 ships the base-currency gate WARN-first (exit 0; `--enforce` reserved for
    V2), so it does not block the introducing phase's own seal or any open PR.
  - The gate identifies "new on this branch" entries by chain-hash set membership
    against the base; it assumes the base ref is fetchable (CI fetch-depth 0).
- non_goals:
  - Promoting the gate to a required/fail-closed CI check (a documented V2 flip,
    after operator evidence -- mirrors prior WARN->VETO gate ramps).
  - Per-entry content-addressed files / Merkle-tree / federation reconciliation
    (#231 alternatives, explicitly out of scope).
  - Auto-rewriting `META_LEDGER.md`; the re-anchor helper RETURNS corrected
    values, it does not edit the ledger.
- exclusions:
  - `check_previous_hash_uniqueness` is retained unchanged as the defense-in-depth
    post-hoc detector.

## Open Questions

None. Scope + WARN-first posture fixed by GH #231 and the operator's cycle
decision.

## Problem

The ledger is a linear hash chain over a git branch DAG (see GH #231). A branch
that seals against a stale base (its first new entry's `previous_hash` does not
equal `origin/main`'s tip `chain_hash`) forks the chain; git can auto-merge the
two appends silently. Today this is prevented only by the manual stacking
discipline and caught only post-hoc by `check_previous_hash_uniqueness`. Verified:

> `grep -nE "def chain_hash|def content_hash" qor/scripts/ledger_hash.py` -> 25, 39
> `grep -nE "_parse_latest_entry" qor/reliability/seal_entry_check.py` -> 49
> `git show origin/main:docs/META_LEDGER.md | grep "Chain Hash" | tail -1` -> the base tip the branch must chain from.

## Phase 1: base-currency gate + re-anchor helper + doctrine

### Affected Files

- `tests/test_ledger_base_currency.py` - NEW. Behavioral tests for the gate
  (ok / stale-base / no-new-entries / multi-new-entry) and the re-anchor fold,
  plus the WARN-first CLI posture.
- `qor/reliability/ledger_base_currency.py` - NEW. stdlib + reuse of
  `ledger_hash`/`entry_id`. The gate, the re-anchor helper, and the CLI.
- `.github/workflows/ci.yml` - EDIT. Add a WARN-only step on the `test` job that
  runs the gate against `origin/main`.
- `qor/references/doctrine-ledger-concurrency.md` - NEW. The provisional-until-
  merge contract; home for the two introduced terms.
- `qor/references/glossary.md` - EDIT. Add the two terms with `referenced_by`.
- `README.md` - EDIT. Add the `ledger-concurrency` row to the doctrine inventory
  (the Phase-160 `test_readme_doctrine_inventory` guard requires it).

### Changes

`ledger_base_currency.py` (each function within the Section 4 Razor budget):

- `_entries(text) -> list[Entry]` — parse `(entry_num, previous_hash, chain_hash)`
  per ledger entry, in document order (reuse the `_HASH_FIELD_RE` shape from
  `seal_entry_check`).
- `check(branch_text, base_text) -> BaseCurrencyResult` — compute the base's
  chain-hash set and its tip (last chain_hash). Walk the branch entries; the
  first whose `chain_hash` is NOT in the base set is the first new-on-branch
  entry. Return ok when there are no new entries, or when that first new entry's
  `previous_hash` equals the base tip; otherwise return a finding naming the
  recorded vs expected predecessor (stale base).
- `reanchor(base_tip_chain, new_entries) -> list[ReanchoredEntry]` — pure fold:
  `prev = base_tip_chain`; for each `{content_hash, ts, phase}` compute
  `chain = ledger_hash.chain_hash(content_hash, prev)` and
  `eid = entry_id.derive_entry_id(ts, phase, content_hash)`, then advance
  `prev = chain`. Returns the corrected `(previous_hash, chain_hash, entry_id)`
  sequence that links cleanly from the live base tip. Does not touch the file.
- `main(argv)` — `--repo-root .`, `--base-ref origin/main`, `--enforce` (V2,
  default off). Reads the working-tree ledger and `git show <base>:docs/META_LEDGER.md`;
  on a finding prints `WARN: ...` and exits 0 (WARN-first), or exits 1 only under
  `--enforce`. Disclosed-skip (exit 0) when the base ref is unresolvable or the
  branch is the base.

`ci.yml`: add to the `test` job, after the existing seal re-verify, a WARN-only
step running `python -m qor.reliability.ledger_base_currency --base-ref origin/main`
(shell-wrapped with `|| true` so it never blocks in V1).

### Unit Tests

- `tests/test_ledger_base_currency.py`:
  - `test_check_ok_when_branch_chains_from_base_tip` — branch's first new entry's
    `previous_hash` == base tip → `ok` True.
  - `test_check_flags_stale_base` — base advanced (tip moved); branch's first new
    entry still cites the OLD tip → `ok` False, finding names recorded vs expected.
  - `test_check_ok_when_no_new_entries` — branch ledger == base → `ok` True.
  - `test_check_ok_with_multi_new_entries` — branch adds a tribunal AND a seal;
    the first new (tribunal) cites the base tip → `ok` True (the seal citing the
    tribunal is correct, not a stale-base signal).
  - `test_reanchor_recomputes_a_valid_subchain` — `reanchor(base_tip, [...])`
    returns entries where each `chain_hash == ledger_hash.chain_hash(content, prev)`
    and `previous_hash` links to the prior `chain_hash` (first links to base_tip).
  - `test_reanchor_changes_a_stale_subchain_to_base_tip` — feeding the stale
    sub-chain's content hashes through `reanchor` yields a first `previous_hash`
    equal to the live base tip (the fix the operator applies).
  - `test_main_cli_warn_only_exits_zero_on_stale` — CLI over a stale-base fixture
    prints `WARN` and returns 0; with `--enforce` returns 1.

## Definition of Done

### Deliverable: base-currency gate

- **D1**: A branch that sealed against a stale `main` tip is surfaced (WARN) before
  merge, instead of only post-hoc by `check_previous_hash_uniqueness`.
- **D2**: `qor/reliability/ledger_base_currency.py` exposing `check`, `reanchor`,
  `main`; CI WARN-only step.
- **D3**: New `doctrine-ledger-concurrency.md` (home for both terms); glossary +
  README inventory updated; `check_previous_hash_uniqueness` retained.
- **D4**: `tests/test_ledger_base_currency.py::test_check_flags_stale_base` and
  `::test_reanchor_recomputes_a_valid_subchain` pass.

### Deliverable: re-anchor helper

- **D1**: An operator can deterministically re-anchor a provisional seal sub-chain
  onto the live base tip without hand-computing hashes.
- **D2**: `reanchor(base_tip_chain, new_entries)` pure fold over `ledger_hash` +
  `entry_id`.
- **D3**: Documented in the doctrine as the merge-time recompute path.
- **D4**: `tests/test_ledger_base_currency.py::test_reanchor_changes_a_stale_subchain_to_base_tip`
  passes.

## CI Commands

- `python -m pytest tests/test_ledger_base_currency.py -v` — gate + re-anchor behavior.
- `python -m pytest tests/test_readme_doctrine_inventory.py -v` — README lists the new doctrine.
- `python -m pytest tests/ -q` — full suite stays green.
- `python -m qor.reliability.ledger_base_currency --base-ref origin/main` — WARN-only base-currency gate.
- `python qor/scripts/check_variant_drift.py` — dist unaffected (no skill change).
