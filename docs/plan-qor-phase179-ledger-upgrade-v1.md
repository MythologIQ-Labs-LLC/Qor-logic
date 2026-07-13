# Plan: Phase 179 - Ledger upgrade V1: version marker + recovery verb (GH #271 slice)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**: (none)

**boundaries**:
- limitations: `upgrade` normalizes MARKUP only (the Phase 170 migrator contract: hashes verbatim, mismatches reported never corrected); a ledger whose post-anchor band genuinely fails verification is left byte-untouched with exit 1 -- recovery of broken math stays with reconcile/remediate.
- non_goals: No typed entry model or renderer; no change to how skills emit entries (deferral per research F3 -- fragment bodies are appended verbatim, so a seal-flow swap would not unify emission); no new gate schema.
- exclusions: #234's reconcile deferred-tail fix is the next queue item, not this slice; wiring `upgrade` into governance-health routing prose is follow-on.

## Open Questions

(none)

## Origin

Research brief docs/research-brief-ledger-upgrade-v1-2026-07-13.md (ledger entry #434, session `2026-07-13T0718-ea9af3`); GH #271 minimal V1 per the recorded deferral rationale.

## Locked Decisions

- **LD-1: reuse, never reimplement.**
  `grep -nE 'def main' qor/scripts/ledger_migrate.py -> 155` (never-in-place migrator, `--dry-run`, hashes verbatim); `grep -nE 'def verify_post_anchor' qor/scripts/ledger_hash.py -> 456` (the acceptance verifier: a re-anchored ledger with disclosed pre-anchor failures is healthy per GH #199). The new module orchestrates these two; it parses nothing itself.
- **LD-2: swap-on-success-only atomicity.**
  Migrate INTO a sibling temp file; run acceptance on the TEMP; only a passing temp is `os.replace`d over the original (the same atomic-write discipline as `validate_gate_artifact._atomic_write`); any failure leaves the original byte-untouched and exits 1 naming the residuals.
- **LD-3: the marker is a head comment, version 0 when absent.**
  `<!-- qor:meta-ledger-schema=1 -->` inserted after the title line; verified inert to `ledger_hash.verify` (entry-block parser), `seal_entry_check` (latest-entry parser), `governance_health._ledger_damage` (title/entries presence), and the badge counter. `schema_version(text) -> int` returns the marker's N or 0 (legacy). Idempotent: an existing marker is never duplicated.
- **LD-4: self-application.**
  This repository's own `docs/META_LEDGER.md` gains the marker in this phase (one head line; entry bodies untouched; chain math unaffected by construction -- bodies are not part of the file-level markers and the marker precedes all entries).

## Phase 1: Upgrade module (TDD first)

### Affected Files

- tests/test_ledger_upgrade.py - NEW; behavioral tests for upgrade success, residual-failure safety, idempotency, marker semantics, dry-run
- qor/scripts/ledger_upgrade.py - NEW; `SCHEMA_MARKER_RE`, `schema_version`, `ensure_marker`, `upgrade`, `main`

### Changes

`ledger_upgrade.py` (<140 lines, stdlib + ledger_migrate/ledger_hash reuse): `schema_version(text) -> int` parses `<!-- qor:meta-ledger-schema=(\d+) -->` (0 when absent). `ensure_marker(text) -> str` inserts the version-1 marker after the first line when absent (idempotent). `upgrade(ledger_path, dry_run=False) -> UpgradeReport` (dataclass: migrated/partial/no_hash counts from the migrator, verify_rc, swapped: bool): runs the migrator into `<ledger>.upgrade.tmp` (same dir), applies `ensure_marker` to the temp, runs `verify_post_anchor` on the temp (stdout captured), and on rc==0 atomically replaces the original (dry_run reports without writing the original and removes the temp); on rc!=0 removes the temp, leaves the original byte-untouched, reports. `main(argv)`: `--ledger` (default docs/META_LEDGER.md), `--dry-run`; exit 0 on swapped-or-already-clean, 1 on residual failure.

### Unit Tests

- tests/test_ledger_upgrade.py::test_upgrade_normalizes_legacy_markup_and_swaps - a synthetic legacy-format ledger (fenced-block hash markup, the migrator's format B) upgrades in place: canonical markup, marker present, verify_post_anchor rc 0, exit 0
- tests/test_ledger_upgrade.py::test_upgrade_preserves_hashes_verbatim - the sets of 64-hex digests extracted before and after upgrade are identical (markup moves, math does not)
- tests/test_ledger_upgrade.py::test_upgrade_failure_leaves_original_untouched - a ledger with a genuine post-anchor chain mismatch: exit 1, original byte-identical (sha256 compare), no temp residue
- tests/test_ledger_upgrade.py::test_upgrade_is_idempotent - second run on an upgraded ledger exits 0 and the file is byte-identical (marker not duplicated)
- tests/test_ledger_upgrade.py::test_schema_version_parses_marker - absent -> 0; version-1 marker -> 1
- tests/test_ledger_upgrade.py::test_dry_run_writes_nothing - dry-run on a legacy ledger reports the counts, original byte-identical, no temp residue

## Phase 2: Self-application + doc

### Affected Files

- docs/META_LEDGER.md - head gains the version-1 marker (one line; LD-4)
- tests/test_ledger_upgrade.py - one live-state test: `schema_version` of the repository's own ledger returns 1
- docs/operations.md - recovery-verb paragraph (`qor-logic scripts ledger_upgrade`) beside the existing failure-recovery section

### Changes

Marker line inserted after the ledger title. operations.md "Ledger chain integrity broken" recovery bullet gains the one-command path with the swap-on-success-only guarantee and the exit-1 residual contract.

### Unit Tests

- tests/test_ledger_upgrade.py::test_current_ledger_declares_schema_version - `schema_version(docs/META_LEDGER.md text)` == 1 (locks the self-application; fails if the marker is ever dropped)

## Feature Inventory Touches

(empty -- governance tooling; no FEATURE_INDEX row)

## Definition of Done

### Deliverable: one-command ledger recovery + versioned format

- **D1**: A consumer whose ledger goes format-DAMAGED after a toolkit update runs one command and returns to a verified state -- or gets an exit-1 report with the original byte-untouched (GH #271 V1; the emission-API unification deferred with the F3 evidence recorded on the issue).
- **D2**: `ledger_upgrade.py` per LD-1/2/3; marker on the repository's own ledger per LD-4.
- **D3**: Ledger entries for plan/audit/implement/seal; operations.md recovery paragraph; GH #271 disposition records the V1/deferral split.
- **D4**: `test_upgrade_failure_leaves_original_untouched` observes the safety contract; `test_upgrade_normalizes_legacy_markup_and_swaps` observes the recovery; `test_current_ledger_declares_schema_version` observes self-application.

## CI Commands

- `python -m pytest tests/test_ledger_upgrade.py -q` - focused suite (run twice for determinism)
- `python -m pytest -q` - full suite; locks every ledger consumer against the marker
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - ledger chain integrity across the phase's entries
