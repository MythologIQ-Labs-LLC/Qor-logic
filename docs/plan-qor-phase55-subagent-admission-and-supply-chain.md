# Plan: Phase 55 — Cedar-enforced subagent admission + model-pinning + CycloneDX SBOM + pre-audit lints

**change_class**: feature

**doc_tier**: standard

**terms_introduced**:
- term: tool-scope policy
  home: qor/references/doctrine-ai-rmf.md
- term: model-pinning frontmatter
  home: qor/references/doctrine-ai-rmf.md
- term: CycloneDX SBOM
  home: qor/references/doctrine-eu-ai-act.md

**boundaries**:
- limitations:
  - Cedar-based admission is enforced at the **skill-admission helper** layer (`qor.reliability.skill_admission`), not at runtime Tool/Agent invocation by the harness. The skill harness (Claude Code, Kilo Code, etc.) is outside Qor-logic's control; skill prose declares scope and the admission gate refuses to admit a skill whose declared scope does not match its actual prose-cited tool invocations.
  - Model-pinning frontmatter is **declarative + lint-enforced**, not runtime-enforced. The harness does not consult the frontmatter at invocation time; the lint surfaces drift between declared `min_model_capability` and the model the operator is running. A skill cannot refuse to execute on a smaller model from its prose alone.
  - CycloneDX SBOM emission is **release-time only** (`/qor-repo-release` Step Z addition). Pre-release sessions do not produce SBOMs; full traceability requires sealing through the release skill.
- non_goals:
  - Harness-level Tool-invocation interception. Out of scope; would require Claude Code / Kilo Code / etc. to read Qor-logic frontmatter at invocation time.
  - SBOM signing (`sigstore`, `in-toto`). Phase 56+ candidate.
  - Vulnerability scanning of dependencies. Out of scope; SBOM is the input to a downstream scan, not the scan itself.
  - Dynamic model-capability detection. The frontmatter declares `min_model_capability` as static metadata; a hypothetical runtime reflection on the active model is out of scope.
- exclusions:
  - Retroactive SBOM generation for prior releases. Forward-only from Phase 55 forward.
  - Frontmatter changes on meta or memory skills (qor-bootstrap, qor-help, etc.). Phase 55 declares `permitted_tools` / `model_compatibility` only on the eight skills that already carry the Phase 54 advisory frontmatter (six SDLC + governance + qor-refactor + four meta gate-writers minus the docs/help skills).

## Sprint context

Phase 55 of the five-phase compliance sprint started at Phase 53. Closes Priority 3 from `docs/research-brief-prompt-logic-frameworks-2026-04-30.md`:

| Phase | Status | Closes |
|---|---|---|
| 53 | sealed v0.39.0 | LLM01 + DRIFT-1/2 + OWASP LOW-4 |
| 54 | sealed v0.40.0 | EU AI Act Art. 13/14/50 + AI RMF doctrines + LLM08 + Phase 54-LLM07-declarative |
| **55 (this plan)** | drafting | LLM05 + LLM07-runtime; AI RMF GV-6.1 + MG-3.1; pre-audit lints (recurring-pattern advisory closure) |
| 56 | queued | LLM06 (secret-scanning gate at substantiate) |
| 57 | folded into Phase 54 | (override-friction; sealed) |

This plan also bundles the **pre-audit lint pair** recommended in both Phase 53 and Phase 54 audit advisories: `plan_test_lint.py` (catches presence-only test descriptions in plan files before `/qor-audit` sees them) and `plan_grep_lint.py` (catches infrastructure-mismatch citations against actual repo state). Net effect: future audits avoid Pass-1 VETO cycles for these recurring failure classes.

## Open Questions

