# Plan: Resync docs/SYSTEM_STATE.md + add freshness drift-guard

**change_class**: hotfix

**doc_tier**: standard

**boundaries**:
- limitations: `docs/SYSTEM_STATE.md` (Tier-1 governance artifact) is frozen at a Phase-75 / v0.51.0 / 2026-05-14 snapshot with a pre-migration File Tree (claims "variant outputs deferred until Phase 2", "META_LEDGER 18 entries"), a stale Ledger-chain-head (Entry #169 / Phase 52), and a stale Shipped-tooling block ("462 tests"). The existing `tests/test_system_state_phase_coverage.py` only enforces per-phase sections for ledger entries phrased "Phase N feature substantiated" — recent entries use different phrasing, so the 61-phase header drift was never caught. This phase: (1) rewrite the stale TOP sections — header (Snapshot/Chain-Status/Phase), Authoritative-source, File Tree, Ledger-chain-head, Shipped-tooling, Advisory-gate-overrides — to current truth; (2) add a condensed "## Phases 108-136 (v0.68.1 -> v0.102.1)" bridging section so the narrative is not misleadingly frozen; (3) add `tests/test_system_state_freshness.py` asserting the header phase is within 1 of the latest ledger SESSION SEAL phase, so this drift cannot recur silently.
- non_goals: Rewriting the accurate historical per-phase `## Phase 36 ... ## Phase 109` narrative sections (those are a frozen, correct record — left intact); backfilling full per-phase narrative for every phase 110-135 (the per-phase detail lives in META_LEDGER; SYSTEM_STATE gets a condensed bridge); changing any code module, gate, or the existing `test_system_state_phase_coverage.py` contract.
- exclusions: No change to `qor/` source, skills, or schemas. Doc + one new test only.

## Open Questions

None. Current truth is derived mechanically: latest ledger entry (#329, Phase 136, v0.102.1, chain `927bc482...`), 329 ledger entries, 30 skills, 98 scripts, 6 reliability modules, 54 references, 18 gate schemas, 2323 tests. The freshness tolerance (header within 1 of latest sealed phase) accommodates the unavoidable one-phase lag while the sealing phase's own entry is written after the pre-seal suite runs.

## Feature Inventory Touches

(`docs/FEATURE_INDEX.md` absent; declared for traceability. Touches `docs/SYSTEM_STATE.md` + new test.)

- entry_id: `n/a` · operation: `MODIFIED` · test_path: `tests/test_system_state_freshness.py` · test_descriptor: `the test parses the max 'SESSION SEAL -- Phase N' number from META_LEDGER and the '**Phase**: Phase P' number from the SYSTEM_STATE.md header, then asserts P >= N-1; run against the pre-resync header (P=75, N=136) the comparison 75 >= 135 is false and the assertion fails, and run against the resynced header it passes -- so a future seal that lets the header drift 2+ phases behind the ledger fails the assertion`

## Phase 1: Resync SYSTEM_STATE.md + freshness guard

### Affected Files

- `tests/test_system_state_freshness.py` - NEW. Written first; red against the current Phase-75 header.
- `docs/SYSTEM_STATE.md` - rewrite the stale top sections to current truth; add the Phases 108-136 bridging section; leave the historical `## Phase 36..109` sections intact.

### Changes

Replace the header (Snapshot -> 2026-06-02; Chain Status -> Phase 136 sealed v0.102.1 + Phase 137 this doc-currency seal; Phase -> concise current-state paragraph pointing to META_LEDGER for full per-phase history instead of the 60-phase run-on), the Authoritative-source note (variants are live, not "deferred until Phase 2"), the File Tree (regenerated to the current `qor/` + `docs/` + `tests/` layout with accurate counts), the Ledger-chain-head (Entry #329 / Phase 136 / v0.102.1 / chain `927bc482...` / 329 entries), the Shipped-tooling block (current CLI surface + 2323 tests + module counts), and the Advisory-gate-overrides note. Append a condensed Phases-108-136 bridging section.

### Unit Tests

- `tests/test_system_state_freshness.py::test_header_phase_within_one_of_latest_seal` - parse `max(Phase N)` over `^### Entry #\d+: SESSION SEAL -- Phase (\d+)` in META_LEDGER and `**Phase**: Phase (\d+)` in the SYSTEM_STATE header; assert `header_phase >= latest_phase - 1`.
- `::test_header_has_parseable_snapshot_date` - the header `**Snapshot**: YYYY-MM-DD` parses as an ISO date (guards against a malformed/again-frozen header).
- `::test_existing_phase_coverage_still_passes` - import + call the existing `_sealed_phases_from_ledger` / `_phases_in_system_state` helpers and assert no regression (the historical sections remain).

## Definition of Done

### Deliverable: current, drift-guarded SYSTEM_STATE.md

- **D1**: SYSTEM_STATE.md reflects the current system (Phase 136/137 era, v0.102.1, 329 ledger entries, live variants) instead of the Phase-75 snapshot, and a mechanical guard prevents the header from silently drifting 2+ phases behind the ledger again.
- **D2**: rewritten header + File Tree + Ledger-chain-head + Shipped-tooling + Advisory sections + Phases-108-136 bridge in `docs/SYSTEM_STATE.md`; new `tests/test_system_state_freshness.py`.
- **D3**: META_LEDGER SESSION SEAL entry; patch bump 0.102.1 -> 0.102.2.
- **D4**: `tests/test_system_state_freshness.py::test_header_phase_within_one_of_latest_seal` green (red before); full `python -m pytest -q` green (no regression in `test_system_state_phase_coverage`).

## CI Commands

- `python -m pytest tests/test_system_state_freshness.py tests/test_system_state_phase_coverage.py -q` — the freshness guard + the existing coverage contract.
- `python -m pytest -q` — full suite green before substantiate.

## CI Coverage Exemptions

- `dependency_admission_lint` — pre-existing dependency-admission job; no dependencies touched.
- `check_variant_drift` — satisfied by the seal-time `dist_compile` recompile.
- `ledger_hash.py verify` — pre-existing ledger chain-integrity check.
- `test_packaging_install` — pre-existing install-smoke job.
- `gate_chain_completeness` — pre-existing gate-chain check, satisfied by the seal process.
