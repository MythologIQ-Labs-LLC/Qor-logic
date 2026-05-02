# Plan: Phase 59 — `/qor-ideate` ideation readiness phase (Issue #20)

**change_class**: feature

**doc_tier**: system

**terms_introduced**:
- term: ideation phase
  home: qor/references/doctrine-ideation-readiness.md
- term: spark record
  home: qor/references/doctrine-ideation-readiness.md
- term: problem frame
  home: qor/references/doctrine-ideation-readiness.md
- term: transformation statement
  home: qor/references/doctrine-ideation-readiness.md
- term: assumption ledger
  home: qor/references/doctrine-ideation-readiness.md
- term: ideation readiness
  home: qor/references/doctrine-ideation-readiness.md

**boundaries**:
- limitations:
  - Ideation outputs (spark, problem frame, transformation statement) are operator-authored prose; the skill structures the dialogue and validates artifact shape but does not generate the content. Phase 59 ships the skill + schema + doctrine; downstream model-assisted authoring is out of scope.
  - Readiness scoring is rule-based (boolean fields per Issue #20 §"Proposed Readiness Scoring"), not probabilistic. A concept either declares the field or it does not.
  - Phase 59 does NOT modify existing `qor-research` or `qor-plan` skills' input contracts. `qor-research` and `qor-plan` remain runnable without an ideation artifact (advisory gate only) — matches Phase 8 advisory-gate posture.
  - The 10-section ideation artifact (Issue #20 §"Proposed Ideation Artifact Sections") is the doctrine target, but Phase 59 ships only the structural fields; the dialogue prose generation is operator-driven via the skill body.
- non_goals:
  - Mandatory blocking of `qor-plan` without an ideation artifact. Phase 59 ships advisory-gate posture; mandatory blocking is a future phase decision per Issue #20 Open Question 1.
  - Hotfix-bypass enforcement. Phase 59 allows hotfixes to skip ideation per Issue #20 Open Question 2; the override is logged as `gate_override` event in the Process Shadow Genome (existing Phase 8 mechanism).
  - Auto-generation of ideation prose by an LLM. Skill prompts the operator; operator authors.
  - Migration of existing plans to retroactive ideation artifacts. Forward-only enforcement starting Phase 59.
- exclusions:
  - Modifying `qor-remediate` to consume the ideation artifact when repeated failures suggest the original concept was malformed (Issue #20 Open Question 6). Out of scope; future phase.
  - Embedding remediation routes in BOTH ideation and plan artifacts vs. inheriting (Issue #20 Open Question 5). Phase 59: routes live in the ideation artifact only; `qor-plan` reads them via prior-artifact lookup.
  - Adding readiness-blocking semantics to `qor-substantiate`. Phase 59: substantiate does not check ideation. Future phase decision.

## Sprint context

Issue #20 was filed as a "future concept" describing a governed ideation readiness phase that sits before research and planning. Phase 59 makes ideation a first-class, auditable phase in the SDLC chain so that early intent is captured, challenged, bounded, and routed before it becomes a plan. Closes the gap where downstream agents and workflows infer missing intent from ambiguous concepts.

This is **not** part of the five-phase compliance sprint (which closed at Phase 56 v0.42.0). Phase 59 is the next concept-to-code work, prompted by Issue #20.

The skill and schema integrate with existing Phase 8 advisory-gate mechanism: `/qor-research` and `/qor-plan` already check for prior-phase artifacts; Phase 59 adds `ideation` as an optional predecessor.

## Open Questions

1. **Mandatory vs. advisory**: should `/qor-ideate` be mandatory before all `change_class: feature | breaking` plans, or advisory? Default: **advisory** (matches Phase 8 posture; hotfix exemption documented; future phase can tighten to mandatory).
2. **Readiness fields stored in artifact or computed at lookup?**: the 15 boolean fields per Issue #20 §"Proposed Readiness Scoring" — store as written values OR compute from artifact-shape inspection? Default: **store as written values** — operator declares readiness; the schema validates shape; computation-from-shape is a future tightening.
3. **Skill placement**: `qor/skills/sdlc/qor-ideate/` (alongside research/plan/implement) or `qor/skills/governance/qor-ideate/` (alongside audit/substantiate)? Default: **`qor/skills/sdlc/`** — ideation precedes planning in the SDLC sequence; sdlc placement matches.

Defaults will be encoded unless overridden during audit.

## Phase 1: ideation gate-artifact schema + readiness model

### Affected Files

- `tests/test_ideation_schema_validation.py` — NEW: locks the JSON schema shape for ideation gate artifacts; validates required fields, readiness enum, optional sections.
- `tests/test_ideation_schema_round_trip.py` — NEW: locks round-trip integrity — every section in the doctrine corresponds to a schema field, and vice versa.
- `qor/gates/schema/ideation.schema.json` — NEW: JSON schema for `phase: ideation` gate artifacts. Required top-level: `phase`, `ts`, `session_id`, `concept_name`, `spark`, `problem_frame`, `transformation_statement`, `boundaries`, `governance_profile`, `readiness`, `ai_provenance`. Optional: `assumptions`, `options`, `failure_remediation`. Schema mirrors Issue #20 §"Proposed Gate Artifact Shape" with these refinements: `readiness.status` enum is `["ready", "blocked", "research_required", "planning_advisory_only"]`; `governance_profile.risk_grade` enum is `["L1", "L2", "L3", "L4"]` (matches existing audit-schema risk grades); `failure_remediation[].return_phase` enum is `["ideation", "research", "plan", "audit", "implement", "remediate", "substantiate"]`.
- `qor/scripts/validate_gate_artifact.py` — UPDATE: extend `PHASES` constant tuple with `"ideation"`. The existing per-phase schema-load mechanism picks up the new schema file automatically.

### Changes

The schema is the canonical structural contract for an ideation artifact. The 10-section ideation artifact described in Issue #20 maps to schema fields as follows: §1 Spark Record → `spark`; §2 Problem Frame → `problem_frame`; §3 Transformation Statement → `transformation_statement`; §4 Assumption Ledger → `assumptions[]`; §5 Scope Boundary Record → `boundaries`; §6 Concept Brief → `concept_name` + `transformation_statement`; §7 Options Matrix → `options[]`; §8 User/System Story Map → optional, deferred to future phase; §9 Governance Profile → `governance_profile`; §10 Failure Remediation Plan → `failure_remediation[]`.

The `readiness` field stores the 15 boolean fields per Issue #20 §"Proposed Readiness Scoring" as written values (per Open Question 2 default). Schema does not enforce that each boolean be `true`; that's the operator's decision. The `readiness.status` enum encodes the routing decision (`ready` → proceed to research/plan; `blocked` → remain in ideation; `research_required` → route to research first; `planning_advisory_only` → allow prototype planning, block production implementation).

`validate_gate_artifact.PHASES` extension matches the Phase 55 pattern (`"deliver"` was added there). Ideation artifacts validate against `qor/gates/schema/ideation.schema.json` exactly like every other phase.

### Unit Tests

- `tests/test_ideation_schema_validation.py`:
  - `test_validates_minimal_ideation_artifact` — fixture with all required fields present (minimal valid shape); assert validation passes.
  - `test_rejects_artifact_missing_spark` — fixture without `spark` field; assert `jsonschema.ValidationError` raised.
  - `test_rejects_artifact_missing_problem_frame` — analogous for `problem_frame`.
  - `test_rejects_artifact_missing_transformation_statement` — analogous.
  - `test_rejects_artifact_missing_boundaries` — analogous.
  - `test_rejects_artifact_missing_governance_profile` — analogous.
  - `test_rejects_artifact_missing_readiness` — analogous.
  - `test_readiness_status_enum_rejects_unknown_value` — fixture with `readiness.status = "definitely_ready"`; assert ValidationError.
  - `test_governance_profile_risk_grade_enum_rejects_L5` — analogous for risk_grade.
  - `test_failure_remediation_return_phase_enum_rejects_unknown` — analogous for return_phase.
  - `test_assumptions_optional_when_readiness_status_is_research_required` — fixture without `assumptions`; assert valid (assumptions are optional per schema).
  - `test_validate_gate_artifact_recognizes_ideation_phase` — invokes `validate_gate_artifact.validate(artifact_path)`; assert it routes to `ideation.schema.json` and not to a default/legacy validator.
- `tests/test_ideation_schema_round_trip.py`:
  - `test_every_doctrine_section_has_corresponding_schema_field` — Phase 50 round-trip integrity. Reads `qor/references/doctrine-ideation-readiness.md`; extracts top-level `## ` sections that are NOT meta-headers (Applicability, References, etc.); asserts each maps to a schema field per a doctrine-declared mapping table.
  - `test_every_required_schema_field_appears_in_doctrine_body` — inverse direction: schema-declared required fields each appear at least once in doctrine prose.

## Phase 2: `/qor-ideate` skill + dialogue protocol + gate-chain integration

### Affected Files

- `tests/test_qor_ideate_skill_admission.py` — NEW: locks skill registration (Phase 55 admission) — `qor-ideate` admitted with `permitted_tools: [Read, Grep, Glob, Bash]` and `permitted_subagents: [Explore, general-purpose]`.
- `tests/test_qor_ideate_writes_gate_artifact.py` — NEW: end-to-end fixture verifying that running the skill prompts ➝ collects ➝ writes a valid `ideation.json` gate artifact passing schema validation.
- `tests/test_qor_ideate_handoff_matrix.py` — NEW: locks handoffs — `qor-ideate -> qor-research, qor-plan` (the two downstream phases per Issue #20). Updated `qor/gates/delegation-table.md` reflects the handoff.
- `tests/test_qor_research_reads_ideation_artifact.py` — NEW: regression — `/qor-research` Step 0 advisory check now ALSO recognizes ideation as a valid prior phase (per Phase 8 advisory-gate posture). Conditional rule: when ideation.json exists for the session, `check_prior_artifact("research")` returns `found=True, prior_phase_used="ideation"`.
- `tests/test_qor_plan_reads_ideation_artifact.py` — NEW: analogous — `/qor-plan` Step 0 advisory check recognizes either research OR ideation as a valid prior phase.
- `qor/skills/sdlc/qor-ideate/SKILL.md` — NEW: ~280 LOC. Frontmatter declares `phase: ideation`, `gate_writes: ideation`, `gate_reads: ""` (chain-start), `permitted_tools`, `permitted_subagents`, `model_compatibility: [claude-opus-4-7, claude-sonnet-4-6]`, `min_model_capability: sonnet`. Body: identity activation (Analyst persona), 10-step ideation dialogue protocol corresponding to the 10 ideation-artifact sections, readiness-scoring step, gate-chain write step, handoff to research/plan.
- `qor/skills/sdlc/qor-ideate/references/dialogue-protocol.md` — NEW: ~150 LOC. Operator-facing prompts for each of the 10 sections; prompts are MULTIPLE-CHOICE where possible per `qor-plan` collaborative-design-dialogue pattern. Example prompts: "What sparked this concept?" → multi-line text; "Risk grade?" → choice (L1/L2/L3/L4); "Recommended next phase?" → choice (research/plan/hold).
- `qor/gates/delegation-table.md` — UPDATE: add row `qor-ideate -> qor-research, qor-plan`.
- `qor/gates/chain.md` — UPDATE: extend the chain visualization to position `ideate` BEFORE `research` (advisory; chain-start may be either ideate or research).
- `qor/scripts/session.py` — VERIFY (no change expected): session module already supports arbitrary phase names via `gate_chain.write_gate_artifact`; ideation phase fits without modification.
- `qor/dist/manifest.json` + `qor/dist/variants/*/` — REGENERATE via `qor.scripts.dist_compile` post-skill-add (existing post-write workflow).

### Changes

The skill's 10-step dialogue mirrors Issue #20's 10 sections. Each step ends with a structural validation (does the operator's response yield a schema-valid value for the corresponding field?). The skill aborts if the operator declares `readiness.status: blocked` and offers to remain in ideation.

The skill writes the gate artifact via `gate_chain.write_gate_artifact("ideation", payload)`. With Phase 52 provenance binding, the skill must run with `QOR_SKILL_ACTIVE=ideation` env set (existing pattern; no change to `gate_chain`).

Downstream phases `/qor-research` and `/qor-plan` already use `gate_chain.check_prior_artifact(<current_phase>, session_id=sid)` at Step 0. Phase 59 extends `check_prior_artifact` to accept ideation as a valid prior phase (current implementation uses a phase ordering tuple; extend it).

Per Open Question 1 default (advisory): `qor-research`/`qor-plan` do NOT abort if ideation is missing. They proceed but log a Process Shadow Genome `gate_override` event with `severity: 1, reason: "ideation phase skipped"`. This matches Phase 8 advisory-gate semantics exactly.

Per Open Question 2 default (hotfix exemption): the skill body documents that `change_class: hotfix` plans MAY skip `/qor-ideate`. The operator declares this in the plan frontmatter (existing `change_class:` field in `plan.schema.json`); no schema change required.

### Unit Tests

- `tests/test_qor_ideate_skill_admission.py`:
  - `test_qor_ideate_skill_passes_admission_check` — invokes `qor.reliability.skill_admission.check_admission("qor-ideate")`; asserts admitted with no tool-scope or subagent-scope violations.
  - `test_qor_ideate_skill_frontmatter_declares_required_fields` — reads SKILL.md frontmatter; asserts `phase: ideation`, `gate_writes: ideation`, `permitted_tools` non-empty list.
- `tests/test_qor_ideate_writes_gate_artifact.py`:
  - `test_skill_completes_writes_valid_ideation_json` — fixture: simulate a complete operator dialogue (mock responses for all 10 steps); invoke skill end-to-end; assert `.qor/gates/<sid>/ideation.json` exists AND validates against `ideation.schema.json`.
  - `test_skill_writes_ai_provenance_field` — asserts written artifact has `ai_provenance.system: "Qor-logic"`.
- `tests/test_qor_ideate_handoff_matrix.py`:
  - `test_qor_ideate_handoff_targets_research_and_plan` — Phase 50 co-occurrence behavior invariant. Reads `qor/gates/delegation-table.md`; asserts row `qor-ideate -> qor-research, qor-plan` present.
  - `test_qor_ideate_in_gate_skill_matrix_with_zero_broken_handoffs` — invokes `qor.reliability.gate_skill_matrix`; asserts `qor-ideate` listed AND zero broken handoffs.
- `tests/test_qor_research_reads_ideation_artifact.py`:
  - `test_check_prior_artifact_recognizes_ideation_for_research_phase` — fixture: write ideation.json; call `check_prior_artifact("research", session_id=sid)`; assert `result.found is True` AND `result.prior_phase_used == "ideation"`.
  - `test_check_prior_artifact_falls_back_to_no_prior_phase_when_neither_ideation_nor_research_present` — fixture: no prior artifact; assert `result.found is False`.
- `tests/test_qor_plan_reads_ideation_artifact.py`:
  - `test_check_prior_artifact_recognizes_ideation_OR_research_for_plan_phase` — fixture: write only ideation.json (no research.json); call `check_prior_artifact("plan", session_id=sid)`; assert `found=True, prior_phase_used="ideation"`.
  - `test_check_prior_artifact_prefers_research_when_both_ideation_and_research_present` — fixture: both written; assert `prior_phase_used == "research"` (closer in chain).

## Phase 3: doctrine + glossary + self-application + skill-registry rollup

### Affected Files

- `tests/test_doctrine_ideation_readiness_anchored.py` — NEW: heading-tree round-trip integrity for the new doctrine.
- `tests/test_phase59_self_application.py` — NEW: 5 self-application tests verifying Phase 59 plan + ledger + skill behavior end-to-end, INCLUDING the meta-coherence test that the Phase 59 plan ITSELF could have been authored as a Phase-58 ideation artifact (worked example).
- `tests/test_skill_registry_includes_qor_ideate.py` — NEW: regression — `qor.reliability.gate_skill_matrix` enumerates `qor-ideate`; Phase 55 admission accepts it; dist variants compile.
- `qor/references/doctrine-ideation-readiness.md` — NEW: ~200 LOC. Sections: `## Applicability`, `## The 10 ideation artifact sections` (one subsection per section, with prose explaining the WHY), `## Readiness scoring model`, `## Routing decision matrix` (readiness.status → next phase), `## Failure-mode catalog` (premature solutioning, language drift, assumption laundering, scope seepage, research asymmetry, failure blindness, premature decomposition, validation collapse — each with detection signals and countermeasures, mirrors Issue #20 §"Natural Unraveling Points to Guard Against"), `## Hotfix exemption`, `## Relationship to qor-research and qor-plan`, `## References`.
- `qor/references/glossary.md` — APPEND 6 new terms: `ideation phase`, `spark record`, `problem frame`, `transformation statement`, `assumption ledger`, `ideation readiness`.
- `qor/references/doctrine-shadow-genome-countermeasures.md` — APPEND new SG entry `SG-PrematureSolutioning-A` codifying the failure pattern from Issue #20 §"Premature Solutioning" + Phase 59 countermeasure (the 10-section dialogue forces problem-frame BEFORE concept-brief).
- `CHANGELOG.md` — APPEND `[0.43.0]` entry summarizing Phase 59 (assumes Phase 57 ships at v0.43.0; Phase 59 ships at v0.44.0 OR ships as a co-bundled v0.43.0 if Phase 57+58 land together).

### Changes

The doctrine codifies the conceptual model behind the skill: ideation is the phase where intent is captured before research, where assumptions are flagged before they become hidden requirements, and where remediation routes are defined before failure occurs. The 10 sections are not bureaucratic checkboxes — they are the specific failure-mode catalog from Issue #20 §"Natural Unraveling Points to Guard Against".

`SG-PrematureSolutioning-A` is the canonical SG entry. Future phases that hit premature-solutioning failure can cite it.

The Phase 59 plan is meta-coherent: it could itself have been authored as an ideation artifact. Test `test_phase59_self_application` includes a worked-example assertion that the plan's `## Sprint context`, `## Open Questions`, and `boundaries` block correspond to ideation `spark`, `assumption_ledger` items, and `boundaries` field values respectively. Phase 59 dogfoods its own structure.

### Unit Tests

- `tests/test_doctrine_ideation_readiness_anchored.py`:
  - `test_doctrine_declares_all_10_section_subsections` — heading-tree integrity: 10 subsections under `## The 10 ideation artifact sections`, each with non-empty body; section names match Issue #20 §"Proposed Ideation Artifact Sections" 1-10.
  - `test_doctrine_routing_decision_matrix_lists_all_readiness_status_values` — round-trip: every value in the schema's `readiness.status` enum appears in the Routing Decision Matrix section.
  - `test_doctrine_failure_mode_catalog_lists_8_canonical_unraveling_points` — Issue #20 §"Natural Unraveling Points" enumerates 8 named patterns; doctrine catalog must list all 8.
- `tests/test_phase59_self_application.py`:
  - `test_phase59_implement_gate_carries_ai_provenance` — reads implement.json; asserts `ai_provenance.human_oversight: absent`.
  - `test_secret_scanner_clean_against_phase59_plan_and_doctrine` — invokes scanner with `mask_blocks=True` against plan + doctrine; asserts empty findings.
  - `test_pre_audit_lints_clean_against_phase59_plan` — Phase 55 lints clean.
  - `test_glossary_round_trips_against_phase59_terms` — all 6 new terms have entries with `home: qor/references/doctrine-ideation-readiness.md` and `introduced_in_plan: phase59-ideation-readiness-phase`.
  - `test_phase59_plan_could_be_an_ideation_artifact` — meta-coherence: the plan's `## Sprint context` paragraph, `## Open Questions` list, and `boundaries` block can be parsed into a structurally-valid `ideation.json` artifact via a transformation script. Asserts the resulting artifact validates against the schema.
- `tests/test_skill_registry_includes_qor_ideate.py`:
  - `test_qor_ideate_listed_by_gate_skill_matrix` — invokes matrix runner; asserts `qor-ideate` in the skill list.
  - `test_dist_variants_include_qor_ideate_skill_dir` — invokes `dist_compile` against tmp_path; asserts each variant directory contains `skills/qor-ideate/SKILL.md`.

## CI Commands

- `python -m pytest tests/test_ideation_schema_validation.py tests/test_ideation_schema_round_trip.py -v` — Phase 1 lock.
- `python -m pytest tests/test_qor_ideate_skill_admission.py tests/test_qor_ideate_writes_gate_artifact.py tests/test_qor_ideate_handoff_matrix.py tests/test_qor_research_reads_ideation_artifact.py tests/test_qor_plan_reads_ideation_artifact.py -v` — Phase 2 lock.
- `python -m pytest tests/test_doctrine_ideation_readiness_anchored.py tests/test_phase59_self_application.py tests/test_skill_registry_includes_qor_ideate.py -v` — Phase 3 lock.
- `python -m pytest -x` — full suite; expect 1141 + Phase 57 (~22) + Phase 59 (~26) = ~1189 passing twice (deterministic).
- `python -m qor.scripts.prompt_injection_canaries --mask-code-blocks --files docs/plan-qor-phase59-ideation-readiness-phase.md qor/references/doctrine-ideation-readiness.md` — Phase 53 self-application.
- `python -m qor.scripts.plan_test_lint --plan docs/plan-qor-phase59-ideation-readiness-phase.md` — Phase 55 self-application.
- `python -m qor.scripts.plan_grep_lint --plan docs/plan-qor-phase59-ideation-readiness-phase.md --repo-root .` — Phase 55 self-application.
- `python -m qor.scripts.secret_scanner --mask-blocks --files docs/plan-qor-phase59-ideation-readiness-phase.md qor/references/doctrine-ideation-readiness.md` — Phase 56 self-application.
- `python -m qor.reliability.skill_admission qor-ideate` — admit new skill.
- `python -m qor.reliability.gate_skill_matrix` — verify 30 skills, +1 handoff (qor-ideate → research, plan), 0 broken.
- `python -m qor.scripts.dist_compile` — emit variants with new skill.
- `python -m qor.scripts.check_variant_drift` — dist parity.
- `python -m qor.scripts.badge_currency --repo-root . --ledger docs/META_LEDGER.md` — badges current (Tests delta, Doctrines +1, Ledger +N).
- After Phase 59 seal: `gh issue close 20 --comment "Resolved by Phase 59 — see commit <sha> on main + docs/plan-qor-phase59-ideation-readiness-phase.md + qor/references/doctrine-ideation-readiness.md"`.