1. **Cedar admission layer**: skill admission gate enforces (a) only at `/qor-substantiate` Step 4.6 reliability sweep (existing surface; advisory→ABORT), (b) at every skill startup (Step 0 gate check, requires every skill body change), or (c) both. Default: **(a)** — Step 4.6 is the canonical reliability sweep surface; per-skill enforcement would require touching all six Step 0 blocks and is duplicative of the substantiate sweep.
2. **SBOM tool**: (a) hand-rolled CycloneDX v1.5 JSON via stdlib (preserves zero-runtime-deps doctrine), (b) `cyclonedx-py` library as a release-time-only dev dep, (c) emit a non-CycloneDX simpler manifest. Default: **(a)** — Qor-logic has zero runtime deps and a well-defined surface (single Python package + 4 doctrine variant outputs). Hand-rolled CycloneDX 1.5 component declaration is ~50 LOC; deferred validation to downstream tooling. Trade-off: rejects future CycloneDX schema migrations vs. an upstream dep.
3. **Model-pinning lint severity**: (a) WARN-only at `/qor-plan` Step 0.2 (operator advisory), (b) WARN at plan + ABORT at substantiate Step 4.6, (c) advisory-only via `qor-logic compliance model-check` opt-in subcommand. Default: **(a)** — declarative-only matches the Phase 54 rollout pattern for `permitted_tools`. Phase 56 or later may promote to ABORT once the operator base settles.

Defaults will be encoded unless overridden during audit.

## Phase 1: Cedar-enforced subagent admission

### Affected Files

- `tests/test_skill_admission_tool_scope.py` — NEW: locks the new admission rules; for each of the eight scoped skills, asserts `qor.reliability.skill_admission.admit(<skill>)` accepts when `permitted_tools` declares the tools the skill prose actually invokes; rejects when the skill prose invokes a tool not in `permitted_tools`. Behavior invariant: round-trip between frontmatter declaration and prose invocation, scoped to the canonical Tool name set.
- `tests/test_cedar_subagent_admission.py` — NEW: locks the new Cedar `forbid` rule. Constructs `Resource(kind="Skill", attributes={"declared_tool_scope": [...], "actual_tool_invocations": [...]})`; evaluates against the policy; asserts `Decision.DENY` when `actual ⊄ declared`, `Decision.ALLOW` otherwise.
- `qor/policies/skill_admission.cedar` — APPEND second rule:
  ```cedar
  // LLM07 + AI RMF GV-6.1: forbid skill invocations whose actual tool surface
  // exceeds the declared permitted_tools frontmatter.
  forbid (
    principal,
    action == Action::"invoke",
    resource
  ) when { resource.actual_tool_invocations_exceed_scope == true };
  ```
- `qor/policy/resource_attributes.py` — APPEND `compute_skill_admission_attributes(skill_md_path: str | Path) -> dict[str, bool]` that returns `{registered: bool, has_frontmatter: bool, actual_tool_invocations_exceed_scope: bool}`. Reads the skill's frontmatter `permitted_tools`; greps the skill body for canonical Tool-name tokens; computes the boolean.
- `qor/reliability/skill_admission.py` — UPDATE: extend `admit()` to consult `qor.policy.resource_attributes.compute_skill_admission_attributes` AND evaluate via `qor.policy.evaluator.evaluate` against the loaded `skill_admission.cedar` policies. Emit ADMITTED / NOT-ADMITTED + reason (frontmatter missing, tool-scope exceeded, etc.).
- `qor/skills/governance/qor-substantiate/SKILL.md` Step 4.6 reliability sweep — UPDATE to invoke `skill_admission` against ALL eight scoped skills (not just `qor-substantiate` itself). Any non-zero exit ABORTs substantiation per the existing sweep contract.
- `qor/references/doctrine-ai-rmf.md` — APPEND new section "Tool-scope policy enforcement" under MANAGE-3.1 documenting the Cedar rule + the `compute_skill_admission_attributes` helper + the eight scoped skills.

### Changes

The single source of truth for canonical Tool names is a new module-level frozenset `_CANONICAL_TOOLS` in `qor/policy/resource_attributes.py`: `{"Read", "Write", "Edit", "Glob", "Grep", "Bash", "Agent", "WebFetch", "WebSearch", "TodoWrite"}`. The grep computes `actual_tool_invocations` by scanning the skill body for the literal pattern `Tool: <name>` and `<name>(` callsites in inline code blocks. Pattern set is small and deterministic; no NLP.

`actual_tool_invocations_exceed_scope` is True iff `set(actual) - set(declared) != ∅`. The Cedar rule denies in that case. The skill admission helper composes the resource attributes via `compute_skill_admission_attributes`, evaluates Cedar, returns the verdict.

