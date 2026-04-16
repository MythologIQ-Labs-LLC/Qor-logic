## Phase 18 — qor-remediate Full Implementation

**change_class**: feature
**Status**: Active
**Author**: QorLogic Governor
**Date**: 2026-04-16
**Branch**: `phase/18-qor-remediate`
**Target version**: `0.7.0 → 0.8.0` (main reconciles against Phase 17 at merge time)

## Open Questions

None. Scope is fully specified by the current `qor/skills/sdlc/qor-remediate/SKILL.md` (87 lines per `wc -l`, grounded 2026-04-16), its Steps 0-5, and the dual-file shadow infrastructure delivered by Phase 14.

## Context (inline grounded)

- `qor/skills/sdlc/qor-remediate/SKILL.md` — 87 lines (`wc -l`, 2026-04-16). Ends with `## Status` block marker "**STUB (minimal)**" at line 85-87. This plan removes that marker and wires the helpers.
- `qor/scripts/shadow_process.py` — 165 lines (`wc -l`, 2026-04-16). Exposes `read_all_events()` (line 142), `id_source_map()` (line 146), `write_events_per_source()` (line 155), `append_event()` (line 65), `LOCAL_LOG_PATH` (line 21), `UPSTREAM_LOG_PATH` (line 22). Verified via `grep -n "^def " qor/scripts/shadow_process.py`.
- `qor/scripts/check_shadow_threshold.py` — 161 lines (`wc -l`, 2026-04-16). Holds `aged_high_severity_unremediated` precedent (line 32 / `ESCALATION_EVENT`). This plan reuses the detection logic in pattern-match, does not modify the file.
- `tests/test_shadow.py` — 394 lines (`wc -l`, 2026-04-16). Provides `make_event()` helper (lines 16-41) and the tmp_path + `mock.patch.object(shadow_process, "LOCAL_LOG_PATH", ...)` pattern (lines 342-394). New tests reuse both.
- Baseline pytest: 234 passed + 6 skipped (verified 2026-04-16 `python -m pytest -q` tail). Target: 234 + N new in this phase; skips unchanged.
- Doctrine countermeasures present: 12 SG entries (`grep -c "SG-" qor/references/doctrine-shadow-genome-countermeasures.md` → 12, 2026-04-16). SG-032 (batch-split-write), SG-033 (positional-to-keyword), SG-036 (inline grounding), SG-038 (prose-code mismatch) all apply.

## Tracks

Each track lists tests first (TDD), then implementation, with the exact test IDs the implementation must turn green.

### Track A — `remediate_read_context.py`

**Purpose**: Read both shadow files, filter `addressed=false`, group by `(event_type, skill, session_id)`.

**Tests (failing first)** in `tests/test_remediate.py`:
1. `test_read_context_reads_both_files` — seeds one LOCAL + one UPSTREAM event (via tmp_path + `monkeypatch` on `LOCAL_LOG_PATH`/`UPSTREAM_LOG_PATH`), asserts both returned.
2. `test_read_context_filters_addressed` — seeds 2 events, one `addressed=True`, one `addressed=False`; asserts only unaddressed returned.
3. `test_read_context_groups_by_key` — seeds 3 events (two share `(event_type, skill, session_id)`, one differs); asserts 2 groups returned, 2-member group correctly keyed.

**Implementation**: `qor/scripts/remediate_read_context.py`. Exports `load_unaddressed_groups() -> dict[tuple[str,str,str], list[dict]]`. Calls `shadow_process.read_all_events()`. Target: under 60 lines.

### Track B — `remediate_pattern_match.py`

**Purpose**: Classify grouped events into one of 5 patterns from SKILL.md Step 2.

**Tests (failing first)** in `tests/test_remediate.py`:
4. `test_classify_gate_loop` — 2+ `gate_override` events against same skill.
5. `test_classify_regression` — 1+ `regression` event.
6. `test_classify_hallucination` — 1+ `hallucination` event.
7. `test_classify_capability_shortfall_aggregation` — 3+ `capability_shortfall` events in one `session_id`.
8. `test_classify_aged_high_severity` — 1+ `aged_high_severity_unremediated` event.
9. `test_classify_empty_returns_none` — no groups in; returns `[]`.

