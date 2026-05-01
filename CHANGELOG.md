# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Merkle seal hashes for each release are recorded in `docs/META_LEDGER.md`; this
file is the user-facing narrative.

## [Unreleased]

## [0.40.0] - 2026-05-01

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

Phase 54: AI provenance metadata + EU AI Act + AI RMF doctrine + subagent scaffolding + override-friction escalator. Bundles Priorities 2/4/5 from `docs/research-brief-prompt-logic-frameworks-2026-04-30.md`. Closes EU AI Act Art. 13/50 transparency and Art. 14 oversight surfaces; aligns with NIST AI RMF 1.0 GOVERN/MAP/MEASURE/MANAGE and AI 600-1 GenAI Profile §2.7+§2.8.

### Added
- **AI provenance metadata in gate artifacts** (Phase 54): new `qor/gates/schema/_provenance.schema.json` (`$ref`'d from all six phase schemas) declaring `{system, version, host, model_family, human_oversight, ts}`. `human_oversight` enum: `pass | veto | override | absent` — operator decision per gate. New `qor/scripts/ai_provenance.py` (~140 LOC) with `build_manifest()` + `HumanOversight` enum. Auto-derives `version` from `pyproject.toml`, `host` from `qor.scripts.qor_platform.current()`, `model_family` from `QOR_MODEL_FAMILY` env (suppressible via `QOR_PROVENANCE_QUIET=1`). All six SDLC + governance skills wired to call `build_manifest` and pass through `gate_chain.write_gate_artifact(... ai_provenance=manifest)`. Closes EU AI Act Art. 13/50 transparency surface and NIST AI RMF MEASURE-2.1 / MANAGE-1.1 evidence-collection contract.
- **`qor-logic compliance ai-provenance` subcommand**: aggregates per-session provenance manifests across `.qor/gates/<sid>/*.json`. Suitable for inclusion in operator AI Act Art. 50 transparency packages. New `qor/cli_handlers/compliance.py` (~110 LOC) hosts this plus extracted `do_report` and new `do_sprint_progress`.
- **`qor-logic compliance sprint-progress` subcommand**: reads the latest `docs/research-brief-*.md`, parses Recommendations Priority headings, walks META_LEDGER for SESSION SEAL entries citing each Priority's phase, emits a sprint-progress table. New `qor/scripts/sprint_progress.py` (~95 LOC).
- **EU AI Act doctrine** (`qor/references/doctrine-eu-ai-act.md`): applicability classification (Qor-logic is *not* high-risk per Annex III; operator inheritance for downstream high-risk systems); article-by-article mapping for Art. 9, 10, 12, 13, 14, 15, 50, 72; Annex IV technical-documentation guidance.
- **AI RMF doctrine** (`qor/references/doctrine-ai-rmf.md`): GOVERN/MAP/MEASURE/MANAGE function-by-function mapping plus AI 600-1 GenAI Profile §2.4/§2.7/§2.8/§2.10/§2.12 mapping. Forward-only evidence-collection contract starting Phase 54.
- **Plan template `impact_assessment` block**: optional in plan top-matter; required when `high_risk_target: true`. Five sub-fields (purpose, affected_stakeholders, identified_risks, mitigations, residual_risks) per AI RMF MAP-3.1 / MAP-5.1. New Step 1c "Impact assessment dialogue" in `/qor-plan` SKILL.md.
- **Subagent tool-scope advisory frontmatter**: `permitted_tools:` and `permitted_subagents:` keys added to all six SDLC + governance skill YAML frontmatters. Declarative-only this phase; Phase 55 candidate wires Cedar-based admission enforcement.
- **Override-friction escalator** (`qor/scripts/override_friction.py`, ~80 LOC): counts `gate_override` events per session; threshold = 3 (symmetric with cycle-count escalator); raises `OverrideFrictionRequired` from `gate_chain.emit_gate_override` when threshold reached and no `justification` (>=50 chars) supplied. All six gate-checking skills wired to handle the exception. Closes OWASP LLM Top 10 LLM08 (Excessive Agency) strengthening + EU AI Act Art. 14.
- **`shadow_event.schema.json` `justification` field**: optional minLength 50 string; populated by `override_friction.record_with_justification` when threshold-friction is supplied.
- **Doctrine §12 "Override-friction escalator"** appended to `qor/references/doctrine-governance-enforcement.md`.

### Changed
- **CLI subcommand-handler split** (closes Pass-1 razor-overage): `qor/cli.py` 227 LOC → ~190 LOC after compliance handler bodies extracted to `qor/cli_handlers/compliance.py`. Headroom for Phase 55+ subcommand additions without re-hitting the cap. Tests under `tests/test_compliance_report_post_phase52.py` and `tests/test_nist_compliance.py` updated to import from the new location.
- **`qor.scripts.validate_gate_artifact`** uses a `referencing.Registry` to resolve `$ref` across local schemas — required for the `_provenance.schema.json` cross-reference. Backward compatible.
- **CLAUDE.md Authority line** appends `eu-ai-act` and `ai-rmf` doctrine references.

### Security
- Aligns Qor-logic with **EU AI Act (Reg. 2024/1689)** Art. 12 (logging, exemplary), Art. 13 (transparency), Art. 14 (oversight, strong), Art. 15 (cybersecurity), Art. 50 (transparency of AI-generated content). Aligns with **NIST AI RMF 1.0** GOVERN/MAP/MEASURE/MANAGE and **AI 600-1 GenAI Profile** §2.7 + §2.8. Sprint context: Phase 54 of a five-phase compliance sprint per `docs/research-brief-prompt-logic-frameworks-2026-04-30.md`; Phase 55 (model-pinning + Cedar-enforced subagent admission + SBOM) and Phase 56 (secret-scanning gate) remain queued.

## [0.39.0] - 2026-04-30

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

Phase 53: prompt-injection defense + path canonicalization + intent-lock anchored regex. Closes OWASP LLM Top 10 (2025) **LLM01 Prompt Injection** (HIGH) at the audit-prose layer for operator-authored governance markdown. Aligns with NIST AI 600-1 §2.7 and EU AI Act Art. 15. Closes OWASP (2021) LOW-4 (intent-lock substring-PASS regex) — zero residual OWASP (2021) MEDIUM/LOW findings open. First phase of a five-phase compliance sprint per `docs/research-brief-prompt-logic-frameworks-2026-04-30.md`.

### Added
- **OWASP LLM01 prompt-injection defense** (Phase 53): canary catalog at `qor/scripts/prompt_injection_canaries.py` (six pattern classes: instruction-redirect, role-redefinition, pass-coercion, meta-override, unicode-directionality, hidden-html), with frozen `CANARIES` tuple, `scan(content)` API, and argv-form CLI (`python -m qor.scripts.prompt_injection_canaries --files ...` plus `--mask-code-blocks` for documentation scanning). Integrated into `/qor-audit` Step 3 as new Prompt Injection Pass that runs before the Security Pass; any canary hit forces VETO with `findings_categories: ["prompt-injection", ...]` plus a severity-3 `prompt_injection_detected` shadow event.
- **Cedar `forbid` rule for governance markdown**: `qor/policies/owasp_enforcement.cedar` carries a fifth rule on `Code::"governance"` resources whose `has_prompt_injection_canary` attribute is True. Commit-time complement to the audit-time pass; two enforcement points, single source of truth (`CANARIES`).
- **Per-resource-kind attribute helper**: new `qor/policy/resource_attributes.py` exposes `compute_governance_attributes(path, content)` and `is_governance_path(path)`. Localizes governance-classification logic without bloating the generic evaluator. Path filter is a literal allowlist for `.md` files under `docs/` or `qor/references/`.
- **Doctrine**: `qor/references/doctrine-prompt-injection.md` (threat model, canary catalog, refusal protocol, out-of-scope limits). Cross-linked from `doctrine-shadow-genome-countermeasures.md` SG-PromptInjection-A.
- **`prompt-injection` finding category**: added to `qor/gates/schema/audit.schema.json` `findings_categories` enum and `qor/scripts/findings_signature.py` `_VALID_CATEGORIES` frozenset.

### Changed
- **Intent-lock anchored PASS regex** (closes Apr-16 OWASP LOW-4): `qor/reliability/intent_lock.py:_audit_has_pass` was `re.search("VERDICT.*PASS", body, re.IGNORECASE)`, which admitted substring "PASS" mentions in narrative prose. Now anchors to a multiline-anchored canonical verdict line (`^Verdict:\s*PASS$` with markdown-bold tolerance and `:`/`-` separator support). After Phase 53: zero residual OWASP (2021) MEDIUM/LOW findings open.
- **Path canonicalization** (DRIFT-1, DRIFT-2): `qor/skills/sdlc/qor-research/SKILL.md`, `qor/skills/governance/qor-substantiate/SKILL.md`, `qor/skills/meta/qor-bootstrap/SKILL.md`, and the five agent files under `qor/agents/` no longer reference legacy `.failsafe/governance/` directory or `memory/failsafe-bridge.md`. Replaced with current canonical paths (`docs/`, `.agent/staging/`, `.qor/gates/<session_id>/`).

### Security
- Closes OWASP LLM Top 10 (2025) **LLM01 Prompt Injection** at the audit-prose layer for the operator-authored governance markdown surface. Aligns with NIST AI 600-1 §2.7 (Information integrity / prompt injection) and EU AI Act Art. 15 (cybersecurity dimension). Sprint context: Phase 53 of a five-phase compliance sprint per `docs/research-brief-prompt-logic-frameworks-2026-04-30.md`; subsequent phases planned for AI provenance metadata (54), subagent least-privilege + model-pinning (55), secret-scanning gate (56), override-friction escalator (57).

## [0.38.0] - 2026-04-30

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

Phase 52: structural enforcement + retroactive remediation. First phase in repo history to land via proper /qor-plan + /qor-audit + /qor-implement + /qor-substantiate skill invocations with all four `.qor/gates/<sid>/*.json` gate artifacts written. Closes G-1 (SSDF tag evidence in ledger), G-3 root cause (skill-protocol bypass), and the retroactive Phase 46/48/49 VETOes from the three-skill audit corpus.

### Added
- **Gate-chain completeness enforcement** (Phase 52, keystone): new `qor/reliability/gate_chain_completeness.py` (103 lines, pure functions, CLI entrypoint via `python -m`). Walks SESSION SEAL ledger entries with phase >= 52; asserts `.qor/gates/<sid>/{plan,audit,implement,substantiate}.json` all exist for each. Wired into `/qor-substantiate` Step 7.8 + new `gate-chain-completeness` job in `.github/workflows/ci.yml` (blocks PR merges to main).
- **Skill-active provenance binding** (Phase 52): `qor/scripts/gate_chain.py` `write_gate_artifact()` reads `QOR_SKILL_ACTIVE` env var and refuses (raises `ProvenanceError`) on absence/mismatch. Closes the surface where any caller could write gate artifacts without skill provenance. `QOR_GATE_PROVENANCE_OPTIONAL=1` autouse fixture in `tests/conftest.py` bypasses for test compatibility.
- **NIST SSDF tag emission** (Phase 52, closes G-1): new `qor/scripts/ssdf_tagger.py` (99 lines) maps `change_class` + `files_touched` to SSDF practice IDs. `/qor-substantiate` Step 7.4 emits `**SSDF Practices**:` line into SESSION SEAL entry body before content_hash. Forward-only (Phase 52+); historical entries grandfathered. `qor.cli compliance report` now shows non-zero coverage starting from this seal.
- **3 structured SG countermeasures** (Phase 52): SG-SkillProtocolBypass (skill markdown executed without runtime provenance), SG-VacuousLint (self-exempting cutoff in commit-walking lints), SG-RecursiveBashInjection (plan that forbids shell-interpolation reintroduces it). Promoted from narrative ledger commentary to structured `qor/references/doctrine-shadow-genome-countermeasures.md` entries with detection + countermeasure + verification hint.

### Changed
- **Phase 46 razor-overage remediation** (closes retroactive VETO): `tests/test_doctrine_test_functionality.py` (was 285 lines) split via new `tests/_helpers.py` (45 lines, shared `proximity` + `strip_section` + `fenced_block_after`) and companion `tests/test_doctrine_test_functionality_negative_paths.py`. Both files now ≤250 lines (158 + 145). 20 tests still GREEN.
- **Phase 48 presence-only test remediation** (closes retroactive VETO): old `test_install_drift_check_emits_qor_logic_fix_string` (read source bytes + asserted substring without invoking unit) DELETED. Replaced by `tests/test_install_drift_check_subprocess.py` which subprocess-invokes `install_drift_check.main()` and asserts on captured output per Phase 46 doctrine.
- **Phase 49 self-exempting cutoff remediation** (closes retroactive VETO): new `tests/test_attribution_tiered_negative_paths.py` adds 6 fixture-based synthetic-violator tests. Closes the SG-VacuousLint anti-pattern at first run.
- **Doctrine update**: `qor/gates/chain.md` lines 34, 74 — "for future wiring" / "future work" prose updated to "Phase 52 wiring". `qor/references/doctrine-nist-ssdf-alignment.md` gains `### Phase 52 wiring (forward-only emission)` subsection. `qor/references/doctrine-governance-enforcement.md` § Skill Integration cited.

## [0.37.0] - 2026-04-29

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

Phase 50: skill-prose filesystem validation contract. Closes G-2 from `docs/compliance-re-evaluation-2026-04-29.md`.

### Added
- **Skill-prose filesystem validation contract** (Phase 50): skill prose performing filesystem operations on operator-controlled identifiers (e.g., `.qor/session/current`) MUST cite the canonical validator helper. `qor/references/doctrine-owasp-governance.md` §A03 gains a "Skill-prose worked example" paragraph naming the contract. `/qor-help --stuck` Mode protocol step 1 routes through `qor.scripts.session.current()` (which reads + validates against `SESSION_ID_PATTERN`) instead of naive marker reads. `qor/skills/sdlc/qor-implement/SKILL.md` and `qor/skills/governance/qor-substantiate/SKILL.md` Step 5.5 / Step 4.6 bash one-liners updated: `cat .qor/session/current` → `python -c "from qor.scripts.session import current; print(current() or 'default')"`. New lint `tests/test_skill_prose_filesystem_validation.py` (5 tests with proximity-anchor + strip-and-fail per Phase 46 doctrine) prevents regression.

## [0.36.0] - 2026-04-29

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

Phase 49: tiered attribution-trailer policy + README badge currency enforcement. Closes G-3 and G-4 from `docs/compliance-re-evaluation-2026-04-29.md`.

### Added
- **Tiered attribution policy** (Phase 49): `qor/references/doctrine-attribution.md` gains a `## Tiered usage` section defining required attribution form per surface — seal commits use full canonical (3 lines); plan/audit/implement commits use compact `Co-Authored-By:` only; PR descriptions use full PR-body footer; CHANGELOG and GitHub releases use the italic attribution line once per version. New `qor.scripts.attribution.commit_trailer_compact()` helper for the compact form. `ATTRIBUTION.md` gains a `## Tiered usage (quickref)` table. Locked by `tests/test_attribution_tiered_usage.py` (9 tests) with proximity-anchored assertions paired with strip-and-fail negative-paths per Phase 46 doctrine. Cutoff: versions ≥ 0.36.0; older commits/CHANGELOG sections grandfathered.
- **README badge currency enforcement** (Phase 49): new `qor/scripts/badge_currency.py` (~140 lines, pure functions) parses README literal-count badges (Tests, Ledger, Skills, Agents, Doctrines) and asserts them against current truth. CLI: `python -m qor.scripts.badge_currency`. Wired into `/qor-substantiate` Step 6.5: ABORTs seal on mismatch when `change_class ∈ {feature, breaking}`. Hotfix exempt. Locked by `tests/test_readme_badge_currency.py` (8 tests) and `tests/test_substantiate_badge_currency_wiring.py` (6 defensive tests). `qor/references/doctrine-governance-enforcement.md` gains a `### Badge currency` subsection under §8 Install Currency. Closes the systemic violation surfaced post-Phase-48 where Phases 45/46/48 each shipped with stale README badges.

## [0.35.0] - 2026-04-29

Phase 48: install-time UX/discoverability + canonical CLI rename + `/qor-help` conversational evolution.

### Added
- **`qor-logic` canonical CLI** (Phase 48): `pyproject.toml` `[project.scripts]` declares both `qor-logic` (canonical) and `qorlogic` (backwards-compat alias) mapping to `qor.cli:main`. `argparse` `prog="qor-logic"`; `--version` emits `qor-logic <semver>`. All operator-facing prose, skill prompts, references, README, and system-tier docs (`docs/operations.md`, `docs/policies.md`) updated. Filesystem state paths (`.qorlogic/config.json`, `.qorlogic-installed.json`) preserved for operator data integrity. New tests `tests/test_cli_rename.py` lock both entry points and the program-name output.
- **Conversational `/qor-help`** (Phase 48): `/qor-help` evolves from static catalog into a three-mode skill. Bare invocation shows the catalog plus a new ASCII SDLC flow chart and a "How to use /qor-help" intro. `/qor-help --stuck` reads `.qor/session/current` and `.qor/gates/<sid>/*.json` to infer SDLC position and recommend the next skill with rationale. `/qor-help -- "<free-form question>"` routes the question against the catalog plus current state. All modes are read-only; recommendation only. Locked by `tests/test_qor_help_conversational.py` with proximity-anchored assertions paired with strip-and-fail negative-path tests; the ASCII chart is verified plain-ASCII (round-trips through `body.encode('ascii')`) and the SDLC phases appear in left-to-right order.

### Changed
- **Script discoverability post-install** (Phase 48): the three remaining path-form `python qor/scripts/<name>.py` invocations in skill prose are now `python -m qor.scripts.<name>`, resolving against the installed package from any CWD. `doctrine-governance-enforcement.md` §138 rewritten to make the `python -m` rule symmetric across both `qor/scripts/` and `qor/reliability/` (previously covered only `reliability/`). Doctrine §92 prose example also updated (`python qor/scripts/session.py new` → `python -m qor.scripts.session new`). New lints `tests/test_installed_import_paths.py::test_no_path_form_qor_scripts_invocations` and `::test_no_path_form_qor_reliability_invocations` prevent regression. Closes the gap left by Phase 35 (which fixed only `qor/reliability/`).

## [0.34.0] - 2026-04-29

Phase 47: seal entry check — structural countermeasure for SG-AdjacentState-A (the bookkeeping-gap class that allowed Phase 46's first substantiate to seal at v0.33.0 without writing META_LEDGER entries).

### Added
- **`qor/reliability/seal_entry_check.py`**: pure-function reliability gate. Exposes `check(ledger_path, phase_num) -> SealEntryResult` and a CLI `python -m qor.reliability.seal_entry_check --ledger <path> --plan <path>`. The helper reads the ledger, asserts the latest entry is a SESSION SEAL for the given phase, verifies the chain hash is internally consistent (`chain_hash == chain_hash(content_hash, previous_hash)`), then runs full chain verification via `ledger_hash.verify()`. Single source of truth = the ledger; no caller-supplied Merkle seal expectation.
- **`/qor-substantiate` Step 7.7 (Post-seal verification)**: new step inserted between Step 7.6 (Stamp CHANGELOG) and Step 8 (Cleanup Staging). Runs `seal_entry_check` after Step 7 (Final Merkle Seal) writes the entry. Bash one-liner uses hardcoded `python -c "from qor.scripts.governance_helpers import current_phase_plan_path; print(current_phase_plan_path())"` to derive the plan path — no shell-variable interpolation into Python literals — then invokes the helper via argv-form `--plan "$PLAN_PATH"`. ABORT on non-zero exit leaves the session unsealed.
- **15 new tests**: 9 behavioral tests in `tests/test_seal_entry_check.py` (covering happy path, missing-seal, phase mismatch, internal chain inconsistency, full chain failure, the meta-test `test_check_replays_phase_46_original_gap` proving the new gate would have caught the historical Phase 46 substantiate gap, and `test_cli_rejects_path_with_shell_metacharacters_safely` confirming argv-form eliminates the OWASP A03 vector); 6 defensive wiring tests in `tests/test_substantiate_seal_entry_wiring.py` using proximity-anchor + strip-and-fail pattern from Phase 46 doctrine, with three direct countermeasures locking V-1 (post-Step-7 placement), V-2 (no `$MERKLE_SEAL` reference), V-3 (no `python -c` shell-interpolation) against future drift.

## [0.33.0] - 2026-04-28

### Added
- **Test functionality doctrine** (Phase 46): new `qor/references/doctrine-test-functionality.md` codifying the "test functionality, not presence" principle and wiring enforcement language into the four SDLC gate skills. `/qor-plan` Step 4 forbids presence-only test descriptions; Step 5 review checklist requires each test description to name the behavior it confirms. `/qor-audit` gains a Test Functionality Pass between Section 4 Razor and Dependency Audit (VETO any plan whose described tests do not invoke the unit). `/qor-implement` Step 5 (TDD-Light) requires the failing test invoke the unit and assert against its output; Step 9 scans newly-added tests for the `assert <substring> in <file_text>` family. `/qor-substantiate` Step 4 Test Audit refuses to seal if a phase-added test is presence-only. `CLAUDE.md` Authority line updated. Cross-references SG-035 ("doctrine-content test unanchored"). Locked by `tests/test_doctrine_test_functionality.py` with proximity-anchored regex assertions paired with strip-and-fail negative-path tests so the doctrine test cannot itself decay into a presence-only check. Variant artifacts regenerated under `qor/dist/variants/`.

## [0.32.0] - 2026-04-28

Phase 45: attribution trailer convention. Implements GitHub issue #18.

### Added
- **`qor/scripts/attribution.py`**: pure-function helper exposing three string-returning functions — `commit_trailer(model=...)`, `pr_footer(model=..., defects_list=..., comparison_doc_path=...)`, and `changelog_attribution_line()`. Module-level constants (`_SDK_NAME`, `_SDK_URL`, `_QOR_URL`, `_MODEL_EMAIL`) are the single source of truth; every default surface accepts a kwarg override so a fork rebranding the SDK or pointing at a different canonical URL needs no code changes outside the call site. Functions are pure: no I/O, no env reads, no time/random/network coupling.
- **`qor/references/doctrine-attribution.md`**: full doctrine — purpose, when-to-apply scope (only commits/PRs/releases produced under `/qor-bootstrap → /qor-plan → /qor-audit → /qor-implement → /qor-substantiate`), three canonical strings captioned with the helper function names that produce them, helper API contract, narrowly-scoped emoji exception (the leading robot emoji on bot-attribution trailer text is the single carve-out from CLAUDE.md's no-non-ASCII-in-data rule), worked example citing issue #18 + BicameralAI MCP #59.
- **`ATTRIBUTION.md`** (root): one-screen quick-ref with copy-pasteable canonical strings; pointers to the doctrine for rationale and to the helper for the canonical source.
- **CLAUDE.md Authority line**: now references `[attribution](qor/references/doctrine-attribution.md)` alongside the existing `token-efficiency`, `test-discipline`, and `governance-enforcement` doctrines.
- **15 new tests** (`tests/test_attribution.py` + `tests/test_attribution_docs_consistency.py`): 9 unit tests pinning canonical output and override semantics, 1 functional test piping the rendered trailer through `git interpret-trailers --parse` to confirm `Co-Authored-By:` is recognized as a valid git trailer (catches spacing/bracket/separator drift that pure presence-tests would miss), and 5 drift-guard tests asserting the helper's output appears verbatim in `ATTRIBUTION.md` and the doctrine and that `CLAUDE.md` Authority line links the doctrine.


## [0.31.1] - 2026-04-24

### Fixed
- **Phase 41 regex regression** (Phase 44): `qor/scripts/ledger_hash.py` now accepts the standard SESSION SEAL convention `**Chain Hash (Merkle seal)**:` and `**Content Hash (session seal)**:` markup. The strict `**Field**` anchor introduced in Phase 41 silently skipped 7 ledger entries with parenthetical-suffix labels (entries #126, #129, #132, #133, #137, #140, #143). Verifier metric: pre-fix 104 OK / 39 skipped; post-fix 112 OK / 32 skipped. Anti-vacuous-green guard added to `tests/test_ledger_hash.py` asserting that every modern entry (≥ #116) with hash markup verifies, would have caught the original Phase 41 regression at audit time. See `docs/META_LEDGER.md` Entry #146 (Phase 44 seal).

## [0.31.0] - 2026-04-24

Phase 41: ledger_hash verifier regex robustness. Resolves GitHub issue #13.

### Added
- **Fenced-form Content/Previous Hash parsing**: `qor/scripts/ledger_hash.py` `CONTENT_HASH_RE` and `PREV_HASH_RE` now accept both inline-backtick `` `<hex>` `` and fenced `= <hex>` forms, symmetric with `CHAIN_HASH_RE`. Real ledgers using fenced Content/Previous markup now verify cleanly where they previously skipped.

### Changed
- **Bounded-span discipline** (issue #13 root cause): all three hash-field regexes now use a non-greedy span bounded by negative lookahead on the next `**FieldName**:` marker; cannot sweep across field boundaries into unrelated hex values (e.g., a `**Plan Hash**` value previously captured as `Content Hash`). The `re.DOTALL` flag is no longer needed; `[\s\S]` is explicit inside the bounded span.
- **`CHAIN_HASH_RE` bold anchor**: now requires `\*\*Chain Hash\*\*` per Phase 41's anchor-symmetry rule. Prose mentions of "Chain Hash" no longer capture unrelated backtick-hex values.
- **`qor-validate` SKILL.md** (Steps 3, 4, 7): replaced three stale references to `.claude/commands/scripts/validate-ledger.py` (a stub path not produced by `qorlogic install`) with the canonical `qor/scripts/ledger_hash.py` module + `qorlogic verify-ledger` CLI. Variant SKILL.md files regenerated via `python -m qor.scripts.dist_compile`.

### Fixed
- **Existing test fixtures using unanchored `Chain Hash = {hash}` markup** (5 lines across 3 tests in `tests/test_ledger_hash.py`) updated to bold-anchored form, plus `capsys`-based stdout assertions (`OK   Entry #N:`) preventing vacuous-green regression where `rc == 0` is satisfied by silent-skip rather than verified-chain.

## [0.30.0] - 2026-04-20

Phase 39b Phases 1+2: Agent Team A/B orchestration + persona sweep.

### Added
- **`/qor-ab-run` skill** (`qor/skills/meta/qor-ab-run/`): orchestrates persona-vs-stance Identity Activation A/B measurement via parallel Task-tool subagent dispatch (20 concurrent calls in one message). Zero external dependency, zero marginal cost. `subagent_type: "general"` per doctrine §4. Subagent prompt template with `{VARIANT_IDENTITY_ACTIVATION_BLOCK}` + `{FIXTURES_CONCATENATED}` placeholders.
- **`qor/scripts/ab_aggregator.py`** (pure Python, no LLM coupling): brace-balanced JSON extractor (malformed-tolerant), per-(skill,variant) mean+stddev aggregation, ±5pp tie-threshold winner declaration, canonical markdown rendering.
- **Delegation-table** row for `/qor-ab-run`; **`/qor-help` catalog** entry.

### Changed
- **Persona sweep** (S3 from Phase 39b): 5 decorative `<persona>` tags removed — `qor-status`, `qor-help`, `qor-repo-scaffold`, `qor-bootstrap`, `qor-document`.
- **R4**: `qor-debug` line 108 `subagent_type: "general"` constraint now cross-references `doctrine-context-discipline.md` §4.
- **R5**: `qor-document` line 251 split into two discrete sentences — Identity Activation stance (main thread) vs `qor-technical-writer` subagent pairing — citing doctrine §1.2/§1.3 to prevent mechanism conflation.

### Changed
- **R3 Identity Activation rewrite** for `/qor-audit` + `/qor-substantiate` is **conditional on A/B evidence**. Operator invokes `/qor-ab-run` to produce `docs/phase39-ab-results.md`; `test_identity_activation_matches_ab_winner_if_results_exist` auto-applies the rewrite rule when results declare `winner: "stance"` for a skill. Without evidence, current persona-named Identity Activation is retained.
- **LOAD_BEARING_PENDING_EVIDENCE registry** (`tests/test_persona_sweep.py`): 19 skills documented as load-bearing by doctrine judgment, awaiting A/B evidence.

## [0.29.0] - 2026-04-20

Phase 39 Phase 1 seal: context-discipline doctrine + A/B corpus fixtures. Anthropic-SDK harness approach withdrawn in favor of Agent Team orchestration (Phase 39b).

### Added
- **`doctrine-context-discipline.md`**: codifies personas as context-prioritization scaffolds for edge-case determinations, evaluated by performance/accuracy/results. Five sections cover the three-mechanism distinction (frontmatter tag vs Identity Activation prose vs subagent invocation), persona evaluation protocol, stance directive discipline, subagent invocation rule (`general` by default; persona-typed requires evidence), and verification protocol requiring `<persona-evidence>` pointers for retained tags. `doctrine-governance-enforcement.md` §11 cross-references.
- **A/B corpus fixtures**: 20 seeded defects at `tests/fixtures/ab_corpus/` spanning 10 `findings_categories` (2 per category; `coverage-gap` and `dependency-unjustified` omitted per plan). Each fixture carries `# SEEDED TEST DEFECT — NOT EXECUTABLE` header. MANIFEST.json uses `line_start`/`line_end` for multi-line defect ranges. 4 hand-authored Identity Activation variant files under `tests/fixtures/ab_corpus/variants/`. Consumed by the Phase 39b Agent Team A/B skill.
- **Tests**: `tests/test_doctrine_context_discipline.py` (3 structural assertions).

### Changed
- Phase 39 Phase 2 scope narrowed: Anthropic-SDK harness (`ab_harness.py`, `ab_live_run.py`, optional `anthropic` dep) withdrawn. Phase 39b will ship `/qor-ab-run` skill that orchestrates the A/B cycle via parallel Task-tool subagents within Claude Code — no external API dependency, no credential management, aligned with the doctrine's "controlled context via subagents" principle.

## [0.28.3] - 2026-04-24

### Fixed
- **Intent-lock HEAD-drift** (Phase 43): `qor/reliability/intent_lock.py` `verify()` now uses `git merge-base --is-ancestor` instead of strict HEAD equality. Captured HEAD must be reachable from current HEAD; current HEAD may be any forward descendant. Eliminates the re-capture-as-SOP anti-pattern observed in Phase 41 and Phase 42 substantiate where the implement commit between Step 5.5 capture and Step 4.6 verify always tripped `DRIFT: head`. Real anti-drift threats (history rewrites, hard resets, branch switches to divergent histories) still caught. See `docs/META_LEDGER.md` Entry #140 (Phase 43 seal).

## [0.28.2] - 2026-04-24

### Fixed
- `test_every_changelog_section_has_tag` no longer blocks phase-seal PRs whose CHANGELOG sections are above the highest existing tag. Pre-release sections are now exempt from the match-a-tag rule, resolving the chicken-and-egg collision with Phase 40's LOCAL-ONLY tag doctrine. See `docs/META_LEDGER.md` Entry #137 (Phase 42 seal).

## [0.28.1] - 2026-04-20

### Fixed
- `.github/workflows/release.yml` now verifies the tag's commit is reachable from `origin/main` before publishing to PyPI; refuses publish otherwise. Closes the pre-merge-publish defect that shipped v0.24.1, v0.25.0, and v0.28.0 from unmerged PR branches. See `docs/META_LEDGER.md` Entry #133 (Phase 40 seal).

## [0.28.0] - 2026-04-20

Procedural surface freeze line. Consolidates phases 36-38 work into a single release: full SG-PlanAuditLoop-A countermeasure set (C1-C4) plus `ci_commands` plan-schema slot. Phase 39 (context-discipline + persona reshape) explicitly deferred pending upstream consumer lockdown.

### Added
- **Two-stage `addressed` flip in `/qor-remediate`** (B19, SG-PlanAuditLoop-A C1): `mark_addressed_pending` (stage 1) / `mark_addressed(review_pass_artifact_path, remediate_gate_path)` (stage 2). Stage 2 verifies the audit gate artifact is `phase: "audit"`, `verdict: "PASS"`, and its `reviews_remediate_gate` field matches the remediate gate being closed; `ReviewAttestationError` raised on any failure, no event mutation. Schema `shadow_event.addressed_pending` optional boolean + `allOf` invariant enforcing `addressed == true AND addressed_reason == "remediated"` implies `addressed_pending == true` (legacy `issue_created`/`stale` paths unaffected). Schema `audit.reviews_remediate_gate` optional `string | null` for the operator signal.
- **Stall-detection infrastructure** (B20 + B21, SG-PlanAuditLoop-A C2-C4): append-only `audit_history.jsonl` alongside singleton audit gate artifact; `findings_signature` module (16-hex-char SHA256 prefix over sorted unique categories, `"LEGACY"` sentinel for absent field, `UnmappedCategoryError` on non-enum); shared `stall_walk.run` helper returning `(count, signature, first_match_ts)`; `cycle_count_escalator.check` K=3 orchestrator; `orchestration_override.record` with session-scoped suppression marker.
- **New 7th `/qor-audit` adversarial pass**: Infrastructure Alignment Pass grep-verifies plan claims (filesystem paths, glob patterns, event types, cross-module signatures, skill-step anchors) against current repo code. New `infrastructure-mismatch` finding category.
- **Schema `audit.findings_categories`**: closed 12-value enum, required when `verdict == "VETO"` via `allOf`/`if-then` conditional.
- **Schema `shadow_event.event_type`**: +`plan-replay`, +`orchestration_override`.
- **Gate-loop classifier union**: `gate_override | orchestration_override` — repeated operator declines escalate via pattern match.
- **`/qor-plan` Step 2c + `/qor-audit` Step 0.5**: cycle-count hooks surface `/qor-remediate` escalation to operator.
- **`ci_commands` required field in `qor/gates/schema/plan.schema.json`** (B22): array with `minItems: 1`, items with `minLength: 1`. Plans authored from Phase 38 forward must declare local-validation commands. Pre-Phase-38 plans grandfathered at test layer. Matching `## CI Commands` template section in `/qor-plan` SKILL.md.
- **Doctrine §10.1-10.5**: Two-stage remediation flip; narrative SG entry closure protocol; audit history + findings signature; cycle-count escalation; operator override + suppression.
- **`SG-InfrastructureMismatch`**: codified countermeasure catalog entry.

### Changed
- 9 existing plan-payload test fixtures updated to include `"ci_commands": ["pytest"]` (fixtures represent Phase-38-era consumers of the schema).

## [0.25.0] - 2026-04-19

### Fixed
- **Installed-mode breakage (SG-Phase35-A)**: package shipped since v0.18.0 was non-functional for `pip install` users. 49 skill-prose Python blocks used `import sys; sys.path.insert(0, 'qor/scripts'); import X` — only works from repo root. Rewritten to `from qor.scripts import X`. `qor/reliability/{intent-lock,skill-admission,gate-skill-matrix}.py` renamed to snake_case; skill subprocess invocations now `python -m qor.reliability.<name>` (path-independent). Two bare intra-`qor/scripts` imports (`doc_integrity.py`, `doc_integrity_strict.py`) qualified. Regression guards in `tests/test_installed_import_paths.py` lock both structural (no hack pattern remains) and runtime (imports resolve) contracts.

### Added
- **Doctrine `doctrine-governance-enforcement.md` §9 Installed-Mode Invariants**: three binding rules — qualified `qor.scripts.*` / `qor.reliability.*` imports in skill prose, snake_case reliability module names, `python -m` invocation pattern.

### Changed
- `qor/reliability/` scripts renamed: `intent-lock.py` → `intent_lock.py`, `skill-admission.py` → `skill_admission.py`, `gate-skill-matrix.py` → `gate_skill_matrix.py`. Git history preserved via `git mv`. Only consumer is skill prose (`/qor-implement` Step 5.5, `/qor-substantiate` Step 4.6); both updated. Tests updated accordingly.

## [0.24.1] - 2026-04-19

### Fixed
- **CLI `__version__` drift (SG-Phase34-A)**: `qor/cli.py` hardcoded `__version__ = "0.18.0"` and never got updated across six releases (v0.18.0 → v0.24.0). `qorlogic --version` printed `0.18.0` even on v0.24.0 installs. `__version__` now reads from `importlib.metadata.version("qor-logic")` at import time; fallback `"0+unknown"` for uninstalled source checkouts. Regression guard `tests/test_cli_version_from_metadata.py` asserts runtime lookup and forbids reintroduction of a SemVer-shaped string literal on the `__version__` line.

## [0.24.0] - 2026-04-19

### Fixed
- **Seal-tag timing bug** affecting v0.19.0–v0.22.0: release tags were placed on the pre-seal HEAD (one commit behind the sealed content) because `create_seal_tag` ran at `/qor-substantiate` Step 7.5, before the seal commit at Step 9.5. Tag creation moved to a new Step 9.5.5 that captures the post-commit SHA via `git rev-parse HEAD` and passes it as a required `commit` argument. See SG-Phase33-A and META_LEDGER Entry #112 for forensic details and affected-tag inventory. Historical tags are not retagged.

### Added
- **Release-doc currency rule** at `/qor-substantiate` Step 6.5. When a plan declares `change_class: feature` or `change_class: breaking`, `check_documentation_currency` now also requires README.md and CHANGELOG.md in `implement.files_touched`. Hotfix is exempt. Catches the pattern where a release ships with stale narrative-doc version claims (SG-Phase32-B).
- **Glossary terms**: `release_docs`, `seal_tag_timing`.
- **Doctrine**: `doctrine-documentation-integrity.md` §5a (release-doc coverage) and `doctrine-governance-enforcement.md` §4 (seal_tag_timing wiring).

### Changed
- `governance_helpers.create_seal_tag` now takes a required `commit: str` positional argument. No HEAD-default fallback. Calling without `commit` raises `TypeError`.
- `check_documentation_currency` signature extended with optional `plan_payload: dict | None = None`. Legacy call sites without the kwarg preserve pre-Phase-33 behavior.

## [0.23.0] - 2026-04-18

### Added
- **Install drift detection** via `qor/scripts/install_drift_check.py`: SHA256-compares source `qor/skills/**/SKILL.md` against the installed copies. Invoked as CLI (`python -m qor.scripts.install_drift_check --host claude --scope repo`) or automatically at `/qor-plan` Step 0.2 as a pre-phase WARN. Fix via `qorlogic install --host <host>`.
- **`/qor-plan` Step 0.2 Install drift nudge** (pre-phase): non-blocking warning when local installed skills lag repo source.
- **Doctrine governance-enforcement §8 Install Currency**: full contract for the drift check, invocation sites, scope boundaries.
- **Check Surface D + E strict-mode is LIVE** at `/qor-substantiate` Step 4.7. `run_all_checks_from_plan(..., strict=True)` is now the default seal-time call; any term-drift or cross-doc conflict raises `ValueError` and aborts substantiation. `legacy` tier still bypasses.

### Changed
- **Check Surface D/E scope fence rewired**: `docs/*.md` is archive-by-default except the 4 system-tier docs (`architecture`, `lifecycle`, `operations`, `policies`); README and CHANGELOG excluded as narrative entry points; archive path patterns replaced by the simpler living-docs allowlist. `check_cross_doc_conflicts` now shares the `_excluded_by_scope_fence` helper with `check_term_drift` (was silently bypassing the fence before Phase 32).
- Glossary receives broad `referenced_by:` adoption across Gate, Shadow Genome, Doctrine, change_class, Substantiate, Check Surface D, and Workflow Bundle to cover all legitimate in-repo consumers.

## [0.22.0] - 2026-04-18

### Added
- **`/qor-substantiate` Step 6.5 Documentation Currency Check**: WARNs at seal time when a phase's `files_touched` includes doc-affecting changes (SKILL.md / doctrine / schema / script) but the 4 system-tier docs (`docs/{architecture,lifecycle,operations,policies}.md`) weren't updated. Operator decides whether to amend docs or continue. Lives in `qor/scripts/doc_integrity_strict.py::check_documentation_currency`. Doctrine §5 of `doctrine-documentation-integrity.md` documents the heuristic.
- **Check Surface D + E scope-fence tuning** (`qor/scripts/doc_integrity_strict.py`): three new exclusion layers -- doctrine-peer (cross-doctrine references not drift), home-directory-peer (siblings discussing shared concepts), and per-entry `scope_exclude: []` glossary frontmatter opt-out.
- **`qor/scripts/doc_integrity_drift_report.py`**: operator CLI producing a Markdown drift report grouped by term. Ad-hoc triage tool.
- **`qor/scripts/pr_citation_lint.py` + `.github/workflows/pr-lint.yml`**: CI lint enforcing `doctrine-governance-enforcement.md` §6 (PR descriptions must cite plan file + ledger entry + Merkle seal).
- **`tests/test_install_sync_with_source.py`**: SHA256-level sync between source SKILL.md files and dist variants (claude / codex / kilo-code). Catches dist drift at CI time.
- **`docs/phase31-drift-triage-report.md`**: 187-line artifact summarizing Phase 2 live drift triage decisions and deferred strict-mode wiring rationale.

### Changed
- `qor/scripts/session.py`: `MARKER_PATH` renamed from `.qor/current_session` to `.qor/session/current` to match bash references in substantiate Step 4.6 and implement Step 5.5. Migration was lossy -- the old marker file carries the rotated Phase 30 session id, the new marker needed manual migration at first Phase 31 substantiate attempt.
- `qor/references/glossary.md`: `Gate` and `Shadow Genome` entries gain 20+ additional `referenced_by:` consumers from the live drift triage.
- `/qor-audit` SKILL.md Documentation Drift section gains an explicit Python block invoking `doc_integrity.render_drift_section` (replacing prose-only narrative).
- `qor-audit-templates.md` gains `<!-- qor:drift-section -->` canonical insertion marker.

## [0.21.0] - 2026-04-18

### Added
- **System-tier documentation topology** at `docs/architecture.md`, `docs/lifecycle.md`, `docs/operations.md`, and `docs/policies.md`. Authored from the existing repo state (chain.md, skills catalog, policies, doctrines). Qor-logic itself can now declare `doc_tier: system` on plans and the check passes. Phase 30 is the first plan to self-substantiate at this tier.
- **`/qor-audit` Step Z** wires audit.json gate artifact writes via `gate_chain.write_gate_artifact` (Phase 29 delivered the SKILL edit; Phase 30 doctrine + live dogfood). Downstream phases can now read structured audit verdicts.
- **Session rotation** via `qor/scripts/session.py::rotate()`. `/qor-substantiate` Step Z calls it after writing `substantiate.json`, so the next `/qor-plan` starts with a clean `.qor/gates/<new_sid>/` directory. Prior session dirs preserved for archaeology. New doctrine section: `doctrine-governance-enforcement.md` §7.
- **Dist recompile on seal**: `/qor-substantiate` Step 8.5 invokes `python -m qor.scripts.dist_compile` automatically so variant outputs (claude / kilo-code / codex / gemini) stay in sync with source skills.
- **Check Surface D (term-drift grep)** and **Check Surface E (cross-doc conflict detection)** in new `qor/scripts/doc_integrity_strict.py`. Lenient-by-default; `strict=True` kwarg routes through `run_all_checks_from_plan`. Both scope-fenced to markdown files; code files excluded.
- **CONTRIBUTING.md**: Phase 29 landed pointer + quickstart; Phase 30 adds full doctrine inventory link from README.
- **Razor compliance forward-regression guards**: `tests/test_doc_integrity_razor_compliance.py` enforces <=250 lines on both `doc_integrity.py` and `doc_integrity_strict.py` (SG-Phase30-A countermeasure).

### Changed
- `/qor-substantiate` Constraints now require `bump_version` to run BEFORE `create_seal_tag` in Step 7.5. Inverted order (bug observed in Phase 29) interdicts on tag-already-exists and forces manual pyproject editing. Paired test locks the contract.
- CLAUDE.md: bare-backtick doctrine paths replaced with markdown links.
- README.md: complete doctrine inventory section added (14 doctrines + patterns + templates + glossary linked).
- 15 `qor/skills/**/SKILL.md` files: XML `<phase>X</phase>` tags lowercased to match YAML frontmatter case (GAP-REPO-06 resolution).
- `.github/workflows/ci.yml` and `.github/workflows/release.yml`: `actions/checkout@v4` gains `fetch-depth: 0, fetch-tags: true` so `test_every_changelog_section_has_tag` finds tags in CI.

### Security
- Check-surface scanners use stdlib `re` only; no new deserialization or subprocess surface. Scope fence explicitly excludes `*.py`, `*.json`, `*.toml`, `*.cedar` and `vendor/` / `fixtures/` / `dist/` directories.

## [0.20.0] - 2026-04-18

### Added
- `/qor-audit` now writes a schema-valid `audit.json` gate artifact at `.qor/gates/<session>/audit.json` (Step Z wiring). Previously missing; downstream phases (`/qor-implement`) had to fall back to gate overrides or hand-written artifacts. Payload carries `target`, `verdict`, `report_path`, and `risk_grade` per `qor/gates/schema/audit.schema.json`.
- `CONTRIBUTING.md` at the repo root (40 lines) -- canonical contributor entry point pointing to CLAUDE.md, gates/chain, delegation-table, workflow-bundles, doctrines, and the glossary in reading order. Quickstart recipe names the `/qor-research -> /qor-plan -> /qor-audit -> /qor-implement -> /qor-substantiate` chain. PR contract delegates to `doctrine-governance-enforcement.md` Section 6 (single source of truth; no duplication).

### Changed
- Glossary orphan adoption: seven `qor/references/glossary.md` entries (`Doctrine`, `Doc Tier`, `Glossary Entry`, `Concept Home`, `Orphan Concept`, `Doc Integrity Check Surface`, `Complecting`) now carry legitimate `referenced_by:` consumers. Closes the Phase 28 doctrine's newly-enforced-doctrine grace gap (SG-Phase29-A) caught during Phase 29 audit pass 1 and resolved before implementation.
- `README.md` gains a one-line link to CONTRIBUTING.md in the quickstart region.

## [0.19.0] - 2026-04-18

### Added
- Documentation-integrity doctrine (`qor/references/doctrine-documentation-integrity.md`) with four tiers (`minimal` / `standard` / `system` / `legacy`) enforced at `/qor-substantiate` time via the new `qor/scripts/doc_integrity.py` module.
- Canonical glossary at `qor/references/glossary.md` with 13 entries covering Phase 28 doctrine terms plus Qor-logic canonical terms (Phase SDLC, Gate, Shadow Genome, Substantiate, Workflow Bundle, change_class, Delegation Table, Complecting). Glossary entries serve simultaneously as concept-map entries (`home:` + `referenced_by:` fields).
- `/qor-plan` Step 1b: dialogue for `doc_tier`, `terms_introduced`, and `boundaries` declarations; Plan Structure top-matter extension.
- `/qor-substantiate` Step 4.7: hard-blocks seal on documentation-integrity violations via `doc_integrity.run_all_checks_from_plan` (topology presence + glossary hygiene + orphan scan). `legacy` tier is the sole documented escape.
- `/qor-audit` Documentation Drift advisory: non-VETO `## Documentation Drift` section in AUDIT_REPORT.md when plan declarations diverge from glossary/topology.

### Changed
- `qor/gates/schema/plan.schema.json` gains optional `doc_tier`, `doc_tier_rationale`, `terms`, and `boundaries` fields. An `if-then` rule enforces that `doc_tier: legacy` requires `doc_tier_rationale`.
- `qor/gates/workflow-bundles.md` example phases list expanded to the canonical seven-phase chain (previously omitted `validate` and `remediate`).

### Security
- New `doc_integrity.parse_glossary` uses `yaml.safe_load` exclusively and rejects documents containing custom tags (SG-Phase24-B countermeasure). Covered by existing `tests/test_yaml_safe_load_discipline.py` scanner.

## [0.18.0] - 2026-04-17

### Added
- `CHANGELOG.md` itself: full backfill v0.3.0 through v0.17.0 plus the "Unreleased" convention going forward.
- `qor/scripts/changelog_stamp.py`: pure-function module that renames `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD` on seal.
- `qor/references/doctrine-changelog.md`: CHANGELOG discipline codified.
- `/qor-substantiate` Step 7.6 stamps the CHANGELOG as part of the seal ceremony; Step 9.5 auto-stage now includes `CHANGELOG.md`.
- Two new lint tests enforce Keep-a-Changelog structure and tag <-> CHANGELOG bijection.

## [0.17.0] - 2026-04-17

### Added
- Per-ground `**Required next action:**` directives in audit reports. Each VETO ground names the correct remediation skill (`/qor-refactor`, `/qor-organize`, `/qor-remediate`, `/qor-debug`) or the Governor for plan-text edits. Canonical mapping codified in `qor/references/doctrine-audit-report-language.md`.
- Repeated-VETO pattern detector (`qor/scripts/veto_pattern.py`): fires when >= 2 consecutive sealed phases each required > 1 audit pass. Emits a severity-3 `repeated_veto_pattern` Shadow Genome event.
- `## Process Pattern Advisory` section appended to every audit report; recommends `/qor-remediate` when the pattern fires (non-blocking).
- `repeated_veto_pattern` added to `qor/gates/schema/shadow_event.schema.json` event_type enum.

### Changed
- Audit-report template: generic "Mandated Remediation" header replaced by per-ground directives.
- `qor-audit` SKILL.md: each pass (Security, OWASP, Ghost UI, Razor, Dependency, Macro-Arch, Orphan) now carries an explicit `**Required next action:**` line.

## [0.16.0] - 2026-04-17

### Added
- `qorlogic seed`: new top-level CLI subcommand. Idempotent scaffold for governance workspaces (`docs/META_LEDGER.md`, `docs/SHADOW_GENOME.md`, `docs/ARCHITECTURE_PLAN.md` + `CONCEPT.md` + `SYSTEM_STATE.md` stubs, `.agent/staging/`, `.qor/gates/`, `.qor/session/`, `.gitignore` section).
- Prompt resilience doctrine (`qor/references/doctrine-prompt-resilience.md`): autonomy classification per skill (`autonomous` | `interactive`). Deep-audit family runs without user prompts; other skills use a single Y/N recovery prompt on missing prerequisites.
- Canonical `skill-recovery-pattern.md` reference with markers `qor:recovery-prompt`, `qor:auto-heal`, `qor:fail-fast-only`, `qor:break-the-glass`.
- Three-tier communication model (technical / standard / plain) via `/qor-tone` session command and `qorlogic init --tone <tier>`. `qor-status` designated as the canonical tone-aware example. Inspired by the MIT-licensed `caveman` project.
- `/qor-tone` skill added to the command catalog.
- `PyYAML>=6` declared as runtime dependency (frontmatter parsing uses `yaml.safe_load` only; unsafe APIs banned codebase-wide).

### Changed
- 11 governance/SDLC skills gained explicit `autonomy` frontmatter; banned over-pause phrases removed or justified with `qor:allow-pause` markers.
- `tests/test_yaml_safe_load_discipline.py` widened to scan both `qor/` and `tests/**/*.py` (excluding deliberate unsafe fixtures).

### Security
- Codebase-wide ban on `yaml.load`, `yaml.load_all`, `yaml.full_load`, `yaml.unsafe_load` enforced by lint; closes SG-Phase24-B and SG-Phase25-A countermeasures.

## [0.15.0] - 2026-04-17

### Added
- Gemini CLI as a first-class host (`qorlogic install --host gemini`). Variant emits TOML command files under `commands/`; frontmatter (`trigger`, `phase`, `persona`) preserved.
- Uniform `--scope {repo,global}` flag on `install`/`uninstall`/`list`/`init` (default `repo`). Applies to all hosts.
- `qor/install.py` module extracted from `qor/cli.py` (Razor remediation).
- `$QORLOGIC_PROJECT_DIR` environment variable for repo-root override.

### Changed
- `qorlogic install --host codex` now reads `variants/codex/` instead of the hardcoded claude variant (bug fix surfaced during Phase 24 audit).
- `HostTarget` shape: now carries `(name, base, install_map)` with prefix-keyed install dispatch. `skills_dir` and `agents_dir` retained as compat properties.

### Removed
- `CLAUDE_PROJECT_DIR` environment variable is no longer consulted. Use `--scope` or `$QORLOGIC_PROJECT_DIR`.

## [0.14.0] - 2026-04-16

### Added
- Cedar-inspired OWASP enforcement policies (`qor/policies/owasp_enforcement.cedar`).
- OWASP Top 10 governance doctrine (`qor/references/doctrine-owasp-governance.md`); OWASP pass wired into `qor-audit` SKILL.md.
- NIST SP 800-218A SSDF alignment: practice tags in ledger entries, `qorlogic compliance report` CLI, `qor/references/doctrine-nist-ssdf-alignment.md`.

### Fixed
- 9 security findings closed (MEDIUM-1..6, LOW-1..6): repo path validation, JSONL warnings, file locking, chain-hash separator, session-id/event-id validation, verdict regex, timezone-aware timestamps, skipped-entry reporting, backward-compatible legacy chain-hash verification.

### Security
- Shadow Genome process-event validation now enforces strict schema compliance on append.

## [0.13.0] - 2026-04-16

### Added
- Cedar-inspired policy evaluator in pure Python (`qor/policy/`). `qorlogic policy check` CLI evaluates request JSON against `*.cedar` policies; supports `permit`/`forbid`, `==` and `in` constraints, `when` conditions, default-deny semantics.
- Codex host resolution (was stub).
- `qorlogic init` CLI subcommand; persists host/profile/scope to `.qorlogic/config.json`.

## [0.12.0] - 2026-04-16

### Added
- `qorlogic install --host <claude|kilo-code|codex>` CLI with target-directory override.
- Manifest emission (`qor/dist/manifest.json`) with SHA256 per file.
- `qorlogic compile` / `qorlogic verify-ledger` CLI subcommands.
- CI workflow gains variant-drift and ledger-hash verification steps.

### Changed
- `qor/scripts/compile.py` renamed to `qor/scripts/dist_compile.py`.

## [0.11.0] - 2026-04-16

### Added
- `qor/resources.py` (`importlib.resources` wrapper) and `qor/workdir.py` (`$QOR_ROOT` or CWD anchor) separate packaged assets from consumer state.
- `pytest -m integration` opt-in marker for install-smoke tests.

### Changed
- 13 sibling imports migrated to package-relative form.
- 11 `REPO_ROOT` reference sites split across `qor.resources` and `qor.workdir`.
- Eliminated `sys.path.insert(...)` from production scripts.

## [0.10.0] - 2026-04-16

### Added
- PyPI packaging foundation: `[tool.setuptools.packages.find]` config, `[tool.setuptools.package-data]` for Markdown/JSON resources, `[project.scripts] qorlogic = qor.cli:main`, `classifiers`/`keywords`/`urls`/`authors`, BSL-1.1 license declaration.
- `.github/workflows/ci.yml` (3 Python x 2 OS matrix).
- `.github/workflows/release.yml` (OIDC trusted publisher flow).

## [0.9.0] - 2026-04-16

### Added
- `/qor-remediate` skill promoted from stub to executable. Five helper scripts: `read_context`, `pattern_match`, `propose`, `mark_addressed`, `emit_gate`.

### Changed
- Parallel-execution rechain: Phase 18 subagent sealed in isolated worktree and rechained from Entry #47 at merge.

## [0.8.0] - 2026-04-16

### Added
- Three reliability scripts under `qor/reliability/`: `intent-lock.py` (captures plan+audit+HEAD fingerprint before implement; re-verified at substantiate), `skill-admission.py` (frontmatter validation), `gate-skill-matrix.py` (verifies every `/qor-*` handoff reference resolves to a real skill).
- Wired into `/qor-implement` Step 5.5 and `/qor-substantiate` Step 4.6.

## [0.7.0] - 2026-04-16

### Added
- SG-036 (grace period), SG-037 (knowledge-surface drift), SG-038 (prose-code mismatch in plans) codified in the Shadow Genome countermeasures doctrine with proximity-anchored tests.

## [0.6.0] - 2026-04-16

### Changed
- `qor-audit` Step 3 cites countermeasures doctrine explicitly.
- `qor-plan` SKILL.md reduced from 278 to 238 lines via `step-extensions.md` reference; keeps Section 4 Razor compliance.

## [0.5.0] - 2026-04-16

### Added
- Shadow Genome countermeasures doctrine (`qor/references/doctrine-shadow-genome-countermeasures.md`) consolidates 9 SG entries (SG-016/017/019/020/021/032/033/034/035). AST-enforced SG-033 test covers `Starred` + `AsyncFunctionDef` node families.
- Proximity-anchored doctrine tests with negative-path validation.

## [0.4.0] - 2026-04-15

### Added
- Shadow attribution dual-file infrastructure: classification-aware `append_event(attribution=...)`, collector upstream-first fallback, `write_events_per_source` helper.
- 7 writer call sites updated to the new attribution API.
- 4 skills reference the shadow-attribution doctrine.

## [0.3.0] - 2026-04-15

### Added
- Governance enforcement pipeline: phase branching, version bumping, tagging, GitHub hygiene. First self-hosted use of `bump_version` (0.2.0 -> 0.3.0 via its own helper).

---

Earlier versions (< v0.3.0) shipped internally before the repo went public; see `git log` for migration pedigree.