The substantiate Step 4.6 update walks the eight scoped skills and ABORTs on any NOT-ADMITTED verdict. Subagent scope (`permitted_subagents`) is enforced symmetrically: `qor.policy.resource_attributes.compute_skill_admission_attributes` returns a parallel `actual_subagent_invocations_exceed_scope` boolean computed from `Agent(subagent_type="...")` callsites in skill prose.

### Unit Tests

- `tests/test_skill_admission_tool_scope.py`:
  - `test_admit_accepts_skill_with_matching_tool_scope` — fixture skill with `permitted_tools: [Read, Grep]` whose body invokes only Read and Grep; asserts admission ADMITTED.
  - `test_admit_rejects_skill_with_tool_invocation_exceeding_scope` — fixture skill with `permitted_tools: [Read]` but body invokes Bash; asserts NOT-ADMITTED with reason citing "Bash" and "tool-scope exceeded".
  - `test_admit_rejects_skill_with_subagent_invocation_exceeding_scope` — fixture skill with `permitted_subagents: []` but body has `Agent(subagent_type="general-purpose")`; asserts NOT-ADMITTED.
  - `test_admit_passes_for_eight_actual_repo_skills` — walks the eight Phase 54-scoped skills in the real repo (qor-research, qor-plan, qor-implement, qor-audit, qor-substantiate, qor-validate, qor-refactor, qor-repo-audit); asserts admission ADMITTED for each. Self-application: this Phase 55 implementation must satisfy the new policy.
  - `test_canonical_tools_set_matches_documented_tool_names` — round-trip integrity: imports `_CANONICAL_TOOLS` and asserts the set matches the canonical Tool names declared in `qor/references/doctrine-ai-rmf.md` Tool-scope policy section. Drift between code and doctrine surfaces immediately.
- `tests/test_cedar_subagent_admission.py`:
  - `test_cedar_denies_when_tool_scope_exceeded` — loads `skill_admission.cedar`; constructs Request + Resource with `actual_tool_invocations_exceed_scope: true`; evaluates; asserts DENY.
  - `test_cedar_allows_when_tool_scope_respected` — same setup with attribute False; asserts ALLOW.
  - `test_cedar_admission_rule_uses_invoke_action` — locates the new forbid rule in the parsed policy; asserts its action is `Action::"invoke"`.
- `tests/test_resource_attributes_skill_scope.py` (new):
  - `test_compute_skill_admission_attributes_returns_expected_shape` — invokes the helper on a fixture skill; asserts return dict has keys `{registered, has_frontmatter, actual_tool_invocations_exceed_scope, actual_subagent_invocations_exceed_scope}`.
  - `test_helper_grep_detects_bash_invocation` — fixture body contains `\`\`\`bash\nls\n\`\`\``; helper detects Bash invocation.
  - `test_helper_grep_detects_agent_invocation_with_subagent_type` — fixture body contains `Agent(subagent_type="explore")`; helper detects Agent + subagent_type.
  - `test_helper_handles_skills_without_permitted_tools_frontmatter` — fixture without the keys; helper returns `actual_tool_invocations_exceed_scope: True` (treats missing-declaration as the empty allowlist; conservatively rejects). Closes the GV-6.1 default-deny posture.

## Phase 2: Model-pinning frontmatter + lint

### Affected Files

- `tests/test_model_pinning_frontmatter.py` — NEW: locks the new YAML keys + lint behavior.
- `qor/skills/sdlc/{qor-research,qor-plan,qor-implement,qor-refactor}/SKILL.md`, `qor/skills/governance/{qor-audit,qor-substantiate,qor-validate}/SKILL.md`, `qor/skills/meta/qor-repo-audit/SKILL.md` — APPEND `model_compatibility:` and `min_model_capability:` keys to each YAML frontmatter. Initial values declared per skill; canonical capability tier set is a frozen tuple `("haiku", "sonnet", "opus")` ordered by capability.
- `qor/scripts/model_pinning_lint.py` — NEW (~75 LOC): pure-Python module exposing `check(repo_root: Path, *, current_model: str | None = None) -> list[ModelPinningWarning]`. Reads `permitted_tools`-scoped skills, compares declared `min_model_capability` to the harness-supplied current model (read from `QOR_MODEL_FAMILY` env or passed argument). Returns warnings for skills whose `min_model_capability` exceeds the running model's tier.
- `qor/skills/sdlc/qor-plan/SKILL.md` Step 0.2 — APPEND a model-pinning lint invocation symmetric with the existing install-drift check; WARN-only per Open Question 3 default.
- `qor/references/doctrine-ai-rmf.md` — APPEND new section "Model-pinning frontmatter" under MANAGE-3.1 documenting the keys + lint + capability ordering.
- `qor/skills/sdlc/qor-plan/references/step-extensions.md` — APPEND short paragraph under Step 0.2 documenting the model-pinning check (existing extension file).

