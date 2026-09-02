# Plan: remediation closure states and threshold semantics (GH #410)

**change_class**: feature

**doc_tier**: standard

**terms**: []

No new domain vocabulary. `deferred_upstream` is a value in the existing
`addressed_reason` enum, not a new concept.

**boundaries**:
- limitations: [a `deferred_upstream` closure asserts ownership transfer, not repair; the upstream issue must exist and be recorded, and nothing here verifies that the upstream repository ever acts on it]
- non_goals: [does not change the threshold value of 10, nor the delegation-table routing rule itself; does not add cross-repository status polling, which would couple this repository to an outside one against the publication boundary]
- exclusions: [no change to `mark_addressed`'s two-stage contract -- stage 2 still requires a verified review-pass artifact]

## Problem

The Phase 166 two-stage flip has no way to express "this remediation is real,
and it must be executed in a different repository". The result is a deadlock,
observed in a consumer workspace and reported in GH #410.

`check_shadow_threshold.py:86` sums severity over events where `addressed` is
false. `mark_addressed_pending` sets `addressed_pending` only; `addressed` stays
false by contract. So a paired remediation never lowers the sum, the
`.qor/remediate-pending` marker persists, and per the delegation table every
subsequent phase routes back to `/qor-remediate`. Development cannot legally
resume.

The only exit is `/qor-audit reviews-remediate:<path>` reaching PASS, which
flips every id in `addressed_event_ids` at once. For the reporter, four of six
proposals targeted a different repository, so that exit would have closed events
against enforcers that do not exist locally -- closing on prose, which
`_validate_closure_enforcer` exists to prevent. The contract's own principle
argues against the only mechanism it offers.

Their workaround was hand-editing the gate artifact to trim the id list. That
works and is not a governance path anyone should take.

### What already exists

Two of the three remedies are closer than the issue assumes, and the plan is
scoped to the actual gaps.

- **Per-change flips**: `remediate_mark_addressed.mark_addressed` already
  accepts `{event_id: enforcer}` as well as a flat list, validating every
  enforcer before any mutation. The capability exists; `/qor-audit` Step 4.2
  passes the flat `addressed_event_ids` with one top-level `closure_enforcer`
  and never uses it.
- **The closure vocabulary**: `addressed_reason` is a closed enum
  (`issue_created`, `remediated`, `stale`, `null`) in
  `qor/gates/schema/shadow_event.schema.json`, and `closure_enforcer` and
  `issue_url` are already fields on the event. The value is missing, not the
  shape.

## Fix

1. **`qor/gates/schema/shadow_event.schema.json`**: add `deferred_upstream` to
   the `addressed_reason` enum. An event closed with that reason MUST carry a
   non-null `issue_url`, expressed as a conditional in the schema -- closure by
   verified transfer of ownership rather than by a claim of repair.
   The issue writes it `deferred-upstream`; the enum's existing values use
   underscores, so the value follows the enum.
2. **`qor/scripts/remediate_mark_addressed.py`**: `mark_addressed` accepts
   `reason="deferred_upstream"` with a required `issue_url`, sets
   `addressed=true`, and records both. Attempting it without an `issue_url`
   raises rather than closing.
3. **`qor/skills/governance/qor-audit/SKILL.md` Step 4.2**: pass the
   `{event_id: enforcer}` mapping when the remediation proposal declares
   per-change enforcers, falling back to the flat form when it declares one.
   The mapping path already exists in the callee; this is the skill catching up
   to it.
4. **`qor/scripts/check_shadow_threshold.py`**: exclude `addressed_pending`
   events from the severity sum **only when the pending flip recorded a
   `closure_enforcer` that validates**. `mark_addressed_pending` gains the
   enforcer argument and validates it with the same function stage 2 uses.

   The guard is the point. Excluding pending events unconditionally would let a
   bare proposal silence the signal, which is the closing-on-prose failure this
   repository rejects elsewhere. Requiring a validated enforcer means the
   discount is bought with the same evidence stage 2 demands -- the proposal
   names a real mechanism -- while stage 2 still requires the review-pass
   attestation before `addressed` becomes true.
5. **Routing escape as a tested fallback.** `check_shadow_threshold` gains
   `every_unaddressed_event_has_a_pending_proposal(events)`, used to clear the
   `.qor/remediate-pending` marker even when the sum stays at or above the
   threshold. With fix 4 in place this is usually unreachable, and it exists so
   that a future phase judging fix 4 too permissive can revert it without
   reintroducing the deadlock.

6. **`qor/scripts/check_shadow_threshold.py`: collapse recurrence in the sum.**
   A disclosed event repeating with the same signature -- same `event_type` and
   same `details.gate` or `details.capability` -- contributes its severity
   **once**, not once per occurrence. Every occurrence stays in the log as
   history; only the sum changes.

   Tribunal ground V-1 (entry #703) measured why this is not optional. This
   repository's own genome sums to 171 against a threshold of 10 across 105
   unaddressed events, and the two largest contributors are
   `gate_skipped_prerequisite_absent` (39) and `gate_override` (28) -- events
   emitted *because* the protocol was followed. `data_api_acl_lint` skips every
   seal because this repository has no SQL migrations, a permanent and correct
   property of it, and each seal adds severity that nothing will ever remediate
   because nothing is wrong.

   So the threshold has been measuring how many phases have been sealed rather
   than accumulated process debt, and under the delegation table that put this
   repository in continuous nominal breach while it kept sealing. Fixes 1
   through 5 all address what happens *after* a breach; without fix 6 they ship
   into a workspace whose threshold is breached for reasons they cannot touch.

   A genuinely new gate skipping, or a new capability falling short, still adds
   its severity -- which is what keeps the threshold meaningful rather than
   merely quieter.

### Implementation divergences (amended; re-audited before seal)

- **Fix 2 shipped as `mark_deferred_upstream`, not a `reason=` parameter.** The
  plan said `mark_addressed` would take `reason="deferred_upstream"`. A separate
  function is better: `mark_addressed` requires a verified review-pass artifact
  and a remediate-gate path, which an upstream transfer has no reason to carry.
  Overloading it would have meant either weakening those requirements for every
  caller or fabricating artifacts for a closure that is not a review pass.
- **A pre-existing test's fixture was corrected, not its assertion.**
  `tests/test_shadow.py::test_threshold_breach_triggers_marker` built its breach
  from two events differing only in timestamp. Under fix 6 those are one
  signature and sum to 5, below the threshold. The test checks that a breach
  writes the marker, not how severity is counted, so the fixture now uses two
  distinct gates and the assertion is untouched.
- **A second fixture, same correction.** `tests/test_e2e.py::test_threshold_breach_writes_marker`
  had the identical shape -- two events differing only in timestamp -- and was
  corrected the same way. That two independent tests reached a breach by
  repeating one event is itself evidence for fix 6: repetition was the easiest
  way to cross the threshold, in fixtures and in practice alike.
- **`qor-audit/SKILL.md` needed LF normalization and a terser comment.** The
  Step 4.2 edit pushed it past its headroom bound, and the file carried CRLF
  which inflates `os.path.getsize` by 685 bytes. Normalized to LF and the
  inline rationale reduced to a pointer, per the progressive-disclosure rule.

## Tests (written first)

- `tests/test_remediation_closure_states.py::test_deferred_upstream_requires_an_issue_url`
  -- closing with the new reason and no `issue_url` raises. Red before fix 2;
  this is what keeps the state a transfer of ownership rather than a synonym for
  "not my problem".
- `::test_deferred_upstream_closes_the_event_and_records_the_url`
  -- with an `issue_url`, `addressed` becomes true and both fields persist.
- `::test_schema_rejects_deferred_upstream_without_issue_url`
  -- the same rule at the schema boundary, so a hand-written event cannot bypass
  the helper.
- `::test_schema_still_rejects_an_unknown_reason`
  -- the enum stays closed; adding one value must not open it.
- `::test_pending_with_a_valid_enforcer_is_excluded_from_the_sum`
  -- fix 4's discount. Red before the change.
- `::test_pending_without_an_enforcer_still_counts`
  -- the compensating guard, and the pair that makes the discount evidence-bound
  rather than automatic.
- `::test_pending_with_an_invalid_enforcer_raises`
  -- an unvalidatable enforcer cannot buy the discount.
- `::test_marker_clears_when_every_unaddressed_event_has_a_proposal`
  and `::test_marker_persists_when_any_event_lacks_a_proposal`
  -- fix 5's pair.
- `::test_repeated_disclosed_event_counts_once`
  -- three `gate_skipped_prerequisite_absent` events sharing a `details.gate`
  contribute severity once. Red before fix 6.
- `::test_distinct_signatures_each_count`
  -- two skips naming *different* gates both contribute, so recurrence collapse
  does not become blanket suppression. The pair is what keeps the threshold a
  signal.
- `::test_live_genome_collapse_removes_the_recurrence_noise`
  -- against this repository's real Process Shadow Genome, the collapsed sum is
  materially smaller than the raw sum and no larger than it. The anti-recurrence
  binding: the repository that wrote the rule is its first subject.

  **Measured, and stated honestly**: 171 raw collapses to 39, which is still
  above the threshold of 10. The collapse removes the recurrence noise; it does
  not clear this repository's breach, and the plan does not claim it will. An
  earlier draft of this test asserted the sum would fall below the threshold --
  that was false, and asserting it would have shipped a test that cannot pass or,
  worse, invited tuning the rule until it did.
- `::test_per_change_enforcer_mapping_flips_each_event`
  -- the mapping form flips events whose enforcers differ, pinning the
  capability Step 4.2 now uses.

Every test invokes the unit and asserts on its return value or raised error.

### What the collapse leaves behind, and why that is correct

After collapsing recurrence, this repository still sums to 39 across distinct
signatures:

```
gate_override                    12      degradation        4
gate_skipped_prerequisite_absent  6      hallucination      4
capability_shortfall              5      regression         3
repeated_veto_pattern             3      orchestration_override  2
```

That residue is not noise and this phase does not try to remove it.
`hallucination`, `regression` and `degradation` are exactly what the Process
Shadow Genome exists to accumulate, and a rule tuned until the number fell below
ten would be tuning the instrument to the reading.

So the honest outcome is that fix 6 makes the threshold measure process debt
instead of phase count, and the debt this repository actually carries is then
visible for the first time. Working it down is an operator backlog item, not a
line of code in this plan.

## Validation

- `python -m pytest tests/test_remediation_closure_states.py -q` -- run twice for determinism
- `python -m pytest -q` (full suite)
- `python -m ruff check qor/ tests/`
- `python -m qor.scripts.check_variant_drift`
- `python -m qor.scripts.publication_boundary_lint` -- the new state records an outside repository's issue URL in operator data, never in tracked repository content
- `qor-logic-plus scripts check_shadow_threshold` -- this repository's own Process Shadow Genome must not change verdict

## CI Commands

- `python -m pytest -q`
- `python -m ruff check qor/ tests/`
- `python -m qor.scripts.check_variant_drift`
