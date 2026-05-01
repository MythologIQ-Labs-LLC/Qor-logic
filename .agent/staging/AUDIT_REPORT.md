# AUDIT REPORT — Phase 54: AI provenance metadata + EU AI Act/AI RMF doctrine + subagent scaffolding + override-friction escalator (Pass 2)

**Plan**: `docs/plan-qor-phase54-ai-provenance-and-act-alignment.md`
**Session**: `2026-04-30T1758-48db18`
**Mode**: Solo (Codex plugin not declared)
**Date**: 2026-04-30T18:35:00Z
**Verdict**: **PASS**
**Risk Grade**: L2
**Findings Categories**: (none)

Prior pass: VETO at Entry #175 with `test-failure`, `infrastructure-mismatch`, `razor-overage` categories. Plan amended per Pass-1 findings; re-audit follows.

---

## Audit Pass Results

### Security Pass (L3) — PASS

Unchanged from Pass 1: no placeholder auth, no hardcoded credentials, no bypassed checks, no mock auth, no `// security: disabled for testing`.

### OWASP Top 10 Pass — PASS

- A03 Injection: argv-form invocations preserved; new `cli_handlers/compliance.py` follows the same pattern as `qor.cli`. Plan free of canary triggers in narrative prose.
- A04 Insecure Design: `OverrideFrictionRequired` exception path is not fail-open.
- A05 Security Misconfig: no new secrets.
- A08 Software/Data Integrity: stdlib only (`tomllib`, `json`, `argparse`, `dataclasses`, `pathlib`); no pickle/eval/exec/unsafe yaml.

### Ghost UI Pass — N/A

CLI/library only.

### Section 4 Razor Pass — PASS

| Check | Limit | Plan Proposes | Status |
|---|---|---|---|
| Max function lines | 40 | helpers ~6-30 LOC; declared explicitly across `ai_provenance.build_manifest`, `override_friction.check`, `compute_governance_attributes` etc. | OK |
| Max file lines | 250 | `ai_provenance.py` ~80 LOC; `override_friction.py` no explicit estimate (inferred small from API surface); `sprint_progress.py` no explicit estimate; `cli_handlers/compliance.py` ~110 LOC; `cli_handlers/__init__.py` ~3 LOC | OK |
| **`qor/cli.py` post-edit** | 250 | 227 LOC -> ~190 LOC after extraction of compliance handlers to `cli_handlers/compliance.py`; thin parser/dispatch retained | **OK** (Pass-1 razor-overage CLOSED) |
| Max nesting depth | 3 | not declared per-function, but module shapes (single-loop `scan`, single-conditional helpers) imply depth ≤ 2 | OK |
| Nested ternaries | 0 | zero declared | OK |

**Pass-1 razor-overage finding closed**: Phase 1 Affected Files now declares the CLI subcommand-handler split. New `qor/cli_handlers/__init__.py` (empty package marker, ~3 LOC) and `qor/cli_handlers/compliance.py` (~110 LOC) host all three compliance handlers (`do_report` extracted; `do_ai_provenance` and `do_sprint_progress` new) plus `register(sub)`. `qor/cli.py` reduces to ~190 LOC after the extraction, leaving headroom for Phase 55+ subcommand additions.

### Test Functionality Pass — PASS

Pass-1 VETO findings remediated. Re-evaluating each amended/reformed test against the acceptance question *"If the unit's behavior were silently broken but the artifact still existed, would this test fail?"*:

