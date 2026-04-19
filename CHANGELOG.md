# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Merkle seal hashes for each release are recorded in `docs/META_LEDGER.md`; this
file is the user-facing narrative.

## [Unreleased]

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
