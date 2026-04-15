# Plan: Qor SSoT Migration & Self-Improvement Loop — v2 (Remediation)

**Status**: Draft (post-VETO remediation)
**Author**: QoreLogic Governor
**Date**: 2026-04-15
**Supersedes**: `docs/plan-qor-migration.md` (v1, VETO — Ledger #12)
**Gate artifact for**: `/qor-audit`, `/qor-implement`

## Open Questions

None. User decisions resolved pre-draft:

- SSoT location: `qor/dist/` (strict boundary)
- `qor-shadow-process` category: `governance/`
- GitHub issue client: `gh` CLI via subprocess
- `/qor-remediate` trigger: auto-invoke on threshold breach
- Meta repo: `MythologIQ/Qorelogic`
- Codex plugin: production-available, adversarial protocol specified (contract level) in Phase 3; detection probe authored with `qor/platform/detect.md` in Phase 6

## 0. Verified Grounding

- Existing pipeline language: **Python 3** (verified: `scripts/compile-claude.py:1`, `scripts/process-skills.py:1`) — all new automation in Python.
- No existing hash automation (verified: `grep "sha256\|hash" scripts/*.py` → empty). Migration introduces `qor/scripts/ledger_hash.py`.
- Existing `compiled/` dir empty (verified: `ls compiled/` → empty). Legacy output target; replaced by `qor/dist/`.
- Ledger chain model: content_hash (SHA256 of artifact), previous_hash, chain_hash = SHA256(content_hash + previous_hash). Verified from Entry #10 (`docs/META_LEDGER.md:L1-L30` of last entries).
- Last chain hash before migration: `1877524df25b0a9e5a1ab2d57ed10317979fd7b975734b6e42d19e6c4d5d7740` (Entry #10 seal).
- `gh` CLI auth assumed pre-configured; validated at script startup, fails fast if not.

## 1. Target Structure (revised — every artifact has a creating phase)

```
qor/
  skills/
    governance/         audit, validate, substantiate, shadow-process
    sdlc/               research, plan, implement, refactor, debug, remediate
    mlops/              (REMOVED — not in v1 scope; re-added when authored)
    memory/             status, document, organize
    meta/               bootstrap, help, repo-audit, repo-release, repo-scaffold
  agents/
    governance/         qor-governor, qor-judge, code-reviewer
    sdlc/               qor-specialist, qor-strategist, qor-fixer, project-planner
    memory/             qor-technical-writer, documentation-scribe, learning-capture
    meta/               agent-architect, system-architect, build-doctor
  platform/
    capabilities.md     (authored in Phase 6)
    detect.md           (authored in Phase 6)
    profiles/
      claude-code-solo.md              (Phase 6)
      claude-code-with-codex.md        (Phase 6)
      claude-code-teams.md             (Phase 6)
      kilo-code.md                     (Phase 6)
      codex-standalone.md              (Phase 6)
  gates/
    chain.md            (Phase 3)
    schema/
      research.schema.json              (Phase 3)
      plan.schema.json                  (Phase 3)
      audit.schema.json                 (Phase 3)
      implement.schema.json             (Phase 3)
      substantiate.schema.json          (Phase 3)
      validate.schema.json              (Phase 3)
      remediate.schema.json             (Phase 3)
  vendor/               third-party skills moved from ingest/skills/ (Phase 1)
  scripts/
    compile.py                         ingest qor/skills/** -> qor/dist/variants/**
    check_variant_drift.py             CI guard: regenerate, diff
    check_shadow_threshold.py          sum unaddressed severity
    collect_shadow_genomes.py          cross-repo sweep
    create_shadow_issue.py             subprocess gh issue create
    ledger_hash.py                     compute content/chain hashes; emit entry
    validate_gate_artifact.py          jsonschema validation against qor/gates/schema/
  dist/
    variants/
      claude/                          (Phase 2 compile output)
      kilo-code/                       (Phase 2 compile output)
      codex/                           (Phase 2 stub only — compiler registers target, no output)

.qor/
  gates/<session_id>/   gate artifacts written by each phase (runtime state; gitignored)

.githooks/
  pre-commit            (Phase 2) — blocks edits to qor/dist/** unless BUILD_REGEN=1; logs override to .qor/override.log

docs/
  META_LEDGER.md        (unchanged structure; Phase 7 appends migration-seal entry)
  SYSTEM_STATE.md       (Phase 7 rewrite)
  PROCESS_SHADOW_GENOME.md    (Phase 4 create; JSONL)
  SHADOW_GENOME.md      (existing — VETO records)
  archive/2026-04-15/   (Phase 0 snapshots)

.gitignore              (Phase 0) — adds .qor/, .qor/override.log
```

**Removed from prior structure**: top-level `build/` (no purpose; `qor/scripts/` is the single automation home); `qor/prompts/` (no content to migrate — can be reintroduced when authored); `qor/skills/mlops/` (deferred).

## 2. Phase-by-phase

### Phase 0 — Freeze & snapshot

**Affected files**:
- `.gitignore` — add `.qor/`, `.qor/override.log`
- `docs/archive/2026-04-15/` — create, populate with copies

**Changes**:
- Git tag `pre-qor-migration` on current HEAD
- Copy `ingest/`, `processed/`, `deployable state/`, `kilo-code/`, `compiled/` to `docs/archive/2026-04-15/`
- Commit: `chore(qor): pre-migration snapshot`

**Unit tests**: none (pure file ops).

**CI validation**: `git tag --list pre-qor-migration` returns tag; `ls docs/archive/2026-04-15/` non-empty.

---

### Phase 1 — Author SSoT under `qor/skills/` and `qor/agents/`

**Affected files**:
- `qor/skills/<category>/qor-<name>/SKILL.md` × (all canonical skills) — moved from `kilo-code/qor-<name>/`
- `qor/agents/<category>/<name>.md` × (all canonical agents) — moved from `ingest/subagents/`
- `qor/skills/sdlc/qor-remediate/SKILL.md` — new (absorbs `qor-course-correct`)
- `qor/skills/governance/qor-shadow-process/SKILL.md` — new
- `qor/skills/governance/qor-audit/references/adversarial-mode.md` — new
- `qor/vendor/**` — moved from `ingest/skills/` (third-party only; qor-* stays in `qor/skills/`)
- `kilo-code/qor-course-correct/` — deleted (absorbed)

**Changes**:
- Canonical source precedence: `kilo-code/qor-*/SKILL.md` (most recent per META_LEDGER #10)
- Each skill gains YAML frontmatter `requires:` and `enhances_with:` blocks
- `qor-remediate` receives auto-invocation contract: reads `docs/PROCESS_SHADOW_GENOME.md`, pattern-matches, proposes process change

**Unit tests** (TDD — authored first):
- `tests/test_skill_inventory.py::test_every_kilo_skill_has_canonical_home` — every `kilo-code/qor-*` either moved or explicitly retired
- `tests/test_skill_inventory.py::test_no_duplicate_skills_across_variants` — each skill name appears once in `qor/skills/`
- `tests/test_skill_inventory.py::test_retired_skills_absent` — `qor-course-correct` removed from all locations

**CI validation**: `python -m pytest tests/test_skill_inventory.py`

---

### Phase 1.5 — Ledger continuation (NEW — audit item #3)

**Affected files**:
- `qor/scripts/ledger_hash.py` — new
- `docs/META_LEDGER.md` — append Entry #13 "MIGRATION-SEAL"

**Changes**:
- `ledger_hash.py` exposes:
  - `content_hash(path) -> str` — SHA256 of file bytes
  - `chain_hash(content_hash, prev_hash) -> str` — SHA256(content + prev)
  - `emit_entry(kind, artifact_path, prev_hash, metadata) -> dict` — structured ledger entry
- Before any Phase 1 file moves: author migration-seal entry recording current state of canonical paths with their content hashes against `1877524d...` previous. Moved-file hashes are recomputed at new paths post-move and recorded in a **second** entry (Entry #14 "MIGRATION-COMPLETE") that chains from #13.
- Historical entries (#1-#10) are **frozen as historical**; their path references become archived. META_LEDGER adds a "Path rebasing" section pointing old paths to new.

**Chain continuation rule** (explicit): entries referencing pre-migration paths are immutable. Entry #13 closes the old chain. Entry #14 opens the new chain at `qor/` paths. Chain verifier reads entries sequentially; path-rebase map allows content re-verification of historical entries.

**Unit tests**:
- `tests/test_ledger_hash.py::test_content_hash_deterministic`
- `tests/test_ledger_hash.py::test_chain_hash_matches_manual_computation` — verifies against Entry #10's known chain hash
- `tests/test_ledger_hash.py::test_emit_entry_has_required_fields`
- `tests/test_ledger_hash.py::test_migration_seal_references_old_paths`
- `tests/test_ledger_hash.py::test_migration_complete_references_new_paths`

**CI validation**: `python qor/scripts/ledger_hash.py --verify docs/META_LEDGER.md`

---

### Phase 2 — Build pipeline

**Affected files**:
- `qor/scripts/compile.py` — new
- `qor/scripts/check_variant_drift.py` — new
- `.githooks/pre-commit` — new
- `docs/hooks-install.md` — new (documents `git config core.hooksPath .githooks`)
- `qor/dist/variants/{claude,kilo-code,codex}/` — created (codex empty by design)

**Changes**:
- `compile.py`:
  - Input: `qor/skills/**/SKILL.md`, `qor/agents/**/*.md`
  - Outputs: `qor/dist/variants/claude/{skills,agents}/`, `qor/dist/variants/kilo-code/{skills,agents}/`
  - Codex target: registered in `TARGETS = {"claude", "kilo-code", "codex"}` but `codex` emit is `pass` (stub)
  - Python stdlib only (`pathlib`, `re`, `hashlib`, `json`); no third-party deps
  - Runtime: Python 3.11+ (verified compatibility required pre-commit)
- `check_variant_drift.py`: runs `compile.py` into a tempdir, diffs against `qor/dist/`, exits non-zero on diff
- `.githooks/pre-commit` (bash): if any staged file matches `qor/dist/**` and `$BUILD_REGEN` != `1`, reject; else append timestamp+user+files to `.qor/override.log`

**Unit tests**:
- `tests/test_compile.py::test_compile_claude_variant_format` — output matches fixture
- `tests/test_compile.py::test_compile_kilocode_variant_format`
- `tests/test_compile.py::test_codex_target_registered_but_empty`
- `tests/test_compile.py::test_drift_detector_flags_manual_edit`
- `tests/test_compile.py::test_hook_bypass_logs_override` — audit item #10

**CI validation**: `python qor/scripts/check_variant_drift.py` exits 0; `python -m pytest tests/test_compile.py`.

---

### Phase 3 — Gate chain (advisory, soft-enforced)

**Affected files**:
- `qor/gates/chain.md` — new
- `qor/gates/schema/*.schema.json` × 7 — new (one per phase)
- `qor/scripts/validate_gate_artifact.py` — new
- Every skill in `qor/skills/` — YAML frontmatter adds `gate_reads:` (prior artifact path pattern) and `gate_writes:` (output artifact)

**Changes**:
- Chain: `research -> plan -> audit -> implement -> substantiate -> validate -> remediate?`
- Artifacts written to `.qor/gates/<session_id>/<phase>.json`
- Each skill on startup:
  1. Resolve session_id (env `QOR_SESSION` or first 8 chars of UTC ISO-min)
  2. Read expected prior artifact; if missing, print advisory + prompt user to override
  3. Override acknowledged → emit shadow-process event (severity 1, event_type=`gate_override`)
- Codex adversarial mode (audit phase only) — **protocol contract**:
  - **Input schema** (`qor/gates/schema/audit.schema.json`): `{plan_path, plan_content_hash, codebase_snapshot_refs[], session_id}`
  - **Expected output** (`adversarial_critique.schema.json`): `{critiques[]: {severity, claim_challenged, counter_evidence, recommended_gap}, confidence}`
  - Invocation mechanism: determined by `qor/platform/detect.md` in Phase 6 (the probe identifies the Codex-plugin tool signature; the invocation binding is a one-line subprocess or tool-call wrapper registered in `qor/platform/profiles/claude-code-with-codex.md`)
  - When capability flag absent: audit runs solo, emits shadow-process event (severity 2, event_type=`capability_shortfall`)

**Unit tests**:
- `tests/test_gates.py::test_missing_prior_artifact_triggers_advisory`
- `tests/test_gates.py::test_override_emits_shadow_event`
- `tests/test_gates.py::test_schema_validates_well_formed_artifact`
- `tests/test_gates.py::test_schema_rejects_malformed_artifact` — audit item #10
- `tests/test_gates.py::test_adversarial_input_schema_well_formed`

**CI validation**: `python -m pytest tests/test_gates.py`; `python qor/scripts/validate_gate_artifact.py --all`.

---

### Phase 4 — Process Shadow Genome

**Affected files**:
- `docs/PROCESS_SHADOW_GENOME.md` — new (JSONL, append-only)
- `qor/scripts/check_shadow_threshold.py` — new
- `qor/scripts/create_shadow_issue.py` — new

**Changes**:
- Event schema (embedded in `qor/gates/schema/shadow_event.schema.json`):
  ```json
  {
    "ts": "ISO-8601 UTC",
    "skill": "qor-<name>",
    "session_id": "string",
    "event_type": "gate_override | regression | hallucination | degradation | capability_shortfall",
    "severity": 1-5,
    "details": {},
    "addressed": false,
    "issue_url": null,
    "addressed_ts": null,
    "addressed_reason": null
  }
  ```
- Severity rubric: override=1, capability_shortfall=2, regression=3, hallucination=4, degradation=5. Threshold=10 unaddressed severity.
- `addressed` state machine (audit item #9):
  - `false → true (issue_created)` — when threshold trips, `create_shadow_issue.py` flips matched entries, sets `issue_url`, `addressed_ts=now`, `addressed_reason="issue_created"`
  - `false → true (resolved_without_issue)` — operator can mark via `qor-remediate`; sets `addressed_reason="remediated"`
  - `false → true (stale_expired)` — entries older than 90 days without triggering threshold; `addressed_reason="stale"` (prevents permanent accumulation)
  - Reverse transitions forbidden (append a new event if re-opened)
- `check_shadow_threshold.py`: reads JSONL, filters `addressed=false`, sums severity, exits with code 10 if ≥ threshold (signals auto-trigger)
- `create_shadow_issue.py`: runs `gh issue create --repo MythologIQ/Qorelogic --title "..." --body "..." --label qor-shadow`, captures URL, mutates JSONL in place (atomic write via temp+rename)
- Auto-trigger wiring: any Qor skill's post-run hook invokes `check_shadow_threshold.py`; if exit=10, invokes `/qor-remediate`

**Unit tests**:
- `tests/test_shadow.py::test_threshold_sum_ignores_addressed`
- `tests/test_shadow.py::test_issue_creation_flips_addressed`
- `tests/test_shadow.py::test_stale_expiry_90_days`
- `tests/test_shadow.py::test_event_schema_validation`
- `tests/test_shadow.py::test_auto_trigger_invokes_remediate`
- `tests/test_shadow.py::test_severity_rubric_threshold_calibration` — audit item #10

**CI validation**: `python -m pytest tests/test_shadow.py`

---

### Phase 5 — Cross-repo batch collector

**Affected files**:
- `qor/scripts/collect_shadow_genomes.py` — new
- `docs/qor-config-schema.md` — new
- `~/.qor/repos.json` — documented, not committed

**Changes**:
- Config schema (`~/.qor/repos.json`):
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
  - Reads config from `$QOR_CONFIG` or `~/.qor/repos.json`
  - For each enabled repo: load `docs/PROCESS_SHADOW_GENOME.md` (JSONL), filter `addressed=false`, tag with `source_repo`
  - Pool globally, apply threshold
  - If tripped: aggregate into single issue body, call `create_shadow_issue.py --consolidated`
- Scheduling: documented in `docs/qor-config-schema.md` (Windows Task Scheduler xml + cron one-liner); not configured by plan

**Unit tests**:
- `tests/test_collect.py::test_config_schema_validation`
- `tests/test_collect.py::test_multi_repo_aggregation`
- `tests/test_collect.py::test_threshold_trips_globally_not_per_repo`
- `tests/test_collect.py::test_missing_repo_path_logged_not_fatal`

**CI validation**: `python -m pytest tests/test_collect.py` with fixture repos under `tests/fixtures/repos/`.

---

### Phase 6 — Platform awareness

**Affected files**:
- `qor/platform/capabilities.md` — new (catalog: Claude Code Agent Teams, Skills, subagents, hooks, MCP, Codex-plugin, Kilo)
- `qor/platform/detect.md` — new (skill spec)
- `qor/platform/profiles/*.md` × 5 — new
- Every skill under `qor/skills/` — frontmatter `requires:` / `enhances_with:` populated

**Changes**:
- `detect.md` defines probes:
  - Codex plugin: probe tool list for `codex` / `mcp__codex*` signatures
  - Agent Teams: probe for `TeamCreate` deferred tool
  - Host (Claude Code vs Kilo): probe `CLAUDE_PROJECT_DIR` env vs Kilo-specific markers
- Marker format: `QOR_PLATFORM_PROFILE: <profile_id>|<capabilities_csv>|<iso_ts>`
- Marker tolerance rule (audit item #13): detection re-runs if marker absent OR marker `iso_ts` older than `session_start_ts` OR capabilities list missing a capability the current skill's `enhances_with` asks about. Concrete rule, not "be tolerant."
- Profile files enumerate expected capabilities and per-capability invocation bindings (e.g., `claude-code-with-codex.md` specifies the exact tool call for adversarial review — pinned once `detect.md` identifies the production Codex plugin signature)

**Unit tests**:
- `tests/test_platform.py::test_marker_format_parseable`
- `tests/test_platform.py::test_redetect_when_marker_stale`
- `tests/test_platform.py::test_redetect_when_capability_missing`
- `tests/test_platform.py::test_codex_probe_identifies_plugin`
- `tests/test_platform.py::test_profile_covers_all_capabilities`

**CI validation**: `python -m pytest tests/test_platform.py` (probes mocked).

---

### Phase 7 — Rewire references & cleanup

**Affected files**:
- `docs/SYSTEM_STATE.md` — rewrite reflecting new tree
- `docs/SKILL_REGISTRY.md` — rewrite
- `docs/META_LEDGER.md` — append Entry #15 "CUTOVER"
- `README.md` — update structure diagram
- `processed/` — delete
- `compiled/` — delete
- `ingest/ql-*.md` — delete (orphan duplicates; archived Phase 0)
- `kilo-code/` — delete top-level (all migrated)
- `deployable state/` — delete (replaced by `qor/dist/`)

**Changes**:
- Sweep `docs/` for old path references; replace with `qor/` paths
- Entry #15 chains from #14, content-hash covers the cutover manifest (list of deleted dirs + new SSoT root)

**Unit tests**:
- `tests/test_cleanup.py::test_no_old_paths_in_docs` — greps for forbidden old paths
- `tests/test_cleanup.py::test_legacy_dirs_absent`

**CI validation**: `python -m pytest tests/test_cleanup.py`; `grep -r "kilo-code/qor-\|deployable state\|processed/\|compiled/" docs/` returns only archive references.

---

### Phase 8 — Validation (expanded per audit item #10)

**Affected files**:
- `tests/test_end_to_end.py` — new (orchestrates)
- `tests/fixtures/trivial_task/` — new

**Changes**:
- Run every migrated skill end-to-end on a trivial task (fixture)
- Verify gate chain prints advisory on out-of-order invocation
- Verify override emits shadow-process event AND appends to `.qor/override.log`
- Verify `check_variant_drift.py` catches manual edit to `qor/dist/`
- Verify `BUILD_REGEN=1` bypass path logs to `.qor/override.log` (audit item — trapdoor verified)
- Verify `collect_shadow_genomes.py` opens an issue at threshold with synthetic entries (mocked `gh`)
- Verify `qor/platform/detect.md` sets marker; subsequent skill reuses
- Verify ledger chain integrity post-migration (`ledger_hash.py --verify` passes from Entry #1 through #15)
- Verify gate artifact schema rejects malformed JSON
- Verify severity rubric: synthetic event stream of known severities trips threshold at exactly the right count

**Unit tests**: aggregated into `test_end_to_end.py` as parameterized cases.

**CI validation**: `python -m pytest tests/` (all suites green).

---

## 3. Traceability — audit remediation items

| Audit # | Remediation | Phase |
|---|---|---|
| 1 | Declare `.qor/` state directory | §1 structure, Phase 3 creation |
| 2 | Populate or remove all seven orphans | §1 (mlops & prompts removed; rest assigned to creating phases) |
| 3 | Add Phase 1.5 — Ledger continuation | Phase 1.5 |
| 4 | Specify script runtime: Python 3.11+, stdlib-only + `gh` subprocess | §0, Phase 2 |
| 5 | Resolve `build/` vs `qor/scripts/` | `build/` removed; `qor/scripts/` is single home |
| 6 | Move `qor-shadow-process` to `governance/` | §1 structure |
| 7 | Specify Codex adversarial protocol | Phase 3 (contract) + Phase 6 (invocation binding) |
| 8 | Specify `/qor-remediate` trigger | Phase 4 (auto-invoke on threshold) |
| 9 | Define `addressed` state machine | Phase 4 |
| 10 | Validation tests for ledger, bypass, schema | Phase 1.5, Phase 2, Phase 3, Phase 8 |
| 11 | `qor/dist/` preserves SSoT boundary | §1 structure |
| 12 | `~/.qor/repos.json` schema + meta repo named | Phase 5 (`MythologIQ/Qorelogic`) |
| 13 | Replace marker-tolerance non-mitigation with concrete rule | Phase 6 |

## 4. Dependencies

- **Python 3.11+** (stdlib only in `qor/scripts/`: `pathlib`, `re`, `hashlib`, `json`, `subprocess`, `argparse`, `dataclasses`)
- **pytest** (dev-only, for test suite)
- **jsonschema** (dev-only, for `validate_gate_artifact.py`; avoids reinventing validation)
- **gh CLI** (runtime dep for `create_shadow_issue.py`; auth pre-configured, validated at script startup)
- No Node, no npm, no `package.json`

Justification vs <10-line vanilla: `jsonschema` replaces ~200 lines of hand-written validator; `pytest` is project-wide test runner already implied by `test_*` files.

## 5. Risks

- **Ledger chain ambiguity across migration**: Mitigation — Phase 1.5 emits explicit migration-seal + complete entries; historical entries frozen with path rebase map.
- **Hook bypass abuse**: Mitigation — override log is audited in Phase 8 test; CI drift check is authoritative regardless of hook state.
- **Codex-plugin signature drift**: Mitigation — `detect.md` probe is testable and re-runs on session start; binding lives in one file (`claude-code-with-codex.md`) for single-point update.
- **Cross-repo collector hits missing/moved repos**: Mitigation — missing path is logged as warning, not fatal; test covers this.
- **Auto-trigger `/qor-remediate` storms**: Mitigation — after auto-invoke, matched entries flip to `addressed=true` immediately, preventing re-trigger on same events.

## 6. Success criteria

- [ ] All 13 audit remediation items resolved (see §3)
- [ ] Single canonical skill source under `qor/skills/`
- [ ] Zero orphan artifacts in `qor/`
- [ ] Ledger chain verifiable from Entry #1 through post-migration entries (#13-#15)
- [ ] `qor-shadow-process` in `governance/`, not `memory/`
- [ ] `qor/dist/` is only variant output location
- [ ] `/qor-remediate` auto-triggers at threshold; demonstrated by Phase 8 test
- [ ] Codex adversarial contract implemented at schema level; invocation pinned in profile
- [ ] All Phase 8 validation tests pass
- [ ] `docs/SYSTEM_STATE.md` reflects `qor/` tree
- [ ] `docs/META_LEDGER.md` Entries #13-#15 appended with valid chain
