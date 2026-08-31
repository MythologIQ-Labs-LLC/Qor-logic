# Reference: governed-procedure execution evidence

Status: Phase 242 portable contract, V1 draft reference.

## Purpose

Some governance policies require more than a plausible artifact. They require evidence that an exact governed procedure executed against an exact governed subject.

This reference defines what that evidence means in canonical Qor. It deliberately does not define a universal signer service or platform-specific enforcement mechanism. Promotion to formal doctrine is deferred until the normal audit/substantiation path admits the contract.

## Three distinct things

Keep these separate:

1. **Procedure requirement** — policy says an exact governed procedure must execute for an exact subject.
2. **Execution claim** — a record says a particular invocation completed using particular procedure/subject bindings.
3. **Independently verified execution claim** — a trusted boundary verified a concrete attestation that is cryptographically or otherwise strongly bound to the exact execution claim.

A plausible output is not execution evidence. An execution claim is not automatically independently verified. An independently verified claim is not human approval or release authority.

## Exact procedure identity

V1 identifies a procedure by the complete tuple:

- name;
- repository;
- revision;
- path;
- SHA-256 of the exact procedure bytes.

All fields compare exactly. Canonical Qor does not normalize repositories, infer aliases, follow mutable names, or treat two similarly named procedures as equivalent.

The byte digest is load-bearing. Same name plus different bytes is a different procedure for governance purposes.

## Exact governed-subject identity

V1 identifies the governed subject by:

- kind;
- repository;
- id;
- revision;
- SHA-256 of the governed subject/change state.

All fields compare exactly. Evidence from another repository, another change, or an earlier head therefore cannot satisfy the requirement.

When policy also requires an exact input/change-set digest, `inputSha256` becomes part of the required binding.

## Evidence classes are categorical

V1 recognizes only:

- `agent-declared`
- `wrapper-observed`
- `ci-attested`

These classes are not a universal numeric ladder. They establish different facts under different trust assumptions.

Policy must explicitly list the classes it accepts. A verifier never upgrades one class into another merely because some additional metadata exists.

In particular, externally verifying an `agent-declared` record does **not** transform it into `wrapper-observed` evidence.

`human-declared` is deliberately absent from V1. An unauthenticated JSON label claiming a human declaration would be mintable by the governed actor and would therefore sound stronger than the contract could prove. A future authenticated-human evidence class requires explicit identity and verification semantics before admission.

## Independently observed classes

`wrapper-observed` and `ci-attested` require independent verification.

A requirement accepting either class must declare one or more trusted principals. The evidence claim must identify an observer, and the evaluator must receive a trusted `VerifiedClaim` fact whose:

- evidence id matches;
- principal id matches the evidence observer;
- claim SHA-256 matches the canonical digest of the exact evidence claim.

This binds independent verification to all fields in the claim, including procedure identity, subject identity, status, observer, input/output digests, and invocation id.

## Trusted verification facts are a separate input

`VerifiedClaim` facts are not fields inside the JSON evidence contract.

That separation is intentional. If the evidence producer could serialize `verified: true` beside its own claim, the evidence producer would also become its own trust authority, which defeats the point with impressive efficiency.

Concrete signature/HMAC/workload-identity verification belongs to the trusted host boundary. That boundary passes only the resulting claim-bound fact to the canonical evaluator.

Canonical Qor defines the satisfaction semantics. The host/provider defines how it authenticates the principal strongly enough to create the trusted fact.

## Required-set completeness

Evaluation is over the policy-derived **required set**, not merely the evidence that happens to be present.

Every requirement receives an explicit result. A collection of valid evidence fails overall when any required procedure lacks satisfying evidence.

This is the completeness lesson from prior projection failures: validating every supplied item is not the same as proving nothing required was omitted.

## Execution status

Only `completed` satisfies V1.

A procedure may complete and produce an adverse governance conclusion such as VETO. That is still a completed execution. A crashed or failed invocation does not satisfy the execution requirement.

The evaluator does not interpret an optional output digest as approval.

## Replay and currentness

V1 rejects replay through exact binding, not wall-clock freshness:

- prior subject revision -> mismatch;
- another change id -> mismatch;
- another repository -> mismatch;
- wrong procedure revision/path/bytes -> mismatch;
- verification copied from a different evidence claim -> claim digest mismatch.

Time-based expiry may be added later only where a policy genuinely needs it. It is not smuggled into V1 as a vague notion of "recent."

## Requirements are policy input from an uncontrolled trust domain

The same argument that keeps verified claims outside the evidence JSON applies to the requirements array: `acceptedEvidenceClasses` and `trustedPrincipals` decide what counts, so whoever authors them is the evidence policy authority. The requirements array MUST originate from a trust domain the evidence producer does not control (repository policy, a governing plan, or a downstream policy engine consuming this contract). An actor who authors both the requirements and the evidence can trivially satisfy the contract by accepting `agent-declared` everywhere -- that outcome is a policy decision by the requirements author, never an evaluator guarantee. The evaluator enforces satisfaction rules over the declared policy; it cannot detect that the policy itself was authored by the party it constrains.

## Existing provenance primitives

Phase 158 local HMAC provenance and CI attestation remain useful, but they prove different claims.

- local sidecars provide tamper evidence with the documented in-repository-actor ceiling;
- CI attestation proves trusted CI verified particular sealed ledger hashes where the CI secret exists.

Neither is silently redefined as proof that a governed procedure executed. A trusted host integration may reuse those or stronger mechanisms where appropriate, then pass a claim-bound verified fact into this evaluator.

## Consequence authority stays separate

Procedure execution evidence never grants, implies, or substitutes for:

- human approval;
- merge authority;
- release authority;
- production-write authority;
- exception/override authority;
- any other independent governance consequence.

Those remain governed by their own authority contracts.

## V1 non-goals

V1 does not:

- prove model cognition;
- create a PKI;
- host a signer;
- define GitHub checks/rulesets;
- rank evidence classes with a model or score;
- require strong evidence for every skill;
- persist trusted-principal state;
- silently approximate an unavailable governed procedure.
