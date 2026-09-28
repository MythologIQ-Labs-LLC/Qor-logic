# AUDIT REPORT

**Tribunal Date**: 2026-09-28
**Target**: `docs/plan-qor-phase299-session-marker-staleness.md`
**Iteration**: 4 (branch `phase/299-session-marker-staleness`, head `1d168ea1`, plan-only; base `main` `8ee9d98a` = 0.175.2)
**Session**: `2026-09-28T0026-1e38ee`
**Risk Grade**: L2
**Auditor**: The Qor-logic Judge
**Mode**: Option B fresh-context reviewer, independent of the plan author and of the three prior auditors. `audit_risk_score`: `option_b_required: true` (flag `high-citation-surface`). Codex plugin unavailable; `external_reviewer.run_external_review` returned `fallback` (no reviewer configured); both `capability_shortfall` events were emitted. Reviewer toolset declaration: shell, git (local objects plus `git ls-remote` over the proxy), file read/grep, Python with the in-tree `qor` package on `PYTHONPATH`, pytest in a scratch clone outside the repository. No GitHub API. The candidate head `5f8be1e2` was read as reference only.

---

## VERDICT: VETO

---

### Executive Summary

The iteration-3 ground V1 and advisories A1 and A2 are closed as written. The Judge rebuilt the 29-item Phase 1 file from the plan text alone in a scratch clone of the base outside the repository: `10 failed, 19 passed` at the base (exactly the ten named items), `29 passed` twice with the Phase 2 `session.py`. M1 to M15 each fail exactly the named items with the stated counts. The full behavior matrix (two ages by ten directory states with valid content, plus three malformed contents at both ages) matches every scoped clause of the new CHANGELOG bullet, `docs/lifecycle.md:68`, `qor/gates/chain.md:20` and the docstrings. The installed-CLI commands behave as stated. All 61 `git show` citations reproduce at `8ee9d98`. With Phases 1 to 3 applied the full suite gives `3611 passed, 3 skipped`, and the release-state proofs reproduce. One ground remains, and it was introduced in iteration 3 and not caught then. The verbatim CHANGELOG bullet that D3 mandates contains a ledger entry number ("sealed at META_LEDGER #818"). The changelog doctrine that LD-9 cites as the rule for that bullet says, in the sentence the citation stops short of, that ledger entry numbers do not appear in the CHANGELOG.

### Pre-audit gates

- Governance health preflight (`python -m qor.cli governance-health --profile skill-entry`): all 8 artifacts OK.
- Step 0 gate check: plan artifact found and valid (`.qor/gates/2026-09-28T0026-1e38ee/plan-iter4.json`, identical to `plan.json`).
- Step 0.3 `plan_iteration_status_lint`: exit 0.
- Step 0.4 unchanged-plan short-circuit: `should_skip=False`; plan hash `c4f85f82d759f9970c4455843a12f3758a2d773e9a8f9d35211aeb472fee8af6` (iteration 3 audited `cfc319c9...`).
- Step 0.5 cycle-count escalator: `cce.check` None, `cce.check_session_total` None. `stall_walk.run` gives consecutive count 1 on signature `31501b86b1c1c0a3` (iteration 3, `specification-drift`); session totals are 1 each for three distinct signatures. K=3, so the escalator does not fire. Note: this VETO carries the same single category as iteration 3, so the consecutive count on that signature becomes 2; a further same-signature VETO would reach K=3 and route to `/qor-remediate`.
- Step 0.6 lints (WARN-only): `plan_grep_lint` truth-checked 61 citations, 0 findings. `workspace_fragility_check` medium (`dirty_gate_artifact_count=64`, pre-existing). `sg_closure_lint` 40 entries, 0 missing. `gate_schema_freeze_lint` 0. `publication_boundary_lint` 0. All other lints exit 0 with no output.
- Step 0.7 spec-delta pre-pass: no `spec_deltas`; no `qor/specs/*` contract covers session-marker behavior.
- Version-Applicability Pass: `ok=True`, `hotfix`, target v0.175.3 > current highest v0.175.2.
- Prompt Injection Pass: `prompt_injection_canaries` over ARCHITECTURE_PLAN, META_LEDGER, CONCEPT and the plan exit 0.
- Runtime Contract Walk (WARN-only): 6 backward WARN findings on unchanged modules; no forward finding.
- `prose_test_lint --enforce`: exit 0 (69 exempted with reason).

### Governor ordering deviation (plan text tightened after the plan gate write)

