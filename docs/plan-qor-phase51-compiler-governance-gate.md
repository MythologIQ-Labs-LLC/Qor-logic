# Plan: Phase 51 — Prompt compiler governance gate

**change_class**: feature

**doc_tier**: system

**originating_remediation**: GH #39 sub-phase 2 (per docs/roadmap-prompt-compiler.md)

**terms_introduced**:
- term: GovernanceGate
  home: qor/compiler/governance/gate.py
- term: GovernanceDecision
  home: qor/compiler/governance/decisions.py
- term: Policy
  home: qor/compiler/governance/policies.py
- term: GovernanceViolation
  home: qor/compiler/governance/gate.py

**boundaries**:
- limitations:
  - V1 ships 4 deterministic policies: denied-tool detection, output-format whitelist, sensitive-data hint, prompt-injection hint. Inference-assisted triage deferred to V2+.
  - Risk levels are `low | medium | high | blocked`; `unknown` (Phase 50 default) is now produced only when the gate has not run.
  - Gate runs before provider compile; non-blocked decisions proceed; blocked decisions raise `GovernanceViolation`.
  - V1 policies are inline-constant; configurable policy registry deferred to a later phase.
- non_goals:
  - Live policy editing or per-tenant policy injection.
  - Network calls. Gate is pure-Python deterministic.
- exclusions:
  - No CLI changes.
  - No `compile_prompt` signature changes; gate runs internally before provider dispatch.

## Open Questions

None at submission.

## Phase 1: governance package + types

### Affected Files
- `qor/compiler/governance/__init__.py` — NEW.
- `qor/compiler/governance/decisions.py` — NEW. `GovernanceDecision` frozen dataclass.
- `qor/compiler/governance/policies.py` — NEW. 4 policy functions + `RISK_LEVELS` tuple.
- `qor/compiler/governance/gate.py` — NEW. `GovernanceGate.evaluate(prompt_ir) -> GovernanceDecision`; `GovernanceViolation` exception.
- `tests/test_compiler_governance_types.py` — NEW.
- `tests/test_compiler_governance_policies.py` — NEW.

### Changes
`GovernanceDecision` carries `allowed: bool`, `risk_level: str`, `violations: tuple`, `warnings: tuple`, `required_controls: tuple`, `evidence: tuple`. Frozen.

4 policies:
1. `policy_denied_tools(ir) -> warnings/violations` — flag any allowed tool also in `denied`.
2. `policy_output_format(ir) -> violations` — reject formats not in `{markdown, json, text}`.
3. `policy_sensitive_data_hint(ir) -> warnings` — scan `user_goal` for tokens like "ssn", "credit card", "api key".
4. `policy_prompt_injection_hint(ir) -> warnings` — scan for prefix patterns "ignore previous", "disregard above".

`risk_level` aggregation: `blocked` if any violation; else `high` if 2+ warnings; else `medium` if 1 warning; else `low`.

### Unit Tests
- `test_governance_decision_is_frozen`
- `test_decision_default_allowed_true_risk_low`
- `test_decision_blocked_when_violations_present`
- `test_decision_risk_level_aggregation_with_two_warnings_is_high`
- `test_policy_denied_tools_flags_intersection`
- `test_policy_output_format_rejects_unknown`
- `test_policy_output_format_accepts_markdown_json_text`
- `test_policy_sensitive_data_hint_warns_on_keywords`
- `test_policy_prompt_injection_hint_warns_on_known_prefixes`

## Phase 2: gate wiring + compile_prompt integration

### Affected Files
- `qor/compiler/governance/gate.py` — `GovernanceGate.evaluate(prompt_ir)`.
- `qor/compiler/compile.py` — invoke gate before provider compile; raise `GovernanceViolation` when `allowed=False`; populate `prompt_ir.governance_contract` from decision before passing to compiler.
- `qor/compiler/__init__.py` — re-export `GovernanceGate`, `GovernanceDecision`, `GovernanceViolation`.
- `tests/test_compiler_governance_gate.py` — NEW.
- `tests/test_compile_prompt_governance_integration.py` — NEW.

### Changes
`compile_prompt` now constructs initial PromptIR, evaluates gate, replaces `governance_contract` with one derived from the decision (`risk_level`, `required_controls`), and either raises `GovernanceViolation` or proceeds.

### Unit Tests
- `test_gate_evaluate_returns_decision_for_clean_ir`
- `test_gate_evaluate_blocks_on_denied_tool_in_allowed_list`
- `test_gate_evaluate_warns_on_sensitive_keyword_user_goal`
- `test_gate_combines_multiple_warnings_into_higher_risk_level`
- `test_compile_prompt_raises_governance_violation_on_blocked_decision`
- `test_compile_prompt_proceeds_with_populated_governance_contract`
- `test_compile_prompt_governance_annotation_reflects_gate_risk_level`

## Phase 3: doctrine + roadmap update

### Affected Files
- `qor/references/doctrine-prompt-compilation.md` — extend §V1 scope → mark Phase 51 delivered; document GovernanceGate.
- `docs/roadmap-prompt-compiler.md` — mark Phase 51 row done with sealing version.
- `tests/test_roadmap_phase_51_marked_done.py` — NEW.

### Unit Tests
- `test_roadmap_phase_51_marked_with_v0_51_0`
- `test_doctrine_documents_governance_gate_and_violation`

## CI Commands
- `python -m pytest tests/test_compiler_governance_types.py tests/test_compiler_governance_policies.py -v`
- `python -m pytest tests/test_compiler_governance_gate.py tests/test_compile_prompt_governance_integration.py -v`
- `python -m pytest tests/test_roadmap_phase_51_marked_done.py -v`
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py`
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase51-compiler-governance-gate.md`
- `python -m qor.scripts.pipeline_inversion_lint --repo-root qor/compiler/`
