# ADR: Two-Gap Assurance Boundary and Outer Assurance-Revision Loop

**Status:** Proposed; formal `/qor-audit` required before adoption
**Date:** 2026-09-22
**Scope:** Qor-logic lifecycle, assurance claims, evidence semantics, and production handoff
**Umbrella:** GH #497
**Owning issue:** GH #498

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

The arrows below describe **claim progression and assurance relationships**, not a mandatory universal runtime sequence or new gate order. Profiles may lawfully omit, collapse, repeat, or interleave steps where the governing contract permits it. Omitted or inapplicable steps MUST NOT be represented as PASS merely because work advanced.

### Inner governed change loop

```text
frame -> plan -> audit -> authorize -> implement -> exercise -> observe -> verify
      -> reconcile -> substantiate -> attest -> accept
```

The inner loop establishes claims only within a declared evidence envelope. Acceptance does not itself perform or authorize promotion.

A separately authorized successor may then prepare or perform promotion actions such as merge, release, publish, deploy, or activate where applicable.

### Outer assurance-revision loop

```text
expose/deploy -> observe W -> compare -> classify divergence -> contain if needed
              -> revise R and/or M and/or E and/or implementation -> re-enter inner loop
```

This is likewise a semantic feedback model rather than a mandatory single runtime ordering. Immediate containment may lawfully precede complete causal classification when safety or operational risk requires it, but only under separately established recovery authority.

The outer loop is not "one more validation gate." Production evidence may invalidate assumptions that made an earlier evaluation sufficient.

Qor does not need to become a deployment controller, telemetry platform, or feature-flag service. External systems may execute rollout, observation, containment, and rollback. Qor governs the contracts, authority, evidence binding, invalidation rules, and handoffs.

## Core assurance claims

Qor MUST distinguish at least these claims:

1. **Verification:** observed behavior satisfies a declared contract under evaluated conditions.
2. **Substantiation:** implementation, evidence, documentation, and governed promise reconcile.
3. **Integrity attestation:** evidence/provenance/governance records are intact according to the active trust model.
4. **Acceptance:** the result is acceptable for its intended use under the responsible acceptance authority.
5. **Promotability / promotion authorization:** the evidence and authority required for a specific next promotion action are present. Acceptance alone does not imply this claim.
6. **Operational observation:** production evidence has been examined against the expected envelope.
7. **Current fitness:** available evidence remains sufficient now; this is not implied permanently by a historical PASS.

No upstream claim silently grants authority for a downstream action. In particular:

`accepted != merge-authorized != released != published != deployed != activated`.

## Evidence envelope

Any assurance claim used to advance lifecycle authority MUST bind to a minimum transition envelope sufficient to establish what was actually evaluated and who may rely on it.

The mandatory core for an authority-bearing transition is:

- exact code/artifact/build revision;
- governing requirement, problem, change, or acceptance-contract version as applicable;
- evaluator/check set used for the claim;
- relevant environment model or evaluated conditions;
- evidence sources supporting the claim;
- time/freshness marker;
- explicit exclusions, limitations, untested conditions, or profile-driven `N/A` states;
- authority actor or authority class responsible for the transition where authority is required.

Profiles MAY add stricter fields. A profile MAY omit a condition-specific field only when the omission is explicitly represented as not applicable with rationale; silence must not be interpreted as evidence.

Non-authority informational observations SHOULD still carry the smallest practical envelope needed for later interpretation, but they need not all satisfy the full transition envelope.

The exact storage representation is deferred to implementation planning. This ADR establishes the semantic contract, not a mandatory universal serialization format.

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

## Minimum current-fitness invalidation contract

Consumers that rely on a prior assurance claim MUST treat current fitness as requiring reassessment when any materially relevant member of this minimum invalidation set occurs:

1. **revision/base drift:** the evaluated revision or material base state changes;
2. **contract drift:** governing problem, requirement, change, or acceptance contract changes;
3. **evaluator drift:** evaluator, test, check set, policy, or acceptance method changes materially;
4. **environment-model drift:** relevant assumptions or evaluated conditions change materially;
5. **dependency/external-contract drift:** dependencies, APIs, schemas, platforms, data contracts, or other relied-upon external contracts change materially;
6. **authority drift:** permissions, responsible authority, trust relationship, or required approval changes where relevant to the claim;
7. **freshness expiry:** the governing freshness window expires;
8. **contradictory operational evidence:** new production/runtime/stakeholder evidence materially contradicts assumptions or outcomes supporting the prior claim.

Profiles MAY add invalidation triggers but MUST NOT silently remove these classes where they are relevant.

