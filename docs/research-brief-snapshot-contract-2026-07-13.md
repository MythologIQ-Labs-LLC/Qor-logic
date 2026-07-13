# Research Brief

**Date**: 2026-07-13T14:40:00Z
**Analyst**: The Qor-logic Analyst
**Target**: GH #270 -- canonical read-only repository governance snapshot contract
**Scope**: existing aggregation surfaces; source-of-truth map per required field; schema publication conventions

---

## Executive Summary

GH #270 is a productization feature that no existing surface satisfies:
`status_json` (Phase 165) aggregates the health-check ladder into check
id/ok/exit/summary rows but exports no identity, session, lifecycle, gate,
seal, shadow, or drift CONTENT, publishes no schema, and has no fail-safe
per-field states; `governance_snapshot.py` (Phase 175) is DNA backup-on-write
-- a naming collision, not an overlap. Every required snapshot field has a
verified repository-local source of truth, so the exporter is a pure
composition of guarded read-only collectors plus one published JSON Schema.

## Findings

### The near-name surfaces do different jobs
- qor/scripts/status_json.py:78-105 -- `run_all` emits {schema_version, ts,
  checks[{id, ok, exit, summary}], overall_ok}; the six-check ladder
  (governance-health, ledger-chain, seal-artifacts, gate-chain-completeness,
  gate-provenance, governance-index) is a VERDICT aggregator, not a state
  export. It is, however, the right INTERNAL engine for the snapshot's
  health section (in-process module runner at :44-60 survives any check).
- qor/scripts/governance_snapshot.py -- Phase 175 DNA file backup/restore;
  unrelated capability despite the name (the new module must NOT collide:
  name it snapshot_export).

### Source-of-truth map for every required field (all repository-local)
- Schema version / generated ts: the exporter's own contract.
- Qor-logic version: pyproject.toml [project].version (the ai_provenance
  precedent reads it the same way).
- Repository identifier: `git config --get remote.origin.url` when the git
  CLI and a remote exist; otherwise explicit state "unavailable" (issue
  requires "when available" + no network -- git config is local).
- Active/most recent session: .qor/session/current (SESSION_ID_PATTERN).
- Lifecycle phase + disposition: docs/META_LEDGER.md tail status line
  (`*Session: SEALED* (Phase N; vX.Y.Z; ...)`) + the latest entry heading.
- Latest gate results by phase: .qor/gates/<sid>/ via
  gate_chain/validate_gate_artifact latest-iteration resolution (Phase 173).
- Ledger verification + head: qor.scripts.ledger_hash verify rc + the last
  recorded Chain Hash; entry count.
- Latest sealed change: the last SESSION SEAL entry (version, phase, Merkle
  seal, entry id).
- Governance-health summary: qor.scripts.governance_health findings.
- Shadow summary by class/severity: docs/PROCESS_SHADOW_GENOME_UPSTREAM.md
  JSONL lines carry event_type + severity + addressed (verified line shape).
- Open/unresolved local findings: shadow events with addressed=false plus
  failing status_json checks.
- Doc/install drift: qor.scripts.doc_integrity_strict rc (doc currency);
  install_drift_check is host-dependent -> state "unknown" with reason when
  the host skills dir is absent (never inferred success).

### Contract publication conventions
- qor/gates/schema/*.schema.json + qor/gates/SCHEMA_REGISTRY.json deliberate
  registration (the Phase 169 freeze rule; gate_schema_freeze_lint.py:1-10).
  A snapshot schema is a new ceremony-adjacent artifact -- registering it is
  exactly what the registry exists for.
- jsonschema is already a dependency (validate_gate_artifact.py:16) -> the
  conformance test validates live output against the published schema.
- CLI convention: `python -m qor.scripts.snapshot_export --repo-root . --out
  PATH` (runnable as `qor-logic scripts snapshot_export`, the house pattern).

### Contract-requirement mapping
- Read-only/deterministic: pure collectors; determinism test strips
  generated_ts and compares two runs byte-for-byte.
- Fail-safe: every section is {state: ok|unknown|error, data..., source,
  reason?}; absence NEVER renders as health (the issue's hard rule).
- Derived-not-authoritative: the export cites source artifact paths per
  section for drill-down; ledger/gates stay canonical.
- Portable: stdlib + jsonschema (already vendored as a dependency); git CLI
  optional with explicit degradation; zero network.
- Tested: fixture matrix healthy / no-session / malformed-ledger /
  missing-artifacts / tampered (chain break) / stale; schema conformance;
  determinism; read-only (tree hash unchanged by export).

## Blueprint Alignment

| Blueprint Claim | Actual Finding | Status |
|----------------|---------------|--------|
| Issue: no single stable contract exists for external consumers | status_json exports verdicts only; nothing else aggregates state | MATCH (gap confirmed) |
| Issue: exporter must be read-only and portable | all mapped sources are local files + optional local git config | MATCH |
| Scout hypothesis: Phase 175 may partially satisfy #270 | governance_snapshot.py is DNA backup; zero overlap | DRIFT (naming collision only) |

## Recommendations

1. (P1) `qor/scripts/snapshot_export.py`: `build_snapshot(repo_root) -> dict`
   composing guarded collectors (each try/except into state=error, never
   raising); CLI with --out and --format json; exit 0 on export success
   regardless of governance state (the snapshot REPORTS state; it does not
   judge it).
2. (P1) `qor/gates/schema/repository_snapshot.schema.json` (schemaVersion
   "1"; additive-compatible: consumers must ignore unknown fields; breaking
   changes bump the major) + SCHEMA_REGISTRY registration + a contract
   reference `qor/references/snapshot-contract.md` (compatibility
   expectations, section state semantics, drill-down source guarantees).
3. (P1) Fixture-driven tests per the issue's six repository conditions plus
   conformance/determinism/read-only.
4. (P2) Enterprise concepts (actors, federation, cross-repo) stay out per
   the issue's explicit boundary.

## Updated Knowledge

The snapshot is a read MODEL: status_json's in-process runner becomes its
health engine, the ledger/gate artifacts stay authoritative, and every
consumer-facing field carries an explicit state plus a source pointer.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
