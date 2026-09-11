# Plan: an escalated event stops counting twice

**change_class**: hotfix

**doc_tier**: standard

**boundaries**:
- limitations: This bounds the measure; it does not clear the breach. Measured by
  iterating `sweep`, the current quantity rises without limit -- 55, 95, 135, 175
  at ninety-day intervals. This holds it at a constant **40**. Forty is genuine
  unaddressed debt and the gate is correct to keep firing on it. Nothing here
  works the debt, lowers the threshold constant, or changes what any event means.
  Forty rather than 25 because eight escalations will report on five conditions:
  the escalation payload carries `aged_entry_id` and no collapsing key, so
  `_signature` makes each unique by construction. Measured, and deferred to its
  own phase for the reason in LD-5.
- non_goals: No attempt to make the gate quiet, and no recalibration of
  `THRESHOLD`. The operator asked for recalibration and the measurement showed a
  constant cannot bound a monotonically non-decreasing quantity; this removes the
  ratchet that made it non-decreasing, which is the prerequisite for any constant
  to mean anything.
- exclusions: No change to the escalation rule, the stale-expiry rule,
  `_signature`, `THRESHOLD`, `STALE_DAYS`, or `orchestration_override`. No event
  is written, mutated, or closed: the change is a read-side filter and touches no
  `addressed` flag.

## Open Questions

None.

## Locked Decisions

### LD-1: an escalated event is counted twice, and that is why no constant holds

At `STALE_DAYS` a severity 1-2 event is closed as stale; a severity >= 3 event is
not. Instead a new severity-5 escalation is appended that names it, and the
original stays open at its own severity.

> `git show HEAD:qor/scripts/check_shadow_threshold.py | grep -n 'addressed_reason.. = .stale.\|elif e\[.severity.\] >= 3\|"source_entry_id": e\["id"\]'`
> -> `62:            e["addressed_reason"] = "stale"`
> -> `63:        elif e["severity"] >= 3 and e["id"] not in existing_escalations:`
> -> `79:                "source_entry_id": e["id"],`

So one condition contributes its original severity and, ninety days later, five
more. Nothing ever de-escalates, and no path reduces it except explicit closure.

**The escalation is itself severity 5, and `existing_escalations` holds source
ids rather than escalation ids**, so an escalation is not excluded from the
branch that escalates:

> `git show HEAD:qor/scripts/check_shadow_threshold.py | grep -n 'existing_escalations = \|e\["source_entry_id"\]$'`
> -> `46:    existing_escalations: set[str] = {`
> -> `47:        e["source_entry_id"]`

`main` persists what `sweep` returns, so the live system is an iterated map: at
ninety days `orig` yields `E1`; at one hundred and eighty `E1` yields `E2`; and
so on without limit.

**Measured by iterating `sweep` and persisting between rounds, as `main` does:**

| | +90d | +180d | +270d | +360d |
|---|---|---|---|---|
| current | 55 | 95 | 135 | **175** |

**+40 every ninety days, unbounded.** An earlier draft of this decision projected
a single `sweep` call from today's log and reported the quantity settling at 55.
That is an artifact of the method: generation two cannot appear in a projection
whose input contains no generation one. The flat 55/55/55 it produced was the
absence of iteration, not the presence of a ceiling.

That is the answer to whether `THRESHOLD` can be recalibrated. No constant bounds
a quantity that rises by 40 every quarter.

### LD-2: the escalation supersedes the original, so only one of them should count

The escalation exists to say the original aged without remediation. It names its
source explicitly at `:79`, so the link is already recorded and needs no new
field. Counting both is double-counting one condition, which is precisely what
`collapsed_severity` exists to prevent.

> `git show HEAD:qor/scripts/check_shadow_threshold.py | grep -n 'contributes its severity ONCE'`
> -> `149:    A disclosed event repeating with the same signature contributes its severity`

The rule this plan adds is the same rule that function already applies, extended
from "same signature" to "one of these supersedes the other".

### LD-3: the writer-side variant is schema-invalid, and its closure is irreversible

The obvious implementation is to mark the original `addressed` with reason
`escalated`, mirroring the stale branch three lines above. It is rejected on
three grounds, none of them the number.

**It does not validate.** `addressed_reason` is a closed enum:

> `python -c "import json;print(json.load(open('qor/gates/schema/shadow_event.schema.json'))['properties']['addressed_reason']['enum'])"`
> -> `['issue_created', 'remediated', 'stale', 'deferred_upstream', None]`

`escalated` is not a member, so the variant fails validation on emission. An
earlier draft argued instead from `permanent_skips`, glossing its guard as
"severity >= 3 events are defects". That was a borrowed argument and a wrong one:
`_CLOSABLE_ON_EMISSION` scopes emit-time closure by **event type**, not severity,
and both types it admits exist at severity 3 in the live log.

