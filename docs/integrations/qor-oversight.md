# Qor Oversight Integration

## Status

**Relationship established; machine contract not yet implemented.**

Qor Oversight is a system-agnostic operator interface that may consume repository-local governance state emitted by Qor-logic. Qor Oversight is not part of Qor-logic, does not replace its CLI or governance artifacts, and is not an authority over repository-local governance semantics.

- Qor Oversight: https://github.com/MythologIQ-Labs-LLC/qor-oversight
- Canonical snapshot work: issue #270

## Responsibility boundary

Qor-logic owns:

- Repository-local lifecycle and gate state
- Meta Ledger verification and head state
- Substantiation and release evidence
- Shadow Genome summaries
- Governance-health conclusions
- Documentation and installation drift
- The canonical repository snapshot schema and exporter

Qor Oversight owns:

- Rendering supported snapshots
- Operator filtering and drill-down
- Cross-source presentation
- Provenance, freshness, and adapter-health display

Qor Oversight must not:

- Parse Qor-logic Markdown or JSONL internals as public APIs
- Recalculate Qor-logic verdicts
- Infer healthy state from missing artifacts
- Mutate Qor-logic ledgers or repository governance state

## Planned integration contract

Issue #270 defines the required deterministic, versioned, read-only repository governance snapshot.

The intended flow is:

```text
Qor-logic authoritative artifacts
        ↓
Qor-logic repository snapshot exporter
        ↓
versioned repository governance snapshot
        ↓
Qor Oversight adapter and operator view
```

Until issue #270 is implemented, Qor Oversight must represent canonical Qor-logic governance state as unavailable or unknown. GitHub activity, filenames, issue labels, and repository prose are not substitutes for the snapshot.

## Compatibility expectations

The future contract must provide:

- A published schema version
- Additive and breaking-change rules
- Explicit stale, missing, malformed, tampered, and unavailable states
- Drill-down references to authoritative artifacts
- Deterministic fixture coverage
- No network or hosted-service requirement in Qor-logic

Qor Oversight is the first named operator-interface consumer, but the contract remains product-level and may support other IDE panels, CI summaries, governance portals, and third-party consumers.

## Current verification

At the time this document was added:

- No Qor-logic exporter exists.
- No Qor Oversight adapter consumes a canonical Qor-logic snapshot.
- No compatibility version has been declared.
- Issue #270 remains the implementation authority.

This document establishes product lineage and integration ownership. It does not claim that the integration has shipped.
