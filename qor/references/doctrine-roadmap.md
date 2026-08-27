# Doctrine: Experimental Qor Roadmap

**Status:** experimental P1 contract (Phase 238)

`/qor-roadmap` is a program-level meta capability for long-horizon objectives that are not yet responsibly expressible as one implementation plan.

It owns durable prerequisite topology and routing only. It does not replace `/qor-ideate`, `/qor-research`, `/qor-plan`, or any implementation phase.

## Canonical state

The only persisted authority in P1 is:

```text
.qor/roadmaps/<roadmap-id>/events.jsonl
```

The event history is versioned, append-only, path-confined to the Roadmap state root, and reduced in memory on load. There is no persisted state cache in P1.

Supported node kinds are:

- `fact` — evidence the agent can establish; investigation routes to `/qor-research`.
- `decision` — a consequential choice with an explicit required authority.
- `prerequisite` — a non-production condition that must become true.

Implementation tasks are deliberately not Roadmap nodes.

## Frontier contract

The actionable frontier is the complete set of unresolved nodes whose blocking predecessors are resolved and whose required authority is available.

Roadmap may expose graph facts such as direct/transitive dependent counts. It does not turn model estimates of leverage, risk, cost, or uncertainty into an authoritative priority score and it does not auto-select a node in P1.

## Authority and evidence

Facts require evidence pointers when resolved.

Decisions require the exact authority declared on the node. Missing authority is a blocker, not an invitation for the agent to self-authorize.

When a resolved decision is superseded, the old decision remains visible. Already-resolved descendants are marked `needs_review`; Roadmap does not semantically re-decide them.

## Delegation boundary

Per `qor/gates/delegation-table.md`:

- missing problem framing routes to `/qor-ideate`;
- factual investigation routes to `/qor-research`;
- a ready named planning scope routes to `/qor-plan`;
- production implementation never occurs inside Roadmap.

Roadmap records pointers to delegated results. It does not inline the delegated skill's process.

## Plan handoff

A planning scope names the Roadmap nodes and unresolved-space entries that must be settled for one implementation plan to become legal.

Handoff fails closed while any named node is not `resolved` or any named unresolved-space entry remains open.

Handoff also requires a repository-local, readable `ideation.json` or `research.json` artifact whose `phase` field matches the declared predecessor. Roadmap does not manufacture a routine gate override for `/qor-plan`.

A successful handoff contains:

- Roadmap and scope identity;
- objective and exclusions;
- settled fact/decision/prerequisite records with evidence pointers;
- predecessor artifact pointer;
- `legal_next: /qor-plan`;
- an empty `implementation_tasks` list.

The empty task list is deliberate: implementation decomposition belongs to `/qor-plan`.

## P1 exclusions

P1 has no Roadmap-specific leases, concurrent canonical writers, heartbeat/reaping protocol, materialized state cache, external tracker projection, automatic invocation, enterprise orchestration integration, or model-tier routing.

Those features require evaluation evidence before admission.