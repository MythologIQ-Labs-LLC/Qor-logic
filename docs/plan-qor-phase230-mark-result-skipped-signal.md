# Plan: Nothing-to-do stops reading as nothing-matched

**iteration**: 2

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: `skipped` names ids known to the shadow log but excluded by the invoked operation's eligibility guard; it does not sub-classify the guard reason (already-addressed vs not-remediated vs citation-equal) -- callers needing the reason read the event.
- non_goals: No change to validation/attestation ordering, the SG-032 `missing` surface, the two-stage flip contract, or any skill-flow step. No compatibility shim: a result that can be two-unpacked back into ignorability would preserve the defect.
- exclusions: GH #332, GH #320, GH #286.

## Iteration 2 disposition of the iteration-1 VETO (F1)

The caller enumeration was incomplete: the research sweep covered two of the three functions whose shape LD-3 changes and never swept `mark_addressed_pending`'s consumers. The true surface is TWELVE two-unpack sites -- the eight previously counted plus `tests/test_remediate.py:210`, `:237`, `:262` and `qor/skills/sdlc/qor-remediate/SKILL.md:103` (the Step 4 pending snippet). LD-3 now locks all twelve with the verified no-unpack exclusion stated; Phase 1 adds red coverage for the pending path's `skipped` semantics, whose guard is declared in LD-5. Recorded as SG-AssertedCompleteness-A (entry #611).

## Open Questions

None. The result shape and the deliberate unpack break are Locked Decisions grounded in the audit-verified twelve-site caller surface.

## Locked Decisions

**LD-1: The legacy flip helper's eligibility guard is the silent-drop site for the mark path.**

```
git show v0.150.0:qor/scripts/remediate_mark_addressed.py | grep -nE 'in target and not event' -> 61:        if event["id"] in target and not event["addressed"]:
```

**LD-2: The per-event helper's non-corrective guard is the second silent-drop site; its corrective branch carries the other two skip classes.**

```
git show v0.150.0:qor/scripts/remediate_mark_addressed.py | grep -nE 'if event.get\("addressed"\):' -> 101:        if event.get("addressed"):
```

**LD-3: `MarkResult` is a NamedTuple `(changed: int, missing: list[str], skipped: list[str])` returned by `mark_addressed`, `mark_addressed_pending`, and `correct_closure_enforcers`.** Two-element unpacking breaks by design; ALL TWELVE call sites update in the same phase: ten test unpacks (`tests/test_remediate.py:210`, `:237`, `:262`, `:446`; `tests/test_remediate_enforcer_edges.py:92`, `:123`; `tests/test_remediate_per_event_enforcers.py:52`, `:112`, `:133`; `tests/test_sg_closure_enforcement.py:63`) and two prose snippets (`qor/skills/sdlc/qor-remediate/SKILL.md:103` and `:130`). The verified no-unpack exclusion is the `qor/skills/governance/qor-audit/SKILL.md:544` call, whose result is discarded and survives the shape change. `skipped` ids appear in first-seen event order; an id both unknown and mapped stays in `missing` only. Evidence for the first demanded site in each cited file and the exclusion, all at v0.150.0:

```
git show v0.150.0:tests/test_remediate.py | grep -nE 'flipped, missing = rma.mark_addressed_pending\(' -> 210:        flipped, missing = rma.mark_addressed_pending(
```

```
git show v0.150.0:tests/test_remediate_enforcer_edges.py | grep -nE 'changed, missing = subject.mark_addressed\(' -> 92:    changed, missing = subject.mark_addressed(
```

```
git show v0.150.0:tests/test_remediate_per_event_enforcers.py | grep -nE 'changed, missing = subject.mark_addressed\(' -> 52:    changed, missing = subject.mark_addressed(
```

```
git show v0.150.0:tests/test_sg_closure_enforcement.py | grep -nE 'flipped, missing = rma.mark_addressed\(' -> 63:        flipped, missing = rma.mark_addressed(
```

```
git show v0.150.0:qor/skills/governance/qor-audit/SKILL.md | grep -nE '    rma.mark_addressed\(' -> 544:    rma.mark_addressed(
```

```
git show v0.150.0:qor/skills/sdlc/qor-remediate/SKILL.md | grep -nE 'flipped, missing = rma.mark_addressed_pending\(' -> 103:flipped, missing = rma.mark_addressed_pending(
```

```
git show v0.150.0:qor/skills/sdlc/qor-remediate/SKILL.md | grep -nE 'flipped, missing = rma.mark_addressed\(' -> 130:flipped, missing = rma.mark_addressed(
```

**LD-4: `changed` and `missing` semantics are unchanged**, so every existing assertion about them survives untouched except for the unpack shape.

**LD-5: The pending path's `skipped` guard is the legacy helper's own eligibility test**: `mark_addressed_pending` flips through `_flip_event_fields`, whose guard (LD-1) excludes already-addressed events -- those ids populate `skipped` for the pending path. An event that is merely already `addressed_pending` still matches the guard and re-flips harmlessly (idempotent update, counted in `changed`), exactly as today.

## Phase 1: Bind the distinguishable outcomes (tests first)

### Affected Files

- `tests/test_remediate_enforcer_edges.py` - extended with three tests (below); existing tests' unpack sites converted to `MarkResult` field access in Phase 2.

### Unit Tests

- `test_already_addressed_batch_surfaces_in_skipped` - `mark_addressed` over a mapping whose every event is already addressed returns `changed == 0`, `missing == []`, `skipped == [ids...]` -- the #341 outcome, now distinguishable from a miss.
- `test_mixed_batch_partitions_changed_missing_skipped` - one flippable, one unknown, one already-addressed id partition into the three fields exactly.
- `test_corrective_noop_and_ineligible_surface_in_skipped` - `correct_closure_enforcers` over one equal-citation event and one not-remediated event returns `changed == 0` with both ids in `skipped`.
- `test_pending_flip_surfaces_already_addressed_in_skipped` - `mark_addressed_pending` over one flippable and one already-addressed event returns `changed == 1` with the addressed id in `skipped` (LD-5's guard, bound for the pending path).

All red at v0.150.0: the result has no `skipped` attribute (AttributeError on field access).

## Phase 2: The result type and the deliberate caller updates

### Affected Files

- `qor/scripts/remediate_mark_addressed.py` - `MarkResult` NamedTuple; both flip helpers collect and return `skipped`; the three public functions return `MarkResult`; docstrings state the per-operation guard meaning.
- `tests/test_remediate.py`, `tests/test_remediate_per_event_enforcers.py`, `tests/test_remediate_enforcer_edges.py`, `tests/test_sg_closure_enforcement.py` - the seven unpack sites converted; assertions on `changed`/`missing` unchanged per LD-4.
- `qor/skills/sdlc/qor-remediate/SKILL.md` - the line-130 snippet's unpack updated to the result form (8.1 KB file; no size-band concern).

### Changes

Phase 1's four tests go green; every pre-existing assertion in the four test files stays green with only the unpack shape changed at the ten test sites.

### Unit Tests

- Phase 1's four tests observed red-then-green.
- The four caller test files observed green after conversion; `python -m pytest tests/ -q` full-suite green.

## Feature Inventory Touches

None. Governance tooling, tests, one skill snippet.

## Definition of Done

### Deliverable 1: Distinguishable outcomes

- **D1**: A caller can tell mutated, unknown, and ineligible apart in one call's result; `(0, [])` ambiguity is structurally gone.
- **D2**: `MarkResult(changed, missing, skipped)` across the three public functions.
- **D3**: Implement-phase ledger entry cites this plan; seal binds this plan file.
- **D4**: `test_already_addressed_batch_surfaces_in_skipped` and `test_mixed_batch_partitions_changed_missing_skipped` observed red at v0.150.0 and green after Phase 2.

### Deliverable 2: No silent caller drift

- **D1**: Every consumer of the old shape is updated in the same change; none can keep reading the ambiguous pair.
- **D2**: The twelve LD-3 sites converted; the one no-unpack call site verified surviving; no other consumption site exists (audit-verified enumeration, entry #611).
- **D4**: full suite green with zero unpack errors.

## CI Commands

- `python -m pytest tests/ -q` -- full suite.
- `qor-logic-plus scripts plan_text_consistency_lint --check docs/plan-qor-phase230-mark-result-skipped-signal.md` -- plan-internal consistency.
- `python -m qor.scripts.plan_grep_lint --plan docs/plan-qor-phase230-mark-result-skipped-signal.md --repo-root .` -- citation truth check.
