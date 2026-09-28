# AUDIT REPORT

**Tribunal Date**: 2026-09-28
**Target**: `docs/plan-qor-phase299-session-marker-staleness.md`
**Iteration**: 2 (branch `phase/299-session-marker-staleness`, head `b5f636f1`, plan-only; base `main` `8ee9d98a` = 0.175.2)
**Session**: `2026-09-28T0026-1e38ee`
**Risk Grade**: L2
**Auditor**: The Qor-logic Judge
**Mode**: Option B fresh-context reviewer, independent of the plan author and of the iteration-1 auditor. `audit_risk_score`: `option_b_required: true` (flag `high-citation-surface`). Codex plugin unavailable; `external_reviewer.run_external_review` returned `fallback` (no reviewer configured); both `capability_shortfall` events emitted. Reviewer toolset declaration: shell, git (local objects plus `git ls-remote` over the proxy), file read/grep, Python with the in-tree `qor` package on `PYTHONPATH`, pytest in scratch clones outside the repository; no GitHub API. The candidate branch head `5f8be1e2` was read as reference only.

---

## VERDICT: VETO

---

### Executive Summary

The three iteration-1 grounds are closed as written. V1: the Judge rebuilt the 18-item Phase 1 file from the plan text in a scratch clone of the base. The base gives `8 failed, 10 passed`; with the Phase 2 `session.py` it gives `18 passed` twice. M6 and M7 each fail exactly the four malformed-content cases, and M6 over the 150 session-related files gives `4 failed, 1269 passed, 4 deselected`. V2: the four replacement lines apply verbatim, and a repository grep finds no other normative statement of the old rule. V3: `ideation.json` is in the tuple, and the parametrized drift test fails when `gate_chain.CHAIN` gains a pre-seal phase (simulated `review`: `1 failed, 18 passed`). End to end on the real `gate_chain`, an ideation-only session with a 26 h marker keeps its id and `check_prior_artifact("plan")` finds `ideation.json`; at the base it splits. All 55 evidence statements reproduce at `8ee9d98`, M1 to M9 match their named failures and counts, and the full suite with Phases 1 and 2 applied gives `3600 passed, 3 skipped`. The release-state proofs reproduce as well. Two grounds remain. First, the amendment makes "a directory with no pre-seal phase artifact rotates" a normative rule, but no test discriminates it: two mutations that widen liveness beyond the chain set keep all 1273 session-related tests green. Second, the lifecycle text keeps "After 24h of inactivity", but the plan asserts every clause matches `_marker_state`, which measures age since the last marker write.

### Pre-audit gates

