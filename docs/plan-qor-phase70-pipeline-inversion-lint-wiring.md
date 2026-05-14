# Plan: Phase 70 - pipeline_inversion_lint wiring into qor-audit

**change_class**: hotfix

**doc_tier**: standard

**originating_remediation**: GH #47 (qor-audit: probe filter-stage ordering in multi-stage pipelines -- Wave 2 manual review blind spot).

**terms_introduced**: none. Builds on existing `qor/scripts/pipeline_inversion_lint.py` shipped at Phase 49.

**boundaries**:
- limitations:
  - V1 wires the existing `pipeline_inversion_lint.py` heuristic detector. The lint surfaces candidate inversions; final verdict is the Judge's at audit time.
  - The lint is advisory (WARN-only), matching the existing Step 0.6 pre-audit lint pattern.
- non_goals:
  - Extending the lint's detection rules (those exist in COREFORGE's Phase 49 implementation).
  - Replacing manual filter-ordering review with the lint; the lint augments, not replaces.
- exclusions:
  - No changes to the lint script itself.
  - No CLI changes.

## Open Questions

None. The pre-existing `pipeline_inversion_lint.py` defines the detector contract; Phase 70 wires it into the operator-visible audit flow.

## Phase 1: Wire pipeline_inversion_lint into qor-audit Step 0.6 + SG doctrine

### Affected Files

- `tests/test_pipeline_inversion_lint_audit_wiring.py` - NEW. 3 tests asserting qor-audit Step 0.6 invokes pipeline_inversion_lint alongside the other three pre-audit lints, and doctrine documents SG-FilterStageInversion-A.
- `qor/skills/governance/qor-audit/SKILL.md` - Step 0.6 gains a fourth lint invocation for pipeline_inversion_lint on the repo source (not the plan; this lint walks `.py` files for filter pipelines).
- `qor/references/doctrine-shadow-genome-countermeasures.md` - new SG entry `SG-FilterStageInversion-A`: filter-stage ordering composition defect class.

### Changes

Step 0.6 currently runs three lints (`plan_test_lint`, `plan_grep_lint`, `plan_text_consistency_lint`). Phase 70 adds a fourth:

```bash
python -m qor.scripts.pipeline_inversion_lint --repo-root . || true
```

The lint's `--repo-root` mode scans every `.py` file under the repo for filter-pipeline shapes and emits advisory findings. WARN-only at audit time; Judge confirms whether the surfaced order represents a real inversion.

Doctrine entry documents the COREFORGE Skill-Forge V1 dispatcher inversion (commit `0999e47`) as the originating pattern. The countermeasure narrative explains why stage-by-stage correctness review (Wave 2) misses composition defects, and how the lint catches them via dependency-graph inference.

### Unit Tests

- `tests/test_pipeline_inversion_lint_audit_wiring.py::test_qor_audit_step_0_6_invokes_pipeline_inversion_lint` - reads qor-audit SKILL.md, locates Step 0.6 body, asserts the module invocation `pipeline_inversion_lint` appears alongside the existing three lints.
- `tests/test_pipeline_inversion_lint_audit_wiring.py::test_doctrine_sg_filter_stage_inversion_documented` - reads the doctrine file, asserts `SG-FilterStageInversion-A` entry is present with the canonical pattern description and cites the COREFORGE dispatcher origin.
- `tests/test_pipeline_inversion_lint_audit_wiring.py::test_step_0_6_lints_use_consistent_warn_pattern` - asserts all four lint invocations in Step 0.6 use the same `|| true` WARN-only trailing pattern (no accidental fail-closed wiring on a lint that's meant to be advisory).

## CI Commands

- `python -m pytest tests/test_pipeline_inversion_lint_audit_wiring.py -v` - validates Phase 70 tests.
- `python -m qor.scripts.dist_compile` - regenerates dist variants.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase70-pipeline-inversion-lint-wiring.md` - self-application with Phase 67's wired discipline.
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py` - full suite.
