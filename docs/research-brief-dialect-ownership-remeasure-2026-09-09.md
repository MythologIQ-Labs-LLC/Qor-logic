# Research brief: re-measuring the parked dialect-ownership design

**Date**: 2026-09-09
**Session**: 2026-09-09T0342-9a87f0
**Issues**: GH #469 (the design), #467, #468, #477 (the cluster it covers)
**Supersedes the measurements in**: docs/research-brief-dialect-ownership-2026-09-08.md

## Why this brief exists

The Phase 276 design was audited through four rounds and parked before
implementation, on branch `phase/276-dialect-ownership`. Its property, its
declaration surface and its baseline key are unchanged and are not re-argued
here. **Only its measurements are stale**, and three phases have landed since
it was written.

Its numbers are quoted throughout that plan as `14 (module, field) pairs / 24
pattern sites / 9 modules`. Re-measured against the current tree they are
different, and the difference is explained rather than absorbed.

## The corrected count

Measured with the design's own rules -- declared label forms, longest form
wins, a pattern site as the unit:

| | parked plan | now |
|---|---|---|
| violating (module, field) pairs | 14 | **8** |
| violating pattern sites | 24 | **19** |
| violating modules | 9 | **5** |

Unscoped by document the figures are 10 / 21 / 6. The difference is
`meta_ledger_walker`, which parses `**Verdict**` and `**Target**` from
`META_LEDGER.md` while `verdict_dialect` owns those names in
`AUDIT_REPORT.md`. Under D2's document scoping it is not a violation, and it
drops out. **That is the parked plan's own stated acceptance test for D2**, and
it now has an independent result: scoping works, and the two rows vanish.

## What accounts for the reduction

- **Phase 277 (v0.171.1)** routed `evidence_bundle` and `gate_provenance`
  through the dialect. Both were violations when the design was written and are
  compliant now. That is 2 of the 4 missing modules.
- **`meta_ledger_walker`** accounts for the other 2 pairs, by scoping rather
  than by any change to it.

Nothing regressed, and no violation was introduced by Phases 277, 279 or 281.

## The violations that remain

| module | sites | fields |
|---|---|---|
| `qor/scripts/ledger_migrate.py` | 13 | Content, Previous, Chain |
| `qor/reliability/ledger_base_currency.py` | 2 | Previous, Chain |
| `qor/scripts/ledger_commitment.py` | 2 | Content |
| `qor/scripts/ledger_emit.py` | 1 | Chain |
| `qor/scripts/snapshot_export.py` | 1 | Chain |

`ledger_migrate` is 13 of the 19 and is a permanent baseline entry by design:
it migrates markup *between* dialects, so reading through the dialect it is
migrating away from is incoherent.

## The aliasing rule is load-bearing, and measurable as such

A first pass of this re-measurement scored `**Previous Chain Hash**`
(`ledger_migrate:47,49`) as **both** a Previous Hash read and a Chain Hash
read, because the label contains both names. That inflated the site count and
is precisely the containment error D1a exists to prevent.

With longest-form-wins applied, those sites resolve to Previous Hash only.
The same rule correctly resolves `**META_LEDGER Content Hash**` (`:35`) and
`**Session Seal**` (`:58`).

So D1a is not a defensive nicety: an implementation without it produces wrong
counts on the live tree today, in two places.

## A limitation of the design now has a live instance

The parked plan states, in Limitations: *"A module can import the owner and
still parse the field itself; the lint sees an import, not a use."*

**GH #477 is that case.** `reconcile.py` imports `PREV_HASH_RE` and
`CHAIN_HASH_RE` from `ledger_dialect`, so it is compliant under the ownership
property -- and at `:44` and `:73` it reads `group(1) or group(2)` from a value
pattern with **three** groups, dropping the bare-hex form. The lint would pass
it.

This is worth recording plainly: the cluster contains a defect this lint does
not detect, and shipping the lint must not be described as covering it.

Measured: 0 live matches currently resolve via `group(3)`, so #477 is latent
rather than live. It is a separate fix and not in scope here.

## #467's remaining module is deliberate, not pending

Phase 277 fixed 2 of the 3 modules #467 names. The third,
`ledger_commitment._CONTENT_RE` (`:54`), is narrow **on purpose**: the comment
at `:44-53` records that widening it takes on-disk stale commitments from 74 to
116 in a gate that hard-ABORTs the seal, and
`test_a_suffixed_session_seal_hash_is_not_a_commitment` guards it.

So it belongs in the baseline with its reason, not on a fix list. #467 should
be closed against that disposition rather than left open implying pending work
-- but that is a separate judgement and not made here.

## What is unchanged

The property, the three-valued declaration surface, the two declaration
cross-checks, the baseline key including the normalized-pattern discriminator,
the permanent entries and their reasons, and all three blind spots in D5. Four
review rounds established those and nothing measured here disturbs any of them.