The plan gate artifact (`plan-iter4.json`, ts `01:42:17Z`) was written before the final plan-text edits committed in `1d168ea1` (`01:43:09Z`). The plan gate schema carries no plan-content hash, so nothing binds the gate to a byte version of the plan; the audit binds the final text through `target_content_hash` `c4f85f82...`. The gate's structured fields were compared with the final text: `phases` and all 10 `ci_commands` are identical, and `boundaries` (limitations, non-goals, exclusions) agree in substance with the final plan (the gate's limitation text is the fuller form of the plan header's). The deviation is immaterial to this verdict.

### Iteration-3 ground and advisories (verification)

| Item | Check | Observed | Status |
| ---- | ----- | -------- | ------ |
| #821 V1 | LD-9 bullet scopes the directory clauses to stale markers; malformed content rotates at any age; fresh valid keeps | Matrix with the Phase 2 `session.py`: at 1 h, all ten directory states (absent, empty, remediate-only, validate-only, audit_history-only, notes-only, ideation-only, plan-only, implement-only, sealed) keep the id from `current()` and `get_or_create()`, and neither writes. At 25 h only ideation-, plan- and implement-only keep; `current()` never writes; `get_or_create()` writes in all ten (kept id in three, new id in seven). `../../evil`, `""` and upper-case hex give `current()` None and a new valid id at 1 h and 25 h. Every scoped clause of the bullet, lifecycle:68, chain.md:20 and docstring line 8 holds; each clause's named pinning tests exist in the rebuilt file and fail under the named mutations. | Closed |
| #821 A1 | Docstrings say "pre-seal phase artifact and no seal" | Applied verbatim to the candidate `session.py`; both function docstrings and line 8 are ASCII and true for the matrix above. | Closed |
| #821 A2 | Installed CLI form in the bullet | Through `python -m qor.cli` with the Phase 2 code on a 25 h live marker: `scripts session new` keeps the id; `scripts session_tool rotate` prints `rotated session: <old> -> <new>`; `scripts session end` removes the marker and a following `session new` prints a new id; each exits 0. | Closed |

### Audit Results

#### Security Pass
**Result**: PASS
No placeholder auth, credentials or bypassed checks. `SESSION_ID_PATTERN` runs before any gate-directory lookup in `_recoverable_stale_id`, `current` and the fresh branch of `get_or_create`; M6, M7 and M15 pin all three.

#### OWASP Top 10 Pass
**Result**: PASS
No subprocess, deserialization or secrets in the product change. Traversal and absolute-path contents are tested with a live-looking target directory planted.

#### Ghost UI Pass
**Result**: PASS
No UI surface.

#### Section 4 Razor Pass
**Result**: PASS

| Check              | Limit | Blueprint Proposes | Status |
| ------------------ | ----- | ------------------ | ------ |
| Max function lines | 40    | 17 (`get_or_create`) | OK   |
| Max file lines     | 250   | 172 (`session.py`) | OK     |
| Max nesting depth  | 3     | 2                  | OK     |
| Nested ternaries   | 0     | 0                  | OK     |

#### Self-Application Sub-Pass
**Result**: FAIL (V1)
`originating_remediation` is `GH #483`. The discipline the plan applies to itself (LD-6, LD-9, D3) is that every mandated text matches the rules that govern it and the behavior it states. Applied to the LD-9 bullet, the behavior clauses now all hold, but the bullet breaks the changelog rule LD-9 invokes (V1).

#### Test Functionality Pass
**Result**: PASS

| Test description | Invokes unit? | Asserts on output? | Verdict |
| ---------------- | ------------- | ------------------ | ------- |
| stale live marker: `current()` / `get_or_create()` keep the id; reuse refreshes mtime | yes | yes | PASS |
| sealed / no-dir / empty-dir / non-pre-seal-only rotate | yes | yes | PASS |
| absent / fresh marker unaffected; fresh reads do not refresh | yes | yes | PASS |
| malformed content rotates (4 contents x 2 ages) | yes | yes | PASS |
| ideation-only live; per-phase liveness (5); set equality both directions | yes | yes | PASS |
| stale-live `current()` does not refresh | yes | yes | PASS |

#### Dependency Pass
**Result**: PASS
No new dependencies.

#### Macro-Level Architecture Pass
**Result**: PASS
The local tuple avoids the `gate_chain` -> `session` import cycle (`gate_chain.py:15`); set equality is pinned in both directions. Callers are unchanged.

#### Feature Test Coverage Pass
**Result**: PASS (exempt)
`feature_inventory_touches: []`.