### Changes

Capability tier is an ordered tuple, not a free-form string: `_CAPABILITY_ORDER = ("haiku", "sonnet", "opus")`. A skill declaring `min_model_capability: opus` and running on `claude-haiku-4-5` (capability tier "haiku") emits a warning. Pattern matches the harness model-family naming convention (e.g., `claude-opus-4-7`, `claude-sonnet-4-6`, `claude-haiku-4-5-20251001`); the lint extracts the tier via simple regex on the env value.

`model_compatibility:` is a list (non-ordered allowlist of compatible model families). `min_model_capability:` is the strict minimum tier. They are independent: a skill could declare `model_compatibility: [claude-opus-4-7, claude-sonnet-4-6]` and `min_model_capability: sonnet` to express "designed for these specific models OR any sonnet-or-better".

The existing `qor.scripts.qor_platform.current()` already returns a state dict from which the host extracts; Phase 55 reuses that path symmetric with Phase 54's `ai_provenance.build_manifest`.

### Unit Tests

- `tests/test_model_pinning_frontmatter.py`:
  - `test_eight_skills_declare_model_pinning_keys` — walks the eight scoped skills; asserts each frontmatter contains `model_compatibility:` (list) and `min_model_capability:` (string from `_CAPABILITY_ORDER`).
  - `test_lint_warns_when_min_capability_exceeds_current_model` — fixture skill with `min_model_capability: opus`; invokes `model_pinning_lint.check(repo_root, current_model="claude-haiku-4-5-20251001")`; asserts return list contains one warning naming the skill and the gap.
  - `test_lint_passes_when_current_model_meets_minimum` — same fixture; current_model `claude-opus-4-7`; asserts return empty.
  - `test_lint_passes_when_current_model_exceeds_minimum` — fixture with `min_model_capability: sonnet`; current_model `claude-opus-4-7`; asserts empty (opus > sonnet).
  - `test_lint_warns_when_current_model_not_in_compatibility_list` — fixture with `model_compatibility: [claude-opus-4-7]` but current_model `claude-sonnet-4-6`; asserts warning naming the mismatch.
  - `test_lint_skips_skills_without_pinning_keys` — fixture without the keys; asserts no warning (silent skip; not all skills must pin).
  - `test_capability_tier_extraction_from_model_family_string` — exercises the regex: `claude-opus-4-7` → "opus"; `claude-haiku-4-5-20251001` → "haiku"; `claude-sonnet-4-6` → "sonnet"; `unknown` → None (treated as "skip lint, do not warn").
  - `test_lint_handles_unset_qor_model_family_env` — fixture skill with pinning; `current_model=None` and `QOR_MODEL_FAMILY` unset; asserts empty result list (cannot warn without a known model).
- `tests/test_qor_plan_skill_invokes_model_pinning_lint.py` (new):
  - `test_skills_with_pinning_keys_are_covered_by_pinning_lint_invocation` — true co-occurrence behavior invariant per Phase 50 model. **Conditional rule**: enumerate every SKILL.md whose YAML frontmatter declares the pair `model_compatibility:` + `min_model_capability:`. For each such skill, assert that **at least one SKILL.md whose `phase:` is `plan` invokes `python -m qor.scripts.model_pinning_lint`**. The conditional anchors the assertion to the actual frontmatter-declaration set; if any pinning-declaring skill exists but no plan-phase skill invokes the lint at Step 0.2, the test fails by enumeration. Acceptance question: if the plan-phase skill silently regressed and dropped the lint invocation while the pinning frontmatter remained on the eight scoped skills, would the test fail? YES — the conditional set is non-empty, the inner assertion fails. Negative-path: synthetic plan-phase skill fixture omitting the lint invocation; the lint enumerates the missing coverage.

