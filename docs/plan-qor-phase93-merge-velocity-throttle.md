# Plan: Phase 93 — Merge-velocity throttle V1 (GH #89)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #89

**boundaries**:
- limitations: V1 ships only the **detector** layer — a new
  `qor.scripts.merge_velocity_check` module + `/qor-substantiate`
  Step 4.6.8 invocation. The check inspects `origin/main`'s recent
  merge history via `git log` (no GitHub API dependency) and computes
  a `VelocityAssessment` with three stabilization-capacity grades
  (`healthy` / `strained` / `exceeded`). V1 is WARN-only at
  substantiate — the assessment is surfaced in the seal report's
  `## Merge Velocity` block but does NOT abort the seal. Shared-core
  path patterns are operator-declarable via repeat `--shared-core-path`
  flag; V1 ships no built-in patterns (consumer-workspace-specific).
- non_goals: enforcement (the V1 detector does not hold new feature
  merges, isolate features as unmerged branches, or require a
  stabilization plan — the issue's enforcement clauses are V2);
  GitHub-API integration (V1 is `git log`-only so it works in any
  cloned repo without network or auth); test-matrix expansion
  detection (V2 — requires per-PR diff analysis); failing-e2e tail-
  check signal (V2 — requires gh API); cross-PR repair-density
  clustering (V1 uses keyword-only repair classification; V2 may
  cluster by subsystem).
- exclusions: no changes to `/qor-plan` (V1 wires only at substantiate
  Step 4.6.8); no new CI workflow; existing Step 4.6.5 / 4.6.6 / 4.6.7
  pre-doc-integrity gates remain unchanged in order; no GitHub-API
  shell calls (the V1 detector is offline-safe by construction).

## Open Questions

None.

## Feature Inventory Touches

Empty. This plan touches a new pre-substantiate detector script under
`qor/scripts/`, one governance skill body, and one new test file; it
introduces no `src/` user-facing feature.
`feature_inventory_touches`: `[]`.

## Design notes

GH #89 documents a process-control failure observed in a sibling
consumer workspace: 27 PRs merged in a single window, 14,758 additions,
a repair cluster across #346-#353 addressing stale authoritative SHA
binding / status lifecycle / preflight noise / schema CI, plus a tail
PR #354 with failing e2e checks. The governance system had no explicit
throttle when high merge throughput, broad shared-surface expansion,
and repair-tail density together signaled that stabilization capacity
was being exceeded. The corrective principle is that **stabilization
capacity should become a pacing constraint, not an after-the-fact
repair loop**.

V1 ships the **detector**, not the enforcer. Per the cluster's
established V1/V2 split pattern (Phase 89/90/91/92 all used this
shape), V1 lands the infrastructure first so operators see the signal;
V2 layers enforcement (block-feature-merges, require stabilization-
plan) on top once operator evidence accumulates on detector accuracy.

WARN-only V1 contract mirrors `delivery_branch_lint`,
`ci_coverage_lint`, `dod_check` — the detector surfaces an assessment
in the seal report but does NOT abort the seal. Operators read the
assessment, decide whether to pause or continue. V2 may tighten
specific grades (`exceeded`) to fail-closed once the detector's false-
positive rate is characterized.

**V1 signals** (operatively testable):

- `prs_merged_in_window` — count of merge commits on `origin/main` in
  the configured window (default 7 days). Measured via
  `git log origin/main --merges --since=<window>`.
- `additions_total` — sum of line-additions across the window's
  merge commits. Measured via `git log --shortstat`.
- `repair_density` — fraction of the window's merge commits whose
  commit message subject contains repair keywords (`fix`, `hotfix`,
  `repair`, `regression`, `rollback`, `revert`). Range `[0.0, 1.0]`.
- `shared_core_touch_count` — count of the window's merges whose
  changed files match any operator-declared `--shared-core-path`
  pattern. Defaults to 0 when no pattern is declared.

**V1 grade thresholds** (tunable; declared as constants in the module
for V1 transparency):

- `exceeded`: `prs_merged_in_window >= 20` AND
  (`repair_density >= 0.30` OR `shared_core_touch_count >= 10`).
- `strained`: `prs_merged_in_window >= 10` OR `repair_density >= 0.20`.
- `healthy`: otherwise.

A second derivation, `recommended_action`, maps the grade to one of
the four operator-actionable strings: `merge_ok | narrow_scope |
branch_only | hardening_only`. V1 mapping is deterministic from grade
alone (no per-signal weighting); V2 may refine.

**Evidence list**: the assessment carries a `list[str]` of concrete
signal-line strings (e.g.,
`"23 PRs merged in 7d (>= strained threshold 10)"`,
`"repair_density=0.35 (>= exceeded threshold 0.30)"`) so the seal
report's `## Merge Velocity` block can render an operator-readable
explanation of why a grade fired.

`/qor-substantiate` Step 4.6.8 invocation:

```bash
PLAN_PATH=$(python -c "from qor.scripts.governance_helpers import current_phase_plan_path; print(current_phase_plan_path())")
python -m qor.scripts.merge_velocity_check --repo-root . --window-days 7 || true
```

WARN-only by `|| true`; the CLI exits 0 on `healthy`/`strained` and
exits 1 on `exceeded` (the latter for operators who pipe the output
into stricter wrappers; the `|| true` swallows the non-zero so
substantiate continues). V2 may remove the `|| true` to convert
`exceeded` into a hard ABORT.

New `SG-MergePaceThrottle-A` doctrine entry in
`qor/references/doctrine-shadow-genome-countermeasures.md` catalogs
the sibling-workspace originating recurrence, the V1 detector, and the
explicit deferral of enforcement to V2.

**Dogfooding**: this plan's `## CI Commands` covers Qor-logic's full
CI surface so Phase 89's `ci_coverage_lint` reports zero WARNs on the
plan (fourth cross-phase application). This plan also carries a
`## Definition of Done` block declaring D1-D4 per deliverable per
Phase 92's new contract — Phase 93 is the first phase to follow the
DoD discipline at plan-authoring time without it being introduced
as a new pattern.

**Self-application caveat**: the new check, when invoked on
Qor-logic's own `origin/main`, will return `strained` if this
session's recent burst of 5 phases (88 → 92) is inside the 7-day
window — which it is. That's the **correct** signal: the cluster
itself just ran 5 phases in 24 hours; the detector should flag it.
Phase 93's own substantiate run will be the first concrete operator-
visible exercise. The test `test_assess_velocity_on_qor_logic_main`
asserts the assessment runs without error and produces a valid grade
on the canonical repo; it does NOT assert a specific grade because
the grade is data-driven and will shift over time.

## Phase 1: merge_velocity_check + Step 4.6.8 wiring + tests

### Affected Files

- `qor/scripts/merge_velocity_check.py` — NEW. `assess_merge_velocity(repo_root, window_days, shared_core_paths) -> VelocityAssessment`; CLI `main()`.
- `qor/skills/governance/qor-substantiate/SKILL.md` — add
  `### Step 4.6.8: Merge-velocity throttle check (Phase 93 wiring; GH #89)` between Step 4.6.7 (DoD check) and Step 4.7 (doc-integrity).
- `qor/references/doctrine-shadow-genome-countermeasures.md` —
  `SG-MergePaceThrottle-A` entry.
- `tests/test_merge_velocity_check.py` — NEW. Behavior tests using a
  scratch repo fixture + canonical-repo forward-only guard.
- `tests/test_merge_velocity_substantiate_wiring.py` — NEW. Anchored
  + strip-and-fail + positional wiring tests for Step 4.6.8.
- `docs/plan-qor-phase93-merge-velocity-throttle.md` — NEW. This plan.

### Unit Tests

- `tests/test_merge_velocity_check.py`
  - `test_assess_healthy_grade_for_low_pr_count` — scratch repo with
    3 merge commits in the window; assert grade is `healthy`.
  - `test_assess_strained_grade_for_moderate_pr_count` — scratch repo
    with 12 merge commits; assert grade is `strained`.
  - `test_assess_exceeded_grade_for_high_pr_count_and_repair_density`
    — scratch repo with 25 merges, 9 of them carrying repair keywords;
    assert grade is `exceeded`.
  - `test_repair_density_classification_matches_keywords` — scratch
    repo with merges named `fix:`, `hotfix:`, `repair:`, `regression:`,
    `rollback:`, `revert:`, plus three `seal:` merges; assert
    `repair_density == 6/9` rounded to 2 places.
  - `test_shared_core_touch_counted_for_declared_paths` — scratch
    repo with 5 merges, 3 touching `core/ledger/`; assert
    `shared_core_touch_count == 3` when `shared_core_paths=("core/ledger/",)`.
  - `test_shared_core_touch_zero_when_no_patterns_declared` — assert
    the field is 0 when no patterns are passed.
  - `test_recommended_action_maps_from_grade` — three sub-cases:
    `healthy -> "merge_ok"`, `strained -> "narrow_scope"`,
    `exceeded -> "branch_only"`. Deterministic V1 mapping.
  - `test_evidence_list_names_threshold_in_each_fired_signal` — when a
    signal fires, the evidence-list string contains the threshold
    value the comparison crossed (e.g., `"23 >= 10"`); when no signal
    fires, evidence is empty.
  - `test_window_days_arg_filters_merges` — scratch repo with merges
    spread over 30 days; assert `window_days=7` counts only the most
    recent 7-day subset.
  - `test_main_cli_exits_zero_on_healthy` — subprocess-invoke
    `python -m qor.scripts.merge_velocity_check --repo-root <healthy-fixture>`;
    assert exit code 0.
  - `test_main_cli_exits_one_on_exceeded` — subprocess-invoke on an
    `exceeded`-fixture; assert exit code 1. The CLI's exit-1 path is
    what V2 will use to convert WARN to BLOCK; V1 wraps in `|| true`
    at the substantiate site.
  - `test_assess_velocity_on_qor_logic_main` — invoke
    `assess_merge_velocity(REPO_ROOT, window_days=30)` on the canonical
    repo; assert the returned assessment has a valid grade in the
    closed set `{"healthy", "strained", "exceeded"}` and that
    `prs_merged_in_window > 0`. This is the canonical-repo forward-
    only guard (Phase 91 / Phase 92 pattern) — the function must run
    against the real ledger without error.

- `tests/test_merge_velocity_substantiate_wiring.py`
  - `test_step_4_6_8_invokes_merge_velocity_check` — read
    `qor/skills/governance/qor-substantiate/SKILL.md`; isolate
    `### Step 4.6.8`; assert it cites `qor.scripts.merge_velocity_check`
    and `|| true` (V1 WARN-only contract).
  - `test_step_4_6_8_section_removed_breaks_assertion` — strip-and-
    fail negative.
  - `test_step_4_6_8_positioned_between_4_6_7_and_4_7` — assert Step
    4.6.8 heading appears AFTER `### Step 4.6.7` and BEFORE
    `### Step 4.7` in document order (the substantiate-sequence
    positional guard from Phase 92).

### Changes

`qor/scripts/merge_velocity_check.py` — new module:

```python
@dataclass(frozen=True)
class VelocityAssessment:
    prs_merged_in_window: int
    additions_total: int
    repair_density: float
    shared_core_touch_count: int
    stabilization_capacity: str  # 'healthy' | 'strained' | 'exceeded'
    recommended_action: str      # 'merge_ok' | 'narrow_scope' | 'branch_only' | 'hardening_only'
    evidence: tuple[str, ...]
    window_days: int


def assess_merge_velocity(
    repo_root: Path,
    *,
    window_days: int = 7,
    shared_core_paths: tuple[str, ...] = (),
) -> VelocityAssessment: ...


def main(argv: list[str] | None = None) -> int:
    """CLI: exit 0 on healthy/strained; exit 1 on exceeded.
    The substantiate Step 4.6.8 wrap uses `|| true` so exit 1 does not
    abort the seal in V1 -- it is informational. V2 may remove the
    `|| true` to convert exceeded into a hard ABORT.
    """
```

`/qor-substantiate` Step 4.6.8 inserted between Step 4.6.7 (DoD
check) and Step 4.7 (doc-integrity). Step body:

```bash
PLAN_PATH=$(python -c "from qor.scripts.governance_helpers import current_phase_plan_path; print(current_phase_plan_path())")
python -m qor.scripts.merge_velocity_check --repo-root . --window-days 7 || true
```

`SG-MergePaceThrottle-A` doctrine entry catalogs the sibling-workspace
originating recurrence (27 PRs / 14,758 additions / repair cluster
#346-#353 / failing e2e on #354), the V1 detector, and the explicit
deferral of enforcement (hold-feature-merges; require-stabilization-
plan; etc.) to V2.

## Definition of Done

Per-deliverable acceptance per `qor/references/doctrine-definition-of-done.md`.

### Deliverable: merge_velocity_check module

- **D1**: A pure-Python detector exists that walks `origin/main`'s
  merge history (via `git log`) and computes a `VelocityAssessment`
  with three stabilization-capacity grades plus an evidence list.
- **D2**: `qor/scripts/merge_velocity_check.py:assess_merge_velocity(...) -> VelocityAssessment`
  with a frozen dataclass carrying `prs_merged_in_window`,
  `additions_total`, `repair_density`, `shared_core_touch_count`,
  `stabilization_capacity`, `recommended_action`, `evidence`,
  `window_days` fields. `main()` CLI with `--repo-root`,
  `--window-days`, `--shared-core-path` (repeatable) args.
- **D3**: Plan + ledger + SYSTEM_STATE Phase 93 entry seal the module;
  new `SG-MergePaceThrottle-A` doctrine entry catalogs the pattern.
- **D4**: `tests/test_merge_velocity_check.py` carries 12 assertions
  covering each branch (healthy / strained / exceeded grades; repair-
  density keyword set; shared-core touch counting; recommended-action
  mapping; evidence-list threshold naming; window-days filtering; CLI
  exit codes; canonical-repo forward-only guard).

### Deliverable: qor-substantiate Step 4.6.8 wiring

- **D1**: `/qor-substantiate` invokes `merge_velocity_check` between
  the DoD check (Step 4.6.7) and the doc-integrity check (Step 4.7),
  surfacing the assessment in the seal report. WARN-only in V1.
- **D2**: `qor/skills/governance/qor-substantiate/SKILL.md` gains
  `### Step 4.6.8: Merge-velocity throttle check (Phase 93 wiring; GH #89)`
  with the `|| true`-wrapped invocation and a wiring paragraph.
- **D3**: Plan + ledger entries cover the SKILL.md change; doctrine
  cross-references `SG-MergePaceThrottle-A`.
- **D4**: `tests/test_merge_velocity_substantiate_wiring.py` carries
  three assertions: anchored positive (Step 4.6.8 cites
  `merge_velocity_check` + `|| true`); strip-and-fail negative;
  positional guard (Step 4.6.8 between 4.6.7 and 4.7).

### Deliverable: SG-MergePaceThrottle-A doctrine entry

- **D1**: The countermeasures doctrine gains an entry naming the
  sibling-workspace originating pattern, the V1 detector, and the V2
  deferral.
- **D2**: `qor/references/doctrine-shadow-genome-countermeasures.md`
  gains a `## SG-MergePaceThrottle-A` section with Pattern /
  Originating recurrence / Countermeasure / V2 reserved /
  Cross-reference sub-sections.
- **D3**: Plan + ledger seal the doctrine extension; SYSTEM_STATE
  Phase 93 entry references it.
- **D4.d**: Waiver. Doctrine entries are operator-readable prose; their behavior is the discipline they describe, which is exercised by the `merge_velocity_check` tests above. A direct behavior test asserting the doctrine entry's structure is over-engineered for V1 (would test markdown shape, not doctrine substance). **Follow-up phase**: reserved for a future doctrine-integrity sweep phase if drift surfaces.

## CI Coverage Exemptions

None. Phase 93's `## CI Commands` covers the full Qor-logic CI surface.

## CI Commands

- `python -m pytest tests/test_merge_velocity_check.py -q` — behavior tests for the detector module.
- `python -m pytest tests/test_merge_velocity_substantiate_wiring.py -q` — Step 4.6.8 wiring tests.
- `python -m pytest tests/ -v` — full regression suite.
- `python qor/scripts/check_variant_drift.py` — ci.yml `test` job step.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` — ci.yml `test` job step.
- `python -m pytest tests/test_packaging_install.py -v -m integration` — ci.yml `install-smoke` job step.
- `python -m qor.reliability.gate_chain_completeness --phase-min 52` — ci.yml `gate-chain-completeness` job step.
- `python qor/scripts/pr_citation_lint.py` — pr-lint.yml `lint` job step.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase93-merge-velocity-throttle.md` — plan-internal text-consistency.
- `python -m qor.scripts.ci_coverage_lint --plan docs/plan-qor-phase93-merge-velocity-throttle.md --workflows-dir .github/workflows` — Phase 89 ci-coverage lint (fourth cross-phase application).
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase93-merge-velocity-throttle.md` — Phase 92 DoD check (first cross-phase application from substantiate Step 4.6.7).
