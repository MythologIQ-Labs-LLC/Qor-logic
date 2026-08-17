# Research Brief

**Date**: 2026-08-17
**Analyst**: The Qor-logic Analyst
**Target**: GH #333 (per-finding closure-enforcer provenance) and the candidate implementation pair on `fix/stabilization-286-332-333-336-337` (commits `57eb632`, `bd63317`)
**Scope**: whether the pair can be salvaged through a governed phase on current main; API adequacy against the issue; scope boundaries; route for the historical repair

---

## Executive Summary

The pair applies cleanly on post-Phase-225 main (`git apply --check` clean; Phase 225 touched neither file) and its tests passed in PR #338's CI on an identical base. The implementation matches the issue's candidate fix: `mark_addressed` accepts an `{event_id: closure_enforcer}` mapping alongside the legacy list-plus-shared-enforcer form, every enforcer validates before any durable mutation, and a deliberately narrow `correct_closure_enforcers` path repairs wrong historical citations under PASS attestation without reopening events. Recommendation: a governed Phase 226 adopts the pair; the actual repair of the three mis-cited Phase 223 events is a follow-on `/qor-remediate` pass using the new API, because the corrective path's attestation contract is exactly the remediation-review flow.

## Findings

### 1. Issue-state pre-check

No merged PR closes #333. PR #339 (merged) mentions it only in disposition prose; PR #338 (open, draft) carries the implementation but is red on unrelated grounds and superseded on its #336 half.

### 2. Applicability on current main

- `git merge-base cfcc232 origin/fix/...` = `8667112`; main's diff from that base does not touch `qor/scripts/remediate_mark_addressed.py` or `tests/test_remediate_per_event_enforcers.py`.
- `git apply --check` of the pair's combined diff against `cfcc232`: clean.
- In PR #338's CI run 32024552666, every `test_remediate_per_event_enforcers` test passed; the five failures were all citation-lint tests. The pair is green on this exact file base.

### 3. API adequacy against the issue's candidate fix

- Mapping form: `_normalized_enforcers` accepts `Mapping[str, str]`, rejects a simultaneous shared `closure_enforcer`, rejects an empty mapping, and validates every enforcer via the existing four-form `_validate_closure_enforcer` BEFORE `_verify_review_pass_artifact` and before any mutation (all-or-nothing).
- Backward compatibility: the list-plus-shared-enforcer signature is preserved; a list with `closure_enforcer=None` raises `ClosureEnforcerError`.
- Corrective path: `correct_closure_enforcers` flips only `closure_enforcer` on events where `addressed` is true and `addressed_reason == "remediated"`, skips no-op corrections, cannot reopen or retimestamp -- matching the issue's "narrow, separately attested" requirement. Attestation shape (per the pair's own tests): a PASS audit artifact whose `reviews_remediate_gate` names the remediation gate file -- i.e., the existing `/qor-remediate` -> `/qor-audit reviews-remediate:<path>` flow.

### 4. What the pair does NOT cover

- The issue's aside that a `(0, [])` return "reads as failure when it means already done" is unaddressed: an all-already-addressed batch still returns `(0, [])` indistinguishably. Candidate scope decision: exclude from Phase 226 (it is an API-signal design question, not a provenance defect) and file it as its own small issue.
- The three mis-cited Phase 223 events (`.qor/gates/2026-08-12T0214-799d77/remediate-iter6.json` names four proposals, each with its own enforcer; three closed under the uniform `qor.scripts.cycle_count_escalator`) are not repaired by shipping the capability. The repair is an operational act under PASS attestation -- the follow-on `/qor-remediate` pass, immediately after Phase 226 seals.

## Blueprint Alignment

| Claim | Actual Finding | Status |
|---|---|---|
| Issue #333 candidate fix: mapping + per-event validation + corrective path | Implemented as specified in `57eb632`; behavioral coverage in `bd63317` | MATCH |
| PR #338 body: "all-or-nothing validation ... backward compatibility" | Verified in diff: validation precedes attestation precedes mutation; legacy signature intact | MATCH |
| Issue aside: distinguishable already-done signal | Not implemented | GAP (scope decision for the plan) |

## Recommendations

1. Phase 226 (feature): adopt the pair via governed cycle -- tests first (the pair's own test file is the red/green evidence, classified as adoption of pre-authored tests with verification), preserving Kevin's authorship via cherry-pick. Priority: high; unblocks truthful closure provenance for every future remediation.
2. Immediately after the seal: a `/qor-remediate` pass constructs the correction proposal for the three mis-cited events (correct enforcers already named in remediate-iter6.json), routes through `/qor-audit reviews-remediate:<path>`, and executes `correct_closure_enforcers`. Only then is #333's observed damage actually repaired -- shipping the capability alone would be a half-measure closure.
3. File the `(0, [])` ambiguity as its own small issue rather than widening Phase 226.

## Updated Knowledge

The corrective path's attestation reuses the two-stage remediation flip contract (Phase 166 / GH #249) unchanged; no new ceremony surface is introduced. Nothing here contradicts existing doctrine.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
