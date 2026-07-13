# Plan: Phase 184 - Reachability probe collection timeout is load-tolerant (GH #264)

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

(none)

## Origin

Research brief docs/research-brief-reachability-timeout-2026-07-13.md (ledger entry #454, session `2026-07-13T0858-c7296a`); GH #264.

## Locked Decisions

- **LD-1: budget correction, not contract change.**
  `grep -nE 'timeout=30' qor/scripts/reachability_probe.py -> 132`; the `except TimeoutExpired: continue` stays (correct for genuine per-candidate failures). New module constant `COLLECTION_TIMEOUT = int(os.environ.get("QOR_REACHABILITY_COLLECTION_TIMEOUT", "120"))` -- reporter-validated default, env-tunable for slower CI. The importability check's 20s stays (not implicated; its child is a bare import).
- **LD-2: no-wait tests.**
  Recorder-monkeypatched `subprocess.run` captures kwargs: one test asserts the collect-only call passes `timeout == COLLECTION_TIMEOUT`; one asserts the env override changes the constant via module reload (importlib.reload under monkeypatched env, restored after). Existing behavioral collection tests remain the functional net.

## Phase 1: Constant + override (TDD first)

### Affected Files

- tests/test_reachability_probe.py - timeout-lock + env-override tests appended
- qor/scripts/reachability_probe.py - COLLECTION_TIMEOUT constant; used at the collect-only call

### Changes

Module-level constant after imports with a two-line comment naming GH #264 and the load-sensitivity rationale; `timeout=30` -> `timeout=COLLECTION_TIMEOUT`.

### Unit Tests

- tests/test_reachability_probe.py::test_collection_subprocess_uses_module_timeout - recorder asserts the passed timeout equals COLLECTION_TIMEOUT and COLLECTION_TIMEOUT == 120 by default (red today: 30 is passed)
- tests/test_reachability_probe.py::test_collection_timeout_env_override - QOR_REACHABILITY_COLLECTION_TIMEOUT=45 + module reload yields COLLECTION_TIMEOUT == 45 (reload restored afterward)

## Feature Inventory Touches

(empty -- QA tooling)

## Definition of Done

### Deliverable: load-tolerant collection probe

- **D1**: Full-suite CPU load can no longer flip the reachability verdict to a false negative (GH #264; the reporter's validated budget shipped, tunable for slower hosts).
- **D2**: LD-1 constant + call-site use; silent-continue semantics unchanged.
- **D3**: Ledger entries for plan/audit/implement/seal; GH #264 disposition.
- **D4**: `test_collection_subprocess_uses_module_timeout` (red today) and `test_collection_timeout_env_override` observe the behaviors.

## CI Commands

- `python -m pytest tests/test_reachability_probe.py -q` - focused suite (run twice for determinism)
- `python -m pytest -q` - full suite
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - ledger chain integrity across the phase's entries
