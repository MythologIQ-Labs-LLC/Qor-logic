# AUDIT REPORT -- Phase 220 (GH #324), iteration 2

**Verdict**: PASS
**Risk Grade**: L2
**Target**: docs/plan-qor-phase220-override-escalation.md
**Session**: 2026-08-11T2009-27b275
**Branch**: phase/220-override-escalation
**Mode**: solo (audit_risk_score option_b_required=false)
**Prior verdict**: VETO at ledger entry #555 (`specification-drift`, two grounds); both cleared

## Prior-ground disposition

**Ground 1 -- the raise-versus-refuse ambiguity -- CLEARED, and well.** LD-2 now
states the contract in the codebase's own terms: `append_event` mirrors
`emit_gate_override` exactly -- raise `OverrideFrictionRequired`, accept a
written justification, record normally. "Friction is a cost, not a wall" is
stated as the governing principle, and the reasoning is given rather than
asserted: an override that cannot be recorded past the threshold makes the
operator choose between undisclosed progress and no progress, and the first is
strictly worse than today.

A new test, `test_justified_override_past_threshold_still_records`, pins it. The
Changes section adds the second-order point the VETO did not ask for: two entry
points with two different friction behaviours would be this phase's own defect in
a new place.

**Ground 2 -- the missing threshold -- CLEARED against evidence rather than
taste.** The value is 3, reusing `DEFAULT_THRESHOLD`, and the justification is
checked against what actually happened: at 3 the escalation fires on the Phase
218 `intent_lock` override, one phase before a human noticed the pattern by
reading the log; at 2 it fires at Phase 217, which is the alarm fatigue Phase 217
was itself sealed to remove; at 4 it fires exactly when the operator already
knew, which is no help.

Choosing a constant by replaying it against the recorded history is the strongest
available form of this argument. `test_two_occurrences_do_not_escalate` pins the
value against silent downward drift.

One internal inconsistency introduced by the amendment -- LD-5 and the Feature
Inventory row still said "four same-gate overrides" after the tests moved to
three -- was corrected before this verdict. Phase 218's audit caught the same
class of contradiction, and `plan_text_consistency_lint` does not see it: the
lint checks paths and commands, not counts.

## Passes

| Pass | Result |
|---|---|
| Prompt Injection | PASS (canary scan, exit 0) |
| Security / OWASP | PASS -- local log reads only |
| Test Functionality | PASS -- twelve declared tests, each invoking the unit |
| Filter-Stage | PASS |
| Infrastructure Alignment | PASS -- three LD citations re-verified |
| Feature Test Declaration | PASS |
| Razor / self-application | PASS |
| Publication boundary | PASS -- 0 findings, scope structural+identity |
| pre-audit lint ladder | all rc=0; dod_check rc=0 |

## Verdict

**PASS** at L2.

Binding: LD-5 -- each fix ships a test failing against `HEAD`. Binding also on
Phase 3: `qor-substantiate` has **75 bytes** of slack. Per Phase 219 LD-3, a
disclosure pass runs first if the addition does not fit, and the step is never
compressed below the point where it stops being executable. That file has now
absorbed steps in three consecutive phases; if the pass cannot free room, the
correct outcome is to say so, not to shave the wiring.
