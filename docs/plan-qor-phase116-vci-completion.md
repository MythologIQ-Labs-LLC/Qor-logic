# Plan: Phase 116 - VCI completion (coverage + stability + prose-lint) (#168, #169, #170)

**change_class**: feature

**doc_tier**: system

**Risk Grade**: L2

**high_risk_target**: false

**originating_remediation**: GH #168, #169, #170; parent #166; umbrella #147; follows Phase 115 (v0.82.0)

**terms_introduced**:
- term: Prose-Behavior Test Lint
  home: qor/references/doctrine-verification-closure-integrity.md

**boundaries**:
- limitations: Completes the qa.json pillars (coverage + stability) and adds the prose-not-behavior test-source lint. Coverage reads an existing coverage data file (skip if absent). Stability re-walks the plan's modules via the existing `runtime_contract_walk` (reuse, not re-author). Prose lint is WARN-first.
- non_goals: No new coverage/runtime tooling authored (reuse coverage.py + runtime_contract_walk). No change to the seal PASS/VETO path; qa pillars stay advisory.
- exclusions: No commit/push/PR beyond the local seal.

## Locked Decisions

- **LD1 (reuse, per the research reframe)**: stability pillar reuses `qor.scripts.runtime_contract_walk.walk_plan` (#108); coverage uses the already-installed `coverage` package. No parallel tooling.
- **LD2 (graceful skip)**: coverage pillar skips when no coverage data file is present (Phase 75 pattern), so the pillar never fabricates a number.
- **LD3 (prose lint WARN-first)**: `prose_test_lint` flags presence-only test assertions (substring-in-SKILL.md) but is WARN-first when wired into `/qor-audit`; it reuses the `plan_test_lint` presence vocabulary as a starting point and adds AST-level test-source detection.

## Context

Phase 114 shipped qa.json with stability/coverage pillars as explicit skip; Phase 115 filled security (SAST). This phase fills the last two pillars and adds the test-source prose-not-behavior lint (#170, the secondary AC of #158) that would have caught #56/#58/#83.

## Feature Inventory Touches

Empty. Governance/QA tooling; no `src/` product feature surface.
`feature_inventory_touches`: `[]`.

## Phase 1: coverage pillar (#168)

### Affected Files
- `tests/test_coverage_pillar.py` - NEW. Behavioral: `coverage_pillar(pct, min_pct)` pass>=threshold, fail<threshold; `run_coverage` skips when no data file.
- `qor/scripts/qa_evidence.py` - AMENDED. `coverage_pillar(total_pct, *, min_pct=80.0) -> dict` and `run_coverage(data_file=".coverage", min_pct=80.0) -> dict` (loads coverage data via the `coverage` API; skip if absent).

### Unit Tests
- `test_coverage_pillar.py::test_pass_at_or_above_threshold` - 91.0 >= 80 -> pass, metric 91.0.
- `::test_fail_below_threshold` - 70.0 < 80 -> fail.
- `::test_run_coverage_skips_without_data` - no `.coverage` -> status skip.

## Phase 2: stability pillar via runtime re-walk (#169)

### Affected Files
- `tests/test_stability_pillar.py` - NEW. Behavioral: `run_stability(plan_path)` pass when walk finds nothing, fail when walk returns findings, skip when plan absent/no modules.
- `qor/scripts/qa_evidence.py` - AMENDED. `run_stability(plan_path, repo_root=".") -> dict` calling `runtime_contract_walk.walk_plan`; maps findings -> pillar.

### Unit Tests
- `test_stability_pillar.py::test_pass_on_no_findings` - monkeypatched walk returns [] -> pass.
- `::test_fail_on_findings` - walk returns a finding -> fail with note.
- `::test_skip_when_plan_absent` - missing plan -> skip.

## Phase 3: prose-not-behavior test-source lint (#170)

### Affected Files
- `tests/test_prose_test_lint.py` - NEW. Behavioral: a test that reads a SKILL.md and asserts a substring is flagged; a behavioral test is not flagged; clean dir -> no findings.
- `qor/scripts/prose_test_lint.py` - NEW. AST scan over `tests/*.py`: flag `assert "<literal>" in <var>` where `<var>` is bound from a `*.read_text()` of a path containing `SKILL.md` (low-false-positive). CLI WARN-first.
- `qor/references/doctrine-verification-closure-integrity.md` - AMENDED. Add Prose-Behavior Test Lint term + the coverage/stability pillar contracts.
- `qor/skills/governance/qor-audit/SKILL.md` - AMENDED (minimal). Reference `prose_test_lint` in the Test Functionality Pass (WARN-first).

### Unit Tests
- `test_prose_test_lint.py::test_flags_presence_only_assertion` - SKILL.md-substring assertion flagged.
- `::test_ignores_behavioral_test` - a test calling a unit and asserting output not flagged.
- `::test_clean_returns_empty` - dir with no presence-only tests -> [].
- `::test_doctrine_defines_prose_lint_term` - doctrine parser asserts the term + coverage/stability contracts.

## Definition of Done

### Deliverable D-116.1: coverage pillar (#168)
- **D1**: qa.json coverage pillar carries a real coverage metric vs a threshold, skipping when no data.
- **D2**: `qa_evidence.coverage_pillar` + `run_coverage`.
- **D3**: Doctrine documents the coverage pillar.
- **D4**: `tests/test_coverage_pillar.py` passes.

### Deliverable D-116.2: stability pillar (#169)
- **D1**: qa.json stability pillar re-walks the runtime contract at seal time, reusing #108.
- **D2**: `qa_evidence.run_stability` over `runtime_contract_walk.walk_plan`.
- **D3**: Doctrine documents the stability pillar.
- **D4**: `tests/test_stability_pillar.py` passes.

### Deliverable D-116.3: prose-not-behavior lint (#170)
- **D1**: A test-source lint flags presence-only (substring-in-SKILL.md) assertions; WARN-first in qor-audit.
- **D2**: `qor/scripts/prose_test_lint.py` + qor-audit Test Functionality Pass reference.
- **D3**: Doctrine documents the Prose-Behavior Test Lint term.
- **D4**: `tests/test_prose_test_lint.py` passes.

## CI Commands

- `python -m pytest tests/test_coverage_pillar.py tests/test_stability_pillar.py tests/test_prose_test_lint.py -q` - new behavioral suites.
- `python -m pytest tests/ -q` - full regression.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase116-vci-completion.md` - plan-internal consistency.
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase116-vci-completion.md` - Definition of Done declaration check.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` - ledger chain integrity.

## CI Coverage Exemptions

- `test_packaging_install` - packaging smoke; orthogonal.
