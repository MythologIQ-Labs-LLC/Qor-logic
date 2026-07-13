# Plan: Phase 191 - Read-only repository governance snapshot contract (GH #270)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**:
- term: Repository snapshot
  home: qor/references/snapshot-contract.md

**boundaries**:
- limitations: [the snapshot is a derived read model; ledgers and gate artifacts remain authoritative; generation metadata (timestamp) varies between runs]
- non_goals: [enterprise concepts (organization actors, cross-repository claims, federation, review contracts) per the issue's explicit boundary; mutation of any governance state; network access of any kind]
- exclusions: [dashboard/consumer implementations (external); GitHub or hosted-service coupling]

## Open Questions

(none)

## Origin

Research brief docs/research-brief-snapshot-contract-2026-07-13.md (ledger entry #482, session `2026-07-13T1505-e508d3`); GH #270. An external oversight consumer has upstream dependencies on this contract; the schema is the interface.

## Locked Decisions

- **LD-1: new module `snapshot_export`; the near-name surfaces stay untouched.**
  `grep -nE 'def run_all' qor/scripts/status_json.py -> 78` (verdict aggregator; its in-process module runner at :44-60 is REUSED as the health-section engine); `grep -nE 'DNA_FILES' qor/scripts/governance_snapshot.py -> matches` (Phase 175 backup; naming collision only). `qor/scripts/snapshot_export.py`: `build_snapshot(repo_root) -> dict` composing guarded read-only collectors; CLI `--repo-root . --out PATH [--indent N]`; exit 0 on successful export regardless of governance state (the snapshot REPORTS state, it does not judge it); exit 1 only when the export itself cannot be produced.
- **LD-2: fail-safe is structural, not conventional.**
  Every section renders as `{{"state": "ok"|"unknown"|"error", "source": <repo-relative path or null>, ...}}`; collectors are individually try/except-guarded into `state: "error"` with a reason -- absence, malformation, or staleness NEVER renders as health (issue contract requirement 3). Unknown-with-reason covers host-dependent surfaces (install drift when no host dir exists) and optional facts (repo identifier without a git remote).
- **LD-3: the schema publishes under the freeze-rule registry.**
  `grep -nE 'SCHEMA_REGISTRY' qor/scripts/gate_schema_freeze_lint.py -> 6,53` -- `qor/gates/schema/repository_snapshot.schema.json` with top-level `schemaVersion` (const "1"), registered in qor/gates/SCHEMA_REGISTRY.json. Compatibility contract (documented in qor/references/snapshot-contract.md): additive changes keep schemaVersion; consumers MUST ignore unknown fields; breaking changes bump the version. `grep -nE 'import jsonschema' qor/scripts/validate_gate_artifact.py -> 16` (dependency already present; the conformance test validates live output against the published schema).
- **LD-4: section inventory (the issue's required content, mapped).**
  `meta` (schemaVersion, qor_logic_version from pyproject, repo_identifier from local `git config --get remote.origin.url`, generated_ts), `session` (.qor/session/current), `lifecycle` (ledger tail status line: phase, version, disposition), `gates` (latest artifact per phase for the snapshot session -- or the most recent session dir -- via the Phase 173 latest-iteration resolution; per-phase verdict + ts + path), `ledger` (verify rc via qor.scripts.ledger_hash, head chain hash, seal-entry count), `latest_seal` (version, phase, Merkle seal, entry id from the last SESSION SEAL entry), `health` (the status_json six-check ladder run in-process), `shadow` (event counts by event_type x severity + unaddressed count from the upstream JSONL), `drift` (doc-currency rc; install drift as unknown-with-reason when host dirs are absent), `findings` (unaddressed shadow events + failing health checks, each with source pointers).
- **LD-5: determinism is tested, not asserted.**
  Two `build_snapshot` calls on identical inputs produce byte-identical JSON after deleting `meta.generated_ts` (the issue's "semantically identical apart from generation metadata"). Read-only is tested by hashing the tree before/after an export run.

## Phase 1: Collectors + schema (TDD first)

### Affected Files

- tests/test_snapshot_export.py - NEW (red first)
- qor/scripts/snapshot_export.py - NEW per LD-1/LD-2/LD-4
- qor/gates/schema/repository_snapshot.schema.json - NEW per LD-3
- qor/gates/SCHEMA_REGISTRY.json - register the schema
- qor/references/snapshot-contract.md - NEW: compatibility + state semantics + drill-down guarantees
- docs/GOVERNANCE_INDEX.md - Tier 2 row for the contract reference

### Changes

Collectors are small pure functions over explicit paths; `build_snapshot` assembles them under the guard wrapper; the CLI serializes with sorted keys and a trailing newline. No collector imports mutate state; the health section reuses status_json's `run_all` with its default registry.

### Unit Tests

- tests/test_snapshot_export.py - test_healthy_repo_snapshot: over THIS repository -> meta/session/lifecycle/ledger/latest_seal sections state ok with real values (version equals pyproject; latest_seal.version equals the CHANGELOG head) (red today)
- tests/test_snapshot_export.py - test_schema_conformance: live snapshot validates against the published schema via jsonschema (red today)
- tests/test_snapshot_export.py - test_no_session_repo: fixture repo without .qor/session -> session.state == "unknown", overall export still succeeds (red today)
- tests/test_snapshot_export.py - test_malformed_ledger_repo: fixture with a truncated META_LEDGER -> ledger.state == "error" with reason; never "ok" (red today)
- tests/test_snapshot_export.py - test_tampered_chain_repo: fixture with a broken chain hash -> ledger.state == "error" and verify rc nonzero surfaced
- tests/test_snapshot_export.py - test_missing_artifacts_repo: session present but empty gates dir -> gates.state == "unknown" with reason
- tests/test_snapshot_export.py - test_determinism_modulo_ts: two runs, generated_ts stripped -> byte-identical JSON (LD-5)
- tests/test_snapshot_export.py - test_export_is_read_only: sha256 over the fixture tree before/after export -> identical (LD-5)
- tests/test_snapshot_export.py - test_cli_writes_out_file: --out path written, exit 0, stdout quiet; parseable JSON with schemaVersion "1"

## Feature Inventory Touches

(empty -- governance tooling; no src/ features)

## Definition of Done

### Deliverable: versioned read-only snapshot contract

- **D1**: External operator surfaces consume one stable, versioned, documented JSON contract instead of parsing markdown or binding to internal layouts (GH #270); absence is always explicit, never inferred success.
- **D2**: `snapshot_export.build_snapshot` + CLI; `repository_snapshot.schema.json` registered per the freeze rule; stdlib + existing jsonschema dependency; zero network.
- **D3**: snapshot-contract.md reference (compatibility expectations + state semantics) registered in GOVERNANCE_INDEX; ledger entries for plan/audit/implement/seal; CHANGELOG feature entry.
- **D4**: The nine tests observe live values, schema conformance, the four degraded-fixture states, determinism modulo generation metadata, tree immutability, and CLI behavior; red-then-green twice.

## CI Commands

- `python -m pytest tests/test_snapshot_export.py -q` - focused suite (run twice for determinism)
- `python -m pytest -q` - full suite
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - chain integrity
