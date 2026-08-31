# ADR: Portable Governance Engine and Enterprise Platform Boundary

**Status:** Proposed for Phase 241, revised after governed-procedure evidence review

**Issue:** GH #381

**Related evidence semantics:** GH #384

**Date:** 2026-08-28

## Context

Qor-logic began as a prompt-centered governance system for AI coding agents and has grown into a portable governance framework with deterministic gates, schemas, evidence, policy, host compilation, execution continuity, provenance, and release controls.

A separate downstream enterprise layer may add organization manifests, actor trust, cross-repository impact, CI/review/release governance, federation, deployment evidence, resource governance, and other control-plane responsibilities.

The architecture has therefore reached a boundary that should be explicit rather than inferred.

If canonical Qor absorbs repository-fleet administration or provider-specific enforcement, it stops being portable. If downstream enterprise layers remain only larger prompt/skill packs, organization policy stays too close to the agents and repositories being governed instead of being projected into independent enforcement surfaces.

The correct separation is not "local Qor" versus "enterprise Qor." It is **portable governance semantics** versus **enterprise governance deployment and federation**.

A later field failure sharpened one part of this boundary: if execution of a specific governed procedure is itself a policy precondition, the meaning of evidence that the procedure executed is a portable governance semantic. The concrete observer, signer, CI identity, or hosted wrapper may live downstream, but the fact that it is deployed downstream does not give it authority to redefine what evidence satisfies Qor policy.

## Decision

Qor-logic is the **portable governance engine**.

It owns the semantics that must remain stable regardless of model, host, source-control forge, organization topology, or enterprise platform:

- S.H.I.E.L.D. lifecycle and legal phase transitions;
- authority and delegation semantics;
- PASS / VETO / ABORT meanings;
- evidence and provenance requirements;
- governed-procedure execution evidence meaning when such execution is a policy precondition;
- deterministic repository-local policy evaluation;
- gate and artifact schemas;
- portable repository contracts;
- model/host execution adaptation;
- execution-continuity and verification semantics;
- governance memory and integrity mechanisms that can operate without an organization control plane.

Qor-logic does **not** own enterprise platform administration.

The following belong to downstream enterprise/control-plane layers:

- organization-wide repository policy deployment;
- repository-fleet classification and reconciliation;
- GitHub/GitLab/Azure DevOps/Bitbucket ruleset administration;
- organization custom-property management;
- required-workflow administration;
- forge App or equivalent control-plane operation;
- organization-wide actor identity/trust administration;
- deployment/operation of enterprise wrappers, signers, and service identities;
- cross-repository enforcement and enterprise federation;
- platform webhook/event ingestion;
- platform-native policy mutation and drift repair.

## Authority direction

Authority flows from portable Qor semantics into downstream enforcement projections, never in the reverse direction.

```text
Qor invariant contract + portable evidence semantics
        |
        v
portable repository facts + evidence verdicts
        |
        v
enterprise desired state (downstream)
        |
        v
platform-specific projection (downstream)
        |
        v
GitHub / GitLab / other enforcement
```

A downstream platform may provide stronger mechanical enforcement of a Qor obligation. It may not redefine the obligation.

Examples:

- A GitHub ruleset may mechanically require a check that Qor policy already requires. The ruleset does not become the source of the Qor requirement.
- A required workflow may prevent merge when Qor evidence is absent. The workflow cannot redefine what counts as valid evidence.
- A platform review rule may enforce a minimum approval count. It cannot grant an actor authority that the Qor authority model denies.
- A trusted enterprise wrapper may observe an exact governed procedure execution. It may produce evidence, but the wrapper does not get to define which bindings or evidence class satisfy Qor policy.
- A platform outage or unavailable API may make enforcement indeterminate. Qor must not reinterpret that as policy satisfaction.

## Three distinct adaptation surfaces

Qor must keep three concerns separate.

### 1. Execution adaptation

How a model/host receives and executes the invariant contract. Execution-context adaptive governance owns this concern inside canonical Qor.

### 2. Portable governance evaluation

What the invariant contract means and whether repository evidence satisfies it. Canonical Qor owns this concern. This includes the semantic contract for governed-procedure execution evidence if exact procedure execution is required by policy.

### 3. Enterprise enforcement projection

How supported parts of governance desired state are represented and enforced by GitHub or another external control plane. A downstream enterprise layer owns this concern.

A model profile is not a platform policy. A platform policy is not a Qor semantic. A Qor semantic is not a GitHub ruleset. A downstream signer is not automatically an evidence authority.

## Governed-procedure execution evidence boundary

GH #384 evaluates the portable contract for a specific failure class:

```text
policy requires exact governed procedure
        -> host cannot resolve/invoke it
        -> agent can imitate expected output
        -> plausible artifact exists
        -> no independent evidence proves exact execution
```

Phase 241 does not prescribe a final receipt schema or signing mechanism. It records the ownership rule that constrains that future design.

If Qor policy requires evidence that an exact governed procedure executed, canonical Qor owns the portable satisfaction semantics, including whatever exact-byte, revision/change, subject, currentness, evidence-class, and completeness rules are eventually admitted.

A host or downstream control plane may provide the mechanism that observes or signs the execution. Enterprise policy may require a stronger admitted evidence class for higher-risk work. Neither fact permits the producer to redefine the evidence semantic.

