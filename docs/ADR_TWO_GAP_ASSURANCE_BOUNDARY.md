# ADR: Two-Gap Assurance Boundary and Outer Assurance-Revision Loop

**Status:** Proposed; bounded amendment prepared; formal `/qor-audit` required before adoption
**Date:** 2026-09-22
**Amended:** 2026-09-23
**Scope:** Qor-logic lifecycle, assurance claims, evidence semantics, and production handoff
**Umbrella:** GH #497
**Architecture issue:** GH #498

## Context

Qor-logic provides strong governance for the inner software-development loop: framing, planning, adversarial audit, implementation, verification, substantiation, provenance, and release evidence. That strength can create a dangerous semantic temptation: treating a well-governed inner-loop PASS as if it proves correctness in production or completeness of stakeholder intent.

The two-gap framework described in *Reality Is the Final Verifier* distinguishes two irreducible mismatches:

- **Requirement gap:** stakeholder intent `I` is not identical to written requirements `R` (`I != R`).
- **Model gap:** the open production world `W` is not identical to the evaluator's environment model `M` (`W != M`).

A strong evaluator can reduce preventable errors inside `R` and `M`, but cannot certify that `R` fully captures `I` or that `M` fully captures `W`.

TRACE or another runtime evidence format can strengthen provenance and execution evidence, but evidence integrity is not equivalent to requirement completeness or world-model fidelity.

Qor therefore needs explicit doctrine that bounds assurance claims and defines how production evidence feeds back into requirements, environment models, evaluators, and implementation.

## Decision

Adopt a bounded-assurance model with two coupled loops.

### Inner governed change loop

```text
frame -> plan -> audit -> authorize -> implement -> exercise -> observe -> verify
      -> reconcile -> substantiate -> attest -> acceptance decision
      -> separately authorized promotion action, where applicable
```

The inner loop establishes claims only within a declared evidence envelope.

Acceptance and promotion are separate authority states. An acceptance decision may establish that a result is acceptable for intended use, but it does not itself grant authority to merge, release, publish, deploy, or activate. Each promotion action requires whatever separate authority its owning system or policy requires.

### Outer assurance-revision loop

```text
expose/deploy -> observe W -> compare -> classify divergence -> contain if needed
              -> revise R and/or M and/or E and/or implementation -> re-enter inner loop
```

The outer loop is not "one more validation gate." Production evidence may invalidate assumptions that made an earlier evaluation sufficient.

Qor does not need to become a deployment controller, telemetry platform, or feature-flag service. External systems may execute rollout, observation, containment, and rollback. Qor governs the contracts, authority, evidence binding, invalidation rules, and handoffs.

## Core assurance claims

Qor MUST distinguish at least these claims:

1. **Verification:** observed behavior satisfies a declared contract under evaluated conditions.
2. **Substantiation:** implementation, evidence, documentation, and governed promise reconcile.
3. **Integrity attestation:** evidence/provenance/governance records are intact according to the active trust model.
4. **Acceptance:** the result is acceptable to advance for the intended use under the responsible authority.
5. **Promotion authorization:** the responsible authority permits a specific promotion action such as merge, release, publish, deploy, or activate.
6. **Operational observation:** production evidence has been examined against the expected envelope.
7. **Current fitness:** available evidence remains sufficient now; this is not implied permanently by a historical PASS.

No claim inherits a stronger claim merely by adjacency. In particular, acceptance does not imply promotion authorization, and promotion does not imply current fitness indefinitely.

## Evidence envelope

Evidence binding is proportional, but authority-bearing transitions require a minimum core envelope.

### Mandatory core for authority-bearing transitions

Any assurance claim used to authorize or justify a lifecycle authority transition MUST bind to:

- the exact code, build, artifact, or governed subject revision;
- the governing requirement, acceptance contract, or change-contract version;
- the evaluator/check set used, or an explicit `not_applicable` value with rationale when no evaluator applies;
- the relevant environment model or evaluated conditions, or an explicit `not_applicable` value with rationale;
- the evidence sources that support the claim;
- a time/freshness marker;
- declared exclusions, limitations, or untested conditions, including an explicit `none_known` when appropriate;
- the authority actor, role, or policy basis when the transition requires authority.

