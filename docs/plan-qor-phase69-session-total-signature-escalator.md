# Plan: Phase 69 - cycle_count_escalator session-total signature mode

**change_class**: hotfix

**doc_tier**: standard

**originating_remediation**: GH #43 (Cycle-count escalator: track session-level signature count across artifacts, not just per-artifact).

**terms_introduced**: none. Builds on existing `cycle_count_escalator` and `stall_walk` machinery from Phase 37.

**boundaries**:
- limitations:
  - V1 counts non-consecutive same-signature VETOs within a single session. Cross-session aggregation (which would require iterating session directories) is out of scope.
  - The session-total mode runs alongside the existing consecutive-streak mode; a non-consecutive triple-VETO triggers the new mode, while consecutive triple-VETO still triggers the original mode.
- non_goals:
  - Changing the consecutive-streak semantics or threshold (still K=3).
  - Per-target / per-artifact aggregation (the issue explicitly asks for non-per-artifact tracking).
- exclusions:
  - No changes to `audit_history` schema or storage.
  - No changes to `findings_signature.compute_record` algorithm.

## Open Questions

None. Issue #43 specifies the desired aggregation (session-level total) and threshold (same K=3 as consecutive).

## Phase 1: Session-total signature counter helper

### Affected Files

- `tests/test_session_total_signature_count.py` - NEW. 6 tests covering: count zero on empty session; count one per single VETO; non-consecutive triple-VETO with PASS interleaved; consecutive triple-VETO; LEGACY-sentinel exclusion; multi-signature isolation (counts are per-signature).
- `qor/scripts/stall_walk.py` - add `count_session_signature_totals(session_id) -> dict[str, int]` returning `{signature: count}` across the entire session audit history. Reads via `audit_history.read`; aggregates non-consecutively; ignores PASS and LEGACY records.
- `qor/scripts/cycle_count_escalator.py` - add `check_session_total(session_id) -> EscalationRecommendation | None` that surfaces escalation when any session-total signature count reaches K=3.

### Changes

`count_session_signature_totals` walks every audit record in `audit_history.jsonl`, computes `findings_signature.compute_record` on each, and accumulates per-signature counts. PASS audits don't contribute; LEGACY sentinels are excluded. The returned dict is the raw distribution; callers decide the threshold.

`check_session_total` calls the new counter, filters to signatures meeting the `ESCALATION_THRESHOLD` (K=3, reused from the existing `cycle_count_escalator` module), respects the same `_suppression_active` marker as the consecutive-mode check, and returns an `EscalationRecommendation` with `escalation_reason="session-total"` (vs the existing `"cycle-count"`).

### Unit Tests

- `tests/test_session_total_signature_count.py::test_empty_session_returns_no_signatures` - invokes `count_session_signature_totals` on a session with no audit history; asserts returns `{}`.
- `tests/test_session_total_signature_count.py::test_single_veto_returns_count_one` - one audit VETO; asserts `{<sig>: 1}`.
- `tests/test_session_total_signature_count.py::test_non_consecutive_triple_veto_with_pass_interleaved` - 3 VETOs same signature interleaved with PASS records; asserts session-total reaches 3 even though consecutive-streak would reset.
- `tests/test_session_total_signature_count.py::test_consecutive_triple_veto_same_signature` - 3 consecutive same-signature VETOs; asserts both consecutive (`stall_walk.run` returns 3) AND session-total (`count_session_signature_totals` returns 3) modes agree.
- `tests/test_session_total_signature_count.py::test_legacy_sentinel_excluded` - audit record without `findings_categories`; asserts LEGACY records do not contribute to any signature count.
- `tests/test_session_total_signature_count.py::test_multi_signature_isolation` - 2 audits with sig A and 1 with sig B; asserts `{A: 2, B: 1}` (per-signature isolation, not pooled).
- `tests/test_session_total_signature_count.py::test_check_session_total_returns_recommendation_at_threshold` - 3 non-consecutive same-signature VETOs; asserts `cycle_count_escalator.check_session_total` returns an `EscalationRecommendation` with `escalation_reason="session-total"`.
- `tests/test_session_total_signature_count.py::test_check_session_total_returns_none_below_threshold` - 2 same-signature VETOs; asserts `check_session_total` returns `None`.

## Phase 2: Skill prose wiring + doctrine update

### Affected Files

- `tests/test_session_total_escalator_skill_wiring.py` - NEW. 3 tests covering qor-plan Step 2c and qor-audit Step 0.5 invoking `check_session_total` alongside the existing `check`.
- `qor/skills/sdlc/qor-plan/SKILL.md` - Step 2c cycle-count escalation check gains a parallel call to `check_session_total` and surfaces both recommendations if both fire.
- `qor/skills/governance/qor-audit/SKILL.md` - Step 0.5 cycle-count escalation check gains the same parallel call.
- `qor/references/doctrine-governance-enforcement.md` - §10.4 cycle-count escalation gains a sub-section documenting session-total mode alongside the existing consecutive-streak mode.

### Changes

Skill prose changes are surgical: one extra Python call to `check_session_total` after the existing `check`, and a print statement when the new mode fires. Doctrine clarification explains the two-mode contract: consecutive-streak catches local recurrence; session-total catches recurrence-across-artifacts within one session.

### Unit Tests

- `tests/test_session_total_escalator_skill_wiring.py::test_qor_plan_step_2c_invokes_check_session_total` - reads qor-plan SKILL.md, locates Step 2c, asserts the block references `check_session_total` alongside the existing `cce.check`.
- `tests/test_session_total_escalator_skill_wiring.py::test_qor_audit_step_0_5_invokes_check_session_total` - same check against qor-audit SKILL.md Step 0.5.
- `tests/test_session_total_escalator_skill_wiring.py::test_doctrine_documents_session_total_mode` - reads doctrine-governance-enforcement.md §10.4 region, asserts it names the session-total mode and contrasts it with consecutive-streak.

## CI Commands

- `python -m pytest tests/test_session_total_signature_count.py tests/test_session_total_escalator_skill_wiring.py -v` - validates Phase 69 tests.
- `python -m qor.scripts.dist_compile` - regenerates dist variants.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase69-session-total-signature-escalator.md` - self-application: lint this plan with Phase 67's wired discipline.
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py` - full suite.
