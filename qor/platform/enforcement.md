# Downstream Enforcement Boundary

Canonical Qor-logic is the **portable governance engine**. This reference defines how a downstream enterprise layer may strengthen Qor governance with platform-native enforcement without making the platform a source of Qor semantics.

Decision of record: `docs/ADR_PORTABLE_GOVERNANCE_ENGINE_BOUNDARY.md` (Phase 241, GH #381).

## Three separate surfaces

| Surface | Owner | Purpose |
|---|---|---|
| Execution adaptation | Qor-logic | Render and execute the invariant governance contract effectively for the active model/host context. |
| Portable governance evaluation | Qor-logic | Decide what lifecycle, authority, evidence, gate, and repository contracts mean. |
| Enterprise enforcement projection | Downstream enterprise layer | Project supported desired state into GitHub or another external enforcement platform. |

These surfaces do not grant authority to one another. A model/host rendering choice cannot alter governance semantics. An external platform control cannot redefine a Qor obligation.

## Authority direction

```text
Qor invariant contract
        |
        v
portable governance facts + evidence
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

The reverse direction is prohibited. Platform state is evidence about enforcement, not authority to rewrite Qor lifecycle, evidence, or actor semantics.

## Downstream projection contract

A downstream projection should keep four concepts distinct:

1. **Desired governance contract** — the Qor/enterprise obligations selected for projection.
2. **Platform observation** — normalized evidence describing effective external controls.
3. **Projection plan** — deterministic desired-versus-observed delta.
4. **Projection receipt** — evidence that an authorized operation or verification occurred against the exact plan.

Canonical Qor does not define a GitHub/GitLab/Azure DevOps/Bitbucket mutation API for these concepts.

## Required downstream semantics

A downstream adapter MUST preserve the following:

- `indeterminate`: external state cannot prove presence or absence; never treat this as satisfied.
- `not_projectable`: an obligation exists but the adapter has no admitted mapping; never silently drop it.
- semantic authority remains with the Qor/enterprise policy owner rather than platform configuration.
- planning/evaluation authority is separate from platform mutation authority.
- verification binds to the exact projection plan rather than silently recomputing a new desired policy after mutation.
- repository content or an executing agent cannot self-authorize organization/platform administration merely by changing a manifest, workflow, label, or prompt.

## Base-Qor boundary

The portable governance-gate path remains network independent. Qor may evaluate previously collected external evidence, but a live forge or organization API is not a prerequisite for gate semantics.

Platform administration belongs downstream. The first concrete consumer of this boundary is Qor-logic Plus ADR-0018 / issue #129, which implements a read-only GitHub branch-policy projection tracer bullet.
