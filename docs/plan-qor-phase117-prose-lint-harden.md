# Plan: Phase 117 - prose_test_lint harden + allowlist + convert + enforce (#174)

**change_class**: feature

**doc_tier**: system

**Risk Grade**: L2

**high_risk_target**: false

**originating_remediation**: GH #174; research brief docs/research-brief-prose-test-lint-debt-2026-05-29.md; follows #170 (Phase 116)

**boundaries**:
- limitations: Hardens `prose_test_lint` so it only flags assertions whose membership comparator traces to a SKILL.md read (eliminates the 8 false positives); adds an inline `# prose-lint: ok=<reason>` allowlist; exempts the 18 legitimate prose-contract findings; converts the 14 genuine ones (importability / file-existence / live-constant); then graduates the lint to `--enforce` in `/qor-audit` once unexplained findings reach 0.
- non_goals: No change to the qa.json pillars or other VCI surfaces. No mass rewrite of tests beyond the 14 converts + 19 allowlists identified by research.
- exclusions: No commit/push/PR beyond the local seal. Does NOT correct the v0.83.0-tag pyproject mismatch (separate operator decision; flagged in handoff).

## Locked Decisions

- **LD1 (harden first)**: per research, the lint over-flags (~20%). `scan_source` must bind the `in` comparator to a SKILL.md-derived value (a var assigned from a SKILL.md `.read_text()`, or an inline SKILL.md read), not any membership assert in a function that merely mentions SKILL.md. This drops 7 of 8 false positives mechanically; the 1 synthetic-fixture round-trip is allowlisted.
- **LD2 (allowlist = inline comment)**: `# prose-lint: ok=<reason>` on the assert line (or its function) suppresses the finding; empty reason still flags. The lint reports `exempted (with reason)` separately from `unexplained`.
- **LD3 (convert vs exempt per research triage)**: 14 convertible (7 module -> find_spec, 5 doc/file -> .exists(), 2 path -> session.MARKER_PATH); 18 prose-contract -> allowlist with reason.
- **LD4 (enforce last)**: graduate `/qor-audit` Test Functionality Pass from WARN-first to `--enforce` (non-zero -> VETO) only after unexplained == 0.

## Context

#174 was filed as "convert 40 presence-only tests." Research reclassified them: 8 lint false positives, 18 legitimate prose-contract, 14 genuinely convertible. The load-bearing fix the original framing missed is hardening the lint's heuristic before enforcing.

## Feature Inventory Touches

Empty. Governance/test tooling; no `src/` product feature surface.
`feature_inventory_touches`: `[]`.

## Phase 1: harden prose_test_lint + allowlist

### Affected Files
- `tests/test_prose_test_lint.py` - AMENDED. Add regression tests for the 4 false-positive shapes (comparator = subprocess stderr / module source / emitted dict / synthetic-but-real-SKILL.md fixture) -> NOT flagged; and allowlist tests (`# prose-lint: ok=reason` suppresses; empty reason still flags).
- `qor/scripts/prose_test_lint.py` - AMENDED. `scan_source`: track vars bound from a SKILL.md `.read_text()`; flag `assert <str> in <x>` only when `<x>` is such a doc-var or an inline SKILL.md read. Add `# prose-lint: ok=<reason>` recognition; return exempted-with-reason separately; `scan_dir` reports unexplained vs exempted counts.

### Unit Tests
- `test_prose_test_lint.py::test_ignores_assert_on_subprocess_stderr` - comparator = proc.stderr -> not flagged.
- `::test_ignores_assert_on_module_source` - comparator = a non-SKILL.md read -> not flagged.
- `::test_ignores_assert_on_emitted_dict` - comparator = a dict from an emitter -> not flagged.
- `::test_allowlist_comment_suppresses` - `# prose-lint: ok=reason` on the assert -> not in unexplained.
- `::test_allowlist_requires_reason` - `# prose-lint: ok=` (empty) -> still flagged.
- (existing flags-presence-only / ignores-behavioral tests retained.)

## Phase 2: exempt the 18 + convert the 14

