# Plan: Phase 54 — AI provenance metadata + EU AI Act/AI RMF doctrine + subagent scaffolding + override-friction escalator

**change_class**: feature

**doc_tier**: standard

**terms_introduced**:
- term: AI provenance manifest
  home: qor/references/doctrine-eu-ai-act.md
- term: human-oversight signal
  home: qor/references/doctrine-eu-ai-act.md
- term: subagent tool scope
  home: qor/references/doctrine-ai-rmf.md
- term: override-friction escalator
  home: qor/references/doctrine-ai-rmf.md

**boundaries**:
- limitations:
  - AI provenance metadata is descriptive (records that a Qor-logic AI system produced the artifact); it is not a cryptographic signature. Tampering with the manifest after seal is detected only by the existing Merkle chain, not by the manifest itself.
  - Subagent `permitted_tools` frontmatter is advisory in this phase (declared in skill YAML; not yet enforced by the harness). Phase 55 will add Cedar-based admission enforcement.
  - Override-friction escalator triggers on count, not on classification of the override. An operator overriding 4 gate-checks in a row gets the same friction as one overriding 4 different gate types.
- non_goals:
  - Model pinning per skill (`model_compatibility:` frontmatter). Phase 55.
  - SBOM emission. Phase 55.
  - Secret-scanning gate at substantiate. Phase 56.
  - Cedar-based subagent admission enforcement. Phase 55.
  - Cryptographic signing of AI provenance manifests. Out of scope; Merkle chain provides integrity.
- exclusions:
  - Retroactive provenance backfill on entries < #175. Forward-only by design (immutable Merkle chain).
  - Operator-facing UI changes to the override prompt. Friction lives in skill prose / shadow event payloads, not new UI.

## Sprint context

Phase 54 of the five-phase compliance sprint started at Phase 53. Bundles Priorities 2, 4, and 5 from `docs/research-brief-prompt-logic-frameworks-2026-04-30.md` Recommendations into one feature phase to reduce ceremony cost. Sprint state after Phase 54:

| Phase | Scope | Status |
|---|---|---|
| 53 | LLM01 prompt-injection defense; OWASP LOW-4; DRIFT-1/2 path canonicalization | **Sealed** v0.39.0 |
| **54 (this plan)** | AI provenance in 6 gate schemas; EU AI Act + AI RMF doctrines; plan-template impact-assessment optional section; subagent tool-scope advisory frontmatter; override-friction escalator | drafting |
| 55 | Model-pinning frontmatter + Cedar-enforced subagent admission + SBOM | queued |
| 56 | Secret-scanning gate at `/qor-substantiate` Step 4 | queued |

## Open Questions

