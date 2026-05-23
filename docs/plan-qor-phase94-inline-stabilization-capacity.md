# Plan: Phase 94 — Inline workspace-fragility / stabilization-capacity check V1 (GH #90)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #90

**boundaries**:
- limitations: V1 ships only the **inline detector** — a new
  `qor.scripts.workspace_fragility_check` module that inspects local
  workspace signals (untracked file count, staged-but-unsealed gate
  artifacts, ledger entries with chain-math failures, branch-count
  pressure) and emits a `FragilityAssessment` with three grades
  (`low` / `medium` / `high`). Wired at `/qor-audit` Step 0.6 alongside
  the existing pre-audit lints; WARN-only. V1 reuses Phase 93's
  shared-core / merge-velocity signals by reference rather than
  re-implementing — the inline check focuses on signals Phase 93's
  detector cannot see (local workspace state pre-merge).
- non_goals: enforcement clauses from GH #90's "Inline Enforcement
  Points" section (warn on scope expansion during implementation;
  require narrow first slice when planned change touches multiple
  shared surfaces; treat workspace fragility as audit evidence not
  background noise — all deferred to V2); GitHub-API integration
  (open PR count; failing check enumeration); test-matrix growth
  detection (V2 — requires per-PR diff analysis); concurrent branch
  pressure beyond simple count; per-deliverable scope-expansion
  surface that Phase 92 D4 tier would naturally extend.
- exclusions: no changes to `/qor-plan` (V1 wires only at audit Step
  0.6); no changes to `/qor-implement`; no new CI workflow; existing
  pre-audit lints (`plan_test_lint`, `plan_grep_lint`,
  `plan_text_consistency_lint`, `delivery_branch_lint`,
  `ci_coverage_lint`) untouched in order. The new lint joins the Step
  0.6 ladder as the SIXTH pre-audit check.

## Open Questions

None.

## Feature Inventory Touches

Empty. New script + skill prose + new test file + doctrine extension;
no `src/` user-facing feature. `feature_inventory_touches`: `[]`.

## Design notes

