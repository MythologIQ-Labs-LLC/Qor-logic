# Plan: SG-MergePaceThrottle-A enforcement + full wiring (combines #153 + #154)

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: Completes the SG-MergePaceThrottle-A throttle family by promoting both companion detectors out of WARN-only. **#153**: `merge_velocity_check` gains a logged `--override`; `/qor-substantiate` Step 4.6.8 flips from `|| true` to fail-closed (`|| ABORT`) so an `exceeded` grade holds the seal unless the operator passes `--override` (emits a `gate_override` shadow event). **#154**: `workspace_fragility_check`'s `FragilityAssessment` regains the dropped `stabilization_capacity` + `shared_surface_risk` fields and the `branch_only` recommended action, and the detector is wired into `/qor-plan` (planning-flow checkpoint) and `/qor-implement` (impl-phase scope-boundary warning), both WARN-only.
- non_goals: Changing the velocity/fragility scoring thresholds; making the `/qor-plan` + `/qor-implement` fragility checkpoints fail-closed (they stay WARN-only — only the substantiate merge-velocity gate becomes enforcing); auto-isolating branches (the controls are imposed-by-blocking-the-seal + the recommended action, not by mutating git).
- exclusions: Non-git hosts / shallow clones where the velocity window is unavailable (the detector already degrades; the gate's `--override` path covers it).

## Open Questions

None. #153 + #154 are the two halves of the SG-MergePaceThrottle-A family (backward `merge_velocity_check` + forward `workspace_fragility_check`, explicit companions in the doctrine); #154 restores fields that already live in #153's script. Combining keeps the contract reconciliation in one cycle. Enforcement posture is fixed by #153's AC (impose-with-logged-override); the override mirrors the Phase 122 `feature_index_verify --override` pattern.

## Feature Inventory Touches

(`docs/FEATURE_INDEX.md` absent; declared for traceability. Touches `qor/scripts` + skills + tests.)

- entry_id: `n/a` · operation: `MODIFIED` · test_path: `tests/test_merge_throttle_enforcement.py` · test_descriptor: `merge_velocity_check.main returns 1 on an exceeded grade without --override and 0 + logs a gate_override with --override (grade mocked, no live-git); workspace_fragility_check assessment carries stabilization_capacity / shared_surface_risk and recommends branch_only when shared-surface risk is high`

## Phase 1: Merge-velocity enforcement (#153) — `qor/scripts/merge_velocity_check.py`

### Affected Files

- `tests/test_merge_throttle_enforcement.py` - NEW. Behavioral tests (grade mocked to avoid the live-git flake) for enforce + override (see Unit Tests). Written first; red before `--override` exists.
- `qor/scripts/merge_velocity_check.py` - add `--override`: on `exceeded` + `--override`, emit a `gate_override` shadow event (`details.gate = merge_velocity_check`) and exit 0; without it, `exceeded` still exits 1.
- `qor/skills/governance/qor-substantiate/SKILL.md` - Step 4.6.8: change `merge_velocity_check ... || true` to `|| ABORT`; document the `--override` escape (logged) for an intentional high-velocity seal.

### Changes

```python
parser.add_argument("--override", action="store_true",
                    help="accept an 'exceeded' grade for this seal; emit a logged gate_override and pass")
# after the grade is computed and printed:
#   if grade == "exceeded":
#       if args.override:
#           shadow_process.append_event({... "event_type": "gate_override",
#               "details": {"gate": "merge_velocity_check", "grade": grade,
#                           "recommended_action": ev.recommended_action}})
#           return 0
#       return 1
#   return 0
```

The substantiate wiring becomes `qor-logic scripts merge_velocity_check --repo-root . --window-days 7 || ABORT`; the operator re-runs with `--override` to seal anyway (recorded). De-complecting: detection (`_grade`/`_build_evidence`) is unchanged; only the exit policy + the logged escape are added.

### Unit Tests

- `tests/test_merge_throttle_enforcement.py::test_main_aborts_on_exceeded` - monkeypatch the assessment builder to return an `exceeded` grade; `main(["--repo-root", d])` returns 1.
- `::test_main_override_exits_0_and_logs_event` - same mocked `exceeded` + `--override`; `main` returns 0 AND one `gate_override` event with `details.gate == "merge_velocity_check"` is appended (monkeypatched `shadow_process.append_event`).
- `::test_main_healthy_returns_0` - mocked `healthy` grade; `main` returns 0, no event.

## Phase 2: Fragility contract + plan/implement wiring (#154) — `qor/scripts/workspace_fragility_check.py`

### Affected Files

- `tests/test_merge_throttle_enforcement.py` - add the fragility-contract + wiring assertions.
- `qor/scripts/workspace_fragility_check.py` - add `stabilization_capacity` (mirror of grade in healthy/strained/exceeded vocab) + `shared_surface_risk` (`low`/`medium`/`high` from `active_branch_count` + `recent_commit_diff_lines`) to `FragilityAssessment`; add `branch_only` as the recommended action when `shared_surface_risk == "high"`.
- `qor/skills/sdlc/qor-plan/SKILL.md` - add a stabilization-capacity checkpoint step invoking `qor-logic scripts workspace_fragility_check --repo-root . || true` (WARN-only) in the planning flow.
- `qor/skills/sdlc/qor-implement/SKILL.md` - add an impl-phase scope-boundary warning invoking the same check (WARN-only).
- `qor/dist/variants/**` - regenerated.

### Changes

```python
_SHARED_SURFACE = {"low": ..., "medium": ..., "high": ...}  # thresholded on branches+diff
_CAPACITY = {"low": "healthy", "medium": "strained", "high": "exceeded"}

@dataclass(frozen=True)
class FragilityAssessment:
    ... existing fields ...
    workspace_fragility: str
    stabilization_capacity: str   # NEW: merge_velocity vocab mirror
    shared_surface_risk: str      # NEW: low|medium|high
    recommended_action: str       # now may be 'branch_only'
    evidence: tuple[str, ...]
```

`recommended_action`: `branch_only` when `shared_surface_risk == "high"`, else the existing grade-based map (`merge_ok`/`narrow_scope`/`hardening_only`). The two new fields restore #90's dropped contract; the plan/implement wiring is WARN-only (only the substantiate merge-velocity gate enforces).

### Unit Tests

- `::test_fragility_has_capacity_and_shared_surface_fields` - `assess(...)` (or a constructed assessment over a tmp repo) exposes `stabilization_capacity` and `shared_surface_risk`.
- `::test_branch_only_when_shared_surface_high` - inputs that drive `shared_surface_risk == "high"` yield `recommended_action == "branch_only"`.
- `::test_capacity_mirrors_grade` - `workspace_fragility == "high"` -> `stabilization_capacity == "exceeded"`.
- `::test_qor_plan_wires_fragility_check` - read `qor-plan/SKILL.md`; assert it names `workspace_fragility_check`.
- `::test_qor_implement_wires_fragility_check` - read `qor-implement/SKILL.md`; assert it names `workspace_fragility_check`.

## Phase 3: Doctrine

### Affected Files

- `qor/references/doctrine-shadow-genome-countermeasures.md` - SG-MergePaceThrottle-A: mark the enforcer shipped — substantiate Step 4.6.8 is fail-closed on `exceeded` (logged `--override`); `workspace_fragility_check` wired into `/qor-plan` + `/qor-implement` with the restored `stabilization_capacity` / `shared_surface_risk` / `branch_only` contract.

## Definition of Done

### Deliverable: merge-throttle enforcement + full wiring

- **D1**: an `exceeded` merge-velocity grade holds the `/qor-substantiate` seal unless overridden (logged); the fragility checkpoint runs in plan + implement; the dropped fields/action are restored.
- **D2**: `--override` + logged emission in `merge_velocity_check.py`; `stabilization_capacity` / `shared_surface_risk` / `branch_only` in `workspace_fragility_check.py`; Step 4.6.8 `|| ABORT`; plan + implement wiring.
- **D3**: doctrine SG-MergePaceThrottle-A marked enforced; META_LEDGER seal entry; version bump; variants recompiled.
- **D4**: `tests/test_merge_throttle_enforcement.py::test_main_aborts_on_exceeded` + `::test_main_override_exits_0_and_logs_event` + `::test_branch_only_when_shared_surface_high` + `::test_qor_plan_wires_fragility_check`.

## CI Commands

- `python -m pytest tests/test_merge_throttle_enforcement.py tests/test_merge_velocity_check.py tests/test_workspace_fragility_check.py -q` — new enforcement/contract + existing detector tests.
- `python -m pytest -q` — full suite green before substantiate.
