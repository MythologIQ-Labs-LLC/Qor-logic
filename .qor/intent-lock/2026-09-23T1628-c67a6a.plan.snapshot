# Plan: Recompose GH #484 escalation-origin signature fix on current main

**change_class**: hotfix

**doc_tier**: standard

**Origin**: GH #484 and historical PR #491.

**Current base**: `eb1ed647c92ac2da5948e7f2a69a534c34fa897c` after PR #506 landed.

## Problem Contract

Shadow threshold escalation events currently carry volatile escalation-local fields such as `aged_entry_id` and `age_days`. Without a stable root-condition signature, multiple escalations of one recurring condition can each contribute independently to collapsed severity, and an escalation-of-an-escalation can drift further from the root condition it represents.

Historical PR #491 implemented and tested a stable `origin_signature` model against an earlier base. That branch also carried independent `0.174.1` release, ledger, seal, generated-manifest, and repository-state changes that conflict with the modern release/governance line. Those historical promotion artifacts must not be replayed onto current main.

PR #507 was first recomposed against `d37c192c...`; PR #506 subsequently landed as `eb1ed647...` with fresh governance evidence for GH #477. This revision reconstructs #507 directly on that newer main while preserving only the #484 semantic change and its tests.

## Change Contract

### Authorized scope

- Preserve the underlying GH #484 implementation from PR #491:
  - separate an event's own `_base_signature` from its stable `_origin_signature`;
  - persist the root `origin_signature` when `sweep()` creates escalation events;
  - collapse escalations by the root signature while keeping escalation identity distinct from a plain event;
  - retain legacy fallback for escalation events that predate the stored origin signature.
- Preserve the behavioral and negative-control tests proving:
  - repeated escalations of one root collapse;
  - different root event types sharing a gate do not collapse together;
  - escalation ancestry remains stable across generations;
  - a multi-generation escalation and a fresh escalation of the same root collapse together;
  - superseded events do not steal a signature slot;
  - escalation signatures cannot equal plain-event signatures.

### Explicit exclusions

- No historical version bump, CHANGELOG release entry, ledger entry, seal, gate artifact, intent lock, README/SYSTEM_STATE seal metadata, or generated-manifest replay from PR #491.
- No Shadow Spectrum schema change under #499 in this slice.
- No threshold-policy redesign beyond the existing GH #484 defect.
- No Qortara Logic migration.

## Locked Decisions

### LD-1: Root condition identity must be stable across escalation generations

New escalation events store the root condition signature when created. Escalations of escalations preserve that stored root rather than wrapping or deriving a new identity from escalation-local payload fields.

### LD-2: Event type remains part of condition identity

A `gate_override` and another event type sharing the same gate are not the same condition. Root signatures must preserve the full source signature rather than only its secondary key.

### LD-3: Escalation identity remains distinct from live plain-event identity

The collapsed escalation signature remains namespaced as an escalation so it cannot collide with an un-escalated live event carrying the same root details.

### LD-4: Historical PR #491 evidence is provenance, not current promotion authority

The old PASS/tests/review remain truthful for their exact revision. Current-base CI and formal `/qor-audit` are required before promotion from this branch.

## Affected Files

- `qor/scripts/check_shadow_threshold.py`
- `tests/test_escalation_origin_signature.py`
- `tests/test_escalation_supersedes.py`

## Definition of Done

- D1: New escalations persist a stable root `origin_signature`.
- D2: Repeated and multi-generation escalations of one root condition collapse to one contribution.
- D3: Distinct event types sharing a key remain distinct.
- D4: Legacy escalation events without stored origin retain safe fallback behavior.
- D5: Behavioral regressions and negative controls are green.
- D6: Full repository CI is green on the exact current branch head.
- D7: Formal `/qor-audit` evaluates this current-base plan before promotion.

## Feature Inventory Touches

Empty. This is a bounded correction to Shadow threshold accounting semantics.

## CI Commands

- `python -m pytest tests/test_escalation_origin_signature.py tests/test_escalation_supersedes.py -q`
- `python -m pytest tests/ -q`
- `ruff check qor/scripts/check_shadow_threshold.py tests/test_escalation_origin_signature.py tests/test_escalation_supersedes.py`
- `python -m qor.scripts.check_variant_drift`
- `python -m qor.scripts.publication_boundary_lint`

## Promotion Rule

Do not merge from PR #491's historical evidence. Promotion requires fresh exact-head CI plus current-base governance evidence.
