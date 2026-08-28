# Plan: Phase 241 - Portable Governance Engine Boundary

**iteration**: 3

**change_class**: feature

**doc_tier**: system

**originating_issue**: GH #381

**adr**: `docs/ADR_PORTABLE_GOVERNANCE_ENGINE_BOUNDARY.md`

## Boundaries

- **limitations**: Phase 241 defines the base/downstream authority boundary; it does not prove that any enterprise platform can express every Qor obligation.
- **non_goals**: no GitHub/GitLab/Azure DevOps API client, no ruleset mutation, no organization controller, no platform webhook receiver, no forge App, no enterprise actor registry.
- **exclusions**: execution-context implementation remains separate; enterprise projection implementation belongs to a downstream private control-plane layer and is not identified in tracked public-repository content.

## Scope Revisions

Iteration 1 proposed rewriting README and the broad legacy architecture overview in the same slice. That added a large, unrelated text diff before the boundary had an executable enterprise consumer.

Iteration 2 narrowed implementation to the ADR, one platform-boundary reference, and its regression test.

Iteration 3 responds to the repository's publication-boundary gate. The paired downstream implementation remains coordinated through issue/PR metadata, but canonical Qor tracked files no longer identify the private downstream repository or issue number. This is not merely lint appeasement: private enterprise implementation identity is not part of the portable public architecture.

## Locked Decisions

1. Qor-logic is the portable governance engine, not merely a prompt system and not an enterprise platform administrator.
2. Qor owns lifecycle, authority, evidence, gate semantics, portable repository contracts, deterministic evaluation, and model/host execution adaptation.
3. Enterprise desired-state deployment, repository-fleet reconciliation, platform-native enforcement, and organization federation belong to downstream control-plane layers.
4. A downstream enforcement surface may strengthen mechanical enforcement but may not redefine a Qor semantic.
5. External platform state is evidence. Unknown state is indeterminate rather than assumed satisfied.
6. Unsupported platform mappings must remain explicit `not_projectable` in downstream projection plans.
7. Canonical Qor remains network-independent at governance-gate time.
8. Phase 241 creates no machine API merely for architectural symmetry. A downstream tracer bullet determines whether a shared machine contract is actually needed later.
9. Canonical tracked content must not identify a private downstream repository merely to prove cross-project coordination.

## Phase 1 - Architecture contract

### Affected Files

- `docs/ADR_PORTABLE_GOVERNANCE_ENGINE_BOUNDARY.md` - decision of record.
- `qor/platform/enforcement.md` - extension reference separating execution adaptation from external enforcement projection.

### Behavior

The documentation must make the following direction unambiguous:

```text
Qor semantics -> downstream enterprise desired state -> platform projection -> external enforcement
```

The reverse direction is prohibited: platform state cannot grant Qor authority or rewrite gate/evidence semantics.

## Phase 2 - Boundary verification

### Affected Files

- `tests/test_portable_governance_boundary.py` - architectural regression test.

### Tests

The test parses the ADR and platform reference and asserts:

1. the canonical role is named `portable governance engine`;
2. the architecture explicitly separates execution adaptation, portable governance evaluation, and enterprise enforcement projection;
3. GitHub-specific mutation is assigned downstream rather than to base Qor;
4. `indeterminate` and `not_projectable` are preserved as required downstream states;
5. no forge-mutation surface is created in the base extension reference;
6. the first paired implementation is described only generically as downstream/private rather than identifying an external repository.

This is a contract/documentation regression test, not proof that an external platform is configured correctly.

## Definition of Done

- The ADR defines Qor-logic as the portable governance engine rather than a local-only prompt layer.
- Enterprise enforcement is recognized without entering the base runtime.
- The three adaptation/evaluation/enforcement surfaces have separate owners.
- Downstream mechanical enforcement cannot become semantic authority.
- Public tracked content does not disclose a private downstream repository identity.
- Full repository CI and variant drift pass apart from intentionally pending pre-substantiate citation evidence.

## CI Commands

- `python -m pytest tests/test_portable_governance_boundary.py -q`
- `python -m pytest tests/ -q`
- `python qor/scripts/check_variant_drift.py`
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md`