A required field may be profile-specific in representation, but it may not disappear silently. `not_applicable` is a governed value, not omission.

### Non-authority claims and enrichment

Claims that do not advance authority SHOULD bind to the smallest practical subset needed to prevent overstatement. Profiles MAY add richer evidence metadata beyond the mandatory core when risk or domain needs justify it.

The exact serialized representation remains an implementation concern. This ADR establishes the semantic minimum and does not require one universal heavyweight schema.

## Historical validity vs current fitness

A prior PASS may remain historically true while becoming insufficient for present fitness.

Example:

```text
PASS(R1, M1, revision X, time T)
        |
production evidence P reveals an unmodeled condition
        |
M1 is revised to M2
        |
old PASS remains part of truthful history
but current fitness becomes CURRENT_FITNESS_NOT_ESTABLISHED
until the affected claim is re-evaluated
```

Qor MUST NOT rewrite historical evidence merely because later evidence changes its present applicability.

`CURRENT_FITNESS_NOT_ESTABLISHED` is a blocking assurance state, not a retroactive failure verdict. A dependent transition that requires current fitness MUST NOT proceed while that state applies.

Unknown or inconclusive invalidation state MUST NOT collapse to current-fit.

## Current-fitness invalidation contract

The following core invalidation classes form the minimum vocabulary. Profiles may add classes, but they must not silently remove or rename these core meanings:

- `REVISION_DRIFT`: the code, build, artifact, or governed base revision changed materially;
- `CONTRACT_DRIFT`: the requirement, acceptance contract, problem contract, or change contract changed materially;
- `EVALUATOR_DRIFT`: the evaluator, check set, policy set, threshold, or interpretation logic changed materially;
- `ENVIRONMENT_DRIFT`: the relevant environment model, configuration, runtime conditions, or deployment assumptions changed materially;
- `DEPENDENCY_DRIFT`: an external dependency, interface, upstream contract, threat model, or platform behavior changed materially;
- `AUTHORITY_DRIFT`: the actor, role, permission, policy basis, or ownership needed for the claim changed materially;
- `FRESHNESS_EXPIRED`: the claim exceeded its governed freshness window or review currency;
- `CONTRADICTORY_EVIDENCE`: new operational, QA, security, compliance, stakeholder, or other material evidence contradicts assumptions supporting the claim.

When an applicable invalidation class is triggered and the affected assurance claim has not yet been re-evaluated, current fitness becomes `CURRENT_FITNESS_NOT_ESTABLISHED`.

Applicability may be resolved by governed profiles and attention/routing mechanisms, but a profile may not convert a material trigger into current-fit by omission. If applicability itself is unresolved, the result remains not established rather than silently fit.

Re-establishing current fitness requires new evidence sufficient for the invalidated dimensions. It does not require rewriting unaffected historical evidence.

## Divergence classification

Outer-loop evidence SHOULD classify the smallest supported cause or set of causes before repair:

- requirement gap: `R` omitted or misstated stakeholder intent;
- model gap: `M` omitted or misstated relevant world conditions;
- evaluator weakness: `E` failed to detect a defect that was representable in `R` and `M`;
- implementation defect: implementation violated the governed contract;
- intent change: stakeholder intent changed after the prior contract;
- world change: dependencies, environment, traffic, threat model, or other relevant conditions changed;
- inconclusive: evidence does not yet support causal classification.

Real incidents may be multi-causal. Classification should preserve supported multiple causes rather than force a false single-cause answer.

Classification does not itself grant mutation authority. Existing Qor ownership and delegation rules remain authoritative.

## Requirement semantics

Requirements are governed hypotheses about stakeholder intent, not authoritative substitutes for stakeholder intent.

A plan may be internally coherent and still target an incomplete requirement set. Qor should therefore preserve the distinction between:

- problem/objective contract;
- change contract;
- acceptance evidence;
- post-exposure stakeholder and operational evidence.

## Production/tooling boundary

Qor core SHOULD define contracts for:

- authorized exposure envelope;
- required production evidence;
- evidence-to-change binding;
- divergence thresholds;
- human judgment boundaries;
- containment/rollback handoff;
- evidence invalidation;
- revision/re-entry into the inner loop.

Qor core SHOULD NOT require any specific rollout, observability, traffic-management, or feature-flag vendor.

## TRACE boundary

