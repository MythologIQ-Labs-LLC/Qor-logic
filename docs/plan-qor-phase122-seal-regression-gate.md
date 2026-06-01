# Plan: Seal-time feature-regression gate — flip fail-closed + logged override

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: Completes GH #155 against the EXISTING `qor.scripts.feature_index_verify` (Phase 114), which already detects outside-scope `verified->unverified` regressions vs a prior-seal snapshot and returns exit 1 when not in `--warn-only`. This phase (1) adds a per-seal logged `--override` escape and (2) flips the `/qor-substantiate` Step 6 wiring from `--warn-only` to fail-closed. It does not change the snapshot baseline mechanism (`.qor/feature_index_snapshots/<sid>.json`) or the regression-detection logic.
- non_goals: A new regression module (superseded — `feature_index_verify` already exists); a git-diff baseline (the module uses persisted snapshots); deep per-feature test re-run (Step 6's reporting pass already re-runs cited tests); measuring/auto-tuning the false-positive rate.
- exclusions: Repos with no `docs/FEATURE_INDEX.md` or no prior snapshot record the existing `feature_index: skip` disclosed-skip (exit 0).

## Open Questions

None. Resolved: the regression ABORT already ships in `feature_index_verify`; #155's residual gap is the Step 6 `--warn-only` downgrade (Phase 114 shipped it warn-only "until the false-positive rate is measured") plus the missing per-seal **logged** override the AC requires. Operator authorized flipping to fail-closed. The `--override` escape emits a `gate_override` shadow event tagged `details.gate = feature_index_verify` (reuses the existing event_type enum; no schema churn).

## Context

GH #155 (umbrella #147; follow-on to #40). PR #68 shipped the advisory FEATURE_INDEX reporting pass; Phase 114 (GH #155/#40) then shipped `qor.scripts.feature_index_verify` — the outside-scope-regression ABORT — but wired it into Step 6 with `--warn-only` (print-and-pass) for graduated rollout. #155's AC ("blocks PASS fail-closed, with an explicit logged override path") is therefore unmet on two counts: the wiring never aborts, and there is no per-seal logged override (only the blanket `--warn-only` bypass). This phase closes both.

## Feature Inventory Touches

(`docs/FEATURE_INDEX.md` absent in this repo; declared for traceability. Touches `qor/` + skills + tests, not `src/`.)

- entry_id: `n/a` · operation: `MODIFIED` · test_path: `tests/test_feature_index_verify_gate.py` · test_descriptor: `feature_index_verify.main returns 1 on an outside-scope verified->unverified regression without --warn-only, and returns 0 + logs a gate_override event with --override`

## Phase 1: Logged override on `feature_index_verify` (`qor/scripts/feature_index_verify.py`)

### Affected Files

- `tests/test_feature_index_verify_gate.py` - NEW. Behavioral tests for the fail-closed exit and the logged `--override` (see Unit Tests). Written first; red before `--override` exists.
- `qor/scripts/feature_index_verify.py` - add an `--override` flag: when a regression is detected and `--override` is passed, emit a logged `gate_override` shadow event (`details.gate = "feature_index_verify"`, `details.regressions = [...]`) and return 0. Without `--override` (and without `--warn-only`), the existing `return 1` ABORT path is unchanged.

### Changes

```python
parser.add_argument("--override", action="store_true",
                    help="accept the regression; emit a logged gate_override event and pass")
# ... in the regression branch, after printing REGRESSION lines:
#   if args.warn_only: print("WARN-only; not aborting"); return 0
#   if args.override:
#       shadow_process.append_event({... "event_type": "gate_override",
#           "details": {"gate": "feature_index_verify", "regressions": [...] } ...})
#       print("feature_index: OVERRIDE (regression accepted; gate_override logged)")
#       return 0
#   print("feature_index: ABORT (outside-scope regression)"); return 1
```

`--warn-only` is retained (backward-compatible) but is no longer used by the seal wiring; `--override` is the per-seal logged escape the AC requires. De-complecting: detection (unchanged `tally`) stays separate from the new escape/exit policy in `main`.

### Unit Tests

- `tests/test_feature_index_verify_gate.py::test_main_aborts_on_outside_scope_regression` - write a `FEATURE_INDEX.md` with `FX091 unverified` and a prior snapshot (`write_seal_snapshot`) recording `FX091 verified`; `main(["--repo-root", d, "--snapshot", sid])` returns 1 (fail-closed; no `--warn-only`).
- `::test_main_warn_only_still_passes` - same regression with `--warn-only`; `main` returns 0 (backward-compat retained).
- `::test_main_override_exits_0_and_logs_event` - same regression with `--override`; `main` returns 0 AND one `gate_override` event with `details.gate == "feature_index_verify"` is appended (assert via monkeypatched `shadow_process.append_event`).
- `::test_main_no_regression_returns_0` - snapshot and current both `FX091 verified`; `main` returns 0 with no event.
- `::test_main_skip_when_index_absent` - no `FEATURE_INDEX.md`; `main` returns 0 and prints a skip line.

## Phase 2: Flip Step 6 wiring fail-closed

### Affected Files

- `tests/test_feature_index_verify_gate.py` - add the wiring assertions (prompt-contract).
- `qor/skills/governance/qor-substantiate/SKILL.md` - Step 6: change the invocation from `feature_index_verify --snapshot <id> --warn-only` to fail-closed `qor-logic scripts feature_index_verify --snapshot <prior-seal-session-id> || ABORT`, and document `--override` as the explicit logged escape. Update the surrounding prose so it no longer says the gate runs warn-only.
- `qor/dist/variants/**` - regenerated via `qor-logic compile`.

### Changes

Drop `--warn-only` from the seal invocation so the existing `return 1` aborts the seal; add the `|| ABORT` idiom; name `--override` as the logged escape for an intentional accepted regression. The disclosed-skip (`feature_index: skip` on absent index) is unchanged.

### Unit Tests

- `tests/test_feature_index_verify_gate.py::test_substantiate_wiring_is_failclosed` - read `qor-substantiate/SKILL.md`; assert the Step 6 `feature_index_verify` invocation is followed by `|| ABORT` and that the seal invocation line does NOT contain `--warn-only`.
- `::test_substantiate_documents_override_escape` - assert the SKILL.md names `--override` as the escape.

## Phase 3: Doctrine

### Affected Files

- `qor/references/doctrine-feature-inventory.md` - note the Phase 122 flip: the Step 6 regression gate is now fail-closed (was Phase 114 `--warn-only`); `--override` is the logged escape (`gate_override` event); snapshot baseline unchanged.
- `tests/test_feature_index_verify_gate.py::test_doctrine_marks_failclosed` - functional doc-contract: the doctrine states the gate is fail-closed at seal and names the `--override` escape.

## Definition of Done

### Deliverable: fail-closed seal regression gate

- **D1**: /qor-substantiate fail-closes on an outside-scope `verified->unverified` regression, with an explicit logged `--override` escape.
- **D2**: `--override` flag + logged `gate_override` emission in `qor/scripts/feature_index_verify.py`; Step 6 invocation drops `--warn-only` and adds `|| ABORT`.
- **D3**: doctrine-feature-inventory.md flip note; META_LEDGER seal entry; version bump; variants recompiled.
- **D4**: `tests/test_feature_index_verify_gate.py::test_main_aborts_on_outside_scope_regression` + `::test_main_override_exits_0_and_logs_event` + `::test_substantiate_wiring_is_failclosed`.

## CI Commands

- `python -m pytest tests/test_feature_index_verify_gate.py tests/test_feature_index_verify_helper.py -q` — new gate behavior + existing helpers.
- `python -m pytest -q` — full suite green before substantiate.
