# Repository Snapshot Contract

The versioned, read-only JSON export of repository-local governance state
(GH #270; Phase 191). Exporter: `qor/scripts/snapshot_export.py`; schema:
`qor/gates/schema/repository_snapshot.schema.json`.

```bash
python -m qor.scripts.snapshot_export --repo-root . --out dist/qor-repository-snapshot.json
```

## What the snapshot is

A derived read model. Ledgers, gate artifacts, and the shadow log remain
authoritative; the snapshot is recomputable from them at any time and every
section carries a `source` pointer sufficient for operator drill-down.

## Section state semantics (fail-safe rule)

Every top-level section renders as `{"state": ..., "source": ..., ...}`:

- `ok` -- the section's facts were read and (where applicable) verified.
- `unknown` -- the source is absent or carries nothing verifiable, with a
  `reason`. Absence is NEVER rendered as health; a ledger where zero entries
  could be verified is `unknown`, not `ok`.
- `error` -- the source exists but is malformed, tampered, or failed
  verification, with a `reason` or verify output.

The exporter's exit code reports whether the EXPORT succeeded, not whether
the repository is healthy: a degraded repository exports successfully with
degraded section states. Conflating the two would make unhealthy
repositories unobservable.

## Compatibility expectations

- `meta.schemaVersion` is `"1"`.
- Additive changes (new fields, new section keys) keep the version;
  consumers MUST ignore fields they do not recognize.
- Breaking changes (removing/renaming fields, changing state semantics)
  bump the version.
- The schema is registered in `qor/gates/SCHEMA_REGISTRY.json` (the Phase
  169 freeze rule), so snapshot surface changes are deliberate, planned
  events.

## Determinism and portability

Identical verified inputs produce byte-identical output apart from
`meta.generated_ts`. No network access; no host, GitHub, or LLM coupling.
The repository identifier comes from local git configuration when available
and is `null` otherwise.

## Boundary

Enterprise concepts (organization actors, cross-repository claims,
federation, review contracts, organization obligations) are outside this
base contract by design.
