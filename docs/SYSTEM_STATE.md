# Qor-logic System State

**Snapshot**: 2026-04-30
**Chain Status**: ACTIVE (Phase 53 feature sealing at v0.39.0 — prompt-injection defense + path canonicalization + intent-lock anchored regex)
**Phase**: Phase 53 sealed (feature). First phase of a five-phase compliance sprint per `docs/research-brief-prompt-logic-frameworks-2026-04-30.md`. Closes OWASP LLM Top 10 (2025) **LLM01 Prompt Injection** (HIGH) at the audit-prose layer for operator-authored governance markdown surface; aligns with NIST AI 600-1 §2.7 and EU AI Act Art. 15 cybersecurity dimension. New `qor/scripts/prompt_injection_canaries.py` (frozen six-class catalog: instruction-redirect, role-redefinition, pass-coercion, meta-override, unicode-directionality, hidden-html); `scan(content)` API; argv-form CLI with `--mask-code-blocks` flag for documentation scanning. `/qor-audit` Step 3 Prompt Injection Pass runs before Security Pass; commit-time complement via fifth `forbid` rule on `Code::"governance"` resources in `qor/policies/owasp_enforcement.cedar`. New `qor/policy/resource_attributes.py` (`compute_governance_attributes`, `is_governance_path`) is the caller-side helper; evaluator unchanged. New doctrine `qor/references/doctrine-prompt-injection.md`. SG-PromptInjection-A appended to countermeasures. `prompt-injection` added to `findings_categories` enum. **OWASP (2021) LOW-4 closed**: `qor/reliability/intent_lock.py:_audit_has_pass` regex tightened from substring `re.search VERDICT.*PASS` to multiline-anchored canonical-line form. After Phase 53: zero residual OWASP (2021) MEDIUM/LOW findings open. **DRIFT-1 + DRIFT-2 closed**: full skill+agent tree sweep cleared `.failsafe/governance/` and `memory/failsafe-bridge.md` legacy references (4 skill files + 5 agent files). 30 source files touched; 947 tests passing twice in a row (deterministic, +37 from Phase 52). Three new glossary terms (prompt-injection canary, untrusted-data quarantine, instruction-anchor regex). Self-application Phase 4 verified: plan + brief + doctrine all scan clean once code-block masking is applied. Sprint roadmap: Phases 54 (AI provenance + AI Act doctrine), 55 (subagent least-privilege + model-pinning), 56 (secret-scanning gate), 57 (override-friction escalator) queued. Previous phase -- Phase 52 sealed (feature). First phase in repo history authored under proper /qor-plan + /qor-audit + /qor-implement + /qor-substantiate skill invocations with all four real `.qor/gates/<sid>/*.json` artifacts written. Three sub-phases: (1) **Structural enforcement (keystone)** — new `qor/reliability/gate_chain_completeness.py` (103 lines) walks SESSION SEAL ledger entries and asserts plan/audit/implement/substantiate gate artifacts exist for sealed phases ≥ 52; new `ProvenanceError` + `QOR_SKILL_ACTIVE` env-var binding on `gate_chain.write_gate_artifact()` refuses calls without skill provenance (`QOR_GATE_PROVENANCE_OPTIONAL=1` autouse fixture in `tests/conftest.py` for test compatibility). (2) **G-1 SSDF tag emission** — new `qor/scripts/ssdf_tagger.py` (99 lines) computes practice tags from `change_class` + `files_touched` (via `git diff --name-only`); `/qor-substantiate` Step 7.4 emits `**SSDF Practices**:` line into SESSION SEAL entry; new `gate-chain-completeness` job in `.github/workflows/ci.yml` blocks PR merges to main on missing gate artifacts. (3) **Retroactive remediation + SG promotion** — closes Phase 46 razor VETO (`tests/test_doctrine_test_functionality.py` split via `tests/_helpers.py` extraction; both files ≤250 lines), Phase 48 presence-only test VETO (`tests/test_install_drift_check_subprocess.py` replaces source-grep with subprocess invocation), Phase 49 self-exempting cutoff VETO (`tests/test_attribution_tiered_negative_paths.py` adds 6 fixture-based synthetic-violator tests); 3 narrative SG entries promoted to structured countermeasures (SG-SkillProtocolBypass, SG-VacuousLint, SG-RecursiveBashInjection). 13 new files + 10 modified; 69 phase-specific tests; 910 full suite passing twice (delta +44 from Phase 50's 866 baseline). Variants regenerated (236 files, no drift). SSDF tag emission self-applied: this seal entry carries `**SSDF Practices**: PO.1.3, PO.1.4, PS.2.1, PS.3.1, PW.1.1, PW.4.1, PW.5.1, RV.1.1, RV.1.2`. Forward-only emission; entries < #169 grandfathered (immutable Merkle chain). `gate_chain_completeness.check(phase_min=52)` returns `ok=True` for this session's all four gate artifacts. Previous phase -- Phase 50 sealed (feature). Closes G-2 from `docs/compliance-re-evaluation-2026-04-29.md`. Skill prose performing filesystem operations on operator-controlled identifiers (`.qor/session/current`) MUST cite the canonical validator helper (`qor.scripts.session.current()` which validates against `SESSION_ID_PATTERN`). `qor/references/doctrine-owasp-governance.md` §A03 gains a "Skill-prose worked example" paragraph; `/qor-help --stuck` Mode protocol step 1 routes through the helper; `qor-implement` Step 5.5 and `qor-substantiate` Step 4.6 bash one-liners updated from `cat .qor/session/current` to `python -c "from qor.scripts.session import current; print(current() or 'default')"`. New 5-test lint with proximity-anchor + strip-and-fail. 866 tests passing twice (delta +5). Phase 49 badge currency enforcement self-applied (passes). Previous phase -- Phase 49 sealed (feature). Closes G-3 and G-4 from `docs/compliance-re-evaluation-2026-04-29.md`. (1) **Tiered attribution policy**: `qor/references/doctrine-attribution.md` `## Tiered usage` table defines required form per surface (seal commit / plan-audit-implement commits / merge / PR description / CHANGELOG / GitHub release); new `qor.scripts.attribution.commit_trailer_compact()` helper. (2) **README badge currency enforcement**: new `qor/scripts/badge_currency.py` (140 lines, pure functions, CLI entrypoint); `/qor-substantiate` Step 6.5 promoted from WARN to ABORT for `change_class ∈ {feature, breaking}`; hotfix exempt. (3) Self-application clean: this seal cycle's Tests badge updated to 862 (truth) and the new currency check passes. 23 new tests (9 attribution-tiering + 8 badge-currency + 6 substantiate-wiring), each invoking the unit and asserting on output, paired with strip-and-fail negative-paths per Phase 46 doctrine. Phase 33 release-doc currency satisfied: CHANGELOG.md `## [0.36.0]` section with the canonical attribution line `_Built via [Qor-logic SDLC](url)._`; pyproject.toml at 0.36.0. 861 tests passing on two consecutive runs (delta +23). Variant artifacts regenerated; 236 files, no drift. Previous phase -- Phase 48 sealed (feature). Three coupled UX/install/discovery improvements. (A) **Script discoverability**: closes the Phase 35 gap that fixed only `qor/reliability/`; the three remaining `qor/scripts/` skill invocations (`qor-shadow-process` lines 89/101 + `qor-process-review-cycle` line 57) now use module form `python -m qor.scripts.<name>` so they resolve against the installed package from any CWD. `doctrine-governance-enforcement.md` §138 rewritten symmetric across both `qor/scripts/` and `qor/reliability/`; §92 prose example also updated. New lints `tests/test_installed_import_paths.py::test_no_path_form_qor_scripts_invocations` + `::test_no_path_form_qor_reliability_invocations` prevent regression. (B) **`qor-logic` canonical CLI**: `pyproject.toml` `[project.scripts]` declares both `qor-logic = "qor.cli:main"` (canonical) and `qorlogic = "qor.cli:main"` (backwards-compat alias entry point). `argparse prog="qor-logic"`; `--version` emits `qor-logic <semver>`. 51 operator-facing CLI invocations renamed across `qor/skills/`, `qor/references/`, `README.md`, `docs/operations.md`, `docs/policies.md`. Filesystem state paths (`.qorlogic/config.json`, `.qorlogic-installed.json`) preserved for operator data integrity (negative-lookbehind regex excludes them). New `tests/test_cli_rename.py` locks both entry points + program-name output via `tomllib.loads` + `cli.main(["--version"])` capsys capture + `cli.main(["--help"])` capsys capture. New skill-prose lint `test_skill_prose_uses_qor_logic_for_cli_invocations` with self-test `test_qorlogic_cli_regex_excludes_filesystem_state_paths`. (C) **`/qor-help` conversational**: skill evolves from static catalog into three-mode skill. Bare `/qor-help` shows intro ("How to use /qor-help") + ASCII SDLC flow chart (plain ASCII, verified via `body.encode('ascii')` round-trip) + catalog tables + "Using /qor-help" section. `/qor-help --stuck` reads `.qor/session/current` and globs `.qor/gates/<sid>/*.json` to infer SDLC position (rank order: research < plan < audit < implement < substantiate), reads audit verdict if present, recommends next skill with rationale per `doctrine-audit-report-language.md`. `/qor-help -- "<question>"` routes free-form question against catalog + state, identifies 1-3 relevant skills with rationale; LLM running the skill is the routing engine, catalog is single source of truth. All modes are read-only; "NEVER execute other skills" constraint preserved. `tests/test_qor_help_conversational.py`: 5 positive proximity-anchored assertions paired with 5 strip-and-fail negative-paths per Phase 46 doctrine; ASCII chart positionally verified for SDLC phase order (research before plan before audit before implement before substantiate). Phase 33 release-doc currency satisfied: `CHANGELOG.md ## [0.35.0]` section added with Added + Changed entries; `pyproject.toml` at 0.35.0; system-tier docs (`docs/operations.md`, `docs/policies.md`) refreshed for the rename. Variant artifacts regenerated via `python -m qor.scripts.dist_compile`; 236 files, no drift. 838 tests passing on two consecutive runs (delta +21 from Phase 47's 817 baseline). **Substantiate remediation**: original Phase 48 substantiate cycle landed seal commit without writing META_LEDGER entries (eighth instance of SG-AdjacentState-A bookkeeping-gap dimension). Remediation: this entry triplet (#158 audit, #159 implement, #160 seal) added retroactively against Phase 47 chain (`1eb7bb31...`); seal commit amended; tag `v0.35.0` recreated at amended commit. Phase 47 step 7.7 gate would have caught the gap had `/qor-substantiate` skill been invoked — manual seal bypassed the skill protocol. Pattern signal: skill protocols are load-bearing; manual short-circuits violate doctrine even when convenient. Previous phase -- Phase 47 sealed (feature). Adds the structural countermeasure for SG-AdjacentState-A's bookkeeping-gap class — the family that allowed Phase 46's first substantiate to seal at v0.33.0 without writing META_LEDGER entries. New: `qor/reliability/seal_entry_check.py` (128 lines) — pure-function helper exposing `check(ledger_path, phase_num)` returning `SealEntryResult(ok, errors)`. Reads the ledger, asserts the latest entry is a SESSION SEAL for the given phase, verifies the chain hash is internally consistent (`chain_hash == chain_hash(content_hash, previous_hash)`), then runs full chain verification via `ledger_hash.verify()`. Single source of truth = the ledger; no caller-supplied Merkle seal expectation. Wired into `/qor-substantiate` as new **Step 7.7 (Post-seal verification)** between Step 7.6 (Stamp CHANGELOG) and Step 8 (Cleanup Staging) — runs *after* Step 7 (Final Merkle Seal) writes the entry. Bash one-liner uses hardcoded `python -c` (no shell-variable interpolation into Python literals) calling `governance_helpers.current_phase_plan_path()` to derive the plan path; argv-form `--plan "$PLAN_PATH"` invocation throughout. 15 phase-47 tests added: 9 behavioral tests (`tests/test_seal_entry_check.py`) including the meta-test `test_check_replays_phase_46_original_gap` that proves the new gate would have caught the historical sixth-instance gap, plus `test_cli_rejects_path_with_shell_metacharacters_safely` confirming argv-form eliminates the OWASP A03 vector flagged in Pass 1 V-3; 6 defensive wiring tests (`tests/test_substantiate_seal_entry_wiring.py`) using the proximity-anchor + strip-and-fail pattern from Phase 46 doctrine, including direct countermeasures locking V-1 (post-Step-7 placement), V-2 (no `$MERKLE_SEAL` reference), V-3 (no `python -c "...'$VAR'..."` interpolation) against future drift. Substantiate dogfoods Phase 47: Step 7.7 runs against Phase 47's own seal entry as part of this seal cycle. Phase 47 took three audit passes to reach PASS — Phase 1 (helper + tests) was sound on first attempt; Phase 2 wiring (bash glue between helper and skill step) was the recurring failure point across all three passes (V-1/V-2/V-3 in Pass 1 plan, V-1 in Pass 2 plan). SG-AdjacentState-A pattern signal: directives that specify "use X" without specifying "how to obtain X" leave a wiring slip surface. Phase 33 release-doc currency satisfied: CHANGELOG.md `## [0.34.0]` section added; pyproject.toml at 0.34.0; README.md badges refreshed. Variant artifacts regenerated under `qor/dist/variants/`; 211 files, no drift. 817 tests passing on two consecutive runs (delta +15). Previous phase -- Phase 46 sealed (feature). Codifies the "test functionality, not presence" principle as a first-class doctrine and wires enforcement language into the four SDLC gate skills. New: `qor/references/doctrine-test-functionality.md` (Principle, Definitions, Rule with the acceptance question — "If the unit's behavior were silently broken but the artifact still existed, would this test fail?", Anti-patterns table citing SG-035 and the Phase 45 originating instance, Verification mechanisms, Update protocol). CLAUDE.md Authority line links the new doctrine alongside `attribution`. `/qor-plan` Step 4 forbids presence-only test descriptions; Step 5 review checklist requires each test description to name the behavior it confirms. `/qor-audit` gains a Test Functionality Pass between Section 4 Razor and Dependency Audit (VETO with `test-failure` category against any plan whose described tests do not invoke the unit). `/qor-implement` Step 5 (TDD-Light) requires the failing test invoke the unit and assert against its output; Step 9 scans newly-added tests for the `assert <substring> in <file_text>` family. `/qor-substantiate` Step 4 Test Audit refuses to seal if a phase-added test is presence-only. `tests/test_doctrine_test_functionality.py` locks each surface with proximity-anchored regex assertions paired with strip-and-fail negative-path tests so the doctrine test cannot itself decay into a presence-only check (every positive proximity assertion is paired with a corresponding negative-path test that proves stripping the named section makes the positive assertion fail). 20/20 doctrine tests green twice in a row. Variant artifacts regenerated under `qor/dist/variants/`. Substantiate remediation: Phase 46's original seal commit landed without META_LEDGER entries; this seal cycle adds Entry #150 (audit), #151 (implementation), #152 (seal) and rebases onto Phase 45 to compute correct chain hashes. Previous phase -- Phase 45 sealed (feature). Implements GitHub issue #18 — a documented convention for crediting Qor-logic SDLC in commit trailers, PR footers, and CHANGELOG attribution lines, plus a pure Python helper as the canonical source of the strings. New: `qor/scripts/attribution.py` (3 pure functions: `commit_trailer`, `pr_footer`, `changelog_attribution_line`; module-level constants are the single source of truth, kwargs override per-call), `qor/references/doctrine-attribution.md` (full doctrine including the narrowly-scoped emoji exception for bot-attribution trailer text), root `ATTRIBUTION.md` (one-screen quick-ref with copy-pasteable strings). CLAUDE.md Authority line updated. 15 phase-45 tests added: 10 unit/functionality (including a real `git interpret-trailers --parse` check that catches trailer-format drift presence-tests would miss) + 5 drift-guard tests asserting helper output appears verbatim across the doc surfaces. No skill wiring this phase by design (option B: doc + helper, defer wiring); follow-up Phase 46 will enforce test-functionality in Qor-logic's own SDLC skill prompts. Audit blind spot logged: Phase 45 audit cleared all six structural passes but missed two plan-format conventions (`change_class` enum, heading capitalization) that block the repo's own `tests/test_skill_doctrine.py` and `tests/test_plan_schema_ci_commands.py`; mid-implement plan corrections applied. 782 tests passing on two consecutive runs (delta +15). Previous phase -- Phase 44 sealed (hotfix). Resolves a Phase 41 regression: `qor/scripts/ledger_hash.py`'s strict `**Field**` anchor silently skipped SESSION SEAL entries with the standard `**Chain Hash (Merkle seal)**:` / `**Content Hash (session seal)**:` markup convention (7 ledger entries: #126, #129, #132, #133, #137, #140, #143). Three-regex relaxation adds optional parenthetical suffix `(?:\s*\([^)]+\))?` inside bold markers; preserves Phase 41's bold-anchor + bounded-span + two-form value protections. Anti-vacuous-green tests added: every modern (≥#116) entry with hash markup must verify; counts verified entries against the real ledger rather than relying on `rc == 0`. Verifier metric: pre-fix 104 OK / 39 skipped; post-fix 112 OK / 32 skipped. SG-AdjacentState-A (provisional family across Phase 41/42/43/44 plan blind spots) — fourth instance promotes the family to formal SG status; the anti-vacuous-green guard provides the structural countermeasure. Previous phase -- Phase 41 sealed (feature). Resolves GitHub issue #13. Three-axis scope: (1) `qor/scripts/ledger_hash.py` `CONTENT_HASH_RE` and `PREV_HASH_RE` now accept fenced `= <hex>` form (new capability, symmetric with `CHAIN_HASH_RE`); (2) all three regexes now require `**Field**` bold anchor and use a bounded non-greedy span via negative lookahead on the next `**FieldName**` marker (eliminates a class of cross-field-bleed accidents); (3) `qor-validate/SKILL.md` Steps 3/4/7 now reference `qor/scripts/ledger_hash.py` + `qorlogic verify-ledger` CLI instead of the stub `.claude/commands/scripts/validate-ledger.py` path. Phase 33 doctrine release-doc currency satisfied: CHANGELOG.md `## [0.31.0]` section + README.md badge refresh (Tests 602→752, Ledger 104→140). 8 new regression tests; 3 existing tests amended with `capsys`-based `OK   Entry #N:` assertions; new `tests/test_qor_validate_skill_references.py` lints source + dist variants. Intent-lock verified first-try post-implement-commit (Phase 43's ancestry fix working live). Previous phase -- Phase 43 sealed (hotfix). Replaces strict HEAD-equality check in `qor/reliability/intent_lock.py` `verify()` with `git merge-base --is-ancestor` ancestry check. Captured HEAD must be reachable from current HEAD; current HEAD may be any forward descendant. Plan-hash and audit-hash equality checks unchanged. Eliminates the re-capture-as-SOP anti-pattern observed in Phase 41 and Phase 42 substantiate where the implement commit between Step 5.5 capture and Step 4.6 verify always tripped `DRIFT: head`. Real anti-drift threats (history rewrites, hard resets, branch switches to divergent histories) still caught. SG-AdjacentState-A (provisional family) logged across Phase 41/42/43 Pass 1 plan-blind-spots — countermeasure becoming reflexive. Previous phase -- Phase 42 sealed (hotfix). Resolves the chicken-and-egg CI failure that blocked PRs #10 (v0.29.0) and #11 (v0.30.0). `test_every_changelog_section_has_tag` now exempts pre-release CHANGELOG sections — versions above the highest existing git tag — from the match-a-tag rule, breaking the collision with Phase 40's LOCAL-ONLY tag doctrine. Pure `_released_orphans(versions, tags)` helper extracted; three direct-call TDD tests cover above-highest / at-or-below-highest / no-tags cases. CHANGELOG.md backfilled with `## [0.28.1]` (Phase 40 retrospective) and `## [0.28.2]` (this hotfix) so the symmetric `test_every_tag_has_changelog_section` is satisfied against origin tags. Local orphan tags v0.29.0 and v0.30.0 (from unmerged phase 39/39b seals) deleted; will be recreated on respective merge commits. 716 tests passing on two consecutive runs. Previous phase -- Phase 33 sealed. Seal-tag timing bug (off-by-one across v0.19.0-v0.22.0) fixed — `governance_helpers.create_seal_tag` now takes a required `commit: str` positional; `/qor-substantiate` Step 7.5 reduced to `bump_version` only; new Step 9.5.5 captures the post-commit SHA via `git rev-parse HEAD` and tags it. Release-doc currency rule added (Phase 33 addition to Step 6.5): when `plan.change_class ∈ {feature, breaking}`, README.md and CHANGELOG.md must appear in `implement.files_touched`; hotfix exempt. SG-Phase33-A records the historical bug + countermeasure; META_LEDGER Entry #112 backfills the 4 affected-tag inventory (historical tags not retagged — rewriting published remote discouraged; no consumer depends on them). 636 tests passing on two consecutive runs (delta +14). First phase branch to start from a reconciliation-merge base (`git merge --no-ff v0.23.0` as Phase 33's first commit) to bring phase/32-amended content back into scope after the PR #4 auto-merge race published pre-amend content to main. Phase 32 prior -- Check Surface D + E are now LIVE STRICT at `/qor-substantiate` Step 4.7 -- any term-drift or cross-doc conflict ABORTs seal. Check Surface D + E are now LIVE STRICT at `/qor-substantiate` Step 4.7 -- any term-drift or cross-doc conflict ABORTs seal. Zero-drift baseline established in Phase 2 via `docs/*.md` archive-by-default scope-fence (only the 4 system-tier docs are living; README + CHANGELOG excluded as narrative entry points) plus broad `referenced_by:` adoption for high-usage terms. Install drift check (`qor/scripts/install_drift_check.py`) SHA256-compares source SKILL.md vs installed copies; invoked as CLI or at `/qor-plan` Step 0.2 as pre-phase WARN. Doctrine §8 Install Currency documents the contract. 622 tests passing on two consecutive runs (delta +20). Phase 32 is the first plan to substantiate under live strict-mode D/E and passed cleanly on first attempt -- the zero-drift baseline held. Previous phase --  Operationalization bundle closes 8 of the 10 items from the post-Phase-30 gap inventory. New machinery: `/qor-substantiate` Step 6.5 Documentation Currency Check (WARNs when doc-affecting changes ship without system-tier doc updates); Check Surface D/E scope-fence tuning (doctrine-peer + home-dir-peer + per-entry scope_exclude); `doc_integrity_drift_report.py` operator CLI; `pr_citation_lint.py` + `.github/workflows/pr-lint.yml` enforcing doctrine-governance-enforcement §6 on every PR; SHA256 install-sync test catching dist drift at CI time; session marker path unified (`MARKER_PATH` = `.qor/session/current`). Live drift triage artifact `docs/phase31-drift-triage-report.md` captures residual-known-drift state. Path-unification migration had a lossy moment at first Phase 31 substantiate attempt (old `.qor/current_session` vs new `.qor/session/current` marker files both exist with different contents; manual migration applied). 602 tests passing on two consecutive runs (delta +29). SG-Phase31-A (in-plan correction parallel to source instead of upstream fix) + SG-Phase31-B (plan self-modification post-audit) codified; both countermeasures applied live during pass-1 VETO -> pass-2 PASS amendment. First seal to exercise Step 6.5 against its own output -- caught 9 currency warnings, system-tier docs amended mid-substantiate.

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

**Deferred (Phase 39b)**:
- Phase 3 (operator action): `ANTHROPIC_API_KEY=... python qor/scripts/ab_live_run.py` produces `docs/phase39-ab-results.md`. Cost ~$32 per full cycle at Opus 4.7 pricing (corrected from plan's earlier ~$4 estimate). ~10-15 min wall-time.
- Phase 4 (conditional on Phase 3 results): S3 persona sweep across 24 skills; R3 Identity Activation rewrites fire only if Phase 3 declares `winner: "stance"`; R4 (qor-debug → doctrine cross-reference); R5 (qor-document persona-vs-agent disambiguation).

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
- **R3 pending**: test `test_identity_activation_matches_ab_winner_if_results_exist` enforces conditional rewrite when operator produces `docs/phase39-ab-results.md` via `/qor-ab-run`.
- **LOAD_BEARING_PENDING_EVIDENCE registry** (19 skills): documented transitional state awaiting A/B evidence.

**Tests**: 743 pytest green × 2. Admission: `qor-ab-run` admitted. Matrix: 29 skills, 112 handoffs, 0 broken.

**Naming note**: branch `phase/39b-*` + plan `plan-qor-phase39b-*.md` use letter-suffix convention not supported by `governance_helpers._BRANCH_PHASE_RE` + `_PHASE_FILENAME_RE` (digit-only). Version bump performed manually (0.29.0 → 0.30.0). Future sub-phases should use next digit (e.g., phase/41) to remain compatible with automated bump.