**Implementation**: `qor/scripts/remediate_pattern_match.py`. Exports `classify(groups: dict) -> list[dict]` where each result dict carries `pattern`, `event_ids`, and supporting group metadata. Target: under 90 lines. Priority order encoded as a constant so aged-high-severity wins over capability-shortfall when both would fire on same session.

### Track C — `remediate_propose.py`

**Purpose**: Produce a remediation proposal skeleton per classification.

**Tests (failing first)** in `tests/test_remediate.py`:
10. `test_propose_gate_loop_produces_proposal` — input `pattern=gate-loop`, asserts output has keys `pattern`, `proposal_kind`, `proposal_text`, `addressed_event_ids` (all four).
11. `test_propose_aged_high_severity_proposal` — asserts `proposal_kind` is one of the four allowed kinds (`skill | agent | gate | doctrine`).
12. `test_propose_event_ids_preserved` — input with 3 event_ids, asserts all 3 appear in `addressed_event_ids`.

**Implementation**: `qor/scripts/remediate_propose.py`. Exports `propose(classification: dict) -> dict`. Target: under 80 lines. Pattern-to-kind mapping:

```python
PATTERN_TO_KIND = {
    "gate-loop": "gate",
    "regression": "skill",
    "hallucination": "skill",
    "capability-shortfall aggregation": "agent",
    "aged-high-severity": "doctrine",
}
```

### Track D — `remediate_mark_addressed.py`

**Purpose**: Flip matched events to `addressed=true`, route back to their origin file via `write_events_per_source`.

**Tests (failing first)** in `tests/test_remediate.py`:
13. `test_mark_addressed_flips_events` — seed 2 events in LOCAL via tmp_path + `monkeypatch.setattr(shadow_process, "LOCAL_LOG_PATH", ...)`; mark one; assert that one is `addressed=True` with `addressed_reason` set; the other remains unchanged.
14. `test_mark_addressed_routes_to_origin_file` — seed one LOCAL + one UPSTREAM; mark both; assert LOCAL file still holds only LOCAL event (now addressed) and UPSTREAM file still holds only UPSTREAM event (now addressed). Guards SG-032 (batch-split-write coverage gap).

**Implementation**: `qor/scripts/remediate_mark_addressed.py`. Exports `mark_addressed(event_ids: list[str], session_id: str) -> int` returning count flipped. Uses `shadow_process.read_all_events()` + `id_source_map()` + `write_events_per_source()`. Target: under 70 lines.

**SG-032 note**: this script does NOT create new events; all records exist in the lookup at call time. Split-write falls back to origin file per `id_source_map`. No default-bucket gap.

### Track E — `remediate_emit_gate.py`

**Purpose**: Write `.qor/gates/<session_id>/remediate.json` for downstream audit.

**Tests (failing first)** in `tests/test_remediate.py`:
15. `test_emit_gate_writes_json_at_expected_path` — tmp_path for gate dir; call `emit(proposal, session_id, base_dir=tmp_path)`; assert file exists at `.qor/gates/<sid>/remediate.json`.
16. `test_emit_gate_payload_roundtrips` — read back the written file; `json.loads` yields dict equal to input proposal plus a `ts` field.

**Implementation**: `qor/scripts/remediate_emit_gate.py`. Exports `emit(proposal: dict, session_id: str, base_dir: Path | None = None) -> Path`. Target: under 50 lines.

### Track F — Skill body update

Remove `## Status` / `**STUB (minimal)**` block (lines 85-87 of current file). Append references to the five helper scripts under each of Steps 1-5, mirroring the `qor-shadow-process/SKILL.md` convention (line 60: `Invoke qor/scripts/shadow_process.py via its library interface`).

**No test added**; covered by existing `tests/test_skill_doctrine.py` suite which already asserts skill presence. A new doctrine test is not required since no new keyword doctrine is introduced.

