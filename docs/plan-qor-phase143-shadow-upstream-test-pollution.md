# Plan: Phase 143 -- stop shadow-genome test pollution + prune residue

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

None. Root cause grep-verified: `tests/test_override_friction_escalator.py::test_emit_gate_override_succeeds_with_justification`
calls `gate_chain.emit_gate_override(...)`, which appends the event via
`shadow_process.append_event(event, attribution="UPSTREAM")` ->
`shadow_process.log_path_for("UPSTREAM")` -> the module global `UPSTREAM_LOG_PATH`
(`qor/scripts/shadow_process.py:25,60-62`) = the tracked `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md`.
The test monkeypatches only `override_friction._shadow_log_path` (the friction-check reader), not the
append target, so each run emits one real `sess-1` event into the tracked file (78 accumulated;
`grep -c '"session_id":"sess-1"' docs/PROCESS_SHADOW_GENOME_UPSTREAM.md` -> 78).

## Phase 1: redirect the upstream append in the emit tests, prune residue, guard

### Affected Files

- `tests/test_override_friction_escalator.py` - in the two `emit_gate_override` tests, also
  `monkeypatch.setattr(shadow_process, "UPSTREAM_LOG_PATH", tmp_path / "upstream.jsonl")` so the
  event append lands in tmp, not the tracked file.
- `tests/test_shadow_upstream_no_test_pollution.py` (NEW) - guard + behavioral redirect test.
- `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md` - delete the 78 `sess-1` test-pollution lines.

### Changes

Test fix: import `from qor.scripts import shadow_process`; in
`test_emit_gate_override_succeeds_with_justification` (and defensively the `_raises_` variant) add
`monkeypatch.setattr(shadow_process, "UPSTREAM_LOG_PATH", tmp_path / "upstream.jsonl")` before the
`emit_gate_override` call. `append_event` resolves the target via `log_path_for("UPSTREAM")` which
reads the module global, so the patch redirects the write.

Prune: remove every line in `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md` whose `session_id` is `sess-1`
(the synthetic test session); keep all real events.

### Unit Tests

- `tests/test_shadow_upstream_no_test_pollution.py`:
  - `test_upstream_file_has_no_test_session_events` - parse the tracked
    `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md`; assert zero events with `session_id == "sess-1"` (proves
    the residue is pruned and no test re-pollutes it; reds CI on regression).
  - `test_emit_gate_override_append_respects_patched_upstream_path` - with
    `UPSTREAM_LOG_PATH` patched to a tmp file and the friction log patched to a 3-event tmp log,
    `gate_chain.emit_gate_override(..., justification=<valid>)` writes the event to the tmp upstream
    file and leaves the real tracked file untouched (assert the tmp file gained one `gate_override`
    line; assert the real file's `sess-1` count stays 0).

## Definition of Done

### Deliverable: D-pollution-stop

- **D1**: no test writes a synthetic event into the tracked upstream shadow-genome file, and the
  accumulated residue is gone.
- **D2**: the two emit tests patch `shadow_process.UPSTREAM_LOG_PATH`; 78 `sess-1` lines removed from
  `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md`.
- **D3**: ledger SESSION SEAL records the fix; no doctrine/term change (minimal tier).
- **D4**: `test_upstream_file_has_no_test_session_events` (0 sess-1 events) +
  `test_emit_gate_override_append_respects_patched_upstream_path` (write lands in tmp, real file
  unchanged).

## CI Commands

- `python -m pytest tests/test_shadow_upstream_no_test_pollution.py tests/test_override_friction_escalator.py -q` -- the guard + fixed tests.
- `python -m pytest -q` -- full suite green.
- `grep -c '"session_id":"sess-1"' docs/PROCESS_SHADOW_GENOME_UPSTREAM.md` -- expect 0.