When TRACE is consumed, Qor may use TRACE records as evidence of execution identity, runtime, policy, tool use, data handling, provenance, and related trust properties supported by the active TRACE profile.

Qor MUST NOT interpret a valid TRACE record as proof that:

- stakeholder intent was complete;
- the policy itself was complete;
- the evaluator modeled all production conditions;
- the software is semantically correct in all real-world contexts;
- the evidence is hardware-rooted unless the active attestation profile and trust roots establish that fact.

TRACE is evidence infrastructure, not epistemic closure.

## Shadow Genome interaction

Outer-loop divergence is expected to produce recurring evidence patterns. The Shadow Genome architecture is therefore a first-class consumer of this model, not an incidental logging mechanism.

Shadow classification consumes assurance evidence; it does not create mutation, acceptance, or promotion authority. GH #499 remains downstream of this authority/applicability boundary.

A separate ADR evaluates whether one undifferentiated Shadow Genome remains sufficient or whether Qor needs a typed/spectral family of shadow observations for requirement, model, evaluator, implementation, operational, and governance drift.

## Freshness and QA interaction

Governance freshness/supersession work under GH #500 and human-QA/environment evidence under GH #502 are cross-cutting consumers and enforcers of this assurance contract. They do not substitute for adoption or implementation of GH #498.

- GH #500 may provide freshness and supersession signals that trigger `FRESHNESS_EXPIRED`, `CONTRACT_DRIFT`, or `AUTHORITY_DRIFT`.
- GH #502 may provide QA/environment evidence that contributes to the evidence envelope or triggers `ENVIRONMENT_DRIFT` or `CONTRADICTORY_EVIDENCE`.

Neither child architecture may silently redefine the core invalidation vocabulary or promotion authority defined here.

## Consequences

### Positive

- prevents `CI green`, `substantiate PASS`, or cryptographic attestation from being overstated as production correctness;
- makes evidence freshness and invalidation principled rather than ad hoc;
- provides a lawful route from production evidence back into governed development;
- preserves truthful historical PASS records while allowing present fitness to change;
- keeps Qor vendor-neutral at the production-control boundary;
- separates acceptance from merge/release/publish/deploy/activate authority;
- gives acceptance, rollback, observation, and revision a coherent architectural reason to exist.

### Costs

- more lifecycle states require precise terminology;
- evidence claims need a mandatory core envelope when they carry authority;
- production integrations need explicit adapter contracts;
- some current documentation that uses `validate`, `complete`, `release`, or `PASS` broadly will require reconciliation;
- review doctrine must distinguish historical integrity from current fitness;
- profiles must resolve `not_applicable` explicitly rather than silently omitting required evidence dimensions.

## Rejected alternatives

### Treat production as a final static validation phase

Rejected. Production evidence may reveal that the evaluator model or requirements were incomplete. A single terminal gate cannot represent that feedback structure.

### Make Qor a native deployment/observability platform

Rejected. Qor should govern the contract and evidence, not replace specialized runtime infrastructure.

### Treat signed runtime evidence as proof of correctness

Rejected. Provenance and integrity evidence do not prove requirement completeness or world-model fidelity.

### Let acceptance imply promotion authority

Rejected. Acceptance and merge/release/publish/deploy/activate are different claims owned by potentially different authorities.

### Treat unknown invalidation state as current-fit

Rejected. Unresolved applicability or contradictory evidence cannot lawfully advance a current-fitness-dependent transition.

### Invalidate or rewrite every historical PASS after a later failure

Rejected. Later evidence may change current applicability without making the earlier bounded claim dishonest.

## Follow-on work

After formal `/qor-audit` adoption, this ADR requires bounded implementation planning for:

1. lifecycle state vocabulary and claim semantics;
2. evidence-envelope serialization and profile-specific applicability;
3. current-fitness invalidation evaluation;
4. outer-loop adapter/handoff contract;
5. recovery/rollback authority semantics;
6. acceptance and promotion-authorization semantics;
7. review documentation updates;
8. Shadow Genome integration after GH #499's authority boundaries are reconciled;
9. Governance Index freshness/supersession integration under GH #500;
10. human QA/environment evidence integration under GH #502.

No implementation is authorized by this proposed ADR until formal `/qor-audit` and an accepted governed plan.