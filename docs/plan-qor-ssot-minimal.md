# Plan: Qor SSoT Migration — MINIMAL

**Status**: Active (override-accepted; advisory gate VETO carried as sev-1 in PROCESS_SHADOW_GENOME)
**Author**: Qor-logic Governor
**Date**: 2026-04-15
**Supersedes**: All prior `plan-qor-migration*.md` iterations (retained in `docs/` for ledger continuity; do not implement from them)
**Scope**: Phases 0, 1, 1.5, 7 only. Tooling phases (2, 3, 4, 5, 6, 8) deferred to `plan-qor-tooling-deferred.md`.

## Why minimal

Five audit rounds compressed violations from 33 → 12 → 6 → 5 → 5. The floor of 5 is amendment-drift against a prose plan that has grown past efficient-review surface area. Debug analysis (this conversation) concluded: implement the irreducible SSoT move; defer tooling to a separate, smaller plan surface.

## Objective

Collapse four parallel skill surfaces into a single source of truth under `qor/`, with ledger chain continuity, and delete the old surfaces. Nothing else.

## Target Structure (this plan's full scope)

```
qor/
  skills/
    governance/   qor-audit, qor-validate, qor-substantiate
    sdlc/         qor-research, qor-plan, qor-implement, qor-refactor, qor-debug,
                  qor-remediate (new — absorbs qor-course-correct)
    memory/       qor-status, qor-document, qor-organize,
                  (+ log-decision, track-shadow-genome migrated from ingest/skills/)
    meta/         qor-bootstrap, qor-help, qor-repo-audit, qor-repo-release,
                  qor-repo-scaffold
    governance/qor-shadow-process (new — minimal stub, full impl deferred)
    custom/       (if any qor-scoped content identified under ingest/skills/custom/)
  agents/
    governance/   qor-governor, qor-judge
    sdlc/         qor-specialist, qor-strategist, qor-fixer, qor-ux-evaluator,
                  project-planner
    memory/       qor-technical-writer, documentation-scribe, learning-capture
    meta/         agent-architect, system-architect, build-doctor
  vendor/
    agents/       accessibility-specialist, code-reviewer, devops-engineer,
                  tauri-launcher, ui-correction-specialist, ultimate-debugger,
                  voice-integration-specialist
    skills/<name>/   (third-party skills per §3.B R-7; collision policy: first-source-wins)
  scripts/
    ledger_hash.py   (minimal — manifest generation + chain verify)
    utilities/       (non-canonical utility scripts from ingest/internal/utilities/)
  experimental/      (non-canonical research from ingest/experimental/)
  templates/         (doc templates from ingest/templates/)

docs/
  migration-manifest-pre.json      (Phase 1.5)
  migration-manifest-post.json     (Phase 1.5)
  META_LEDGER.md                   (append Entries #17, #18, #19)
  SYSTEM_STATE.md                  (rewritten Phase 7)
  SKILL_REGISTRY.md                (rewritten Phase 7)
  PROCESS_SHADOW_GENOME.md         (already initialized; carries the gate override)
  SHADOW_GENOME.md                 (existing VETO records — unchanged)
  archive/2026-04-15/              (Phase 0 snapshots)

.gitignore                         append .qor/, __pycache__/, .pytest_cache/
pyproject.toml                     minimal: [project] + pytest config
```

Explicitly deleted post-migration: `kilo-code/`, `deployable state/`, `processed/`, `compiled/`, `ingest/` (fully dispositioned).

## Phase 0 — Snapshot & infrastructure

- Git tag `pre-qor-migration` on HEAD.
- Copy `ingest/`, `processed/`, `deployable state/`, `kilo-code/`, `compiled/` → `docs/archive/2026-04-15/`.
- Author `pyproject.toml`:
  ```toml
  [build-system]
  requires = ["setuptools>=68"]
  build-backend = "setuptools.build_meta"
  [project]
  name = "qorelogic"
  version = "0.2.0"
  requires-python = ">=3.11"
  [project.optional-dependencies]
  dev = ["pytest>=8"]
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  ```
- Append `.gitignore`: `.qor/`, `__pycache__/`, `.pytest_cache/`.
- Commit: `chore(qor): pre-migration snapshot + minimal infra`.

## Phase 1 — Migrate skills, agents, vendor (per §3 + §3.B rules below)

**Subagents (25 files)**: apply §3 mapping table from `plan-qor-migration-final.md` verbatim (13 → qor/agents/, 7 → qor/vendor/agents/, 5 hearthlink → DELETE).

**Canonical Qor skills**: move `kilo-code/qor-<name>/` → `qor/skills/<category>/qor-<name>/` per structure above. Retire `qor-course-correct`. Create stubs: `qor/skills/sdlc/qor-remediate/` and `qor/skills/governance/qor-shadow-process/` (SKILL.md minimal — full behavior deferred).

**`ingest/skills/` (90 items)**: apply §3.B rules from `plan-qor-migration-final.md`:
- R-1: delete 10 `qor-*.md` (superseded)
- R-2: promote `qor-*` to `qor/skills/<category>/` or `qor/vendor/skills/` per name
- R-3: `log-decision.md`, `track-shadow-genome.md` → `qor/skills/memory/`
- R-4: delete `_quarantine/`
- R-5/R-6: inspect `agents/` and `custom/` at execution; default qor-scoped if content uses qor/qor frontmatter, else vendor
- R-7: all remaining third-party → `qor/vendor/skills/<name>/`

