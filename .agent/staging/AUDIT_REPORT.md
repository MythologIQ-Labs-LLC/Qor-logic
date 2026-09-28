# AUDIT REPORT

**Tribunal Date**: 2026-09-28
**Target**: `docs/plan-qor-phase299-session-marker-staleness.md`
**Iteration**: 3 (branch `phase/299-session-marker-staleness`, head `0c0d0420`, plan-only; base `main` `8ee9d98a` = 0.175.2)
**Session**: `2026-09-28T0026-1e38ee`
**Risk Grade**: L2
**Auditor**: The Qor-logic Judge
**Mode**: Option B fresh-context reviewer, independent of the plan author and of both prior auditors. `audit_risk_score`: `option_b_required: true` (flag `high-citation-surface`). Codex plugin unavailable. `external_reviewer.run_external_review` returned `fallback` because no reviewer is configured. Both `capability_shortfall` events were emitted. Reviewer toolset declaration: shell, git (local objects plus `git ls-remote` over the proxy), file read/grep, Python with the in-tree `qor` package on `PYTHONPATH`, and pytest in scratch clones outside the repository. No GitHub API. The candidate head `5f8be1e2` was read as reference only.

---

## VERDICT: VETO

---

### Executive Summary

Both iteration-2 grounds are closed as written, and so is the new doctrine correction. The Judge rebuilt the 29-item Phase 1 file from the plan text alone, in a scratch clone of the base outside the repository. At the base it gives `10 failed, 19 passed`, with exactly the ten named items failing. With the Phase 2 `session.py` it gives `29 passed`, twice. Each of M1 to M15 fails exactly the tests the plan names, with the stated counts. Over the 150 session-related files, M10 gives `2 failed, 1282 passed` and M11 gives `3 failed, 1281 passed`, and the file gives `1284 passed` without them. Every age-rule clause was executed and holds. All 57 `git show` citations reproduce at `8ee9d98`. With Phases 1 and 2 applied, the full suite gives `3611 passed, 3 skipped` and variant drift is clean. The release-state proofs reproduce. One ground remains. The plan mandates verbatim CHANGELOG text, and one clause in it contradicts LD-3 and two of the plan's own tests. The plan also asserts that every clause of that text matches.

### Pre-audit gates

- Governance health preflight (`python -m qor.cli governance-health --profile skill-entry`): all 8 artifacts OK.
- Step 0 gate check: plan artifact found and valid (`.qor/gates/2026-09-28T0026-1e38ee/plan-iter3.json`).
- Step 0.3 `plan_iteration_status_lint`: exit 0.
- Step 0.4 unchanged-plan short-circuit: `should_skip=False`; plan hash `cfc319c922426b6f792150d108d11016f7e525f12980157d5099127cc182b05d`. Iteration 2 audited `7f527185...`.
- Step 0.5 cycle-count escalator: `cce.check` returned None and `cce.check_session_total` returned None, so the escalator did not fire. `stall_walk.run` gives a consecutive count of 1. The two prior VETOs have different findings signatures (`ef42868df40386e5` for `coverage-gap`, `specification-drift`, `infrastructure-mismatch`; `3de72aeb48f32473` for `coverage-gap`, `specification-drift`), and each has a session total of 1. The threshold is K=3.
- Step 0.6 lints (WARN-only): `plan_grep_lint` truth-checked 57 citations with 0 findings. `workspace_fragility_check` reports medium (`dirty_gate_artifact_count=64`, pre-existing). `sg_closure_lint`: 40 entries, 0 missing. `gate_schema_freeze_lint`: 0. `publication_boundary_lint`: 0 findings. All other lints exited 0 with no output.
- Step 0.7 spec-delta pre-pass: no `spec_deltas` are declared. No `qor/specs/*/spec.md` contracts session-marker behavior. The rule lives in `docs/lifecycle.md` and `qor/gates/chain.md`, and the plan edits both.
- Version-Applicability Pass: `ok=True`, `hotfix`, target v0.175.3 > current highest v0.175.2.
- Prompt Injection Pass: `prompt_injection_canaries` over ARCHITECTURE_PLAN, META_LEDGER, CONCEPT and the plan exited 0.
- Runtime Contract Walk (WARN-only): 6 backward WARN findings on unchanged caller modules; no forward finding.
- `prose_test_lint --enforce`: exit 0 (69 exempted with reason).

### Iteration-2 grounds and new in-scope items (verification)

