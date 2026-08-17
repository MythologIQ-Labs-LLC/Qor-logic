# Research Brief

**Date**: 2026-08-17
**Analyst**: The Qor-logic Analyst
**Target**: GH #337 (the documented seal staging block omits files every seal commits)
**Scope**: the true seal-commit file inventory, derived from history; the size-budget constraint that forbids the enumerated fix; the structural alternative

---

## Executive Summary

The Step 9.5 `git add` block names 8 path families; the union of the last six seal commits (measured via `git show --name-only`) contains 13: additionally `README.md`, `pyproject.toml`, `docs/GOVERNANCE_INDEX.md`, `docs/SHADOW_GENOME.md`, `docs/PROCESS_SHADOW_GENOME.md` (+ `_UPSTREAM`), the phase plan, research briefs, `.agent/staging/AUDIT_REPORT.md`, and `qor/dist/` -- confirming and extending #337's five. The enumerated fix is arithmetically impossible: `test_ladder_rewrite_left_usable_slack` requires >= 2,700 B slack under the 39 KB bound and the file sits at 37,209 B, leaving a 27-byte addition budget against a ~300-byte enumeration. The fix that both fits and ends the rot class: a NEW `qor.scripts.seal_stage` module stages the complete ceremony set programmatically, the Step 9.5 block shrinks to one invocation line (net-negative bytes), and the staging list becomes tested code instead of prose that drifts.

## Findings

### 1. True inventory (by execution over the last six seal commits)

Ceremony families present in seal commits but absent from the documented block: `README.md` (badge regeneration, all seals), `pyproject.toml` (version bump, all seals), `docs/GOVERNANCE_INDEX.md` (Last-Reviewed advance, all seals), `docs/SHADOW_GENOME.md` and `docs/PROCESS_SHADOW_GENOME*.md` (VETO entries and process events), `docs/plan-qor-phase*.md` and `docs/research-brief-*.md` (seal binds the plan; brief cited by ledger), `.agent/staging/AUDIT_REPORT.md` (final report), `qor/dist/` (Step 8.5 recompile output, 7 occurrences), `qor/specs/` (when Step 7.9 folds; per #337). Documented-and-real: `CHANGELOG.md`, `docs/CONCEPT.md`, `docs/ARCHITECTURE_PLAN.md`, `docs/META_LEDGER.md`, `docs/SYSTEM_STATE.md`, `docs/BACKLOG.md`, `src/` (implementation staging duty), `.qor/gates/$SESSION_ID/`.

### 2. The size-budget wall

- `tests/test_substantiate_staging_gates.py::test_ladder_rewrite_left_usable_slack` (Phase 222; GH #327): slack floor 2,700 B under the 39,936 B headroom bound. Current file 37,209 B; addition budget 27 B.
- Same file pins the block's shape: `test_step_9_5_stages_the_sealed_gate_dir` requires a `git add` line naming `.qor/gates/$SESSION_ID`; `test_variants_match_canonical_step_9_5` requires dist-variant equality (satisfied automatically by Step 8.5 recompile). The first is a deliberate-update candidate if the block's mechanism changes; #337 itself warns that partial enumeration "looks corrected and is still wrong."

### 3. Structural alternative

`qor.scripts.seal_stage`: stages the fixed ceremony set plus the session gate directory; invoked from Step 9.5 as one line (`python -m qor.scripts.seal_stage --session "$SESSION_ID"`); behaviorally tested in a tmp git repo (ceremony files staged, unrelated noise not staged, unchanged files harmless). The Phase 176 gate-dir contract migrates from prose-shape ("a git add line mentions the dir") to behavior ("the executable stages the dir"), a strictly stronger guarantee. The in-repo invocation uses the `python -m` fallback form the Environment section already documents, avoiding installed-CLI drift (the permanent install-drift condition on this host).

### 4. Rot-class closure

Enumerations in prose drift silently -- #337 is the third instance of the family (staging block, doctrine kind ceilings, veto_pattern conventions). Executable-plus-behavioral-test is the same remedy Phases 225 and 227 applied to the other two.

## Blueprint Alignment

| Claim | Actual Finding | Status |
|---|---|---|
| #337: five omitted files | Measured: five confirmed plus four more families (README/pyproject/GOVERNANCE_INDEX/dist) | MATCH, extended |
| #337: partial completion worse than staleness | The 27-byte budget makes even partial enumeration infeasible; the structural fix avoids the trap entirely | MATCH |

## Recommendations

1. Phase 229 (feature): `seal_stage` module + behavioral tests + one-line Step 9.5 block (net-negative bytes) + deliberate update of `test_step_9_5_stages_the_sealed_gate_dir` to bind the invocation line and delegate the gate-dir guarantee to the behavioral suite.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