**It closes the wrong things unattested.** The eight events it would close are
four `repeated_veto_pattern` and four `degradation`. Neither type is in
`permanent_skips._CLOSABLE_ON_EMISSION`, which bounds unattested closure to types
reporting an absence. Marking them `addressed` outside
`remediate_mark_addressed.mark_addressed` closes them without the PASS review
artifact that path requires.

**Its closure has no way back.** Both variants reach the same figure under a
projection in which nothing is closed. They diverge the moment an escalation is
resolved through the attested path: the read-side filter computes `superseded`
from live escalations only, so the original returns to the count; the writer-side
form stamped it `addressed` and there is no path back. The debt would vanish
because its escalation was resolved, which is the opposite of what resolution
means. That divergence is LD-4's live-only semantic and
`test_a_closed_escalation_returns_the_original_to_the_count` pins it.

The figures live in LD-1 and are not restated here. An earlier draft carried its
own table quoting the one-shot series LD-1 retracts, so the document asserted as
fact forty lines below what it had already withdrawn above.

**Neither variant hides anything from the operator.** `check_shadow_threshold.py:234`
builds `unaddr_ids` from every unaddressed event without the filter, and
`create_shadow_issue` enumerates that list, so the issue a breach generates names
the original and its escalation both. The filter changes the sum, not the
inventory.

### LD-4: escalation still escalates

Skipping the original and counting the escalation preserves the severity increase
escalation exists to produce, and removes the original that was being counted
alongside it.

The arithmetic is per *signature*, not per event, and an earlier draft of this
decision said "from 3 to 5" as though the two were the same. They are not. Six
`degradation` events share one `gate` and therefore one signature contributing 3
today; four of them are severity 3 and each spawns its own escalation. So that
one condition rises from 3 to 20, and the filter takes it to 20 rather than to 5.
Returning it to 5 needs the escalation payload to carry a collapsing key, which
LD-5 defers.

A superseded original is skipped only while its escalation is live. Should the
escalation be closed through the attested path, the original is counted again --
the debt does not vanish because its escalation was resolved; it returns to
being ordinary unaddressed debt.

### LD-5: the payload key is measured, and deferred

Giving the escalation payload a collapsing key derived from its source would take
the constant from 40 to 25. It was drafted into this plan and removed after
review found two defects in it, both in surface added mid-cycle:

- `_signature` returns `(event_type, key)`; a key built from `[1]` alone discards
  the event type. `intent_lock` appears today under both `gate_override` and
  `gate_skipped_prerequisite_absent`, and
  `tests/test_shadow_residue_disposition.py:40` pins the second as its own closed
  signature. Collapsing them is the direction `check_shadow_threshold.py:103-104`
  calls "the more dangerous one".
- The key compounds across generations -- measured as
  `escalated:`, `escalated:escalated:`, `escalated:escalated:escalated:` -- growing
  ten characters every ninety days in an append-only log, and changing the
  signature every generation.

Both are fixable and neither is fixable well inside a phase that has already been
reviewed three times. The measurement stands; the change belongs to a phase that
can be reviewed on its own terms.


## Phase 1: pin the double-count

### Affected Files

- `tests/test_escalation_supersedes.py` - NEW.

### Changes

Tests build an event and its escalation directly and call `collapsed_severity`,
which is the function containing the change. Fixtures use the escalation shape
`sweep` actually appends -- `event_type` `ESCALATION_EVENT`, severity 5,
`source_entry_id` set to the original's `id` -- read from the module rather than
retyped, so a fixture cannot drift from the producer.

### Unit Tests

- `test_an_escalated_original_is_not_counted_alongside_its_escalation` - a
  severity-3 event plus its live escalation sum to 5, not 8. Red before: they sum
  to 8.
- `test_an_unescalated_event_of_the_same_severity_still_counts` - the same
  severity-3 event with no escalation present sums to 3. The negative control;
  fails if the rule keys on severity rather than on supersession.
- `test_an_escalation_whose_source_is_absent_still_counts_itself` - an escalation
  naming an id no event carries contributes its own severity. Guards the
  degenerate case where the filter is written as a join that drops orphans.
- `test_a_closed_escalation_returns_the_original_to_the_count` - with the
  escalation `addressed`, the original counts again at 3. Pins LD-4: supersession
  is a live relationship, not a permanent erasure.
- `test_a_superseded_event_does_not_claim_its_signature_slot` - a superseded
  event, its escalation, and a live sibling sharing the superseded event's
  signature; the sum includes the sibling. Red before the change and red under
  the late placement, which is the only test that distinguishes the two.
- `test_a_chain_of_escalations_counts_only_its_live_tip` - builds
  `orig <- E1 <- E2` directly and asserts the sum is the tip's severity alone.
  Red before: all three count. This is the property that converts an unbounded
  quantity into a bounded one, and no single-generation fixture can observe it.