Procedure-execution evidence is also distinct from consequence authority. Evidence that a governed procedure executed cannot substitute for a required human approval, merge authority, release authority, or another independent grant.

## Downstream projection contract

Canonical Qor recognizes four generic concepts without implementing a forge-specific adapter:

1. **Desired governance contract**: the portable Qor facts and obligations that a downstream layer may project.
2. **Platform observation**: externally collected evidence describing the effective state of a platform control.
3. **Projection plan**: a deterministic desired-versus-observed delta produced by the downstream layer.
4. **Projection receipt**: evidence that an authorized downstream operation or verification occurred against the exact plan.

A projection receipt is not the same thing as evidence that a governed skill/procedure executed. They may share generic provenance mechanisms, but they prove different claims and must not be conflated merely because both are called receipts.

These are responsibility boundaries, not new base-Qor APIs in Phase 241.

A downstream projection must preserve these rules:

- unknown external state is `indeterminate`, never satisfied by assumption;
- unsupported obligations are explicit `not_projectable`, never silently dropped;
- mutation authority is separate from planning/evaluation authority;
- platform state is evidence, not semantic authority;
- a target repository or governed agent must not be able to self-authorize administrative enforcement changes merely by editing repository content;
- a target repository, prompt, platform comment, or agent declaration must not redefine Qor evidence strength or satisfaction;
- verification binds to the exact desired-state plan rather than recomputing an unconstrained new interpretation after mutation.

## Network and mutation boundary

Canonical Qor remains network-independent at governance-gate time.

Repository-local deterministic evaluation may consume previously collected external evidence, including independently produced execution evidence, but base gate semantics must not require live access to GitHub, GitLab, an organization API, or an enterprise service.

Existing operator-selected delivery actions such as push/PR creation remain explicit delivery operations. They do not create a general platform-administration authority in Qor.

## Relationship to downstream enterprise layers

A downstream enterprise control plane may be built above this boundary.

Its responsibility is to:

- resolve organization and repository desired state;
- classify enterprise actors and repository participation;
- project supported desired state into enterprise platforms;
- compare desired and effective platform state;
- detect drift;
- require separate authority for mutation;
- deploy or administer trusted wrappers/signers when enterprise policy requires them;
- record platform projection/verification receipts;
- consume canonical Qor evidence semantics rather than redefine them;
- federate conclusions across repositories without redefining canonical Qor semantics.

The first paired implementation is intentionally maintained outside this public repository and exercises a read-only GitHub branch-policy projection tracer bullet against this contract. Its private repository identity is not part of canonical Qor's published architecture.

## Rejected alternatives

### Make Qor-logic local-only

Rejected. Qor already ships repository artifacts, CI-compatible checks, host variants, release semantics, provenance, and portable controls. Calling it local-only understates and artificially limits the base.

### Put GitHub administration in canonical Qor

Rejected. It creates forge coupling, network requirements, organization-permission assumptions, and a temptation to treat platform configuration as semantic authority.

### Let a downstream enterprise layer own evidence meaning because it owns the signer

Rejected. Producing evidence and defining the semantic claim are different authorities. This would let each enterprise adapter redefine Qor satisfaction and would directly contradict the portable-engine boundary.

### Keep the enterprise layer as only a larger skill/prompt pack

Rejected. An enterprise layer that owns organization policy but never projects it into independent controls leaves enforcement unnecessarily close to the governed repository.

### Let each consumer repository implement its own platform mapping

Rejected. It duplicates policy mapping, produces drift, and allows the governed repository to sit too close to the mechanism that constrains it.

## Consequences

Positive:

- canonical Qor remains forge- and enterprise-provider-neutral;
- downstream enterprise layers gain a clear deployment/reconciliation responsibility;
- external enforcement can be stronger without contaminating Qor semantics;
- governed-procedure evidence can gain independent observation without creating a second semantic authority;
- execution-context adaptation and platform enforcement no longer compete for the same "platform" abstraction;
- future GitHub/GitLab/Azure DevOps adapters can share enterprise projection concepts without entering base Qor.

Costs:

- some concepts exist in both semantic and enforcement forms and require explicit mapping;
- downstream layers must track `not_projectable` obligations rather than pretending every Qor control has a native platform equivalent;
- platform mutation requires its own authority, receipts, and drift verification rather than piggybacking on repository write access;
- governed-procedure execution evidence, if admitted by GH #384, needs a clear producer/verifier trust boundary without making base-Qor gates network dependent.

## Phase 241 scope

Phase 241 records this architecture in this ADR and the concise `qor/references/downstream-enforcement-boundary.md` extension-boundary reference (deliberately housed with the doctrine/reference corpus rather than under `qor/platform/`, which owns execution-context adaptation -- the two concerns this ADR separates do not share a namespace), with regression tests that protect the responsibility split.

Phase 241 adds no GitHub API client, ruleset schema, organization controller, platform mutation code, hosted signer, procedure-execution receipt implementation, remote dependency, README rewrite, or broad architecture-document rewrite.

The earlier iteration-3 same-context audit PASS predates the GH #384 evidence-boundary sharpening. It remains historical evidence for iteration 3 only. Formal re-audit/substantiation must evaluate the revised boundary before the phase is considered complete.
