# Plan: Qor SSoT Migration & Self-Improvement Loop

**Status**: Draft (awaiting audit gate)
**Author**: QoreLogic Governor
**Date**: 2026-04-15
**Gate artifact for**: `/qor-audit`, `/qor-implement`

## 1. Objectives

1. Collapse the four parallel skill surfaces (`kilo-code/`, `deployable state/claude/`, `deployable state/kilo-code/`, `ingest/skills/`) into a single source of truth under `qor/`.
2. Categorize skills by function (governance, SDLC, MLOps, memory, meta).
3. Treat variant outputs (claude, kilo-code, codex) as build artifacts, never hand-edited.
4. Replace binary audit pass/veto with a full SDLC gate chain, soft-enforced.
5. Introduce `/qor-remediate` (absorbs `/qor-course-correct`) for process-level failures.
6. Introduce Process Shadow Genome — log process failures, trigger GitHub issues at severity threshold, pooled across repos via scheduled batch job.
7. Add platform-capability awareness so skills adapt to Claude Code (Agent Teams, Codex plugin) vs Kilo vs future Codex-standalone.

## 2. Target Structure

```
qor/
  skills/
    governance/       audit, validate, substantiate
    sdlc/             research, plan, implement, refactor, debug, remediate
    mlops/            (stub — future)
    memory/           status, document, organize, shadow-process
    meta/             bootstrap, help, repo-audit, repo-release, repo-scaffold
  agents/
    governance/       ql-governor, ql-judge, code-reviewer, ...
    sdlc/             ql-specialist, ql-strategist, ql-fixer, project-planner, ...
    memory/           ql-technical-writer, documentation-scribe, learning-capture
    meta/             agent-architect, system-architect, build-doctor
  platform/
    capabilities.md   catalog of platform features Qor skills can leverage
    detect.md         session-scoped detection skill
    profiles/         claude-code-solo, claude-code-with-codex,
                      claude-code-teams, kilo-code, codex-standalone
  gates/
    schema/           JSON schemas for phase artifacts (research.json, plan.json, ...)
    chain.md          gate chain definition (soft-enforced)
  prompts/            non-skill prompts, categorized same as skills/
  vendor/             third-party skills (react-best-practices, tauri2-*, elevenlabs, ...)
  scripts/
    compile.mjs                      ingest qor/skills/** -> variant outputs
    check-variant-drift.mjs          CI guard: regenerate temp, diff against committed
    check-shadow-threshold.mjs       read shadow genome, compute severity sum
    collect-shadow-genomes.mjs       cross-repo sweep for scheduled issue creation
    gh-create-shadow-issue.mjs       create GitHub issue from aggregated entries

deployable state/           (generated output, do not hand-edit)
  claude/skills/...
  claude/agents/...
  kilo-code/...

docs/                       (unchanged structure, content updated)
archive/2026-04-15/         (pre-migration snapshots)
build/                      (compile scripts live under qor/scripts/ — build/ reserved for CI wrappers)
```

## 3. Migration Phases

### Phase 0 — Freeze & snapshot
- Git tag `pre-qor-migration`
- Copy `ingest/`, `processed/`, `deployable state/`, `kilo-code/` into `archive/2026-04-15/`
- Commit snapshot

### Phase 1 — Author SSoT
- Canonical source for each skill: current `kilo-code/qor-*` (most recent version per META_LEDGER)
- Move (not copy) to `qor/skills/<category>/qor-<name>/`
- Retire `qor-course-correct` (functionality merges into `qor-remediate`)
- Create skill stubs:
  - `qor/skills/sdlc/qor-remediate/` (process-failure skill)
  - `qor/skills/memory/qor-shadow-process/` (log + threshold check)
  - `qor/platform/detect.md`
- Create reference (not a skill):
  - `qor/skills/governance/qor-audit/references/adversarial-mode.md` — invoked by `qor-audit` when Codex capability detected; otherwise audit runs in solo mode

### Phase 2 — Build pipeline
- `qor/scripts/compile.mjs`:
  - Input: `qor/skills/**/*.md`
  - Outputs: `deployable state/claude/skills/`, `deployable state/kilo-code/`
  - Format transforms per variant profile
- `qor/scripts/check-variant-drift.mjs`: CI-invoked, fails on uncommitted drift
- Pre-commit hook (`.githooks/pre-commit`): reject edits to `deployable state/**` unless `BUILD_REGEN=1` env flag is set
- Codex variant: registered in compiler but target stubbed (no output yet)