If the system cannot determine whether a material invalidation trigger occurred, present fitness is **UNESTABLISHED**, not implicitly current-fit. Historical evidence remains preserved.

## Divergence classification

Outer-loop evidence SHOULD classify the smallest supported cause before root-cause repair:

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

## Recovery, containment, rollback, and remediation authority

Recovery/containment and remediation are separate authority domains.

- **Containment / rollback** restores or protects a safe operating state now.
- **Remediation** changes code, architecture, process, policy, or governance to address root cause or recurrence.

A valid divergence classification does not create either authority.

Containment MAY occur before full causal classification when delay would increase material risk, but only under an explicit recovery/containment authority already granted by the applicable contract or operator. That emergency action MUST preserve evidence where practical and MUST NOT be represented as root-cause remediation.

Rollback success does not close the underlying defect automatically. Remediation success does not prove operational recovery automatically.

## Production/tooling boundary

Qor core SHOULD define contracts for:

- authorized exposure envelope;
- required production evidence;
- evidence-to-change binding;
- divergence thresholds;
- human judgment boundaries;
- containment/rollback handoff and authority;
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

## Outer-loop handoff contract

Qor's runtime boundary is vendor-neutral, but the handoff must still be explicit. An outer-loop evidence handoff SHOULD identify, as applicable:

- the release/deployment/artifact observed;
- the relevant evidence envelope;
- observed divergence or changed assumption;
- confidence / inconclusive state;
- containment already taken, if any, and the authority used;
- current-fitness disposition;
- the lawful next owner: research, plan, debug, remediate, acceptance authority, recovery authority, or operator escalation.

Observation or classification alone MUST NOT mutate requirements, implementation, policy, or deployment state without the receiving owner's authority.

## Shadow Genome interaction

Outer-loop divergence is expected to produce recurring evidence patterns. The Shadow Genome architecture is therefore a first-class consumer of this model, not an incidental logging mechanism.

A separate ADR evaluates whether one undifferentiated Shadow Genome remains sufficient or whether Qor needs a typed/spectral family of shadow observations for requirement, model, evaluator, implementation, operational, and governance drift.

Shadow classification remains downstream of the evidence/authority rules here. It must not create mutation authority or rewrite historical causal claims silently.

## Consequences

### Positive

- prevents `CI green`, `substantiate PASS`, or cryptographic attestation from being overstated as production correctness;
- makes authority-bearing evidence envelopes mandatory rather than advisory;
- separates acceptance from promotion authority;
- makes evidence freshness and invalidation enforceable rather than purely narrative;
- provides a lawful route from production evidence back into governed development;
- preserves truthful historical PASS records while allowing present fitness to change;
- keeps Qor vendor-neutral at the production-control boundary;
- separates containment/rollback authority from root-cause remediation authority.

### Costs

- more lifecycle claims require precise terminology;
- authority-bearing transitions need minimum envelope metadata;
- production integrations need explicit adapter/handoff contracts;
- some current documentation that uses `validate`, `complete`, `release`, or `PASS` broadly will require reconciliation;
- review doctrine must distinguish historical integrity from current fitness;
- consumers need explicit handling for `UNESTABLISHED` current fitness rather than optimistic defaults.

## Rejected alternatives

### Treat production as a final static validation phase

Rejected. Production evidence may reveal that the evaluator model or requirements were incomplete. A single terminal gate cannot represent that feedback structure.

### Make Qor a native deployment/observability platform

Rejected. Qor should govern the contract and evidence, not replace specialized runtime infrastructure.

### Treat signed runtime evidence as proof of correctness

Rejected. Provenance and integrity evidence do not prove requirement completeness or world-model fidelity.

### Let acceptance imply promotion authority

Rejected. Acceptance is an assurance decision; merge, release, publish, deploy, and activate are separately authorized actions.

### Treat unknown invalidation state as current-fit

Rejected. Uncertainty about material drift is evidence insufficiency, not positive evidence of continued fitness.

### Invalidate or rewrite every historical PASS after a later failure

Rejected. Later evidence may change current applicability without making the earlier bounded claim dishonest.

## Follow-on work

This ADR requires follow-on planning for:

1. lifecycle state vocabulary and claim semantics;
2. concrete evidence-envelope representation and validation;
3. current-fitness invalidation enforcement;
4. outer-loop adapter/handoff contract;
5. recovery/rollback authority semantics;
6. acceptance and promotability semantics;
7. review documentation updates;
8. Shadow Genome integration;
9. Governance Index and supersession/freshness enforcement.

No runtime implementation is authorized by this proposed ADR until formal `/qor-audit` and an accepted governed plan. Documentation-only correction of the proposal does not itself adopt the ADR.