### Affected Files (test edits per the research triage; cite file:line)
- ALLOWLIST (18): add `# prose-lint: ok=<reason>` to the prose-contract assertions in `test_audit_skill_iteration_lint_wiring.py` (lines 40,41), `test_ci_coverage_lint_wiring.py` (44), `test_dod_substantiate_wiring.py` (45), `test_merge_velocity_substantiate_wiring.py` (41), `test_install_drift_wiring.py` (24), `test_qor_substantiate_capability_declarations.py` (9), `test_persona_sweep.py` (109,110), `test_qor_research_issue_state_check.py` (42,46,50,51,81), `test_shadow_genome_doctrine.py` (178,179), `test_substantiate_tag_push_timing.py` (81,82), and `test_qor_plan_skill_invokes_model_pinning_lint.py` (108, synthetic fixture).
- CONVERT (14): add behavioral assertions in `test_audit_risk_score_wiring.py` (54,55), `test_audit_skill_iteration_lint_wiring.py` (39), `test_ci_coverage_lint_wiring.py` (39), `test_dod_substantiate_wiring.py` (41), `test_merge_velocity_substantiate_wiring.py` (38), `test_install_drift_wiring.py` (33) -> `importlib.util.find_spec(...)`; `test_persona_sweep.py` (101,112), `test_shadow_genome_doctrine.py` (90,170,181) -> `Path(...).exists()`; `test_session_marker_path_unified.py` (34,44) -> assert against `session.MARKER_PATH`. Retained citation substrings get `# prose-lint: ok=paired with behavioral assertion`.

### Unit Tests
- The converted tests themselves are the tests; each must still pass and now assert behavior.
- `tests/test_prose_lint_floor.py` - NEW. Asserts `prose_test_lint.scan_dir("tests")` returns 0 UNEXPLAINED findings (exempted-with-reason allowed) -> the enforce floor.

## Phase 3: graduate to --enforce

### Affected Files
- `qor/skills/governance/qor-audit/SKILL.md` - AMENDED. Change the Phase 116 WARN-first prose_test_lint reference to `--enforce` (non-zero -> VETO `test-failure`), now that unexplained == 0.
- `qor/references/doctrine-verification-closure-integrity.md` - AMENDED. Update the Prose-Behavior Test Lint section: hardened heuristic, allowlist contract, enforced.

### Unit Tests
- `tests/test_prose_test_lint.py::test_enforce_exit_nonzero_on_unexplained` - `--enforce` with an unexplained finding -> rc 1; with only exempted -> rc 0.

## Definition of Done

### Deliverable D-117.1: hardened lint + allowlist
- **D1**: lint flags only SKILL.md-comparator asserts; inline allowlist with required reason.
- **D2**: `prose_test_lint.scan_source` comparator-tracing + allowlist; exempted/unexplained split.
- **D3**: doctrine updated.
- **D4**: `tests/test_prose_test_lint.py` false-positive + allowlist cases pass.

### Deliverable D-117.2: triage applied (18 exempt / 14 convert)
- **D1**: 18 prose-contract allowlisted with reasons; 14 converted to behavioral assertions.
- **D2**: edits per the research file:line list.
- **D3**: n/a.
- **D4**: `tests/test_prose_lint_floor.py` asserts 0 unexplained.

### Deliverable D-117.3: enforced gate
- **D1**: `/qor-audit` Test Functionality Pass enforces prose_test_lint (VETO on unexplained).
- **D2**: qor-audit SKILL.md `--enforce` wiring.
- **D3**: doctrine notes the graduation.
- **D4**: `test_prose_test_lint.py::test_enforce_exit_nonzero_on_unexplained` passes.

## CI Commands

- `python -m pytest tests/test_prose_test_lint.py tests/test_prose_lint_floor.py -q` - lint + floor.
- `python -m pytest tests/ -q` - full regression.
- `python -m qor.scripts.prose_test_lint --tests-dir tests` - confirm 0 unexplained.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase117-prose-lint-harden.md`
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase117-prose-lint-harden.md`
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md`

## CI Coverage Exemptions

- `test_packaging_install` - packaging smoke; orthogonal.
