# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Merkle seal hashes for each release are recorded in `docs/META_LEDGER.md`; this
file is the user-facing narrative.

## [Unreleased]

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
