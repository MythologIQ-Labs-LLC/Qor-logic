# Plan: Phase 68 - qor-audit self-application sub-pass + Option B adversarial codification

**change_class**: hotfix

**doc_tier**: standard

**originating_remediation**: GH #44 (qor-audit should self-apply plan-introduced discipline) and GH #50 (qor-audit independent adversarial reviewer not codified in skill prompt -- Option B is operational only).

**terms_introduced**: none. Both fixes operate on existing surfaces.

**boundaries**:
- limitations:
  - V1 self-application sub-pass relies on plan declaring `originating_remediation` field. Plans without the field bypass the sub-pass; no inference from prose.
  - V1 Option B codification is prose-only: the skill prompt names the pattern, decision criteria, and operator dispatch protocol, but does not auto-dispatch independent reviewers from within the skill.
- non_goals:
  - Auto-discovering whether a plan introduces a discipline that should self-apply (the operator declares this via the field; auditor obeys).
  - Auto-spawning independent-reviewer subagents from within qor-audit (Option B remains an operator-mediated dispatch).
- exclusions:
  - No changes to qor-implement or qor-substantiate.
  - No CLI changes.

## Open Questions

None. Both issues specify exact placement and behavior.

## Phase 1: plan.schema.json declares `originating_remediation`

### Affected Files

- `tests/test_plan_schema_originating_remediation.py` - NEW. 3 tests asserting the schema accepts the field with the expected pattern, accepts null, and accepts absence (backward compat).
- `qor/gates/schema/plan.schema.json` - extend with optional `originating_remediation` field accepting a free-form string (typically `GH #N`, `SG-Foo-A`, or a free-text remediation reference) or null.

### Changes

Field declaration only; no validation tightening. Existing plans without the field continue to validate. The downstream consumer of the field is qor-audit Step 3.5 (Phase 2 of this plan); other phases ignore it.

### Unit Tests

- `tests/test_plan_schema_originating_remediation.py::test_schema_accepts_originating_remediation_string` - constructs a minimal plan payload with `originating_remediation: "GH #44"`, validates against schema, asserts no errors.
- `tests/test_plan_schema_originating_remediation.py::test_schema_accepts_originating_remediation_null` - same with `null`; asserts validates.
- `tests/test_plan_schema_originating_remediation.py::test_schema_accepts_plan_without_originating_remediation` - omits field entirely; asserts validates (backward compat with pre-Phase-68 plans).

## Phase 2: qor-audit Step 3.5 Self-Application Sub-Pass (GH #44)

### Affected Files

- `tests/test_qor_audit_self_application_pass.py` - NEW. 3 tests asserting the prose names the sub-pass and the helper-or-condition logic.
- `qor/skills/governance/qor-audit/SKILL.md` - new Step 3.5 between Section 4 Razor Pass and Test Functionality Pass in Step 3 body. Body:
  - States the rule: when `plan_artifact.originating_remediation` is set, the auditor manually performs the discipline the plan introduces, against the plan itself.
  - References the originating pattern: SG-007 (self-audit verification scope bias) and the COREFORGE 3-VETO meta-recurrence (plan that introduces a lint exhibits the very pattern its lint targets).
  - Describes dispatch: the auditor reads the plan's `originating_remediation` field via `gate_chain.read_phase_artifact("plan", session_id=sid).get("originating_remediation")`, then applies the named discipline (search for issue body wording, grep the plan for matching patterns, or otherwise enact the discipline) against the plan content.
  - VETO category: `specification-drift` when self-application detects the targeted pattern in the plan itself.

### Changes

Pure skill-prose addition. The audit logic is operator-mediated: the LLM running the skill reads the plan's declared remediation, fetches the corresponding discipline description (from the issue body referenced or from the operator), and applies it against the plan text. No new helper code in this phase; the discipline-application path is per-issue and lives in the issue body, not in qor-logic source.

### Unit Tests

- `tests/test_qor_audit_self_application_pass.py::test_skill_prose_declares_self_application_subpass` - reads qor-audit SKILL.md, locates Step 3 body, asserts a sub-section names the self-application sub-pass and references `originating_remediation`.
- `tests/test_qor_audit_self_application_pass.py::test_skill_prose_cites_originating_pattern` - asserts the sub-pass prose cites SG-007 or names "self-audit verification scope bias" / "author-audit momentum".
- `tests/test_qor_audit_self_application_pass.py::test_skill_prose_names_veto_category` - asserts the sub-pass prose names `specification-drift` as the VETO category when self-application detects the pattern (matches existing findings_categories enum).

## Phase 3: qor-audit Step 1.a Option B independent reviewer codification (GH #50)

### Affected Files

- `tests/test_qor_audit_option_b_codification.py` - NEW. 3 tests asserting the prose names Option B, the SG-007 origin, and the operator-dispatch protocol.
- `qor/skills/governance/qor-audit/SKILL.md` - extend the existing Step 1.a (Adversarial mode check) with explicit Option A / Option B framing:
  - **Option A** (existing): Codex plugin available -> delegate counter-argument pass to Codex.
  - **Option B** (Phase 68 codification): independent reviewer pattern. When the auditor was also the plan's author (common in single-LLM operation), the audit inherits the author's search-path momentum (SG-007). Codification states the dispatch protocol: the operator MAY request a fresh-context audit by re-running the skill from a new session (clearing author-context), invoking an architect-reviewer subagent for the audit pass, or asking a second operator to run the audit.

### Changes

The existing Step 1.a block runs `runtime.should_run_adversarial_mode()` which checks for Codex plugin and logs a `capability_shortfall` event when absent. Phase 68 extends the prose to formalize Option B as the documented fallback (and explicit choice) when Option A is unavailable. No new code; the operator-mediated dispatch is the change.

### Unit Tests

- `tests/test_qor_audit_option_b_codification.py::test_skill_prose_names_option_b_independent_reviewer` - reads qor-audit SKILL.md, locates Step 1.a, asserts "Option B" appears alongside the existing Option A flow.
- `tests/test_qor_audit_option_b_codification.py::test_skill_prose_cites_sg_007_origin` - asserts the Option B prose cites SG-007 or "self-audit verification scope bias" as the originating pattern.
- `tests/test_qor_audit_option_b_codification.py::test_skill_prose_names_dispatch_protocol_options` - asserts the Option B prose enumerates at least two of: fresh-context audit (new session), architect-reviewer subagent, second operator.

## Phase 4: Documentation refresh

### Affected Files

- `docs/SYSTEM_STATE.md` - prepend Phase 68 entry.
- `CHANGELOG.md` - stamp Phase 68 0.47.2 section at substantiate time.
- `README.md` - badge currency updates at substantiate time (ledger 202).
- `qor/references/doctrine-shadow-genome-countermeasures.md` - SG-AuthorAuditMomentum-A entry promoted from SG-007 narrative reference.

### Changes

Mechanical. SG-AuthorAuditMomentum-A formalizes the long-standing SG-007 pattern in the structured countermeasures catalog now that Phase 68 wires the framework countermeasure.

### Unit Tests

None for Phase 4. Existing badge currency + procedural fidelity + SYSTEM_STATE coverage tests are the structural enforcement.

## CI Commands

- `python -m pytest tests/test_plan_schema_originating_remediation.py tests/test_qor_audit_self_application_pass.py tests/test_qor_audit_option_b_codification.py -v` - validates Phase 68 tests.
- `python -m qor.scripts.dist_compile` - regenerates dist variants for skill prose changes.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase68-audit-self-application-and-adversarial-codification.md` - self-application: lint this plan with the Phase 67 newly-wired discipline.
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py` - full suite.
