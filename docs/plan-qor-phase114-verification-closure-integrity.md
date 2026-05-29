# Plan: Phase 114 - Verification & Closure Integrity (spine slice) (#166, #158)

**change_class**: feature

**doc_tier**: system

**Risk Grade**: L3

**high_risk_target**: false

**originating_remediation**: GH #147 (half-measure umbrella); GH #166 + #158; ideation `2026-05-29T0252-f6486c`; research brief docs/research-brief-verification-closure-integrity-2026-05-29.md

**terms_introduced**:
- term: QA Evidence Artifact
  home: qor/references/doctrine-verification-closure-integrity.md
- term: Acceptance-Criteria Close Guard
  home: qor/references/doctrine-verification-closure-integrity.md

**boundaries**:
- limitations: Spine slice only. Ships the qa.json evidence artifact (regression pillar real; security/stability/coverage pillars honestly marked skip with follow-on pointers), the deferred FEATURE_INDEX regression ABORT CLI (#155/#40), and the acceptance-criteria close guard (#158) WARN-first. Close guard does not block a seal in V1.
- non_goals: SAST authoring, the coverage pillar, seal-time runtime-contract re-walk, and the prose-not-behavior test-source lint are DEFERRED to tracked follow-ons (filed at handoff), NOT built here. No new QA skill is authored (research reframe: consolidate existing surfaces).
- exclusions: No change to the live seal PASS/VETO decision; close guard is advisory in V1. No commit/push/PR/merge (Review Boundary).

## Locked Decisions

- **LD1 (reframe, per research)**: This is NOT a new QA discipline/skill. It is the fail-closed promotion + wiring of existing surfaces. Regression pillar reuses `qor.scripts.feature_index_verify.tally`; the DoD D4 tier (`doctrine-definition-of-done.md`) is the conceptual home; `skill_size_budget_lint` (#162) is the context-lean guardrail, not a merge target.
- **LD2 (high_risk_target semantics)**: Risk Grade is L3 (internal: touches the seal/close control path). `high_risk_target` stays `false` because the EU AI Act Annex III sense (supporting a downstream high-risk AI system) does not apply to internal governance tooling. A full `impact_assessment` block is included regardless, per the L3 evidence bar. Misrepresenting the flag would itself be a governance-integrity defect.
- **LD3 (close guard WARN-first)**: The close guard sits on the seal control path; it ships WARN-only (exit 0, prints findings) with an `--enforce` flag reserved for a graduated V2 once false-positive rate is measured. Met-ness comes from the qa.json evidence verdict, NOT from checkbox state at close time; unmet checkboxes must have a linked follow-on. Issues with no machine-checkable checklist fall back to ALLOW + WARN.
- **LD4 (honest partial pillars)**: The qa.json artifact carries all four pillars, but only `regression` is wired to real evidence in this slice. `security`, `stability`, `coverage` are emitted with `status: "skip"` and a `note` naming their follow-on. This is explicit, not silent omission (anti-half-measure).

## Context

The 2026-05-29 closed-issue audit (umbrella #147) found 10/52 issues closed on half-measures: advisory layers shipped, enforcers deferred to unfiled V2s. Research (`research.json`, session `2026-05-29T0252-f6486c`) reframed the fix as completing two scoped deferrals (#155/#40 FEATURE_INDEX ABORT; #158 close guard) plus a compact qa.json evidence spine, reusing existing parsing/gate primitives.

## Feature Inventory Touches

Empty. Governance tooling + schema + doctrine; no `src/` product feature surface.
`feature_inventory_touches`: `[]`.

## Impact Assessment

- **purpose**: Make local-cycle "done" provable: emit a compact QA evidence artifact and add an acceptance-criteria close guard so issues are not asserted closed without met-or-split criteria. Counter-control for the half-measure pattern (SG-HalfMeasureClosure).
- **affected_stakeholders**: maintainer/operator; coding agents executing the SDLC; downstream consumer workspaces that inherit governance tooling.
- **identified_risks**:
  - R1: A close guard on the seal path could block legitimate closures (false positives) if acceptance-criteria formats vary.
  - R2: A FEATURE_INDEX ABORT that exits non-zero could halt a seal on a stale/missing snapshot.
  - R3: qa.json could imply more verification than performed if partial pillars are not clearly marked.
  - R4: gh dependency unavailable on offline/non-GitHub hosts.
- **mitigations**:
  - M1 (R1): close guard is WARN-first (exit 0) in V1; no-checklist issues fall back to ALLOW+WARN; enforcement gated behind a future `--enforce` flag after FP measurement.
  - M2 (R2): ABORT CLI provides `--warn-only`; missing snapshot/index yields a clear skip, not a crash.
  - M3 (R3): partial pillars emit `status: "skip"` + a `note` naming the follow-on; schema enumerates pillar status.
  - M4 (R4): reuse `create_shadow_issue.ensure_gh_auth` + Phase 75 SKIP semantics; guard degrades to a documented skip when gh absent.
- **residual_risks**: With WARN-first, residual blast radius is low (advisory only). Residual: operators may ignore WARN output (accepted in V1; V2 graduates to enforcement). The semantic gap between Qor L3 grade and EU AI Act high_risk_target is documented (LD2), not enforced.

## Phase 1: qa.json evidence artifact

### Affected Files
- `tests/test_qa_evidence.py` - NEW. Behavioral: schema round-trip validates; pillar status enum enforced; partial-pillar skip+note; regression pillar derived from a feature_index summary; invalid verdict rejected.
- `qor/gates/schema/qa.schema.json` - NEW. Envelope (phase const `qa`, ts, session_id, ai_provenance) + `verdict` PASS|FAIL + `pillars{regression,security,stability,coverage}` each `{status: pass|fail|skip, evidence?, metric?, note?}`.
- `qor/scripts/qa_evidence.py` - NEW. `build_payload(regression_summary, ...) -> dict` and `write(sid) -> Path` via `gate_chain.write_gate_artifact("qa", ..., skill="qa")`; regression pillar status derived from `IndexSummary` (fail iff `newly_unverified`); other pillars default skip+note.
- `qor/scripts/validate_gate_artifact.py` - AMENDED. Add `"qa"` to `PHASES`.

### Unit Tests
- `test_qa_evidence.py::test_payload_validates_against_schema` - built payload passes `validate_one("qa", ...)`.
- `::test_invalid_verdict_rejected` - verdict outside PASS|FAIL fails validation.
- `::test_pillar_status_enum_enforced` - a pillar status outside pass|fail|skip fails validation.
- `::test_regression_pillar_fails_on_newly_unverified` - `IndexSummary(newly_unverified=("x",))` -> regression status fail and overall verdict FAIL.
- `::test_partial_pillars_skip_with_note` - security/stability/coverage emit skip + non-empty note.

## Phase 2: FEATURE_INDEX regression ABORT CLI (#155/#40)

### Affected Files
- `tests/test_feature_index_abort.py` - NEW. Behavioral: exit 0 when no regressions; exit non-zero when `newly_unverified` non-empty; exit 0 under `--warn-only`; missing index -> skip exit 0.
- `qor/scripts/feature_index_verify.py` - AMENDED. Add `main(argv)`/argparse: `--repo-root`, `--snapshot <sid>`, `--warn-only`. Loads prior snapshot via `read_seal_snapshot`, calls `tally`, prints summary; exits 1 when `newly_unverified` and not `--warn-only`.

### Unit Tests
- `test_feature_index_abort.py::test_exit_zero_no_regression` - clean index -> rc 0.
- `::test_exit_nonzero_on_newly_unverified` - prior snapshot verified + current unverified -> rc 1.
- `::test_warn_only_suppresses_exit` - same regression + `--warn-only` -> rc 0.
- `::test_missing_index_skips` - no FEATURE_INDEX -> rc 0 with skip notice.

## Phase 3: Acceptance-Criteria Close Guard (#158, WARN-first)

### Affected Files
- `tests/test_ac_close_guard.py` - NEW. Behavioral on pure functions: parse met/unmet/none; decide allow/block reasons; WARN-first CLI exits 0; qa verdict consumed.
- `qor/scripts/ac_close_guard.py` - NEW. `parse_acceptance_criteria(body) -> list[Criterion]` (section-slice for "Acceptance criteria" + checkbox regex, fence-stripped); `evaluate(criteria, followons, qa_verdict) -> Decision`; thin gh layer `_issue_body`/`_followons`; `main()` WARN-first (exit 0), `--enforce` reserved.

### Unit Tests
- `test_ac_close_guard.py::test_parse_met_and_unmet` - mixed `- [x]`/`- [ ]` parsed correctly.
- `::test_parse_no_checklist_returns_empty` - body without a checklist -> [].
- `::test_evaluate_all_met_allows` - all met -> allow, no warnings.
- `::test_evaluate_unmet_without_followon_flags` - unmet + no follow-on -> would_block reason present.
- `::test_evaluate_unmet_with_followon_ok` - unmet + linked follow-on -> allowed.
- `::test_evaluate_qa_verdict_fail_warns` - qa verdict FAIL -> warning present.
- `::test_no_checklist_fallback_allows_with_warn` - empty criteria -> allow + warn.

## Phase 4: wiring + doctrine (context-lean)

### Affected Files
- `qor/references/doctrine-verification-closure-integrity.md` - NEW. Compact: the qa.json contract, the close-guard met-or-split rule, the WARN-first->enforce graduation, the two glossary terms. Detail lives here, not inline in SKILL.md (context-lean constraint, #162).
- `qor/skills/governance/qor-substantiate/SKILL.md` - AMENDED (minimal). Consolidate the FEATURE_INDEX ABORT into the EXISTING FEATURE_INDEX verification pass (replace the "manual / deferred" note at the pass with the CLI invocation); add a brief Step 4.6.10 close-guard line pointing to the doctrine. No large prose blocks inline.
- `tests/test_vci_wiring.py` - NEW. Behavioral-ish: substantiate SKILL.md invokes feature_index_verify CLI and ac_close_guard; doctrine defines the two terms and the WARN-first rule. (Kept minimal; the load-bearing tests are the behavioral ones in Phases 1-3.)

### Unit Tests
- `test_vci_wiring.py::test_substantiate_invokes_feature_index_abort` - the FEATURE_INDEX pass references the CLI module (not "deferred").
- `::test_substantiate_references_close_guard` - a close-guard step references `ac_close_guard`.
- `::test_doctrine_defines_terms_and_warn_first_rule` - doctrine parser asserts both terms + the WARN-first graduation rule + met-or-split rule.

## Definition of Done

### Deliverable D-114.1: qa.json evidence artifact
- **D1**: A compact, schema-validated QA evidence artifact records per-pillar status + overall verdict, readable by the close guard.
- **D2**: `qa.schema.json` + `qa_evidence.py` + `"qa"` registered in PHASES.
- **D3**: `doctrine-verification-closure-integrity.md` documents the qa.json contract; partial pillars marked skip+note.
- **D4**: `tests/test_qa_evidence.py` passes all five cases.

### Deliverable D-114.2: FEATURE_INDEX regression ABORT (#155/#40)
- **D1**: The deferred regression gate exists: a CLI that exits non-zero on outside-scope verified->unverified regression.
- **D2**: `feature_index_verify.main` with `--warn-only`; wired into the existing substantiate FEATURE_INDEX pass.
- **D3**: Doctrine notes the ABORT and the `--warn-only` graduated path.
- **D4**: `tests/test_feature_index_abort.py` passes all four cases.

### Deliverable D-114.3: Acceptance-Criteria Close Guard (#158)
- **D1**: A WARN-first guard parses an issue's acceptance criteria and flags unmet-without-follow-on; consumes qa.json verdict.
- **D2**: `ac_close_guard.py` with pure parse/evaluate functions + thin gh layer + `--enforce` reserved; substantiate Step 4.6.10.
- **D3**: Doctrine states the met-or-split rule, the no-checklist ALLOW+WARN fallback, and the WARN-first->enforce graduation.
- **D4**: `tests/test_ac_close_guard.py` passes all seven cases.

## CI Commands

- `python -m pytest tests/test_qa_evidence.py tests/test_feature_index_abort.py tests/test_ac_close_guard.py tests/test_vci_wiring.py -q` - new behavioral suites.
- `python -m pytest tests/ -q` - full regression.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase114-verification-closure-integrity.md` - plan-internal consistency.
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase114-verification-closure-integrity.md` - Definition of Done declaration check.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` - ledger chain integrity.

## CI Coverage Exemptions

- `test_packaging_install` - packaging smoke; orthogonal.
- `dependency_admission_lint` - no dependency changes (stdlib + existing gh only).
- `check_variant_drift` - substantiate SKILL.md edit will be recompiled to variants before seal; flagged for the substantiate step.