## Phase 3: CycloneDX SBOM emission at /qor-repo-release

### Affected Files

- `tests/test_sbom_emission.py` — NEW: locks the SBOM emitter behavior + schema-tier validity.
- `qor/scripts/sbom_emit.py` — NEW (~80 LOC): pure-Python emitter producing a CycloneDX v1.5-compatible JSON document. Walks `pyproject.toml` for the Qor-logic component; walks `qor/dist/variants/*/manifest.json` for the four variant artifacts; walks `qor/skills/**/SKILL.md` for the 29 skill components and `qor/references/doctrine-*.md` for the 20 doctrines. Each component declares `bom-ref`, `name`, `version`, `purl` (where applicable), `type`, and `description`. Output: pretty-printed JSON to `dist/sbom.cdx.json` (or path given via `--out`).
- `qor/skills/meta/qor-repo-release/SKILL.md` Step Z — APPEND SBOM-emission step before the `gate_chain.write_gate_artifact` call. Emit SBOM to a **sidecar path** `dist/sbom.cdx.json` (not embedded in the deliver gate payload — sidecar is symmetric with the existing post-substantiate Merkle-seal pattern). Capture the sidecar path into the deliver gate payload as `sbom_path` for downstream operator discovery.
- `qor/gates/schema/deliver.schema.json` — **NEW** (closes pre-existing surface gap). `qor-repo-release/SKILL.md:15` declares `gate_writes: deliver` and `qor-repo-release/SKILL.md:217` writes `gate_chain.write_gate_artifact(phase="deliver", ...)`, but `qor.scripts.validate_gate_artifact.PHASES` (verified at HEAD) currently has no `"deliver"` entry — the deliver write currently bypasses schema validation. Phase 55 closes this incidental gap as part of Phase 3 by declaring the schema with required fields `{phase: const "deliver", ts, session_id, version, tag, sbom_path}` (sbom_path optional — captures the sidecar path when emit succeeds; omitted when emission is skipped). Schema follows the existing `_provenance.schema.json` `$ref` pattern from Phase 54 for the embedded `ai_provenance` field.
- `qor/scripts/validate_gate_artifact.py` — UPDATE: add `"deliver"` to `PHASES` list. One-line addition; closes the silent-bypass surface.
- `qor/references/doctrine-eu-ai-act.md` — APPEND new section "CycloneDX SBOM" under Art. 50 documenting the emitter + path + downstream-consumer guidance.
- `qor/cli_handlers/release.py` — NEW (~30 LOC): hosts `do_sbom` handler invoked via `qor-logic release sbom --out <path>` for ad-hoc SBOM generation outside the seal cycle.
- `qor/cli.py` — REGISTER new `release` subcommand group with `sbom` subcommand. Mirrors the `compliance` registration pattern from Phase 54.

### Changes

CycloneDX 1.5 schema reference: https://cyclonedx.org/docs/1.5/json/. The hand-rolled emitter targets the minimum viable component set:

- `metadata.tools` declares Qor-logic itself (the SBOM emitter).
- `metadata.component` is the Qor-logic root component (`type: application`, `bom-ref: qor-logic@<semver>`, `purl: pkg:pypi/qor-logic@<semver>`).
- `components` lists 29 skills (`type: file`, `bom-ref: skill:<name>@<semver>`), 20 doctrines (`type: file`, `bom-ref: doctrine:<name>@<semver>`), 4 variant artifacts (`type: framework`, `bom-ref: variant:<host>@<semver>`).
- `dependencies` declares the Qor-logic root depends on all components.

`bom-ref` strings use `<kind>:<name>@<semver>` for cross-document referenceability. No external dependencies declared (Python stdlib only); a future phase may add `pkg:pypi/<dep>@<ver>` entries when the doctrine relaxes the zero-runtime-deps stance.

### Unit Tests

