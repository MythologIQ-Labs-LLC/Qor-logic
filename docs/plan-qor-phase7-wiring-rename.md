# Plan: Phase 7 — Qor/qor Rename + Skill Wiring (Tier B)

**Status**: Active (scope-limited)
**Author**: QorLogic Governor
**Date**: 2026-04-15
**Scope**: Two orthogonal cleanups combined because they share the dist-regeneration cost. (A) Rename `qor-*` directories + Qor/qor text occurrences to Qor/qor-. (B) Gate-frontmatter on all 18 qor-* skills + full runtime wiring on qor-audit.

## Open Questions

None. Decisions settled:
- Archive and historical artifacts untouched (frozen record)
- Tier B wiring: frontmatter everywhere, runtime in `qor-audit` only as template
- `is_available("codex-plugin")` branching gated by host=`claude-code`
- `qor-*` skill directory renames: all 14 directories migrate

## Task A — Rename sweep

### A.1 Directory renames (14)

Verified: `find qor/skills qor/vendor -maxdepth 4 -type d -name 'qor-*'`.

```
qor/skills/governance/qor-governance-compliance    -> qor/skills/governance/qor-governance-compliance
qor/skills/memory/qor-docs-technical-writing       -> qor/skills/memory/qor-docs-technical-writing
qor/skills/meta/qor-meta-log-decision              -> qor/skills/meta/qor-meta-log-decision
qor/skills/meta/qor-meta-track-shadow              -> qor/skills/meta/qor-meta-track-shadow
qor/vendor/skills/chrome-devtools/qor-web-chrome-devtools-audit  -> qor-web-chrome-devtools-audit
qor/vendor/skills/tauri/qor-tauri2-{async,cicd,errors,ipc,performance,plugins,security,state,testing}
    -> qor-tauri2-*                                                               (9 dirs)
```

Method: `git mv` each, batched.

### A.2 Text sweep

Scoped replacement. In-scope files: every currently-active markdown/yaml/py in `qor/`, `docs/` (excluding historical), `README.md`.

**Rules**:
- `QorLogic` → `QorLogic` (preserve compound form)
- `Qor Logic` → `Qor Logic`
- Bare `Qor` (word boundary) → `Qor`
- `qor-` (path-like, in prose or code) → `qor-`
- `qor-` (path-like) → `qor-`
- `/qor` (slash command) → `/qor`

**Excluded from sweep** (historical record, frozen):

