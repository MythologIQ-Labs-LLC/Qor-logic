# Plan: Phase 159 / GH #223 — seal_entry_check plan-name fallback

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

None. The issue's "Expected" section is explicit: a non-conforming plan filename
must not hard-block the seal-entry consistency check (which is about the LEDGER
entry, not the filename); derive the phase from the latest ledger entry and WARN
instead of rc=1.

## Problem

`seal_entry_check._main` (substantiate Step 7.7, `|| ABORT`) calls
`governance_helpers.derive_phase_metadata(args.plan)`, whose strict
`_PHASE_FILENAME_RE = ^plan-qor-phase(\d+)-([a-z0-9-]+)\.md$` rejects any
downstream plan name (e.g. the sibling governance repository's `plan-<slug>.md`). On rejection `_main`
prints `plan path resolution failed` and returns 1, blocking `/qor-substantiate`
for a cryptographically valid seal. Verified:

> `grep -nE "derive_phase_metadata|plan path resolution failed|return 1" qor/reliability/seal_entry_check.py`
> -> lines 230-233: the hard-fail path.

The `--auto` path already derives the phase from the latest entry via
`check_latest` (Phase 156), which runs the same GOV-01 content_hash<->cited-plan
binding. The fix routes the non-conforming `--plan` case through that same
fallback.

## Phase 1: ledger-derived phase fallback on non-conforming plan name

### Affected Files

- `tests/test_seal_entry_check.py` - EDIT. Behavioral tests for the fallback:
  non-conforming name still PASSes a valid latest entry (with WARN), still FAILs
  a broken latest entry (fallback is not a blanket bypass), and a conforming
  name keeps using the filename-derived phase.
- `qor/reliability/seal_entry_check.py` - EDIT. In `_main`, when
  `derive_phase_metadata` raises `ValueError`/`FileNotFoundError`, emit a WARN to
  stderr and delegate to `check_latest(args.ledger)` instead of returning 1.

### Changes

In `_main`'s non-`--auto` branch, replace the `except ... : return 1` with a
fallback: print `WARN: plan filename not phase-tagged (<reason>); deriving phase
from the latest ledger entry instead.` to stderr, then `result =
check_latest(args.ledger)` with `label = "latest (plan-name fallback)"`. The
conforming path is unchanged (`derive_phase_metadata` succeeds ->
`check(phase_num)`). The consistency guarantee is preserved: `check_latest`
derives the phase from the entry and `check` still recomputes content_hash from
the entry's cited plan (GOV-01), so a real inconsistency still FAILs.

### Unit Tests

- `tests/test_seal_entry_check.py`:
  - `test_main_nonconforming_plan_name_falls_back_and_passes` — build a ledger
    whose latest entry is a valid SESSION SEAL; call
    `_main(["--ledger", L, "--plan", "plan-monitor-theme-inheritance.md"])`;
    assert rc == 0 and a `WARN` line was written to stderr (capsys).
  - `test_main_nonconforming_plan_name_still_fails_broken_entry` — same
    non-conforming plan name but tamper the latest entry's chain hash; assert
    rc == 1 (the fallback still runs the consistency check; it is not a bypass).
  - `test_main_conforming_plan_name_uses_filename_phase` — a conforming
    `plan-qor-phase158-x.md` whose phase (158) does NOT match the latest entry's
    phase yields a phase-mismatch FAIL (rc == 1), proving the conforming path
    still derives the phase from the filename, unchanged.

## Definition of Done

### Deliverable: plan-name fallback

- **D1**: A valid seal whose plan uses a non-`plan-qor-phase<N>` name passes
  Step 7.7 with a WARN, not a hard ABORT; real inconsistencies still FAIL.
- **D2**: `seal_entry_check._main` delegates to `check_latest` on a
  `derive_phase_metadata` raise; no signature change to `check`/`check_latest`.
- **D3**: Ledger SESSION SEAL entry records the hotfix; CHANGELOG `### Fixed`.
- **D4**: `tests/test_seal_entry_check.py::test_main_nonconforming_plan_name_falls_back_and_passes`
  and `::test_main_nonconforming_plan_name_still_fails_broken_entry` pass.

## CI Commands

- `python -m pytest tests/test_seal_entry_check.py -v` — fallback + regression behavior.
- `python -m pytest tests/ -q` — full suite stays green.
- `python -m qor.reliability.seal_entry_check --ledger docs/META_LEDGER.md --auto` — committed-seal re-verify unaffected.