- `tests/test_sbom_emission.py`:
  - `test_sbom_emitter_produces_cyclonedx_v1_5_shape` — invokes `sbom_emit.emit(repo_root=tmp_path_with_fixture)`; asserts output JSON has `bomFormat: "CycloneDX"`, `specVersion: "1.5"`, `metadata.tools[0].name == "Qor-logic"`, `metadata.component.bom-ref` matches `qor-logic@<semver>`.
  - `test_sbom_emitter_lists_qor_logic_root_component` — asserts `metadata.component.type == "application"`, `purl.startswith("pkg:pypi/qor-logic@")`.
  - `test_sbom_emitter_lists_29_skill_components` — fixture repo with 29 SKILL.md files; emitter; asserts `len([c for c in components if c["type"] == "file" and c["bom-ref"].startswith("skill:")]) == 29`.
  - `test_sbom_emitter_lists_20_doctrine_components` — fixture with 20 doctrines; asserts count.
  - `test_sbom_emitter_lists_4_variant_components` — fixture with 4 variant manifests; asserts count.
  - `test_sbom_emitter_dependencies_root_depends_on_all` — asserts `dependencies[0]["ref"] == "qor-logic@<semver>"` and `len(dependencies[0]["dependsOn"]) == 29 + 20 + 4`.
  - `test_sbom_emitter_writes_to_specified_out_path` — invokes with `out=tmp / "x.json"`; asserts file written.
  - `test_skills_writing_deliver_gate_invoke_sbom_emit` — true co-occurrence behavior invariant per Phase 50 model. **Conditional rule**: enumerate every SKILL.md whose YAML frontmatter declares `gate_writes: deliver`. For each such skill, assert the body invokes `sbom_emit.emit(` AND captures the result into a payload field named `sbom_path` AND the resulting `gate_chain.write_gate_artifact(phase="deliver", ...)` call passes that payload. Conditional on actual deliver-gate-write target, not on a single-skill substring. Acceptance question: if a deliver-writing skill silently dropped the SBOM emission while keeping the gate write, would the test fail? YES — the conditional set still includes that skill, the inner assertion fails. Negative-path: synthetic skill fixture declaring `gate_writes: deliver` and writing the gate but omitting `sbom_emit.emit`; the lint catches it.
  - `test_release_cli_subcommand_emits_sbom` — subprocess: `qor-logic release sbom --out <tmp>`; asserts exit 0 + output file matches schema shape.
- `tests/test_release_handler_module_present.py` (new):
  - `test_release_handler_register_function_exists` — imports `qor.cli_handlers.release.register`; asserts callable.
  - `test_qor_cli_dispatches_release_subcommand` — subprocess `qor-logic release sbom --help`; asserts exit 0.

## Phase 4: Pre-audit lints (recurring-pattern advisory closure)

### Affected Files

- `tests/test_plan_test_lint.py` — NEW: locks the presence-only-test detector.
- `tests/test_plan_grep_lint.py` — NEW: locks the infrastructure-mismatch detector.
- `qor/scripts/plan_test_lint.py` — NEW (~60 LOC): walks `docs/plan-qor-phase*.md`; detects test descriptions matching the presence-only patterns: `asserts.*contains.*\bliteral\b`, `asserts.*\bsection\b.*\bexists\b`, `assert\s.*\bin\s+<file_text>\b`, `\bassert path\.exists\(`. Emits warning per detection with line number + suggested reformulation.
- `qor/scripts/plan_grep_lint.py` — NEW (~70 LOC): walks `docs/plan-qor-phase*.md`; extracts cited Python module paths (`qor.scripts.<name>`, `qor.policy.<name>`, `qor.reliability.<name>`) and skill paths (`qor/skills/**/*.md`); verifies each cited path resolves at HEAD. Emits warning per missing citation.
- `qor/skills/governance/qor-audit/SKILL.md` Step 0.5 — APPEND a pre-audit lint invocation block running both lints against the audit target plan; non-blocking WARN (does not VETO; surfaces drift before Step 3 passes evaluate).
- `qor/references/doctrine-shadow-genome-countermeasures.md` — APPEND new SG entry `SG-PreAuditLintGap-A` documenting the recurring presence-only-test + infrastructure-mismatch pattern across Phase 53 + Phase 54 first audits and the Phase 55 countermeasure (the two pre-audit lints).

### Changes

