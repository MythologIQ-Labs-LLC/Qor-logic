# Qor-logic System State

**Snapshot**: 2026-06-10
**Chain Status**: ACTIVE. Phase 161 (hotfix, v0.110.3) closed a `PYTHONHASHSEED`-coupled CI flake; Phase 162 (feature, v0.111.0) implemented GH #231 Option 1 -- a WARN-first ledger base-currency gate; this entry (Phase 163, hotfix, v0.111.1) closes a release-pipeline gap: the PyPI publish is now gated on the CI suite passing for the tagged commit. (PyPI is a continuous 0.109.0->0.109.5 + 0.110.0->0.110.3 + 0.111.0 line, now + 0.111.1, as of 2026-06-10.)
**Phase**: Phase 163 (hotfix; release-pipeline integrity). `release.yml` had `build -> publish` with NO test step, so a publish was coupled to the tests passing only by operator discipline (verify PR CI before approving the `pypi` environment) -- an early approval or a broken `main` could ship untested code. New `qor/scripts/release_ci_gate.py` (pure, fail-closed `evaluate(runs, head_sha)` -> ok iff a `CI` run for that exact SHA concluded `success`; `main` reads the `gh api` runs JSON from stdin and exits 1 otherwise) is wired into BOTH the build (early) and publish (enforcement) jobs before their work, with `actions: read` added to each. The workflow runs `gh api .../workflows/ci.yml/runs?head_sha=<SHA>` and pipes it to the gate; a publish cannot proceed unless CI was green for the tagged commit, regardless of approval timing. Mirrors the existing tag-reachability double-gate; the 13 release-immutability/guard properties (jobs=={build,publish}, id-token once, SHA-pinned) still hold. Self-application: Phase 163's own release (after merge) is the first gated by this. The fix turns publish-after-green from discipline into structure.
**Prior phase**: Phase 162 (feature; GH #231 ledger base-currency gate).
**Prior phase**: Phase 161 (hotfix; deterministic merge-velocity test naming).
**Prior phase**: Phase 160 (hotfix; documentation currency for GAP-GOV-05 + README doctrine-inventory enforcement test).
**Prior phase**: Phase 159 (hotfix; closed GH #223). `seal_entry_check` plan-name fallback -- a non-conforming `--plan` now routes through `check_latest` (ledger-derived phase) with a WARN instead of `rc=1`, still running the GOV-01 binding.
**Prior phase**: Phase 158 (feature, GAP-GOV-05; closed GH #210). The pre-158 gate-artifact binding (`gate_chain.write_gate_artifact`) authorized a write on the self-asserted env string `QOR_SKILL_ACTIVE==phase`: any process exporting it could write a schema-valid artifact. New `qor/scripts/gate_provenance.py` adds a layered, honest replacement. **Layer A** (local, per-session HMAC): a `<phase>.provenance` sidecar written beside each artifact carries a keyless `payload_sha256` and an `hmac_tag` keyed by a per-session 32-byte secret under the gitignored `.qor/session/keys/`; the wiring in `write_gate_artifact` is fail-closed. It buys tamper-evidence + cross-session replay resistance; the honest ceiling is an in-repo filesystem actor (the key is readable locally). **Layer B** (CI, merge boundary): `verify-committed --phase-min 158` recomputes each committed artifact's payload digest against its sidecar (keyless, runs on forks) and is a required CI job, so a forged committed artifact fails merge; `attest-latest` emits a CI-secret-keyed HMAC over the latest sealed entry that only trusted CI can produce (verifiable only in CI). All signed material is LF-normalized (the GAP-GOV-03 CRLF lesson). Non-forgeability against the operator is a declared non-goal (impossible by construction: the operator is both author and bound party). New `doctrine-provenance-binding.md` + 3 glossary terms. **Sprint A (GH #210) is now fully closed; only #209 (the audit umbrella) remains open.** **Recent arc (Phases 146-158, all published to PyPI through v0.110.0):** FEATURE_INDEX backfill (#146); a 6-agent production-gap red-team audit (Entry #353) -> Sprint C session_id path-safety + citation accuracy (#147), Sprint B compliance-enforce conveyance + py.typed (#148, GH #211), README currency (#149), Sprint A content_hash<->plan binding + provenance/completeness hardening (#150) + dead-hasher removal (#151) + verify() decompose (#153) + markup-required floor (#155, GAP-GOV-09) + committed-seal re-verify & content_hash CRLF-invariance (#156) + hash_file CRLF-invariant seal-text option (#157) + non-forgeable provenance (#158, GAP-GOV-05); plus the Shadow Genome producers (#152, GH #213) and Claude Fable 5 (Mythos-class) model-adaptive comms research (Entry #354, deferred). Open backlog: #209 (audit umbrella); Fable 5 feature deferred. Full per-phase history is authoritative in `docs/META_LEDGER.md` (367 entries; latest Entry #367 -- Phase 158 -- v0.110.0 -- chain `<sealed below>`); SYSTEM_STATE keeps the current-state header, physical map, and a condensed recent-phase bridge rather than restating every phase. The pre-1.0 line is current: the half-measure-closures cluster (GH #147 + #148-#165) is fully closed with real enforcers, and the two largest governance skills remain under the 40 KB skill-size budget (Phases 135/136).

## Authoritative source

All canonical Qor content lives under `qor/`. Variant outputs (`claude`, `codex`, `gemini`, `kilo-code`) are LIVE and regenerated on every seal via `qor-logic scripts dist_compile` (Step 8.5); `qor/scripts/check_variant_drift.py` gates drift in CI.

## File Tree

```
Qor-logic/
|-- qor/                                  Single source of truth (installable package)
|   |-- skills/                           30 SKILL.md across 4 categories
|   |   |-- governance/                   6: qor-audit, qor-substantiate, qor-validate,
|   |   |                                    qor-shadow-process, qor-governance-compliance,
|   |   |                                    qor-process-review-cycle
|   |   |-- sdlc/                          7: qor-research, qor-plan, qor-implement,
|   |   |                                    qor-refactor, qor-debug, qor-remediate, qor-ideate
|   |   |-- memory/                        5: qor-status, qor-document, qor-organize, + 2
|   |   `-- meta/                          12: qor-bootstrap, qor-help, qor-repo-*, + more
|   |-- scripts/                           98 .py -- lints, gate_chain, ledger_hash, dist_compile,
|   |                                        version_backends, changelog_backends, governance_index,
|   |                                        merge_velocity_check, data_api_acl_lint, ...
|   |-- reliability/                       6 .py -- intent_lock, skill_admission, gate_skill_matrix,
|   |                                        seal_entry_check, gate_chain_completeness, cycle_count
|   |-- references/                        54 .md -- 33 doctrine-*.md + glossary + audit refs
|   |-- gates/                             schema/ (18 JSON schemas) + chain.md, delegation-table.md,
|   |                                        workflow-bundles.md
|   |-- policies/                          3 Cedar policy files (skill_admission, owasp_enforcement)
|   |-- policy/                            resource_attributes (Cedar caller-side helpers)
|   |-- cli_handlers/                      compliance, release subcommand handlers
|   |-- agents/, capabilities/, compiler/, platform/, templates/, vendor/, experimental/
|   `-- dist/                              Compiled variants: claude / codex / gemini / kilo-code
|
|-- docs/                                  209 .md
|   |-- META_LEDGER.md                     Hash-chained governance ledger (329 entries)
|   |-- SYSTEM_STATE.md                    This file
|   |-- SHADOW_GENOME.md                   Audit-verdict failure records
|   |-- PROCESS_SHADOW_GENOME.md           Process-level failure log (JSONL append-only)
|   |-- GOVERNANCE_INDEX.md                Hierarchical governance-artifact index (self-policing)
|   |-- CONCEPT.md, ARCHITECTURE_PLAN.md, BACKLOG.md, SKILL_REGISTRY.md
|   |-- plan-qor-phase*.md                 171 per-phase plans
|   `-- research-brief-*.md, *-roadmap.md, archive/
|
|-- tests/                                 373 test_*.py (2323 collected)
|-- .qor/                                  Runtime state: session/current + gates/<sid>/*.json
|-- CHANGELOG.md, README.md, CLAUDE.md, ATTRIBUTION.md, CONTRIBUTING.md
`-- pyproject.toml                         Python 3.11+; version 0.103.1
```

## Ledger chain head

- Entry #335 SESSION SEAL -- Phase 139 (v0.103.1) -- chain `33e04a59aa745ae723188ead1e4be6e0d0944c5aca6e46be8d27ff8ba4c19cd2`
- Entry #333 SESSION SEAL -- Phase 138 (v0.103.0) -- chain `24cd1569d4a38c047942dbc36e3ff624ee003890d083a7f3e2e4c3790bb2b96a`
- Entry #330 SESSION SEAL -- Phase 137 (v0.102.2) -- chain `246f86ddd9aef4402fd90269462e1be7a606b84d82af214fa1cd68fceb0477df`
- 335 ledger entries total (Entry #334 GATE TRIBUNAL precedes the Phase 139 seal). Verification: `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` -> all sealable entries OK.

## Shipped tooling

- CLI (`qor-logic`, alias `qorlogic`): `install | uninstall | list | init | info | compile | verify-ledger | seed | compliance | policy | scripts | reliability | reconcile | governance-index | governance-health | substantiate-capability | release`
- 98 scripts under `qor/scripts/` + 6 reliability gates under `qor/reliability/`, dispatched via `qor-logic scripts <name>` / `qor-logic reliability <name>` (resolve from any CWD against the installed package).
- Tests: 2323 collected, green.
- Supported hosts: claude, codex, gemini, kilo-code (repo/global scope); communication tiers technical/standard/plain via `/qor-tone`.
- Release: tag-push triggers `release.yml` build-and-publish (PyPI publish gated by the `pypi` environment's human reviewers); pluggable version/changelog backends (Phase 133) handle python/node/rust archetypes.

## Advisory-gate overrides carried

None carried into this seal. Override events (when they occur) are logged as severity-1 `gate_override` entries in `docs/PROCESS_SHADOW_GENOME.md` (e.g. the `--override` escapes on `merge_velocity_check` and `feature_index_verify`, now fail-closed).

## Recent phases (108-136) -- condensed bridge

Per-phase detail is authoritative in `docs/META_LEDGER.md`; this bridges the gap between the historical sections below (which end at Phase 109) and the current head.

- **Phases 108-117**: PyPI publication hardening cluster close-out, dependency-admission tooling, module-reachability CLI dispatch, prose-behavior test-lint hardening (GH #174 -> enforced).
- **Phases 118-134 (the GH #147 half-measure-closures cluster)**: replaced advisory stopgaps with real enforcers -- META_LEDGER reconcile tool (#148), governance-index enforcement (#149/#120), citation-drift + consumer-trace (#152/#157), fail-closed merge-velocity + stabilization-capacity (#153/#154), seal-time regression gate (#155), live-progress detector (#156/#127), AC close guard (#158), per-feature TDD lint (#159/#130), external-reviewer bridge (#160), text-consistency autofix (#161), progressive-disclosure enforcement (#162/#132), pluggable release backends (#163/#133), shadow-genome graph export + roadmap (#164/#134), and the qor-compliance Option-(c) determination (#151). Cluster fully closed.
- **Phase 135 (v0.102.0)**: pre-1.0 skill-corpus consolidation -- qor-audit 52.7->40.6 KB, qor-substantiate 49.0->40.8 KB via progressive disclosure; corpus reports zero EXCEEDED.
- **Phase 136 (v0.102.1)**: qor-substantiate Step 4.5 / Step Z restructure -- extracted the misplaced embedded gate-write block; write ordered before Step 7.8, `session.rotate()` moved to a final Step 9.8.

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

## Phase 98 (v0.67.2 — 2026-05-24): Meta-skill examples → references/ (F5+F6)

Hotfix closing F5+F6 internal prompt-surface review finding. Two meta skills (`qor-meta-log-decision`, `qor-meta-track-shadow`) carried sizable `## Examples` sections (three numbered concrete invocation examples each, in fenced code blocks) that loaded into every skill invocation. Per the `SG-SkillCorpusGrowth-A` progressive-disclosure doctrine, this example prose belongs in per-skill `references/` files with a pointer in SKILL.md, not loaded inline.

**Moves**:
- `qor-meta-log-decision`: ~90 lines (Architecture L2 / Security L3 / Scope Change L2) moved from SKILL.md (lines 292-382) to `references/example-decision-entries.md`; SKILL.md retains a short pointer paragraph.
- `qor-meta-track-shadow`: ~65 lines (SG-001 Dependency Bloat / SG-002 Premature Optimization / SG-003 Hallucination) moved from SKILL.md (lines 156-219) to `references/example-shadow-genome-events.md`; SKILL.md retains a short pointer paragraph.

**Decision Point closed at plan-authoring time**: the operator-deferred question about the "stranded Entry #6 fragment" at `qor-meta-log-decision/SKILL.md:437` resolved during file inspection. The fragment is inside the `## Meta-Ledger File Structure` fenced code block (lines 386-451) as deliberate artifact-format example content, NOT stranded. The research brief misread the structure. No edit needed; the File Structure section remains intact in SKILL.md as integral artifact-format documentation.

**New test `tests/test_meta_skill_examples_progressive_disclosure.py`** (~80 LOC, 6 assertions): three per migrated skill — SKILL.md cites the references file by path, reference file exists at HEAD, reference file preserves all three example identifiers (Example 1/2/3 headings or SG-001/SG-002/SG-003 IDs). Catches the inline-examples regression: if a future edit removes the pointer or inlines the examples back into SKILL.md, the test fails.

**TDD red-green**: impl GREEN on first pass. All 6 pass twice deterministically. Full suite: 1862 passed, 1 skipped (+6 from Phase 97's 1856).

**Skill-size impact** (per Phase 95 `skill_size_budget_lint`): qor-meta-log-decision reduces from ~16.4 KB to ~13.7 KB (still well under WARN 25 KB); qor-meta-track-shadow reduces from ~12.3 KB to ~10.4 KB. Neither was at risk pre-move; this phase is hygiene, not size-budget repair. The standing Phase 95 EXCEEDED findings on qor-audit + qor-substantiate persist unchanged.

**Lessons recurring across cluster**: CHANGELOG section authored AFTER tag push misses the structural test until the next phase runs. Phase 98 retroactively backfills v0.67.1 (Phase 97's omission) plus adds v0.67.2 for itself. Phase 96 → Phase 97 had the same pattern (Phase 97 backfilled v0.67.0 missed by Phase 96). Captured as a recurring pattern; possible V2 work in a separate phase: tighten the changelog-tag-coverage test to also walk pyproject.toml and assert any declared version has a CHANGELOG section regardless of tag presence.

**V1 boundaries** (declared non_goals): rewriting example content; auto-generating examples from real entries; extending treatment to other meta skills; merging into shared examples doc.

**Dogfooding milestone**: F5+F6 is itself a progressive-disclosure finding; Phase 98 applies the discipline (move prose to references/) AND adds the structural test catching regression. The new test is the dogfooding shipping-correctness anchor.

**Cluster context**: Phase 98 closes the THIRD of five Tier-1 prompt-surface sub-plans. Cluster progress: 3 of 5 shipped. Sequence remaining: 99 (V2, GH #108 full close, feature → v0.68.0) → 100 (F4 Critical Invariants, hotfix → v0.68.1).

**Decision**: Phase 98 implemented; audit PASS on iter-1. Substantiated as v0.67.2 (hotfix → patch bump).

## Phase 99 (v0.68.0 — 2026-05-24): Runtime Contract Walk V2 — GH #108 full close

Feature closing GH #108 fully. V1 (Phase 96) shipped the recon-side five-check `reachability_probe`; V2 ships the audit-side `runtime_contract_walk` at `/qor-audit` Step 3 Infrastructure Alignment Pass. The walk runs one hop forward (callees: cited module's own imports must parse via subprocess `python -c "import X"`) and one hop backward (callers: at least one production caller must parse via `ast.parse`) for each Python module path cited in a plan being audited. Walk + probe together close the GH #108 governance-level finding across two lifecycle phases.

**WARN-only ramp**: V2 ships WARN-only despite touching a binding-VETO surface because no Phase 96 V1 operator-evidence has accumulated in this same-session cluster. CLI exits 0 by default; `--exit-on-any` opts into hard fail; the audit-site invocation uses `|| true` wrap. A future V2-of-V2 phase will gather V1 operator-evidence on false-positive rate, tune walk thresholds, remove the `|| true` wrap, and convert to hard VETO with `runtime-contract-mismatch` category. The honest framing is captured in `SG-GrepShapedRunclaim-A` doctrine (now updated from "V2 reserved" to "V2 shipped") and the new `qor/references/audit-runtime-contract-walk.md` reference file.

**Progressive disclosure honored**: full two-direction protocol + WARN-ramp rationale + examples live in `qor/references/audit-runtime-contract-walk.md`. qor-audit/SKILL.md gains only a one-paragraph summary + reference pointer + bash invocation block (~500 chars). The standing Phase 95 EXCEEDED finding on qor-audit (43.5 KB) is not materially worsened.

**Tests**: 9 + 3 = 12 new tests. `test_runtime_contract_walk.py`: forward+backward walk pass/fail per direction, graceful skip on unresolvable module, CLI exit modes (default WARN-only, --exit-on-any), positive dogfooding on Phase 99 plan's own module. `test_runtime_contract_walk_audit_wiring.py`: anchored positive on the Phase 99 wiring paragraph; WARN-only-ramp assertion (`|| true` present, not hard VETO); progressive-disclosure sweep. All pass twice deterministically. Full suite: 1875 passed, 1 skipped (+12).

**TDD red-green**: impl GREEN after one fixture-choice iteration. Initial `walk_backward` positive test used `qor.scripts.ci_coverage_lint` which has zero .py importers (it's invoked via `python -m` from .yml workflows only); changed to `qor.scripts.ledger_hash` which is imported by `qor/cli_handlers/compliance.py`. The TDD bug was instructive: the walk correctly catches "no production caller" for modules whose only callers are workflow files — this is a valid signal, just not what the test was probing.

**V1 boundaries** (declared non_goals): multi-language walk (Rust/TS/JS deferred); hard VETO at first rollout (V2-of-V2); replacing the existing grep-verify Infrastructure Alignment checks (the walk complements them); auto-rewriting plans on walk failure.

**Walk vs probe distinction**: Phase 96 V1 `reachability_probe` runs five checks per recon claim at recon Phase 3 Round 0 — operator-actioned, before plan authoring. Phase 99 V2 `runtime_contract_walk` runs two-direction import graph walk per plan-cited module at audit Step 3 — Judge-actioned, after plan, before implement. Different mechanisms for different lifecycle phases. Both close GH #108 from different angles.

**Dogfooding milestones**: GH #108 V2 closes the issue with the structural countermeasure operative on the same surface that introduced it. NINTH cross-phase exercise of Phase 89's `ci_coverage_lint`. THIRD cross-phase exercise of Phase 95's `skill_size_budget_lint`. The walk's positive dogfooding test (Phase 99 plan walks clean against own cited module) is the cluster's standard shipping-correctness anchor pattern.

**Cluster context**: Phase 99 is the FOURTH of five Tier-1 prompt-surface sub-plans. GH #108 closes here. Cluster progress: 4 of 5 shipped. Sequence remaining: 100 (F4 Critical Invariants summaries; hotfix → v0.68.1). The F4-after-V2 sequencing constraint from the meta-memo is now operative: Phase 100 will include the freshly-landed V2 walk-VETO in the qor-audit Critical Invariants summary block from authoring time, avoiding the amendment cycle the meta-memo warned about.

**Decision**: Phase 99 implemented; audit PASS on iter-1. Substantiated as v0.68.0 (feature → minor bump). GH #108 fully closed (V1 + V2 both shipped).

## Phase 100 (v0.68.1 — 2026-05-24): Critical Invariants summaries — Tier 1 cluster close (F4)

Hotfix closing F4 internal prompt-surface review finding AND closing the Tier 1 prompt-surface remediation cluster. Two binding-gate governance skills (qor-audit, qor-substantiate) gain a top-level `## Critical Invariants` summary block between `## Purpose` and `## Environment`.

**qor-audit invariants** (9 binding contracts): Step 0.3 plan-iteration ABORT; Step 3 Prompt Injection Pass ABORT; Step 3 L3 / OWASP / Ghost-UI / Razor / self-application VETOs; Step 3 Test Functionality / Filter-Stage / Infrastructure Alignment / Feature Test Declaration VETOs. Plus an explicit V2 ramp note clarifying the Phase 99 Runtime Contract Walk is NEW at Step 3 but ships WARN-only (not yet a binding VETO; V2-of-V2 will flip the ramp).

**qor-substantiate invariants** (4 binding contracts): Step 4.6.* reliability gate ladder (intent-lock, secret-scanner, procedural-fidelity, ci-coverage, dod-check, merge-velocity, skill-corpus-budget); Step 6.5 README badge currency `|| ABORT`; Step 7.8 gate-chain completeness `|| ABORT`; Constraints section at file foot.

**New test `tests/test_governance_skills_carry_critical_invariants_block.py`** (~80 LOC, 4 assertions): per-skill anchored positives (qor-audit + qor-substantiate); positional guard (block must precede Environment); forward-only sweep using binding-gate syntax patterns (`-> VETO`, `-> ABORT`, `|| ABORT`, `**VETO**`, `**ABORT**`, `binding-VETO`, `binding VETO`) so any future governance skill carrying binding gates must also carry an invariants block.

**TDD red-green**: impl GREEN after one sweep-pattern iteration. Initial sweep used unscoped `VETO`/`ABORT` keyword match which caught two unrelated governance skills with `ai_provenance.HumanOversight.VETO` enum references; tightened to binding-gate syntax patterns for accurate detection. All 4 pass twice deterministically. Full suite: 1879 passed, 1 skipped (+4).

**Cross-coupling constraint honored** (per meta-memo): Phase 100 sequenced AFTER Phase 99 V2 so the qor-audit invariants block correctly frames the Runtime Contract Walk as NEW at Step 3 but WARN-only. The amendment cycle the meta-memo warned about is avoided — future amendment (when V2-of-V2 flips the ramp) will be additive: append item 10 to the list and adjust the V2 ramp note.

**Razor compliance**: ~16 lines per skill (block + cross-reference paragraph) = ~32 LOC of skill prose total + ~80 LOC structural test. No new module; no doctrine entry (F4 is a prompt-surface clarity finding, not a process pattern).

**Cluster milestone (FINAL)**: Phase 100 closes the Tier 1 prompt-surface remediation cluster. Sequence shipped (96 → 97 → 98 → 99 → 100): GH #108 V1 (visibility) + F8 (registry per-category) + F5+F6 (meta-skill examples to references/) + GH #108 V2 (audit-side walk; GH #108 full close) + F4 (Critical Invariants). Cluster totals: **5 phases**, **5 PRs** (#113/#114/#115/#116/#117), **5 releases** (v0.67.0 / v0.67.1 / v0.67.2 / v0.68.0 / v0.68.1), **+47 tests** (18+7+6+12+4 = 47 new tests; full suite 1879 passed at cluster close), **15 new ledger entries** (#257-#271), **1 GH issue closed** (#108), **4 internal F-findings closed** (F4 + F5+F6 + F8 — Entry #6 fragment Decision Point resolved honestly during Phase 98 plan-authoring rather than requiring an edit).

**Lessons captured across cluster**:
1. Post-substantiate currency tests (README badges, SYSTEM_STATE, CHANGELOG) must re-run AFTER ledger append, not just after implementation. Caught omissions one phase late in Phases 96/97/98; discipline applied successfully Phases 99 onward.
2. CHANGELOG sections must be added in the same commit as the pyproject.toml version bump, not deferred. The `test_every_tag_has_changelog_section` only catches the omission AFTER tag push (one phase later). Possible V2 candidate for a future hygiene phase: tighten the test to walk pyproject.toml as well.
3. Structural sweep tests need binding-gate syntax patterns, not raw keyword matches, to avoid false positives on enum references.
4. The cluster's V1/V2 split pattern (visibility-first, evidence-second, enforce-third) shipped 13 consecutive phases (88-100); the pattern is now confirmed across the post-cluster session and Tier 1 prompt-surface cluster. V2 audit-side enforcement (Phase 99) honest about WARN-only ramp pending V1 operator evidence.

**V2-of-V2 reserved for future phase OUTSIDE this cluster**: gather Phase 96 V1 (`reachability_probe`) operator-evidence on false-positive rate, tune Phase 99 V2 (`runtime_contract_walk`) thresholds, remove the `|| true` wrap at qor-audit Step 3, and convert the walk to a hard VETO with `runtime-contract-mismatch` category. When that lands, the qor-audit Critical Invariants block will need item 10 appended and the V2 ramp note updated.

**Decision**: Phase 100 implemented; audit PASS on iter-1. Substantiated as v0.68.1 (hotfix → patch bump). **Tier 1 prompt-surface cluster CLOSED.**

## Phase 101 (v0.69.0 — 2026-05-24): PyPI Publication Hardening P0 (GH #118 partial)

Feature opening the supply-chain hardening cluster (3 sub-plans: 101 → 102 → 103 closing GH #118). P0 ships workflow-side controls; P1 (102) adds dependency + evidence layer; P2 (103) adds post-publish verification + cooling-period doctrine. Three independent ancestry legs of supply-chain integrity articulated in research brief `docs/research-brief-gh118-pypi-hardening-2026-05-24.md`: commit-ancestry (existing tag-reachable guard preserved and replicated), artifact-ancestry (NEW: SHA256SUMS handoff between split jobs), workflow-ancestry (NEW: full SHA pins; environment-with-policy).

**Closes 5 of 13 GH #118 acceptance items** (F-1a pypi env protection rules, F-1b id-token job-scope, F-1c split build/publish + artifact handoff, F-2a SHA pin Actions, F-2c no cache on publish job).

**Workflow split**: `.github/workflows/release.yml` rewritten from single `build-and-publish` job into two jobs. `build` runs unprivileged (`contents: read`, `cache: pip` allowed), generates `dist/SHA256SUMS`, uploads `release-dist` artifact (retention 7 days). `publish` runs privileged (`id-token: write`, `environment: pypi`, `needs: build`, no setup-python, no cache), downloads artifact, runs `sha256sum -c SHA256SUMS` for integrity verification, then invokes `pypa/gh-action-pypi-publish`. Tag-ancestry guard (`git merge-base --is-ancestor origin/main`) runs in BOTH jobs — load-bearing-gate replication per qor-substantiate Constraints; defense-in-depth against the SG-StructureWithoutPolicy-A pattern documented in the research brief (the env existed since 2026-04-16 with empty `protection_rules` — structure without policy).

**SHA pinning across all three workflows**: actions/checkout `@34e114876b0b11c390a56381ad16ebd13914f8d5  # v4.3.1`; actions/setup-python `@a26af69be951a213d495a4c3e4e4022e16d87065  # v5.6.0`; actions/upload-artifact `@ea165f8d65b6e75b540449e92b4886f43607fa02  # v4.6.2`; actions/download-artifact `@d3f86a106a0bac45b974a628896c90dbdf5c8093  # v4.3.0`; pypa/gh-action-pypi-publish `@cef221092ed1bacb1cc03d23a2d87d1d172e277b  # v1.14.0`. SHAs resolved live via `gh api repos/<owner>/<repo>/git/ref/tags/<tag>`. Worst prior pin was a mutable branch ref (`pypa/gh-action-pypi-publish@release/v1`). Action majors preserved (v4/v5/v1); major bumps deferred.

**Live environment configuration**: new `qor/scripts/configure_pypi_environment.py` (idempotent gh-api wrapper exposing `build_put_body()` pure factory + `build_branch_policy_body()` for unit testing). Invoked once during the cycle: `python -m qor.scripts.configure_pypi_environment --repo MythologIQ-Labs-LLC/Qor-logic --reviewer-id 205245245 --reviewer-type User`. Post-state verified via `gh api repos/.../environments/pypi`: `protection_rule_count` 0 → 2 (required_reviewers + branch_policy), `reviewer_logins == ["Knapp-Kevin"]`, `prevent_self_review == true`, `deployment_branch_policy.custom_branch_policies == true`, single `v*.*.*` tag policy attached. The `pypi` environment now ENFORCES; the structure-without-policy gap is closed at the surface where the policy attaches.

**Test surface**: 16 new tests across `tests/test_release_workflow_immutability.py` (8 structural assertions on the workflow YAML — SHA-pinning across all three files, build/publish split, id-token scoping, cache-isolation asymmetry, artifact-handoff with SHA verification) and `tests/test_configure_pypi_environment.py` (7 unit tests on the PUT-body factory: reviewer requirement, tag-only policy, idempotency, input validation). One amended test in `tests/test_release_workflow_guard.py` (`test_tag_ancestry_guard_present_in_both_jobs`) locks in the load-bearing-gate replication. All 16 pass twice deterministically per CLAUDE.md test discipline. Full suite: 1895 passed, 1 skipped, 4 deselected.

**TDD red-green**: tests written first (collection error red — `qor.scripts.configure_pypi_environment` module didn't exist), then script + workflow rewrite landed, re-run green first attempt. Two post-impl fixes were doctrine-driven rather than logic-driven: (1) `**change_class**: minor` → `**change_class**: feature` per the doctrine enum (`hotfix|feature|breaking`, not SemVer terms); (2) META_LEDGER entries 273-275 initially computed with legacy chain-hash format, corrected to Phase 23+ pipe-separated format after `seal_entry_check` caught the divergence (verify accepts both; seal_entry_check strict on new format only).

**L3 high_risk_target audit**: plan declared `high_risk_target: true` with impact_assessment block enumerating three named failure modes paired with mitigations and SSDF practices (PO.4.1, PO.5.1, PS.2.1, PS.3.1). Audit iter-1 PASS across all 9 binding passes (Prompt Injection, L3 contracts, OWASP Top-10, Ghost-UI/Razor/self-application, Test Functionality, Filter-Stage, Infrastructure Alignment, Runtime Contract Walk V2 WARN-only, Feature Test Declaration). Non-blocking observations: workflow integration tests would need `act`/runner harness (out of scope); admin-bypass disable not API-exposed (UI follow-up); single-reviewer initial protection level (broaden as team grows).

**Cluster context**: Phase 101 opens the 3-phase supply-chain hardening cluster — 1 of 3 sub-plans. Sequence remaining: 102 (P1: hash-pinned requirements-release.txt, CODEOWNERS, SBOM + GH release evidence bundle, dependency-review workflow — closes 4 more acceptance items) → 103 (P2: post-publish PyPI pull-back + cooling-period doctrine — closes final 2 items). After Phase 103 seal, GH #118 fully closed.

**Carry-forward**: admin-bypass UI disable (Knapp-Kevin to set once via repo settings); Dependabot config for `github-actions` ecosystem (P1 follow-up to manage SHA-pin updates); CODEOWNERS for the new workflow + script surface (P1 scope).

**Decision**: Phase 101 implemented; audit PASS on iter-1 (L3 high_risk_target). Substantiated as v0.69.0 (feature → minor bump). First of three phases in the supply-chain hardening cluster.

## Phase 102 (v0.70.0 — 2026-05-24): PyPI Publication Hardening P1 (GH #118 partial)

Feature continuing the supply-chain hardening cluster (101 → 102 → 103 closing GH #118). P1 ships the dependency + evidence layer on top of P0's workflow split.

**Closes 4 more GH #118 acceptance items** (F-2b CODEOWNERS, F-3a dependency-review workflow, F-3b hash-pinned build lockfile, F-4a/F-4c SBOM + evidence bundle). Cluster total: 9 of 13 acceptance items closed across Phases 101+102.

**Hash-pinned build lockfile**: `requirements-release.in` + `requirements-release.txt` (pip-compile 7.5.3 generated; SHA-256 hashes for `build==1.5.0` + 3 transitives `colorama==0.4.6`, `packaging==26.2`, `pyproject-hooks==1.2.0`). Release workflow's build job now runs `pip install --require-hashes -r requirements-release.txt` (replaces bare `pip install build`). Lockfile is under CODEOWNERS protection.

**CODEOWNERS**: `.github/CODEOWNERS` attaches `@Knapp-Kevin` as required reviewer to `/.github/workflows/`, `/.github/CODEOWNERS`, `/pyproject.toml`, `/requirements-release.{in,txt}`, `/qor/reliability/intent_lock.py`, `/qor/scripts/configure_pypi_environment.py`. Single-owner initial; broaden when maintainer team provisioned.

**PR dependency-review workflow**: `.github/workflows/pr-dependency-review.yml` triggers on PRs touching `pyproject.toml`, `requirements-release.txt`, or `.github/workflows/**`. Runs `actions/dependency-review-action@2031cfc080254a8a887f58cffee85186f0e49e48  # v4.9.0` (SHA-pinned). Fails on `high` severity; comments summary on failure. License-allowlist deferred to a future hygiene phase.

**SBOM + evidence bundle**: Build job adds two new steps: (1) `pip install cyclonedx-bom` (unpinned -- deferred as documented non_goal: SBOM tool is metadata-only, not the released artifact; its transitive set with ~120 lxml wheel hashes would exceed the Razor file budget), (2) `cyclonedx-py environment --of JSON --output-file dist/sbom.json` -- captures build-environment dependency tree. Publish job adds (a) evidence-bundle assembly step producing `dist/evidence.json` with `git_sha`, `tag`, `workflow_run_id`, `workflow_sha`, `lockfile_sha256`, `artifact_sha256sums`, `action_pins` (5 SHAs); (b) post-publish `gh release create` attaching `dist/*.whl`, `dist/*.tar.gz`, `sbom.json`, `evidence.json`, `SHA256SUMS`. Publish job's `permissions.contents` widened `read -> write` for the release-attachment responsibility; `id-token: write` remains scoped to publish job only.

**Test surface**: 17 new tests across 3 new files plus 1 amended file. `tests/test_requirements_release_lockfile.py` (5 tests: presence, SHA-256 hash format, build pin block, transitive coverage, `--require-hashes` consumption). `tests/test_pr_dependency_review_workflow.py` (4 tests: presence, SHA-pinned action with annotation, paths-trigger coverage, fail-on-severity=high). `tests/test_codeowners.py` (5 tests: presence, workflow dir, pyproject + lockfile, intent_lock + env-config, every-rule-has-owner). `tests/test_release_workflow_immutability.py` amended (+3 tests: SBOM step in build, evidence-bundle assembly in publish, gh release create attaches required artifacts). All 17 pass twice deterministically. Full suite: 1910 passed, 1 skipped, 4 deselected.

**Mid-audit amendment**: cyclonedx-bom transitive set (~120 lxml wheel hashes) exceeded Section 4 Razor file budget when initially generated as `requirements-sbom.txt`. Plan amended in-cycle to drop the SBOM-tool lockfile with explicit non_goal rationale (SBOM is metadata about the artifact, not the artifact itself; lower-risk; the producer `build` IS hash-pinned). Post-amendment lints exit 0; audit remains iter-1 PASS.

**Razor compliance**: `release.yml` grew ~73 → ~115 lines (still <250); `pr-dependency-review.yml` ~28 lines; `CODEOWNERS` 11 lines; new test files 70-95 lines each; amended `test_release_workflow_immutability.py` ~200 lines. All within budget.

**L3 high_risk_target audit**: plan declared `high_risk_target: true` with impact_assessment block enumerating 4 named failure modes paired with mitigations (transitive-dep drift, vulnerable-dep via PR, no provenance record, unreviewed workflow/manifest/lockfile changes). SSDF practices PO.4.1, PS.2.1, PS.3.1, PS.3.2, PW.4.1, PW.4.4, RV.1.1 declared. Audit iter-1 PASS across all 9 binding passes.

**Cluster context**: Phase 102 is the SECOND of three sub-plans in the supply-chain hardening cluster — 2 of 3 shipped. Sequence remaining: 103 (P2: post-publish PyPI pull-back + cooling-period doctrine — closes final 2 explicit acceptance items F-4b + F-3c). After Phase 103 seal, GH #118 fully closed.

**Carry-forward**: F-4b post-publish PyPI pull-back + hash compare (Phase 103); F-3c `qor/references/doctrine-dependency-admission.md` cooling-period policy (Phase 103); admin-bypass UI disable (still not API-exposed); Dependabot config for `github-actions` ecosystem; broaden CODEOWNERS reviewer once a maintainer team exists; cyclonedx-bom hash-pinning (deferred non_goal).

**Decision**: Phase 102 implemented; audit PASS on iter-1 (L3 high_risk_target). Substantiated as v0.70.0 (feature → minor bump). Second of three phases in the supply-chain hardening cluster.

## Phase 103 (v0.71.0 — 2026-05-24): PyPI Publication Hardening P2 — Cluster Close (GH #118 FULL CLOSE)

Feature closing the supply-chain hardening cluster. Final 2 GH #118 acceptance items shipped; **issue #118 fully closed across the 3-phase cluster**.

**Closes F-4b** (post-publish PyPI pull-back verification) and **F-3c** (dependency-admission doctrine).

**Post-publish PyPI pull-back**: release workflow's publish job adds a new step between `pypa/gh-action-pypi-publish` and `Attach evidence bundle to GitHub release`. Extracts `VERSION` from `${GITHUB_REF_NAME#v}`, runs `pip download --no-deps --dest=/tmp/pypi-verify --no-cache-dir qor-logic==${VERSION}` with bounded retries (6 attempts at 10s intervals = 60s total budget; loud, recoverable failure on max-retry exhaustion). Computes SHA-256 of the downloaded wheel + sdist and `diff -u`-compares against the build-produced `dist/SHA256SUMS` (filtered to `.whl|.tar.gz` lines). Mismatch fails the workflow non-zero, preventing `gh release create` from attaching a false bundle. Closes the "published artifact differs from built artifact" attack class (rare but high-signal: PyPI-side error, mid-publish replacement, CDN cache poisoning, workflow bug).

**Dependency-admission doctrine** (`qor/references/doctrine-dependency-admission.md`, ~85 lines): declares a 14-day cooling-period minimum age threshold for new transitive dependencies entering the release tree (`requirements-release.txt` or direct deps in `pyproject.toml`). Check mechanic uses the PyPI Warehouse API (`https://pypi.org/pypi/<pkg>/<version>/json`, `upload_time_iso_8601` field); currently manual, automated lint deferred as documented non_goal. Emergency-override procedure has three components: (1) META_LEDGER entry with `**Dependency admission override**:` line naming the within-window version and justification (CVE id, incident reference); (2) `dep-admit-override` PR label ratified by CODEOWNERS approval; (3) 30-day follow-up re-evaluation logged in the next phase's IMPLEMENTATION entry. Coordinates with the Phase 102 `pr-dependency-review.yml` workflow orthogonally (severity-graded vulnerability catch + freshness-vector catch fire independently). SSDF practices PS.2.1, PW.4.4, RV.1.1.

**Test surface**: 7 new tests across 1 new file + 1 amendment. `tests/test_doctrine_dependency_admission.py` (5 tests: presence, 14-day threshold, override procedure components, coordination with dep-review workflow, SSDF mapping). `tests/test_release_workflow_immutability.py` amended (+2 tests: pull-back step position between publish and gh-release-create, bounded retry semantics with for-loop + sleep + exit). All 7 pass twice deterministically. Full suite: 1919 collected.

**Razor compliance**: pull-back step ~25 bash lines (within 40-line block budget); release.yml ~140 lines now (was 115; still <250); doctrine ~85 lines (well under 250); test files within budget.

**L3 high_risk_target audit**: plan declared `high_risk_target: true` with impact_assessment block (2 named failure modes: published-artifact-differs-from-built; freshness-vector supply-chain attack). SSDF PS.2.1, PS.3.1, PW.4.4, RV.1.1. Audit iter-1 PASS across all 9 binding passes.

**Cluster close summary** (FINAL): three-phase supply-chain hardening cluster complete. Sequence shipped (101 → 102 → 103): P0 (5 items: workflow split, SHA pins on all third-party Actions, pypi environment protection rules, id-token scoping, no-cache publish) → P1 (4 items: hash-pinned build lockfile, CODEOWNERS, SBOM + evidence bundle, dependency-review workflow) → P2 (2 items: post-publish PyPI pull-back, cooling-period doctrine). **Cluster totals**: 3 phases, 3 PRs (to be opened by operator post-cycle), 3 releases (v0.69.0 / v0.70.0 / v0.71.0), +40 new tests across 6 new test files + 2 amendments, 10 new ledger entries (#272 research + #273-#281 cluster), 1 GH issue fully closed (#118), 6 SHA-pinned third-party Actions in active use, 1 new doctrine, 1 live environment configuration (pypi GitHub environment now ENFORCES), 1 hash-pinned lockfile, 1 new CODEOWNERS file, 1 new dependency-review workflow.

**Three-leg defense-in-depth complete**: commit-ancestry (Phase 40 tag-reachable guard + Phase 101 replication to both jobs) + artifact-ancestry (Phase 101 SHA256SUMS handoff + Phase 102 hash-pinned lockfile + Phase 103 PyPI pull-back) + workflow-ancestry (Phase 101 SHA pins on all actions + Phase 102 CODEOWNERS + dependency-review-action + SBOM + evidence bundle). The SG-StructureWithoutPolicy-A pattern documented in the research brief is now operative-with-policy across all three legs. Phase 103's cooling-period doctrine catches the freshness-vector attack class orthogonally (severity vs. age).

**Carry-forward (post-cluster non-blockers)**: admin-bypass UI disable (not API-exposed; one-time manual setting); Dependabot config for `github-actions` ecosystem (separate hygiene phase to manage the 6 SHA pins now in place); cyclonedx-bom hash-pinning (deferred as non_goal in Phase 102 — would require ~120 lxml wheel hashes); automated dependency-admission lint (deferred as non_goal in Phase 103); broaden CODEOWNERS reviewer pool when a maintainer team exists; periodic re-evaluation of dep-admit-override targets per the new doctrine.

**Decision**: Phase 103 implemented; audit PASS on iter-1 (L3 high_risk_target). Substantiated as v0.71.0 (feature → minor bump). **Tier 1 supply-chain hardening cluster CLOSED. GH #118 fully closed.**

## Phase 104 (v0.72.0 — 2026-05-25): Release publish-step fix + Dependabot carry-forward (cluster recovery)

Hotfix recovering the cluster's failed first-attempt publish. The Phase 101 build job placed `SHA256SUMS` into `dist/`; Phase 102 added `sbom.json` and `evidence.json` into `dist/`. `pypa/gh-action-pypi-publish` uploads every file in its `packages-dir` (default `dist/`), so the three pushed tags (v0.69.0/v0.70.0/v0.71.0) all failed at the publish step with `InvalidDistribution: Unknown distribution format: 'SHA256SUMS'`. Nothing reached PyPI. Phase 104 fixes the bug and ships the cumulative cluster work as v0.72.0.

**Fix**: insert a `Prepare publish-only directory` step in the publish job that creates a sibling `dist-publish/` directory and copies only `*.whl` and `*.tar.gz` from `dist/`. Point `pypa/gh-action-pypi-publish` at `dist-publish/` via `with.packages-dir: dist-publish/`. Downstream evidence-assembly + pull-back + `gh release create` steps continue to operate on `dist/` (which still contains the auxiliary files). The separation imposes the missing policy: `dist/` is the assembly directory, `dist-publish/` is the delivery directory. Files added to `dist/` by future phases never leak into the publish payload.

**Dependabot carry-forward**: `.github/dependabot.yml` (v2) authored as standalone hygiene PR #122 but closed because the PR-citation-lint requires a plan file path + Merkle seal, neither of which a standalone hygiene PR carried. Folded into this hotfix to attach it to Phase 104's plan + seal. Manages `github-actions` ecosystem (weekly Monday checks; preserves the `# vX.Y.Z` annotation comments added in Phase 101; grouped minor+patch updates) and `pip` ecosystem (weekly Monday checks for the hash-pinned `requirements-release.txt` lockfile).

**Operator decisions logged (pre-Phase-104)**:
- `can_admins_bypass: false` set on pypi env via `gh api PUT` (closes Phase 101 carry-forward F-1a UI follow-up; GitHub API has since added the field).
- `prevent_self_review: false` set on pypi env to resolve the single-maintainer deadlock. Required-reviewer rule + tag-only policy + admin-bypass-disabled remain operative.

**Version bump rationale**: hotfix change_class normally implies a patch bump (0.71.0 → 0.71.1), but the v0.69.0/v0.70.0/v0.71.0 tags exist as historical artifacts with failed publish workflows. To avoid claimed-but-unpublished version confusion on PyPI, this hotfix takes the next available minor (0.72.0) and ships the cumulative cluster work in one published release. CHANGELOG `[0.72.0]` documents the v0.69-v0.71 publish-step bug + the Phase 104 fix.

**Test surface**: 5 new tests. `test_release_workflow_publish_uses_separate_packages_dir` + `test_release_workflow_publish_only_dir_excludes_non_dist_files` (amended onto Phase 101's structural assertions). `test_dependabot_config_file_exists` + `test_dependabot_config_covers_actions_and_pip_ecosystems` + `test_dependabot_config_uses_supported_schedule_intervals` (new file). All 5 pass twice deterministically.

**SG-StructureWithoutPolicy-A third instance**: the bug was the third observed instance of the structure-without-policy pattern (Phase 52 gate-chain bypass + Phase 101 pypi env protection-rules-empty + Phase 104 dist directory unfiltered). The pattern is hereby a candidate for formal SG promotion in the next Shadow Genome doctrine update.

**Cluster aftermath**: Phase 101-103 cluster delivered all 13 GH #118 acceptance items but had this publish-step bug. Phase 104 is the structural fix. After v0.72.0 publishes successfully:
- PyPI: 0.68.1 → 0.72.0 (v0.69-v0.71 skipped on PyPI; tags remain on remote)
- GH #118: already closed
- Dependabot: will start producing PRs for the 6 SHA-pinned Actions + the hash-pinned lockfile

**Carry-forward (post-cluster, post-Phase-104)**: broaden CODEOWNERS reviewer pool once a maintainer team is provisioned; cyclonedx-bom hash-pinning (deferred non_goal in Phase 102); automated dependency-admission lint (deferred non_goal in Phase 103); periodic re-evaluation of dep-admit-override targets per the Phase 103 doctrine; consider deleting the v0.69.0/v0.70.0/v0.71.0 remote tags if their presence becomes confusing for downstream consumers.

**Decision**: Phase 104 implemented; audit PASS on iter-1 (L3 high_risk_target). Substantiated as v0.72.0 (hotfix → minor bump for cluster-publish recovery). **Cluster fully recovered.**

## Phase 105 (v0.73.0 — 2026-05-25): Dependency-admission tooling (GH #118 cluster carry-forward)

Feature consuming the Phase 103 `doctrine-dependency-admission.md` carry-forward. Ships the operator-and-CI-invokable tools the doctrine declared but did not yet implement: a cooling-period lint and a 30-day re-evaluation tracker. WARN-only CI ramp per Phase 99 V2 pattern (visibility-first, evidence-second, enforce-third).

**Shared parsing helpers** (`qor/scripts/_dep_admit_common.py`, ~110 lines): pure functions over committed artifacts. `parse_lockfile_entries(text)` handles pip-compile --generate-hashes format with multiline `--hash=sha256:...` continuations; `diff_lockfile_against_base(current, base)` returns new + version-bumped entries (removals not reported); `parse_override_entries(ledger_text)` walks META_LEDGER for `**Dependency admission override**:` lines paired with their containing entry's `**Timestamp**`. Three frozen dataclasses (`LockfileEntry`, `Bump`, `OverrideEntry`) and a named `LockfileParseError` for malformed input.

**Dependency-admission lint** (`qor/scripts/dependency_admission_lint.py`, ~155 lines): operator- and CI-invokable. Diffs `requirements-release.txt` against a base ref (default `merge-base origin/main HEAD`); queries `https://pypi.org/pypi/<pkg>/<version>/json` via stdlib `urllib.request` (bounded retry 3 × 5s = 15s budget per package); reports admissions younger than the 14-day cooling-period threshold absent matching ledger override. Three-way exit semantics (0 clean / 1 violations / 2 network failure) distinct so CI workflows can route on cause. Markdown summary table to stdout + per-violation stderr line.

**Override tracker** (`qor/scripts/dep_admit_override_tracker.py`, ~115 lines): operator-invokable only. Scans META_LEDGER for override entries and emits a markdown (or CSV) table showing which entries are due for 30-day re-evaluation per the Phase 103 doctrine. Always exit 0 (informational). Flags: `--filter due|pending|all`, `--since YYYY-MM-DD`, `--follow-up-days N`, `--format markdown|csv`.

**CI wiring** (`.github/workflows/pr-dependency-review.yml`): the lint runs as a new step after the existing `actions/dependency-review-action` step. Trigger paths unchanged from Phase 102 (`pyproject.toml`, `requirements-release.txt`, `.github/workflows/**`). Wrapped with `|| true` for WARN-only V1 rollout — a future V2 phase will flip the wrap to hard fail after operator-evidence on false-positive rate accumulates. The setup-python step uses `cache: pip` (PR-time workflow is unprivileged; cache appropriate per Phase 101 build-vs-publish asymmetry).

**Doctrine update** (`qor/references/doctrine-dependency-admission.md`): additive note under `### Check mechanic` points operators at the Phase 105 tooling and documents the WARN-only ramp posture.

**Phase 89 forward-maintenance**: appended the new `python -m qor.scripts.dependency_admission_lint --base <ref>` workflow command to Phase 89's `## CI Commands` list. Phase 89's `test_lint_self_applies_to_phase_89_plan` requires Phase 89's plan to enumerate every operator-runnable Python invocation across all workflows; the maintenance comment in the bullet explains the forward-edit pattern for future readers.

**Test surface**: 12 new behavioral tests across 3 new files. Network calls in lint tests mocked via `monkeypatch.setattr(lint.urllib.request, "urlopen", ...)`; no live PyPI hits. Each test invokes the unit and asserts on output -- exit codes 0/1/2, stdout content (markdown column headers), stderr content (violation lines), filter behavior, age-computation correctness. All pass twice deterministically. Full regression: 1937 collected.

**TDD red-green discipline**: 3 test files authored FIRST; pytest collection produced `ImportError: cannot import name '_dep_admit_common'` (red). Three implementation files written; 12/12 green first attempt. Determinism confirmed by re-running (12/12 green, 1.51s).

**Pre-substantiate full regression** uncovered 4 failures all resolved inline before seal: (1) `test_lint_self_applies_to_phase_89_plan` -- new lint command not in Phase 89 plan; fixed by appending the command with forward-maintenance comment. (2) `test_setup_python_uses_cache` -- new setup-python step missing `cache: pip`; fixed. (3) + (4) README badge currency -- routine substantiate-time bumps (Tests 1925 → 1937, Ledger 284 → 287). At seal: 1937 passed, 2 skipped, 4 deselected. The substantiate also surfaced 14 pre-existing glossary `referenced_by` drift findings (terms `gate_skipped_prerequisite_absent` + `SG-HalfSealedClaim-A` introduced in Phase 75 but never wired into the 7 skill files that consume them) + 1 false-positive cross-doc conflict on term `Gate` (regex `\bGate\s+(?:is|means|refers to)\s+...` tripped by "a compile gate is offline" in DoD doctrine prose); both fixed in this phase as `referenced_by` backfills + one prose reword, documented in CHANGELOG.

**Razor compliance**: all functions <40 lines (`_fetch_pypi_upload_time` ~17, `parse_lockfile_entries` ~30, `main` ~30 per script). File line counts: shared helper ~110, lint ~155, tracker ~115, test files 95-130. All under 250-line budget. Max nesting depth: 2 (retry loop). No nested ternaries.

**Self-application discipline (Phase 68 sub-pass)**: plan declares `originating_remediation: Phase 103 doctrine-dependency-admission.md cluster carry-forward`. The discipline introduced is the 14-day cooling-period check on transitive dependency admissions. The implementation adds **zero** third-party dependencies (stdlib only: `urllib.request`, `json`, `argparse`, `dataclasses`, `datetime`, `re`, `csv`, `io`, `pathlib`, `time`, `subprocess`). Vacuously satisfied: there are no transitive admissions to gate.

**Carry-forward to V2** (documented in audit non-blocking observations and the Phase 105 plan non_goals): flip the WARN-only ramp to hard fail after operator-evidence accumulates; PR-label override detection (`dep-admit-override` label via `gh pr view --json labels`); cyclonedx-bom hash-pinning (separate carry-forward; Razor file-budget concern unchanged); broaden the cooling-period to direct deps in `pyproject.toml`; calendar integration for the tracker; auto-create GitHub issues for due-for-review overrides.

**Decision**: Phase 105 implemented; audit PASS on iter-1 (L2; tooling supports L3 doctrine but is itself non-security-critical). Substantiated as v0.73.0 (feature → minor bump). Phase 103 dependency-admission doctrine now has operational tooling on both legs (PR-time cooling-period check + 30-day follow-up tracker).

## Phase 106 (v0.74.0 — 2026-05-26): Dependency-admission lint V1.1 extensions

Feature shipping three V1.1 extensions on top of Phase 105's V1 dependency-admission lint surface. Closes 3 of 5 Phase 105 V2 carry-forward items in a cohesive cycle. The remaining 2 items (WARN→hard-fail flip on the cooling-period lint, broaden CODEOWNERS reviewer pool) have legitimate blockers — operator-evidence accumulation and maintainer-team provisioning, respectively — and remain explicit carry-forward.

**PR-label override** (D-106.1): the lint now accepts the GitHub PR label `dep-admit-override` as a supplementary override signal alongside the existing META_LEDGER `**Dependency admission override**:` entry. CI context is detected via the standard GitHub Actions env vars (`GITHUB_EVENT_NAME == "pull_request"` + `GITHUB_REPOSITORY` + `GITHUB_REF` regex-parsed for the PR number `refs/pull/<n>/merge`). The lint shells out to `gh pr view <n> --repo <owner>/<name> --json labels` (gh is pre-installed on GitHub Actions runners; default GITHUB_TOKEN has label read access). Fails open: any subprocess/JSON/I/O error emits a stderr fallback note `"WARN: PR label query failed; falling back to META_LEDGER-only override check"` and returns `None` (caller treats as no-label-override-available). The fails-open semantics are deliberate — a failed network query must not introduce a spurious within-window violation when the operator has done the right thing via ledger entry. New `--skip-pr-labels` flag bypasses the gh query for local testing.

**pyproject.toml exact-pin coverage** (D-106.2): new `parse_pyproject_exact_pins(text) -> list[LockfileEntry]` pure function in `qor/scripts/_dep_admit_common.py`. Uses Python 3.11+ stdlib `tomllib` (no new third-party dependency) to extract entries matching `^([a-zA-Z0-9][a-zA-Z0-9._-]*)\s*==\s*([0-9][^\s;,]*)\s*$` from `[project] dependencies` and `[project.optional-dependencies]`. Range pins (`>=4`, `~=2.1`, `<5`) and unbounded specifiers (`requests`) are skipped because the resolved version is not knowable until install time. The lint's `run_lint()` signature gains `current_pyproject_text` + `base_pyproject_text` parameters; pyproject bumps union with lockfile bumps before the PyPI query loop. qor-logic's own pyproject today carries only range-pinned deps (`jsonschema>=4`, `PyYAML>=6`), so V1.1 lint output against current state is the empty set; the check becomes operative when a maintainer commits to an explicit `==` pin.

**Session ID convention lint** (D-106.3): new `qor/scripts/session_id_lint.py` (~46 lines). Pure `lint(marker_path) -> (conforming, msg)` helper; argparse `main()` always exits 0. Emits stderr WARN when `.qor/session/current` doesn't match `qor.scripts.session.SESSION_ID_PATTERN` (canonical 6-hex slug format `\d{4}-\d{2}-\d{2}T\d{4}-[0-9a-f]{6}$`). The WARN names the canonical format and points operators at `session.rotate()` for compliant generation. Wired into `/qor-substantiate` Step 4.6 between `gate_skill_matrix` and `secret_scanner` with `|| true` belt-and-suspenders (the script already exits 0 unconditionally; the wrap documents intent for future readers). Catches the fall-through-to-default pattern observed in Phase 105 substantiate where the operator-supplied session ID (`2026-05-25T0400-phase105-deps`) didn't match the regex; `qor.scripts.session.current()` returned `None`; downstream tooling fell through to the string `"default"`, fragmenting event provenance across phases. Phase 106's own session (`2026-05-25T2035-c8f105`) is the first to comply with the new convention.

**Doctrine notes**: `qor/references/doctrine-dependency-admission.md` gains a `### Check mechanic` paragraph documenting the PR-label and pyproject extensions + their fails-open / exact-pin-only semantics. `qor/references/doctrine-governance-enforcement.md` gains a new §7.1 "Session ID convention" subsection documenting the canonical regex + the `session_id_lint` WARN surface.

**Glossary**: 3 new term entries (`PR-label override`, `pyproject exact-pin admission`, `session ID convention lint`), all homed in their respective doctrines and `referenced_by` populated.

**Phase 89 forward-maintenance**: Phase 89's `test_lint_self_applies_to_phase_89_plan` requires its plan to enumerate every operator-runnable Python invocation across all workflows + skills. The new `python -m qor.scripts.session_id_lint` was appended to Phase 89's CI Commands list with a forward-maintenance comment.

**Test surface**: 8 new behavioral tests across 3 test files (one NEW + two amended), plus 1 bonus marker-missing test (9 new total). All invoke the unit and assert on output — exit codes, override status, stderr content, dataclass fields. Network and gh CLI calls mocked via `monkeypatch`; no live network in tests. All pass twice deterministically (18/18 across the three dependency-admission test files, including pre-existing Phase 105 tests). Critical-gate suite run: 117/119 PASS (only 2 expected README badge currency failures during impl-time which clear at substantiate-time bumps). Full regression at seal: 1946 collected.

**TDD red-green**: test files authored FIRST. `tests/test_session_id_lint.py` collection red (`ImportError: cannot import name 'session_id_lint' from 'qor.scripts'`); pyproject tests runtime red (`AttributeError: parse_pyproject_exact_pins` not in `_dep_admit_common`). All 18 green first attempt after implementation files landed. Determinism verified by re-running (2.93s + 2.55s).

**Razor compliance**: all functions <40 lines (`_query_pr_labels` 24, `parse_pyproject_exact_pins` 24, `session_id_lint.lint` 13, `session_id_lint.main` 9). File totals: `_dep_admit_common.py` 167 lines (was ~110); `dependency_admission_lint.py` 213 lines (was ~155); `session_id_lint.py` 46 lines (NEW). All well within 250-line budget. Max nesting depth: 2 (existing retry loop in `_fetch_pypi_upload_time`). No nested ternaries.

**Self-application discipline (Phase 68 sub-pass)**: plan declares `originating_remediation: Phase 105 V2 carry-forward`. Discipline extended is the cooling-period admission check. Implementation adds zero new third-party dependencies — stdlib only (`tomllib`, `subprocess`, `urllib.request`, `os`, `re`, `json`, `argparse`, `dataclasses`, `pathlib`, `sys`). gh CLI is a shell tool, not a Python dependency. Vacuously satisfied — there are no transitive admissions to gate. Phase 105's vacuous-satisfaction argument carries forward.

**SG-StructureWithoutPolicy-A follow-through (now complete across the dependency-admission surface)**: Phase 103 declared the cooling-period structure (META_LEDGER override + PR label + 30-day re-eval). Phase 105 shipped the META_LEDGER signal + the 30-day tracker. Phase 106 closes the PR label signal — all three components of the documented override procedure now have operational enforcement / detection. The countermeasure is complete across the structure → declaration → enforcement chain at this surface.

**Carry-forward (unchanged from Phase 105 carry-forward, minus the 3 items shipped here)**: WARN→hard-fail flip on cooling-period lint (needs operator-evidence from V1.1 first runs); broaden CODEOWNERS reviewer pool (needs maintainer team); `cyclonedx-bom` hash-pinning (Razor file-budget concern); future V2 extensions (calendar/GH-issue integration for tracker; broaden cooling-period to non-exact pyproject specifiers).

**Decision**: Phase 106 implemented; audit PASS on iter-1 (L2; tooling extension). Substantiated as v0.74.0 (feature → minor bump). Phase 105 V2 carry-forward 3 of 5 items shipped; dependency-admission lint surface now operative on PR-label, ledger, and pyproject signals.

## Phase 107 (v0.75.0 — 2026-05-26): Carry-forward close en masse (V2 list reaches zero)

Feature closing ALL five V2 carry-forward items accumulated across Phases 101-106 in one cohesive cycle per the operator's `/qor-auto-dev-1` "wrap with zero pending items remaining" directive. After this seal, the project's V2 carry-forward list is **empty**.

**Five deliverables shipped**: (1) cooling-period lint flipped from WARN-only to hard fail (Phase 105 V2 #1); (2) cyclonedx-bom hash-pinned via new `requirements-sbom.{in,txt}` (Phase 102 V2); (3) range-pin lower-bound coverage via new `parse_pyproject_range_pins(text)` (Phase 106 V2); (4) tracker `--emit-issue` flag invoking `gh issue create` for due rollup entries (Phase 105 V2 calendar/GH-issue); (5) CODEOWNERS solo-owner doctrine note in `doctrine-governance-enforcement.md` §6.1 with 4 expansion triggers (Phase 101 V2).

**Hard-fail flip**: `.github/workflows/pr-dependency-review.yml` removed the `|| true` wrap on the cooling-period lint step. Lint exit-1 on real violations now blocks PR merge. The operator override path (META_LEDGER `**Dependency admission override**:` entry OR `dep-admit-override` PR label) remains operative as the loud-recoverable safety valve. Authority for the flip is the operator's direct command; the evidence-second ramp stage was operator-overridden as documented in the audit's non-blocking observation 2.

**cyclonedx-bom hash-pinning**: pip-compile autogenerated `requirements-sbom.txt` is 392 lines (lxml alone carries ~120 wheel hashes). Explicit narrow Razor exemption declared in the plan and approved at audit (autogenerated lockfile; size tracks dependency graph, not authoring complexity). Release workflow build job switched from `pip install cyclonedx-bom` to `pip install --require-hashes -r requirements-sbom.txt`. Exemption scope is this single file only; no broader pattern.

**Range-pin lower-bound coverage**: new `parse_pyproject_range_pins(text) -> list[LockfileEntry]` extracts lower-bound versions from `>=X.Y.Z` and `~=X.Y.Z` PEP 440 specifiers in `[project] dependencies` and `[project.optional-dependencies]`. The lint applies the 14-day threshold to those lower-bound versions because pip's installer could resolve to that version on a fresh install (conservative interpretation: catches the earliest possible install). `<`, `!=`, and unbounded specifiers are skipped. qor-logic's current pyproject (`jsonschema>=4`, `PyYAML>=6`) has version 4 and 6 as lower bounds — both ancient (well outside the window) — so no false positives at this seal.

**GH-issue emit**: `dep_admit_override_tracker.py` gained `--emit-issue` flag. When set, builds a single rollup body listing due (≥30 days old) override entries from META_LEDGER and invokes `gh issue create --title "..." --body "..." --label dep-admit-override-review`. Single rollup per invocation (anti-spam); silent (no gh call, no output) when no due entries. Network behavior matches Phase 106's gh PR-label query (subprocess.run with check=True, timeout=30; no automatic retry since this is operator-initiated).

**CODEOWNERS solo-owner doctrine**: new `qor/references/doctrine-governance-enforcement.md` §6.1 "CODEOWNERS operational mode" documents the current solo-owner state (`@Knapp-Kevin` for all security-critical files) as the project's deliberate operational mode for solo-maintained governance repositories, not an interim placeholder. Four expansion trigger conditions named: (1) second maintainer joins, (2) federation with other Qor-logic deployments, (3) compliance audit requires reviewer separation, (4) operator-initiated team formalization. Closes Phase 101 carry-forward via documentation rather than scaffold change; future expansion is gated on a real trigger event.

**Test surface**: 13 new behavioral tests across 4 amended + 2 NEW test files. All invoke the unit and assert on output (lockfile parser dataclass fields, lint exit codes + override status, tracker rollup body content + gh subprocess args, workflow YAML shape, doctrine text presence). Mocked gh CLI + PyPI. All pass twice deterministically (51/51 in two consecutive targeted runs; 4.29s + 4.10s). Full regression at seal: 1960 collected (1957 passing after badge updates).

**TDD red-green**: test files authored FIRST; 7 RED at initial run. Implementation files written; 51/51 GREEN first attempt across all 7 targeted test files. Determinism verified by second run.

**Razor compliance**: all new functions <40 lines (`parse_pyproject_range_pins` 33, `emit_rollup_issue` 27). File totals: `_dep_admit_common.py` 167 → ~205; `dependency_admission_lint.py` 213 → ~225; `dep_admit_override_tracker.py` 123 → ~165; test files within budget. `requirements-sbom.txt` (392 lines) is Razor-exempt per the explicit narrow exemption block in the plan + audit ratification.

**Self-application discipline (Phase 68 sub-pass)**: D-107.2 IS the artifact-ancestry discipline applied to the SBOM tool itself (the tool that produces the SBOM is now hash-pinned). D-107.1 commits the operator to the hard-fail enforcement they authorized. D-107.5 closes a carry-forward via deliberate documentation rather than waiting for an external trigger. No new top-level third-party Python dependencies introduced. Phase 105's self-application argument extends through this phase.

**SG-StructureWithoutPolicy-A countermeasure**: fully closed across two distinct surfaces — (a) the dependency-admission chain: Phase 103 declaration → Phase 105 ledger+tracker signal → Phase 106 PR-label signal → Phase 107 hard-fail enforcement; (b) the SBOM toolchain: Phase 102 introduces cyclonedx-bom unpinned → Phase 107 hash-pinned. The pattern is now operative as a complete countermeasure across structure → declaration → enforcement → artifact-ancestry layers at the supply-chain perimeter.

**Phase 107 conventions self-applied at this seal**:
- Session ID `2026-05-26T1410-c8f107` is a conforming 6-hex slug (Phase 106 convention); `session_id_lint` runs silent at Step 4.6.
- The Phase 106 `dependency_admission_lint` runs at PR-check time on this PR; will be the **first PR to encounter the hard-fail variant** when its workflow runs (operationally: should still pass because qor-logic's current pyproject deps and lockfile are all >14 days old; the hard-fail flip doesn't regress on existing state).
- doc_integrity strict passes cleanly (4 new glossary terms wired to their `referenced_by` paths; no drift remediation needed).
- All Phase 75 substantiate-step prerequisites are met (Python toolkit + pyproject.toml + CHANGELOG.md); no SKIP records emitted.

**Carry-forward (post-Phase-107)**: **EMPTY**. The operator's "wrap this session with zero pending items remaining" directive is satisfied at this seal. Future cycles begin from a clean carry-forward state.

**Operator-directive Review Boundary override**: per the `/qor-auto-dev-1` wrap directive, the default stage-artifacts-only Review Boundary was explicitly overridden to include commit + push + PR + merge + tag + PyPI deployment within this cycle. The orchestrator handles those remote actions after this seal as part of the wrap; substantiate writes the seal entry as the cryptographic anchor before they execute. The override is logged in the seal entry text for chain-of-custody.

**Decision**: Phase 107 implemented; audit PASS on iter-1 (L3 high_risk_target). Substantiated as v0.75.0 (feature → minor bump). **V2 carry-forward list reaches zero; session wrapped per operator directive.**

---

## Phase 109: Governance artifact health gate

**New surface**: `qor.scripts.governance_health` classifies the required governance artifacts (`META_LEDGER`, `CONCEPT`, `ARCHITECTURE_PLAN`, `SYSTEM_STATE`, `SHADOW_GENOME`, `BACKLOG`, `FEATURE_INDEX`) as OK / UNINITIALIZED / MISSING / DAMAGED / INCOMPLETE, each with its single legal next action. Exposed as `qor-logic governance-health` (CLI) and `python -m qor.scripts.governance_health` (exit 0 OK / 1 MISSING|INCOMPLETE|UNINITIALIZED / 2 DAMAGED).

**Enforcement**: 17 governance-reading source skills carry `qor:governance-health-preflight`; `qor-bootstrap` (inverse guard) and `qor-remediate` (repair) carry justified `qor:governance-health-exempt` markers. Markers are preserved into all three skill variants (claude/codex/kilo-code). `/qor-status` gains a Step 0 health gate that surfaces DAMAGED/INCOMPLETE before lifecycle routing.

**Scaffold-owned set** is pinned to `qor.seed.SEED_TARGETS` file targets so the seed list and the required-artifact list cannot drift (LD3). `docs/GOVERNANCE_INDEX.md` is explicitly out of scope (LD1); the registry is extensible for a future Governance Index phase.

**Doctrine**: `doctrine-prompt-resilience.md` defines Governance Artifact Health and Ungoverned Path Forward; `skill-recovery-pattern.md` defines Governance Repair Mode and the preflight snippet; `doctrine-governance-enforcement.md` §15 records the no-ungoverned-path-forward invariant; glossary gains the three terms.

**TDD**: test files authored first (governance_health, prompt-health-coverage, qor-status routing, CLI exit codes, variant drift); RED confirmed before implementation; GREEN and determinism verified.

---

## Phase 140: governance-health + ledger-seal robustness (GH #199, #200, #201)

**New surface**: `qor.scripts.ledger_hash` gains `assert_sealable_text(text, *, label)` (raises `ValueError` naming the first non-ASCII codepoint + index) and `normalize_punctuation(text)` (opt-in smart-punctuation -> ASCII map, idempotent). `qor.scripts.ledger_fragment` calls the gate in both `write_fragment` (fragment creation) and `canonicalize_fragments` (the META_LEDGER write), so non-ASCII / codepoint-truncated / cp1252 bytes can no longer be sealed into a content hash; on rejection the ledger is left untouched and fragments stay pending (GH #201).

**Skill-entry tolerance (GH #199)**: `governance_health._ledger_damage` now falls back to `_verify_post_anchor` (wrapping `ledger_hash.verify_post_anchor`) when strict `ledger_hash.verify` fails. A disclosed pre-anchor residual (failure at or below the auto-detected boundary) is tolerated -- parity with the release gate -- while a genuine post-anchor failure still classifies `DAMAGED`. Closes the asymmetry where the skill-entry preflight hard-failed single-lineage manual-era residuals the release gate already accepts.

**Placeholder discipline (GH #200)**: `governance_health._PLACEHOLDER_MARKERS` (bare-substring tuple) is replaced by `_PLACEHOLDER_PATTERNS` (compiled regexes requiring a structural cue: colon-suffixed to-do / fix-me labels, HTML-comment to-do scaffolds, mustache verify tags, bracketed fill-in slots). `_incomplete_reason` matches via `pattern.search` and names the matched marker. Prose mentions of the bare to-do word no longer false-positive a non-ledger artifact as `INCOMPLETE`; the ledger path (`_ledger_incomplete`) is unchanged.

**TDD**: three test files authored first (`test_ledger_seal_utf8_validation`, `test_governance_health_post_anchor_tolerance`, extended `test_governance_health`); RED confirmed (8 failing), then GREEN; the three target suites (19 tests) run green twice for determinism. doc_tier standard; no new dependencies; no new glossary terms (existing symbols).

---

## Phase 141: compliance-conveyance integrity (control matrix + conformance + ratchet)

**New surface**: `qor/compliance/control_matrix.json` (+ `qor/gates/schema/control_matrix.schema.json`) is the declarative registry of every compliance control Qor-logic conveys downstream -- each row carries framework, enforcing module, posture (ABORT/WARN), detection mode (skill-marker/test/ci-job), conveyance target, and variants. Seeded with the deterministic shipping controls (prompt-injection, prose-test-lint, secret-scan, data-api-acl, badge-currency, governance-index, gate-chain-completeness, ai-provenance, dependency-review). `qor.scripts.compliance_matrix` loads + schema-validates it.

**Conformance gate**: `qor.scripts.compliance_conformance.verify_all` (pytest `test_compliance_conformance.py`) verifies each row is wired at its declared posture and reaches the conveyed payload, dispatching on detection mode (skill-marker checks the source skill step + every variant's compiled skill; test checks the named behavioral test exists; ci-job checks the workflow references the module). Runs in the existing CI pytest matrix; a downgraded or un-conveyed control reds every PR. Self-validating: a wrong seeded posture reds its own conformance test.

**Ratchet**: `qor.scripts.compliance_ratchet.ratchet_check` (pytest `test_compliance_ratchet.py`) compares the matrix against the prior release tag via `git show`; a dropped or `ABORT -> WARN` control fails unless a `waivers` entry (id+justification+issue) covers it. Growth is always allowed; first introduction is a no-op. Makes conveyed compliance monotonic across versions.

**Doctrine**: `qor/references/doctrine-compliance-conveyance.md` is the home for the four new glossary terms (Compliance Control Matrix, Control Posture, Conveyance Conformance, Compliance Ratchet).

**TDD**: three test files authored first; RED confirmed, then GREEN; the conformance test caught a step-anchor substring bug and the gemini `commands/*.toml` variant layout during build before passing. doc_tier standard; no new dependency (jsonschema already present); hooks explicitly out of scope per operator.

---

## Phase 142: downstream enforcement SDK (engagement manifest + mini-SDK)

**New surface**: the Phase 141 control matrix gains two precursor fields per control -- `engagement` (which active enforcement layers it plugs into: pre-commit/pre-push/pre-tool-write/ci/seal) and an optional `runner` (`module`/`entry`/`args`) for controls standalone-runnable at a runnable point. Schema + `qor.scripts.compliance_matrix` (`ENGAGEMENTS`, `RUNNABLE_POINTS`, `load_packaged_matrix`) carry them; all nine controls seeded (four runnable: secret-scan, data-api-acl, prose-test-lint, badge-currency; prompt-injection is ci, the rest seal).

**SDK**: `qor.compliance.enforce` (`run_control`, `select`, `enforce`, `Verdict`, `ControlResult`), re-exported at `qor.sdk`, surfaced as `qor-logic compliance enforce --engagement <point>` (wired in `cli_handlers/compliance.py`). It loads control definitions from the installed package and runs each wired runnable control against the consumer working tree, returning a `Verdict` (ABORT-posture failures fail it; WARN advisory). Downstream owns the trigger; no hook installer ships.

**Packaging**: `pyproject.toml` package-data gains `compliance/*.json` so the matrix actually reaches pip consumers (without it the SDK had no manifest downstream).

**Conformance**: `compliance_conformance._verify_runner` folds into `verify_control` -- every control engaging a runnable point must have an importable, callable runner; the live conformance test guards it.

**Docs**: `doctrine-compliance-conveyance.md` extended (engagement manifest + runner + ownership boundary); new `qor/references/downstream-enforcement-sdk.md` (consumer contract); two glossary terms (Engagement Point, Enforcement Runner).

**TDD**: tests authored first across loader/enforce/conformance/packaging; RED then GREEN; 21 target-suite tests deterministic x2. doc_tier standard; no new dependency (importlib/contextlib/tomllib stdlib); Razor-clean. Hooks explicitly out of scope per operator.
