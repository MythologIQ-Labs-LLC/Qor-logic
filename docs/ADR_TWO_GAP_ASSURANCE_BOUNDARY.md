# ADR: Two-Gap Assurance Boundary and Outer Assurance-Revision Loop

**Status:** Proposed; formal `/qor-audit` required before adoption
**Date:** 2026-09-22
**Scope:** Qor-logic lifecycle, assurance claims, evidence semantics, and production handoff
**Umbrella:** GH #497

## Context

Qor-logic provides strong governance for the inner software-development loop: framing, planning, adversarial audit, implementation, verification, substantiation, provenance, and release evidence. That strength can create a dangerous semantic temptation: treating a well-governed inner-loop PASS as if it proves correctness in production or completeness of stakeholder intent.

The two-gap framework described in *Reality Is the Final Verifier* distinguishes two irreducible mismatches:

- **Requirement gap:** stakeholder intent `I` is not identical to written requirements `R` (`I != R`).
- **Model gap:** the open production world `W` is not identical to the evaluator's environment model `M` (`W != M`).

A strong evaluator can reduce preventable errors inside `R` and `M`, but cannot certify that `R` fully captures `I` or that `M` fully captures `W`.

TRACE or another runtime evidence format can strengthen provenance and execution evidence, but evidence integrity is not equivalent to requirement completeness or world-model fidelity.

Qor therefore needs explicit doctrine that bounds assurance claims and defines how production evidence feeds back into requirements, environment models, evaluators, and implementation.

## Decision

Adopt a bounded-assurance model with two coupled loops:

### Inner governed change loop

```text
frame -> plan -> audit -> authorize -> implement -> exercise -> observe -> verify
      -> reconcile -> substantiate -> attest -> accept/promote as applicable
```

The inner loop establishes claims only within a declared evidence envelope.

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
5. **Operational observation:** production evidence has been examined against the expected envelope.
6. **Current fitness:** available evidence remains sufficient now; this is not implied permanently by a historical PASS.

## Evidence envelope

Material assurance claims SHOULD bind to the smallest practical set of:

- code/artifact revision;
- requirement or acceptance-contract version;
- evaluator/check set;
- environment model or relevant evaluated conditions;
- evidence sources;
- time/freshness marker;
- declared exclusions or untested conditions;
- authority actor where required.

The exact representation is deferred to implementation planning. This ADR establishes the semantic requirement, not a mandatory universal schema.

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
but current fitness is no longer established until re-evaluated
```

Qor MUST NOT rewrite historical evidence merely because later evidence changes its present applicability.

## Divergence classification

Outer-loop evidence SHOULD classify the smallest supported cause before repair:

- requirement gap: `R` omitted or misstated stakeholder intent;
- model gap: `M` omitted or misstated relevant world conditions;
- evaluator weakness: `E` failed to detect a defect that was representable in `R` and `M`;
- implementation defect: implementation violated the governed contract;
- intent change: stakeholder intent changed after the prior contract;
- world change: dependencies, environment, traffic, threat model, or other relevant conditions changed;
- inconclusive: evidence does not yet support causal classification.

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

A separate ADR will evaluate whether one undifferentiated Shadow Genome remains sufficient or whether Qor needs a typed/spectral family of shadow observations for requirement, model, evaluator, implementation, operational, and governance drift.

## Consequences

### Positive

- prevents `CI green`, `substantiate PASS`, or cryptographic attestation from being overstated as production correctness;
- makes evidence freshness and invalidation principled rather than ad hoc;
- provides a lawful route from production evidence back into governed development;
- preserves truthful historical PASS records while allowing present fitness to change;
- keeps Qor vendor-neutral at the production-control boundary;
- gives acceptance, rollback, observation, and revision a coherent architectural reason to exist.

### Costs

- more lifecycle states require precise terminology;
- evidence claims may need additional envelope metadata;
- production integrations need explicit adapter contracts;
- some current documentation that uses `validate`, `complete`, `release`, or `PASS` broadly will require reconciliation;
- review doctrine must distinguish historical integrity from current fitness.

## Rejected alternatives

### Treat production as a final static validation phase

Rejected. Production evidence may reveal that the evaluator model or requirements were incomplete. A single terminal gate cannot represent that feedback structure.

### Make Qor a native deployment/observability platform

Rejected. Qor should govern the contract and evidence, not replace specialized runtime infrastructure.

### Treat signed runtime evidence as proof of correctness

Rejected. Provenance and integrity evidence do not prove requirement completeness or world-model fidelity.

### Invalidate or rewrite every historical PASS after a later failure

Rejected. Later evidence may change current applicability without making the earlier bounded claim dishonest.

## Follow-on work

This ADR requires follow-on planning for:

1. lifecycle state vocabulary and claim semantics;
2. evidence envelope and invalidation doctrine;
3. outer-loop adapter/handoff contract;
4. recovery/rollback authority semantics;
5. acceptance and current-fitness semantics;
6. review documentation updates;
7. Shadow Genome integration;
8. Governance Index and supersession/freshness enforcement.

No implementation is authorized by this proposed ADR until formal `/qor-audit` and an accepted governed plan.