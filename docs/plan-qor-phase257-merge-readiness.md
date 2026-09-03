# Plan: an executable answer to "is any check still pending?" (closes the merge-on-green override)

**change_class**: feature

**doc_tier**: standard

**terms**: []

No new domain vocabulary.

**boundaries**:
- limitations: [cannot prevent an admin merge; GitHub's admin flag is a bypass by design, so this is a detective and procedural control and the plan does not claim otherwise]
- non_goals: [does not merge, close, or otherwise mutate any pull request; does not import a forge SDK; does not add a CI job, since a CI check cannot gate the flag whose purpose is to bypass CI checks]
- exclusions: [no change to `release_ci_gate`, which already gates the downstream consequence at publish time]

## Problem

One severity-3 `gate_override` has stood open since 2026-08-17 with a real remedy
and no enforcer. Phase 256 deliberately declined to close it, because closing an
event on prose is the failure this repository rejects. Its record:

```
gate:   merge-on-green
what:   PR #344 admin-merged while CI checks were still pending; the pending run
        failed after merge (provenance test), landing a red main and a refused
        v0.148.1 release
remedy: never admin-merge with any check pending; admin flag is for
        ruleset-blocked GREEN runs only
```

The remedy is a question a person has to answer by reading a list: *is anything
still pending?* Nothing in this repository answers it, so the answer is produced
by eye, at the moment of least patience in the cycle, by whoever wants the merge.

This event will never age out. `check_shadow_threshold`'s stale expiry closes
unaddressed severity 1-2 events after 90 days; severity 3 and above instead
self-escalate to a severity-5 `aged_high_severity_unremediated`. Left alone, this
one gets louder rather than quieter, which is the correct design and the reason
it is worth discharging rather than waiting out.

### The trap that makes the naive rule useless

"Refuse to merge while any check is pending" cannot be implemented as written.
Measured against the three most recent pull requests in this repository, every
one carries the identical shape:

| PR | pass | pending |
|---|---|---|
| #422 | 16 | 1 (`publish`, state `WAITING`) |
| #421 | 16 | 1 (`publish`, state `WAITING`) |
| #420 | 16 | 1 (`publish`, state `WAITING`) |

The `publish` job waits on a deployment-environment approval that is only ever
granted after merge. It is *permanently* pending by design. A gate that treats it
as a blocker would refuse every merge this repository will ever make, and would
become a control nobody can satisfy -- which the publication-boundary doctrine
already records as the way a control becomes one nobody enforces.

So the distinction the check must draw is between **pending because it is still
running** and **pending because it is waiting for a human**. GitHub reports the
first as `QUEUED` or `IN_PROGRESS` and the second as `WAITING`.

## Fix

`qor/scripts/merge_readiness.py`, following the `ac_close_guard` precedent: a
`gh`-shelling guard, no forge SDK imported, with the decision logic in a pure
function that takes the parsed check list so it is testable without a network.

`classify(checks) -> Readiness` returns one of `FAILING`, `RUNNING`,
`NO_CHECKS`, `UNRECOGNIZED`, or `READY`. `READY` is the only state that exits 0.

**The default is deny (tribunal ground V-1).** `READY` is not the fall-through
case. It requires that *every* check is positively recognized as one of:

- bucket `pass`
- bucket `skipping`
- state `WAITING` -- deferred on a human, not on a machine

Anything else blocks: the `fail` bucket yields `FAILING`, the running states
(`QUEUED`, `IN_PROGRESS`, bare `PENDING`) yield `RUNNING`, and any bucket or
state outside those sets yields `UNRECOGNIZED` with the offending value named in
the output.

This matters more than the enumeration it replaces. `gh pr checks` also emits a
`cancel` bucket, and a cancelled required check is exactly the shape this gate
exists to catch -- it did not pass, it is not running, and under a fall-through
rule it reads as green. A workflow cancelled by a force-push, a timeout, or a
concurrency-group eviction would be waved through.

More generally, failing safe on an unknown value makes the check's correctness
independent of how completely its author enumerated GitHub's vocabulary. That
vocabulary is not this repository's to control and will change without notice. A
gate that fails open needs perfect knowledge of it forever; a gate that fails
closed needs none.

`WAITING` checks are reported by name so the operator sees what is deferred
rather than having it silently dropped.

**`NO_CHECKS` is not `READY` either.** The recorded failure was merging while
checks ran; its sibling is merging before checks are created, when a workflow has
not yet been scheduled. Zero checks is not evidence of health; it is absence of
evidence -- and so is a state the tool does not understand. That principle is why
both cases block.

## Where its force comes from, stated honestly

This cannot be a preventive control. `gh pr merge --admin` exists to bypass
branch protection, so no CI job can gate it -- a check that could stop the flag
whose purpose is to ignore checks is a contradiction. Claiming otherwise would be
the closing-on-prose failure wearing a script.

What it is: an executable answer replacing a judgement call, wired into the
`/qor-substantiate` post-seal handoff so the safe path is the one already written
down. The downstream consequence is separately gated -- Phase 163 made the PyPI
publish refuse unless CI is green for that exact SHA (`release_ci_gate`), which
is why PR #344's damage stopped at a red `main` and a refused release rather than
a bad artifact. This closes the remaining gap: the moment before the merge, where
today the only instrument is someone's patience.

That is a smaller claim than "this prevents the recurrence", and it is the true
one. The event's remedy asks for a rule to be followed; this makes the rule
checkable in one command instead of by reading a list.

## Affected Files

- `qor/scripts/merge_readiness.py` - NEW. The pure `classify` plus the `gh`-shelling CLI.
- `tests/test_merge_readiness.py` - NEW. The six payload-driven tests.
- `qor/references/doctrine-governance-enforcement.md` - gains section 17, the
  normative merge-readiness rule, so the check is written down where merge rules
  belong and where `/qor-substantiate` Step 9.6 already points (tribunal ground
  V-2, revised at iteration 3). Without a home the module ships referenced by
  nothing, which is the same defect class this phase discharges: a rule living
  only somewhere nobody is directed to look.

The seal skill itself is **not** touched, and the reason is a finding. Wiring the
invocation inline was attempted and reverted: `qor-substantiate/SKILL.md` stands
at 2,702 B of slack against the 2,700 B floor that
`test_ladder_rewrite_left_usable_slack` enforces, so even a minimal two-line
pointer breached it. Every route to those bytes ran through compressing normative
gate text -- the runtime-principal fidelity directive, the presence-only seal gate
-- and that floor exists precisely because three earlier phases each resolved a
size breach under pressure and made the next one harder. Buying room by weakening
a gate directive is the trade the floor was written to refuse, so the wiring went
to the doctrine instead and the seal skill's need for a progressive-disclosure
pass is recorded rather than paid for out of a gate.

## Definition of Done

- **D1 vision**: the merge-on-green remedy stops being a rule someone remembers
  and becomes a question one command answers.
- **D2 code**: `classify` and the CLI exist, with the `WAITING` and empty-list
  distinctions implemented rather than described.
- **D3 governance**: the severity-3 `gate_override` closes as `remediated`
  against `tests/test_merge_readiness.py`, and the seal records that the control
  is detective and procedural rather than preventive.
- **D4 empirical**: the CLI is run against a real pull request and its output
  recorded, not just exercised through fixtures.

## Tests (written first)

All six drive `classify` directly over check payloads in the shape `gh pr checks
--json name,state,bucket` actually returns, so no test touches the network.

- `tests/test_merge_readiness.py::test_running_check_blocks`
  -- a payload with one `IN_PROGRESS` check among passes returns `RUNNING`. This
  is the PR #344 failure; red before the module exists.
- `::test_waiting_check_does_not_block`
  -- sixteen passes plus the `publish` check in state `WAITING` returns `READY`,
  matching the measured shape of every recent pull request. Without this the gate
  refuses every merge and is worthless.
- `::test_waiting_does_not_mask_a_running_check`
  -- `WAITING` and `IN_PROGRESS` together return `RUNNING`. The permanent
  exception must not become a hiding place for the real one.
- `::test_empty_check_list_is_not_ready`
  -- an empty payload returns `NO_CHECKS`, not `READY`. Absence of evidence is
  not evidence of health.
- `::test_failure_blocks_even_when_everything_else_passed`
  -- one `fail` bucket among passes returns `FAILING`.
- `::test_unrecognized_bucket_blocks`
  -- a `cancel` bucket among passes returns `UNRECOGNIZED`, not `READY`. This is
  the test that makes the default-deny inversion a behavior rather than a
  sentence; without it V-1 is unresolved.

## Validation

- `python -m pytest tests/test_merge_readiness.py -q` -- run twice for determinism
- `python -m pytest -q` (full suite)
- `python -m ruff check qor/ tests/`
- `python -m qor.scripts.merge_readiness --pr 422` -- run against a real merged pull request and record the output; it must report READY with the `publish` check named as deferred
- `python -m qor.scripts.publication_boundary_lint`
- `python -m qor.scripts.check_variant_drift`

## CI Commands

- `python -m pytest -q`
- `python -m ruff check qor/ tests/`
- `python -m qor.scripts.check_variant_drift`