`plan_test_lint.py` greps test description bullets in plan files for the four presence-only patterns. Match precision over recall: false-positive on a test that genuinely uses substring presence as part of a larger behavior assertion is acceptable; the plan author can amend the description to clarify the behavior. False-negative (a presence-only test that escapes the lint) is captured downstream by `/qor-audit` Test Functionality Pass.

`plan_grep_lint.py` parses Python-import-style references (`qor.scripts.X`, `qor.X.Y`, `qor.references.<file>.md`, `qor/skills/**/SKILL.md`) and verifies each resolves. References declared as NEW in the plan's Affected Files block are excluded — the lint reads the Affected Files block and excludes its contents from the verification set. Closes the false-positive case where a plan correctly cites a path that the plan itself creates.

Both lints expose CLI entry points (`python -m qor.scripts.plan_test_lint --plan <path>`, `--plan_grep_lint --plan <path>`); audit Step 0.5 invokes them via argv-form.

### Unit Tests

- `tests/test_plan_test_lint.py`:
  - `test_lint_detects_substring_presence_pattern` — fixture plan body containing `asserts the body contains the literal "foo"`; asserts lint returns one warning with the bullet's line number.
  - `test_lint_detects_section_exists_pattern` — fixture with `asserts the section exists`; warning emitted.
  - `test_lint_detects_assert_in_file_text_pattern` — fixture with `assert "foo" in <file_text>`; warning.
  - `test_lint_detects_path_exists_pattern` — fixture with `assert path.exists()`; warning.
  - `test_lint_passes_for_behavior_invariant_test` — fixture with `asserts scan() returns the expected hit class`; no warning.
  - `test_lint_handles_plan_without_test_descriptions` — empty Unit Tests section; no warnings.
  - `test_lint_cli_emits_warnings_to_stderr_with_line_numbers` — subprocess invocation; asserts stderr contains the warning + line number.
- `tests/test_plan_grep_lint.py`:
  - `test_lint_detects_missing_module_citation` — fixture plan citing `qor.scripts.fake_module`; lint detects missing path.
  - `test_lint_passes_for_existing_module_citation` — fixture citing `qor.scripts.session`; no warning.
  - `test_lint_excludes_paths_declared_as_new_in_affected_files` — fixture plan whose Affected Files block declares `qor/scripts/new_helper.py — NEW`; main body cites `qor.scripts.new_helper`; lint suppresses warning.
  - `test_lint_detects_missing_skill_path` — fixture citing `qor/skills/sdlc/fake-skill/SKILL.md`; warning.
  - `test_lint_handles_plan_with_no_module_citations` — fixture with no Python references; no warnings.
  - `test_audit_phase_skills_invoke_both_pre_audit_lints` — true co-occurrence behavior invariant per Phase 50 model. **Conditional rule**: enumerate every SKILL.md whose YAML frontmatter declares `phase: audit`. For each such skill, assert the body invokes BOTH `python -m qor.scripts.plan_test_lint` AND `python -m qor.scripts.plan_grep_lint` (at any pre-Step-3 invocation site). Conditional on the audit-phase frontmatter set, not on a single-skill substring. Acceptance question: if the audit skill silently regressed and dropped one of the two lint invocations, would the test fail? YES — the conditional set still includes the skill, the inner per-lint assertion fails identifying which lint is missing. Negative-path: synthetic audit-phase skill fixture invoking only one of the two lints; the test catches the missing invocation.

## Phase 5: Self-application + sprint-progress reconciliation

### Affected Files

- `tests/test_phase55_self_application.py` — NEW.
- `qor/scripts/sprint_progress.py` — UPDATE: amend `parse_priorities` to recognize bundled-priority declarations in research-brief headings (e.g., `Priority 4 — folded into Phase 53`). Reads brief body (not just heading) for "folded into Phase NN" or "bundled into Phase NN" patterns and credits the originating Priority as SEALED when the named phase is sealed. Closes the Phase 54 issue where the CLI reported Phase 56/57 PENDING despite their work being bundled into Phase 53/54.

### Changes

Phase 55 self-application: this implement gate's `ai_provenance.human_oversight: absent` field is verified; the new `compute_skill_admission_attributes` helper is invoked against the eight scoped skills (including Phase 55's own additions) and asserted ADMITTED; the SBOM emitter run against this repo state is asserted to produce a valid CycloneDX 1.5 document; both pre-audit lints are run against this Phase 55 plan file and asserted to produce zero warnings.

