# Plan: Phase 241 - Portable Governance Engine Boundary

**iteration**: 5

**change_class**: feature

**doc_tier**: system

**originating_issue**: GH #381

**related_evidence_issue**: GH #384

**adr**: `docs/ADR_PORTABLE_GOVERNANCE_ENGINE_BOUNDARY.md`

## Boundaries

- **limitations**: Phase 241 defines the base/downstream authority boundary; it does not prove that any enterprise platform can express every Qor obligation and does not design the final governed-procedure receipt schema.
- **non_goals**: no GitHub/GitLab/Azure DevOps API client, no ruleset mutation, no organization controller, no platform webhook receiver, no forge App, no enterprise actor registry, no hosted signer, no procedure-execution receipt implementation.
- **exclusions**: execution-context implementation remains separate; enterprise projection implementation belongs to a downstream private control-plane layer and is not identified in tracked public-repository content.

## Scope Revisions

Iteration 1 proposed rewriting README and the broad legacy architecture overview in the same slice. That added a large, unrelated text diff before the boundary had an executable enterprise consumer.

Iteration 2 narrowed implementation to the ADR, one platform-boundary reference, and its regression test.

Iteration 3 responded to the repository publication-boundary gate. The paired downstream implementation remains coordinated through issue/PR metadata, but canonical Qor tracked files no longer identify the private downstream repository or issue number.

Iteration 5 closes the independent revalidation audit's findings on the rebased head: the carried-over iteration-3 gate artifacts (stale verdict, no provenance sidecars) are removed in favor of this promotion's own ceremony; the extension reference relocates from qor/platform/ (which owns execution-context adaptation) to qor/references/downstream-enforcement-boundary.md; both ADRs register in the governance index; and the boundary tests harden from phrase presence to the reference's actual binding guard sentence, an ordered authority-direction block assertion, and a forge-SDK import scan over executable qor/ code.

Iteration 4 responds to field evidence that policy may require an exact governed procedure while the host cannot actually invoke that procedure and an agent can still imitate its expected output. The original portable/enterprise split survives, but the evidence boundary needed sharpening:

- if exact governed-procedure execution is a governance precondition, canonical Qor owns the portable meaning and satisfaction semantics of that evidence;
- a host or downstream trusted wrapper may produce the concrete observation/attestation;
- an enterprise layer may deploy the observer/signer and choose stronger admitted evidence requirements for risk classes;
- GitHub or another platform may enforce a Qor-evaluated conclusion;
- neither the evidence producer nor the platform becomes semantic authority merely because it owns the mechanism.

Procedure-execution evidence is explicitly distinct from a downstream platform projection receipt and from consequence authority such as human approval or release authority.

The prior iteration-3 same-context audit PASS is historical evidence for iteration 3 only. Formal re-audit/substantiation must evaluate iteration 4.

## Locked Decisions

1. Qor-logic is the portable governance engine, not merely a prompt system and not an enterprise platform administrator.
2. Qor owns lifecycle, authority, evidence, provenance, gate semantics, portable repository contracts, deterministic evaluation, and model/host execution adaptation.
3. When execution of an exact governed procedure is itself a policy precondition, Qor also owns the portable evidence satisfaction semantics for that claim.
4. Enterprise desired-state deployment, repository-fleet reconciliation, platform-native enforcement, organization federation, and deployment of enterprise wrappers/signers belong to downstream control-plane layers.
5. Evidence production and evidence-semantic authority are different responsibilities.
6. A downstream enforcement surface may strengthen mechanical enforcement but may not redefine a Qor semantic.
7. External platform state is evidence. Unknown state is indeterminate rather than assumed satisfied.
8. Unsupported platform mappings must remain explicit `not_projectable` in downstream projection plans.
9. A platform success check cannot promote agent self-report into independently observed procedure evidence.
10. A governed-procedure execution artifact cannot substitute for separate human, merge, release, or other consequence authority.
11. Canonical Qor remains network-independent at governance-gate time; it may consume previously collected external evidence.
12. Phase 241 creates no machine API merely for architectural symmetry. GH #384 inventories existing provenance/attestation machinery before any new portable evidence contract is admitted.
13. Canonical tracked content must not identify a private downstream repository merely to prove cross-project coordination.

## Phase 1 - Architecture contract

### Affected Files

- `docs/ADR_PORTABLE_GOVERNANCE_ENGINE_BOUNDARY.md` - decision of record.
- `qor/references/downstream-enforcement-boundary.md` - extension reference separating execution adaptation, portable evidence semantics, and external enforcement projection (iteration 5: relocated out of qor/platform/, which owns execution-context adaptation, per independent-audit F2).

### Behavior

The documentation must make the following direction unambiguous:

```text
Qor semantics + evidence semantics
        -> downstream enterprise desired state
        -> platform projection
        -> external enforcement
```

The reverse direction is prohibited: platform state cannot grant Qor authority, rewrite gate/evidence semantics, or manufacture independent execution evidence from an agent declaration.

## Phase 2 - Boundary verification

### Affected Files

- `tests/test_portable_governance_boundary.py` - architectural regression tests.

### Tests

The tests parse the ADR and platform reference and assert:

1. the canonical role is named `portable governance engine`;
2. the architecture explicitly separates execution adaptation, portable governance evaluation, and enterprise enforcement projection;
3. GitHub-specific mutation is assigned downstream rather than to base Qor;
4. `indeterminate` and `not_projectable` are preserved as required downstream states;
5. governed-procedure execution evidence semantics remain canonical Qor responsibility even when a downstream wrapper produces evidence;
6. a platform cannot promote agent self-report into independently observed evidence;
7. procedure-execution evidence is distinct from a platform projection receipt and cannot substitute for human/consequence authority;
8. no forge-mutation or hosted-signer surface is created in the base extension reference;
9. the first paired implementation is described only generically as downstream/private rather than identifying an external repository.

This is a contract/documentation regression test, not proof that an external platform is configured correctly or that a particular procedure actually executed.

## Definition of Done

- The ADR defines Qor-logic as the portable governance engine rather than a local-only prompt layer.
- Enterprise enforcement is recognized without entering the base runtime.
- The three adaptation/evaluation/enforcement surfaces have separate owners.
- Portable evidence semantics cannot migrate downstream merely because an enterprise service produces the evidence.
- Procedure-execution evidence and platform projection receipts are not conflated.
- Downstream mechanical enforcement cannot become semantic authority.
- Public tracked content does not disclose a private downstream repository identity.
- Full repository CI and variant drift pass apart from intentionally pending pre-substantiate citation evidence.
- Formal audit/substantiation reflects iteration 4 and does not reuse the historical iteration-3 PASS.

## CI Commands

- `python -m pytest tests/test_portable_governance_boundary.py -q`
- `python -m pytest tests/ -q`
- `python qor/scripts/check_variant_drift.py`
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md`