GH #90 is a follow-up to GH #89 (closed by Phase 93). Where Phase 93
detects MACRO merge-pace at substantiate time (looking backward at
`origin/main`'s recent merge history), Phase 94 detects MICRO
workspace fragility at AUDIT time (looking at the CURRENT working tree
before any merge). The two halves are complementary signals into the
same governance surface: stabilization capacity should be a pacing
constraint, surfaced as early as possible in the cycle.

Per `[[feedback-progressive-disclosure]]`, V1 is kept lean: one new
script, one new pre-audit lint in the existing Step 0.6 ladder, one
SG entry extension. No new doctrine file (the parent surface is
`SG-MergePaceThrottle-A` from Phase 93; Phase 94 extends it).

**V1 signals** (operatively testable, locally measurable, no network):

- `untracked_count` — `git status --short` lines whose path is not
  tracked. High untracked count signals workspace-state drift.
- `dirty_gate_artifact_count` — count of `.qor/gates/<sid>/` artifacts
  whose containing session has no SESSION SEAL entry in META_LEDGER
  yet. High count signals stalled mid-cycle work.
- `ledger_chain_failure_count` — count of META_LEDGER entries that
  fail `verify-ledger` chain math (excluding grandfathered residuals
  per Phase 91). Non-zero is a serious workspace integrity signal.
- `active_branch_count` — count of local branches (`git branch | wc -l`).
  Many concurrent branches signal scope-spread.
- `recent_commit_diff_lines` — sum of added/removed lines across
  commits on the current branch since branching off `main`. Very
  large diffs on a single branch signal scope-creep risk.

**V1 grade thresholds** (tunable constants):

- `high`: `ledger_chain_failure_count > 0` (any integrity failure)
  OR `untracked_count >= 50` OR `recent_commit_diff_lines >= 5000`.
- `medium`: `untracked_count >= 15` OR `dirty_gate_artifact_count >= 3`
  OR `active_branch_count >= 10` OR `recent_commit_diff_lines >= 1500`.
- `low`: otherwise.

`recommended_action` mapping V1:
- `low` -> `merge_ok`
- `medium` -> `narrow_scope`
- `high` -> `hardening_only`

(The `branch_only` action from Phase 93 is reserved for the merge-pace
detector; Phase 94's high-fragility recommends pausing forward work in
favor of hardening the workspace.)

**Evidence list**: each fired signal contributes a string naming the
metric value and the threshold that fired, mirroring Phase 93's
`evidence` shape so operators see consistent output across both
detectors.

`/qor-audit` Step 0.6 invocation (added as the SIXTH lint after the
five existing):

```bash
python -m qor.scripts.workspace_fragility_check --repo-root . || true
```

WARN-only V1. CLI exits 0 on `low`/`medium`, exits 1 on `high` so V2
can remove the `|| true` to convert `high` into a hard ABORT.

**Doctrine**: extend the existing `SG-MergePaceThrottle-A`
countermeasure (Phase 93) with a new sub-paragraph titled "Inline
companion (Phase 94 wiring; GH #90)" rather than creating a separate
SG entry — Phase 90 = inline mechanism = same root surface as Phase
89's macro throttle. This honors the issue's own framing ("#89 covers
the macro throttle ... this issue covers the inline mechanism").

## Phase 1: workspace_fragility_check + Step 0.6 wiring + tests

### Affected Files

- `qor/scripts/workspace_fragility_check.py` — NEW. Detector module.
- `qor/skills/governance/qor-audit/SKILL.md` — add the sixth lint line
  to Step 0.6 + Phase 94 wiring paragraph.
- `qor/references/doctrine-shadow-genome-countermeasures.md` — extend
  `SG-MergePaceThrottle-A` with an "Inline companion (Phase 94)"
  sub-paragraph.
- `tests/test_workspace_fragility_check.py` — NEW. Behavior tests
  using scratch-repo fixtures + canonical-repo forward-only guard.
- `tests/test_workspace_fragility_audit_wiring.py` — NEW. Anchored +
  strip-and-fail Step 0.6 wiring tests.
- `docs/plan-qor-phase94-inline-stabilization-capacity.md` — NEW.
  This plan.

### Unit Tests

- `tests/test_workspace_fragility_check.py`
  - `test_assess_low_grade_for_clean_workspace` — scratch repo with
    no untracked, no extra branches, one ledger entry; assert grade
    `low`.
  - `test_assess_medium_grade_when_untracked_count_at_threshold` —
    scratch repo with 15+ untracked files; assert grade `medium`.
  - `test_assess_high_grade_for_ledger_chain_failure` — scratch repo
    with a deliberately corrupted META_LEDGER entry; assert grade
    `high`.
  - `test_active_branch_count_counts_local_branches` — scratch repo
    with 5 created branches; assert returned count matches.
  - `test_dirty_gate_artifact_count_finds_unsealed_sessions` —
    scratch repo with `.qor/gates/test-session/plan.json` but no
    matching SESSION SEAL entry in META_LEDGER; assert count is 1.
  - `test_recommended_action_maps_from_grade` — three sub-cases
    (`low -> merge_ok`, `medium -> narrow_scope`, `high -> hardening_only`).
  - `test_evidence_list_names_threshold_for_each_fired_signal` —
    fixture with multiple signals firing; assert each appears in
    the evidence list with its threshold value.
  - `test_main_cli_exits_zero_on_low_or_medium` — subprocess CLI
    invocation; assert exit 0.
  - `test_main_cli_exits_one_on_high` — subprocess on a high-grade
    fixture; assert exit 1.
  - `test_assess_fragility_on_qor_logic_main` — canonical-repo
    forward-only guard. Runs the assessment on Qor-logic's own
    repo; asserts the returned grade is in the closed set and the
    function does not raise. Does NOT assert a specific grade
    (data-driven; this session's burst of phases means current
    workspace state varies).

- `tests/test_workspace_fragility_audit_wiring.py`
  - `test_step_0_6_invokes_workspace_fragility_check` — isolate
    `### Step 0.6` in qor-audit SKILL.md; assert it cites
    `qor.scripts.workspace_fragility_check` and `|| true`.
  - `test_step_0_6_section_removed_breaks_assertion` — strip-and-
    fail negative.
  - `test_step_0_6_fragility_check_appears_after_ci_coverage_lint`
    — positional guard: the new line must appear AFTER the
    existing `ci_coverage_lint` line (Phase 89 wiring) to preserve
    the sixth-in-order placement.

### Changes

`qor/scripts/workspace_fragility_check.py` — module structured like
Phase 93's `merge_velocity_check`:

```python
@dataclass(frozen=True)
class FragilityAssessment:
    untracked_count: int
    dirty_gate_artifact_count: int
    ledger_chain_failure_count: int
    active_branch_count: int
    recent_commit_diff_lines: int
    workspace_fragility: str  # 'low' | 'medium' | 'high'
    recommended_action: str   # 'merge_ok' | 'narrow_scope' | 'hardening_only'
    evidence: tuple[str, ...]


def assess_workspace_fragility(repo_root: Path) -> FragilityAssessment: ...

def main(argv: list[str] | None = None) -> int:
    """CLI: exit 0 on low/medium, exit 1 on high so V2 can convert
    to a hard ABORT by removing the `|| true` wrap at the audit site."""
```

Helpers:

- `_git_status_untracked(repo_root) -> int` — count of `??` lines from
  `git status --short`.
- `_dirty_gate_artifacts(repo_root) -> int` — walk `.qor/gates/`,
  cross-reference each session_id against META_LEDGER SESSION SEAL
  entries.
- `_ledger_chain_failures(repo_root) -> int` — invoke
  `ledger_hash.verify` in tolerate-grandfathered mode (Phase 91);
  count `FAIL` lines.
- `_active_branch_count(repo_root) -> int` — `git branch | wc -l`
  equivalent.
- `_recent_commit_diff_lines(repo_root) -> int` — `git diff
  --shortstat origin/main..HEAD` parsed; returns added + deleted.

`/qor-audit` Step 0.6 prose update:

```bash
python -m qor.scripts.workspace_fragility_check --repo-root . || true
```

Added as the sixth line in the Step 0.6 bash block, after the existing
`ci_coverage_lint` line.

`qor/references/doctrine-shadow-genome-countermeasures.md`
`SG-MergePaceThrottle-A` extension: a new sub-paragraph titled
"**Inline companion** (Phase 94 wiring; GH #90)" naming the
`workspace_fragility_check` detector, the five V1 signals, the three-
grade output, and the explicit deferral of enforcement clauses to V2.

## Definition of Done

### Deliverable: workspace_fragility_check module

- **D1**: A pure-Python detector exists that inspects local workspace
  signals (untracked count, dirty gate artifacts, ledger integrity,
  branch count, branch-diff size) and returns a `FragilityAssessment`
  with three grades plus an evidence list.
- **D2**: `qor/scripts/workspace_fragility_check.py:assess_workspace_fragility(repo_root) -> FragilityAssessment`
  with a frozen dataclass carrying `untracked_count`,
  `dirty_gate_artifact_count`, `ledger_chain_failure_count`,
  `active_branch_count`, `recent_commit_diff_lines`,
  `workspace_fragility`, `recommended_action`, `evidence` fields.
  `main()` CLI with `--repo-root` arg.
- **D3**: Plan + ledger + SYSTEM_STATE Phase 94 entry seal the module;
  `SG-MergePaceThrottle-A` extension catalogs the inline companion.
- **D4**: `tests/test_workspace_fragility_check.py` carries 10
  assertions covering each grade transition, each signal helper, the
  recommended-action mapping, the evidence-list shape, the CLI exit
  codes, and the canonical-repo forward-only guard.

### Deliverable: qor-audit Step 0.6 wiring

- **D1**: `/qor-audit` Step 0.6 invokes the fragility check alongside
  the existing five pre-audit lints. WARN-only.
- **D2**: `qor/skills/governance/qor-audit/SKILL.md` Step 0.6 bash
  block gains the `python -m qor.scripts.workspace_fragility_check
  --repo-root . || true` invocation after `ci_coverage_lint` and a
  Phase 94 wiring paragraph.
- **D3**: Plan + ledger entries cover the SKILL.md change.
- **D4**: `tests/test_workspace_fragility_audit_wiring.py` carries
  three assertions: anchored positive (invocation + `|| true`); strip-
  and-fail negative; positional guard (new line appears AFTER
  `ci_coverage_lint`).

### Deliverable: SG-MergePaceThrottle-A inline-companion extension

- **D1**: The countermeasures doctrine gains an "Inline companion"
  sub-paragraph under the existing `SG-MergePaceThrottle-A` entry
  naming the Phase 94 detector and its V1 signals.
- **D2**: `qor/references/doctrine-shadow-genome-countermeasures.md`
  `SG-MergePaceThrottle-A` section gains the sub-paragraph between
  the existing **Countermeasure** and **V2 reserved** paragraphs.
- **D3**: Plan + ledger seal the doctrine extension.
- **D4.d**: Waiver. Doctrine sub-paragraphs are operator-readable prose; their behavior is the discipline they describe, which is exercised by the `workspace_fragility_check` tests above. **Follow-up phase**: reserved for a future doctrine-integrity sweep.

## CI Coverage Exemptions

None. Phase 94's `## CI Commands` covers the full Qor-logic CI surface.

## CI Commands

- `python -m pytest tests/test_workspace_fragility_check.py -q` — behavior tests for the detector module.
- `python -m pytest tests/test_workspace_fragility_audit_wiring.py -q` — Step 0.6 wiring tests.
- `python -m pytest tests/ -v` — full regression suite.
- `python qor/scripts/check_variant_drift.py` — ci.yml `test` job step.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` — ci.yml `test` job step.
- `python -m pytest tests/test_packaging_install.py -v -m integration` — ci.yml `install-smoke` job step.
- `python -m qor.reliability.gate_chain_completeness --phase-min 52` — ci.yml `gate-chain-completeness` job step.
- `python qor/scripts/pr_citation_lint.py` — pr-lint.yml `lint` job step.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase94-inline-stabilization-capacity.md` — plan-internal text-consistency.
- `python -m qor.scripts.ci_coverage_lint --plan docs/plan-qor-phase94-inline-stabilization-capacity.md --workflows-dir .github/workflows` — Phase 89 ci-coverage lint.
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase94-inline-stabilization-capacity.md` — Phase 92 DoD check.
