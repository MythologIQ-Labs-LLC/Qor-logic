# AUDIT REPORT

**Tribunal Date**: 2026-09-28
**Target**: `docs/plan-qor-phase299-session-marker-staleness.md`
**Iteration**: 1 (branch `phase/299-session-marker-staleness`, head `2e880e4c`, plan-only; base `main` `8ee9d98a` = 0.175.2)
**Session**: `2026-09-28T0026-1e38ee`
**Risk Grade**: L2
**Auditor**: The Qor-logic Judge
**Mode**: Option B fresh-context reviewer, independent of the plan author. `audit_risk_score`: `option_b_required: true` (flag `high-citation-surface`). Codex plugin unavailable; `external_reviewer.run_external_review` returned `fallback` (no reviewer configured in `.qorlogic/config.json`); both `capability_shortfall` events emitted. Reviewer toolset declaration: shell, git (local objects plus `git ls-remote` over the proxy), file read/grep, Python with the in-tree `qor` package on `PYTHONPATH`, pytest in scratch clones outside the repository; no GitHub API. The candidate branch `fix/483-session-marker-current` (`5f8be1e2`) was read as reference only; it carries no audit authority.

---

## VERDICT: VETO

---

### Executive Summary

The carried substance mostly holds. All 44 `git show 8ee9d98...:<path> | grep -nE` evidence statements were re-executed and reproduce exactly. Provenance claims reproduce: the candidate is not an ancestor of the base, its diff against merge base `15729311` is the declared four files (`250 insertions(+), 7 deletions(-)`), and `session.py` and `docs/lifecycle.md` are unchanged between `15729311` and the base. In a scratch clone of the base, the Judge rebuilt the eight Phase 1 tests (the candidate's seven plus the declared eighth). The base gives `2 failed, 6 passed`. With the candidate logic it gives `8 passed` twice. Each of mutations M1 to M5 fails exactly the tests the plan names. An end-to-end run on the real `gate_chain` with a session id created before a day boundary and a marker aged 26 h behaves as intended. At the base, `current()` is `None` and `qor_audit_runtime.session_id()` splits to a new id whose directory lacks `plan.json`. With the fix, both return the original id, `check_prior_artifact("audit")` finds the plan and the marker mtime is refreshed. A sealed session still rotates. The release-state continuity proof is non-vacuous. The CI-view simulation prints `{'0.175.2'} {'0.175.2'}` at the base. The guarded clone proof fails at the base, fails on a bump-only commit, fails on a simulated seal without the entry (`1 failed, 3 passed`, orphan `0.175.2`), and passes with the entry (`4 passed`, twice). The remote's highest tag is `v0.172.2`. Scope stays hotfix. Three grounds remain. V1: the one guard that keeps marker content from becoming a path segment on the new recovery path is not tested. Deleting it leaves all 1263 session-related tests green, and `get_or_create()` then returns `../../evil` as the session id. V2: the lifecycle wording the plan mandates is contradicted by the plan's own rule and eighth test. The plan also leaves `qor/gates/chain.md` stating the old 24 h rule while asserting that only two lines change. V3: the liveness tuple omits `ideation.json`, which `gate_chain` treats as a chain predecessor. An ideation-only cycle that outlives the TTL is still split, which is the #483 failure.

### Pre-audit gates

- Governance health preflight (`python -m qor.cli governance-health --profile skill-entry`): all 8 artifacts OK.
- Step 0 gate check: plan artifact found and valid (`.qor/gates/2026-09-28T0026-1e38ee/plan-iter1.json`).
- Step 0.3 `plan_iteration_status_lint`: exit 0.
- Step 0.4 unchanged-plan short-circuit: `should_skip=False` (no prior audit in session); plan hash `b270cf06ceb32ee65ffcf6f0b63517c72bb949e84a7fbdef7003e38a4e1311cc`.
- Step 0.5 cycle-count escalator: `cce.check` None, `cce.check_session_total` None.
- Step 0.6 lints (WARN-only): `plan_grep_lint` 44 citations truth-checked, 0 findings; `workspace_fragility_check` medium (`dirty_gate_artifact_count=64`, pre-existing); `sg_closure_lint` 40 entries, 0 missing; `gate_schema_freeze_lint` 0; `publication_boundary_lint` 0 findings. All other lints: exit 0, no output.
- Step 0.7 spec-delta pre-pass: no `spec_deltas` declared; the contracted behavior (session marker rule) is carried by `docs/lifecycle.md` and `qor/gates/chain.md`, addressed under V2.
- Version-Applicability Pass: `ok=True`, `hotfix`, target v0.175.3 > current highest v0.175.2.
- Prompt Injection Pass: `prompt_injection_canaries` over ARCHITECTURE_PLAN, META_LEDGER, CONCEPT and the plan: exit 0.
- Runtime Contract Walk (WARN-only): 6 backward WARN findings on unchanged caller modules; no forward finding.
- `prose_test_lint --enforce`: exit 0 (69 exempted with reason).

### Audit Results

#### Security Pass
**Result**: PASS (design) -- see V1 for the untested guard
No placeholder auth, credentials, or bypassed checks. The design validates marker content against `SESSION_ID_PATTERN` before `_workdir.gate_dir() / session_id` (LD-2).

#### OWASP Top 10 Pass
**Result**: PASS (design)
No subprocess, deserialization, or secrets. The path-segment guard (A01/A03 class) is present in the design, but no test protects it (V1). `gate_chain.check_prior_artifact` and `write_gate_artifact` build `GATES_DIR / sid` without `validate_session_id`, so this guard is the only protection on that path.

#### Ghost UI Pass
**Result**: PASS
No UI surface.

#### Section 4 Razor Pass
**Result**: PASS

| Check              | Limit | Blueprint Proposes | Status |
| ------------------ | ----- | ------------------ | ------ |
| Max function lines | 40    | ~20 (`current`)    | OK     |
| Max file lines     | 250   | ~172 (`session.py`), ~129 (test) | OK |
| Max nesting depth  | 3     | 2                  | OK     |
| Nested ternaries   | 0     | 0                  | OK     |

#### Self-Application Sub-Pass
**Result**: FAIL (V2, V3)
`originating_remediation` is `GH #483`. The plan's own discipline has two parts. LD-6 says documentation must state the new rule, and LD-3 says a live chain must not be split by the clock. Applied to the plan itself, both fail: one normative document stays false (V2), and one chain predecessor is left out (V3).

#### Test Functionality Pass
**Result**: FAIL (V1)

| Test description | Invokes unit? | Asserts on output? | Verdict |
| ---------------- | ------------- | ------------------ | ------- |
| stale unsealed -> `current()` returns id | yes | yes | PASS |
| stale unsealed -> `get_or_create()` reuses id | yes | yes | PASS |
| reuse refreshes mtime | yes | yes | PASS |
| sealed dir rotates | yes | yes | PASS |
| no gate dir rotates | yes | yes | PASS |
| absent marker unaffected | yes | yes | PASS |
| fresh marker unaffected | yes | yes | PASS |
| empty gate dir rotates | yes | yes | PASS |
| stale marker with non-pattern content rotates | not planned | -- | coverage-gap (V1) |

Every planned test is functional, but the planned set leaves out a declared, security-relevant behavior (V1).

#### Dependency Pass
**Result**: PASS
No new dependencies.

#### Macro-Level Architecture Pass
**Result**: PASS
The local artifact tuple avoids the `gate_chain` -> `session` import cycle (verified: `gate_chain.py:15`). Callers unchanged (LD-4).

#### Feature Test Coverage Pass
**Result**: PASS (exempt)
`feature_inventory_touches: []`; `docs/FEATURE_INDEX.md` has no session row.

#### Infrastructure Alignment Pass
**Result**: FAIL (V3)
All 44 citations reproduce. The run observations reproduce too: `2 failed, 6 passed` at the base, M1 to M5 as named, `1263 passed, 4 deselected` over the session-related files, and the CI-view and clone-proof outcomes. The phase-artifact set does not match the chain `gate_chain` actually resolves (V3).

#### Filter-Stage Ordering Coherence
**Result**: PASS
The stages run in this order: marker state, then pattern match, then liveness, then reuse or rotation. The pattern check precedes the path build in both `current` and `_recoverable_stale_id`.

#### Orphan Pass
**Result**: PASS
The new test file is collected by pytest. `session.py` is already on the build path.

### Violations Found

| ID | Category | Location | Description |
| -- | -------- | -------- | ----------- |
| V1 | coverage-gap | plan Phase 1 Unit Tests; LD-2; boundaries.exclusions; Deliverable 1 D1 | The `SESSION_ID_PATTERN` guard on the new stale-recovery path has no discriminating test. Mutation M6 deletes the pattern check in `_recoverable_stale_id`. Under M6, the 8-test file, `tests/test_gates.py` and `tests/test_e2e.py` give `47 passed`, and all 150 session-related test files give `1263 passed, 4 deselected`. In a scratch run with a stale marker reading `../../evil` and `<root>/evil/plan.json` present, `get_or_create()` returns `'../../evil'` under M6 and a fresh id with the guard. |
| V2 | specification-drift | plan LD-6 and Phase 2 (`docs/lifecycle.md` line 68 text); `qor/gates/chain.md:20` | The mandated lifecycle sentence says a new id is issued "only if" the gate directory "is absent, or already sealed via `substantiate.json`", and otherwise the id is reused. The plan's own D1 and its eighth test (`test_stale_valid_marker_with_empty_gate_dir_still_rotates`) rotate an existing, unsealed, empty directory, and the code also rotates a directory holding only non-phase files. The document would therefore misstate the implemented rule. Separately, `qor/gates/chain.md:20` ("regenerated if older than 24h") becomes false, while LD-6 asserts "Only these two lines change". |
| V3 | infrastructure-mismatch | plan LD-2 / LD-3 / Phase 2 `_GATE_PHASE_ARTIFACTS` | `gate_chain` accepts `ideation.json` as the predecessor of research and plan (`gate_chain.py:24-29`, `IDEATION_PHASE`; `check_prior_artifact` lines 64-86). LD-2 cites `CHAIN` at line 28 but not this predecessor, and the tuple omits it. Reproduced with the candidate logic: a session holding only `ideation.json` with a 26 h marker gives `current()` None, `get_or_create()` issues a new id, and `check_prior_artifact("plan")` in the new id reports the prior artifact missing. LD-3 says the fix "never issues a second id for an in-flight phase". The limitations boundary lists the four artifacts but does not disclose this remaining #483 path. |

### Per-ground directives (if VETO)

#### Plan-text

V1: the plan declares that invalid marker content keeps the base behavior (boundaries.exclusions, D1) and relies on the pattern check as the path-safety guard (LD-2), yet no planned test fails when that guard is removed. V2: the prescribed `docs/lifecycle.md` sentence contradicts the plan's own rule and test, and a second normative statement of the old rule (`qor/gates/chain.md:20`) is left out of Affected Files while LD-6 asserts completeness. V3: the liveness artifact set omits the `ideation.json` chain predecessor that `gate_chain` resolves, with no declared residual. The plan's claim that the recovery keeps one gate chain is therefore not true for every in-flight chain.

**Required next action:** Governor: amend plan text, re-run `/qor-audit`

### Advisories (non-VETO)

- **A1** LD-5 residual scope. Under the fix, `/qor-plan` Step 0 (`session.get_or_create()`) run after an abandoned, unsealed cycle older than the TTL no longer starts a new session. The new phase's artifacts land in the old session directory, and session-scoped counters (`cycle_count_escalator.check_session_total`, audit history) then span two phases. `verdict_reconcile` target binding limits wrong-plan PASS reuse. The plan describes the residual only as "stays current until an operator ends or rotates it".
- **A2** `MARKER_PATH` (`session.py`) and `GATES_DIR` (`gate_chain.py:21`) are fixed at import, while the new `_has_unsealed_gate_artifacts` resolves `_workdir.gate_dir()` at call time. `current(marker=X)` also judges liveness against the cwd root, not X's root. A process that changes cwd or `QOR_ROOT` after import can judge liveness against a different gates directory than `gate_chain` reads.
- **A3** LD-4 counts "149 test files ... the Phase 1 file among them"; the Judge's `grep -l -E 'session|lifecycle\.md' tests/*.py` with the Phase 1 file present selects 150, with the identical `1263 passed, 4 deselected`.
- **A4** `workspace_fragility_check` reports medium (64 dirty gate-artifact directories across the repository). This is pre-existing.

## Documentation Drift

<!-- qor:drift-section -->
(clean)

## Process Pattern Advisory

<!-- qor:veto-pattern-advisory -->

No repeated-VETO pattern detected in the last 2 sealed phases.

### Report Hash

SHA256(this_report) is recorded as the Content Hash of the GATE TRIBUNAL entry in `docs/META_LEDGER.md` (a report cannot contain its own hash).

---
_This verdict is binding._