**Collision policy (accepting carried violation V-2)**: when an item in `ingest/skills/<name>` and `ingest/scripts/<name>` both target the same `qor/vendor/skills/<name>/`, the `ingest/skills/` version wins. Discarded content is logged to `.qor/migration-discards.log` for post-hoc review. Not automated; executor logs manually during Phase 1.

**`ingest/` subdirs (§2.B applied)**:
- `ingest/docs/` → `docs/` (merge; 2 files)
- `ingest/experimental/` → `qor/experimental/`
- `ingest/internal/` → split: `agents/` → `qor/agents/` (merge; skill-name wins on collision); `governance/` → `qor/skills/governance/`; `references/` → per-skill `references/`; `scripts/` → `qor/scripts/utilities/` (NOT `qor/scripts/` root — avoids V-3 collision with canonical scripts); `utilities/` → `qor/scripts/utilities/`
- `ingest/lessons-learned/` → `docs/Lessons-Learned/`
- `ingest/references/` → per-skill `references/` folders (qor-*-patterns routed by name; tauri2-* links → `qor/vendor/skills/tauri*/references/`)
- `ingest/scripts/` → `calculate-session-seal.py` → `qor/scripts/`; framework subdirs → `qor/vendor/skills/<name>/` (collision policy above)
- `ingest/templates/` → `qor/templates/`
- `ingest/third-party/` → `qor/vendor/` (merge)
- `ingest/workflows/` → DELETE (legacy qor-* alternates; superseded)

**Deletions in this phase**: all five hearthlink-*, ten ingest/skills/qor-*.md, ingest/skills/_quarantine/, ingest/workflows/ (content), `kilo-code/qor-course-correct/`.

## Phase 1.5 — Ledger continuation

- Author `qor/scripts/ledger_hash.py` with: `content_hash`, `chain_hash`, `write_manifest`, `emit_entry`, `verify`. Atomic writes via `os.replace()` (Windows-safe).
- **Before** Phase 1 moves: emit `docs/migration-manifest-pre.json` covering all migration-source paths with SHA256. Append Entry #17 MIGRATION-SEAL chaining from Entry #16 (chain hash `9730f979...`).
- **After** Phase 1 moves: emit `docs/migration-manifest-post.json`. Append Entry #18 MIGRATION-COMPLETE chaining from #17.
- Verify content-hash integrity: for every file in both manifests (matched by content SHA256), confirm it was a move not a content change. Abort if any `content_modified` mismatch.

## Phase 7 — Cleanup + rewire

- Delete: `ingest/`, `kilo-code/`, `deployable state/`, `processed/`, `compiled/`.
- Rewrite `docs/SYSTEM_STATE.md` with new tree.
- Rewrite `docs/SKILL_REGISTRY.md` with category-organized skill index.
- Update `README.md` structure diagram.
- Append Entry #19 CUTOVER chaining from #18. Content_hash = SHA256 of a brief cutover-manifest listing deleted roots + new SSoT root.
- Sanity checks (narrow, not plan-wide guards — accepting carried V-5):
  ```bash
  [ ! -d ingest/ ] && [ ! -d kilo-code/ ] && [ ! -d 'deployable state/' ] && [ ! -d processed/ ] && [ ! -d compiled/ ]
  ! grep "kilo-code/qor-\|deployable state\|ingest/" docs/SYSTEM_STATE.md docs/SKILL_REGISTRY.md README.md
  ```

## Deferred to `plan-qor-tooling-deferred.md`

- Phase 2: `compile.py`, variant drift check, pre-commit hook, `qor/dist/`
- Phase 3: Gate chain runtime, `session.py`, `validate_gate_artifact.py`, gate schemas
- Phase 4: Full Process Shadow Genome automation (threshold trip, issue creation, escalation idempotence)
- Phase 5: Cross-repo collector
- Phase 6: Platform detection, capability manifests
- Phase 8: End-to-end validation suite

## Carried violations (accepted as known risk)

- V-1 (§2.B dests not in §2 tree): addressed — this minimal plan's §Target Structure lists them explicitly
- V-2 (21 ingest collisions): addressed — collision policy stated (first-source-wins, logged)
- V-3 (merge order for internal/scripts): addressed — routed to `qor/scripts/utilities/` not root
- V-4 (R-5/R-6 deferred): accepted — runtime inspection with stated default (qor-scoped if qor frontmatter present)
- V-5 (CI grep over-aggressive): addressed — narrowed to forward-looking docs only

## Success criteria

- [ ] Git tag `pre-qor-migration` present
- [ ] `docs/archive/2026-04-15/` populated
- [ ] `qor/` SSoT present with skills, agents, vendor, scripts, experimental, templates populated
- [ ] `docs/migration-manifest-pre.json` and `-post.json` present; Entries #17, #18, #19 appended to ledger with valid chain
- [ ] `kilo-code/`, `deployable state/`, `processed/`, `compiled/`, `ingest/` all deleted
- [ ] `ledger_hash.py --verify docs/META_LEDGER.md` exits 0 (chain intact from Entry #1 through #19)
- [ ] `SYSTEM_STATE.md` and `SKILL_REGISTRY.md` rewritten
- [ ] `PROCESS_SHADOW_GENOME.md` records gate override event (already done pre-implementation)