#### Infrastructure Alignment Pass
**Result**: PASS
All 61 `git show 8ee9d98...:<path> | grep -nE` statements were re-executed by script: each prints exactly the quoted line. Prose claims reproduce: `gate_chain.py` lines 206 and 288; `_marker_fresh` 3 hits; candidate diff 4 files, `250 insertions(+), 7 deletions(-)`; candidate not an ancestor (exit 1); the four ported files unchanged from `15729311` to base; the Phase 1 test file absent at base; completeness grep 3 lines; `qor/dist` 0 hits; `chain.md:12` remediate wording; doctrine 109 text; `docs/operations.md` lines 96, 131-132, 144-146, 232, 238, 267, 273; Entry #818 sentence on lines 24134 and 24228; local `v0.175.2` an ancestor of base; highest remote tag `v0.172.2`; the candidate branch exists on the remote at `5f8be1e2`, so the Phase 2 fidelity fetch resolves. Scratch results: 150 session-related files `1284 passed, 4 deselected`; the seven chain/lifecycle files plus `test_gates`/`test_e2e` `95 passed`; the six doctrine-naming files `43 passed`; full suite `3611 passed, 3 skipped, 4 deselected`; variant drift `OK: 406 files, no drift`; ruff clean. End to end with the real `gate_chain` and a 26 h marker on an ideation-only session: the base issues a new id and reports `prior-phase artifact missing`; the fix keeps the id and resolves `ideation.json` in the original directory. Release state: CI-view simulation prints `{'0.175.2'} {'0.175.2'}` without the entry and `set() {'0.175.2'}` with it; the guarded clone proof on a simulated seal commit exits 0 (`4 passed`, twice), exits 1 without the entry (orphan `0.175.2`) and exits 1 at the base (guard FAIL).

#### Filter-Stage Ordering Coherence
**Result**: PASS
Marker state, then pattern match, then directory and seal check, then pre-seal membership. No stage runs before its precondition.

#### Orphan Pass
**Result**: PASS
The new test file is collected; `session.py` is on the build path.

### Violations Found

| ID | Category | Location | Description |
| -- | -------- | -------- | ----------- |
| V1 | specification-drift | plan LD-9 (CHANGELOG bullet, "exactly this text"), final sentence "`docs/release-state.json` records `0.175.2` as `sealed_unpublished` (sealed at META_LEDGER #818; no remote tag)."; LD-9 citation of `qor/references/doctrine-changelog.md` line 14; DoD D3 ("carries exactly the LD-9 text") | LD-9 names `doctrine-changelog.md` lines 13-14 as the `/qor-implement` rule for the `## [Unreleased]` bullet. That rule continues on lines 14-16 at `8ee9d98`: "Internal refactors, ledger entry numbers, and hash values do NOT appear in the CHANGELOG -- they live in `docs/META_LEDGER.md`." The mandated bullet carries a ledger entry number, `META_LEDGER #818`, which is internal seal provenance, not a user-facing effect. D3 requires the exact text, so an implementer cannot satisfy both D3 and the doctrine the plan invokes. The immediate precedent follows the doctrine: the sealed Phase 298 bullet (0.175.2 section) ends "`docs/release-state.json` records `0.175.1` as `sealed_unpublished`." with no ledger number. The ledger reference was added in iteration 3 (absent in iterations 1 and 2). The rule is not machine-enforced (`changelog_stamp` checks structure only) and older dated sections carry entry numbers, but a plan may not mandate new text that breaks a doctrine it cites; this is the same class as #820 V2 and #821 V1, mandated verbatim text that does not match its governing rule. |

### Per-ground directives (if VETO)

#### Plan-text

V1: the LD-9 CHANGELOG bullet, mandated verbatim by D3, includes the ledger entry number "META_LEDGER #818", which `qor/references/doctrine-changelog.md` (lines 14-16, the rule LD-9 cites) excludes from the CHANGELOG. The release-state reason in LD-10 may keep the number; the CHANGELOG bullet may not.

**Required next action:** Governor: amend plan text, re-run `/qor-audit`

### Advisories (non-VETO)

- **A1** LD-6's wider sweep says `git grep -nE '24 ?h|24-hour|SESSION_TTL|inactivity' ... -- qor docs/*.md README.md`, filtered to session/marker/staleness/inactivity lines, prints only the three rule lines plus `session.py` lines 24 and 62. The `docs/*.md` pathspec recurses into `docs/archive/2026-04-15/ingest/`, which yields about a dozen more matching lines from archived third-party skill material. None states the Qor marker rule, so the conclusion holds, but the stated output is not what the command prints.
- **A2** `qor/skills/meta/qor-help/SKILL.md:135` lists the cases where `current()` returns None as "(no marker, stale beyond TTL, or invalid format)". After the fix a stale live marker returns its id. The list is still a true list of possible causes, but it is outside the LD-6 completeness sweep, which only covers `lifecycle`, `chain.md`, the docstring and the doctrine line.
- **A3** The Governor ordering deviation is immaterial (see above).
- **A4** `workspace_fragility_check` reports medium (64 dirty gate-artifact directories across the repository), which is pre-existing.

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
