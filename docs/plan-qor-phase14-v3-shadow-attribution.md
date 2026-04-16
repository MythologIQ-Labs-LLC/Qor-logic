## Phase 14 v3 — Shadow Attribution (remediation of Entry #32 VETO)

**change_class**: feature
**Status**: Active
**Author**: QorLogic Governor
**Date**: 2026-04-15
**Branch**: `phase/14-shadow-attribution`
**Supersedes**: `docs/plan-qor-phase14-v2-shadow-attribution.md` (VETO'd — Entry #32)

## Open Questions

None. All Entry #32 violations have prescribed fixes accepted in dialogue.

## Delta from v2

v3 is v2 with 4 surgical changes closing Entry #32 violations. All v2 Tracks (A through F) remain; only the affected sections are restated below. Unchanged v2 sections (Track A doctrine, Track B skill wiring, Track D collector fallback) are incorporated by reference.

### V-1 closure: classify-at-creation (Track E, `check_shadow_threshold.py`)

**Audit prescription** (verbatim): "rewrite `sweep()` to call `shadow_process.append_event(new_event, attribution="UPSTREAM")` immediately instead of batching, eliminating the need for a post-hoc split."

Current `sweep()` (lines 39-87 of `check_shadow_threshold.py`) accumulates `new_escalations` in a list, appends them to `combined = events + new_escalations`, then the caller writes the whole batch via `write_events(updated, args.log)`.

v3 change: `sweep()` no longer returns new escalation events in its result list. Instead, it calls `shadow_process.append_event(new_event, attribution="UPSTREAM")` for each escalation event inline. The function signature changes:

```python
def sweep(
    events: list[dict],
    now: datetime,
    log_path: Path | None = None,
) -> tuple[list[dict], int, int]:
    """Apply stale expiry + self-escalation; return (updated_events, escalation_count, breach_sum).

    Escalation events are appended immediately via shadow_process.append_event
    with attribution="UPSTREAM" (infrastructure-generated). They are NOT included
    in updated_events to avoid double-write during the caller's batch rewrite.
    """
```

Caller flow becomes:
1. Read events from both files (or `--log` override).
2. `sweep(events, now, log_path)` — stale-expires in-place; escalation events written immediately to UPSTREAM.
3. Write back stale-expired originals per-source (using `write_events_per_source`; see V-3 closure).

The `log_path` parameter allows tests to direct escalation appends to a temp file.

**Why this is simpler**: no post-hoc id-to-file lookup for new events. Escalation events are classified at the moment of creation — the only moment their attribution is unambiguous. SG-032 closed.

### V-2 closure: update positional callers (Track F, `tests/test_shadow.py`)

**Audit prescription** (verbatim): "Explicitly update `tests/test_shadow.py:329` and `tests/test_shadow.py:341` from `shadow_process.append_event(e, log)` to `shadow_process.append_event(e, log_path=log)`."

Two call sites, verified via grep (`tests/test_shadow.py:329`, `tests/test_shadow.py:341`):

```python
# Before (positional — breaks under keyword-only *)
shadow_process.append_event(e, log)

# After
shadow_process.append_event(e, log_path=log)
```

Additional grep verification required at implementation time: confirm no other positional callers exist in `tests/test_e2e.py`, `tests/test_gates.py`, `tests/test_qor_audit_runtime.py`, `tests/test_collect.py`. (v2 grounding found only these 2; re-verify to close SG-033.)

### V-3 closure: extract `write_events_per_source` helper (Track C, `shadow_process.py`)

**Audit prescription** (verbatim): "extract a `write_events_per_source(events, src_map)` helper into `shadow_process.py` (keeps `create_shadow_issue.py` thin — callers shrink by ~10 lines each)."

Add to `shadow_process.py`:

```python
def write_events_per_source(
    events: list[dict],
    src_map: dict[str, Path],
) -> None:
    """Split events by source file and write each batch back.

    Events whose id is not in src_map are skipped (caller is responsible
    for handling new events before calling this function).
    """
    by_file: dict[Path, list[dict]] = {}
    for e in events:
        path = src_map.get(e["id"])
        if path is not None:
            by_file.setdefault(path, []).append(e)
    for path, batch in by_file.items():
        write_events(batch, path)
```

Callers in `check_shadow_threshold.py` and `create_shadow_issue.py` replace their inline split-write with:

```python
src_map = shadow_process.id_source_map()
shadow_process.write_events_per_source(updated, src_map)
```

**Line count impact on `create_shadow_issue.py`**: removes ~15 lines of inline split logic from `flip_events_only`, `mark_resolved`, and main flow; adds ~3 lines of import + call. Net delta: ~-12 lines. 227 - 12 + ~10 (dual-file read plumbing) = ~225. Under 250. Razor closed.

### V-4 closure: fix count header

Affected Files summary header: "Modified — scripts (5)" → "Modified — scripts (6)".

## Restated Track C — `shadow_process.py` (v3 additions over v2)

v2 Track C additions remain (module constants, `log_path_for()`, `append_event` signature, `read_all_events()`, `id_source_map()`). v3 adds:

- `write_events_per_source(events, src_map)` — shared helper for dual-file write-back.

Estimated `shadow_process.py` total: 121 (current) + ~24 (v2) + ~12 (v3 helper) = ~157 lines. Under 250.

## Restated Track E — Downstream writer callers (v3 revision)

v2 Track E changes to `gate_chain.py:100` and `qor_audit_runtime.py:66` remain unchanged (`attribution="UPSTREAM"`).

**`check_shadow_threshold.py`** (revised from v2):

- Default read: `shadow_process.read_all_events()` when `--log` not given.
- `sweep()` signature gains `log_path` parameter; escalation events appended immediately with `attribution="UPSTREAM"`.
- Write-back of stale-expired originals via `shadow_process.write_events_per_source(updated, src_map)`.
- `--log <path>` override retained: single-file mode for tests.

**`create_shadow_issue.py`** (revised from v2):

- `flip_events_only`, `mark_resolved`, and main flow use `shadow_process.write_events_per_source()`.
- `--log <path>` override retained.

## Restated Track F — Tests (v3 additions over v2)

v2 Track F tests remain (9 + 2 + 3 + 1 = 15 tests). v3 adds:

### `tests/test_shadow.py` (1 test added, total +3 over baseline)

- `test_escalation_events_not_dropped_during_sweep` — create events in both LOCAL and UPSTREAM tmp files; run `sweep()` with an aged high-severity event triggering escalation; verify escalation event is readable from UPSTREAM file (not lost). Closes V-1.

### `tests/test_shadow_attribution.py` (1 test added, total 10)

- `test_write_events_per_source_splits_correctly` — create 2 events in LOCAL tmp, 1 in UPSTREAM tmp; modify all 3 in-memory; call `write_events_per_source(events, src_map)`; verify each file contains only its events. Closes V-3 helper correctness.

## Affected Files (v3 complete, supersedes v2 summary)

### New (3)
- `qor/references/doctrine-shadow-attribution.md`
- `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md`
- `tests/test_shadow_attribution.py`

### Modified — skills (4)
- `qor/skills/governance/qor-shadow-process/SKILL.md`
- `qor/skills/governance/qor-audit/SKILL.md`
- `qor/skills/memory/track-shadow-genome.md`
- `qor/skills/meta/qor-meta-track-shadow/SKILL.md`

### Modified — scripts (6)
- `qor/scripts/shadow_process.py`
- `qor/scripts/collect_shadow_genomes.py`
- `qor/scripts/gate_chain.py`
- `qor/scripts/qor_audit_runtime.py`
- `qor/scripts/check_shadow_threshold.py`
- `qor/scripts/create_shadow_issue.py`

### Modified — tests (3)
- `tests/test_shadow.py` (+3: classify-upstream, id-source-map, escalation-not-dropped)
- `tests/test_skill_doctrine.py` (+3: attribution, both-log-files, tracking-skills)
- `tests/test_collect.py` (+1: reads-upstream-file)

## Constraints

- **No changes to narrative `docs/SHADOW_GENOME.md`** (doctrine §6 declares it out of scope).
- **Tests before code** for `test_shadow_attribution.py` and the 3 new `test_shadow.py` entries.
- **Reliability**: pytest 2x consecutive identical results before commit.
- **W-1 literal-keyword discipline**: doctrine strings match test substrings verbatim (`UPSTREAM`, `LOCAL`, `Worked example`, `out of scope`).
- **Rule 4 (Rule = Test)**: `append_event` attribution-required → test. Collector legacy warning → test. Escalation not dropped → test. `write_events_per_source` correctness → test.
- **`attribution` keyword-only** on `append_event` — prevents positional misorder, preserves `log_path=` test overrides.
- **`gate_writes:` YAML list** — no runtime parser exists (verified); doctrinal convention only.
- **SG-032 discipline**: no post-hoc id lookup for events created mid-cycle; classify at creation.
- **SG-033 discipline**: all positional callers of changed signatures updated (verified via grep).

## Success Criteria

- [ ] Doctrine has 6 sections; all literal-match tests green.
- [ ] Upstream starter file exists.
- [ ] 4 skills reference doctrine + both files.
- [ ] `shadow_process.py`: `LOCAL_LOG_PATH`, `UPSTREAM_LOG_PATH`, `log_path_for()`, `append_event(attribution=...)`, `read_all_events()`, `id_source_map()`, `write_events_per_source()` all present.
- [ ] Collector reads UPSTREAM; legacy fallback emits the expected stderr line.
- [ ] 4 downstream callers classify correctly; 2 read+writer callers use `write_events_per_source()`.
- [ ] Escalation events in `check_shadow_threshold.py` appended immediately to UPSTREAM (not batched).
- [ ] `tests/test_shadow.py:329,341` updated to keyword `log_path=log`.
- [ ] Tests: +10 attribution + 3 shadow + 3 skill_doctrine + 1 collect = **+17 new**. Baseline 202 → **219 passing**, skipped unchanged.
- [ ] `check_variant_drift.py` clean after `BUILD_REGEN=1`.
- [ ] `ledger_hash.py verify docs/META_LEDGER.md` → chain valid.
- [ ] Substantiation: `0.3.0 → 0.4.0`; annotated tag `v0.4.0`.

## CI Commands

```bash
python -m pytest tests/test_shadow_attribution.py tests/test_shadow.py tests/test_skill_doctrine.py tests/test_collect.py -v
python -m pytest tests/
BUILD_REGEN=1 python qor/scripts/check_variant_drift.py
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md
git tag --list 'v*' | tail -3
```