| Ground | Check | Observed | Status |
| ------ | ----- | -------- | ------ |
| #820 V1 | Set-equality test; non-pre-seal rotate test over `remediate.json`, `validate.json`, `audit_history.jsonl`, `notes.json`; M10, M11 | M10 fails the equality test and `[remediate.json]` (`2 failed, 27 passed`). M11 fails `[remediate.json]`, `[validate.json]` and `[notes.json]` (`3 failed, 26 passed`). M12 fails all four cases, and M3 fails the four cases plus the empty-dir test. With `review` inserted into `gate_chain.CHAIN` before `substantiate`, `[review]` and the equality test fail (`2 failed, 28 passed`). | Closed |
| #820 V2 | Every surface states the age rule: stale 24h after the last write, reads do not refresh, `get_or_create` refreshes on keep | Executed with the real `gate_chain` and `QOR_ROOT` set to scratch. A 23 h marker is still 23.0 h old after three rounds of `get_or_create`, `current` and `check_prior_artifact`. `_marker_state` returns `stale` at exactly 24 h and `fresh` 1 s earlier. At 25 h with no gate dir, `current()` returns None. At 25 h with `plan.json`, `current()` returns the id and leaves the mtime unchanged, and `get_or_create()` returns the id and leaves the marker 0.0 h old. The lifecycle, chain.md and docstring replacements apply verbatim, each on one ASCII line. | Closed |
| doctrine:109 | `session new` replaced by `session_tool rotate` | At the base, `session new` on a fresh marker prints the same id. With the fix, on a 25 h live marker, `session new` prints the same id and `session_tool rotate` prints `rotated session: <old> -> <new>`. `session end` then `session new` gives a different id. The wet rotate is already tested (`tests/test_dry_run_modes.py:137`). No `qor/dist` copy exists. The six doctrine-naming test files give `43 passed`. | Closed |
| M13-M15 | No-refresh tests; fresh malformed items | M13 fails `test_reads_of_a_fresh_marker_do_not_refresh_it`. M14 fails `test_current_on_a_stale_live_marker_does_not_refresh_it`. M15 fails exactly the four `fresh` malformed items. M6 fails the four `stale` items, and M7 fails all eight. | Closed |

### Audit Results

#### Security Pass
**Result**: PASS
No placeholder auth, credentials or bypassed checks. The `SESSION_ID_PATTERN` guard runs before any gate-directory lookup in `_recoverable_stale_id` and `current`, and in the fresh branch of `get_or_create`. M6, M7 and M15 pin all three.

#### OWASP Top 10 Pass
**Result**: PASS
The product change has no subprocess, deserialization or secrets. The path-segment guard is tested with the traversal and absolute-path cases, and a live-looking target directory is planted for each.

#### Ghost UI Pass
**Result**: PASS
No UI surface.

#### Section 4 Razor Pass
**Result**: PASS

| Check              | Limit | Blueprint Proposes | Status |
| ------------------ | ----- | ------------------ | ------ |
| Max function lines | 40    | ~16 (`get_or_create`) | OK  |
| Max file lines     | 250   | 172 (`session.py`) | OK |
| Max nesting depth  | 3     | 2                  | OK     |
| Nested ternaries   | 0     | 0                  | OK     |

#### Self-Application Sub-Pass
**Result**: FAIL (V1)
`originating_remediation` is `GH #483`. The discipline the plan introduces is LD-6's rule that every normative statement of the marker rule matches the implemented rule, plus the iteration-3 claim that each clause is exact. Applied to the plan's own mandated CHANGELOG text, one clause is false for fresh markers (V1).

#### Test Functionality Pass
**Result**: PASS

| Test description | Invokes unit? | Asserts on output? | Verdict |
| ---------------- | ------------- | ------------------ | ------- |
| stale unsealed: `current()` / `get_or_create()` keep the id | yes | yes | PASS |
| reuse refreshes mtime | yes | yes | PASS |
| sealed / no-dir / empty-dir rotate | yes | yes | PASS |
| absent / fresh marker unaffected | yes | yes | PASS |
| malformed content rotates (4 x 2) | yes | yes | PASS |
| ideation-only live; per-phase liveness (5) | yes | yes | PASS |
| liveness set equals pre-seal chain set (both directions) | yes | yes | PASS |
| non-pre-seal-only directory rotates (4) | yes | yes | PASS |
| fresh reads / stale-live `current()` do not refresh | yes | yes | PASS |

#### Dependency Pass
**Result**: PASS
No new dependencies.

#### Macro-Level Architecture Pass
**Result**: PASS
The local tuple avoids the `gate_chain` -> `session` import cycle (`gate_chain.py:15`), and the tests pin set equality in both directions. The callers are unchanged.

#### Feature Test Coverage Pass
**Result**: PASS (exempt)
`feature_inventory_touches: []`.

