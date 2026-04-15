# Plan: Phase 3 — Gate Chain Runtime

**Status**: Active (scope-limited)
**Author**: QorLogic Governor
**Date**: 2026-04-15
**Scope**: Runtime machinery for the advisory gate chain. Session IDs, artifact schemas, prior-phase verification, override logging.
**Base spec**: `docs/plan-qor-migration-final.md` §Phase 3

## Open Questions

None. Decisions settled:
- Advisory (soft) enforcement — missing/invalid prior artifact warns + prompts user, does not block
- Override emits `gate_override` shadow event (severity 1, integrates with Phase 4)
- Session carrier: file marker (`.qor/current_session`), 24h regeneration
- Session format: `<UTC-ISO-MIN>-<6hex>` via `secrets.token_hex(3)`

## Gate chain

```
research -> plan -> audit -> implement -> substantiate -> validate -> (remediate?)
```

Defined canonically in `qor/gates/chain.md`. Each phase writes one artifact to `.qor/gates/<session_id>/<phase>.json`. The next phase reads its expected prior artifact at startup.

## Deliverables

### 1. `qor/gates/chain.md`

Phase sequence + `gate_reads`/`gate_writes` declarations. Referenced by skill frontmatter going forward.

### 2. `qor/gates/schema/*.schema.json` × 7

Minimal schemas for v1 — each declares a small stable field set. Each schema can be extended later without breaking old artifacts (additive-only rule).

- `research.schema.json` — questions, findings, sources
- `plan.schema.json` — plan_path, phases, open_questions
- `audit.schema.json` — target, verdict (PASS/VETO), violations, risk_grade
- `implement.schema.json` — files_touched, commits, test_summary
- `substantiate.schema.json` — reality_check, merkle_seal, content_hash
- `validate.schema.json` — criteria_results, overall
- `remediate.schema.json` — events_addressed, proposed_changes

### 3. `qor/scripts/session.py`

File-marker session carrier. Library interface:

- `get_or_create() -> str` — reads `.qor/current_session`; if absent OR mtime > 24h, generates new `<UTC-ISO-MIN>-<6hex>` and writes atomically via `os.replace`. Returns session id.
- `current() -> str | None` — returns current session id if marker exists and fresh, else None.
- `end_session() -> None` — removes marker.
- CLI: `python qor/scripts/session.py current|new|end`

### 4. `qor/scripts/validate_gate_artifact.py`

CLI validator.

- `python qor/scripts/validate_gate_artifact.py <phase> <artifact.json>` — validate single artifact against matching schema. Exit 0 on valid, 1 on invalid with error report.
- `python qor/scripts/validate_gate_artifact.py --all` — walk `.qor/gates/<session_id>/` for current session, validate every `.json` present. Useful pre-merge CI check.

### 5. `qor/scripts/gate_chain.py`

Library for skill-startup gate checks.

- `check_prior_artifact(current_phase: str, session_id: str | None = None) -> GateResult` — resolves prior phase from chain, reads `.qor/gates/<session_id>/<prior>.json`, validates against schema. Returns `GateResult(found: bool, valid: bool, path: Path | None, errors: list[str])`.
- `emit_gate_override(current_phase: str, prior_phase: str, reason: str, session_id: str)` — writes gate_override event via `shadow_process.append_event` (sev 1).
- Skills call `check_prior_artifact` on startup; if `not found` or `not valid`, skill surfaces prompt to user. On user confirming override, skill calls `emit_gate_override`.

### 6. `tests/test_gates.py`

- `test_session_id_format` — `^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}-[0-9a-f]{6}$`
- `test_session_id_collision_resistant` — 10k IDs in the same minute produce zero collisions
- `test_marker_roundtrip` — `get_or_create` called twice within 24h returns same id
- `test_marker_regenerates_after_24h` — mocked mtime past threshold produces new id
- `test_end_session_removes_marker`
- `test_schema_accepts_valid_artifact` (one per phase, parameterized)
- `test_schema_rejects_missing_required_field`
- `test_check_prior_artifact_missing_returns_not_found`
- `test_check_prior_artifact_valid_returns_valid`
- `test_check_prior_artifact_malformed_returns_invalid_with_errors`
- `test_emit_gate_override_writes_shadow_event` — appends to fixture log, verifies event fields

## Constraints

- **Python 3.11+ stdlib + jsonschema** (already runtime dep).
- **All atomic writes use `os.replace()`**.
- **Advisory only** — no function in this phase blocks execution. Callers surface prompts; users override.
- **No changes to existing skills** (Phase 3 provides library infra; wiring into skills is a separate future task).

## Success Criteria

- [ ] `qor/gates/chain.md` authored with phase sequence + per-phase reads/writes declared
- [ ] 7 schemas under `qor/gates/schema/` (one per phase)
- [ ] `session.py current` returns a valid id on first run; subsequent runs within 24h return same id
- [ ] `validate_gate_artifact.py --all` exits 0 when no artifacts present (empty dir ok)
- [ ] `gate_chain.check_prior_artifact('plan')` returns `found=False` with no prior research artifact (expected in current state)
- [ ] `pytest tests/test_gates.py` all pass
- [ ] 40 total tests (11 compile + 18 shadow + 11 new gate) all pass
- [ ] Drift check still clean
- [ ] Ledger chain still verifies
- [ ] Committed + pushed

## CI Commands

```bash
python -m pytest tests/test_gates.py -v
python qor/scripts/validate_gate_artifact.py --all
```
