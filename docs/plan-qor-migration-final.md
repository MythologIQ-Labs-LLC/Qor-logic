# Plan: Qor SSoT Migration & Self-Improvement Loop — FINAL

**Status**: Draft (consolidated; awaiting audit)
**Author**: QoreLogic Governor
**Date**: 2026-04-15
**Supersedes**: `plan-qor-migration.md` (v1, VETO — Ledger #12), `plan-qor-migration-v2.md` (v2, VETO — Ledger #13), `plan-qor-migration-v3.md` (v3, VETO — Ledger #14). **This document is the sole authoritative plan.** v1/v2/v3 retained for ledger chain continuity only; do not implement from them.
**Gate artifact for**: `/qor-audit`, `/qor-implement`

## Open Questions

None.

## 0. Verified Grounding

- Existing pipeline language: **Python 3** (verified: `scripts/compile-claude.py:1` shebang, `scripts/process-skills.py:1`). All new automation in Python.
- No existing hash automation (verified: `grep "sha256\|hash" scripts/*.py` → empty). Migration introduces `qor/scripts/ledger_hash.py`.
- Existing `compiled/` dir empty (verified: `ls compiled/` → empty). Legacy output target; replaced by `qor/dist/`.
- Ledger chain: content_hash = SHA256(artifact bytes); chain_hash = SHA256(content_hash + previous_hash). Verified from Entries #1–#14.
- Last chain hash before migration implementation: Entry #14 = `d048e5b0df5f84140c1034e081ea597e1ea45013897599e751f5265254feb271`.
- Subagent inventory: 25 files in `ingest/subagents/` (verified: `ls ingest/subagents/ | wc -l` → 25).
- No existing `tests/` directory, no `pyproject.toml` / `pytest.ini` / `setup.cfg` (verified: `ls tests/ pyproject.toml pytest.ini setup.cfg` → all "No such file").
- `gh` CLI auth is user-managed; every script consuming it validates `gh auth status` at startup.

## 1. Objectives

1. Single source of truth for Qor skills under `qor/`, with `qor/dist/` as generated variant output.
2. Functional categorization: governance, SDLC, memory, meta. (`mlops/` deferred; not scaffolded until authored.)
3. Variants (claude, kilo-code, codex) are build artifacts — never hand-edited. Drift detectable by CI.
4. Advisory SDLC gate chain: `research → plan → audit → implement → substantiate → validate → remediate?`. Overrides permitted, logged.
5. `/qor-remediate` absorbs `/qor-course-correct` for process-level failures; auto-invoked on Process Shadow Genome threshold breach.
6. Process Shadow Genome: append-only event log; threshold-triggered GitHub issues, aggregated cross-repo.
7. Platform-capability awareness: skills adapt to Claude Code (Agent Teams, Codex plugin) vs Kilo vs future hosts.

## 2. Target Structure

```
qor/
  skills/
    governance/         qor-audit, qor-validate, qor-substantiate, qor-shadow-process
    sdlc/               qor-research, qor-plan, qor-implement, qor-refactor, qor-debug, qor-remediate
    memory/             qor-status, qor-document, qor-organize
    meta/               qor-bootstrap, qor-help, qor-repo-audit, qor-repo-release, qor-repo-scaffold
  agents/
    governance/         qor-governor, qor-judge                                         (2)
    sdlc/               qor-specialist, qor-strategist, qor-fixer, qor-ux-evaluator,
                        project-planner                                                 (5)
    memory/             qor-technical-writer, documentation-scribe, learning-capture    (3)
    meta/               agent-architect, system-architect, build-doctor                 (3)
  platform/
    capabilities.md
    detect.md
    profiles/
      claude-code-solo.md
      claude-code-with-codex.md
      claude-code-teams.md
      kilo-code.md
      codex-standalone.md
  gates/
    chain.md
    schema/
      research.schema.json, plan.schema.json, audit.schema.json, implement.schema.json,
      substantiate.schema.json, validate.schema.json, remediate.schema.json,
      shadow_event.schema.json, adversarial_critique.schema.json
  vendor/
    agents/             accessibility-specialist, code-reviewer, devops-engineer,
                        tauri-launcher, ui-correction-specialist, ultimate-debugger,
                        voice-integration-specialist                                    (7)
    skills/             (third-party skills moved from ingest/skills/)
  scripts/
    compile.py                         ingest qor/skills/** -> qor/dist/variants/**
    check_variant_drift.py             CI guard: regenerate, diff
    check_shadow_threshold.py          sum unaddressed severity; exit 10 on breach
    collect_shadow_genomes.py          cross-repo sweep, pooled threshold
    create_shadow_issue.py             subprocess gh issue create
    ledger_hash.py                     content/chain hashes; manifest generator; verify
    validate_gate_artifact.py          jsonschema validation against qor/gates/schema/
    session.py                         session_id lifecycle (file-marker carrier)
  dist/
    variants/
      claude/                          (compile output)
      kilo-code/                       (compile output)
      codex/                           (stub: only .gitkeep committed)

.qor/                                  (gitignored runtime state)
  gates/<session_id>/<phase>.json      gate artifacts
  current_session                      session_id marker file (file-based carrier)
  override.log                         pre-commit hook bypass audit

.githooks/
  pre-commit                           blocks edits to qor/dist/** unless BUILD_REGEN=1

tests/
  fixtures/
    trivial_task/                      (Phase 8)
    repos/                             (Phase 5)
    skill_samples/                     (Phase 1)
  integration/                         (pytest mark: integration — opt-in)
  test_skill_inventory.py, test_agent_inventory.py, test_ledger_hash.py,
  test_ledger_path_rebase.py, test_compile.py, test_gates.py, test_shadow.py,
  test_collect.py, test_platform.py, test_cleanup.py, test_end_to_end.py
  integration/test_platform_live.py

pyproject.toml                         [project.dependencies] = ["jsonschema>=4"],
                                       [project.optional-dependencies.dev] = ["pytest>=8"],
                                       [tool.pytest.ini_options] = markers + testpaths

docs/
  META_LEDGER.md                       (existing; appended during migration)
  SYSTEM_STATE.md                      (rewritten Phase 7)
  SKILL_REGISTRY.md                    (rewritten Phase 7)
  PROCESS_SHADOW_GENOME.md             (Phase 4; JSONL append-only)
  SHADOW_GENOME.md                     (existing VETO records)
  migration-manifest-pre.json          (Phase 1.5 artifact)
  migration-manifest-post.json         (Phase 1.5 artifact)
  qor-config-schema.md                 (Phase 5)
  hooks-install.md                     (Phase 2)
  archive/2026-04-15/                  (Phase 0 snapshots)

.gitignore                             adds .qor/, __pycache__/, .pytest_cache/
```

**Not in structure (explicit deletions or non-reintroductions)**:
- Top-level `build/` (consolidated into `qor/scripts/`)
- `qor/prompts/` (no content to migrate; re-add when authored)
- `qor/skills/mlops/` (deferred)
- `kilo-code/` top-level (all migrated)
- `deployable state/` (replaced by `qor/dist/`)
- `processed/`, `compiled/` (empty; deleted)
- `ingest/skills/ql-*.md` × 10 (superseded by canonical in `kilo-code/` — `ingest` copies are older)
- `ingest/subagents/hearthlink-*.md` × 5 (project retired)
- `ingest/` root itself (fully dispositioned per §2.B; empty shell deleted in Phase 7)

## 2.B Disposition of `ingest/` subdirectories (V-5 resolution)

Verified (`ls ingest/`): 11 subdirectories. Disposition mirrors the subagent approach — categorize, migrate, never silently retain.

| Source | Destination | Action |
|---|---|---|
| `ingest/docs/` (2 files: `MERKLE_ITERATION_GUIDE.md`, `SHIELD_SELF_AUDIT.md`) | `docs/` | merge (qor-scoped internal docs) |
| `ingest/experimental/` (5 files: tauri2-*, tauri-ipc-wiring, tauri-launcher, build-doctor) | `qor/experimental/` | retain as non-canonical research material; NOT part of SSoT pipeline |
| `ingest/internal/` (subdirs: agents, governance, references, scripts, utilities) | per-subdir: `agents/` → merge into `qor/agents/`; `governance/` → merge into `qor/skills/governance/`; `references/` → per-skill `references/` folders; `scripts/` → `qor/scripts/`; `utilities/` → `qor/scripts/utilities/` | migrate (qor-scoped) |
| `ingest/lessons-learned/` (3 files) | `docs/Lessons-Learned/` | merge (existing dir) |
| `ingest/references/` (ql-*-patterns, github-api-helpers, tauri2-*-links) | per-skill `references/` folders in `qor/skills/<category>/<skill>/references/` (ql-*) and `qor/vendor/skills/tauri/references/` (tauri2-*) | migrate |
| `ingest/scripts/` (subdirs: composition-patterns, react-best-practices, rust-skills, etc. + `calculate-session-seal.py`) | `calculate-session-seal.py` → `qor/scripts/`; framework subdirs (react-*, rust-skills, composition-patterns, playwright-*, security-permission-audit, frontend-bridge-integration, marketplace-plugin-ops) → `qor/vendor/skills/<name>/` | split per-item |
| `ingest/templates/` (6 doc templates: ARCHITECTURE_PLAN, CLAUDE.md.tpl, CONCEPT, META_LEDGER, SHADOW_GENOME, SYSTEM_STATE) | `qor/templates/` | migrate |
| `ingest/third-party/` (subdirs: agents) | merge into `qor/vendor/agents/` | migrate |
| `ingest/workflows/` (ql-* legacy alt copies: audit, bootstrap, governor, judge, organize, plan, etc.) | **DELETE** (superseded by canonical in `kilo-code/qor-*`; these are older variant forks) | delete |
| `ingest/skills/` | See §3.B — extensive | — |
| `ingest/subagents/` | Already dispositioned per §3 | — |

Post-migration: `ingest/` directory is empty and removed in Phase 7.

## 3.B `ingest/skills/` → destination rules (V-3 resolution)

Verified (`ls ingest/skills/ | wc -l`): **90 items**. Rules applied in order (first match wins):

| Rule | Pattern | Destination | Rationale |
|---|---|---|---|
| R-1 | `ingest/skills/ql-*.md` (10 files) | **DELETE** | Older variants superseded by `kilo-code/qor-*` canonical sources |
| R-2 | `ingest/skills/qore-*` (qore-docs-technical-writing, qore-governance-compliance, qore-meta-log-decision, qore-meta-track-shadow, qore-tauri2-*, qore-web-chrome-devtools-audit) | `qor/skills/<category>/<name>/` (inspect each: governance-* → governance/; meta-* → meta/; tauri2-* → vendor/skills/tauri/; docs-* → memory/; web-chrome-devtools → vendor/skills/chrome-devtools/) | qor-scoped, promote |
| R-3 | `ingest/skills/log-decision.md`, `track-shadow-genome.md` | `qor/skills/memory/` | memory operations, qor-scoped |
| R-4 | `ingest/skills/_quarantine/` | **DELETE** | Previously quarantined; retirement upheld |
| R-5 | `ingest/skills/agents/` | merge into `qor/agents/` if qor-scoped content; else `qor/vendor/agents/` (inspection step, 1:1 file check at Phase 1 execution) | consolidation |
| R-6 | `ingest/skills/custom/` | `qor/skills/custom/` if qor-scoped; else `qor/vendor/skills/custom/` (inspection at Phase 1) | internal custom work preserved |
| R-7 | Third-party framework skills (aspnet-core, chatgpt-apps, cloudflare-deploy, composition-patterns, develop-web-game, doc, figma*, frontend-bridge-integration, gh-*, imagegen, jupyter-notebook, linear, marketplace-plugin-ops, music, netlify-deploy, notion-*, openai-docs, pdf, playwright*, react-*, render-deploy, rust-skills, screenshot, security-*, sentry, setup-api-key, skill-lifecycle-ops, slides, sora, sound-effects, speech*, spreadsheet, tauri2-*, tauri-ipc-wiring, technical-writing-narrative, text-to-speech, transcribe, vercel-deploy, wcag-audit-patterns, web-design-guidelines, winui-app, yeet) | `qor/vendor/skills/<name>/` | third-party, preserved as vendor |

Phase 1 executor iterates `ingest/skills/` in alphabetical order, applies rules R-1..R-7, logs destination per file, aborts on ambiguous item (no rule match). Added unit test:
- `tests/test_skill_inventory.py::test_ingest_skills_exhaustive_mapping` — every one of 90 items classified by R-1..R-7; no unclassified remainder
- `tests/test_skill_inventory.py::test_deletion_count_matches` — R-1 deletes exactly 10 `ql-*.md`; R-4 deletes `_quarantine/`

## 3. Agent Mapping Table (25 files → dispositions)

| Source | Destination | Rename |
|---|---|---|
| `ql-governor.md` | `qor/agents/governance/qor-governor.md` | ql→qor |
| `ql-judge.md` | `qor/agents/governance/qor-judge.md` | ql→qor |
| `ql-specialist.md` | `qor/agents/sdlc/qor-specialist.md` | ql→qor |
| `ql-strategist.md` | `qor/agents/sdlc/qor-strategist.md` | ql→qor |
| `ql-fixer.md` | `qor/agents/sdlc/qor-fixer.md` | ql→qor |
| `ql-ux-evaluator.md` | `qor/agents/sdlc/qor-ux-evaluator.md` | ql→qor |
| `project-planner.md` | `qor/agents/sdlc/project-planner.md` | — |
| `ql-technical-writer.md` | `qor/agents/memory/qor-technical-writer.md` | ql→qor |
| `documentation-scribe.md` | `qor/agents/memory/documentation-scribe.md` | — |
| `learning-capture.md` | `qor/agents/memory/learning-capture.md` | — |
| `agent-architect.md` | `qor/agents/meta/agent-architect.md` | — |
| `system-architect.md` | `qor/agents/meta/system-architect.md` | — |
| `build-doctor.md` | `qor/agents/meta/build-doctor.md` | — |
| `accessibility-specialist.md` | `qor/vendor/agents/accessibility-specialist.md` | — |
| `code-reviewer.md` | `qor/vendor/agents/code-reviewer.md` | — |
| `devops-engineer.md` | `qor/vendor/agents/devops-engineer.md` | — |
| `tauri-launcher.md` | `qor/vendor/agents/tauri-launcher.md` | — |
| `ui-correction-specialist.md` | `qor/vendor/agents/ui-correction-specialist.md` | — |
| `ultimate-debugger.md` | `qor/vendor/agents/ultimate-debugger.md` | — |
| `voice-integration-specialist.md` | `qor/vendor/agents/voice-integration-specialist.md` | — |
| `hearthlink-backend-dev.md` | **DELETE** | — |
| `hearthlink-frontend-dev.md` | **DELETE** | — |
| `hearthlink-skill-framework.md` | **DELETE** | — |
| `hearthlink-skill-template.md` | **DELETE** | — |
| `hearthlink-ui-ux-designer.md` | **DELETE** | — |

Totals: 13 → `qor/agents/` (2 governance, 5 sdlc, 3 memory, 3 meta); 7 → `qor/vendor/agents/`; 5 deleted. Sum 25.

## 4. Phases

### Phase 0 — Freeze, snapshot, infrastructure

**Affected files**:
- `pyproject.toml` (new)
- `.gitignore` (append)
- `tests/.gitkeep`, `tests/fixtures/.gitkeep`, `tests/integration/.gitkeep` (new)
- `docs/archive/2026-04-15/**` (new, populated via copy)

**Changes**:
- Git tag `pre-qor-migration` on current HEAD.
- Copy `ingest/`, `processed/`, `deployable state/`, `kilo-code/`, `compiled/` into `docs/archive/2026-04-15/`.
- Author `pyproject.toml`:
  ```toml
  [build-system]
  requires = ["setuptools>=68"]
  build-backend = "setuptools.build_meta"

  [project]
  name = "qorelogic"
  version = "0.1.0"
  requires-python = ">=3.11"
  dependencies = ["jsonschema>=4"]

  [project.optional-dependencies]
  dev = ["pytest>=8"]

  [tool.pytest.ini_options]
  testpaths = ["tests"]
  markers = ["integration: live environment probes; opt-in via -m integration"]
  ```
- Append to `.gitignore`: `.qor/`, `__pycache__/`, `.pytest_cache/`.
- Commit: `chore(qor): pre-migration snapshot + test infrastructure`.

**Unit tests** (TDD — file creation before any other phase):
- `tests/test_cleanup.py::test_pyproject_valid_toml` — parses as TOML; required keys present
- `tests/test_cleanup.py::test_gitignore_covers_qor_runtime` — `.qor/` matched

**CI validation**: `python -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"`; `git tag --list pre-qor-migration` non-empty.

---

### Phase 1 — Author SSoT (skills, agents, vendor, fixtures)

**Affected files**:
- `qor/skills/<category>/qor-<name>/SKILL.md` × all canonical skills (moved from `kilo-code/qor-*`)
- `qor/agents/<category>/<name>.md` × 13 (per §3 mapping)
- `qor/vendor/agents/<name>.md` × 7 (per §3 mapping)
- `qor/vendor/skills/**` (moved from `ingest/skills/` — third-party only)
- `qor/skills/sdlc/qor-remediate/SKILL.md` (new; absorbs `qor-course-correct`)
- `qor/skills/governance/qor-shadow-process/SKILL.md` (new)
- `qor/skills/governance/qor-audit/references/adversarial-mode.md` (new)
- `tests/fixtures/skill_samples/` (new — authored in this phase; seeded with 2 canonical skill .md fixtures + 1 intentionally malformed fixture for validation tests)
- `kilo-code/qor-course-correct/` (deleted)
- `ingest/subagents/hearthlink-*.md` × 5 (deleted per §3)

**Changes**:
- Canonical source: `kilo-code/qor-*/SKILL.md` (most recent per Ledger #10).
- Each Qor skill's frontmatter gains `requires:` and `enhances_with:` keys (populated in Phase 6, stubbed here).
- `qor-remediate` declares auto-trigger contract: reads `docs/PROCESS_SHADOW_GENOME.md`, pattern-matches aged/high-severity events, emits remediation proposal.
- `tests/fixtures/skill_samples/` contents:
  - `valid_minimal.md` — minimal SHIELD-compliant skill for positive compile tests
  - `valid_full.md` — full-featured canonical skill for integration fixtures
  - `invalid_missing_frontmatter.md` — malformed; used by `test_compile.py::test_rejects_malformed`

**Unit tests** (authored first):
- `tests/test_skill_inventory.py::test_every_kilo_skill_has_canonical_home`
- `tests/test_skill_inventory.py::test_no_duplicate_skills_across_variants`
- `tests/test_skill_inventory.py::test_retired_skills_absent` (`qor-course-correct`)
- `tests/test_agent_inventory.py::test_mapping_is_exhaustive` (every `ingest/subagents/*.md` has disposition)
- `tests/test_agent_inventory.py::test_no_hearthlink_survives`
- `tests/test_agent_inventory.py::test_vendor_agents_count` (7)

**CI validation**: `python -m pytest tests/test_skill_inventory.py tests/test_agent_inventory.py`.

---

### Phase 1.5 — Ledger continuation

**Affected files**:
- `qor/scripts/ledger_hash.py` (new)
- `docs/migration-manifest-pre.json` (new — written by `ledger_hash.py write_manifest`)
- `docs/migration-manifest-post.json` (new — written post-move by same function)
- `docs/META_LEDGER.md` (append Entries #15 MIGRATION-SEAL, #16 MIGRATION-COMPLETE)

**Changes**:
- `ledger_hash.py` exposes:
  - `content_hash(path: Path) -> str` — SHA256 of file bytes
  - `chain_hash(content_hash: str, previous_hash: str) -> str`
  - `write_manifest(root: Path, include_globs: list[str], output: Path) -> dict` — walks `root`, collects files matching globs, emits `{schema_version: "1", generated_ts: ISO-8601, paths: [{path, sha256}, ...]}` sorted by path. Returns parsed dict for caller.
  - `emit_entry(kind: str, content_subject: Path, prev_hash: str, metadata: dict) -> dict` — structured ledger entry (content_hash is of `content_subject` file)
  - `verify(ledger_path: Path) -> None` — reads all entries sequentially, recomputes chain hashes, raises on mismatch
- **Execution order**:
  1. **Before** Phase 1 file moves: run `write_manifest(repo_root, ["kilo-code/qor-*", "ingest/subagents/*.md", "ingest/skills/**"], "docs/migration-manifest-pre.json")`; emit Entry #15 with `content_subject=docs/migration-manifest-pre.json`, `previous_hash=d048e5b0...` (Entry #14).
  2. Execute Phase 1 moves.
  3. **After** moves: run `write_manifest(repo_root, ["qor/skills/**", "qor/agents/**", "qor/vendor/**"], "docs/migration-manifest-post.json")`; emit Entry #16 chained from #15.
- **Path rebase map**: derived by `ledger_hash.py rebase_map(pre, post)` — zips entries by `sha256` equality; emits `{old_path: new_path}` dict; files with content_modified (sha256 mismatch between pre/post) fail hard and abort Phase 1.5 (migration must preserve content).
- Historical entries #1–#14 are **frozen as historical**; ledger gains a "Path Rebasing" section citing the rebase map. Chain verification at old paths uses the rebase map for lookup.

**Unit tests**:
- `tests/test_ledger_hash.py::test_content_hash_deterministic`
- `tests/test_ledger_hash.py::test_chain_hash_matches_entry_10` — verifies computation against known-good hash `1877524d...` from historical entry
- `tests/test_ledger_hash.py::test_write_manifest_sorted_by_path`
- `tests/test_ledger_hash.py::test_manifest_hash_reproducible`
- `tests/test_ledger_hash.py::test_rebase_map_zips_by_sha`
- `tests/test_ledger_hash.py::test_rebase_map_aborts_on_content_change`
- `tests/test_ledger_path_rebase.py::test_historical_entry_verifiable_via_rebase_map` — picks Entry #5 (or any entry referencing a migrated path), looks up via rebase map, recomputes content_hash at new path, asserts match with Entry #5's stored hash

**CI validation**: `python -m pytest tests/test_ledger_hash.py tests/test_ledger_path_rebase.py`; `python qor/scripts/ledger_hash.py --verify docs/META_LEDGER.md` returns exit 0.

---

### Phase 2 — Build pipeline & hooks

**Affected files**:
- `qor/scripts/compile.py` (new)
- `qor/scripts/check_variant_drift.py` (new)
- `.githooks/pre-commit` (new)
- `docs/hooks-install.md` (new)
- `qor/dist/variants/claude/{skills,agents}/` (created, populated)
- `qor/dist/variants/kilo-code/{skills,agents}/` (created, populated)
- `qor/dist/variants/codex/.gitkeep` (new — committed; `compile.py` writes idempotently)

**Changes**:
- `compile.py` — Python 3.11 stdlib only (`pathlib`, `re`, `hashlib`, `json`, `shutil`):
  - Input: `qor/skills/**/SKILL.md`, `qor/agents/**/*.md`
  - `TARGETS = {"claude": emit_claude, "kilo-code": emit_kilocode, "codex": emit_codex}`
  - `emit_codex(src, dst_root) -> None: (dst_root / ".gitkeep").touch()` — idempotent stub
- `check_variant_drift.py`:
  - Compiles into a `tempfile.TemporaryDirectory()`.
  - `filecmp.dircmp` against `qor/dist/`; exits non-zero on diff, printing diff report.
- `.githooks/pre-commit` (bash, per `git config core.hooksPath .githooks`):
  ```bash
  #!/usr/bin/env bash
  set -e
  STAGED=$(git diff --cached --name-only)
  if echo "$STAGED" | grep -q '^qor/dist/'; then
    if [ "$BUILD_REGEN" != "1" ]; then
      echo "ERROR: qor/dist/ is generated. Rebuild via 'BUILD_REGEN=1 python qor/scripts/compile.py' then commit."
      exit 1
    fi
    printf '%s\t%s\t%s\n' "$(date -Is)" "$USER" "$(echo "$STAGED" | tr '\n' ',')" >> .qor/override.log
  fi
  ```
- `docs/hooks-install.md`: documents `git config core.hooksPath .githooks` one-time setup.

**Unit tests**:
- `tests/test_compile.py::test_compile_claude_variant_format` — output matches fixture
- `tests/test_compile.py::test_compile_kilocode_variant_format`
- `tests/test_compile.py::test_codex_stub_writes_gitkeep` — only `.gitkeep` emitted
- `tests/test_compile.py::test_drift_detector_flags_manual_edit`
- `tests/test_compile.py::test_hook_bypass_logs_override` — sets `BUILD_REGEN=1`, simulates staged change, asserts `.qor/override.log` appended
- `tests/test_compile.py::test_rejects_malformed` — uses `invalid_missing_frontmatter.md` fixture

**CI validation**: `python qor/scripts/check_variant_drift.py` exit 0; `python -m pytest tests/test_compile.py`.

---

### Phase 3 — Gate chain & session management

**Affected files**:
- `qor/gates/chain.md` (new — defines phase order and transitions)
- `qor/gates/schema/*.schema.json` × 9 (new)
- `qor/scripts/validate_gate_artifact.py` (new — uses `jsonschema`)
- `qor/scripts/session.py` (new — file-marker session carrier)
- Every skill under `qor/skills/` — frontmatter `gate_reads:` / `gate_writes:` populated

**Changes**:
- Gate chain: `research → plan → audit → implement → substantiate → validate → (remediate?)`.
- Gate artifacts: `.qor/gates/<session_id>/<phase>.json` conforming to matching schema.
- **Session ID carrier (file-marker)**:
  - Format: `<UTC_ISO_MIN>-<6hex>` where `6hex = secrets.token_hex(3)`.
  - `session.py` exposes:
    - `get_or_create() -> str` — reads `.qor/current_session`; if absent or older than 24h (mtime), generates new ID, writes file atomically via `tempfile.NamedTemporaryFile` + `os.replace()` (Windows-safe atomic primitive — `os.rename()` raises `FileExistsError` on Windows when target exists), returns. All atomic-write sites in `qor/scripts/` (including `ledger_hash.py` manifest output) use `os.replace()` uniformly.
    - `end_session() -> None` — removes `.qor/current_session`.
  - Every Qor skill calls `get_or_create()` at startup — this is the authoritative carrier. No env var dependency.
- **Gate enforcement (advisory)**: on skill startup, resolve session_id, check `.qor/gates/<session_id>/<prior_phase>.json` exists and validates against schema. Missing/invalid → print advisory, prompt user to confirm override. Override emits shadow event (severity 1, `gate_override`).
- **Codex adversarial mode** (audit phase):
  - Input schema (`audit.schema.json`): `{plan_path, plan_content_hash, codebase_snapshot_refs[], session_id}`
  - Critique schema (`adversarial_critique.schema.json`): `{critiques: [{severity, claim_challenged, counter_evidence, recommended_gap}], confidence}`
  - Invocation binding authored in `qor/platform/profiles/claude-code-with-codex.md` (Phase 6); absent capability → solo audit + shadow event (severity 2, `capability_shortfall`).

**Unit tests**:
- `tests/test_gates.py::test_missing_prior_artifact_triggers_advisory`
- `tests/test_gates.py::test_override_emits_shadow_event`
- `tests/test_gates.py::test_schema_validates_well_formed_artifact`
- `tests/test_gates.py::test_schema_rejects_malformed_artifact`
- `tests/test_gates.py::test_adversarial_input_schema_well_formed`
- `tests/test_gates.py::test_session_id_collision_probability` — 10k IDs in same minute, zero collisions
- `tests/test_gates.py::test_session_marker_roundtrip` — `get_or_create` twice returns same ID within 24h
- `tests/test_gates.py::test_session_marker_regenerates_after_24h` — mocked mtime

**CI validation**: `python -m pytest tests/test_gates.py`; `python qor/scripts/validate_gate_artifact.py --all`.

---

### Phase 4 — Process Shadow Genome

**Affected files**:
- `docs/PROCESS_SHADOW_GENOME.md` (new — JSONL, append-only)
- `qor/scripts/check_shadow_threshold.py` (new)
- `qor/scripts/create_shadow_issue.py` (new)
- `qor/gates/schema/shadow_event.schema.json` (authored Phase 3; referenced here)

**Changes**:
- Event schema:
  ```json
  {
    "ts": "ISO-8601 UTC",
    "skill": "qor-<name>",
    "session_id": "<UTC-ISO-MIN>-<6hex>",
    "event_type": "gate_override | regression | hallucination | degradation | capability_shortfall | aged_high_severity_unremediated",
    "severity": 1,
    "details": {},
    "addressed": false,
    "issue_url": null,
    "addressed_ts": null,
    "addressed_reason": null,
    "source_entry_id": null
  }
  ```
  - Each event gets stable `id` = SHA256 of first 7 fields; `source_entry_id` references another event's `id` (used by aged escalation).
- **Severity rubric**: override=1, capability_shortfall=2, regression=3, hallucination=4, degradation=5.
- **Threshold** = 10 unaddressed severity points.
- **`addressed` state machine** (strictly forward):
  - `false → true (issue_created)` — any severity; threshold trips → `create_shadow_issue.py` atomically flips matched entries
  - `false → true (resolved_without_issue)` — any severity; operator action via `qor-remediate`
  - `false → true (stale_expired)` — **severity 1–2 only**; 90 days unaddressed
  - **Severity ≥ 3 never stale-expires**
  - Reverse transitions forbidden; re-opening requires a new event
- **Aged high-severity self-escalation** with idempotence:
  - Collector sweep: for each event with `severity ≥ 3`, `addressed == false`, age ≥ 90 days:
    - If any event exists with `event_type == "aged_high_severity_unremediated"` AND `source_entry_id == this_event.id` (regardless of `addressed` state of that escalation): **skip** (idempotence — at-most-one escalation per source).
    - Else emit: `{event_type: "aged_high_severity_unremediated", severity: 5, source_entry_id: this_event.id, details: {aged_entry_id, aged_skill, age_days}}`
- **Auto-trigger `/qor-remediate`**: every Qor skill post-run invokes `check_shadow_threshold.py`; exit code 10 triggers `/qor-remediate` (prompt to user in Claude Code, interactive).

**Unit tests**:
- `tests/test_shadow.py::test_threshold_sum_ignores_addressed`
- `tests/test_shadow.py::test_issue_creation_flips_addressed`
- `tests/test_shadow.py::test_severity_gated_stale_expiry` — sev 1–2 expire; sev 3–5 do not
- `tests/test_shadow.py::test_aged_high_severity_self_escalates`
- `tests/test_shadow.py::test_aged_escalation_is_idempotent` — second sweep produces no new escalation for same source
- `tests/test_shadow.py::test_event_schema_validation`
- `tests/test_shadow.py::test_auto_trigger_exit_code`
- `tests/test_shadow.py::test_severity_rubric_threshold_calibration`

**CI validation**: `python -m pytest tests/test_shadow.py`.

---

### Phase 5 — Cross-repo batch collector

**Affected files**:
- `qor/scripts/collect_shadow_genomes.py` (new)
- `docs/qor-config-schema.md` (new)
- `tests/fixtures/repos/` (new — seeded with 2 synthetic repo fixtures)

**Changes**:
- Config (`~/.qor/repos.json`, not committed):
  ```json
  {
    "version": "1",
    "meta_repo": "MythologIQ/Qorelogic",
    "repos": [
      {"path": "G:/MythologIQ/Qorelogic", "name": "qorelogic", "enabled": true}
    ],
    "threshold": 10,
    "stale_days": 90
  }
  ```
- `collect_shadow_genomes.py`:
  - Reads `$QOR_CONFIG` or `~/.qor/repos.json`.
  - For each enabled repo: load `docs/PROCESS_SHADOW_GENOME.md` (JSONL), filter `addressed=false`, tag with `source_repo`.
  - Runs aged-high-severity self-escalation pass (see Phase 4) per-repo, writing new events back to each repo's log.
  - Pools remaining unaddressed entries globally; applies threshold.
  - If tripped: aggregates into single issue body; invokes `create_shadow_issue.py --consolidated --repo MythologIQ/Qorelogic`; flips matched entries in every source repo atomically.
  - Missing repo path: logs warning, continues.
- Scheduling documented in `qor-config-schema.md` (Windows Task Scheduler XML + cron one-liner); not configured by plan.

**Unit tests**:
- `tests/test_collect.py::test_config_schema_validation`
- `tests/test_collect.py::test_multi_repo_aggregation`
- `tests/test_collect.py::test_threshold_trips_globally_not_per_repo`
- `tests/test_collect.py::test_missing_repo_path_logged_not_fatal`
- `tests/test_collect.py::test_aged_escalation_applied_per_repo_before_pool`

**CI validation**: `python -m pytest tests/test_collect.py`.

---

### Phase 6 — Platform awareness

**Affected files**:
- `qor/platform/capabilities.md` (new)
- `qor/platform/detect.md` (new)
- `qor/platform/profiles/*.md` × 5 (new)
- Every skill under `qor/skills/` — frontmatter `requires:` / `enhances_with:` populated

**Changes**:
- `capabilities.md` catalogs: Claude Code Agent Teams, Skills, subagents, hooks, MCP, Codex-plugin, Kilo Code host.
- `detect.md` probes:
  - Codex plugin: probe active tool list for `codex` / `mcp__codex*` signatures
  - Agent Teams: probe for `TeamCreate` deferred tool
  - Host: `CLAUDE_PROJECT_DIR` env var vs Kilo-specific markers
- **Marker format** (conversation-scoped sentinel): `QOR_PLATFORM_PROFILE: <profile_id>|<capabilities_csv>|<iso_ts>`. Written into conversation context on first Qor skill invocation per session.
- **Tolerance rule** (concrete):
  - Re-detect if marker absent
  - Re-detect if marker `iso_ts` < session_start_ts (from `.qor/current_session` mtime)
  - Re-detect if marker's capabilities list is missing any capability the current skill's `enhances_with` references
- `claude-code-with-codex.md` pins the Codex invocation binding for adversarial audit (tool name + prompt contract + return format), resolved once detection identifies the production Codex plugin signature.

**Unit tests**:
- `tests/test_platform.py::test_marker_format_parseable`
- `tests/test_platform.py::test_redetect_when_marker_absent`
- `tests/test_platform.py::test_redetect_when_marker_stale`
- `tests/test_platform.py::test_redetect_when_capability_missing`
- `tests/test_platform.py::test_codex_probe_identifies_plugin` (mocked tool list)
- `tests/test_platform.py::test_profile_covers_all_capabilities`
- `tests/integration/test_platform_live.py::test_detect_against_live_session` — `@pytest.mark.integration`; opt-in via `pytest -m integration`; exercises detection against current session env

**CI validation**: `python -m pytest tests/test_platform.py`; integration optional.

---

### Phase 7 — Rewire references & cleanup

**Affected files**:
- `docs/SYSTEM_STATE.md` (rewrite)
- `docs/SKILL_REGISTRY.md` (rewrite)
- `docs/META_LEDGER.md` (append Entry #17 CUTOVER)
- `README.md` (update structure diagram)
- `processed/` (deleted)
- `compiled/` (deleted)
- `ingest/skills/ql-*.md` × 10 (deleted per §3.B R-1 — verified location)
- `ingest/skills/_quarantine/` (deleted per §3.B R-4)
- `ingest/workflows/` (deleted per §2.B — legacy ql-* alternates superseded)
- `ingest/` root (empty after all §2.B + §3.B migrations; removed)
- `kilo-code/` top-level (deleted — all migrated)
- `deployable state/` (deleted — replaced by `qor/dist/`)
- `ingest/subagents/hearthlink-*.md` × 5 (deleted in Phase 1; verify here)

**Changes**:
- Sweep `docs/` for old path references; replace with new `qor/` paths.
- Entry #17 chains from #16; content_hash = hash of a cutover-manifest enumerating deleted dirs + new SSoT root.

**Unit tests**:
- `tests/test_cleanup.py::test_no_old_paths_in_docs`
- `tests/test_cleanup.py::test_legacy_dirs_absent`
- `tests/test_cleanup.py::test_ledger_entry_17_chain_valid`

**CI validation**:
```bash
python -m pytest tests/test_cleanup.py
! grep -r "kilo-code/qor-\|deployable state\|processed/\|compiled/\|ingest/" docs/ --exclude-dir=archive
! grep -rn "hearthlink" qor/
```

(Note: `!` prefix inverts exit code — command fails if grep finds matches. All tokens unanchored so inline markdown references like `` `processed/` directory `` are detected.)

---

### Phase 8 — Validation (end-to-end)

**Affected files**:
- `tests/test_end_to_end.py` (new)
- `tests/fixtures/trivial_task/` (new)

**Changes**:
- Orchestrates every migrated skill against trivial-task fixture.
- Asserts:
  - Gate chain prints advisory on out-of-order invocation
  - Override emits shadow-process event AND appends `.qor/override.log`
  - `check_variant_drift.py` catches manual edit to `qor/dist/`
  - `BUILD_REGEN=1` bypass path logs to `.qor/override.log`
  - `collect_shadow_genomes.py` opens issue at threshold (mocked `gh`)
  - Platform marker set once; subsequent skills reuse
  - `ledger_hash.py --verify` passes from Entry #1 through #17
  - Gate schema rejects malformed JSON
  - Severity rubric trips threshold at exactly the right count
  - Aged-escalation idempotence: two sweeps over same state produce identical event log

**CI validation**: `python -m pytest tests/` (all suites green); `python -m pytest tests/ -m integration` (opt-in).

## 5. Dependencies

| Package | Classification | Justification |
|---|---|---|
| Python 3.11+ stdlib | Runtime | All scripts; `secrets`, `hashlib`, `pathlib`, `json`, `subprocess`, `tomllib` |
| `jsonschema>=4` | Runtime | Gate artifact validation; 7 schema types with `$ref` and `format` — ~300 lines vanilla otherwise |
| `pytest>=8` | Dev | Test runner; standard |
| `gh` CLI | Runtime system | Issue creation; auth user-managed; validated per-invocation |

No Node, no npm, no `package.json`.

## 6. Remediation Traceability

v1 → v2 → v3 → final. All audit items resolved:

**v1 (33 violations)**: orphans, ghost handlers, chain integrity, dep specs, macro SSoT — all resolved by v2 base.

**v2 (12 violations)**:
- jsonschema classification → §5 (runtime)
- subagent mapping → §3
- `tests/` + pyproject → §2 structure, Phase 0
- codex `.gitkeep` → Phase 2
- Entry #13/#14 subject → Phase 1.5 manifest files
- severity-blind expiry → Phase 4 (sev 1–2 only)
- session_id collision → Phase 3 `<UTC-ISO-MIN>-<6hex>`
- path-rebase test → Phase 1.5
- severity-gated expiry test → Phase 4
- live platform probe → Phase 6 (integration-marked)

**v3 (6 violations)**:
- Manifest generator unnamed → Phase 1.5 (`ledger_hash.py write_manifest`)
- Plan SoT split → this consolidated document
- `skill_samples/` Phase 1 → Phase 1 explicitly authors fixtures
- Escalation idempotence → Phase 4 at-most-one-per-source rule
- Session carrier ambiguous → Phase 3 file-based `.qor/current_session`
- Broken CI grep → Phase 7 uses `!` prefix

**final v1 (5 violations)**:
- Grep anchor misuse (`^processed/` etc.) → Phase 7 + §9 unanchored tokens
- Wrong path `ingest/ql-*.md` → `ingest/skills/ql-*.md` corrected in §2 "Not in structure" and Phase 7
- `ingest/skills/` mapping → §3.B rules R-1..R-7 with exhaustive-mapping test
- `os.rename` portability → §Phase 3 mandates `os.replace()` uniformly for all atomic writes
- `ingest/` 9-subdir blind spot → §2.B disposition table (all 11 subdirs covered; `ingest/` empty post-migration)

## 7. Risks

- **Ledger chain ambiguity across migration** — Mitigation: Phase 1.5 manifest-based Entries #15/#16 + rebase map; `ledger_hash.py --verify` validates full chain including historical.
- **Hook bypass abuse** — Mitigation: `BUILD_REGEN=1` appends to `.qor/override.log`; CI drift check is authoritative regardless of hook state.
- **Codex-plugin signature drift** — Mitigation: binding lives in single file (`claude-code-with-codex.md`); detection re-runs when capability list missing.
- **Cross-repo collector hits missing repos** — Mitigation: missing path logs warning, non-fatal; tested.
- **Auto-trigger `/qor-remediate` storms** — Mitigation: matched entries flip to `addressed=true` atomically; aged-escalation idempotent at-most-one-per-source.
- **Session file stale across long-running sessions** — Mitigation: 24h regeneration; deterministic via mtime check.
- **Platform marker dropped by context compression** — Mitigation: absence triggers re-detect (cheap); file-based session carrier unaffected.

## 8. Success Criteria

- [ ] Single canonical skill/agent source under `qor/`
- [ ] Zero orphan artifacts in `qor/` (every file has a creating phase)
- [ ] `qor/dist/` is sole variant output location; drift detector enforces
- [ ] Ledger chain verifiable from Entry #1 through #17 via `ledger_hash.py --verify`
- [ ] `qor-shadow-process` in `governance/`; `qor-remediate` replaces `qor-course-correct`
- [ ] All 25 subagents resolved per §3 mapping
- [ ] `tests/` declared, populated; `pyproject.toml` committed with correct markers
- [ ] `qor/dist/variants/codex/.gitkeep` present and committed
- [ ] Entries #15, #16, #17 appended with valid chain hashes
- [ ] Severity-gated stale expiry + self-escalation idempotence verified by tests
- [ ] Session IDs collision-resistant (10k concurrent-same-minute test passes)
- [ ] File-marker session carrier roundtrip tested
- [ ] All 8 phases' unit tests green; end-to-end Phase 8 green

## 9. CI Commands

```bash
# From repo root, post-implementation
python -m pytest tests/ -v                                     # all unit tests
python -m pytest tests/ -m integration                         # live probes (opt-in)
python qor/scripts/check_variant_drift.py                      # exit 0 on clean
python qor/scripts/ledger_hash.py --verify docs/META_LEDGER.md # chain verification
! grep -r "kilo-code/qor-\|deployable state\|processed/\|compiled/\|ingest/" docs/ --exclude-dir=archive
! grep -rn "hearthlink" qor/
python -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"  # pyproject valid
[ ! -d ingest/ ] && [ ! -d kilo-code/ ] && [ ! -d 'deployable state/' ]  # legacy roots gone
```

All commands must exit 0 for CI to pass.
