# Qor-logic System State

**Snapshot**: 2026-05-14
**Chain Status**: ACTIVE (Phase 75 feature staged at v0.51.0 — skill capability declaration for /qor-substantiate; closes GH #38 V1).
**Phase**: Phase 75 staged (feature). V1 implements Option 1 from GH #38 ideation (session 2026-05-14T2216-a5f692): skill capability declaration mechanism. New `qor/scripts/substantiate_capability.py` parses qor-substantiate SKILL.md `## Step Prerequisites` table; new `qor-logic substantiate-capability` CLI emits a markdown table of per-step prerequisite status (PRESENT/ABSENT + evidence). 12 V1 step declarations (Steps 4.6, 4.6.5, 4.6.6, 4.7, 6.5, 6.8, 7.4, 7.5, 7.6, 7.7, 7.8, 8.5) cover the Python-toolkit and release-shape prerequisites. Each affected step body cross-references the table. `gate_skipped_prerequisite_absent` shadow_event enum entry added. SG-HalfSealedClaim-A doctrine entry catalogues the half-checked-seal pattern with 2026-05-06 originating recurrence (Customer-App-3.0 React+bun+Supabase, 8 of 15 gates failed/skipped, ended SUBSTANTIATE DEFERRED). 3 new glossary terms. 12 new tests across 5 files. Plan: `docs/plan-qor-phase75-skill-capability-declaration.md`. Gate artifacts at `.qor/gates/2026-05-14T2216-a5f692/`. V2 follow-on: pluggable backends (version_bump / changelog_stamp / release_artifact_compile) keyed off .qor/workspace.json archetype detection. V3 follow-on: two-track skill split (core + release). Previous phase -- Phase 74 sealed (feature v0.50.0, GH #49 + #58). V1 prose-only audit-pass extensions. `/qor-audit` Step 3 Infrastructure Alignment Pass gains a sixth bullet for third-party SDK + behavioral-semantics claim citations (closes SG-006 PostHog SDK hallucination class + SG-010 mechanism-detail hallucination recurrence class). `/qor-audit` Step 3 Ghost UI Pass gains a Live-Progress Invariant sub-rule (4 checklist items: intermediate state, no fake-jump, event-stream subscription, dismiss/retry surface). VETO sub-tag `live-progress-fake` under existing `ghost-ui` category (no schema enum change). SG-FakeProgress-A doctrine entry catalogues the fake-jump pattern with FailSafe v5.1.0 originating recurrence. 4 new glossary terms (third-party SDK citation, behavioral-semantics claim, Live-Progress Invariant, SG-FakeProgress-A). 6 new tests across 3 files. Plan: `docs/plan-qor-phase74-audit-pass-extensions.md`. Gate artifacts at `.qor/gates/2026-05-14T2154-26505b/`. V2 follow-on: mechanical `qor/scripts/plan_live_progress_lint.py` at Step 0.6 pre-audit lint surface deferred pending V1 prose adoption signals. Previous phase -- Phase 73 sealed (feature v0.49.0, GH #40 + #41). V1 ships doctrine + skill prose + plan schema field; runtime parser/verifier and ABORT-on-regression helper deferred to V2 with rationale. New doctrines: `qor/references/doctrine-feature-inventory.md` + `qor/references/doctrine-feature-tdd.md`. `qor/gates/schema/plan.schema.json` gains optional `feature_inventory_touches` field; `audit.schema.json` `findings_categories` enum gains `feature-test-undeclared`. SKILL prose: `/qor-plan` Step 5 declaration; `/qor-audit` Step 3 Feature Test Coverage Pass; `/qor-implement` Step 5 per-feature TDD layer + Step 12.5 FEATURE_INDEX update; `/qor-substantiate` Step 6 FEATURE_INDEX verification pass. 4 new glossary terms (Feature Inventory, Feature Inventory Touches, per-feature TDD, feature-test-undeclared). 15 new tests across 7 files. Plan: `docs/plan-qor-phase73-feature-inventory-tdd.md`. Gate artifacts at `.qor/gates/2026-05-14T2016-0a7b68/`. Previous phase -- Phase 72 sealed (feature v0.48.0, GH #56). Adds `/qor-plan` Step 2 Infrastructure Citation Inventory sub-section requiring grep-evidence statements paired with every Locked Decision citing sealed infrastructure (migration name, function signature, file:line, schema, env var, edge-function path). Canonical form: `git show <sealed-ref>:<path> | grep -nE '<pattern>' -> <exact observed text>`. Unverified citations are Open Questions, not LDs, and block submission to /qor-audit. Adds `/qor-audit` Step 3 Infrastructure Alignment Pass iter-N>1 full re-walk sub-section: on iter-N>1, Judge re-walks the FULL Locked Decision set (not diff-from-iter-N-1) and grep-verifies every sealed-infrastructure citation; missing inline grep-evidence triggers immediate VETO with `infrastructure-mismatch` category regardless of LD amendment status. Adds SG-CitationDrift-A doctrine entry catalogueing pattern + originating recurrence (Accountable-App `attribution-12g` 2026-05-13 iter-1->iter-3 chain) + P1+P2 countermeasures. 8 new tests across 3 files. Plan: `docs/plan-qor-phase72-sg-citation-drift-countermeasure.md`. Gate artifacts at `.qor/gates/2026-05-14T1958-dcd418/`. Lint-extension complement (P4 -- heuristic plan_grep_lint hook for sealed-infrastructure citation patterns) deferred to a future phase. Previous phase -- Phase 69 sealed (hotfix v0.47.3, GH #43). Adds `stall_walk.count_session_signature_totals` (per-signature counts across entire session audit history, non-consecutive) and `cycle_count_escalator.check_session_total` (surfaces escalation at K=3 cumulative). Runs alongside existing consecutive-streak `check`; both modes can fire independently with distinguishing `escalation_reason` ("cycle-count" vs "session-total"). `/qor-plan` Step 2c + `/qor-audit` Step 0.5 + doctrine §10.4 all updated. 11 new tests across 2 files. Plan: `docs/plan-qor-phase69-session-total-signature-escalator.md`. Gate artifacts at `.qor/gates/2026-05-14T1902-7b3e5d/`. Previous phase -- Phase 68 sealed (hotfix v0.47.2, GH #44 + #50). Previous phase -- Phase 67 sealed (hotfix v0.47.1, GH #42 + #45). Previous phase -- Phase 66 sealed (feature v0.47.0, GH #54 + #55). Previous phase -- Phase 65 sealed (hotfix v0.46.2, GH #57 + #53). Phase 64 prior -- (hotfix v0.46.1, GH #48). Three coupled fixes around the seal-integrity surface. (1) Wires the existing `qor/scripts/hash_guard.py` helpers into `/qor-substantiate` Step 6.8 (Seal Hash Integrity Gate). New Step 6.8 calls `require_toolkit_modules(("qor.scripts.ledger_hash", "qor.scripts.hash_guard"))` then `validate_sha256` on `merkle_seal`, `content_hash`, `previous_hash`, `chain_hash` before any hash value enters the SESSION SEAL entry body. Fail-closed: no override path, not governed by Phase 47 skip semantics. Step 6.8 carries a Preparation paragraph naming the canonical hash-producing helpers (`hash_guard.hash_file`, `ledger_hash.content_hash`, `ledger_hash.chain_hash`) operators invoke before the validation block runs. (2) Fixes pre-existing Phase-31-era import bug at `qor/scripts/doc_integrity.py:218`: bare `import doc_integrity_strict` -> package form `from qor.scripts import doc_integrity_strict`, unblocking `/qor-substantiate` Step 4.7 strict-mode execution. (3) `qor/references/doctrine-governance-enforcement.md` §13 documents the gate contract (toolkit modules, four validated labels, ABORT remediation guidance, OWASP LLM06 / NIST AI RMF MAP-3.1 / EU AI Act Art. 12 mapping). 5 substantiate-prose tests + 3 dist-variant tests + 3 doc_integrity strict-import regression tests = 11 phase-64 tests; suite at 1543 passing (1 pre-existing reconciliation-baseline failure unrelated to this phase, also pre-existing). Variants regenerated via `python -m qor.scripts.dist_compile`. Plan: `docs/plan-qor-phase64-seal-hash-substantiate-wiring.md`. Gate artifacts at `.qor/gates/2026-05-14T0030-552696/`. Previous phase -- Phase 55 sealed (feature). Third phase of a five-phase compliance sprint per `docs/research-brief-prompt-logic-frameworks-2026-04-30.md`. Closes Priority 3 (subagent least-privilege + model-pinning) plus the recurring-pattern advisory from Phase 53/54 audits via pre-audit lints. New `qor/policies/skill_admission.cedar` extended with two `forbid` rules over `actual_tool_invocations_exceed_scope` and `actual_subagent_invocations_exceed_scope`. New `compute_skill_admission_attributes` in `qor/policy/resource_attributes.py` with `_CANONICAL_TOOLS` frozenset (10 Tool names). 8 scoped skills declare `model_compatibility` + `min_model_capability` from ordered `(haiku, sonnet, opus)` tier set. New `qor/scripts/model_pinning_lint.py` (~135 LOC) wired at `/qor-plan` Step 0.3 (WARN-only). New CycloneDX v1.5 SBOM emitter `qor/scripts/sbom_emit.py` (~145 LOC, hand-rolled stdlib, zero new runtime deps); `qor-logic release sbom` CLI registered via new `qor/cli_handlers/release.py`. **`qor/gates/schema/deliver.schema.json` declared NEW** (closes long-standing surface gap where `qor-repo-release` wrote `phase="deliver"` artifacts that bypassed schema validation; `validate_gate_artifact.PHASES` extended with `"deliver"`). New `qor/scripts/plan_test_lint.py` + `plan_grep_lint.py` (pre-audit lints catching presence-only test descriptions and infrastructure-mismatch citations) wired at `/qor-audit` Step 0.6 + `/qor-repo-audit` Step 0.6 (WARN-only). SG-PreAuditLintGap-A appended to countermeasures doctrine documenting the cross-session recurring pattern. `qor/scripts/sprint_progress.py` extended with `sealed_priorities_from_ledger` that walks SESSION SEAL entries and recognizes "Bundles Priorities N, M, ..." patterns. 1104 tests passing twice in a row (deterministic, +67 from Phase 54). 3 new glossary terms (tool-scope policy, model-pinning frontmatter, CycloneDX SBOM). Sprint state: 5/5 priorities sealed post-Phase-55-seal. Previous phase -- Phase 54 sealed (feature). Second phase of a five-phase compliance sprint per `docs/research-brief-prompt-logic-frameworks-2026-04-30.md`. Closes Priorities 2 (AI provenance + AI Act/RMF doctrines + machine-readable transparency), 4 (path-currency cleanup folded earlier into Phase 53), and 5 (override-friction escalator). Bundles three priorities into one feature phase to reduce ceremony cost. New `qor/gates/schema/_provenance.schema.json` `$ref`'d from all six phase schemas declaring `{system, version, host, model_family, human_oversight, ts}`. New `qor/scripts/ai_provenance.py` (~140 LOC) with `build_manifest` + `HumanOversight` enum (`pass | veto | override | absent`); auto-derives `version` from `pyproject.toml`, `host` from `qor.scripts.qor_platform.current()`, `model_family` from `QOR_MODEL_FAMILY` env; warning suppressible via `QOR_PROVENANCE_QUIET=1`. CLI subcommand-handler split: NEW `qor/cli_handlers/{__init__,compliance.py}` (~110 LOC) hosts extracted `do_report` plus new `do_ai_provenance` and `do_sprint_progress`; `qor/cli.py` 227 LOC -> 186 LOC. `qor.scripts.validate_gate_artifact` extended with `referencing.Registry` to resolve cross-schema `$ref`. New doctrines: `doctrine-eu-ai-act.md` (Art. 9/10/12/13/14/15/50/72 mapping; Annex IV guidance; applicability classification asserts Qor-logic is *not* high-risk per Annex III) + `doctrine-ai-rmf.md` (GOVERN/MAP/MEASURE/MANAGE + AI 600-1 GenAI Profile §2.4/§2.7/§2.8/§2.10/§2.12). Plan schema `impact_assessment` block (5 required subfields when `high_risk_target: true`); new Step 1c "Impact assessment dialogue" in `/qor-plan`. `permitted_tools` + `permitted_subagents` advisory frontmatter on 6 SDLC + governance skills (declarative-only this phase; Phase 55 wires Cedar enforcement). New `qor/scripts/override_friction.py` (~80 LOC) with `OverrideFrictionRequired` exception (threshold = 3, symmetric with cycle-count escalator); `gate_chain.emit_gate_override` consults the friction module; 7 override-emitting skills handle the exception. `shadow_event.schema.json` `justification` field (minLength 50). Doctrine §12 added to `doctrine-governance-enforcement.md`. New `qor/scripts/sprint_progress.py` + `qor-logic compliance sprint-progress` CLI (reads latest research brief, walks ledger, emits per-Priority status). 1037 tests passing twice in a row (deterministic, +90 from Phase 53). 4 new glossary terms (AI provenance manifest, human-oversight signal, subagent tool scope, override-friction escalator). Self-application: this implement gate carries the first `ai_provenance` field in repo history (`{system: Qor-logic, version: 0.39.0, host: unknown, model_family: unknown, human_oversight: absent}`). Phase 53 historical fix landed mid-implement: seal commit amended (operator-authorized) to add canonical attribution trailer; tag `v0.39.0` recreated at new SHA; Merkle seal in Entry #174 unaffected. Sprint roadmap: Phases 55 (Cedar-enforced subagent admission + model-pinning + SBOM) and 56 (secret-scanning gate at substantiate) queued. Previous phase -- Phase 53 sealed (feature). First phase of a five-phase compliance sprint per `docs/research-brief-prompt-logic-frameworks-2026-04-30.md`. Closes OWASP LLM Top 10 (2025) **LLM01 Prompt Injection** (HIGH) at the audit-prose layer for operator-authored governance markdown surface; aligns with NIST AI 600-1 §2.7 and EU AI Act Art. 15 cybersecurity dimension. New `qor/scripts/prompt_injection_canaries.py` (frozen six-class catalog: instruction-redirect, role-redefinition, pass-coercion, meta-override, unicode-directionality, hidden-html); `scan(content)` API; argv-form CLI with `--mask-code-blocks` flag for documentation scanning. `/qor-audit` Step 3 Prompt Injection Pass runs before Security Pass; commit-time complement via fifth `forbid` rule on `Code::"governance"` resources in `qor/policies/owasp_enforcement.cedar`. New `qor/policy/resource_attributes.py` (`compute_governance_attributes`, `is_governance_path`) is the caller-side helper; evaluator unchanged. New doctrine `qor/references/doctrine-prompt-injection.md`. SG-PromptInjection-A appended to countermeasures. `prompt-injection` added to `findings_categories` enum. **OWASP (2021) LOW-4 closed**: `qor/reliability/intent_lock.py:_audit_has_pass` regex tightened from substring `re.search VERDICT.*PASS` to multiline-anchored canonical-line form. After Phase 53: zero residual OWASP (2021) MEDIUM/LOW findings open. **DRIFT-1 + DRIFT-2 closed**: full skill+agent tree sweep cleared `.failsafe/governance/` and `memory/failsafe-bridge.md` legacy references (4 skill files + 5 agent files). 30 source files touched; 947 tests passing twice in a row (deterministic, +37 from Phase 52). Three new glossary terms (prompt-injection canary, untrusted-data quarantine, instruction-anchor regex). Self-application Phase 4 verified: plan + brief + doctrine all scan clean once code-block masking is applied. Sprint roadmap: Phases 54 (AI provenance + AI Act doctrine), 55 (subagent least-privilege + model-pinning), 56 (secret-scanning gate), 57 (override-friction escalator) queued. Previous phase -- Phase 52 sealed (feature). First phase in repo history authored under proper /qor-plan + /qor-audit + /qor-implement + /qor-substantiate skill invocations with all four real `.qor/gates/<sid>/*.json` artifacts written. Three sub-phases: (1) **Structural enforcement (keystone)** — new `qor/reliability/gate_chain_completeness.py` (103 lines) walks SESSION SEAL ledger entries and asserts plan/audit/implement/substantiate gate artifacts exist for sealed phases ≥ 52; new `ProvenanceError` + `QOR_SKILL_ACTIVE` env-var binding on `gate_chain.write_gate_artifact()` refuses calls without skill provenance (`QOR_GATE_PROVENANCE_OPTIONAL=1` autouse fixture in `tests/conftest.py` for test compatibility). (2) **G-1 SSDF tag emission** — new `qor/scripts/ssdf_tagger.py` (99 lines) computes practice tags from `change_class` + `files_touched` (via `git diff --name-only`); `/qor-substantiate` Step 7.4 emits `**SSDF Practices**:` line into SESSION SEAL entry; new `gate-chain-completeness` job in `.github/workflows/ci.yml` blocks PR merges to main on missing gate artifacts. (3) **Retroactive remediation + SG promotion** — closes Phase 46 razor VETO (`tests/test_doctrine_test_functionality.py` split via `tests/_helpers.py` extraction; both files ≤250 lines), Phase 48 presence-only test VETO (`tests/test_install_drift_check_subprocess.py` replaces source-grep with subprocess invocation), Phase 49 self-exempting cutoff VETO (`tests/test_attribution_tiered_negative_paths.py` adds 6 fixture-based synthetic-violator tests); 3 narrative SG entries promoted to structured countermeasures (SG-SkillProtocolBypass, SG-VacuousLint, SG-RecursiveBashInjection). 13 new files + 10 modified; 69 phase-specific tests; 910 full suite passing twice (delta +44 from Phase 50's 866 baseline). Variants regenerated (236 files, no drift). SSDF tag emission self-applied: this seal entry carries `**SSDF Practices**: PO.1.3, PO.1.4, PS.2.1, PS.3.1, PW.1.1, PW.4.1, PW.5.1, RV.1.1, RV.1.2`. Forward-only emission; entries < #169 grandfathered (immutable Merkle chain). `gate_chain_completeness.check(phase_min=52)` returns `ok=True` for this session's all four gate artifacts. Previous phase -- Phase 50 sealed (feature). Closes G-2 from `docs/compliance-re-evaluation-2026-04-29.md`. Skill prose performing filesystem operations on operator-controlled identifiers (`.qor/session/current`) MUST cite the canonical validator helper (`qor.scripts.session.current()` which validates against `SESSION_ID_PATTERN`). `qor/references/doctrine-owasp-governance.md` §A03 gains a "Skill-prose worked example" paragraph; `/qor-help --stuck` Mode protocol step 1 routes through the helper; `qor-implement` Step 5.5 and `qor-substantiate` Step 4.6 bash one-liners updated from `cat .qor/session/current` to `python -c "from qor.scripts.session import current; print(current() or 'default')"`. New 5-test lint with proximity-anchor + strip-and-fail. 866 tests passing twice (delta +5). Phase 49 badge currency enforcement self-applied (passes). Previous phase -- Phase 49 sealed (feature). Closes G-3 and G-4 from `docs/compliance-re-evaluation-2026-04-29.md`. (1) **Tiered attribution policy**: `qor/references/doctrine-attribution.md` `## Tiered usage` table defines required form per surface (seal commit / plan-audit-implement commits / merge / PR description / CHANGELOG / GitHub release); new `qor.scripts.attribution.commit_trailer_compact()` helper. (2) **README badge currency enforcement**: new `qor/scripts/badge_currency.py` (140 lines, pure functions, CLI entrypoint); `/qor-substantiate` Step 6.5 promoted from WARN to ABORT for `change_class ∈ {feature, breaking}`; hotfix exempt. (3) Self-application clean: this seal cycle's Tests badge updated to 862 (truth) and the new currency check passes. 23 new tests (9 attribution-tiering + 8 badge-currency + 6 substantiate-wiring), each invoking the unit and asserting on output, paired with strip-and-fail negative-paths per Phase 46 doctrine. Phase 33 release-doc currency satisfied: CHANGELOG.md `## [0.36.0]` section with the canonical attribution line `_Built via [Qor-logic SDLC](url)._`; pyproject.toml at 0.36.0. 861 tests passing on two consecutive runs (delta +23). Variant artifacts regenerated; 236 files, no drift. Previous phase -- Phase 48 sealed (feature). Three coupled UX/install/discovery improvements. (A) **Script discoverability**: closes the Phase 35 gap that fixed only `qor/reliability/`; the three remaining `qor/scripts/` skill invocations (`qor-shadow-process` lines 89/101 + `qor-process-review-cycle` line 57) now use module form `python -m qor.scripts.<name>` so they resolve against the installed package from any CWD. `doctrine-governance-enforcement.md` §138 rewritten symmetric across both `qor/scripts/` and `qor/reliability/`; §92 prose example also updated. New lints `tests/test_installed_import_paths.py::test_no_path_form_qor_scripts_invocations` + `::test_no_path_form_qor_reliability_invocations` prevent regression. (B) **`qor-logic` canonical CLI**: `pyproject.toml` `[project.scripts]` declares both `qor-logic = "qor.cli:main"` (canonical) and `qorlogic = "qor.cli:main"` (backwards-compat alias entry point). `argparse prog="qor-logic"`; `--version` emits `qor-logic <semver>`. 51 operator-facing CLI invocations renamed across `qor/skills/`, `qor/references/`, `README.md`, `docs/operations.md`, `docs/policies.md`. Filesystem state paths (`.qorlogic/config.json`, `.qorlogic-installed.json`) preserved for operator data integrity (negative-lookbehind regex excludes them). New `tests/test_cli_rename.py` locks both entry points + program-name output via `tomllib.loads` + `cli.main(["--version"])` capsys capture + `cli.main(["--help"])` capsys capture. New skill-prose lint `test_skill_prose_uses_qor_logic_for_cli_invocations` with self-test `test_qorlogic_cli_regex_excludes_filesystem_state_paths`. (C) **`/qor-help` conversational**: skill evolves from static catalog into three-mode skill. Bare `/qor-help` shows intro ("How to use /qor-help") + ASCII SDLC flow chart (plain ASCII, verified via `body.encode('ascii')` round-trip) + catalog tables + "Using /qor-help" section. `/qor-help --stuck` reads `.qor/session/current` and globs `.qor/gates/<sid>/*.json` to infer SDLC position (rank order: research < plan < audit < implement < substantiate), reads audit verdict if present, recommends next skill with rationale per `doctrine-audit-report-language.md`. `/qor-help -- "<question>"` routes free-form question against catalog + state, identifies 1-3 relevant skills with rationale; LLM running the skill is the routing engine, catalog is single source of truth. All modes are read-only; "NEVER execute other skills" constraint preserved. `tests/test_qor_help_conversational.py`: 5 positive proximity-anchored assertions paired with 5 strip-and-fail negative-paths per Phase 46 doctrine; ASCII chart positionally verified for SDLC phase order (research before plan before audit before implement before substantiate). Phase 33 release-doc currency satisfied: `CHANGELOG.md ## [0.35.0]` section added with Added + Changed entries; `pyproject.toml` at 0.35.0; system-tier docs (`docs/operations.md`, `docs/policies.md`) refreshed for the rename. Variant artifacts regenerated via `python -m qor.scripts.dist_compile`; 236 files, no drift. 838 tests passing on two consecutive runs (delta +21 from Phase 47's 817 baseline). **Substantiate remediation**: original Phase 48 substantiate cycle landed seal commit without writing META_LEDGER entries (eighth instance of SG-AdjacentState-A bookkeeping-gap dimension). Remediation: this entry triplet (#158 audit, #159 implement, #160 seal) added retroactively against Phase 47 chain (`1eb7bb31...`); seal commit amended; tag `v0.35.0` recreated at amended commit. Phase 47 step 7.7 gate would have caught the gap had `/qor-substantiate` skill been invoked — manual seal bypassed the skill protocol. Pattern signal: skill protocols are load-bearing; manual short-circuits violate doctrine even when convenient. Previous phase -- Phase 47 sealed (feature). Adds the structural countermeasure for SG-AdjacentState-A's bookkeeping-gap class — the family that allowed Phase 46's first substantiate to seal at v0.33.0 without writing META_LEDGER entries. New: `qor/reliability/seal_entry_check.py` (128 lines) — pure-function helper exposing `check(ledger_path, phase_num)` returning `SealEntryResult(ok, errors)`. Reads the ledger, asserts the latest entry is a SESSION SEAL for the given phase, verifies the chain hash is internally consistent (`chain_hash == chain_hash(content_hash, previous_hash)`), then runs full chain verification via `ledger_hash.verify()`. Single source of truth = the ledger; no caller-supplied Merkle seal expectation. Wired into `/qor-substantiate` as new **Step 7.7 (Post-seal verification)** between Step 7.6 (Stamp CHANGELOG) and Step 8 (Cleanup Staging) — runs *after* Step 7 (Final Merkle Seal) writes the entry. Bash one-liner uses hardcoded `python -c` (no shell-variable interpolation into Python literals) calling `governance_helpers.current_phase_plan_path()` to derive the plan path; argv-form `--plan "$PLAN_PATH"` invocation throughout. 15 phase-47 tests added: 9 behavioral tests (`tests/test_seal_entry_check.py`) including the meta-test `test_check_replays_phase_46_original_gap` that proves the new gate would have caught the historical sixth-instance gap, plus `test_cli_rejects_path_with_shell_metacharacters_safely` confirming argv-form eliminates the OWASP A03 vector flagged in Pass 1 V-3; 6 defensive wiring tests (`tests/test_substantiate_seal_entry_wiring.py`) using the proximity-anchor + strip-and-fail pattern from Phase 46 doctrine, including direct countermeasures locking V-1 (post-Step-7 placement), V-2 (no `$MERKLE_SEAL` reference), V-3 (no `python -c "...'$VAR'..."` interpolation) against future drift. Substantiate dogfoods Phase 47: Step 7.7 runs against Phase 47's own seal entry as part of this seal cycle. Phase 47 took three audit passes to reach PASS — Phase 1 (helper + tests) was sound on first attempt; Phase 2 wiring (bash glue between helper and skill step) was the recurring failure point across all three passes (V-1/V-2/V-3 in Pass 1 plan, V-1 in Pass 2 plan). SG-AdjacentState-A pattern signal: directives that specify "use X" without specifying "how to obtain X" leave a wiring slip surface. Phase 33 release-doc currency satisfied: CHANGELOG.md `## [0.34.0]` section added; pyproject.toml at 0.34.0; README.md badges refreshed. Variant artifacts regenerated under `qor/dist/variants/`; 211 files, no drift. 817 tests passing on two consecutive runs (delta +15). Previous phase -- Phase 46 sealed (feature). Codifies the "test functionality, not presence" principle as a first-class doctrine and wires enforcement language into the four SDLC gate skills. New: `qor/references/doctrine-test-functionality.md` (Principle, Definitions, Rule with the acceptance question — "If the unit's behavior were silently broken but the artifact still existed, would this test fail?", Anti-patterns table citing SG-035 and the Phase 45 originating instance, Verification mechanisms, Update protocol). CLAUDE.md Authority line links the new doctrine alongside `attribution`. `/qor-plan` Step 4 forbids presence-only test descriptions; Step 5 review checklist requires each test description to name the behavior it confirms. `/qor-audit` gains a Test Functionality Pass between Section 4 Razor and Dependency Audit (VETO with `test-failure` category against any plan whose described tests do not invoke the unit). `/qor-implement` Step 5 (TDD-Light) requires the failing test invoke the unit and assert against its output; Step 9 scans newly-added tests for the `assert <substring> in <file_text>` family. `/qor-substantiate` Step 4 Test Audit refuses to seal if a phase-added test is presence-only. `tests/test_doctrine_test_functionality.py` locks each surface with proximity-anchored regex assertions paired with strip-and-fail negative-path tests so the doctrine test cannot itself decay into a presence-only check (every positive proximity assertion is paired with a corresponding negative-path test that proves stripping the named section makes the positive assertion fail). 20/20 doctrine tests green twice in a row. Variant artifacts regenerated under `qor/dist/variants/`. Substantiate remediation: Phase 46's original seal commit landed without META_LEDGER entries; this seal cycle adds Entry #150 (audit), #151 (implementation), #152 (seal) and rebases onto Phase 45 to compute correct chain hashes. Previous phase -- Phase 45 sealed (feature). Implements GitHub issue #18 — a documented convention for crediting Qor-logic SDLC in commit trailers, PR footers, and CHANGELOG attribution lines, plus a pure Python helper as the canonical source of the strings. New: `qor/scripts/attribution.py` (3 pure functions: `commit_trailer`, `pr_footer`, `changelog_attribution_line`; module-level constants are the single source of truth, kwargs override per-call), `qor/references/doctrine-attribution.md` (full doctrine including the narrowly-scoped emoji exception for bot-attribution trailer text), root `ATTRIBUTION.md` (one-screen quick-ref with copy-pasteable strings). CLAUDE.md Authority line updated. 15 phase-45 tests added: 10 unit/functionality (including a real `git interpret-trailers --parse` check that catches trailer-format drift presence-tests would miss) + 5 drift-guard tests asserting helper output appears verbatim across the doc surfaces. No skill wiring this phase by design (option B: doc + helper, defer wiring); follow-up Phase 46 will enforce test-functionality in Qor-logic's own SDLC skill prompts. Audit blind spot logged: Phase 45 audit cleared all six structural passes but missed two plan-format conventions (`change_class` enum, heading capitalization) that block the repo's own `tests/test_skill_doctrine.py` and `tests/test_plan_schema_ci_commands.py`; mid-implement plan corrections applied. 782 tests passing on two consecutive runs (delta +15). Previous phase -- Phase 44 sealed (hotfix). Resolves a Phase 41 regression: `qor/scripts/ledger_hash.py`'s strict `**Field**` anchor silently skipped SESSION SEAL entries with the standard `**Chain Hash (Merkle seal)**:` / `**Content Hash (session seal)**:` markup convention (7 ledger entries: #126, #129, #132, #133, #137, #140, #143). Three-regex relaxation adds optional parenthetical suffix `(?:\s*\([^)]+\))?` inside bold markers; preserves Phase 41's bold-anchor + bounded-span + two-form value protections. Anti-vacuous-green tests added: every modern (≥#116) entry with hash markup must verify; counts verified entries against the real ledger rather than relying on `rc == 0`. Verifier metric: pre-fix 104 OK / 39 skipped; post-fix 112 OK / 32 skipped. SG-AdjacentState-A (provisional family across Phase 41/42/43/44 plan blind spots) — fourth instance promotes the family to formal SG status; the anti-vacuous-green guard provides the structural countermeasure. Previous phase -- Phase 41 sealed (feature). Resolves GitHub issue #13. Three-axis scope: (1) `qor/scripts/ledger_hash.py` `CONTENT_HASH_RE` and `PREV_HASH_RE` now accept fenced `= <hex>` form (new capability, symmetric with `CHAIN_HASH_RE`); (2) all three regexes now require `**Field**` bold anchor and use a bounded non-greedy span via negative lookahead on the next `**FieldName**` marker (eliminates a class of cross-field-bleed accidents); (3) `qor-validate/SKILL.md` Steps 3/4/7 now reference `qor/scripts/ledger_hash.py` + `qorlogic verify-ledger` CLI instead of the stub `.claude/commands/scripts/validate-ledger.py` path. Phase 33 doctrine release-doc currency satisfied: CHANGELOG.md `## [0.31.0]` section + README.md badge refresh (Tests 602→752, Ledger 104→140). 8 new regression tests; 3 existing tests amended with `capsys`-based `OK   Entry #N:` assertions; new `tests/test_qor_validate_skill_references.py` lints source + dist variants. Intent-lock verified first-try post-implement-commit (Phase 43's ancestry fix working live). Previous phase -- Phase 43 sealed (hotfix). Replaces strict HEAD-equality check in `qor/reliability/intent_lock.py` `verify()` with `git merge-base --is-ancestor` ancestry check. Captured HEAD must be reachable from current HEAD; current HEAD may be any forward descendant. Plan-hash and audit-hash equality checks unchanged. Eliminates the re-capture-as-SOP anti-pattern observed in Phase 41 and Phase 42 substantiate where the implement commit between Step 5.5 capture and Step 4.6 verify always tripped `DRIFT: head`. Real anti-drift threats (history rewrites, hard resets, branch switches to divergent histories) still caught. SG-AdjacentState-A (provisional family) logged across Phase 41/42/43 Pass 1 plan-blind-spots — countermeasure becoming reflexive. Previous phase -- Phase 42 sealed (hotfix). Resolves the chicken-and-egg CI failure that blocked PRs #10 (v0.29.0) and #11 (v0.30.0). `test_every_changelog_section_has_tag` now exempts pre-release CHANGELOG sections — versions above the highest existing git tag — from the match-a-tag rule, breaking the collision with Phase 40's LOCAL-ONLY tag doctrine. Pure `_released_orphans(versions, tags)` helper extracted; three direct-call TDD tests cover above-highest / at-or-below-highest / no-tags cases. CHANGELOG.md backfilled with `## [0.28.1]` (Phase 40 retrospective) and `## [0.28.2]` (this hotfix) so the symmetric `test_every_tag_has_changelog_section` is satisfied against origin tags. Local orphan tags v0.29.0 and v0.30.0 (from unmerged phase 39/39b seals) deleted; will be recreated on respective merge commits. 716 tests passing on two consecutive runs. Previous phase -- Phase 33 sealed. Seal-tag timing bug (off-by-one across v0.19.0-v0.22.0) fixed — `governance_helpers.create_seal_tag` now takes a required `commit: str` positional; `/qor-substantiate` Step 7.5 reduced to `bump_version` only; new Step 9.5.5 captures the post-commit SHA via `git rev-parse HEAD` and tags it. Release-doc currency rule added (Phase 33 addition to Step 6.5): when `plan.change_class ∈ {feature, breaking}`, README.md and CHANGELOG.md must appear in `implement.files_touched`; hotfix exempt. SG-Phase33-A records the historical bug + countermeasure; META_LEDGER Entry #112 backfills the 4 affected-tag inventory (historical tags not retagged — rewriting published remote discouraged; no consumer depends on them). 636 tests passing on two consecutive runs (delta +14). First phase branch to start from a reconciliation-merge base (`git merge --no-ff v0.23.0` as Phase 33's first commit) to bring phase/32-amended content back into scope after the PR #4 auto-merge race published pre-amend content to main. Phase 32 prior -- Check Surface D + E are now LIVE STRICT at `/qor-substantiate` Step 4.7 -- any term-drift or cross-doc conflict ABORTs seal. Check Surface D + E are now LIVE STRICT at `/qor-substantiate` Step 4.7 -- any term-drift or cross-doc conflict ABORTs seal. Zero-drift baseline established in Phase 2 via `docs/*.md` archive-by-default scope-fence (only the 4 system-tier docs are living; README + CHANGELOG excluded as narrative entry points) plus broad `referenced_by:` adoption for high-usage terms. Install drift check (`qor/scripts/install_drift_check.py`) SHA256-compares source SKILL.md vs installed copies; invoked as CLI or at `/qor-plan` Step 0.2 as pre-phase WARN. Doctrine §8 Install Currency documents the contract. 622 tests passing on two consecutive runs (delta +20). Phase 32 is the first plan to substantiate under live strict-mode D/E and passed cleanly on first attempt -- the zero-drift baseline held. Previous phase --  Operationalization bundle closes 8 of the 10 items from the post-Phase-30 gap inventory. New machinery: `/qor-substantiate` Step 6.5 Documentation Currency Check (WARNs when doc-affecting changes ship without system-tier doc updates); Check Surface D/E scope-fence tuning (doctrine-peer + home-dir-peer + per-entry scope_exclude); `doc_integrity_drift_report.py` operator CLI; `pr_citation_lint.py` + `.github/workflows/pr-lint.yml` enforcing doctrine-governance-enforcement §6 on every PR; SHA256 install-sync test catching dist drift at CI time; session marker path unified (`MARKER_PATH` = `.qor/session/current`). Live drift triage artifact `docs/phase31-drift-triage-report.md` captures residual-known-drift state. Path-unification migration had a lossy moment at first Phase 31 substantiate attempt (old `.qor/current_session` vs new `.qor/session/current` marker files both exist with different contents; manual migration applied). 602 tests passing on two consecutive runs (delta +29). SG-Phase31-A (in-plan correction parallel to source instead of upstream fix) + SG-Phase31-B (plan self-modification post-audit) codified; both countermeasures applied live during pass-1 VETO -> pass-2 PASS amendment. First seal to exercise Step 6.5 against its own output -- caught 9 currency warnings, system-tier docs amended mid-substantiate.

## Authoritative source

All canonical Qor content lives under `qor/`. Variant outputs (`claude`, `kilo-code`, `codex`) are deferred until Phase 2 re-introduces the compile pipeline.

## File Tree

```
G:/MythologIQ/Qor-logic/
├── qor/                                   Single source of truth
│   ├── skills/
│   │   ├── governance/                    Gate & audit authority
│   │   │   ├── qor-audit/
│   │   │   ├── qor-validate/
│   │   │   ├── qor-substantiate/
│   │   │   ├── qor-shadow-process/        (stub — full impl deferred)
│   │   │   └── qor-governance-compliance/
│   │   ├── sdlc/                          Research → implement cycle
│   │   │   ├── qor-research/
│   │   │   ├── qor-plan/
│   │   │   ├── qor-implement/
│   │   │   ├── qor-refactor/
│   │   │   ├── qor-debug/
│   │   │   └── qor-remediate/             (stub — absorbs qor-course-correct)
│   │   ├── memory/                        State tracking & documentation
│   │   │   ├── qor-status/
│   │   │   ├── qor-document/
│   │   │   ├── qor-organize/
│   │   │   ├── log-decision.md
│   │   │   ├── track-shadow-genome.md
│   │   │   └── qor-docs-technical-writing/
│   │   ├── meta/                          Bootstrapping & repo management
│   │   │   ├── qor-bootstrap/
│   │   │   ├── qor-help/
│   │   │   ├── qor-repo-audit/
│   │   │   ├── qor-repo-release/
│   │   │   ├── qor-repo-scaffold/
│   │   │   ├── qor-meta-log-decision/
│   │   │   └── qor-meta-track-shadow/
│   │   └── custom/                        (reserved; empty until qor-scoped custom content identified)
│   │
│   ├── agents/
│   │   ├── governance/                    qor-governor, qor-judge
│   │   ├── sdlc/                          qor-specialist, qor-strategist, qor-fixer,
│   │   │                                  qor-ux-evaluator, project-planner
│   │   ├── memory/                        qor-technical-writer, documentation-scribe,
│   │   │                                  learning-capture
│   │   └── meta/                          agent-architect, system-architect, build-doctor
│   │
│   ├── vendor/
│   │   ├── agents/                        7 generic specialists + third-party/ (wshobson-agents)
│   │   └── skills/                        ~65 third-party skills (frameworks, integrations,
│   │                                      tauri/, chrome-devtools/, custom/, _system/, agents/)
│   │
│   ├── scripts/
│   │   ├── ledger_hash.py                 Content/chain hashing + manifest generation + verify
│   │   ├── calculate-session-seal.py      Session seal utility
│   │   ├── legacy/                        Pre-migration pipeline (process-skills.py,
│   │   │                                  compile-*.py, admit-skill.py, gate-skill-matrix.py,
│   │   │                                  intent-lock.py)
│   │   └── utilities/                     Assorted utility scripts
│   │
│   ├── references/                        Doctrine + patterns + qor-* examples
│   ├── experimental/                      Non-canonical research (tauri2-state, tauri-launcher, etc.)
│   └── templates/                         Doc templates (ARCHITECTURE_PLAN, CONCEPT, SYSTEM_STATE, etc.)
│
├── docs/
│   ├── META_LEDGER.md                     Hash-chained governance ledger (18 entries)
│   ├── SHADOW_GENOME.md                   Audit-verdict failure records (5 entries)
│   ├── PROCESS_SHADOW_GENOME.md           Process-level failure log (JSONL append-only)
│   ├── SYSTEM_STATE.md                    This file
│   ├── SKILL_REGISTRY.md                  Category-organized skill index
│   ├── ARCHITECTURE_PLAN.md
│   ├── BACKLOG.md
│   ├── CONCEPT.md
│   ├── SKILL_AUDIT_CHECKLIST.md
│   ├── Lessons-Learned/
│   ├── plan-qor-*.md                      Migration plan iterations (v1, v2, v3, final, minimal, deferred)
│   ├── migration-manifest-pre.json        Phase 1.5 pre-move manifest (2176 paths)
│   ├── migration-manifest-post.json       Phase 1.5 post-move manifest (1458 paths)
│   ├── MERKLE_ITERATION_GUIDE.md
│   ├── SHIELD_SELF_AUDIT.md
│   └── archive/2026-04-15/                Pre-migration snapshots (ingest, processed, compiled,
│                                          deployable_state, kilo-code)
│
├── .qor/                                  Runtime state (gitignored)
│   └── migration-discards.log             First-source-wins discard record
│
├── pyproject.toml                         Python 3.11+, pytest config, jsonschema runtime dep
├── .gitignore
└── README.md
```

## Ledger chain head

- Entry #169 SESSION SEAL — Phase 52 substantiated (v0.38.0; first seal with full gate-chain artifacts)
- Entry #166 SESSION SEAL — Phase 50 substantiated (v0.37.0)
- Chain hash: `c4a13570a901e26d5b971fff28e39f6b193b2915726b0565d2110b3285841b64`
- Entry #163 SESSION SEAL — Phase 49 substantiated (v0.36.0)
- Chain hash: `2d7fc8e5249c20c22141e63ec01d615e670637c5f280aa585ad2e3916945910a`
- Entry #160 SESSION SEAL — Phase 48 substantiated (v0.35.0)
- Entry #157 SESSION SEAL — Phase 47 substantiated (v0.34.0)
- Entry #152 SESSION SEAL — Phase 46 substantiated (v0.33.0)
- Verification: `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` → all sealable entries OK

## Shipped tooling

Compile pipeline, gate chain runtime, shadow threshold automation, cross-repo collector, platform detect, and validation suite were all shipped across Phases 10-23. Current tooling surface is operational:

- CLI: `qor-logic install|uninstall|list|init|info|compile|verify-ledger|seed|compliance|policy` (Phase 48: canonical name; `qorlogic` retained as backwards-compat alias)
- Python modules: `qor/seed.py`, `qor/tone.py`, `qor/install.py`, `qor/hosts.py`, `qor/scripts/veto_pattern.py`, `qor/scripts/gemini_variant.py`, `qor/scripts/dist_compile.py`, `qor/scripts/ledger_hash.py`, `qor/scripts/shadow_process.py`
- Tests: 462 passing (unit + integration + e2e + doctrine + bundle contract)
- Supported hosts: claude, kilo-code, codex, gemini (all with repo/global scope)
- Communication tiers: technical / standard / plain via `/qor-tone` or `qorlogic init --tone`
- Shadow Genome events: 7 structured `event_type` enum values (incl. `repeated_veto_pattern` from Phase 26)

## Advisory-gate overrides carried

One sev-1 `gate_override` event logged in `docs/PROCESS_SHADOW_GENOME.md` against the 5-round audit loop verdicts on the full plan. User-approved per `/qor-debug` analysis. Remaining violations (V-1..V-5) are addressed in `plan-qor-ssot-minimal.md` or explicitly carried as known risk.

## Phase 36 (v0.26.0 — 2026-04-20): two-stage addressed flip in /qor-remediate

Phase scoped to B19 only after a four-pass audit loop on the original Phase 36 plan (archived at `docs/plan-qor-phase36-planaudit-loop-countermeasures.archived.md`) surfaced V1-V10 across progressively deeper infrastructure-alignment mismatches. `/qor-remediate` Entry #122 proposal was accepted 2026-04-20; scope narrowed.

**Shipped**:
- Schema: `addressed_pending` optional field + `allOf` invariant (`shadow_event.schema.json`); `reviews_remediate_gate` optional field (`audit.schema.json`).
- Script: `remediate_mark_addressed.py` rewritten into two-stage API (`mark_addressed_pending` + `mark_addressed`) with `ReviewAttestationError`. 4 functions each under the Razor 40-line limit.
- Skills: `/qor-remediate` Step 4 calls pending variant; new Step 6 documents review-pass flip invoked from `/qor-audit`. `/qor-audit` Step 4.1 captures `reviews-remediate:<path>` operator arg; Step 4.2 invokes `mark_addressed` on PASS.
- Doctrine: §10.1 "Two-stage remediation flip," §10.2 "Narrative SG entry closure."
- Tests: `test_shadow_event_schema.py` NEW (5 tests); `test_remediate.py` +10 new + 3 existing updated to pending-stage API. 654 passed across 2 consecutive runs (delta +12).

**SG closures**:
- SG-PlanAuditLoop-A: partially closed. B19 ships the first countermeasure (advisory-until-reviewed enforced). C2-C4 (stall detection, cycle-count escalation, CI-command slot) deferred to Phase 37/38.
- SG-Phase36-A: active but not triggered in this phase (narrow B19 scope did not re-expose the specification-drift pattern).

**Deferred** (per BACKLOG post-Phase-35 queue):
- Phase 37: B20/B21 + gate artifact accumulation infrastructure. Plan authored at `docs/plan-qor-phase37-stall-detection-infrastructure.md` — unmerged, unreviewed.
- Phase 38: B22 `ci_commands` schema slot.
- Phase 39: context-discipline doctrine + persona context-prioritization reframe (research brief `.agent/staging/RESEARCH_BRIEF.md`; META_LEDGER #116).

## Phase 37 (v0.27.0 — 2026-04-20): stall-detection infrastructure (B20 + B21)

Closes C2-C4 countermeasures from SG-PlanAuditLoop-A. Phase 36 shipped B19 (two-stage addressed flip) as prerequisite; Phase 37 ships the full stall-detection machinery on append-only audit history.

**Shipped**:
- `qor/scripts/audit_history.py` NEW — append-only `.qor/gates/<sid>/audit_history.jsonl` alongside singleton. Solves V10 from original Phase 36 plan.
- `qor/scripts/findings_signature.py` NEW — 16-hex-char SHA256 prefix over sorted unique `findings_categories`; `"LEGACY"` sentinel for absent field; `UnmappedCategoryError` on non-enum.
- `qor/scripts/stall_walk.py` NEW — shared walker returning `(count, signature, first_match_ts)` for both escalator and classifier.
- `qor/scripts/cycle_count_escalator.py` NEW — K=3 orchestrator + session-scoped suppression marker.
- `qor/scripts/orchestration_override.py` NEW — severity-2 event + suppression marker.
- Schema: `audit.schema.json` `findings_categories` 12-value closed enum + `allOf` required-on-VETO; `shadow_event.schema.json` event_type +`plan-replay` +`orchestration_override`.
- Classifier: `remediate_pattern_match` gate-loop unions `gate_override | orchestration_override`; plan-replay pattern added with gate-loop dedup.
- Skills: `/qor-plan` Step 2c cycle-count hook; `/qor-audit` Step 0.5 cycle-count hook + new 7th Infrastructure Alignment Pass.
- Doctrine: §10.3 audit history + findings signature; §10.4 cycle-count escalation; §10.5 override + suppression; new `SG-InfrastructureMismatch` countermeasure in the catalog.
- Tests: 46 new across 8 new files + 5 new in `test_remediate` + 1 update in `test_audit_gate_artifact`. 705 passed x2.

**SG closures**:
- SG-PlanAuditLoop-A: **fully closed** (C1 Phase 36, C2-C4 Phase 37).
- SG-Phase36-A: active; authoring discipline held.
- SG-InfrastructureMismatch: codified in countermeasure catalog this phase.

**Procedural surface freeze line**: v0.28.0 (after Phase 38). Phase 39 (context-discipline / persona reshape) explicitly deferred pending upstream consumer lockdown.

## Phase 38 (v0.28.0 — 2026-04-20): ci_commands schema slot (B22) — **FREEZE LINE**

Trivial scope: one schema field + one skill template section + one 6-test file. Establishes v0.28.0 as the procedural-surface freeze line per user direction for upstream consumer lockdown.

**Shipped**:
- `qor/gates/schema/plan.schema.json` — `ci_commands` required array (minItems 1, item minLength 1).
- `qor/skills/sdlc/qor-plan/SKILL.md` §Plan Structure — new `## CI Commands` template section + Phase 38 contract note.
- `tests/test_plan_schema_ci_commands.py` NEW (6 tests covering required-field enforcement, empty-array rejection, empty-string rejection, valid-case acceptance, skill-prose lint, grandfathering for pre-Phase-38 markdown plans).
- 9 existing plan-payload test fixtures updated to include `ci_commands` (payloads represent Phase-38-era consumers).
- `CHANGELOG.md` v0.27.0 section authored (Phase 37 debt).

**Procedural surface frozen**:
- Skill protocols (qor-plan/audit/remediate/implement/substantiate) — stable
- Event-type enum (9 values) — stable
- Gate-artifact schemas (plan + ci_commands now required, audit + findings_categories/reviews_remediate_gate, shadow_event + addressed_pending) — stable
- Findings categories enum (12 values) — stable
- Delegation table (108 handoffs) — stable
- Doctrine §10.1-10.5 — stable

**Deferred beyond freeze**:
- Phase 39: context-discipline doctrine + persona reshape (~30 skill files, M4 A/B harness). Explicitly out of scope pending upstream consumer lockdown against v0.28.0.

## Phase 39 Phases 1+2 (v0.29.0 — 2026-04-20): context-discipline doctrine + A/B harness infrastructure

Partial phase seal. Phases 1 and 2 of the 4-phase plan ship in v0.29.0; Phases 3 (live A/B run) and 4 (persona sweep + conditional Identity Activation rewrites) deferred to a separate operator-driven cycle.

**Phase 1 shipped** — doctrine codification:
- `qor/references/doctrine-context-discipline.md` NEW. 5 sections: three-mechanism distinction (frontmatter tag vs Identity Activation prose vs subagent invocation), persona-as-context-prioritization-scaffold rule, stance directive discipline, subagent invocation rule (`general` by default; persona-typed requires evidence), verification protocol requiring `<persona-evidence>` pointers.
- `qor/references/doctrine-governance-enforcement.md` §11 cross-reference.
- `tests/test_doctrine_context_discipline.py` — 3 structural tests.

**Phase 2 shipped** — A/B harness infrastructure (Anthropic SDK):
- `qor/scripts/ab_harness.py` — pure library (5 public functions + helpers), mockable, never reads env. `load_manifest`, `load_variant`, `score_response`, `run(variant, skill, client, ...)`, `compare`, `aggregate_runs`.
- `qor/scripts/ab_live_run.py` — operator CLI. Reads `ANTHROPIC_API_KEY`; exits clearly if absent; builds real `anthropic.Anthropic()` client; runs 2 skills × 2 variants × 5 runs × 20 defects = 400 API calls.
- `tests/fixtures/ab_corpus/` — 20 seeded defects across 10 `findings_categories` (2 per category, omitting `coverage-gap` and `dependency-unjustified` per plan). Each fixture carries `# SEEDED TEST DEFECT — NOT EXECUTABLE` header. `MANIFEST.json` uses `line_start` + `line_end` fields for multi-line defect ranges.
- `tests/fixtures/ab_corpus/variants/` — 4 hand-authored Identity Activation variant files (`qor-audit.persona.md`, `qor-audit.stance.md`, `qor-substantiate.persona.md`, `qor-substantiate.stance.md`).
- `pyproject.toml` — `anthropic>=0.40,<1.0` under `[project.optional-dependencies].ab-harness`. Default installs do not pull this dependency.
- `tests/test_ab_harness.py` — 16 CI tests, all Anthropic calls mocked.

**Phase 39b Phase 3 status**: dropped. The originally-planned operator action (invoke `/qor-ab-run` with `ANTHROPIC_API_KEY` to produce `docs/phase39-ab-results.md`, ~$32/cycle external spend) is no longer scheduled. Phase 39b Phases 1+2 shipped the infrastructure (skill, aggregator, fixtures, persona sweep S3+R4+R5) and stand on their own. The R3 conditional rewrite mechanism that gated on results-file existence has been removed (Phase 59 cleanup).

**Cost awareness (corrected from Pass 2 audit O1)**: actual skill body sizes are ~4,000-4,500 tokens each, not the plan's original ~500-token per-call assumption. Real cost ~$32 per full A/B cycle at Opus 4.7 pricing. Codified in `ab_harness.py` module docstring.

## Phase 39b Phases 1+2 (v0.30.0 — 2026-04-20): Agent Team A/B + persona sweep

Supersedes the v0.29.0 anthropic-SDK approach. Ships:
- `/qor-ab-run` skill orchestrating A/B via parallel Task-tool subagent dispatch (20 concurrent calls, zero external dep, aligned with doctrine §4 subagent invocation rule).
- `qor/scripts/ab_aggregator.py` pure-Python reducer: brace-balanced JSON extraction, malformed-tolerant, mean+stddev, winner declaration (±5pp tie threshold), markdown rendering.
- Subagent prompt template with `{VARIANT_IDENTITY_ACTIVATION_BLOCK}` + `{FIXTURES_CONCATENATED}` placeholders.
- Delegation-table + `/qor-help` catalog entries.

**Persona sweep applied**:
- **S3**: 5 decorative `<persona>` tags removed (`qor-status`, `qor-help`, `qor-repo-scaffold`, `qor-bootstrap`, `qor-document`).
- **R4**: `qor-debug` line 108 subagent_type constraint cross-references `doctrine-context-discipline.md` §4.
- **R5**: `qor-document` splits Identity Activation stance (main thread) from subagent pairing (`Task` dispatch) citing doctrine §1.2/§1.3.
- **LOAD_BEARING_PENDING_EVIDENCE registry** (20 skills incl. Phase 59 `qor-ideate`): documents skills retained as load-bearing by doctrine judgment.

**Tests**: 743 pytest green × 2. Admission: `qor-ab-run` admitted. Matrix: 29 skills, 112 handoffs, 0 broken.

**Naming note**: branch `phase/39b-*` + plan `plan-qor-phase39b-*.md` use letter-suffix convention not supported by `governance_helpers._BRANCH_PHASE_RE` + `_PHASE_FILENAME_RE` (digit-only). Version bump performed manually (0.29.0 → 0.30.0). Future sub-phases should use next digit (e.g., phase/41) to remain compatible with automated bump.

## Phase 41 (v0.31.0): build-and-publish workflow + Phase 40 doctrine

Ledger Entry #143. Annotated tags created LOCAL ONLY until PR merge per Phase 40 doctrine to prevent stale-tag publishing. Build-and-publish workflow refuses to publish tags not reachable from main (Phase 40 guard).

## Phase 45 (v0.32.0): attribution-trailer convention

Ledger Entry #149. Canonical full trailer for seal commits + compact `Co-Authored-By:` for plan/audit/implement commits. `qor/scripts/attribution.py` `commit_trailer()` / `commit_trailer_compact()` / `pr_footer()` / `changelog_attribution_line()` helpers. Locked by `tests/test_attribution_tiered_usage.py`.

## Phase 46 (v0.33.0): test-functionality doctrine

Ledger Entry #152. Doctrine `qor/references/doctrine-test-functionality.md` requires unit tests to invoke the unit and assert on output, not artifact existence. SG-035 ("doctrine-content test unanchored") codified. /qor-audit Test Functionality Pass added.

## Phase 47 (v0.34.0): seal-entry-check at substantiate

Ledger Entry #157. New reliability gate at substantiate Step 7.7 verifies SESSION SEAL entry was actually written (closes SG-AdjacentState-A bookkeeping-gap subclass). Substantiate cycles cannot complete without writing the SESSION SEAL ledger entry.

## Phase 48 (v0.35.0): governance-enforcement doctrine §10 expansions

Ledger Entry #160. Doctrine `qor/references/doctrine-governance-enforcement.md` extended with §10.1 (two-stage remediation flip), §10.2 (SG narrative closure protocol), §10.3-10.5 (cycle-count escalation + orchestration-override + gate-loop classifier). Subagent invocation rule clarified.

## Phase 49 (v0.36.0): Phase 11D + Phase 28 documentation integrity strict mode

Ledger Entry #163. /qor-substantiate Step 4.7 runs `doc_integrity.run_all_checks_from_plan` strict mode; ABORTs on `ValueError`. `legacy` doc_tier bypasses checks. Topology + glossary + orphan checks enforced at seal time.

## Phase 50 (v0.37.0): co-occurrence behavior invariant model

Ledger Entry #166. Test pattern: instead of substring grep for "test K invokes M", parse the AST/frontmatter and assert "for every SKILL.md whose phase: X, body MUST contain invocation Y". Anchored to actual frontmatter-declaration set; not single-skill substring. Phase 50 model used by all subsequent phases.

## Phase 52 (v0.38.0): provenance binding for write_gate_artifact

Ledger Entry #169. `gate_chain.write_gate_artifact` refuses writes from contexts that have not declared `QOR_SKILL_ACTIVE=<phase>` env var. Closes the bypass surface that allowed Phases 46/48/49/50 to silently land defective work. `QOR_GATE_PROVENANCE_OPTIONAL=1` test-only bypass; autouse fixture in conftest.py sets it.

## Phase 53 (v0.39.0): OWASP LLM01 prompt-injection canary scanner

Ledger Entry #174. `qor/scripts/prompt_injection_canaries.py` (~155 LOC) scans operator-authored governance markdown (docs/, qor/references/) for canary patterns before any other audit pass. /qor-audit Step 3 Prompt Injection Pass invokes; canary hit → VETO with `prompt-injection` category. New `compute_governance_attributes` driver for Cedar `forbid has_prompt_injection_canary` rule. SG-PromptInjection-A codified.

## Phase 54 (v0.40.0): EU AI Act + AI RMF alignment

Ledger Entry #178. `ai_provenance` field on every gate artifact (system, version, host, model_family, human_oversight, ts). `qor/scripts/ai_provenance.py` (~140 LOC) builds manifests; `qor/scripts/override_friction.py` requires ≥50-char justification on third consecutive override. New `qor/references/doctrine-eu-ai-act.md` + `doctrine-ai-rmf.md`. `qor-logic compliance ai-provenance` aggregator. Closes EU AI Act Art. 13/14/50 + NIST AI RMF MEASURE-2.1 / MANAGE-1.1.

## Phase 55 (v0.41.0): Cedar admission + model-pinning + CycloneDX SBOM + pre-audit lints + deliver schema

Ledger Entry #182. Two new `forbid` rules in `qor/policies/skill_admission.cedar` over `actual_tool_invocations_exceed_scope` + `actual_subagent_invocations_exceed_scope`. New `compute_skill_admission_attributes` + `_CANONICAL_TOOLS` frozenset. 8 scoped skills declare `model_compatibility:` + `min_model_capability:`. New `qor/scripts/sbom_emit.py` (~145 LOC, hand-rolled CycloneDX v1.5, zero new deps). New `qor/cli_handlers/release.py` `do_sbom`. New `qor/gates/schema/deliver.schema.json` closes pre-existing surface gap. New `qor/scripts/plan_test_lint.py` + `plan_grep_lint.py` pre-audit lints at /qor-audit Step 0.6. SG-PreAuditLintGap-A codified. Closes OWASP LLM05 + LLM07 + AI RMF GV-6.1 + MG-3.1.

## Phase 56 (v0.42.0): secret-scanning gate at /qor-substantiate Step 4.6.5

Ledger Entry #185. `qor/scripts/secret_scanner.py` (~248 LOC, 11-pattern frozen catalog, 15-entry `_ALLOWLIST`, gitleaks v8 schema findings JSON, redacted match form). New `compute_production_attributes` drives long-dormant Cedar `has_hardcoded_secrets` attribute (rule on books since Phase 23). /qor-substantiate Step 4.6.5 invokes `python -m qor.scripts.secret_scanner --staged --out dist/secrets.findings.json || ABORT`. SG-SecretLeakAtSeal-A codified. Closes OWASP LLM06 + NIST AI 600-1 §2.10. Five-phase compliance sprint complete.

## Phase 57 (v0.43.0 — 2026-05-01): `gate_written` observer channel (PR #12 + B24 reintegration)

Reintegrates PR #12 `feat/b24-gate-written-hooks` (FailSafe-Pro B24 contribution, opened 2026-04-20) on top of current main with the OWASP A04 SIGINT-swallow VETO ground from Entry #186 explicitly resolved. Net-new public-API surface for downstream governance-ledger bridges to observe gate writes without filesystem polling. Aligns with OWASP LLM Top 10 (2025) **LLM07 Insecure Plugin Design** at the contract layer.

**Phase 1 — `gate_hooks` module**:
- `qor/scripts/gate_hooks.py` (165 LOC, zero new runtime deps; PyYAML already locked).
- Frozen `GateWrittenEvent(phase, session_id, artifact_path, payload_sha256, ts)` and `_HookTarget` dataclasses.
- `dispatch_gate_written(event)` synchronous fan-out: entry-points (under group `qor_logic.events.gate_written`) first, then `<root>/.qor/hooks.yaml` config-file entries (top-to-bottom). Deterministic ordering; no concurrency.
- `reload_entry_points()` test-only cache invalidator.
- JSONL hook-log at `<root>/.qor/hooks/hooks.log` (ts, hook, event, status, duration_ms, [exception]).
- **Critical Phase 57 fix**: `except Exception` (NOT `BaseException`) in `_invoke_hook_safely`. `KeyboardInterrupt` and `SystemExit` propagate so operators retain Ctrl-C control over runaway hooks.

**Phase 2 — `gate_chain` post-write hook fire**:
- `qor/scripts/gate_chain.py:_fire_gate_written_hook` (15-line bridging helper).
- Fires AFTER Phase 52 provenance check, AFTER `vga.write_artifact`, AFTER Phase 37 `audit_history.append`, BEFORE function return.
- Reads artifact bytes back from disk to compute `payload_sha256` so the event matches what's persisted (no in-memory/on-disk drift).
- Wrapped in `try/except Exception` so hook errors never break the authoritative write path.

**Phase 3 — doctrine + glossary + countermeasure + CHANGELOG**:
- `qor/references/doctrine-hook-contract.md` (NEW, ~95 LOC): applicability + event payload + entry-point + config-file format + invocation order + log format + trust model + performance + Phase 57 changes vs. PR #12 origin.
- `qor/references/doctrine-shadow-genome-countermeasures.md` extended with `SG-BareExceptionSwallowsSignals-A` codifying the BaseException-swallow risk class with corrected `except Exception` and cleanup-then-reraise patterns.
- `qor/references/glossary.md` extended with 2 new terms: `gate_written hook`, `hook contract`.
- CHANGELOG `[0.43.0] - 2026-05-01` entry.
- README badges: Tests 1142 → 1176, Doctrines 20 → 21, Ledger 188 → 190.

**Trust model**: hooks execute arbitrary code from the consumer's repo. Mirrors `.github/workflows/`, `.pre-commit-config.yaml`, `Makefile`, npm `preinstall`. Documented explicitly in `qor/references/doctrine-hook-contract.md`; qor-logic does NOT sandbox, sign, or vet hooks.

**Tests**: 1175 pytest passing × 2 (deterministic). +34 new Phase 57 tests including AST-anchored static check that `_invoke_hook_safely` never catches `BaseException`, behavioral regression that `KeyboardInterrupt` and `SystemExit` propagate through dispatch, Phase 50 AST-based co-occurrence behavior invariant for the `gate_chain` ↔ `gate_hooks` wiring, Phase 52 provenance-still-enforced regression.

**Reliability sweep**: intent-lock VERIFIED, skill admission ADMITTED, gate-skill matrix 29 skills/112 handoffs/0 broken, secret-scan EXIT 0 (Phase 56 substantiate Step 4.6.5 self-application clean), dist 4 variants OK (236 files, no drift), badge currency OK.

**Razor compliance**: `gate_hooks.py` 165 LOC (under 250 cap); longest function `_resolve_config_entry` ~22 LOC; max nesting depth 2; zero nested ternaries.

**Resolves Entry #186 VETO grounds explicitly**:
1. ✅ `except Exception` (not `BaseException`) — SIGINT/SystemExit propagate; AST-anchored regression test in place.
2. ✅ Built on top of current main (`d5726e9` post-Phase-56), not a stale-branch merge.
3. ✅ Module docstring cites Phase 57 + LLM07 framework gap; FailSafe-Pro origin attribution moves to CHANGELOG per Phase 53/54/55/56 docstring discipline.

**Companion**: Phase 58 plan + audit gate artifact (`docs/plan-qor-phase58-ideation-readiness-phase.md`, Issue #20 `/qor-ideate`) committed alongside this seal as governance records (audit PASS at Entry #188). Phase 58 implementation can proceed independently after this PR merges.

**Decision**: Phase 57 sealed at v0.43.0. PR #12 superseded by this seal; close after merge with link to Entry #190. FailSafe-Pro `failsafe-qor-hook` consumer (their B24 PR) can register under `qor_logic.events.gate_written` and observe governance writes without filesystem polling.

## Phase 58 (v0.44.0 — 2026-05-02): procedural-fidelity check + tech-debt wrap-up (B23 closure)

Closes B23 (operator request from Phase 57 substantiate cycle where doc-surface gaps were caught manually) by shipping a static-analysis procedural-fidelity check at /qor-substantiate Step 4.6.6 with WARN-posture severity-2 events to the Process Shadow Genome. Plus three tech-debt wrap-up items: SYSTEM_STATE.md backfill for 12 sealed phases (41, 45-50, 52-56) with forward-only drift-prevention test, conftest.py session-end cleanup of `.qor/gates/test*` pollution, and Phase 58→59 ideation plan rename (Issue #20 ideation moves to Phase 59 since the Phase 58 slot is now this tech-debt scope). Codifies `SG-DocSurfaceUncovered-A` countermeasure.

**Phase 1 — `procedural_fidelity` module + substantiate Step 4.6.6 wiring**:
- `qor/scripts/procedural_fidelity.py` (~190 LOC, zero new runtime deps).
- Frozen `Deviation` dataclass + `DEVIATION_CLASSES` frozenset (4 v1 classes: `doc-surface-uncovered` active, `missing-step` / `ordering-drift` / `argv-shape-divergence` reserved as stubs).
- `check_seal_commit(repo_root, session_id)` reads `.qor/gates/<sid>/implement.json` `files_touched` and runs detectors. Empty list = clean.
- `_detect_doc_surface_coverage` is the v1 detector: `qor/skills/`, `qor/scripts/`, `qor/references/doctrine-`, or `qor/gates/schema/` paths in `files_touched` require at least one of the four system-tier docs (`docs/SYSTEM_STATE.md`, `docs/operations.md`, `docs/architecture.md`, `docs/lifecycle.md`).
- CLI: `python -m qor.scripts.procedural_fidelity --session SID [--repo-root .] [--out PATH]`. Exit 0 always (WARN posture); stderr WARN on deviations; exit 2 only on missing implement gate. Severity-2 events to Process Shadow Genome via `shadow_process.append_event`.
- Substantiate Step 4.6.6 between existing Step 4.6.5 (Phase 56 secret-scan, BLOCK semantics) and Step 4.7 (Phase 28 doc-integrity, ABORT). WARN-only invocation; no `|| ABORT`.

**Phase 2 — SYSTEM_STATE.md backfill + drift prevention**:
- 12 sealed phases backfilled: 41 (v0.31.0), 45 (v0.32.0), 46 (v0.33.0), 47 (v0.34.0), 48 (v0.35.0), 49 (v0.36.0), 50 (v0.37.0), 52 (v0.38.0), 53 (v0.39.0), 54 (v0.40.0), 55 (v0.41.0), 56 (v0.42.0). One concise paragraph per phase extracted from corresponding META_LEDGER seal entry.
- New `tests/test_system_state_phase_coverage.py` enforces forward-only invariant: every `### Entry #N: SESSION SEAL -- Phase X feature substantiated` ledger entry must have a corresponding `## Phase X (vY.Z.W)` heading in SYSTEM_STATE.md, modulo `_NO_SEAL_PHASES = {42, 43, 44, 51}` for adjacent-work-absorbed phases.
- Meta-coherence: this very Phase 58 entry is required by the test the same phase ships. Drift-prevention dogfooded.

**Phase 3 — conftest cleanup + ideation rename + doctrine + glossary + SG + CHANGELOG**:
- `tests/conftest.py`: new session-scope autouse cleanup fixture sweeping `.qor/gates/test*`, `cli-*`, `tN` pollution at session-end. Pattern conservative; never matches timestamp-prefixed real session IDs.
- `docs/plan-qor-phase58-ideation-readiness-phase.md` → `docs/plan-qor-phase59-ideation-readiness-phase.md` rename. Plan body Phase 58 → Phase 59 substring updates (19 occurrences).
- `qor/references/doctrine-procedural-fidelity.md` (NEW, ~95 LOC): applicability + four-class catalog + doc-surface coverage rule + operator workflow + Phase 58 changes vs. ad-hoc operator review + future extensions.
- `qor/references/doctrine-shadow-genome-countermeasures.md`: appended `SG-DocSurfaceUncovered-A` codifying documentation-update gap risk class with Phase 57 source incident.
- `qor/references/glossary.md`: 3 new terms (`procedural-fidelity check`, `procedural deviation`, `doc-surface coverage`) all with `home: qor/references/doctrine-procedural-fidelity.md` + `introduced_in_plan: phase58-procedural-fidelity-and-tech-debt-wrapup`.
- `docs/BACKLOG.md`: B23 marked `[x] (v0.44.0 — Complete)`.

**Substantiate-time meta-coherence enforcement**: Step 4.6.6 ran against Phase 58's own seal commit's `files_touched` set — `dist/procedural-fidelity.findings.json` empty (`[]`), EXIT 0. The Phase 58 plan dogfoods its own contract: skill body + script + doctrine + schema-adjacent changes all matched against `docs/SYSTEM_STATE.md` update (12-phase backfill) → at-least-one threshold satisfied → no deviation.

**Tests**: 1202 passing × 2 (deterministic). +27 new Phase 58 tests including AST-anchored substantiate-skill wiring invariant, doctrine round-trip integrity, conftest fixture introspection, glossary round-trip, Phase 59 ideation-rename regression, meta-coherence self-application.

**Reliability sweep**: intent-lock VERIFIED, skill admission ADMITTED, gate-skill matrix 29/112/0, secret-scan EXIT 0, procedural-fidelity EXIT 0, dist 4 variants OK (236 files), badge currency OK.

**Razor compliance**: `procedural_fidelity.py` 190 LOC (under 250 cap); longest function ~22 LOC; max nesting 2; zero nested ternaries.

**Decision**: Phase 58 sealed at v0.44.0. B23 fully closed. Pre-Phase-58 SYSTEM_STATE drift remediated; forward-only invariant enforced. Test pollution structurally prevented. Issue #20 ideation moved to Phase 59 ready for independent implementation. The Phase 57-style "operator caught the doc-surface gap manually" failure mode is now structurally surfaced at substantiate-time via `SG-DocSurfaceUncovered-A` countermeasure.

## Phase 59 (v0.45.0 — 2026-05-02): `/qor-ideate` ideation readiness phase (Issue #20)

Closes Issue #20 (governed ideation readiness phase) by introducing `/qor-ideate` as an optional pre-research SDLC phase. Captures intent and assumptions before they become inferred by downstream agents. Codifies `SG-PrematureSolutioning-A` countermeasure. Advisory-gate posture matching Phase 8: hotfixes MAY skip ideation; `/qor-research` and `/qor-plan` accept either ideation OR research as their prior artifact.

**Phase 1 — Ideation gate-artifact schema**:
- `qor/gates/schema/ideation.schema.json` (NEW): required envelope + 6 required content sections (`spark`, `problem_frame`, `transformation_statement`, `boundaries`, `governance_profile`, `readiness`) + 3 optional (`assumptions`, `options`, `failure_remediation`). Closed enums for `readiness.status`, `governance_profile.risk_grade`, `failure_remediation[].return_phase`.
- `qor/scripts/validate_gate_artifact.py` `PHASES` extended with `"ideation"`.

**Phase 2 — `/qor-ideate` skill + dialogue protocol + gate-chain extension**:
- `qor/skills/sdlc/qor-ideate/SKILL.md` (NEW, ~120 LOC) + `references/dialogue-protocol.md` (NEW, ~150 LOC).
- `qor/scripts/gate_chain.py:_check_ideation_predecessor` recognizes `ideation.json` as a valid prior for `/qor-research` and `/qor-plan`. Backward-compatible.
- `qor/gates/delegation-table.md`: 5 new rows for `qor-ideate` routing.
- `qor/gates/chain.md`: chain visualization extended with `(ideate?)` as optional pre-research phase.
- `qor/skills/meta/qor-help/SKILL.md`: catalog row added.

**Phase 3 — doctrine + glossary + SG + CHANGELOG**:
- `qor/references/doctrine-ideation-readiness.md` (NEW, ~140 LOC): 10-section catalog + readiness scoring model + routing matrix + 8-failure-mode catalog (Premature Solutioning / Language Drift / Assumption Laundering / Scope Seepage / Research Asymmetry / Failure Blindness / Premature Decomposition / Validation Collapse).
- `SG-PrematureSolutioning-A` in `doctrine-shadow-genome-countermeasures.md`.
- 6 new glossary terms.

**Tests**: 1237 passing × 2 (deterministic). +35 new Phase 59 tests. Skill registry: 30 skills (was 29). Handoff matrix: 115 handoffs (was 112; +3 from qor-ideate routes), 0 broken. Dist: 243 files (was 236; +7 for qor-ideate across 4 variants).

**Reliability sweep**: intent-lock VERIFIED, skill admission ADMITTED, gate-skill matrix 30/115/0, dist drift OK, badge currency OK.

**Razor compliance**: zero new `.py` modules; gate_chain.py extension `_check_ideation_predecessor` is 14 LOC. Within bounds.

**Decision**: Phase 59 sealed at v0.45.0. Issue #20 fully closed. Ideation is now a first-class auditable SDLC phase with structural guards against the 8 canonical unraveling points. Advisory-gate posture preserves backward compatibility; existing flows continue to work without ideation.

## Phase 60 (v0.46.0 — 2026-05-11): session reconciliation consolidated (Phase 63 closing seal)

Reconciles a divergent local session work-stream (originally numbered Phase 45 through Phase 61 plus two hotfixes; locally sealed at v0.45.0-v0.59.0 + v0.54.1 + v0.58.1) onto canonical upstream (`origin/main` at Phase 59 ideate, v0.45.0). Path B (consolidated reconciliation) chosen per the new `qor/references/doctrine-governance-enforcement.md` §10.10 because session and upstream had independently evolved shared governance surfaces (qor-audit, qor-substantiate, qor-implement, qor-plan SKILLs plus governance/documentation/shadow-genome doctrines), making per-phase replay impractical without merge-domain judgment on every shared file.

**Consolidated session-NEW deliverables imported into this Phase 60 commit**:
- `qor/compiler/` package (prompt compiler V1-V4 chain): PromptIR, ProviderCompiler protocol, AnthropicCompiler, governance gate, rulepack registry, execution modes, evaluation loop, intent parser.
- `qor/capabilities/` package: KNOWN_CAPABILITIES inventory, governance context packet builder, risk routing, verification-request artifact emitter.
- 11 NEW `qor/scripts/` modules: `path_match`, `audit_triggers`, `hash_guard`, `ledger_entry_id`, `ledger_fragment`, `meta_ledger_walker`, `host_capability`, `pipeline_inversion_lint`, `plan_text_consistency_lint`, `feature_index_verify` (note: upstream Phase 56's `secret_scanner` is canonical; session's parallel implementation deferred).
- 4 NEW doctrines: feature-inventory, feature-tdd, host-repo-posture, prompt-compilation.
- 5 NEW gate schemas: capability_inventory, feature_index, governance_context, risk_routing, verification_request.
- ~50 functionality tests for the imported surfaces.
- 20 historical plan + roadmap docs (forensic record).
- `qor capabilities {inventory,context,route-risk,verification-request}` CLI subcommand (surgically added; upstream's qor-logic rename + release/compliance/policy subcommands preserved).

**Intentionally dropped surfaces** (upstream's parallel evolution is canonical): all session-side edits to `qor-audit`, `qor-substantiate`, `qor-implement`, `qor-plan`, `qor-debug` SKILLs; all session-side edits to `doctrine-governance-enforcement.md` (except the new §10.10 added by this phase), `doctrine-documentation-integrity.md`, `doctrine-shadow-genome-countermeasures.md`; all session-side edits to existing gate schemas. Also dropped: 36 session-side tests that asserted the specific text of the above dropped governance edits.

**Doctrine added**: `qor/references/doctrine-governance-enforcement.md` §10.10 Session reconciliation protocol — the rebase+renumber-or-consolidate playbook for future divergences.

**Tag cleanup**: 16 abandoned session tags deleted (v0.46.0-v0.59.0 + v0.54.1 + v0.58.1). Local v0.45.0 re-bound to upstream's Phase 59 ideate commit (`5c0879361f70a283b8f3f53326676d59d867516e`).

**Chain-rewrite event** (NIST AI RMF MANAGE-2.4 / EU AI Act Art. 12 record-keeping): META_LEDGER Entry #196 documents the rewrite explicitly; chain anchors at upstream's Entry #195 (Phase 59 ideate seal). Original 17-phase session commit history preserved on the local `archive/session-2026-05-09` branch at `8c72acf039f6098152a4dcd142708b05c461c91f`. Session entries #148-164 (locally sealed 2026-05-09 through 2026-05-11) are intentionally orphaned from the canonical chain.

**Follow-up cleanup** (Entry #197): both pre-reconciliation worktrees (`busy-williams-270b35`, `fervent-easley-26be58`) inspected and removed; cherry-pick dry-run confirmed the WT1 unique commit was content-subsumed by upstream's PR #37 squash. No deliverable lost.

**Audit-driven hygiene** (commit `2eda709`): `.gitignore` typo fixed (`.qor/intent_lock/` → `.qor/intent-lock/`); runtime state entries added (`.qor/current_session`, `.qor/hooks/`, `.qor/hooks.log`).

**Tests**: 1538 passing, 1 skipped, 4 deselected. Deterministic across multiple runs. Build: `python -m build` produces `qor_logic-0.46.0.tar.gz` + `qor_logic-0.46.0-py3-none-any.whl`, both pip-installable; CLI smoke `qor-logic --version` returns `qor-logic 0.46.0`.

**Decision**: Phase 60 sealed at v0.46.0. The session work-stream is reconciled with upstream's canonical timeline. Path B's explicit trade-off — sacrificing granular 17-phase replay identity in exchange for tractable merge resolution — is documented in §10.10 as the standard approach when shared governance surfaces have been independently evolved by both timelines.

## Phase 83 (v0.56.0 — 2026-05-22): qor-audit Phase 37 Infrastructure Alignment hardening (GH #83 + #87)

Two sub-checks added to the `/qor-audit` Step 3 Infrastructure Alignment Pass. Full procedures live in the new reference file `qor/skills/governance/qor-audit/references/phase37-subpasses.md` (progressive disclosure per GH #92); `SKILL.md` carries one-line pointers.

**Citation consumer-trace (GH #83)**: an auditor-executed prose sub-check. For every cited code symbol in a plan Locked Decision claiming to fix a defect at a named entry-point surface, the auditor verifies the symbol is reachable from that entry point; an unreached citation (dead code, or the wrong symbol cited) is an `infrastructure-mismatch` VETO.

**Delivery-Branch Currency (GH #87)**: a new pre-audit lint `qor/scripts/delivery_branch_lint.py` (wired into `/qor-audit` Step 0.6) extracts the optional `pr_target` plan field, allowlist-validates it against a conservative branch-name pattern (a `-`-prefixed value is rejected and never passed to `git` — argument-injection guard added per the iter-1 OWASP A03 VETO), and runs `git ls-remote` to confirm the branch exists on the remote. Prose in the reference file directs the auditor to obtain operator confirmation that the branch is still open and to grep cited infrastructure against `pr_target` specifically. New optional `pr_target` field on `qor/gates/schema/plan.schema.json`; new `SG-DeliveryBranchDrift-A` doctrine entry.

**Tests**: 11 new tests across `tests/test_delivery_branch_lint.py` (helper behavior — no-op, existing, dash-prefix rejection, absent, CLI, schema) and `tests/test_audit_phase37_subpasses.py` (sub-pass wiring + procedure-content + SG doctrine round-trip). Deterministic across two runs.

**Decision**: Phase 83 sealed at v0.56.0. Audit iter-1 VETO (OWASP A03 argument injection in the unvalidated `pr_target` path) corrected at iter-2 by adding branch-name allowlist validation before any subprocess call.

## Phase 84 (v0.57.0 — 2026-05-22): Audit-readiness guards — pre-audit short-circuit + inverse-coverage discipline (GH #81 + #84)

Two pre-audit lint guards plus thin skill-prose wiring; detailed prose lands in doctrine reference files per GH #92 progressive disclosure.

**Pre-audit readiness short-circuit (GH #81)**: a new pre-audit lint `qor/scripts/plan_iteration_status_lint.py` detects three pre-audit self-declaration signals in a plan — an `**iteration**:` value containing `draft` / `pre-audit`, an "Operator Decisions Required Before Audit" section, or an Open Questions bullet ending "Operator confirms before audit" — and exits non-zero on any hit. `/qor-audit` gains Step 0.3, which runs the lint before identity activation and before any adversarial pass; on non-zero exit the audit aborts and emits no gate artifact, so a structurally not-ready plan consumes no audit cycle. Unlike the WARN-only Step 0.6 lints, this is a hard short-circuit.

**Inverse-coverage discipline (GH #84)**: `qor/scripts/plan_test_lint.py` gains an inverse-coverage check — when a plan declares a closed-enum taxonomy (a `CANONICAL_*_VALUES` constant plus a `normalize*` function) with no inverse-coverage test bullet, it emits a WARN-only `inverse-coverage-missing` finding. `/qor-plan` Step 5 and the `/qor-audit` Step 3 Test Functionality Pass require both the forward round-trip and the inverse coverage assertion; missing inverse coverage is a `coverage-gap` VETO. The discipline (forward + inverse assertions, gated-bucket exemption, standard test pattern) is documented in `qor/references/doctrine-test-functionality.md`.

**Doctrine**: two new entries — `SG-PreAuditDraftSubmission-A` and `SG-InverseCoverageGapTaxonomy-A` — in `qor/references/doctrine-shadow-genome-countermeasures.md`; three new glossary terms.

**Tests**: 26 tests across `tests/test_plan_iteration_status_lint.py` (8 — signal detection, CLI exit codes, missing-plan), `tests/test_audit_skill_iteration_lint_wiring.py` (2 — Step 0.3 wiring, anchored + strip-and-fail), `tests/test_inverse_coverage_skill_wiring.py` (4 — doctrine section + skill citations, anchored + strip-and-fail), and `tests/test_plan_test_lint.py` (4 added — inverse-coverage detection + presence-only regression). Deterministic across two runs.

**Decision**: Phase 84 implemented; audit PASS on iter-1 under Step 1.a Option B (independent architect-reviewer subagent, clearing SG-AuthorAuditMomentum-A self-audit bias). Targets v0.57.0 (feature → minor bump) at substantiate.

## Phase 85 (v0.57.1 — 2026-05-22): CI-health fixes — canonical-trailer integrity + drift-report scan hoist (GH #96)

Hotfix closing GH #96, the three pre-existing suite failures surfaced by the Phase 84 cycle and root-caused by `/qor-debug`.

**Canonical-trailer integrity (FIX A)**: `test_seal_commits_after_cutoff_have_full_canonical_trailer` was red on `main` because the phase 82/83 seal commits were authored locally with only the compact `Co-Authored-By:` line, missing the `Authored via [Qor-logic SDLC]` line. New pure function `qor.scripts.attribution.message_has_full_trailer` is the single source of truth for the full-trailer predicate, consumed by both the doctrine test and a new `qor/scripts/seal_trailer_check.py` CLI. `/qor-substantiate` gains Step 9.5.4, which runs the guard after the seal commit and ABORTs if the full trailer is absent. The test keeps its `phase >= 49` floor but adds `_GRANDFATHERED_SEAL_PHASES = frozenset({82, 83})` — a precise exception set that discloses the two non-compliant historical commits while preserving strict coverage for all other phases (a blanket floor-raise to 85 would have discarded coverage of compliant phases 49-84).

**Drift-report scan hoist (FIX B/C)**: `check_term_drift` and `check_cross_doc_conflicts` in `qor/scripts/doc_integrity_strict.py` called `_iter_scan_files()` inside the per-term loop — O(terms x files) ~= 156k tree-walks + re-reads, 68-81s locally, over the `test_doc_integrity_drift_report_cli.py` 60s cap. New `_scan_corpus` helper materializes the corpus once before the term loop; both functions iterate the materialized `(rel, text)` list. Behavior-preserving (same files, same scope fence, same finding content and append order); ~75x fewer file operations.

**Tests**: 13 new tests across `tests/test_seal_trailer_guard.py` (7 — `message_has_full_trailer` accept/reject cases, CLI exit codes against tmp git repos, dash-prefix rejection), `tests/test_doc_integrity_strict_corpus_scan.py` (5 — hoisted-function findings correctness, strict-mode raise, `_scan_corpus` one-entry-per-file), and `tests/test_attribution_tiered_usage.py` (3 added — `_seal_phase_in_scope` scope helper). The previously-failing `test_doc_integrity_drift_report_cli.py` and `test_seal_commits_after_cutoff_have_full_canonical_trailer` now pass. `doc_integrity_strict.py` 222/250 lines after the hoist.

**Decision**: Phase 85 implemented; audit PASS on iter-1 under Step 1.a Option B (independent architect-reviewer subagent). Targets v0.57.1 (hotfix → patch bump) at substantiate.

## Phase 86 (v0.57.2 — 2026-05-22): Post-merge seal-tag push (GH #98)

Hotfix closing GH #98 — every seal PR required `gh pr merge --admin` because `/qor-substantiate` pushed the annotated `v{X.Y.Z}` tag together with the phase branch, before the seal commit reached `origin/main`. `release.yml` triggers `on: push: tags` and its `build-and-publish` job refuses to publish a tag whose commit is not an ancestor of `origin/main`; that failing check then blocked the seal PR (the branch ruleset gates merge on all checks).

**Fix**: tag CREATION stays at Step 9.5.5 (pre-merge, on the seal commit — the Phase 33 timing fix is unchanged). Tag PUSH moves to a new `/qor-substantiate` Step 9.7, gated on `git merge-base --is-ancestor "$SEAL_COMMIT" origin/main` — the same reachability predicate `release.yml` uses, so the tag push and the publish guard agree by construction. Step 9.6's push options push the branch only (the `--tags` instruction is removed). A Constraints line and the `doctrine-governance-enforcement.md` `seal_tag_timing` note record the creation-vs-push separation.

**Tests**: 5 new anchored + strip-and-fail wiring tests in `tests/test_substantiate_tag_push_timing.py` (Step 9.6 pushes branch-only; Step 9.6 defers the tag; Step 9.7 pushes the tag gated on `origin/main` reachability; two strip-and-fail negatives). The two dependent step-layout tests (`test_seal_flow_ordering.py`, `test_substantiate_tag_timing_wired.py`, enumerated in the plan after the iter-1 VETO) confirmed green after the SKILL.md edit.

**Audit history**: iter-1 VETO (Entry #226, L2) — `infrastructure-mismatch`: the plan omitted those two dependent wiring tests from Affected Files. Resolved at iter-2 (Entry #227 PASS) by a `### Dependent tests (verified unaffected)` plan subsection with the boundary impact analysis.

**Decision**: Phase 86 implemented; audit PASS on iter-2 under Step 1.a Option B. Targets v0.57.2 (hotfix → patch bump) at substantiate. The fix takes effect for phase 87 onward; phase 86's own seal still tags-before-merge, so its own PR still needs `--admin`.

## Phase 87 (v0.58.0 — 2026-05-22): Author-momentum risk auto-dispatch (GH #82)

Feature closing GH #82 — the Phase 68 Option B independent reviewer was operator-discretion and reactive (dispatched after a VETO). This phase makes it proactive: a risk score, consulted at `/qor-audit` Step 1, auto-mandates Option B on the iteration where author-momentum risk first appears.

**New module `qor/scripts/audit_risk_score.py`**: `score_plan(plan_path) -> RiskAssessment` (frozen dataclass: `flags: tuple[str, ...]`, `option_b_required: bool`). V1 implements the two mechanically-deterministic GH #82 signals — `config-file-cite` (a cited `*.config.{ts,js,yaml,toml}` file; config-fabrication class) and `high-citation-surface` (>=5 `git show ... | grep` grep-evidence statements). `option_b_required = bool(flags)` — fires on ANY signal. The CLI prints `option_b_required: true|false`. GH #82 signals 2 and 3 (sealed-shared-module + new shared-type field; analytics-emit + new state-flow) are declared `non_goals` for a follow-on: they are plan-semantic judgements a lean text heuristic cannot anchor a non-vague test to; the `flags` tuple is open so they can be added without an API break.

**`/qor-audit` Step 1**: a `Phase 87 wiring (GH #82)` paragraph runs `audit_risk_score` against the plan; when it reports `option_b_required: true`, Option B is mandatory (the auditing agent must run an independent reviewer, not a solo audit), operator override only with written justification. The `SG-AuthorAuditMomentum-A` doctrine entry gains a Risk-score auto-dispatch countermeasure bullet.

**Tests**: 10 new — 8 behavior tests in `tests/test_audit_risk_score.py` (each signal fires; the 4-vs-5 grep-evidence threshold boundary; clean plan; both signals; missing plan; CLI true/false) + 2 anchored + strip-and-fail wiring tests in `tests/test_audit_risk_score_wiring.py`. `audit_risk_score.py` 81 lines; functions 16/15.

**Audit history**: iter-1 PASS (Entry #230, L2), conducted under Step 1.a Option B (independent `architect-reviewer` subagent — doubly indicated, since the plan cites `vitest.config.ts` and so trips the very V1 signal it introduces). The 2-of-4-signals V1 scoping was ruled a legitimate disclosed boundary.

**Decision**: Phase 87 implemented; audit PASS on iter-1. Targets v0.58.0 (feature → minor bump) at substantiate.

## Phase 88 (v0.59.0 — 2026-05-22): gh-PR-state pre-check for /qor-research (GH #80)

Feature closing GH #80 — `/qor-research` previously had no mechanism to detect that the PR closing the target issue had already MERGED elsewhere. A full plan-audit-implement cycle could be wasted on already-shipped work (the COREFORGE 2026-05-18 incident: issue #410 cycled to staged implementation before PR #493 was discovered merged hours earlier). This phase adds a five-line operator pre-check at the top of the research flow.

**`/qor-research` SKILL.md gains Step 2.5 (issue-state pre-check)**: when the research target is an existing GH issue (e.g., `#80`), run `gh pr list --state all --search "#<N>"` and `gh pr list --state all --search "in:body <N>"`; if any PR is MERGED and closes the target, surface number/state/mergedAt/title to the operator before continuing. Scope-conditional — non-issue targets (API surfaces, dependencies) and `gh`-absent hosts skip with a one-line note (Phase 75 declarative-tolerance pattern). No new script, no new doctrine file — kept lean per the GH #92 progressive-disclosure lesson.

**Out of scope (declared non_goal)**: GH #80 also names `/qor-auto-dev-1`, but that skill lives at the user-side install path (`~/.claude/skills/qor-auto-dev-1/SKILL.md`), not in this repo's canonical SSoT under `qor/skills/`. The same Step 2.5 prose pattern is recommended as a companion change applied externally to the user-side artifact.

**Tests**: 3 new wiring tests in `tests/test_qor_research_issue_state_check.py` — anchored positive (Step 2.5 cites both `gh pr list` invocations + `MERGED` + `surface` operative directive) + strip-and-fail negative (assertions collapse when the section is removed) + scope-conditional language guard (the `existing GH issue` phrase is load-bearing; without it the prose would direct unconditional `gh` API calls on non-issue research targets). Pattern mirrors `tests/test_audit_skill_iteration_lint_wiring.py` (Phase 84 wiring-test convention).

**Decision**: Phase 88 implemented; audit PASS on iter-1 (audit_risk_score reported no Option B mandate — no `*.config.*` cite, fewer than 5 grep-evidence citations; solo audit valid). Targets v0.59.0 (feature → minor bump) at substantiate.

## Phase 89 (v0.60.0 — 2026-05-22): Plan ci_commands reconciliation against .github/workflows (GH #91)

Feature closing GH #91 — phase plans hand-author a `## CI Commands` list and `/qor-substantiate` runs exactly that list, but nothing reconciles the list against the repo's actual GitHub Actions workflow definitions. A CI job the operator forgot to enumerate never runs through the governed cycle, so the seal entry reads "all CI green" while a real CI job would fail. The COREFORGE 2026-05-22 origination case sealed 10 phases "green" while the `Architecture Guard` job (running `scripts/architecture/check_test_metadata.py`) would have failed.

**New module `qor/scripts/ci_coverage_lint.py`**: `discover_ci_commands(workflows_dir)` walks `.github/workflows/*.yml` (PyYAML safe_load), skips tag-only workflows (`on.push.tags` without `branches`), filters environment-setup boilerplate (`pip install`, `git fetch`, `git merge-base`, `echo`/`printf`, doc-only `[[ ]]` conditional bash, `>> $GITHUB_OUTPUT`, etc.), and extracts the V1 Python-fingerprint `run:` commands (lines beginning with `python ` or `pytest `). `check_plan(plan, workflows_dir) -> list[LintWarning]` compares each discovered command (flag-normalized for pytest verbose/quiet variants) as a substring against the plan's `## CI Commands` bullets; honors a `## CI Coverage Exemptions` block of substring patterns; emits a WARN per unmatched, non-exempt command. CLI exits 0 always (WARN-only contract; parallels `delivery_branch_lint`).

**`/qor-audit` Step 0.6**: gains one new line in the WARN-only pre-audit lint block, after the existing four lints, plus a `Phase 89 wiring (GH #91)` paragraph that cites the workflow-vs-plan reconciliation purpose and `SG-CICoverageDrift-A`.

**Doctrine extension**: `qor/references/doctrine-shadow-genome-countermeasures.md` gains an `SG-CICoverageDrift-A` entry with pattern (plans never reconciled against actual workflows; latent CI failures invisible until integration PR), originating incident (COREFORGE 2026-05-22 10-phase stack; `Architecture Guard`), and countermeasure (Phase 89 lint at Step 0.6; WARN-only; plan-side exemption block; self-application test as the deterministic shipping-correctness anchor).

**Tests**: 13 new behavior tests in `tests/test_ci_coverage_lint.py` (matched-by-plan, missing-from-plan, env-setup filter, git-plumbing filter, doc-only-bash filter, tag-only-skip, multiline-run, exemption-suppresses, exemption-must-match-substring, plan-without-section, pytest-marker-form, CLI-exit-zero, self-application against Phase 89's own plan) + 2 anchored + strip-and-fail wiring tests in `tests/test_ci_coverage_lint_wiring.py`. Pattern mirrors Phase 84/87/88 wiring-test convention. All 15 pass twice deterministically. Full suite: 1757 passed, 1 skipped, 0 failed.

**V1 boundaries**: Python-fingerprint heuristic only — non-Python CI checks (cargo, npm, custom shell) out of scope (the COREFORGE origination case is Python; that surface is covered). Tag-only workflows skipped (they don't run on branch PRs). No substantiate-time re-assert (deferred follow-on, analogous to the V1/V2 split for other cluster items). Operator justification is via the plan-side exemption block only; workflow-comment-annotation exemptions are non_goals. WARN-only; no VETO binding in V1.

**Decision**: Phase 89 implemented; audit PASS on iter-1 (audit_risk_score reported no Option B mandate — no `*.config.*` cite, fewer than 5 grep-evidence citations; solo audit valid). Targets v0.60.0 (feature → minor bump) at substantiate.

## Phase 90 (v0.61.0 — 2026-05-23): Skill preflight + Environment contract for Python-dependent invocations (GH #79)

Feature closing the visible-misconfiguration half of GH #79. Phase 75 (v0.51.0) gave skills declarative tolerance when `qor-logic` modules are unreachable: emit `gate_skipped_prerequisite_absent`, log SKIP in the seal, continue. That countermeasure is correct for legitimately non-Python hosts. It misfires on Python hosts where the operator simply has the wrong venv active — the SKIP cascade looks identical to the legitimate non-Python case, and operators learn to treat SKIPs as normal. The COREFORGE consumer session in GH #79 documented exactly that drift, with a project-memory rule encoding the silent-skip pattern across subsequent sessions.

**Two layered additions to each of 7 affected skills** (qor-audit, qor-process-review-cycle, qor-shadow-process, qor-substantiate, qor-repo-audit, qor-implement, qor-plan) — every SKILL.md in `qor/skills/` that grep-matches `python -m qor\.(?:reliability|scripts)\.\w+`:

- **(D) `## Environment` block** between `## Purpose` and the protocol section. Documents the install contract: verify with `python -c "import qor.reliability"`; fix by activating the install venv (`pip show qor-logic` resolves) or `pipx install qor-logic` for a global install. Explicitly cross-references the Phase 75 SKIP fallback so non-Python operators retain the documented escape valve and Python operators understand the relationship.
- **(C) WARN-only preflight one-liner** at the top of `## Execution Protocol` (or `## Bundle protocol` for qor-process-review-cycle): `python -c "import qor.reliability" || echo "WARN [qor-logic]: ..." >&2`. Surfaces the misconfiguration once at skill entry. Critically, NOT an ABORT — Phase 75 SKIP behavior must remain intact on legitimately non-Python hosts; the WARN is the visibility layer, the SKIP remains the tolerance layer.

**Doctrine extension**: `qor/references/doctrine-shadow-genome-countermeasures.md` gains an `SG-SilentSkipMisconfig-A` entry with pattern (silent-SKIP cascade indistinguishable from legitimate non-Python case), originating recurrence (COREFORGE per GH #79; project-memory rule encoded silent-skip), and countermeasure (Phase 90 C+D combination; cross-skill test enforces forward-only structural discipline).

**Tests**: 7 new wiring assertions in `tests/test_skill_environment_block.py`. (1) precondition: at least 5 Python-invoking skills detected (catches regex drift); (2) every detected skill carries `## Environment` section; (3) Environment block cites `pip show qor-logic` AND `pipx install qor-logic` (partial-decay guard); (4) Environment block cites Phase 75 AND `gate_skipped_prerequisite_absent` (cross-reference enforcement); (5) preflight `python -c "import qor.reliability"` present and precedes the first concrete qor-module invocation (semantic placement guard, stronger than 'after Execution Protocol heading' since qor-process-review-cycle uses `## Bundle protocol` instead); (6) preflight WARN-only, not ABORT (negative-existence check on `exit 1` and `|| ABORT`); (7) forward-only structural sweep (future-skill drift guard). All pass twice deterministically.

**V1 boundaries**: ships only Options C + D from GH #79's four-option menu. Option A (`qor-logic <subcommand>` CLI dispatch using the CLI's own `sys.executable`) and Option B (install-time `${QOR_PYTHON}` path-rewriting) deferred to a future phase pending operator evidence on how effectively C+D converts the silent-skip pattern into visible misconfiguration. Per-invocation preflight (the issue's literal "prepend each reliability step" reading) declared non_goal — per-skill preflight at protocol entry is operatively sufficient since the misconfiguration manifests the same way regardless of which downstream call trips first.

**Self-application: Phase 89's `ci_coverage_lint` on Phase 90's plan** — first cross-phase exercise of the lint introduced last cycle. Phase 90's `## CI Commands` block was authored to cover the full Qor-logic CI surface (matching Phase 89's self-application convention); `ci_coverage_lint` exit 0 with zero warnings, confirming Phase 89's countermeasure operative on a fresh plan.

**Decision**: Phase 90 implemented; audit PASS on iter-1 (audit_risk_score reported no Option B mandate; solo audit valid; all 5 Step 0.6 pre-audit lints exit 0 including the new Phase 89 ci_coverage_lint). Targets v0.61.0 (feature → minor bump) at substantiate.

## Phase 91 (v0.62.0 — 2026-05-23): verify-ledger --tolerate-known-grandfathered stopgap (GH #85)

Feature closing the consumer-blocker half of GH #85 via Option D from the issue's four-option menu. Phase 76 (v0.52.0) introduced forward-only detection/prevention of the concurrent-write race via content-addressable Entry IDs + `check_previous_hash_uniqueness`, but explicitly deferred reconciliation of pre-V1 duplicate entries to a V2 follow-on. Consumer workspaces with the documented residual (e.g., `Accountable-Live-LLC/Accountable-App-3.0` per GH #85: entries #16a/b, #17a/b, #18a/b sharing previous_hashes from concurrent analytics-376 / accountable-live-335 / migration-332 sessions, plus an Entry #20 downstream chain-hash mismatch) could not ship a clean `qor-logic verify-ledger` result on their main ledger and could not pre-commit-hook the chain validator — a usability/release-gate blocker.

**New helper `find_grandfathered_entries(ledger_md, cutoff=207)`** in `qor/scripts/ledger_hash.py`. Returns a `frozenset[int]` of entry numbers whose `previous_hash` is shared by 2+ entries AND whose entry number is `<= cutoff` (default 207, matching `check_previous_hash_uniqueness`'s `min_entry_num`). Single-pass over the ledger; groups entries by `previous_hash` value; collects the pre-cutoff members of every multi-entry group.

**`verify()` extension**: two keyword-only args (`tolerate_known_grandfathered: bool = False`, `grandfather_cutoff: int = 207`). When the flag is True, chain-math failures on grandfathered entries produce `DISCLOSED_GRANDFATHERED Entry #N: tolerated SG-ConcurrentLedgerRace-A residual` on stdout instead of `FAIL` on stderr, do not increment the error count, and do not propagate TAINTED to downstream entries (the existing `last_failed = num` cascade does not fire for tolerated entries). Placeholder-pattern failures remain non-tolerated (different failure class).

**`qor-logic verify-ledger` CLI**: two new args `--tolerate-known-grandfathered` (store_true, default False) and `--grandfather-cutoff` (int, default 207). Both propagate to `verify()` via `_do_verify_ledger` in `qor/cli.py`. Existing `--post-anchor` and `--boundary` semantics unchanged; the new flags compose orthogonally with the strict-verify path only (post-anchor mode handles a different tolerance class — disclosed pre-anchor failures up to a re-anchor boundary).

**Doctrine extension**: `qor/references/doctrine-shadow-genome-countermeasures.md` `SG-ConcurrentLedgerRace-A` section gains a "V2 stopgap (Phase 91 wiring; GH #85)" paragraph naming the flag, the signature, the read-only verifier semantics, and the explicit deferral of real reconciliation (Options A/B from GH #85 — RECONCILIATION entry append; post-anchor pinning) to a future phase with operator-authorization protocol design.

**Tests**: 13 new behavior tests in `tests/test_ledger_hash_tolerate_grandfathered.py`. (1-4) `find_grandfathered_entries` signature detection: returns entries with duplicate previous_hash below cutoff; excludes post-cutoff entries; excludes unique-previous_hash entries; handles mixed pre/post-cutoff groups correctly. (5-9) `verify()` behavior: without flag still fails on grandfathered chain mismatch; with flag reports DISCLOSED_GRANDFATHERED not FAIL; with flag does NOT propagate taint from tolerated failure; with flag still fails on post-cutoff chain mismatch (the critical non-masking guard); custom cutoff overrides default. (10-11) CLI flag plumbing: `--tolerate-known-grandfathered` parses and propagates; `--grandfather-cutoff` arg parses and widens the toleration set. (12-13) Canonical-ledger forward-only guards: `verify(canonical, tolerate=False)` returns 0 (unchanged behavior); `verify(canonical, tolerate=True)` returns 0 with no `DISCLOSED_GRANDFATHERED` output (zero-noise on a clean ledger).

**V1 boundaries** (declared non_goals): Options A (RECONCILIATION ledger entry append), B (post-anchor pinning at reconciliation entry), and C (per-session sub-ledger merge tool) from GH #85 NOT implemented. Each requires real operator-authorization protocol design and a new schema-bearing ledger entry type. Phase 91's read-only verifier-semantics-only fix is the V1 stopgap; A/B reserved for a future phase. Placeholder-pattern failures (Phase 66 detection) remain non-tolerated even on grandfathered entries — different failure class than the concurrent-race signature.

**Dogfooding pattern continued**: this audit was the second cross-phase exercise of Phase 89's `ci_coverage_lint` (after Phase 90's first). Phase 91's `## CI Commands` covers the full Qor-logic CI surface; lint exit 0. Phase 91 also continues the canonical-ledger forward-only guard pattern established in Phase 90 — two new tests assert the canonical Qor-logic META_LEDGER's verifier behavior is observably unchanged by the introduction of the flag (both with flag on and off).

**Decision**: Phase 91 implemented; audit PASS on iter-1 (audit_risk_score reported no Option B mandate; solo audit valid; all 5 Step 0.6 pre-audit lints exit 0). Targets v0.62.0 (feature → minor bump) at substantiate.

## Phase 92 (v0.63.0 — 2026-05-23): Multi-tier Definition of Done V1 (GH #86)

Feature closing the contract-layer half of GH #86. The proposal-class issue documented a credibility-erosion pattern: multiple Qor governance phases return PASS while the artifact in question is still a placeholder or a lie at runtime (the COREFORGE originating recurrence: ~5 production-credibility blockers — hardcoded `true` recovery routines, vendor placeholders, constraint checks returning `Ok(())` — sailed through `PASS → seal` cycles undetected). The root cause is that existing gates verify artifact-shape and ledger chain, not behavior; D4 (empirical/runtime verification) was structurally missing.

**Phase 92 V1 scope**: ship the explicit multi-tier contract layer (plan emission + structural substantiate check). Empirical-execution enforcement (D4 test-name → pytest-output cross-reference) is V2 and deferred — per the cluster's established V1/V2 split pattern, V1 lands the infrastructure first so operators adopt the discipline before the heavier empirical machinery is layered on top.

**New module `qor/scripts/dod_record.py`** (138 LOC): `parse_plan(plan_path) -> list[DodRecord]` walks the plan's `## Definition of Done` section, splits on `### Deliverable: <name>` sub-headers, returns one frozen `DodRecord` per deliverable with `{deliverable, d1, d2, d3, d4, d4_waiver_rationale, d4_waiver_followup}` fields. Permissive: returns the empty list on absent section. Robust to fenced code blocks (the parser strips them before scanning for the section header so example templates inside plan design notes don't confuse the scan — caught during TDD red-green when Phase 92's own plan example fence shadowed the real section header). Multi-line follow-up references supported via DOTALL regex bounded by paragraph break.

**New module `qor/scripts/dod_check.py`** (122 LOC): `check_plan(plan_path) -> list[CheckFinding]` walks the parsed records and emits findings — `missing-dod-section`, `deliverable-missing-tier`, `waiver-without-rationale`, `waiver-without-followup` — each with V1 `severity="warn"`. CLI `main()` exits 0 always (WARN-only contract; parallels `delivery_branch_lint` and `ci_coverage_lint`).

**`/qor-substantiate` Step 4.6.7 NEW** (between procedural-fidelity 4.6.6 and doc-integrity 4.7): invokes `python -m qor.scripts.dod_check --plan "$PLAN_PATH" || true`. SG-Phase47-A countermeasure honored (argv-only PLAN_PATH). WARN-only: findings surface in the seal report's `## Definition of Done` block but do not abort substantiate. V2 may tighten specific categories to fail-closed once adoption matures.

**`/qor-plan` SKILL.md**: plan-structure template gains a new `## Definition of Done` section between `## Phase N` and `## CI Commands`, with `### Deliverable: [name]` sub-headers and D1-D4 / D4.d bullet template. New "Phase 92 wiring (GH #86)" paragraph documents the contract; pre-Phase-92 plans grandfathered.

**New doctrine file `qor/references/doctrine-definition-of-done.md`**: documents the four-tier contract (Purpose / D-tier definitions / Plan-section format / Waiver protocol / V1 enforcement / V2 reserved / Cross-references). The 28th doctrine in the corpus; bumps the Doctrines badge 27 → 28.

**New `SG-DoDImplicit-A` doctrine entry** in `qor/references/doctrine-shadow-genome-countermeasures.md`: pattern (implicit DoD; ceremonial gates pass while substantive behavior is unverified), originating recurrence (COREFORGE per GH #86), countermeasure (Phase 92 V1 structural check), forbidden interpretation (WARN-only V1 contract is the adoption ramp, not permission to ignore D4). Cross-references SG-HalfSealedClaim-A (Phase 75) and SG-DocSurfaceUncovered-A (Phase 58) — same root family: ceremonial gates pass while substantive verification is absent.

**Tests**: 14 new tests across three files. `test_dod_record.py` (4): each parse-shape branch (empty-section / single / multi / D4.d waiver). `test_dod_check.py` (7): each finding category + complete-block-no-findings + CLI exit-0 contract + `test_check_plan_self_applies_to_phase_92_plan` deterministic shipping-correctness anchor (Phase 92's own plan declares a complete DoD block; the lint reports zero findings against it — the dogfooding pattern from Phase 89/91). `test_dod_substantiate_wiring.py` (3): anchored positive + strip-and-fail negative + positional guard (Step 4.6.7 ordered between 4.6.6 and 4.7). All pass twice deterministically. Full suite: 1791 passed, 1 skipped (+14 from Phase 91's 1777). README Doctrines badge bumped 27 → 28 to track the new doctrine file.

**V1 boundaries** (declared non_goals): D4 empirical-execution check (cross-reference D4-declared test names against pytest output; fail seal on mismatch — V2); ledger SESSION SEAL body D-tier status block (V2); `/qor-ideate` integration (V2); implement-time D4 author-intent capture (V2); waiver-friction escalator (V2); retroactive DoD section in prior sealed plans (forward-only by construction); schema-level validation beyond field presence (V1 permissive). The waiver protocol is the operator's escape valve when empirical verification is impossible in the current cycle; rationale + follow-up phase reference are mandatory.

**Dogfooding milestone**: third cross-phase exercise of Phase 89's `ci_coverage_lint` (after Phase 90 + Phase 91). Phase 92's `## CI Commands` covers the full Qor-logic CI surface; lint exit 0. Phase 92 is the first phase to *eat its own dogfood at plan-authoring time* — the plan itself declares a `## Definition of Done` block with D1-D4 rows for each V1 deliverable, and the self-application anchor verifies the new lint reports zero findings against its own plan. The dogfooding pattern is now stable across 4 consecutive phases.

**Decision**: Phase 92 implemented; audit PASS on iter-1 (audit_risk_score reported no Option B mandate; solo audit valid; all 5 Step 0.6 pre-audit lints exit 0 including the third cross-phase exercise of Phase 89 `ci_coverage_lint`). Targets v0.63.0 (feature → minor bump) at substantiate.

## Phase 93 (v0.64.0 — 2026-05-23): Merge-velocity throttle detector V1 (GH #89)

Feature closing the detector half of GH #89. The Bicameral consumer-workspace originating recurrence: 27 PRs merged in a single window, 14,758 additions, repair cluster #346-#353 (stale authoritative SHA binding / status lifecycle / preflight noise / schema CI reliability), failing e2e on tail PR #354, later operational response backed Jira/Notion/Slack/Linear out of `dev`. Throughput exceeded the rate at which the project could reliably absorb changes; the governance system had no explicit throttle. The corrective principle: stabilization capacity should become a pacing constraint, not an after-the-fact repair loop.

**New module `qor/scripts/merge_velocity_check.py`** (224 LOC): `assess_merge_velocity(repo_root, window_days, shared_core_paths) -> VelocityAssessment` walks `origin/main`'s recent merge history via `git log --merges --pretty=format:'%H\\0%cI\\0%s'` (offline-safe; falls back to HEAD when origin/main absent), filters commits by committer date in Python (avoids the `git log --since` early-stop on non-monotonic histories — a bug found during TDD), computes line-additions via `git diff --shortstat <sha>^..<sha>` (which surfaces merge-commit deltas where `git show --shortstat` returns empty), enumerates changed paths via `git diff --name-only <sha>^..<sha>` for shared-core detection. Three grades plus an evidence list naming the thresholds that fired. Repair-keyword classification covers six tokens; deterministic action mapping from grade.

**`/qor-substantiate` Step 4.6.8 NEW** (between DoD check 4.6.7 and doc-integrity 4.7): invokes `python -m qor.scripts.merge_velocity_check --repo-root . --window-days 7 || true`. WARN-only V1 contract; CLI exits 1 on `exceeded` so V2 can remove the `|| true` wrap.

**Doctrine extension**: `SG-MergePaceThrottle-A` entry catalogs the Bicameral originating recurrence, the V1 detector, and the explicit deferral of enforcement (hold-feature-merges, isolate as unmerged branches, require stabilization plan) plus GitHub-API signals (failing-e2e tail-check, test-matrix expansion, cross-PR repair clustering) to V2.

**Tests**: 12 + 3 = 15 new tests. `test_merge_velocity_check.py` covers each grade transition (healthy/strained/exceeded), repair-density keyword classification, shared-core touch counting, recommended-action mapping, evidence-list threshold naming, window-days filtering, CLI exit codes, and a canonical-repo forward-only guard (`test_assess_velocity_on_qor_logic_main` asserts the detector runs on Qor-logic's own main with a valid grade in the closed set). `test_merge_velocity_substantiate_wiring.py` covers anchored positive + strip-and-fail negative + positional guard (Step 4.6.8 ordered between 4.6.7 and 4.7).

**Red-green TDD observed**: three implementation bugs caught during TDD — (a) Windows filename character handling (`:` in repair-subject filenames blocked `git commit`); (b) `git log --since` early-stop on histories with non-monotonic committer dates (back-dated old merge after recent merge); (c) `git show --name-only` and `git show --shortstat` return empty for clean merge commits (workaround: `git diff <sha>^..<sha>`). All three caught at red-green; impl iterated 3 times to GREEN. All 15 pass twice deterministically. Full suite: 1806 passed, 1 skipped, 0 failed (+15 from Phase 92's 1791).

**V1 boundaries** (declared non_goals): enforcement (hold-feature-merges, isolate as unmerged branches, require stabilization plan) deferred to V2; GitHub-API integration (failing-e2e tail-check signal, test-matrix expansion detection, cross-PR repair-density clustering by subsystem) deferred to V2; built-in shared-core path patterns (operator-declarable only in V1; consumer-workspace-specific). Per the cluster's established V1/V2 split pattern.

**Dogfooding milestones**: fourth cross-phase exercise of Phase 89's `ci_coverage_lint` (88 → 89 → 90 → 91 → 92 → 93). FIRST cross-phase exercise of Phase 92's `dod_check` (on Phase 93's own plan); the new lint caught a real line-wrap drift in the SG-MergePaceThrottle-A waiver `**Follow-up phase**:` reference at plan-audit time, before the plan reached substantiate. The discipline introduced last phase already paid off this phase. Phase 93 is the third consecutive phase to declare a `## Definition of Done` block at plan-authoring time, and the second to carry `D4.d` waivers exercising the waiver-shape contract.

**Decision**: Phase 93 implemented; audit PASS on iter-1. Targets v0.64.0 (feature → minor bump) at substantiate.

## Phase 94 (v0.65.0 — 2026-05-23): Inline workspace-fragility detector V1 (GH #90)

Feature closing the inline-mechanism half of GH #90 (filed as "Follow-up to #89"). Where Phase 93 detects MACRO merge-pace at substantiate time (looking backward at `origin/main`'s recent merge history), Phase 94 detects MICRO workspace fragility at AUDIT time (looking at the CURRENT working tree before any merge). The two halves are complementary signals into the same governance surface: stabilization capacity should be a pacing constraint, surfaced as early as possible in the cycle.

**New module `qor/scripts/workspace_fragility_check.py`** (~190 LOC): `assess_workspace_fragility(repo_root) -> FragilityAssessment` inspects five local signals — untracked file count via `git status --short --untracked-files=all`; dirty gate artifacts via `.qor/gates/` walk + cross-reference against META_LEDGER SESSION SEAL `**Session**:` markers; ledger chain-math failures via Phase 91's `verify(ledger, tolerate_known_grandfathered=True)` (excludes SG-ConcurrentLedgerRace-A grandfathered residuals); active local branch count via `git branch --list`; branch-diff size via `git diff --shortstat origin/main..HEAD`. Three grades (`low` / `medium` / `high`) with deterministic action mapping (`merge_ok` / `narrow_scope` / `hardening_only`). V1 thresholds: `medium` at `untracked_count >= 15` OR `dirty_gate_artifact_count >= 3` OR `active_branch_count >= 10` OR `recent_commit_diff_lines >= 1500`; `high` at `ledger_chain_failure_count > 0` OR `untracked_count >= 50` OR `recent_commit_diff_lines >= 5000`.

**`/qor-audit` Step 0.6 extension**: the new lint joins the existing pre-audit ladder as the SIXTH line, after `ci_coverage_lint`. Step 0.6 now runs 6 lints (plan_test_lint, plan_grep_lint, plan_text_consistency_lint, delivery_branch_lint, ci_coverage_lint, workspace_fragility_check). All WARN-only. CLI exits 1 on `high` so V2 can remove the `|| true` wrap and convert to a hard ABORT.

**Doctrine extension**: `SG-MergePaceThrottle-A` (Phase 93) gains an "Inline companion (Phase 94 wiring; GH #90)" sub-paragraph naming the new detector's five signals, three grades, and explicit V2 deferral. No new SG entry — Phase 90 is the inline mechanism complementing Phase 89's macro throttle per the issue's own framing.

**Tests**: 10 + 3 = 13 new tests. `test_workspace_fragility_check.py`: each grade transition, each signal helper (untracked, dirty gates, ledger failures, branch count), recommended-action mapping, evidence-list shape, CLI exit codes, canonical-repo forward-only guard. `test_workspace_fragility_audit_wiring.py`: anchored positive (invocation + `|| true`), strip-and-fail negative, positional guard (new line appears AFTER `ci_coverage_lint`). All pass; full suite 1819 passed.

**Dogfooding milestones**: SIXTH cross-phase exercise of Phase 89's `ci_coverage_lint`. SECOND cross-phase exercise of Phase 92's `dod_check` (Phase 94 plan declares complete DoD block; lint exit 0 — no waiver drift this time). The pre-audit lint ladder grew from 4 → 5 → 6 lints across Phases 89/93/94 — Step 0.6 is now the most active surface in the substantiate-adjacent governance gate set.

**V1 boundaries**: enforcement clauses from GH #90's "Inline Enforcement Points" section (warn on scope expansion during implementation; require narrow first slice when planned change touches multiple shared surfaces; treat workspace fragility as audit evidence not background noise) deferred to V2; GitHub-API integration (open PR count; failing check enumeration) deferred; test-matrix growth detection deferred; per-deliverable scope-expansion surface (Phase 92 D4 tier natural extension) deferred.

**Decision**: Phase 94 implemented; audit PASS on iter-1. Targets v0.65.0 (feature → minor bump) at substantiate.

## Phase 95 (v0.66.0 — 2026-05-23): Skill-corpus size-budget lint V1 (GH #92)

Feature closing the meta process-finding from GH #92. The issue documented monotonic corpus growth (91 KB → 282 KB in 6 weeks; 30 SKILL.md files; qor-audit + qor-substantiate at 25% of the corpus; reference fan-out up to 80-100+ KB per audit invocation). The proposed counterweights: progressive disclosure (doctrinally honored already); per-skill size budget; periodic consolidation pass.

**Phase 95 V1 scope**: ship the per-skill size budget detector. V2 reserved for periodic consolidation cadence and historical-growth tracking.

**New module `qor/scripts/skill_size_budget_lint.py`** (~80 LOC): `check_skills(skills_root) -> list[SizeFinding]` walks `qor/skills/**/SKILL.md`, emits one finding per file exceeding the per-skill size threshold. Two thresholds: `WARN_BYTES = 25 * 1024` and `EXCEEDED_BYTES = 40 * 1024`. CLI exits 1 when any EXCEEDED finding is present so V2 can convert to a hard ABORT by removing the substantiate-site `|| true` wrap.

**`/qor-substantiate` Step 4.6.9 NEW**: between merge-velocity 4.6.8 (Phase 93) and doc-integrity 4.7. WARN-only V1 contract.

**New `SG-SkillCorpusGrowth-A` doctrine entry**: catalogs the pattern (monotonic corpus growth; no consolidation counterweight), the GH #92 measurement table (91 KB / 3024 lines at Phase 0 → 282 KB / 6766 lines at Phase 81; ~3.1x bytes, ~2.2x lines in 6 weeks), the V1 detector, and a **reflective note** acknowledging that the lint itself adds ~270 LOC + ~120 doctrine lines + ~20 skill-prose lines to the very corpus it measures. The V1/V2 split is itself a corpus-growth mechanism; V2 work will need to evaluate which doctrine prose is operative vs archival.

**Tests**: 8 + 3 = 11 new tests. `test_skill_size_budget_lint.py`: each threshold transition (below WARN, between WARN/EXCEEDED, above EXCEEDED), non-SKILL.md exclusion, CLI exit codes, and **TWO self-application anchors** — `qor-audit` is in EXCEEDED at 44 KB; `qor-substantiate` is in WARN range (39.8 KB → ~40 KB after this phase's edits; the test accepts either WARN or EXCEEDED to tolerate Phase 95's own skill-prose additions). `test_skill_size_budget_substantiate_wiring.py`: anchored positive + strip-and-fail negative + positional guard (Step 4.6.9 between 4.6.8 and 4.7).

**TDD red-green**: impl GREEN on first pass (no implementation bugs at red-green). All 11 pass twice deterministically. Full suite: 1830 passed, 1 skipped, 0 failed (+11 from Phase 94's 1819).

**V1 boundaries** (declared non_goals): periodic consolidation cadence (V2 extension of `qor-process-review-cycle`); historical-growth tracking from git history (V2 generalization of the GH #92 measurement table); context-load measurement per phase (per-skill reference fan-out); auto-suggest of progressive-disclosure refactor candidates. V1 lint does NOT auto-refactor skills; it is purely an observation surface.

**Dogfooding milestones**: SEVENTH cross-phase exercise of Phase 89's `ci_coverage_lint` (88 → 89 → 90 → 91 → 92 → 93 → 94 → 95). First cross-phase exercise of Phase 94's `workspace_fragility_check`. Phase 95 is the SECOND consecutive lint where the canonical Qor-logic corpus triggers the lint at substantiate-time (same pattern as Phase 94's `dirty_gate_artifact_count`); the dogfooding pattern is now stable across 8 consecutive phases.

**Decision**: Phase 95 implemented; audit PASS on iter-1. Targets v0.66.0 (feature → minor bump) at substantiate. Closes the post-cluster session's three governance backlogs (#89/#90/#92) and the cluster's eighth consecutive phase.

## Phase 96 (v0.67.0 — 2026-05-23): Recon reachability probe V1 (GH #108 partial)

Feature opening the Tier 1 prompt-surface remediation cluster (meta-memo at `docs/cluster-memo-prompt-surface-tier1-2026-05-23.md` sequences 5 sub-plans: 96 → 97 → 98 → 99 → 100). The cluster carries the same V1/V2 split discipline as the prior 8-phase governance burst (Phases 88-95). Phase 96 closes GH #108 partially: V1 visibility-only detector now ships; V2 enforcement reserved for Phase 99.

**New module `qor/scripts/reachability_probe.py`** (~250 LOC): `check_claim(claim, repo_root, manifest_path) -> list[ReachabilityFinding]` runs five checks per cited surface — importability (subprocess `python -c "from <module> import <symbol>"`), test collection (heuristic discovery + `pytest --collect-only`), caller graph (walk production .py files filtering out tests/.agent/.claude/.qor/docs), packaging (substring match against pyproject.toml or operator-passed manifest), interface match (AST parse of module signature vs regex parse of call-site invocation). Each failing check emits a `reachability-*-failed` / `-no-production-caller` / `-packaging-missing` / `-interface-mismatch` finding with `severity="warn"`. CLI exits 0 by default (V1 WARN-only); `--exit-on-any` opts into CI-style enforcement.

**`/qor-deep-audit-recon` Phase 3 Round 0 NEW**: between after-synthesis checkpoint and existing Phase 3 VERIFICATION (Rounds 1-3). The inline prose is a one-paragraph summary + reference pointer to `qor/references/recon-reachability-probe.md` (progressive disclosure per GH #92 doctrine). The skill also gains the Phase 90 Environment block + canonical preflight required by the structural sweep test from Phase 90.

**New `SG-GrepShapedRunclaim-A` doctrine entry**: catalogs the pattern (recon grades on grep-shaped evidence without proving runtime contract), the COREFORGE Phase 371 originating recurrence (persona IPC envelope graded HIGH on grep evidence; implementation surfaced runtime import failures, missing modules, syntax errors in tests, zero non-test importers), the V1 detector, and a V2-reserved enforcement clause that Phase 99 will fill in `/qor-audit` Step 3 Infrastructure Alignment Pass (binding-VETO surface).

**Tests**: 14 + 4 = 18 new tests. `test_reachability_probe.py`: pass + fail per each of the five checks, CLI exit modes (default WARN-only, --exit-on-any), and ONE self-application anchor (`test_probe_self_application_on_broken_fixture_emits_all_five`) that constructs a synthetic broken repo (syntax-errored module + no test reference + no production caller + no manifest + missing call-site) and asserts findings span all five categories — the dogfooding shipping-correctness anchor (the V1 probe must catch a zombie-code claim the first time it runs). `test_reachability_probe_recon_wiring.py`: anchored positive (Round 0 heading + reference pointer present), strip-and-fail negative, positional guard (Round 0 ordered before Phase 3), progressive-disclosure sweep (SKILL.md cites the reference file). All 18 pass twice deterministically. Full suite: 1849 passed, 1 skipped (+18 from Phase 95's 1831 collected pre-phase).

**TDD red-green**: impl GREEN on first pass for the probe module + behavior tests. Phase 90 structural sweep flagged the canonical-preflight requirement during initial regression — recon SKILL.md needed `python -c "import qor.reliability"` (the universal preflight anchor) not a probe-specific check, and the preflight code block had to appear before any `python -m qor.X` prose mention. Both caught and fixed at red-green. README Tests + Ledger badges updated post-substantiate per the structural-currency tests; the Ledger badge update was missed at first push and caught by CI (now corrected).

**V1 boundaries** (declared non_goals): blocking VETO behavior in `/qor-audit` (Phase 99 V2 surface); multi-language probe (Rust/TS/JS — V1 is Python-only); auto-rewriting of recon briefs to apply the downgrade (V1 emits findings; the operator or subagent updates `RESEARCH_BRIEF.md`); caching of probe results across runs. V1 also does NOT touch `qor-audit/SKILL.md` (Phase 99 surface preserved) or any existing Step 0.6 audit lints or Step 4.6.* substantiate gates.

**Dogfooding milestones**: EIGHTH cross-phase exercise of Phase 89's `ci_coverage_lint`. SECOND cross-phase exercise of Phase 95's `skill_size_budget_lint` (recon SKILL.md stays well under 25 KB after Round 0 + Environment block additions; the standing Phase 95 WARN findings on qor-audit + qor-substantiate persist as designed). Phase 90 Environment-block sweep verified on the recon SKILL.md (structural test caught the canonical-preflight requirement at first-run red-green).

**Cluster context**: Phase 96 opens the Tier 1 prompt-surface cluster — 1 of 5 sub-plans. Sequence remaining: 97 (F8 SKILL_REGISTRY drift) → 98 (F5+F6 meta-skill examples → references/) → 99 (V2, GH #108 full close) → 100 (F4 Critical Invariants summaries). Key cross-coupling constraint: F4 must follow Phase 99 V2 to avoid amending the freshly-written Critical Invariants block as soon as V2 lands a new binding VETO.

**Decision**: Phase 96 implemented; audit PASS on iter-1. Substantiated as v0.67.0 (feature → minor bump). Opens the Tier 1 prompt-surface cluster.

## Phase 97 (v0.67.1 — 2026-05-23): SKILL_REGISTRY per-category drift reconciliation (F8)

Hotfix closing the F8 internal prompt-surface review finding. The registry at HEAD declared 30 total skills across four categories, which happened to match the actual total only by offset cancellation: sdlc undercounted by 1 (missing qor-ideate), meta undercounted by 1 (missing qor-ab-run), memory was internally consistent. A total-only currency test passed while two categories silently drifted.

**Reconciliation**: snapshot date updated 2026-04-29 → 2026-05-23; sdlc count 6 → 7 with qor-ideate row added; meta count 11 → 12 with qor-ab-run row added; governance (6) and memory (7) unchanged (already correct). The actual total is 32 .md files across the four categories (was 30 declared with offset cancellation).

**New test `tests/test_skill_registry_per_category_currency.py`** (~140 LOC, 7 assertions): per-category currency checks for governance/sdlc/memory/meta; inverse-drift sweep (every actual .md file is referenced by name in its category's table); cross-category drift guard (skill at path X must be listed in category X's table); arithmetic guard (any documented "Total" line must equal sum-of-per-category counts). The per-category granularity is the structural countermeasure preventing total-cancellation masking — F8 cannot recur the same way.

**TDD red-green**: 3 of 7 tests failed against the drifted registry (per-category sdlc + per-category meta + inverse-drift sweep); all 7 green post-reconciliation. The new test would have caught F8 the first time it ran. All pass twice deterministically.

**Lessons incorporated from Phase 96**: post-substantiate currency tests (README badges, SYSTEM_STATE, CHANGELOG) were re-run AFTER appending ledger entries — caught three drift omissions in a single local regression pass (change_class label not in valid set, CHANGELOG missing v0.67.0 section, README test badge stale 1850 → 1857 needed). Phase 96 caught the equivalent omissions only at CI time. The improvement is process discipline, not new code.

**Files touched** (6): `docs/SKILL_REGISTRY.md`, `tests/test_skill_registry_per_category_currency.py` (NEW), `docs/plan-qor-phase97-skill-registry-per-category-drift.md` (NEW), `README.md` (Tests badge + Ledger badge), `CHANGELOG.md` (v0.67.0 retroactive backfill + v0.67.1 section), `pyproject.toml` (0.67.0 → 0.67.1).

**V1 boundaries** (declared non_goals): changing the registry's counting methodology; cross-referencing the registry to dist variant manifests; auto-regenerating registry from disk state (V2 candidate).

**Dogfooding milestone**: F8 is itself a registry-currency finding; Phase 97 reconciles the registry AND adds the structural test that would have caught F8 the first time it ran. The TDD red-green sequence IS the dogfooding shipping-correctness anchor.

**Cluster context**: Phase 97 closes the SECOND of five Tier-1 prompt-surface sub-plans (96 → 97 → 98 → 99 → 100). Cluster progress: 2 of 5 shipped. The lightest-touch phase in the cluster (L1 risk grade; hotfix bump).

**Decision**: Phase 97 implemented; audit PASS on iter-1. Substantiated as v0.67.1 (hotfix → patch bump).