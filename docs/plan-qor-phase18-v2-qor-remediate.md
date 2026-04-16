## Phase 18 v2 — qor-remediate Full Implementation (remediation of Entry #48 VETO)

**change_class**: feature
**Status**: Active
**Author**: QorLogic Governor
**Date**: 2026-04-16
**Branch**: `phase/18-qor-remediate`
**Target version**: `0.7.0 → 0.8.0` (main reconciles against Phase 17 at merge time)
**Supersedes**: `docs/plan-qor-phase18-qor-remediate.md` (VETO'd — Entry #48)

## Open Questions

None. v2 closes the two Entry #48 violations (V-1 SG-032 recurrence, V-2 missing empty-state test).

## Delta from v1 (inline-grounded)

### V-1 closure: `mark_addressed` surfaces unknown IDs instead of silent drop

v1 Track D asserted "no default-bucket gap" but did not test or specify behavior when the caller passes an event_id that is not in `id_source_map()` (e.g., typo, stale ID, or externally-created event). Under current `shadow_process.write_events_per_source` (lines 159-165 of shadow_process.py per `wc -l` 2026-04-16), unmapped records are silently dropped — textbook SG-032.

v2 change: `mark_addressed(event_ids, session_id) -> tuple[int, list[str]]` returns `(flipped_count, missing_ids)`. Missing IDs are surfaced explicitly. Test 17 below exercises the unknown-id path.

### V-2 closure: empty-state coverage for `load_unaddressed_groups`

v1 Track A had 3 tests; none seeded empty logs. v2 adds Test 18: fresh tmp_path, no events, `load_unaddressed_groups()` returns `{}` (dict, not None).

## Context (inline grounded)

Unchanged from v1 (all 2026-04-16 grounding still valid). Key references:

- `qor/skills/sdlc/qor-remediate/SKILL.md` — 87 lines (`wc -l`, 2026-04-16).
- `qor/scripts/shadow_process.py` — 165 lines (`wc -l`, 2026-04-16). `read_all_events()` at line 142, `id_source_map()` at line 146, `write_events_per_source()` at line 155, `append_event()` at line 65, `LOCAL_LOG_PATH` at line 21, `UPSTREAM_LOG_PATH` at line 22.
- `qor/scripts/check_shadow_threshold.py` — 161 lines (`wc -l`, 2026-04-16). `ESCALATION_EVENT` at line 32.
- `tests/test_shadow.py` — 394 lines (`wc -l`, 2026-04-16). `make_event()` helper at lines 16-41; `mock.patch.object` + tmp_path pattern at lines 342-394.
- Baseline pytest: 234 passed + 6 skipped (verified 2026-04-16).
- Doctrine countermeasures: 12 SG entries (`grep -c "SG-" qor/references/doctrine-shadow-genome-countermeasures.md` → 12, 2026-04-16). SG-032, SG-033, SG-036, SG-038 all applicable.

## Tracks

Each track lists tests first (TDD), then implementation.

### Track A — `remediate_read_context.py`

**Purpose**: Read both shadow files, filter `addressed=false`, group by `(event_type, skill, session_id)`.

**Tests (failing first)** in `tests/test_remediate.py`:
1. `test_read_context_reads_both_files` — seeds one LOCAL + one UPSTREAM event (via tmp_path + `mock.patch.object` on `LOCAL_LOG_PATH`/`UPSTREAM_LOG_PATH`), asserts both returned.
2. `test_read_context_filters_addressed` — seeds 2 events, one `addressed=True`, one `addressed=False`; asserts only unaddressed returned.
3. `test_read_context_groups_by_key` — seeds 3 events (two share `(event_type, skill, session_id)`, one differs); asserts 2 groups returned, 2-member group correctly keyed.
4. **(new, V-2)** `test_read_context_empty_returns_empty_dict` — no events seeded; asserts `load_unaddressed_groups()` returns `{}` (dict).

**Implementation**: `qor/scripts/remediate_read_context.py`. Exports `load_unaddressed_groups() -> dict[tuple[str,str,str], list[dict]]`. Calls `shadow_process.read_all_events()`. Target: under 60 lines.

### Track B — `remediate_pattern_match.py`

**Purpose**: Classify grouped events into one of 5 patterns from SKILL.md Step 2.

**Tests (failing first)** in `tests/test_remediate.py`:
5. `test_classify_gate_loop` — 2+ `gate_override` events against same skill.
6. `test_classify_regression` — 1+ `regression` event.
7. `test_classify_hallucination` — 1+ `hallucination` event.
8. `test_classify_capability_shortfall_aggregation` — 3+ `capability_shortfall` events in one `session_id`.
9. `test_classify_aged_high_severity` — 1+ `aged_high_severity_unremediated` event.
10. `test_classify_empty_returns_empty_list` — no groups in; returns `[]`.

**Implementation**: `qor/scripts/remediate_pattern_match.py`. Exports `classify(groups: dict) -> list[dict]` where each result dict carries `pattern`, `event_ids`, and supporting group metadata. Target: under 90 lines. Priority order encoded as a constant so aged-high-severity wins over capability-shortfall when both would fire on the same session.

### Track C — `remediate_propose.py`

**Purpose**: Produce a remediation proposal skeleton per classification.

**Tests (failing first)** in `tests/test_remediate.py`:
11. `test_propose_gate_loop_produces_proposal` — input `pattern=gate-loop`, asserts output has keys `pattern`, `proposal_kind`, `proposal_text`, `addressed_event_ids` (all four).
12. `test_propose_aged_high_severity_proposal` — asserts `proposal_kind` is one of the four allowed kinds (`skill | agent | gate | doctrine`).
13. `test_propose_event_ids_preserved` — input with 3 event_ids, asserts all 3 appear in `addressed_event_ids`.

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

**Purpose**: Flip matched events to `addressed=true`, route back to their origin file via `write_events_per_source`. Surface unknown IDs instead of silent drop.

**Tests (failing first)** in `tests/test_remediate.py`:
14. `test_mark_addressed_flips_events` — seed 2 events in LOCAL via tmp_path + `mock.patch.object(shadow_process, "LOCAL_LOG_PATH", ...)`; mark one; assert that one is `addressed=True` with `addressed_reason` set; the other remains unchanged.
15. `test_mark_addressed_routes_to_origin_file` — seed one LOCAL + one UPSTREAM; mark both; assert LOCAL file still holds only LOCAL event (now addressed) and UPSTREAM file still holds only UPSTREAM event (now addressed). Guards SG-032 split-write.
16. **(new, V-1)** `test_mark_addressed_surfaces_missing_ids` — seed 1 real event, call `mark_addressed([real_id, "deadbeef"*8], sid)`; assert `(1, ["deadbeef"*8])` returned. Guards SG-032 silent-drop recurrence.

**Implementation**: `qor/scripts/remediate_mark_addressed.py`. Exports `mark_addressed(event_ids: list[str], session_id: str) -> tuple[int, list[str]]` returning `(flipped_count, missing_ids)`. Uses `shadow_process.read_all_events()` + `id_source_map()` + `write_events_per_source()`. Target: under 80 lines (+10 vs v1 for missing-id tracking).

**SG-032 closure**: unknown IDs routed into `missing_ids` return value, not silently dropped. Test 16 enforces.

### Track E — `remediate_emit_gate.py`

**Purpose**: Write `.qor/gates/<session_id>/remediate.json` for downstream audit.

**Tests (failing first)** in `tests/test_remediate.py`:
17. `test_emit_gate_writes_json_at_expected_path` — tmp_path for gate dir; call `emit(proposal, session_id, base_dir=tmp_path)`; assert file exists at `.qor/gates/<sid>/remediate.json`.
18. `test_emit_gate_payload_roundtrips` — read back the written file; `json.loads` yields dict equal to input proposal plus a `ts` field.

**Implementation**: `qor/scripts/remediate_emit_gate.py`. Exports `emit(proposal: dict, session_id: str, base_dir: Path | None = None) -> Path`. Target: under 50 lines.

### Track F — Skill body update

Remove `## Status` / `**STUB (minimal)**` block (lines 85-87 of current file per `wc -l` 2026-04-16). Append references to the five helper scripts under each of Steps 1-5, mirroring the `qor-shadow-process/SKILL.md` convention (line 60 of that file: "Invoke `qor/scripts/shadow_process.py` via its library interface").

**No test added**; existing `tests/test_skill_doctrine.py` already asserts skill presence.

## Affected Files

**New**:
- `docs/plan-qor-phase18-qor-remediate.md` (v1 — kept for audit trail)
- `docs/plan-qor-phase18-v2-qor-remediate.md` (this file)
- `qor/scripts/remediate_read_context.py`
- `qor/scripts/remediate_pattern_match.py`
- `qor/scripts/remediate_propose.py`
- `qor/scripts/remediate_mark_addressed.py`
- `qor/scripts/remediate_emit_gate.py`
- `tests/test_remediate.py`

**Modified**:
- `qor/skills/sdlc/qor-remediate/SKILL.md` (STUB marker removed; helper references added)
- `pyproject.toml` (version bump 0.7.0 → 0.8.0 at substantiate time)
- `docs/META_LEDGER.md` (Entry #48 v1 VETO, Entry #49 v2 PASS, Entry #50 implementation, Entry #51 session seal)

**Regenerated** (by `BUILD_REGEN=1 python qor/scripts/compile.py`):
- Variant directories under `processed/` for the updated skill.

File count: 8 new (v1 plan + v2 plan + 5 helpers + 1 test file) + 3 modified = 11 direct edits.

## Constraints

- **No new dependencies**. Python stdlib + jsonschema + pytest only.
- **SG-032**: Track D's `mark_addressed` returns `(flipped_count, missing_ids)`. Unknown IDs never silently drop. Test 16 enforces.
- **SG-033**: Plan introduces no new `*`-keyword signatures. Callers of `shadow_process.append_event(..., attribution=...)` use keyword form.
- **SG-036**: Inline dated provenance for every file-size/location claim (see Context).
- **SG-038**: Prose cites "5 helpers + 1 test file + 2 plan files = 8 new"; code block lists 8 new; success criteria cite 18 tests. All three lockstep.
- **Never** touch `qor-implement/SKILL.md`, `qor-substantiate/SKILL.md`, `tools/reliability/`, or `~/.claude/skills/`.
- Section 4 Razor: each helper under 100 lines (targets: 60/90/80/80/50 per track — Track D bumped from 70 to 80 to accommodate missing-ids tracking). Each function under 40 lines.

## Success Criteria

1. `tests/test_remediate.py` contains 18 tests (enumerated Tests 1-18 in Tracks A-E). All pass.
2. Full `python -m pytest -q` reports 252 passed + 6 skipped (234 baseline + 18 new). Run 2x to confirm deterministic.
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
python -m pytest -q  # expect 252 passed, 6 skipped
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
