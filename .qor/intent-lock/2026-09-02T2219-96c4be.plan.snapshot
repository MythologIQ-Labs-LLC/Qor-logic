# Plan: signature discrimination in the severity collapse (Phase 253 follow-up)

**change_class**: hotfix

**doc_tier**: standard

**terms**: []

No new domain vocabulary. This corrects the discriminator used by an existing
rule.

**boundaries**:
- limitations: [does not change the threshold value, the routing rule, or the pending-proposal discount; only which events the collapse treats as the same condition]
- non_goals: [does not close or re-classify any existing event -- the honest-closure pass over the residue is separate work with its own evidence]
- exclusions: [no change to the events themselves; occurrences continue to be retained in full as history]

## Problem

Phase 253 introduced `collapsed_severity` so a disclosed event repeating with
the same signature contributes its severity once. The signature is
`(event_type, details.gate or details.capability)`.

Events carrying neither key collapse by `event_type` alone, which merges
genuinely distinct defects. Measured against this repository's own genome:

```
degradation, sev 4   pattern: concurrent-edit-during-audit
degradation, sev 3   pattern: delegated-review-delivery-failure
```

Two unrelated failures -- one about amending a plan mid-audit, one about a
mandated reviewer going idle without delivering -- count as one. The same
flattening applies to three `orchestration_override` events recording three
different operator decisions on three different phases, and to three
`repeated_veto_pattern` firings naming different phase pairs.

The direction of the error is worth naming: Phase 253 was written to stop the
threshold over-counting recurrence, and it introduced an under-count of distinct
defects. A rule that hides real debt is the more dangerous failure, because the
number it produces looks better.

## Fix

`check_shadow_threshold._signature` resolves its discriminator as the first
present of:

1. `details.gate`
2. `details.capability`
3. `details.pattern`
4. a stable digest of the whole `details` mapping

The governing principle is that **collapse requires positive evidence that two
events describe the same condition**. A shared `gate`, `capability` or `pattern`
is that evidence. Absent all three, identical details are the evidence; differing
details mean we do not know the events are the same, so they are not merged.

That is the fail-safe direction, and it matches how this repository has resolved
the same question elsewhere: an absent discriminator is not evidence of sameness,
in the way an unreadable input is not evidence of an empty one.

The digest is only ever reached when no stable classifier exists, so a varying
field such as `details.phase` cannot defeat collapse for the many events that do
carry a `gate` -- `gate` wins before the digest is consulted.

### The emitter half (tribunal ground V-1, entry #709)

`veto_pattern.py:123-126` emits details of only `recent_phases` and
`max_pass_count`. `recent_phases` is a sliding window that differs on every
firing, so under the digest fallback each firing is a distinct signature: the
three present firings name `[234, 244]`, `[243, 244]` and `[246, 247]`, which
would become 9 severity instead of 3, then 12, growing by one severity-3
signature per seal of any phase that took two audit passes.

That is a sum growing monotonically with phase count -- the exact failure Phase
253 removed, reintroduced through the fallback. So the emitter carries
`"pattern": "repeated-veto"` and the chain resolves at step 3.
`recent_phases` and `max_pass_count` stay in `details` as the per-firing
evidence; only the discriminator changes.

**The general rule, stated because the next detector will meet it:** an event
type whose details vary *by construction* on every emission MUST carry an
explicit `pattern`. Relying on the digest for such a type converts one recurring
condition into unbounded distinct signatures.

The test is whether details vary by construction or by content.
`orchestration_override` also reaches the digest, and its three events record
three different operator decisions about three different phases -- varying by
content, genuinely distinct, and correctly left without a classifier.

## Measured effect

**Corrected twice during implementation.** Both errors were mine and both made
the number look better than it is; they are recorded here rather than quietly
replaced.

The first two drafts measured `shadow_process.read_events()` -- the local genome
only, 75 events. The threshold CLI reads `read_all_events()`, which includes the
upstream genome: **134 events, 107 unaddressed**. Every figure below is on that
basis.

| discriminator | signatures | sum |
|---|---|---|
| Phase 253 shipped rule | 20 | 42 |
| **Phase 254 chain** | **33** | **63** |
| no collapse at all | 107 | 173 |

The correction raises this repository's debt from 42 to 63 against a threshold
of 10, because distinct defects stop being merged. That is the point of the
phase, and no option was chosen for the number it produces.

### The emitter fix is forward-only

The second error: an earlier draft predicted 46, on the assumption that adding
`"pattern": "repeated-veto"` would collapse the three existing
`repeated_veto_pattern` firings. It does not. Those events are already written
and carry no `pattern`, so they remain three distinct signatures.

The emitter change prevents *future* unbounded growth -- from the next firing
onward the detector collapses to one signature. It does not retroactively
rewrite history, and it should not: editing sealed events to improve a number
would be the worst available move.

So the honest statement is that this phase raises the visible debt and caps the
rate at which one detector can inflate it going forward.

## Tests (written first)

- `tests/test_signature_discrimination.py::test_distinct_patterns_do_not_collapse`
  -- two `degradation` events with different `details.pattern` contribute
  separately. Red before the fix; this is the exact pair found in the live
  genome.
- `::test_identical_details_still_collapse`
  -- two events with no gate, no capability, no pattern and identical details
  contribute once, so the fix does not become "never collapse".
- `::test_gate_still_wins_over_the_digest`
  -- two events sharing a `gate` but differing elsewhere in `details` (a varying
  `phase`, as the real skip events carry) still collapse. Without this the fix
  would silently undo Phase 253 for the events it was written for.
- `::test_capability_and_pattern_precedence`
  -- the discriminator chain resolves in the declared order.
- `::test_sliding_window_detector_collapses_by_pattern`
  -- three `repeated_veto_pattern` events with different `recent_phases`
  contribute once, because the emitter now supplies `pattern`. Red before the
  emitter change; without it the discriminator fix makes this detector grow
  without bound.
- `tests/test_veto_pattern.py` (existing): the emitted event carries
  `details.pattern == "repeated-veto"` alongside its existing fields.
- `::test_live_genome_sum_rises_after_discrimination`
  -- against the real genome, the corrected sum is strictly greater than the
  shipped rule's. The anti-recurrence binding, and a guard against a future
  change quietly re-merging distinct defects.

Every test invokes `collapsed_severity` or `_signature` and asserts on the
returned value.

## Validation

- `python -m pytest tests/test_signature_discrimination.py -q` -- run twice for determinism
- `python -m pytest -q` (full suite)
- `python -m ruff check qor/ tests/`
- `python -m qor.scripts.check_variant_drift`
- `python -m qor.scripts.publication_boundary_lint`
- `qor-logic-plus scripts check_shadow_threshold` -- expected to report a HIGHER sum than before, and the seal must not be adjusted to compensate

## CI Commands

- `python -m pytest -q`
- `python -m ruff check qor/ tests/`
- `python -m qor.scripts.check_variant_drift`