- `docs/archive/**`
- `docs/META_LEDGER.md` (entries cite old paths as historical fact)
- `docs/SHADOW_GENOME.md` (VETO records reference what existed then)
- `docs/PROCESS_SHADOW_GENOME.md` (event `details` reference contemporaneous paths)
- `docs/migration-manifest-{pre,post}.json` + `substantiate-manifest-*.json` + `cutover-manifest-*.json` (content-hashed; changing invalidates Entry #17/#18/#19)
- `docs/plan-qor-migration{,v2,v3,-final}.md`, `docs/plan-qor-migration-final.md`, `docs/plan-skill-consolidation.md`, `docs/plan-b5-b8-navigator-fixer.md`, `docs/plan-compilation-pipeline.md` (historical plans)
- `docs/Lessons-Learned/**`
- `.qor/migration-discards.log`

### A.3 Dist regeneration

Source renames invalidate drift. Run `BUILD_REGEN=1 python qor/scripts/compile.py` to re-emit variants. Pre-commit hook logs the override.

## Task B — Skill wiring (Tier B)

### B.1 Gate frontmatter on all 18 qor-* skills

Add to every `qor/skills/<category>/qor-<name>/SKILL.md` that lacks it:

```yaml
---
phase: <phase-name>
gate_reads: <prior-phase>   # or empty for research
gate_writes: <phase-name>
---
```

Per `qor/gates/chain.md` table. Skills already having frontmatter (e.g., `qor-remediate`, `qor-shadow-process` from earlier phases) already include these keys; audit for consistency.

Affected: 16 existing `qor-*` skill files (exclude the 2 new stubs already frontmattered). No runtime behavior change.

### B.2 Full runtime wiring on qor-audit

Create `qor/scripts/qor_audit_runtime.py` with:

```python
def check_prior_artifact(session_id=None) -> GateResult
def should_run_adversarial_mode(platform_marker=None) -> bool
def emit_capability_shortfall(capability: str, session_id: str) -> str
```

`should_run_adversarial_mode`:
- Returns True only when `qplat.current()["detected"]["host"] == "claude-code"` AND `qplat.is_available("codex-plugin")`
- codex-plugin is Claude Code-specific (user confirmed pre-draft); skip even if declared on other hosts

Update `qor/skills/governance/qor-audit/SKILL.md` body to prepend:

- **Step 0 — Gate check**: Call `check_prior_artifact("audit")`. If `not found`, prompt user. On override, `emit_gate_override`.
- **Step 1.a — Mode selection**: `if should_run_adversarial_mode(): adversarial` else `solo + emit_capability_shortfall("codex-plugin")`.

Existing audit methodology body (security pass, razor pass, etc.) unchanged.

## Affected Files

### Task A
- 14 directories renamed (via `git mv`)
- `docs/SYSTEM_STATE.md`, `docs/SKILL_REGISTRY.md`, `README.md`: path updates post-rename + Qor→Qor text
- `qor/agents/**/*.md` (10 files): Qor/qor text
- `qor/skills/**/SKILL.md` + `references/**.md`: Qor/qor text
- `qor/platform/*.md`, `qor/platform/profiles/*.md`, `qor/gates/chain.md`: text
- `docs/plan-qor-phase[2-6]-*.md`, `docs/plan-qor-ssot-minimal.md`, `docs/plan-qor-tooling-deferred.md`: text
- `docs/CONCEPT.md`, `docs/ARCHITECTURE_PLAN.md`, `docs/BACKLOG.md`, `docs/SHIELD_SELF_AUDIT.md`, `docs/MERKLE_ITERATION_GUIDE.md`, `docs/SKILL_AUDIT_CHECKLIST.md`: text
- `qor/dist/**`: regenerated by compile.py

### Task B
- `qor/scripts/qor_audit_runtime.py` (new)
- 16 `qor/skills/<category>/qor-*/SKILL.md`: frontmatter keys added/reconciled
- `qor/skills/governance/qor-audit/SKILL.md`: prepended wiring steps
- `tests/test_qor_audit_runtime.py` (new)

## Unit Tests

- `tests/test_qor_audit_runtime.py`:
  - `test_check_prior_artifact_delegates_to_gate_chain`
  - `test_adversarial_true_only_when_claude_code_with_codex`
  - `test_adversarial_false_on_kilo_code_even_if_codex_declared` — user said codex is Claude Code-only; enforce
  - `test_adversarial_false_when_codex_absent`
  - `test_adversarial_false_when_no_platform_marker`
  - `test_emit_capability_shortfall_appends_sev2_event`
  - `test_emit_capability_shortfall_details_shape`

## Constraints

- Python 3.11+ stdlib + jsonschema (already runtime)
- Atomic writes via existing `shadow_process.append_event` / `os.replace`
- **No changes to META_LEDGER, SHADOW_GENOME, PROCESS_SHADOW_GENOME, manifests** — historical record integrity
- Frontmatter additions are additive only (no required-key changes to existing frontmatter shapes)

## Success Criteria

- [ ] Zero `qor-` or `qor-` references in non-excluded files (grep verifies)
- [ ] 14 directories renamed under `qor/skills/` + `qor/vendor/skills/`
- [ ] `qor/dist/` regenerated; drift check exits 0
- [ ] All 18 `qor-*` skills have `phase`, `gate_reads`, `gate_writes` frontmatter
- [ ] `qor-audit` SKILL.md prepended with Step 0 + Step 1.a wiring references
- [ ] `qor_audit_runtime.py` library + 7 tests green
- [ ] Full test suite 104/104 (97 existing + 7 new)
- [ ] Ledger chain verify OK (historical unchanged)
- [ ] Committed + pushed with `BUILD_REGEN=1` (dist changes)

## CI Commands

```bash
python -m pytest tests/ -v
python qor/scripts/check_variant_drift.py
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md
# Post-sweep verification:
! grep -r "Qor\|qor-\|qor-" docs/SYSTEM_STATE.md docs/SKILL_REGISTRY.md README.md qor/platform/ qor/gates/ qor/skills/ qor/agents/ 2>/dev/null
```
