# Plan: The seal stages what a seal commits, by executable

**iteration**: 1

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: `seal_stage` stages the fixed ceremony families and the session gate directory; implementation files (`src/`, `tests/`, `qor/scripts/`, `qor/skills/`, `qor/references/`) remain the implement phase's staging duty, exactly as today. Untracked noise outside the ceremony set is never staged.
- non_goals: No change to commit-message composition, trailer verification, tagging, or push steps. No `git add -A` (staging everything is the opposite of a documented ceremony).
- exclusions: GH #332, GH #320, GH #286, GH #341.

## Open Questions

None. The ceremony set is measured, not asserted: the union of the last six seal commits (research brief, ledger #606), plus `qor/specs/` per #337's Step 7.9 case.

## Locked Decisions

**LD-1: The enumerated block being replaced is the defect surface; its two lines become one invocation line, so the byte delta is negative against a 27-byte addition budget.**

```
git show v0.149.0:qor/skills/governance/qor-substantiate/SKILL.md | grep -nE 'git add CHANGELOG' -> 549:  git add CHANGELOG.md docs/CONCEPT.md docs/ARCHITECTURE_PLAN.md docs/META_LEDGER.md
```

**LD-2: The slack-floor contract is the binding constraint the enumerated fix cannot satisfy; this plan's mechanism must keep it green.**

```
git show v0.149.0:tests/test_substantiate_staging_gates.py | grep -nE 'slack >= 2700' -> 93:    assert slack >= 2700, (
```

**LD-3: The Phase 176 prose-shape test migrates deliberately.**

```
git show v0.149.0:tests/test_substantiate_staging_gates.py | grep -nE 'def test_step_9_5_stages' -> 37:def test_step_9_5_stages_the_sealed_gate_dir():
```

The test's contract (a seal must stage the session gate directory) is preserved and strengthened: the rewritten test binds Step 9.5's invocation line (`seal_stage` named with `$SESSION_ID`), and the gate-directory guarantee moves to the behavioral suite where it is proven by execution rather than by prose shape. The variant-equality test is untouched (Step 8.5 recompile satisfies it).

**LD-4: The ceremony set is a module constant, one name per line**, so the next family a future phase adds is a one-line diff reviewed as code: `CHANGELOG.md`, `README.md`, `pyproject.toml`, `docs/CONCEPT.md`, `docs/ARCHITECTURE_PLAN.md`, `docs/META_LEDGER.md`, `docs/SYSTEM_STATE.md`, `docs/BACKLOG.md`, `docs/GOVERNANCE_INDEX.md`, `docs/SHADOW_GENOME.md`, `docs/PROCESS_SHADOW_GENOME.md`, `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md`, `.agent/staging/AUDIT_REPORT.md`, the globs `docs/plan-qor-phase*.md` and `docs/research-brief-*.md`, the trees `qor/dist/` and `qor/specs/`, and `.qor/gates/<session>/`.

**LD-5: In-repo invocation uses the `python -m qor.scripts.seal_stage` fallback form** the Environment section already documents, avoiding the permanent installed-CLI drift on this host class.

## Phase 1: Bind the behavior (tests first)

### Affected Files

- `tests/test_seal_stage.py` - NEW; behavioral coverage in a tmp git repo.

### Unit Tests

- `test_ceremony_files_are_staged` - a tmp repo with dirty ceremony files (ledger, README, pyproject, a plan file, a research brief, the audit report, a gate-dir artifact) runs `seal_stage.stage(session_id, repo_root)`; `git diff --cached --name-only` lists every one of them.
- `test_noise_is_not_staged` - an unrelated untracked file (`scratch.txt`) and a dirty non-ceremony source file remain unstaged after the run.
- `test_missing_families_are_harmless` - a repo lacking optional families (no specs, no research brief) stages what exists and exits 0 (no error on absent paths).
- `test_gate_directory_is_staged_for_the_session` - the named session's `.qor/gates/<sid>/` contents are staged, another session's are not touched (the Phase 176 guarantee, now behavioral).
- `tests/test_substantiate_staging_gates.py::test_step_9_5_invokes_seal_stage` - REWRITE of `test_step_9_5_stages_the_sealed_gate_dir` per LD-3: the Step 9.5 bash block names `qor.scripts.seal_stage` and passes `"$SESSION_ID"`.

All red at v0.149.0 (module absent -> ImportError; block carries no invocation).

## Phase 2: The executable and the one-line block

### Affected Files

- `qor/scripts/seal_stage.py` - NEW; `CEREMONY_FILES`, `CEREMONY_GLOBS`, `CEREMONY_TREES` constants per LD-4; `stage(session_id, repo_root) -> list[str]` returning the staged paths; argparse `main` (`--session`, `--repo-root`); list-form `git add` invocations only, absent paths skipped.
- `qor/skills/governance/qor-substantiate/SKILL.md` - Step 9.5 block's two `git add` lines replaced with the single invocation line plus its one-sentence rationale; net byte change negative (LD-1 vs LD-2 arithmetic).

### Changes

Phase 1's five tests go green; the slack-floor and headroom tests stay green with more room than before; the variant-equality test goes green at Step 8.5 recompile time.

### Unit Tests

- Phase 1's five listed tests observed red-then-green.
- `tests/test_substantiate_staging_gates.py` remaining tests (headroom, slack floor, variant equality) observed green.

## Feature Inventory Touches

None. Governance tooling, ceremony documentation, tests.

## Definition of Done

### Deliverable 1: The staging ceremony is executable and complete

- **D1**: An operator or agent following the written ceremony produces a complete seal commit; the list can no longer silently drift from reality because it IS the mechanism.
- **D2**: `qor.scripts.seal_stage.stage(session_id, repo_root)` staging the LD-4 set; one invocation line in Step 9.5.
- **D3**: Implement-phase ledger entry cites this plan; seal binds this plan file; this phase's own seal is the first live exercise.
- **D4**: the four behavioral tests observed red at v0.149.0 and green after Phase 2.

### Deliverable 2: The size constraint is respected, not fought

- **D1**: The seal skill gains usable slack rather than spending it.
- **D2**: Step 9.5 block byte delta negative; file remains under the slack floor's bound with more room than at v0.149.0.
- **D4**: `test_ladder_rewrite_left_usable_slack` and `test_governance_skills_keep_headroom` observed green; byte counts recorded in the substantiate sweep.

## CI Commands

- `python -m pytest tests/ -q` -- full suite.
- `qor-logic-plus scripts plan_text_consistency_lint --check docs/plan-qor-phase229-seal-stage-executable.md` -- plan-internal consistency.
- `python -m qor.scripts.plan_grep_lint --plan docs/plan-qor-phase229-seal-stage-executable.md --repo-root .` -- citation truth check.