1. **Provenance schema location**: should `ai_provenance` be (a) a single new top-level field added to each of the 6 gate schemas, (b) an external `qor/gates/schema/_provenance.schema.json` that all 6 reference via `$ref`, or (c) a separate sidecar file `.qor/gates/<sid>/<phase>.provenance.json`? Default: **(b)** — single source of truth via `$ref`, no payload bloat in each schema, consistent with how the closed-enum `findings_categories` is locally embedded but logically shared.
2. **Override-friction trigger threshold**: at what count does the escalator engage? (a) 3 (matches the cycle-count escalator's same-signature-VETO threshold), (b) 5 (one per workflow phase: research/plan/audit/implement/substantiate), (c) operator-configurable via env var. Default: **(a)** 3 — symmetric with existing cycle-count escalator; familiar threshold from `qor/scripts/cycle_count_escalator.py`; a single tuning value across the override-discipline doctrine.
3. **Friction form**: at threshold, is the friction (a) free-text justification (~50 char min) appended to the override event, (b) a confirmation re-prompt with a 5-second pause and explicit "I have read the override events and accept" string, (c) an automatic invocation of `/qor-remediate` (matching the cycle-count escalator). Default: **(a)** free-text justification — lowest UX cost, highest signal value (operator must articulate WHY); does not require timing-sensitive prose; appendable to the existing `gate_override` shadow event without schema change beyond a `justification:` field.

Defaults will be encoded unless overridden during audit.

## Phase 1: AI provenance metadata in gate schemas + helper module

### Affected Files

- `tests/test_ai_provenance_schema.py` — NEW: locks the new schema's required-field shape and round-trip integrity through the existing `qor.scripts.validate_gate_artifact` infrastructure.
- `tests/test_ai_provenance_helper.py` — NEW: locks `qor.scripts.ai_provenance.build_manifest` behavior — given `phase`, `host`, `model`, `human_oversight`, returns a dict that validates against the schema.
- `qor/gates/schema/_provenance.schema.json` — NEW: declares `ai_provenance` object shape (system, version, host, model_family, human_oversight, ts). Standalone schema referenced by `$ref` from the 6 phase schemas. The `human_oversight` field declares one of: `pass | veto | override | absent` (operator-elected at gate-write time; absent only when the phase has no human-decision gate, e.g. research).
- `qor/gates/schema/{research,plan,audit,implement,substantiate,validate}.schema.json` — AMEND: add optional `ai_provenance` property declaring `{ "$ref": "_provenance.schema.json" }`. Backward-compatible; pre-Phase-54 artifacts with no field still validate.
- `qor/scripts/ai_provenance.py` — NEW: pure-Python helper module (~80 LOC). Public API:
  - `build_manifest(phase: str, *, host: str | None = None, model_family: str | None = None, human_oversight: HumanOversight, system_version: str | None = None) -> dict` — composes a manifest dict matching the schema. Reads `system_version` from `pyproject.toml` if not supplied. When `host` is None, calls `qor.scripts.qor_platform.current()` (the canonical runtime helper at `qor/scripts/qor_platform.py:140`) which returns `dict | None`; caller extracts `state.get("detected", {}).get("host", "unknown")` per the existing `qor-implement` SKILL.md Step 1.a pattern. When `model_family` is None, reads optional `QOR_MODEL_FAMILY` env var (set by harness if available) with `"unknown"` fallback.
  - `HumanOversight` enum: `PASS | VETO | OVERRIDE | ABSENT`.
- `qor/scripts/gate_chain.py` — UPDATE: `write_gate_artifact()` accepts optional `ai_provenance: dict | None = None` kwarg; if supplied, validated against `_provenance.schema.json` and embedded in the payload before validation against the phase schema. No behavior change when omitted (backward compat for non-Phase-54 callers).
- `qor/cli_handlers/__init__.py` — NEW (empty `__init__.py` to make the package importable; ~3 LOC).
- `qor/cli_handlers/compliance.py` — NEW (~110 LOC). Hosts the three `compliance` subcommand handlers: `do_report` (extracted from `qor/cli.py:_do_compliance_report`), `do_ai_provenance` (new — walks `.qor/gates/<sid>/*.json` and emits aggregated JSON manifest for EU AI Act Art. 50 transparency reporting), `do_sprint_progress` (new — Phase 4 deliverable, see below). Also hosts `register(sub)` which adds the `compliance` parser group with all three subcommands. Replaces the in-cli inline registration block at `qor/cli.py:150-160`.
- `qor/cli.py` — REFACTOR: remove inline `_do_compliance_report` (move to `qor/cli_handlers/compliance.py`); remove inline `_register_compliance_policy` body for the compliance side and call `qor.cli_handlers.compliance.register(sub)` instead. Net file change: ~227 LOC → ~190 LOC (handler bodies extracted; thin parser/dispatch retained). Stays well under the 250 cap with headroom for Phase 55+ growth. Closes Pass-1 `razor-overage` finding.
- `qor/skills/sdlc/qor-research/SKILL.md`, `qor/skills/sdlc/qor-plan/SKILL.md`, `qor/skills/governance/qor-audit/SKILL.md`, `qor/skills/sdlc/qor-implement/SKILL.md`, `qor/skills/governance/qor-substantiate/SKILL.md`, `qor/skills/governance/qor-validate/SKILL.md` — APPEND a single line to each Step Z (gate artifact write) instructing the skill to call `ai_provenance.build_manifest(...)` and pass the result into `gate_chain.write_gate_artifact(... ai_provenance=manifest)`. The line is identical across all six skills (delegated to the helper); no per-skill skill-prose drift.
- `tests/test_skill_prose_cites_ai_provenance.py` — NEW: walks the six SDLC + governance skills; asserts each Step Z block invokes `ai_provenance.build_manifest`.

### Changes

The single source of truth for provenance shape is `_provenance.schema.json`; phase schemas reference it via `$ref`. The helper module is what skills actually call; skills do not construct manifests by hand. Helper auto-derives `system_version` from `pyproject.toml` (read via stdlib `tomllib`, Python 3.11+). For `host`: helper calls `qor.scripts.qor_platform.current()` (the existing runtime detector at `qor/scripts/qor_platform.py:140` returning `dict | None`) and extracts via `state.get("detected", {}).get("host", "unknown")` per the existing `qor-implement` SKILL.md Step 1.a pattern. For `model_family`: helper reads optional `QOR_MODEL_FAMILY` env var (set by harness if available); falls back to `"unknown"`. Emits a one-time stderr warning per process when either falls back to `"unknown"` (the warning is suppressible via `QOR_PROVENANCE_QUIET=1` for tests/CI).

CLI subcommand split (Pass-1 razor-overage closure): `qor/cli.py` is at 227 LOC pre-Phase-54; appending two new compliance subcommands plus their handlers would push it past the 250-line cap. The split moves all `compliance` subcommand handlers (existing `report` plus new `ai-provenance` and `sprint-progress`) into `qor/cli_handlers/compliance.py`. `qor/cli.py` retains only parser/dispatcher logic; subcommand registration moves to `qor.cli_handlers.compliance.register(sub)`. Net `qor/cli.py` reduces to ~190 LOC after the extraction, leaving headroom for Phase 55+ subcommand additions without re-hitting the cap.

The `human_oversight` field is the most-important field for EU AI Act Art. 14 compliance: it captures the operator's binary decision at each gate. For research/implement phases (no operator decision), the value is `absent`. For audit, it's `pass | veto`. For substantiate, `pass | veto`. For override events, the original phase records the override flag; the override is also captured as a separate shadow event with its own provenance.

### Unit Tests

- `tests/test_ai_provenance_schema.py`:
  - `test_schema_validates_full_manifest`: feeds a valid manifest dict to `validate_gate_artifact._validate_data` (or its provenance-specific equivalent); asserts no errors. Inverse: `test_schema_rejects_unknown_human_oversight_value`.
  - `test_schema_optional_in_phase_schemas`: validates a phase artifact WITHOUT `ai_provenance`; asserts no errors (backward compat).
  - `test_schema_required_fields`: removes each required field one-at-a-time; asserts validation fails citing the specific field.
- `tests/test_ai_provenance_helper.py`:
  - `test_build_manifest_returns_schema_valid_dict`: invokes `build_manifest("audit", host="claude-code", model_family="claude-opus-4-7", human_oversight=HumanOversight.PASS)`; asserts return validates against schema.
  - `test_build_manifest_reads_system_version_from_pyproject`: invokes without `system_version`; asserts the returned manifest's `system` field matches the `version` declared in `pyproject.toml` (round-trip).
  - `test_build_manifest_rejects_invalid_human_oversight_for_phase`: `build_manifest("research", human_oversight=HumanOversight.PASS)` raises `ValueError` (research has no operator decision; only `ABSENT` is valid). Maps each phase to its valid set.
  - `test_build_manifest_warns_once_on_missing_host`: invokes with `host=None`; asserts manifest carries `host="unknown"` AND a stderr warning is emitted exactly once across N invocations in the same session.
- `tests/test_skill_prose_cites_ai_provenance.py`:
  - `test_skills_writing_gate_artifacts_invoke_build_manifest` — co-occurrence behavior invariant per the canonical Phase 50 model. Walks `qor/skills/**/*.md`. **Conditional rule**: for any SKILL.md whose body invokes `gate_chain.write_gate_artifact(`, assert the same body also invokes `ai_provenance.build_manifest(`. The conditional is what makes this behavior-anchored: the test enumerates skills exhibiting the gate-write behavior, then asserts the provenance-build invariant holds for each. Acceptance question: if any of those skills regressed and stopped calling `build_manifest` (e.g., moved into a comment block while the underlying gate-write behavior remained), would this test fail? YES — the conditional set still contains that skill, the inner assertion fails, the test points at the offending file. Negative-path: synthetic skill fixture invoking `gate_chain.write_gate_artifact` but omitting `ai_provenance.build_manifest`; asserts the lint catches it.
- `tests/test_compliance_ai_provenance_cli.py`:
  - `test_cli_aggregates_session_provenance`: builds 3 fixture gate files in a tmp session dir; invokes the CLI subcommand via subprocess; asserts the emitted JSON aggregates all three with correct ordering.
  - `test_cli_handles_missing_provenance_field`: gate file without `ai_provenance` field; CLI emits a `null` entry rather than failing.

## Phase 2: EU AI Act + AI RMF doctrine files + plan-template impact-assessment section

### Affected Files

- `tests/test_doctrine_eu_ai_act_anchored.py` — NEW: round-trip integrity test against the article-by-article mapping; for each Article cited (9, 12, 13, 14, 15, 50), asserts the doctrine body contains a non-empty paragraph naming the article.
- `tests/test_doctrine_ai_rmf_anchored.py` — NEW: round-trip integrity test for the four AI RMF functions (GOVERN, MAP, MEASURE, MANAGE) and the AI 600-1 GenAI profile sections cited.
- `tests/test_plan_schema_impact_assessment.py` — NEW: locks the new optional `impact_assessment` field shape in `plan.schema.json`; validates a plan with the field; asserts schema accepts when `change_class: breaking` and `high_risk_target: true` together; asserts plan without the field still validates (backward compat).
- `qor/references/doctrine-eu-ai-act.md` — NEW: prose doctrine. Sections: Applicability classification (Qor-logic as developer support tool, not high-risk system; downstream-operator inheritance), Article-by-article mapping (9, 10, 12, 13, 14, 15, 50, 72; each citing concrete Qor-logic surface), Annex IV technical-documentation guidance (advisory, for downstream operators applying Qor-logic to high-risk systems), Limitations + scope.
- `qor/references/doctrine-ai-rmf.md` — NEW: prose doctrine. Sections: AI RMF 1.0 framework summary, GOVERN/MAP/MEASURE/MANAGE function-by-function mapping (each citing Qor-logic surface), AI 600-1 GenAI profile section-by-section mapping (§2.4, §2.7, §2.8, §2.10, §2.12), evidence-collection contract (existing META_LEDGER + shadow genome already serve as MEASURE-3.1 evidence; Phase 54 `ai_provenance` field is the new MEASURE-2.1 surface).
- `qor/gates/schema/plan.schema.json` — AMEND: add optional `impact_assessment` object property with sub-fields `{ purpose, affected_stakeholders, identified_risks, mitigations, residual_risks }`. Add optional `high_risk_target: boolean` declaring whether the downstream system being supported by this Qor-logic invocation is itself a high-risk AI system per EU AI Act Annex III.
- `qor/skills/sdlc/qor-plan/SKILL.md` — APPEND new optional Step 1c "Impact assessment dialogue (Phase 54 wiring)". Triggered when `change_class: breaking` AND operator declares `high_risk_target: true` during Step 1b documentation-integrity dialogue. Elicits the five impact-assessment fields. Skipped silently for non-high-risk-target plans (default).
- `qor/references/doctrine-context-discipline.md` — APPEND short paragraph cross-linking the new doctrines (existing context-discipline doctrine already covers MAP-1.1).
- `CLAUDE.md` Authority line — APPEND `eu-ai-act` and `ai-rmf` doctrine references alongside existing `attribution`, `test-discipline`, etc.

### Changes

EU AI Act doctrine carries the explicit applicability statement: Qor-logic itself is NOT a high-risk AI system per Annex III; operators applying Qor-logic to high-risk-system development inherit Annex III obligations. The doctrine maps each obligation an inheriting operator would need (Art. 9 risk register, Art. 13 transparency to deployers, etc.) to the Qor-logic surface that supports it (META_LEDGER as Art. 12 logging, override-with-event as Art. 14 oversight, etc.).

AI RMF doctrine reuses the GOVERN/MAP/MEASURE/MANAGE structure from `docs/research-brief-prompt-logic-frameworks-2026-04-30.md` §B and adds the AI 600-1 GenAI profile section explicitly. The doctrine declares a forward-only evidence-collection contract: starting Phase 54, `ai_provenance.human_oversight` field on each gate artifact serves as MANAGE-1.1 + MEASURE-2.1 evidence per session.

The plan template `impact_assessment` block is opt-in via the new `high_risk_target: true` declaration. Most plans (which target Qor-logic itself) do not set the flag and the section is omitted. When set, the template enforces the five sub-fields (purpose, stakeholders, risks, mitigations, residual risks) per AI RMF MAP-3.1/MAP-5.1.

### Unit Tests

- `tests/test_doctrine_eu_ai_act_anchored.py`:
  - `test_doctrine_round_trip_against_articles`: imports a tuple `_CITED_ARTICLES = (9, 10, 12, 13, 14, 15, 50, 72)` (literal in the test file; doctrine references the same set); reads the doctrine; asserts each `Art. <N>` heading exists with a non-empty body. Heading-tree integrity (mirroring Phase 53 doctrine test pattern).
  - `test_doctrine_classifies_qor_logic_under_applicability_section_with_non_empty_body` — heading-tree integrity test (per Phase 53 `test_doctrine_round_trip_against_canary_catalog` template). Asserts: (1) doctrine declares a `## Applicability classification` section heading; (2) the body between that heading and the next heading is non-empty after whitespace trim and contains at least one substantive sentence (>=20 chars after collapse); (3) the body explicitly mentions both `Annex III` and the literal classification (`not high-risk` or `not classified as high-risk`). Acceptance question: if the section body were silently emptied while the heading remained, would the test fail? YES — body-emptiness check fails. If the Annex III + classification words were removed from the body, would the test fail? YES — substring round-trip on the canonical classification claim fails.
- `tests/test_doctrine_ai_rmf_anchored.py`:
  - `test_doctrine_round_trip_against_functions`: imports `_RMF_FUNCTIONS = ("GOVERN", "MAP", "MEASURE", "MANAGE")`; asserts each function has its own canonical section with a non-empty body and at least one Qor-logic surface citation.
  - `test_doctrine_round_trip_against_genai_profile_sections`: imports `_GENAI_SECTIONS = ("2.4", "2.7", "2.8", "2.10", "2.12")`; asserts each section is mapped.
- `tests/test_plan_schema_impact_assessment.py`:
  - `test_schema_accepts_plan_with_impact_assessment`: feeds a plan payload with a complete `impact_assessment` block; asserts validates.
  - `test_schema_accepts_plan_without_impact_assessment`: feeds a plan payload without the field; asserts validates (backward compat).
  - `test_schema_rejects_high_risk_target_without_impact_assessment`: feeds a plan with `high_risk_target: true` but no `impact_assessment`; asserts schema fails validation (contract: high-risk target plans MUST declare impact assessment).
- `tests/test_plan_skill_prose_cites_impact_assessment.py`:
  - `test_plan_skill_step_1c_round_trips_impact_assessment_subfields` — schema-anchored round-trip integrity test. Reads `qor/gates/schema/plan.schema.json`; extracts the `impact_assessment` object's required sub-field names (`purpose`, `affected_stakeholders`, `identified_risks`, `mitigations`, `residual_risks`); asserts every sub-field name appears in the body of the qor-plan SKILL.md `### Step 1c: Impact assessment dialogue` section AND the section body is non-empty after whitespace trim. Acceptance question: if any sub-field were silently dropped from the schema or the SKILL.md prose drifted out of sync, would the test fail? YES — round-trip mismatch surfaces the offending field. If the section body were emptied while the heading remained, would the test fail? YES — body-emptiness check fails.

## Phase 3: Subagent tool-scope advisory frontmatter + override-friction escalator

### Affected Files

- `tests/test_skill_frontmatter_permitted_tools.py` — NEW: lints all `qor/skills/**/SKILL.md` for the `permitted_tools:` and `permitted_subagents:` YAML keys. Tolerant in this phase (warns on absence; does not fail). Phase 55 promotes to ABORT.
- `tests/test_override_friction_escalator.py` — NEW: locks `qor.scripts.override_friction.check(session_id)` behavior — returns `OverrideFrictionResult(threshold_reached, count, override_events)` based on shadow log; raises `RuntimeError` if invoked without justification text on the third+ override.
- `qor/skills/governance/qor-audit/SKILL.md`, `qor/skills/sdlc/qor-implement/SKILL.md`, `qor/skills/sdlc/qor-plan/SKILL.md`, `qor/skills/governance/qor-substantiate/SKILL.md`, `qor/skills/governance/qor-validate/SKILL.md`, `qor/skills/sdlc/qor-research/SKILL.md` — APPEND `permitted_tools:` and `permitted_subagents:` keys to each frontmatter block. Initial values: conservative defaults (`permitted_tools: [Read, Grep, Glob, Bash, Edit, Write]` for SDLC skills; `permitted_subagents: []` for everyone in this phase). Documented in doctrine-ai-rmf as a pre-enforcement declaration; Phase 55 wires Cedar-based admission.
- `qor/scripts/override_friction.py` — NEW: pure-Python module. Public API:
  - `check(session_id: str, *, threshold: int = 3) -> OverrideFrictionResult` — counts `gate_override` events for the session; if count >= threshold, returns `threshold_reached=True`.
  - `record_with_justification(event: dict, justification: str) -> dict` — extends a gate_override event payload with a non-empty `justification` field; raises `ValueError` if justification is shorter than 50 chars.
- `qor/gates/schema/shadow_event.schema.json` — AMEND: add optional `justification` field (string, minLength 50) to event payloads. Required when `event_type == "gate_override"` AND the event is the third+ in a session (enforced at write-time by `override_friction.record_with_justification`, not by schema).
- `qor/scripts/gate_chain.py` — UPDATE: `emit_gate_override()` consults `override_friction.check()` before emitting; if threshold reached AND no justification provided, raises `OverrideFrictionRequired` exception. Skill prose for the six gate-checking skills updates to catch this exception, prompt the operator for a justification, and re-call with `justification=...`.
- `qor/skills/{sdlc/qor-plan,governance/qor-audit,sdlc/qor-implement,governance/qor-substantiate,governance/qor-validate,sdlc/qor-research}/SKILL.md` — APPEND a single line to each gate-check block: "On `OverrideFrictionRequired` exception, prompt operator for justification (>=50 chars), re-call `emit_gate_override` with `justification=<text>`."
- `qor/references/doctrine-governance-enforcement.md` — APPEND `§11 Override-friction escalator` subsection citing the threshold, the friction form (free-text justification), and the symmetry with `§10.4 Cycle-count escalator`.

### Changes

Subagent frontmatter is **declarative-only** in this phase. The YAML keys are added to skills but no admission code reads them yet. This is a deliberate two-step rollout: Phase 54 ships the surface so Phase 55 can wire enforcement without touching every skill; Phase 55's audit will be smaller because the structural change has already landed.

Override-friction escalator engages at the third override per session (matching `cycle_count_escalator`'s threshold). The friction form is a free-text justification appended to the override event; minimum 50 characters forces meaningful articulation. Below threshold, override behavior is unchanged. The escalator is deliberately count-based (not classification-based) to keep the rule simple; future tuning may stratify by override type.

The `OverrideFrictionRequired` exception is the runtime signal that the threshold has been crossed. Skill prose handles it by prompting the operator inline; if the operator refuses to provide a justification, the override is refused (the gate stays in its current state and the operator must address the underlying cause via `/qor-remediate`). This keeps the friction proportional: one friction event per crossing, not per attempted override.

### Unit Tests

- `tests/test_skill_frontmatter_permitted_tools.py`:
  - `test_six_gate_skills_declare_permitted_tools`: walks the six SDLC + governance skills; asserts each YAML frontmatter contains `permitted_tools:` and `permitted_subagents:` keys with list values.
  - `test_permitted_tools_lint_warns_on_absent_skill`: synthetic fixture removing the keys from a tmp copy; asserts lint produces a warning (stderr) but not an error (exit 0). Phase 55 will flip to error.
- `tests/test_override_friction_escalator.py`:
  - `test_check_returns_false_below_threshold`: 2 override events; asserts `threshold_reached=False`.
  - `test_check_returns_true_at_threshold`: 3 override events; asserts `threshold_reached=True`.
  - `test_record_with_justification_validates_length`: invokes with 49-char justification; asserts `ValueError` raised; with 50-char justification; asserts returned payload contains the justification.
  - `test_emit_gate_override_raises_on_third_without_justification`: simulates 3 overrides in a session; the third call without `justification=` raises `OverrideFrictionRequired`.
  - `test_emit_gate_override_succeeds_with_justification`: same scenario but third call passes `justification=<50-char-string>`; asserts succeeds; assert event payload carries justification field.
- `tests/test_skill_prose_handles_friction_exception.py`:
  - `test_skills_emitting_gate_overrides_handle_friction_exception` — co-occurrence behavior invariant per the canonical Phase 50 model. Walks `qor/skills/**/*.md`. **Conditional rule**: for any SKILL.md whose body invokes `gate_chain.emit_gate_override(`, assert the same body also references `OverrideFrictionRequired` AND describes a re-call path with `justification=`. The conditional anchors the assertion to actual override-emitting behavior; a skill that does not emit overrides is not checked, a skill that does is required to handle the friction exception. Acceptance question: if any override-emitting skill regressed and stopped describing the friction handling (moved into a comment, deleted), would the test fail? YES — the conditional set still contains the skill, the inner assertion fails. Negative-path: synthetic skill fixture invoking `emit_gate_override` but omitting friction handling; asserts the lint catches it.

## Phase 4: Self-application + sprint-progress dashboard

### Affected Files

- `tests/test_phase54_self_application.py` — NEW: validates that Phase 54's own gate artifacts carry the new `ai_provenance` field and that the manifest aggregator CLI works end-to-end against this session's artifacts.
- `qor/scripts/sprint_progress.py` — NEW: small CLI that reads the latest research brief in `docs/research-brief-*.md`, parses the Recommendations table for Priority numbers, walks `docs/META_LEDGER.md` for SESSION SEAL entries that cite each Priority, and emits a sprint-progress table. Useful for operator visibility into multi-phase compliance work.
- `tests/test_sprint_progress_cli.py` — NEW: locks the CLI behavior with a fixture brief + fixture ledger.

### Changes

Self-application Phase 4 verifies the full chain end-to-end on Phase 54's own seal: the substantiate gate artifact from this session must carry the `ai_provenance` field, the CLI must aggregate it into a session manifest, and the sprint-progress dashboard must show Phase 54 as completing Priorities 2/4/5.

Sprint-progress CLI is opt-in (operator runs `qor-logic compliance sprint-progress`); it reads the latest research brief and matches Priorities to ledger entries. Useful as the audit-readable narrative for any external reviewer asking "where are you in the LLM Top 10 rollout?".

### Unit Tests

- `tests/test_phase54_self_application.py`:
  - `test_phase54_substantiate_gate_carries_ai_provenance`: reads `.qor/gates/<this_session>/substantiate.json`; asserts `ai_provenance` field present with `human_oversight: pass` (this seal's verdict).
  - `test_phase54_provenance_manifest_aggregator_emits_5_phases`: invokes CLI against this session; asserts manifest contains 5 entries (research/plan/audit/implement/substantiate).
  - `test_phase54_self_scan_no_canary_triggers`: scans this plan + new doctrines + new helper modules with `qor.scripts.prompt_injection_canaries.scan` (with `--mask-code-blocks`); asserts zero hits. Reuses Phase 53's self-application pattern.
- `tests/test_sprint_progress_cli.py`:
  - `test_cli_emits_priority_status_table`: fixture brief with Priorities 1-5 + fixture ledger with seal entries citing Priorities 1, 2; asserts CLI emits "1: SEALED, 2: SEALED, 3-5: PENDING" or equivalent canonical format.
  - `test_cli_handles_missing_brief`: no research brief in `docs/`; CLI emits a clear "no sprint in progress" message rather than failing.

## CI Commands

- `python -m pytest tests/test_ai_provenance_schema.py tests/test_ai_provenance_helper.py tests/test_skill_prose_cites_ai_provenance.py tests/test_compliance_ai_provenance_cli.py -v` — Phase 1 lock.
- `python -m pytest tests/test_doctrine_eu_ai_act_anchored.py tests/test_doctrine_ai_rmf_anchored.py tests/test_plan_schema_impact_assessment.py tests/test_plan_skill_prose_cites_impact_assessment.py -v` — Phase 2 lock.
- `python -m pytest tests/test_skill_frontmatter_permitted_tools.py tests/test_override_friction_escalator.py tests/test_skill_prose_handles_friction_exception.py -v` — Phase 3 lock.
- `python -m pytest tests/test_phase54_self_application.py tests/test_sprint_progress_cli.py -v` — Phase 4 lock.
- `python -m pytest -x` — full suite; expect 947 + ~35 new = ~982 passing twice (deterministic).
- `python -m qor.scripts.prompt_injection_canaries --mask-code-blocks --files docs/plan-qor-phase54-ai-provenance-and-act-alignment.md docs/META_LEDGER.md qor/references/doctrine-eu-ai-act.md qor/references/doctrine-ai-rmf.md` — verify Phase 54 docs scan clean.
- `python -m qor.reliability.skill_admission qor-substantiate` — admit modified skills.
- `python -m qor.reliability.gate_skill_matrix` — handoff integrity post-edits.
- `python -m qor.scripts.check_variant_drift` — dist parity post-skill edits.
- `python -m qor.scripts.badge_currency --repo-root . --ledger docs/META_LEDGER.md` — Tests + Doctrines + Ledger badges current.
- `python -m qor.cli compliance ai-provenance --session <this-session>` — manifest aggregator works.
- `python -m qor.cli compliance sprint-progress` — sprint dashboard works.
