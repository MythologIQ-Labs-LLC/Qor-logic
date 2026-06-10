# Plan: Phase 160 — doc currency for the GOV-05 provenance work + inventory enforcement

**change_class**: hotfix

**doc_tier**: standard

**boundaries**:
- limitations:
  - Scope is documentation currency for the Phase 158/159 work plus one
    enforcement test; no behavior changes to any runtime module.
- non_goals:
  - Registering `provenance-binding` in `GOVERNANCE_INDEX.md` (that index
    intentionally tracks only Tier-1 cornerstone doctrines, not all 35).
  - A broader `/qor-document` rewrite of unrelated sections.
- exclusions:
  - The conceptual detail already lives in `doctrine-provenance-binding.md`;
    `operations.md` gets an operational pointer, not a re-derivation.

## Open Questions

None. The gaps are enumerated below from a disk-vs-doc reconciliation.

## Problem

Phase 158 (GAP-GOV-05) shipped `qor/references/doctrine-provenance-binding.md`,
the `gate_provenance` module, per-session provenance sidecars, and the CI
`provenance-attest` job; Phase 159 (GH #223) added the seal-entry plan-name
fallback. The release docs drifted:

- The README doctrine inventory table omits `provenance-binding` -- it lists 34
  of the 35 `doctrine-*.md` files. Verified:
  > `python - <<'PY'` reconciliation -> `on disk not in README: ['provenance-binding']`
  The `badge_currency` gate did not catch this: it compares the **badge number**
  (35 == 35 file count) and never inspects the prose table, so the table can
  silently drift by any amount that keeps the count coincidentally matching.
- `docs/operations.md` describes the substantiate reliability gates and CI jobs
  but not the new `provenance-attest` job, the per-session sidecar written at
  each gate, or the Phase 159 seal-entry plan-name fallback.

## Phase 1: doctrine-inventory enforcement test + README + operations currency

### Affected Files

- `tests/test_readme_doctrine_inventory.py` - NEW. Asserts the set of
  `qor/references/doctrine-*.md` files equals the set of doctrines linked in the
  README inventory table -- bidirectional, so a future doctrine added or removed
  without a README update FAILs (closes the gap `badge_currency` leaves open).
- `README.md` - EDIT. Add the `provenance-binding` row to the doctrine inventory
  table in alphabetical position.
- `docs/operations.md` - EDIT. Document the Phase 158 `provenance-attest` CI job
  + the per-session provenance sidecar written at each gate, and note the Phase
  159 seal-entry plan-name fallback in the Step 7.7 description.

### Changes

- New test parses the README doctrine table with the same link pattern the table
  uses (`doctrine-<name>.md`), globs `qor/references/doctrine-*.md`, and asserts
  set equality, naming any symmetric-difference members in the failure message.
- README: insert `| [provenance-binding](qor/references/doctrine-provenance-binding.md) | Gate-artifact provenance binding (GAP-GOV-05): per-session HMAC sidecars (Layer A) + CI attestation (Layer B); honest threat-model ceiling |` in alphabetical order.
- operations.md: add a short paragraph under the CI/substantiate-gate narrative
  describing the `provenance-attest` job (keyless `verify-committed --phase-min 158`
  required gate + CI-secret `attest-latest`) and that `gate_chain.write_gate_artifact`
  writes a `<phase>.provenance` sidecar; extend the Step 7.7 description to note
  that a non-`plan-qor-phase<N>` plan filename now falls back to the
  ledger-derived phase with a WARN (GH #223).

### Unit Tests

- `tests/test_readme_doctrine_inventory.py`:
  - `test_readme_lists_every_doctrine_file` — globs `doctrine-*.md`, parses the
    README table, asserts every file is linked; FAILs naming any missing file
    (currently `provenance-binding`).
  - `test_readme_doctrine_table_has_no_phantom_entries` — asserts every doctrine
    the README links resolves to a real file on disk (no dangling rows).

## Definition of Done

### Deliverable: doctrine-inventory currency + enforcement

- **D1**: The README doctrine inventory matches the doctrine corpus on disk, and a
  test prevents future drift; the new GOV-05 provenance mechanism is discoverable
  from the operational docs.
- **D2**: `tests/test_readme_doctrine_inventory.py` (2 tests); README table + 1 row;
  `operations.md` provenance paragraph + Step 7.7 note.
- **D3**: Ledger SESSION SEAL records the doc-currency hotfix; CHANGELOG `### Fixed`.
- **D4**: `tests/test_readme_doctrine_inventory.py::test_readme_lists_every_doctrine_file`
  passes (was red on `provenance-binding`).

## CI Commands

- `python -m pytest tests/test_readme_doctrine_inventory.py -v` — inventory enforcement.
- `python -m pytest tests/ -q` — full suite stays green.
- `python -m qor.scripts.badge_currency --repo-root . --ledger docs/META_LEDGER.md` — badge counts unaffected.
