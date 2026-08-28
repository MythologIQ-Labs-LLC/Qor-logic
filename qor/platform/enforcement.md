# Downstream Enforcement Boundary

Canonical Qor-logic is the **portable governance engine**. This reference defines how a downstream enterprise layer may strengthen Qor governance with platform-native enforcement without making the platform a source of Qor semantics.

Decision of record: `docs/ADR_PORTABLE_GOVERNANCE_ENGINE_BOUNDARY.md` (Phase 241, GH #381). Governed-procedure execution evidence semantics are evaluated in GH #384.

## Three separate surfaces

| Surface | Owner | Purpose |
|---|---|---|
| Execution adaptation | Qor-logic | Render and execute the invariant governance contract effectively for the active model/host context. |
| Portable governance evaluation | Qor-logic | Decide what lifecycle, authority, evidence, provenance, gate, and repository contracts mean. |
| Enterprise enforcement projection | Downstream enterprise layer | Project supported desired state and Qor-evaluated conclusions into GitHub or another external enforcement platform. |

These surfaces do not grant authority to one another. A model/host rendering choice cannot alter governance semantics. An external platform control cannot redefine a Qor obligation. A downstream signer or wrapper may produce evidence without becoming the authority that defines the evidence claim.

## Authority direction

```text
Qor invariant contract + evidence semantics
        |
        v
portable governance facts + evidence verdicts
        |
        v
downstream enterprise desired state
        |
        v
platform-specific projection
        |
        v
external mechanical enforcement
```

The reverse direction is prohibited. Platform state is evidence about enforcement, not authority to rewrite Qor lifecycle, evidence, provenance, or actor semantics.

## Governed-procedure execution evidence

If policy requires proof that an exact governed procedure executed, canonical Qor owns the portable evidence satisfaction semantics. A host or trusted downstream wrapper may resolve exact canonical bytes, observe execution, and produce an independently verifiable artifact. Enterprise policy may require an admitted stronger evidence class for higher-risk work.

The producer does not get to redefine what its artifact proves. A GitHub check, workflow, App, comment, label, prompt, or agent declaration may carry or enforce a Qor-evaluated result, but it cannot decide by itself that procedure-execution evidence is valid.

This claim is distinct from a platform projection receipt. Evidence that a governed procedure ran also does not substitute for human approval, merge authority, release authority, or another independent consequence.

## Downstream projection contract

A downstream projection should keep four concepts distinct:

1. **Desired governance contract** - the Qor/enterprise obligations selected for projection.
2. **Platform observation** - normalized evidence describing effective external controls.
3. **Projection plan** - deterministic desired-versus-observed delta.
4. **Projection receipt** - evidence that an authorized platform operation or verification occurred against the exact plan.

Canonical Qor does not define a GitHub/GitLab/Azure DevOps/Bitbucket mutation API for these concepts.

## Required downstream semantics

A downstream adapter MUST preserve the following:

- `indeterminate`: external state cannot prove presence or absence; never treat this as satisfied.
- `not_projectable`: an obligation exists but the adapter has no admitted mapping; never silently drop it.
- semantic authority remains with the Qor/enterprise policy owner rather than platform configuration.
- portable evidence semantics remain with canonical Qor even when a downstream service produces the evidence.
- planning/evaluation authority is separate from platform mutation authority.
- verification binds to the exact projection plan rather than silently recomputing a new desired policy after mutation.
- repository content or an executing agent cannot self-authorize organization/platform administration merely by changing a manifest, workflow, label, or prompt.
- platform success state cannot promote agent self-report into independently observed evidence.

## Base-Qor boundary

The portable governance-gate path remains network independent. Qor may evaluate previously collected external evidence, but a live forge, signer, wrapper service, or organization API is not a prerequisite for gate semantics.

Platform administration and deployment of enterprise trust infrastructure belong downstream. A paired private enterprise tracer bullet is the first concrete consumer of this boundary; its repository identity is intentionally not part of canonical Qor's published contract.