Sprint-progress reconciliation: the CLI now correctly reports 4/5 priorities sealed after Phase 55 (Priorities 1, 2, 3 directly via Phases 53/54/55; Priority 5 via Phase 54 bundling; Priority 4 folded into Phase 53 since path-canonicalization landed there). Priority 4's "folded into Phase 53" claim is matched in the brief body during parse.

### Unit Tests

- `tests/test_phase55_self_application.py`:
  - `test_phase55_implement_gate_carries_ai_provenance` — reads `.qor/gates/<this_session>/implement.json`; asserts `ai_provenance` field present.
  - `test_eight_scoped_skills_admit_under_new_policy` — invokes `qor.reliability.skill_admission` against each of the eight scoped skills (qor-research, qor-plan, qor-implement, qor-refactor, qor-audit, qor-substantiate, qor-validate, qor-repo-audit); asserts ADMITTED for each. Self-application: this Phase 55 plan must satisfy its own policy.
  - `test_sbom_emitter_produces_valid_document_for_current_repo` — invokes `sbom_emit.emit(repo_root=REPO_ROOT)`; asserts output is valid CycloneDX 1.5 JSON; asserts `metadata.component.version == <pyproject version>`.
  - `test_pre_audit_lints_clean_against_phase55_plan` — invokes `plan_test_lint` and `plan_grep_lint` against this Phase 55 plan file; asserts both return empty warning list. Meta-coherence: this plan must not contain its own anti-patterns.
  - `test_sprint_progress_reports_4_of_5_priorities_after_phase55` — invokes `sprint_progress.render_progress(REPO_ROOT)`; asserts output contains `"4/5 priorities sealed"` after Phase 55 seals (computed against the brief's Priority headings and the ledger's SESSION SEAL entries). Pre-Phase-55-seal state would be 2/5; post-seal expectation is 4/5 (Priority 4 reconciled via the new "folded into" detector).

## CI Commands

- `python -m pytest tests/test_skill_admission_tool_scope.py tests/test_cedar_subagent_admission.py tests/test_resource_attributes_skill_scope.py -v` — Phase 1 lock.
- `python -m pytest tests/test_model_pinning_frontmatter.py tests/test_qor_plan_skill_invokes_model_pinning_lint.py -v` — Phase 2 lock.
- `python -m pytest tests/test_sbom_emission.py tests/test_release_handler_module_present.py -v` — Phase 3 lock.
- `python -m pytest tests/test_plan_test_lint.py tests/test_plan_grep_lint.py -v` — Phase 4 lock.
- `python -m pytest tests/test_phase55_self_application.py -v` — Phase 5 lock.
- `python -m pytest -x` — full suite; expect 1037 + ~50 new = ~1087 passing twice in a row (deterministic).
- `python -m qor.scripts.prompt_injection_canaries --mask-code-blocks --files docs/plan-qor-phase55-subagent-admission-and-supply-chain.md docs/META_LEDGER.md qor/references/doctrine-ai-rmf.md qor/references/doctrine-eu-ai-act.md` — verify Phase 55 docs scan clean.
- `python -m qor.scripts.plan_test_lint --plan docs/plan-qor-phase55-subagent-admission-and-supply-chain.md` — self-application of the new presence-only-test lint; expect exit 0.
- `python -m qor.scripts.plan_grep_lint --plan docs/plan-qor-phase55-subagent-admission-and-supply-chain.md` — self-application of the new infrastructure-mismatch lint; expect exit 0.
- `python -m qor.scripts.sbom_emit --out dist/sbom.cdx.json` — emit the SBOM and assert the output is a well-formed CycloneDX 1.5 document.
- `python -m qor.reliability.skill_admission qor-substantiate` — admit modified skills (substantiate gained the Step 4.6 sweep extension).
- `python -m qor.reliability.gate_skill_matrix` — handoff integrity post-edits.
- `python -m qor.scripts.check_variant_drift` — dist parity.
- `python -m qor.scripts.badge_currency --repo-root . --ledger docs/META_LEDGER.md` — Tests + Doctrines + Ledger badges current.
