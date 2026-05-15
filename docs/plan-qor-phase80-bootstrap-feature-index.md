# Plan: Phase 80 - qor-bootstrap scaffolds FEATURE_INDEX.md (GH #73)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #73 -- Phase 73 made `docs/FEATURE_INDEX.md` a hard obligation inside `/qor-implement` (Step 12.5 staging fails when `src/` is touched but `FEATURE_INDEX.md` is not appended/updated). But `/qor-bootstrap` does not seed the file. Result: chicken-and-egg on first cycle of newly-bootstrapped projects -- the implementing agent either creates `FEATURE_INDEX.md` manually (off-protocol) or has implement bend the rule (defeats the obligation). Closing this requires adding the seed scaffold to bootstrap.

**terms_introduced**:
- term: FEATURE_INDEX.md genesis seed
  home: qor/skills/meta/qor-bootstrap/SKILL.md

**boundaries**:
- limitations:
  - V1 ships the bootstrap-side seed only. The plan-time mechanical lint that compares `Feature Inventory Touches` declarations against shipped `FEATURE_INDEX.md` rows (GH #73 bonus suggestion `Step 10.6`) is deferred to a follow-on phase; V1 unblocks the obligation, V2 mechanizes the check.
- non_goals:
  - No new `qor/scripts/feature_index_lint.py`.
  - No changes to `/qor-implement` Step 12.5 (the staging gate already enforces the obligation; this phase makes the gate satisfiable on first cycle).
  - No changes to `/qor-substantiate`.
- exclusions:
  - No CI workflow changes.
  - No backfill of past-bootstrapped projects (forward-only; existing projects already either have a FEATURE_INDEX.md or have routed around the gap operator-side).

## Open Questions

None. GH #73 specifies the exact seed template; insertion point is between Step 6.5 (Create Backlog) and Step 7 (Calculate Genesis Hash).

## Feature Inventory Touches

| FEATURE_INDEX entry | Operation | Test descriptor |
|---|---|---|
| qor-bootstrap Step 6.6 FEATURE_INDEX.md seed | NEW | tests/test_qor_bootstrap_feature_index_seed.py asserts SKILL.md has Step 6.6 + Coverage Summary scaffold + 4-column table header + Phase 73 obligation cross-reference |
| qor-bootstrap templates FEATURE_INDEX.md section | NEW | tests/test_qor_bootstrap_feature_index_template.py asserts references/qor-bootstrap-templates.md has the FEATURE_INDEX seed template with required sections |

## Phase 1: Step 6.6 Seed FEATURE_INDEX.md (qor-bootstrap)

### Affected Files

- `qor/skills/meta/qor-bootstrap/SKILL.md` -- insert new Step 6.6 between Step 6.5 (Create Backlog) and Step 7 (Calculate Genesis Hash). Update Success Criteria with `FEATURE_INDEX.md exists with seed scaffold`.
- `qor/skills/meta/qor-bootstrap/references/qor-bootstrap-templates.md` -- new `## FEATURE_INDEX.md Template` section.
- `tests/test_qor_bootstrap_feature_index_seed.py` -- NEW. 2 tests.
- `tests/test_qor_bootstrap_feature_index_template.py` -- NEW. 1 test.

### Changes

Insert `### Step 6.6: Seed FEATURE_INDEX.md` step. Body authors `docs/FEATURE_INDEX.md` from the template (single canonical cross-reference of every user-touchable feature against documentation, source code, and test surface; updated per Phase 73 obligation in every `/qor-implement` cycle).

Template structure (per GH #73 acceptance):
- Title: `# {project_name} Feature Index`
- One-paragraph purpose statement naming Phase 73 obligation as the consumer.
- `## Coverage Summary` block with 0/0/0/0 placeholders (Verified / Unverified / N/A / Total).
- One placeholder `## Section: {category}` with a 7-column table (`| ID | Feature | Doc | Code | Test | Status | Notes |`) and a leading HTML comment marker (`<!-- First /qor-implement cycle appends rows here. -->`).
- `## Gaps Surfaced` placeholder block.

Update Success Criteria to add: `[ ] FEATURE_INDEX.md exists with seed scaffold (Phase 73 obligation satisfiable on first cycle)`.

### Unit Tests

- `tests/test_qor_bootstrap_feature_index_seed.py::test_step_6_6_seeds_feature_index_with_phase73_cross_reference` -- reads bootstrap SKILL.md, asserts Step 6.6 names `FEATURE_INDEX.md` + `Phase 73` + the obligation rationale (chicken-and-egg on first /qor-implement cycle).
- `tests/test_qor_bootstrap_feature_index_seed.py::test_success_criteria_lists_feature_index_seed` -- asserts Success Criteria includes the new `FEATURE_INDEX.md exists with seed scaffold` bullet.
- `tests/test_qor_bootstrap_feature_index_template.py::test_templates_define_feature_index_section` -- reads templates file, asserts `## FEATURE_INDEX.md Template` section exists with the 7-column table header and the Coverage Summary scaffold.

## Phase 2: Glossary term

### Affected Files

- `qor/references/glossary.md` -- add 1 new term: `FEATURE_INDEX.md genesis seed`.
- `tests/test_glossary_feature_index_seed_term.py` -- NEW. 1 test.

### Changes

Add glossary entry pointing at bootstrap SKILL.md home.

### Unit Tests

- `tests/test_glossary_feature_index_seed_term.py::test_glossary_defines_feature_index_seed_term` -- asserts term present with Phase 80 plan slug.

## CI Commands

- `python -m pytest tests/test_qor_bootstrap_feature_index_seed.py tests/test_qor_bootstrap_feature_index_template.py tests/test_glossary_feature_index_seed_term.py -v` -- validates Phase 80 tests.
- `python -m qor.scripts.dist_compile` -- regenerates dist variants.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase80-bootstrap-feature-index.md` -- self-application.
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py` -- full suite.