### Phase 3 — Gate chain
- Chain: `research -> plan -> audit -> implement -> substantiate -> validate -> remediate?`
- `audit` runs in adversarial mode when Codex capability is detected (delegates counter-argument pass to Codex, synthesizes critique); falls back to solo audit otherwise. Absence of Codex logs a severity-2 `capability_shortfall` event but does not block.
- Each skill:
  - On startup, reads expected prior-phase artifact from `.qor/gates/<session>/`
  - Missing artifact -> advisory warning printed, prompts user to confirm override
  - Override is permitted, but emits a shadow-process event (severity 1)
- Artifact schemas defined under `qor/gates/schema/`

### Phase 4 — Process Shadow Genome
- `docs/PROCESS_SHADOW_GENOME.md` — append-only log, JSON lines format
- Event schema:
  ```json
  {
    "ts": "ISO-8601",
    "skill": "qor-implement",
    "session_id": "...",
    "event_type": "gate_override | regression | hallucination | degradation | capability_shortfall",
    "severity": 1-5,
    "details": { ... },
    "addressed": false,
    "issue_url": null
  }
  ```
- Severity rubric: override=1, capability_shortfall=2, regression=3, hallucination=4, degradation=5
- `qor/scripts/check-shadow-threshold.mjs`: sums unaddressed severity; threshold = 10
- When threshold breached: `gh issue create` with aggregated entries, mark entries `addressed: true`, store `issue_url`

### Phase 5 — Cross-repo batch collector
- `qor/scripts/collect-shadow-genomes.mjs`:
  - Reads a config (`~/.qor/repos.json`) listing local Qor-using repo paths
  - Sweeps each repo's `docs/PROCESS_SHADOW_GENOME.md`
  - Pools unaddressed entries, applies threshold check globally
  - Creates consolidated issue in a designated "meta" repo (this one, while private)
- Scheduled via cron or Windows Task Scheduler (out-of-scope to configure; provide docs)

### Phase 6 — Platform awareness
- `qor/platform/detect.md`:
  - On first Qor skill invocation per session, runs detection:
    - Is `codex` plugin available? (probe env / tool list)
    - Is Agent Teams tooling available? (probe for `TeamCreate`)
    - Which host? (Claude Code vs Kilo vs standalone)
  - Writes marker: a stable sentinel string in conversation (`QOR_PLATFORM_PROFILE: <profile>`)
  - Subsequent skills grep context for marker; skip detection if present
  - Ambiguous -> asks user
- Each skill's front matter gains `<requires>` and `<enhances-with>` blocks
- `qor-audit` enhances with `codex-plugin` (switches to adversarial mode); absent -> solo audit + capability_shortfall logged
- `qor-plan` / `qor-implement` enhance with `agent-teams`; absent -> sequential mode

### Phase 7 — Rewire references
- Update `docs/SKILL_REGISTRY.md`, `SYSTEM_STATE.md`, `META_LEDGER.md`
- Update `README.md` with new structure diagram
- Delete `processed/` (empty), `compiled/` (empty)
- Delete orphan `ingest/ql-*.md` duplicates (archived in Phase 0)

### Phase 8 — Validation
- Run every migrated skill end-to-end on a trivial task
- Verify gate chain prints advisory on out-of-order invocation
- Verify override emits shadow-process event
- Verify `check-variant-drift.mjs` catches a manual edit to `deployable state/`
- Verify `collect-shadow-genomes.mjs` opens an issue at threshold (test with synthetic entries)
- Verify `qor/platform/detect.md` sets marker and subsequent skills reuse it

## 4. Out of scope for this migration

- MLOps skill authoring (directory scaffolded only)
- Codex variant output (compiler target stubbed)
- Scheduling config for the cross-repo collector (docs only)
- Migration of `ingest/third-party/`, `ingest/experimental/`, `ingest/internal/` — evaluated per-item after migration stable

## 5. Risks

- **Reference rot**: Docs and external consumers referencing old paths. Mitigation: keep `archive/` snapshot, one-pass sweep of `docs/` for old paths.
- **Variant drift reintroduced**: Contributors ignore pre-commit hook. Mitigation: CI guard is authoritative; hook is a convenience.
- **Over-categorization**: Skills that straddle categories. Mitigation: pick primary category, cross-link in registry.
- **Platform detection false negatives**: Marker missing due to context compression. Mitigation: detection is cheap enough to re-run; make marker check tolerant.

## 6. Success criteria

- [ ] Single canonical skill source under `qor/skills/`
- [ ] Zero hand-edits to `deployable state/` after cutover (enforced by CI)
- [ ] All SDLC phases represented as skills with advisory gates
- [ ] `/qor-remediate` replaces `/qor-course-correct` (old skill removed)
- [ ] Shadow Process Genome active, threshold trigger tested
- [ ] Platform detection runs once per session, skills adapt
- [ ] `docs/SYSTEM_STATE.md` reflects new tree
- [ ] `docs/META_LEDGER.md` entry recording migration hash