| Test description (post-amendment) | Invokes unit? | Asserts on output? | Verdict |
|---|---|---|---|
| `test_schema_validates_full_manifest` | yes | yes | PASS |
| `test_schema_rejects_unknown_human_oversight_value` | yes | yes | PASS |
| `test_schema_optional_in_phase_schemas` | yes | yes | PASS |
| `test_schema_required_fields` | yes | yes | PASS |
| `test_build_manifest_returns_schema_valid_dict` | yes | yes | PASS |
| `test_build_manifest_reads_system_version_from_pyproject` | yes | yes (round-trip) | PASS |
| `test_build_manifest_rejects_invalid_human_oversight_for_phase` | yes | yes (ValueError) | PASS |
| `test_build_manifest_warns_once_on_missing_host` | yes | yes (stderr count + suppressible via `QOR_PROVENANCE_QUIET=1`) | PASS |
| **`test_skills_writing_gate_artifacts_invoke_build_manifest`** (replaces Pass-1 VETO test) | **yes** (walks SKILL.md tree, conditionally enumerates skills calling `gate_chain.write_gate_artifact(`, asserts each also calls `ai_provenance.build_manifest(`) | **yes** (per-skill assertion under conditional) | **PASS** |
| `test_cli_aggregates_session_provenance` | yes (subprocess) | yes (JSON output) | PASS |
| `test_cli_handles_missing_provenance_field` | yes | yes | PASS |
| `test_doctrine_round_trip_against_articles` | yes (heading-tree parse) | yes (per-article body integrity) | PASS |
| **`test_doctrine_classifies_qor_logic_under_applicability_section_with_non_empty_body`** (replaces Pass-1 borderline test) | **yes** (heading-tree integrity per Phase 53 template; reads `## Applicability classification` section; body-non-empty + substantive-length + canonical-substring round-trip on `Annex III` and `not high-risk`) | **yes** (multi-axis assertion) | **PASS** |
| `test_doctrine_round_trip_against_functions` | yes | yes | PASS |
| `test_doctrine_round_trip_against_genai_profile_sections` | yes | yes | PASS |
| `test_schema_accepts_plan_with_impact_assessment` | yes | yes | PASS |
| `test_schema_accepts_plan_without_impact_assessment` | yes | yes | PASS |
| `test_schema_rejects_high_risk_target_without_impact_assessment` | yes | yes | PASS |
| **`test_plan_skill_step_1c_round_trips_impact_assessment_subfields`** (replaces Pass-1 VETO test) | **yes** (reads `plan.schema.json`, extracts `impact_assessment` sub-field names, walks SKILL.md, asserts every sub-field name appears in Step 1c body AND body is non-empty after whitespace trim) | **yes** (schema-anchored round-trip + body-emptiness check) | **PASS** |
| `test_six_gate_skills_declare_permitted_tools` | yes (YAML parse + shape check) | yes | PASS |
| `test_permitted_tools_lint_warns_on_absent_skill` | yes | yes | PASS |
| `test_check_returns_false_below_threshold` | yes | yes | PASS |
| `test_check_returns_true_at_threshold` | yes | yes | PASS |
| `test_record_with_justification_validates_length` | yes | yes (ValueError) | PASS |
| `test_emit_gate_override_raises_on_third_without_justification` | yes | yes (exception) | PASS |
| `test_emit_gate_override_succeeds_with_justification` | yes | yes (event payload) | PASS |
| **`test_skills_emitting_gate_overrides_handle_friction_exception`** (replaces Pass-1 VETO test) | **yes** (walks SKILL.md tree, conditionally enumerates skills calling `gate_chain.emit_gate_override(`, asserts each also references `OverrideFrictionRequired` AND describes re-call with `justification=`) | **yes** (per-skill assertion under conditional) | **PASS** |
| `test_phase54_substantiate_gate_carries_ai_provenance` | yes | yes | PASS |
| `test_phase54_provenance_manifest_aggregator_emits_5_phases` | yes | yes | PASS |
| `test_phase54_self_scan_no_canary_triggers` | yes | yes | PASS |
| `test_cli_emits_priority_status_table` | yes | yes | PASS |
| `test_cli_handles_missing_brief` | yes | yes | PASS |

**All described tests now invoke the unit under test and assert on its output**. The three Pass-1 presence-only tests have been reformed:

1. `test_six_sdlc_skills_call_build_manifest` -> `test_skills_writing_gate_artifacts_invoke_build_manifest`. Now a true co-occurrence behavior invariant: the conditional rule "any skill calling `gate_chain.write_gate_artifact` MUST call `ai_provenance.build_manifest`" makes the assertion behavior-anchored. A regression in any gate-writing skill that drops the build_manifest call (whether deleted, moved into a comment block, or detached) is caught because the conditional set still includes that skill and the inner assertion fails.