- `test_the_iterated_projection_is_constant` - iterates `sweep` over a copy of the
  real log across four ninety-day rounds, feeding each round's returned
  `updated + new_escalations` into the next **in memory**, and asserts the total
  is identical at every round and strictly below the unpatched series. It must
  not call `shadow_process.write_events_per_source`: that writes to
  `LOCAL_LOG_PATH`, and a test iterating four rounds would append thirty-two
  synthetic escalations to `docs/PROCESS_SHADOW_GENOME.md` -- mutating an
  append-only governance artifact, which `tests/test_shadow_upstream_no_test_pollution.py`
  exists to prevent. The acceptance test. A single `sweep` call cannot observe
  the defect at all, which is how an earlier draft of this plan came to report a
  ceiling that does not exist.

## Phase 2: skip superseded originals in the sum

### Affected Files

- `qor/scripts/check_shadow_threshold.py` - `collapsed_severity` gains the
  supersession filter; its docstring records why.

### Changes

```python
    superseded = {
        e.get("source_entry_id")
        for e in events
        if e.get("event_type") == ESCALATION_EVENT
        and e.get("source_entry_id")
        and not e.get("addressed")
    }
```

evaluated once before the loop, with the existing loop gaining the check
**before `seen.add(sig)`**:

```python
        if event.get("id") in superseded:
            continue
```

The placement is load-bearing. After `seen.add(sig)` a superseded event claims
its signature slot and a live sibling sharing that signature contributes nothing.
Measured on a three-event fixture -- a superseded event, its escalation, and a
live sibling sharing the superseded event's gate -- the correct placement totals
8 and the late placement totals 5, silently dropping the sibling. That is an
under-count, the direction `check_shadow_threshold.py:103-104` calls "the more
dangerous one".

`addressed` is never written. The original remains open, visible, and reachable
by every consumer that reads the log; it stops contributing a second time to one
condition's debt while its escalation carries that debt at the higher severity.

### Unit Tests

The Phase 1 tests go green. No new tests.

## Feature Inventory Touches

Empty. This plan touches `qor/scripts/` and `tests/` only.

## Definition of Done

### Deliverable: one condition contributes once

- **D1**: An event and the escalation that names it are one condition and are
  counted once, at the escalation's severity.
- **D2**: `collapsed_severity` computes a `superseded` set from live escalations'
  `source_entry_id` and skips members of it; no `addressed` flag is written.
- **D3**: Plan gate artifact; audit verdict; seal entry citing this plan by
  content hash. The two vetoes at #782 and #783 and the research brief at #781
  stand behind it as the record of what was tried first.
- **D4**: `test_an_escalated_original_is_not_counted_alongside_its_escalation` --
  a severity-3 event plus its live escalation sum to 5. Observed before the
  change: 8.

### Deliverable: the measure becomes bounded

- **D1**: The quantity stops rising from escalation alone. The bound counts
  events, not conditions -- eight escalations for five conditions is why the
  figure is 40 and not 25, per LD-5.
- **D2**: The filter is evaluated over the same list `collapsed_severity` already
  receives, so every caller benefits without changing its call.
- **D3**: LD-1 records the projection that shows a constant cannot bound the
  current quantity.
- **D4**: `test_the_iterated_projection_is_constant` -- four ninety-day rounds of
  `sweep` over the real log, persisted between rounds, total the same figure each
  time. Observed before the change: 55, 95, 135, 175.

### Deliverable: no defect is closed without attestation

- **D1**: Severity >= 3 events keep the attested two-stage closure path.
- **D2**: The change writes nothing; `addressed`, `addressed_ts` and
  `addressed_reason` are untouched on every event.
- **D3**: LD-3 records the rejected writer-side variant and why.
- **D4**: `test_a_closed_escalation_returns_the_original_to_the_count` -- the
  original is skipped only while its escalation is live, which is only possible
  if nothing was permanently closed.

## CI Commands

- `python -m pytest tests/test_escalation_supersedes.py -q` — the supersession rule and its controls.
- `python -m pytest tests/test_signature_discrimination.py tests/test_remediation_closure_states.py tests/test_shadow_residue_disposition.py tests/test_remediate.py -q` — the existing collapse and closure contracts this must not disturb.
- `python -m qor.scripts.check_shadow_threshold` — the live sum; expected to remain in breach and unchanged by this phase until the first severity >= 3 event crosses ninety days, after which the filter is what holds it constant. The figure is not pinned here because it moves on that sweep.
- `python -m qor.scripts.publication_boundary_lint` — this plan and its artifacts introduce no boundary finding.
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` — chain integrity across the phase's entries.
- `python -m pytest -q` — full suite; the seal writes badges and header state that freshness tests read.
