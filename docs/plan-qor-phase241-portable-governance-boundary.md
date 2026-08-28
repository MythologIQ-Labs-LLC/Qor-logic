# Plan: Phase 241 — Portable Governance Engine Boundary

**change_class**: feature

**doc_tier**: system

**originating_issue**: GH #381

**adr**: `docs/ADR_PORTABLE_GOVERNANCE_ENGINE_BOUNDARY.md`

**paired_enterprise_issue**: `MythologIQ-Labs-LLC/Qor-logic-plus#129`

## Boundaries

- **limitations**: Phase 241 defines the base/downstream authority boundary; it does not prove that any enterprise platform can express every Qor obligation.
- **non_goals**: no GitHub/GitLab/Azure DevOps API client, no ruleset mutation, no organization controller, no platform webhook receiver, no GitHub App, no enterprise actor registry.
- **exclusions**: execution-context implementation remains Phase 240 / GH #379; enterprise GitHub projection implementation belongs to Plus #129.

## Locked Decisions

1. Qor-logic is the portable governance engine, not merely a prompt system and not an enterprise platform administrator.
2. Qor owns lifecycle, authority, evidence, gate semantics, portable repository contracts, deterministic evaluation, and model/host execution adaptation.
3. Enterprise desired-state deployment, repository-fleet reconciliation, platform-native enforcement, and organization federation belong to downstream control-plane layers.
4. A downstream enforcement surface may strengthen mechanical enforcement but may not redefine a Qor semantic.
5. External platform state is evidence. Unknown state is indeterminate rather than assumed satisfied.
6. Unsupported platform mappings must remain explicit `not_projectable` in downstream projection plans.
7. Canonical Qor remains network-independent at governance-gate time.
8. Phase 241 creates no machine API merely for architectural symmetry. The paired Plus tracer bullet will prove whether a shared machine contract is actually needed.

## Phase 1 — Architecture contract

### Affected Files

- `docs/ADR_PORTABLE_GOVERNANCE_ENGINE_BOUNDARY.md` — decision of record.
- `docs/architecture.md` — change the top-level positioning and add the portable-engine / enterprise-enforcement boundary.
- `README.md` — concise product-boundary clarification under What Qor-logic Does.
- `qor/platform/enforcement.md` — short extension reference separating execution adaptation from external enforcement projection.

### Behavior

The documentation must make the following direction unambiguous:

```text
Qor semantics -> downstream enterprise desired state -> platform projection -> external enforcement
```

The reverse direction is prohibited: platform state cannot grant Qor authority or rewrite gate/evidence semantics.

## Phase 2 — Boundary verification

### Affected Files

- `tests/test_portable_governance_boundary.py` — architectural regression test.

### Tests

The test will parse the ADR and platform reference and assert:

1. the canonical role is named `portable governance engine`;
2. the architecture explicitly separates execution adaptation, portable governance evaluation, and enterprise enforcement projection;
3. GitHub-specific mutation is assigned downstream rather than to base Qor;
4. `indeterminate` and `not_projectable` are preserved as required downstream states;
5. the extension reference contains no command/API surface that mutates a forge;
6. the paired Plus issue is cited as the first concrete consumer.

This is a contract/documentation regression test, not proof that an external platform is configured correctly.

## Definition of Done

- Base Qor architecture no longer describes the project only as a prompt system.
- Enterprise enforcement is recognized without entering the base runtime.
- The three adaptation/evaluation/enforcement surfaces have separate owners.
- Downstream mechanical enforcement cannot become semantic authority.
- The paired Plus tracer bullet has a stable base boundary to consume.
- Full repository CI and variant drift pass.

## CI Commands

- `python -m pytest tests/test_portable_governance_boundary.py -q`
- `python -m pytest tests/ -q`
- `python qor/scripts/check_variant_drift.py`
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md`