2. `test_plan_skill_step_1c_present` -> `test_plan_skill_step_1c_round_trips_impact_assessment_subfields`. Schema-anchored round-trip integrity test (mirrors Phase 53's `test_doctrine_round_trip_against_canary_catalog` model). Drift between the schema's `impact_assessment` sub-field declarations and the SKILL.md prose surfaces immediately. Body-emptiness check rejects "heading-only" presence.

3. `test_six_gate_skills_handle_override_friction_required` -> `test_skills_emitting_gate_overrides_handle_friction_exception`. Co-occurrence behavior invariant: the conditional rule "any skill calling `emit_gate_override` MUST handle `OverrideFrictionRequired` AND describe re-call with `justification=`" anchors to the override-emission behavior.

4. Borderline `test_doctrine_declares_qor_logic_not_high_risk` -> `test_doctrine_classifies_qor_logic_under_applicability_section_with_non_empty_body`. Heading-tree integrity per Phase 53 template; multi-axis assertion (heading present + body non-empty + canonical-substring round-trip on `Annex III` and `not high-risk`).

### Dependency Audit — PASS

| Package | Justification | <10 lines vanilla? | Verdict |
|---|---|---|---|
| (none) | Zero new dependencies; uses stdlib (`tomllib`, `json`, `argparse`, `dataclasses`, `pathlib`) | yes | PASS |

### Macro-Level Architecture Pass — PASS

- Module boundaries clear: parser/dispatcher in `qor/cli.py`, subcommand handlers in `qor/cli_handlers/`, helpers under `qor/scripts/`, schemas under `qor/gates/schema/`, doctrine under `qor/references/`.
- New `qor/cli_handlers/` package is a clean layering split: cli (entry) → cli_handlers (subcommand handlers) → scripts (utility helpers). Forward direction; no reverse imports.
- No cycles. The `_provenance.schema.json` `$ref` from 6 phase schemas is JSON Schema cross-reference, not a Python import cycle.
- Single source of truth preserved: `_provenance.schema.json` for provenance shape; `qor.scripts.ai_provenance.build_manifest` for builder; `qor.cli_handlers.compliance` for compliance subcommand handlers; `qor.scripts.override_friction` for the escalator.
- Cross-cutting concerns (host detection, version derivation) consolidated in `ai_provenance.py`; not duplicated across the six skills.
- Build path explicit: `qor-logic compliance ai-provenance` argv-form CLI; `qor.cli_handlers.compliance.register(sub)` is the single registration site.

### Infrastructure Alignment Pass (Phase 37) — PASS

Pass-1 VETO finding remediated. Re-verifying each plan claim against HEAD:

1. ✓ `qor.scripts.qor_platform.current()` — verified at `qor/scripts/qor_platform.py:140`. Returns `dict | None` (full platform-state dict). Plan now correctly cites this path; `build_manifest` extracts host via `state.get("detected", {}).get("host", "unknown")` per the existing `qor-implement` SKILL.md Step 1.a pattern.
2. ✓ `qor.cli` `compliance` subcommand group exists at `qor/cli.py:150-160` (`_register_compliance_policy`); plan declares the existing `_do_compliance_report` body extracts to `qor/cli_handlers/compliance.py::do_report` (refactor, not break).
3. ✓ `qor.scripts.gate_chain.write_gate_artifact()` accepts kwargs at `qor/scripts/gate_chain.py:126`; additive `ai_provenance: dict | None = None` does not break existing callers.
4. ✓ `qor.scripts.gate_chain.emit_gate_override()` exists at `qor/scripts/gate_chain.py:83`.
5. ✓ `qor.scripts.cycle_count_escalator` exists; symmetric threshold (3) matches plan.
6. ✓ `qor.scripts.shadow_process.append_event` exists at `qor/scripts/shadow_process.py:68`.
7. ✓ `qor.scripts.validate_gate_artifact._validate_data` exists at `qor/scripts/validate_gate_artifact.py:112`.
8. ✓ `qor/gates/schema/shadow_event.schema.json` exists.
9. ✓ `tomllib` is Python 3.11+ stdlib (already required by `pyproject.toml`).

No infrastructure-mismatch findings remain.

### Orphan Detection — PASS

| Proposed File | Entry Point Connection | Status |
|---|---|---|
| `qor/scripts/ai_provenance.py` | imported by `qor.scripts.gate_chain.write_gate_artifact` and the six SDLC + governance skills' Step Z blocks | Connected |
| `qor/scripts/override_friction.py` | imported by `qor.scripts.gate_chain.emit_gate_override` | Connected |
| `qor/scripts/sprint_progress.py` | imported by `qor.cli_handlers.compliance.do_sprint_progress` (new entry surface) | Connected |
| `qor/cli_handlers/__init__.py` | package marker; required for `qor.cli_handlers.compliance` import | Connected |
| `qor/cli_handlers/compliance.py` | imported by `qor.cli` parser/dispatcher via `register(sub)` call | Connected |
| `qor/gates/schema/_provenance.schema.json` | `$ref`'d from 6 phase schemas | Connected |
| `qor/references/doctrine-eu-ai-act.md` / `doctrine-ai-rmf.md` | cross-linked from `CLAUDE.md` Authority line + plan template impact-assessment Step 1c | Connected |
| 12 new test files | pytest collection | Connected |

---

## Verdict: **PASS**

All eight passes clear. Plan-text defects from Pass 1 (`razor-overage`, `test-failure`, `infrastructure-mismatch`) are remediated. Architectural posture is preserved: bundling Priorities 2/4/5 into one feature phase; `_provenance.schema.json` `$ref` single source of truth; `human_oversight` enum mapping cleanly to EU AI Act Art. 14; override-friction threshold (3) symmetric with cycle-count escalator; declarative-only `permitted_tools` frontmatter as a clean two-step rollout for Phase 55 enforcement; self-application Phase 4 + sprint-progress dashboard as correct meta-coherence checks.

### No findings

(empty `findings_categories` array; PASS verdict carries no entries.)

### Required next action

Per `qor/gates/chain.md`: `/qor-implement`. Implementation should track each phase explicitly and run the CI Commands listed in the plan after each phase to detect regressions early. The intent-lock will capture plan + audit + HEAD fingerprint at `/qor-implement` Step 5.5; substantiate-time verification at Step 4.6 will fail if any of those drift.

### Strengths preserved (do not change)

- CLI subcommand-handler split (Pass-2 amendment): clean layering separation; `qor/cli.py` regains headroom for Phase 55+ subcommand additions without re-hitting the razor cap.
- Co-occurrence behavior invariant pattern (Phase 50 model) consistently applied across the three reformed lints — *conditional on actual behavior, not literal substring presence*.
- Schema-anchored round-trip integrity (Phase 53 template) for Step 1c sub-field test — drift between schema and SKILL.md prose surfaces immediately.
- Heading-tree integrity (Phase 53 template) for the applicability-section doctrine test — body-emptiness rejection rejects heading-only presence.
- Override-friction count threshold (3) matches the existing cycle-count escalator — symmetric, learnable, single tuning point across the override-discipline doctrine.
- Subagent `permitted_tools` frontmatter as declarative-only this phase, with Phase 55 wiring the Cedar enforcement — clean two-step rollout.

### Process pattern advisory

`veto_pattern.check()` would return `detected=False` (1 VETO + 1 PASS in this session; well below the 3-consecutive-same-signature threshold). No `/qor-remediate` recommendation.

**Cross-session pattern signal (carryover from Pass-1 advisory)**: The presence-only-test pattern recurred across Phase 53 and Phase 54 first audits despite SG-035 doctrine being live. Phase 55 should consider pre-audit lints (`qor/scripts/plan_test_lint.py`, `qor/scripts/plan_grep_lint.py`) that catch presence-only test descriptions and infrastructure-mismatch citations before the Judge sees them. Net savings ≈ half an audit cycle per phase.

### Risk grade rationale

L2 retained: feature phase touches AI-governance metadata + skill-prose surfaces; not L3 because no auth/credentials/cryptographic code is modified.

---

_Audit complete. Verdict binding. Governor: proceed to `/qor-implement`._