- Governance health preflight (`python -m qor.cli governance-health --profile skill-entry`): all 8 artifacts OK.
- Step 0 gate check: plan artifact found and valid (`.qor/gates/2026-09-28T0026-1e38ee/plan-iter2.json`).
- Step 0.3 `plan_iteration_status_lint`: exit 0.
- Step 0.4 unchanged-plan short-circuit: `should_skip=False`; plan hash `7f5271858e65004554fb5ab1efedda3b832cc41d453a70c3f7a235b882ed4686` (iteration 1 audited `b270cf06...`).
- Step 0.5 cycle-count escalator: `cce.check` None, `cce.check_session_total` None. This is the second audit in the session; the prior VETO (#819) carried categories `coverage-gap`, `specification-drift`, `infrastructure-mismatch`.
- Step 0.6 lints (WARN-only): `plan_grep_lint` 55 citations truth-checked, 0 findings; `workspace_fragility_check` medium (`dirty_gate_artifact_count=64`, pre-existing); `sg_closure_lint` 40 entries, 0 missing; `gate_schema_freeze_lint` 0; `publication_boundary_lint` 0 findings. All other lints: exit 0, no output.
- Step 0.7 spec-delta pre-pass: no `spec_deltas` declared; the contracted rule is carried by `docs/lifecycle.md` and `qor/gates/chain.md`, which the plan edits (see V2).
- Version-Applicability Pass: `ok=True`, `hotfix`, target v0.175.3 > current highest v0.175.2.
- Prompt Injection Pass: `prompt_injection_canaries` over ARCHITECTURE_PLAN, META_LEDGER, CONCEPT and the plan: exit 0.
- Runtime Contract Walk (WARN-only): 6 backward WARN findings on unchanged caller modules; no forward finding.
- `prose_test_lint --enforce`: exit 0 (69 exempted with reason).

### Iteration-1 grounds (verification)

| Ground | Check | Observed | Status |
| ------ | ----- | -------- | ------ |
| V1 | 4-case malformed-content test; M6, M7 | Each of M6 and M7 fails all four cases (`4 failed, 14 passed`). M6 over 150 files gives `4 failed, 1269 passed, 4 deselected`. Without M6/M7, `18 passed` twice. | Closed |
| V2 | Exact lines `docs/lifecycle.md:68`, `qor/gates/chain.md:20`, `session.py:7-8` | All four apply verbatim and are ASCII. A `git grep` at `8ee9d98` over `qor`, `docs`, `README.md` and `tests` (excluding dated plans, ledgers and vendored text) finds no other statement of the 24 h marker rule. The 7 chain/lifecycle test files plus `test_gates`/`test_e2e` give `95 passed`. | Closed (see new V2) |
| V3 | `ideation.json` in the tuple; drift test; ideation-only end to end | M8 gives `2 failed`, M9 `1 failed`. With `review` added to `CHAIN`, `[review]` fails. End to end at the base: `current()` None, new id, plan prior missing. With the fix: same id from both calls, `ideation.json` found, marker refreshed. | Closed |

### Audit Results

#### Security Pass
**Result**: PASS
No placeholder auth, credentials or bypassed checks. The `SESSION_ID_PATTERN` guard precedes every gate-directory lookup on the stale path in both `current` and `_recoverable_stale_id`, and it is now pinned by M6/M7.

#### OWASP Top 10 Pass
**Result**: PASS
No subprocess, deserialization or secrets in the product change. The path-segment guard (A01/A03 class) is tested.

#### Ghost UI Pass
**Result**: PASS
No UI surface.

#### Section 4 Razor Pass
**Result**: PASS

| Check              | Limit | Blueprint Proposes | Status |
| ------------------ | ----- | ------------------ | ------ |
| Max function lines | 40    | ~15 (`get_or_create`) | OK  |
| Max file lines     | 250   | 172 (`session.py`), ~190 (test) | OK |
| Max nesting depth  | 3     | 2                  | OK     |
| Nested ternaries   | 0     | 0                  | OK     |

#### Self-Application Sub-Pass
**Result**: FAIL (V1, V2)
`originating_remediation` is `GH #483`. The plan's own disciplines are LD-6 (every normative statement matches the new rule) and the iteration-1 V1 standard it adopts in LD-7 deviation 6 (a declared rotation case needs a test that fails when its check is removed). Applied to the plan: the "no pre-seal phase artifact rotates" rule, now normative, has no discriminating test (V1). One clause of the mandated lifecycle text does not match `_marker_state` (V2).

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
| malformed content rotates (4 cases) | yes | yes | PASS |
| ideation-only dir is current | yes | yes | PASS |
| every pre-seal chain phase is live (5 cases) | yes | yes | PASS |
| non-empty dir holding only non-chain artifacts rotates | not planned | -- | coverage-gap (V1) |

#### Dependency Pass
**Result**: PASS
No new dependencies.

#### Macro-Level Architecture Pass
**Result**: PASS
The local tuple avoids the `gate_chain` -> `session` import cycle (`gate_chain.py:15`). The six modules that call `current()`/`get_or_create()` are exactly the six LD-4 names (`git grep` at the base); the other six importers of `session` use only `validate_session_id`.

#### Feature Test Coverage Pass
**Result**: PASS (exempt)
`feature_inventory_touches: []`.

#### Infrastructure Alignment Pass
**Result**: PASS
All 55 `git show 8ee9d98...:<path> | grep -nE` statements, re-run by hand, print exactly one line each and match. The provenance claims reproduce: `_marker_fresh` has 3 hits, all in `session.py`; the candidate diff against `15729311` is 4 files, `250 insertions(+), 7 deletions(-)`; `--is-ancestor` of the candidate exits 1; the three edited files are unchanged from `15729311` to the base; the completeness grep prints 3 lines; `qor/dist` has 0 hits; the Entry #818 sentence is on lines 24134 and 24228; the local `v0.175.2` is an ancestor. The highest remote tag is `v0.172.2`. The Phase 3 proofs reproduce. The CI-view simulation prints `{'0.175.2'} {'0.175.2'}` at the base and `set() {'0.175.2'}` with the entry. The guarded clone proof on a simulated seal commit exits 1 without the entry (orphan assertion) and exits 0 with it (`4 passed`, twice).

#### Filter-Stage Ordering Coherence
**Result**: PASS
The order is marker state, then pattern match, then seal check, then phase-artifact membership. No stage precedes its precondition.

#### Orphan Pass
**Result**: PASS
The new test file is collected. `session.py` is on the build path.

### Violations Found

| ID | Category | Location | Description |
| -- | -------- | -------- | ----------- |
| V1 | coverage-gap | plan LD-2 (liveness set, remediate sentence, derivation decision); Phase 2 tuple comment; DoD D1 ("phase-artifact-free"); Phase 2 `docs/lifecycle.md` and `qor/gates/chain.md` text ("it holds no pre-seal phase artifact") | In response to #819 V2, the iteration-2 text makes "a stale marker whose directory holds no pre-seal phase artifact rotates" a normative rule, and LD-2 states that a remediation-only directory is not live. No planned test discriminates that rule for a non-empty directory. The drift test pins only one direction (every `gate_chain` pre-seal phase is in the tuple), yet the plan calls the tuple derived and has the code comment say the test "pins the two sets". Reproduced with the Phase 2 `session.py`. M10 (append `"remediate.json"` to `_GATE_PHASE_ARTIFACTS`) and M11 (replace the membership `any(...)` with `any(p.suffix == ".json" for p in sess_dir.iterdir())`) each give `18 passed` on the Phase 1 file and `1273 passed, 4 deselected` over all 150 session-related files. Each mutation silently widens the LD-5 accepted residual, because more abandoned sessions then stay current past the TTL. This is the same failure class as #819 V1, and the plan's own LD-7 deviation 6 rejects it for M3. |
| V2 | specification-drift | plan Phase 2 `docs/lifecycle.md` line 68 replacement ("After 24h of inactivity, the marker is considered stale"); plan claim "every clause matches `_marker_state` ..." | `_marker_state` measures age since the last marker write. The marker is written only on creation, on `rotate`, and on the new stale-live reuse. Fresh reads, `current()` and gate writes do not refresh it. Reproduced: a marker aged 23 h stays 23.0 h old after three `get_or_create()`/`current()` calls, and at 25 h with no phase artifact `current()` returns None despite that activity. So an actively used session goes stale 24 h after its marker was written, not after 24 h of inactivity. That is the #483 trigger, which the plan's own Problem section words correctly ("without a marker write"). The replacement `chain.md` line ("A marker older than 24h") and the docstring ("older than 24h") are accurate, so the lifecycle line alone misstates the rule while LD-6 and Phase 2 assert that every clause matches. |

### Per-ground directives (if VETO)

#### Plan-text

V1: the plan declares a rotation rule for non-empty directories that hold no pre-seal phase artifact (LD-2, D1, and the new lifecycle and chain.md text). It also describes the liveness tuple as derived from and pinned to `gate_chain`, but no planned test fails when the tuple or the membership check admits a non-chain artifact (M10, M11). V2: the prescribed `docs/lifecycle.md` line 68 text keeps an "inactivity" clause that does not match `_marker_state`, contrary to the plan's LD-6 completeness and clause-match assertions.

**Required next action:** Governor: amend plan text, re-run `/qor-audit`

### Advisories (non-VETO)

- **A1** `workspace_fragility_check` reports medium (64 dirty gate-artifact directories across the repository). This is pre-existing.
- **A2** LD-4 names six callers. They are exactly the modules that call `current()` or `get_or_create()`. Six further importers use only `validate_session_id` and are unaffected.
- **A3** The drift test's parameter list is computed from `gate_chain` at collection time. If `substantiate` were renamed, collection would raise `ValueError` (fail-loud). Recorded as a property of the design, not a finding.

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