## Affected Files

**New**:
- `docs/plan-qor-phase18-qor-remediate.md` (this file)
- `qor/scripts/remediate_read_context.py`
- `qor/scripts/remediate_pattern_match.py`
- `qor/scripts/remediate_propose.py`
- `qor/scripts/remediate_mark_addressed.py`
- `qor/scripts/remediate_emit_gate.py`
- `tests/test_remediate.py`

**Modified**:
- `qor/skills/sdlc/qor-remediate/SKILL.md` (STUB marker removed; helper references added)
- `pyproject.toml` (version bump 0.7.0 → 0.8.0 at substantiate time)
- `docs/META_LEDGER.md` (Entry #48 gate tribunal, Entry #49 implementation, Entry #50 session seal — adjust if audit v1 VETOs)

**Regenerated** (by `BUILD_REGEN=1 python qor/scripts/compile.py`):
- Variant directories under `processed/` for the updated skill.

File count: 7 new + 3 modified + variant regen = 10 direct edits.

## Constraints

- **No new dependencies**. Python stdlib + jsonschema + pytest only.
- **SG-032**: Track D uses `id_source_map()` from a fresh `read_all_events()` call made in the same function. No new event creation inside `remediate_mark_addressed.py`. Test 14 guards the split.
- **SG-033**: Any `*`-keyword signature new to this phase — grep all callers inside this worktree before committing. Current plan introduces none; `shadow_process.append_event` already exposes `attribution` as keyword-only and we only *call* it, never redefine it.
- **SG-036**: This plan carries inline dated provenance for every file-size/location claim (see Context).
- **SG-038**: Prose references "5 helpers + test file" (6 new code files + 1 plan = 7 new total); code block above lists 7 new; success criteria below lists 16 tests. All three lockstep-consistent.
- **Never** touch `qor-implement/SKILL.md`, `qor-substantiate/SKILL.md`, `tools/reliability/`, or `~/.claude/skills/`.
- Section 4 Razor: each helper under 100 lines (targets: 60/90/80/70/50 per track). Each function under 40 lines.

## Success Criteria

1. `tests/test_remediate.py` contains 16 tests (Tests 1-16 enumerated in Tracks A-E). All pass.
2. Full `python -m pytest -q` reports 250 passed + 6 skipped (234 baseline + 16 new). Run 2x to confirm deterministic.
3. `qor/skills/sdlc/qor-remediate/SKILL.md` no longer contains the string "STUB (minimal)" (`grep -c "STUB" qor/skills/sdlc/qor-remediate/SKILL.md` → 0).
4. All 5 helper scripts exist under `qor/scripts/` and are importable without side effects (`python -c "import sys; sys.path.insert(0,'qor/scripts'); import remediate_read_context, remediate_pattern_match, remediate_propose, remediate_mark_addressed, remediate_emit_gate"` exits 0).
5. `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` passes after each ledger append.
6. Version bumps 0.7.0 → 0.8.0 via `governance_helpers.bump_version("feature")`.
7. `BUILD_REGEN=1 python qor/scripts/compile.py` exits 0 and commits cleanly.

## CI Commands

```bash
# Baseline check
python -m pytest -q  # expect 234 passed, 6 skipped before implement

# After implement
python -m pytest -q  # expect 250 passed, 6 skipped
python -m pytest -q  # run #2 to confirm deterministic

# Helper importability
python -c "import sys; sys.path.insert(0,'qor/scripts'); import remediate_read_context, remediate_pattern_match, remediate_propose, remediate_mark_addressed, remediate_emit_gate; print('ok')"

# Skill update check
grep -c "STUB" qor/skills/sdlc/qor-remediate/SKILL.md  # expect 0

# Variant regen
BUILD_REGEN=1 python qor/scripts/compile.py

# Ledger verify
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md

# Version bump (substantiate phase)
python -c "import sys; sys.path.insert(0,'qor/scripts'); from governance_helpers import bump_version; print(bump_version('feature'))"  # expect 0.8.0
```