#### Infrastructure Alignment Pass
**Result**: PASS
The Judge re-ran all 57 `git show 8ee9d98...:<path> | grep -nE` statements by script. Each prints exactly one line, and every line matches. The prose claims also reproduce:
- `gate_chain.py` lines 206 and 288 both read `sid = session_id or session.get_or_create()`.
- `_marker_fresh` has 3 hits.
- The candidate diff is 4 files, `250 insertions(+), 7 deletions(-)`, and the candidate is not an ancestor of the base (exit 1).
- The four ported files are identical from `15729311` to the base.
- The completeness grep prints 3 lines, and a wider grep finds no other statement of the marker rule. `qor/dist` has 0 hits.
- `docs/operations.md` lines 131 and 132 hold `session.py end` and `session.py new`.
- The Entry #818 sentence is on lines 24134 and 24228, and the local `v0.175.2` tag is an ancestor of the base.
- The highest remote tag is `v0.172.2`.

The end-to-end check also reproduces. With a 26 h marker and an ideation-only session, the base code issues a new id and reports `prior-phase artifact missing`. With the fix, both calls keep the id and `check_prior_artifact("plan")` resolves `ideation.json` in the original directory. The Phase 3 proofs reproduce:
- The CI-view simulation prints `{'0.175.2'} {'0.175.2'}` at the base and `set() {'0.175.2'}` with the entry. `test_release_state` and tag coverage give `29 passed`.
- On a simulated seal commit, the guarded clone proof exits 0 (`4 passed`) with the entry. It exits 1 without the entry (orphan assertion) and exits 1 at the base (guard FAIL).

#### Filter-Stage Ordering Coherence
**Result**: PASS
The stages run in this order: marker state, pattern match, directory and seal check, pre-seal membership. No stage runs before its precondition.

#### Orphan Pass
**Result**: PASS
The new test file is collected, and `session.py` is on the build path.

### Violations Found

| ID | Category | Location | Description |
| -- | -------- | -------- | ----------- |
| V1 | specification-drift | plan LD-9 (CHANGELOG bullet, "exactly this text"), sentence "A marker with malformed content, or one naming an absent, empty or sealed directory or a directory with no pre-seal phase artifact, still rotates to a new id."; LD-9 claim "every clause matches LD-1, LD-2, LD-3, LD-5 and LD-10"; DoD D3 ("carries exactly the LD-9 text") | The subject of the sentence is "A marker", not "a stale marker". It deliberately has no age qualifier, because the malformed-content clause applies at any age (the plan tests malformed content at 25 h and at 1 h). As a result, "one naming an absent, empty or sealed directory or a directory with no pre-seal phase artifact" also covers fresh markers, and for a fresh marker with valid content that clause is false before and after this fix. LD-3 states that on a fresh valid marker, `current` and `get_or_create` both return the id. `test_fresh_marker_is_unaffected` (fresh marker, no gate dir) and `test_reads_of_a_fresh_marker_do_not_refresh_it` pin that. Reproduced with the Phase 2 `session.py`: a 1 h marker naming an absent, empty, remediate-only or sealed directory keeps its id from both `current()` and `get_or_create()`. None of them rotates. A fresh marker naming an absent directory is the normal state after every seal's `session.rotate()`, and the user-facing note tells operators that this state rotates. DoD D1 correctly scopes the same list to "stale markers naming ...", and so do the lifecycle, chain.md and docstring texts. Only the CHANGELOG sentence drops the qualifier, while LD-9 asserts that every clause matches. This is the failure class of #820 V2: a mandated verbatim sentence whose clause does not match the implemented rule. |

### Per-ground directives (if VETO)

#### Plan-text

V1: the LD-9 CHANGELOG bullet, which D3 mandates verbatim, says that a marker naming an absent, empty, sealed or no-pre-seal-artifact directory "still rotates to a new id". That holds only for a stale marker. A fresh marker with valid content keeps its id whatever its directory holds, as LD-3 and two planned tests state. The plan's claim that every clause matches LD-3 is therefore false.

**Required next action:** Governor: amend plan text, re-run `/qor-audit`

### Advisories (non-VETO)

- **A1** The Phase 2 docstring line 8 says a stale id is kept when its "gate dir holds unsealed phase work". A remediation-only directory also holds phase work, but it rotates (LD-2). "Phase work" is undefined here, so this is imprecise rather than false. Recorded, not a ground.
- **A2** The LD-9 bullet tells operators to run `python qor/scripts/session.py end`, a source-tree path that exists only in a Qor-logic checkout. The same bullet uses the module form for `session_tool`. This matches the existing `docs/operations.md` convention.
- **A3** `workspace_fragility_check` reports medium (64 dirty gate-artifact directories across the repository). This is pre-existing.

## Documentation Drift

<!-- qor:drift-section -->
(clean)

## Process Pattern Advisory

<!-- qor:veto-pattern-advisory -->

No repeated-VETO pattern detected in the last 2 sealed phases.

### Report Hash

SHA256(this_report) is recorded as the Content Hash of the GATE TRIBUNAL entry in `docs/META_LEDGER.md`. A report cannot contain its own hash.

---
_This verdict is binding._
