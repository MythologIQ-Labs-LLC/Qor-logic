# Spec Grammar (Phase A contract)

Format contract for per-capability behavioral specs under `qor/specs/` and
the deltas that fold into them. Enforced by `qor/scripts/spec_lint.py`;
folded by `qor/scripts/spec_merge.py`. Origin: GH #239 Phase A (Phase 190).

## Spec files (`qor/specs/<capability>/spec.md`)

- One capability per file; a top-level `# Capability: <name>` line opens it.
- Each behavior is a `### Requirement: <name>` block containing:
  - exactly ONE RFC-2119 statement (SHALL or MUST) in the body prose;
  - at least one nested `#### Scenario: <name>`;
  - observable behavior only -- no implementation detail.
- Each scenario carries GIVEN / WHEN / THEN as list bullets (one or more of
  each; case-insensitive; `-` or `*` markers).

## Delta documents

Three optional sections, applied in this order by the merge:

1. `## MODIFIED Requirements` -- complete requirement blocks; the block
   REPLACES the whole existing block with the same heading (restating the
   complete requirement is what makes the merge deterministic).
2. `## REMOVED Requirements` -- a bullet list of requirement headings.
3. `## ADDED Requirements` -- complete requirement blocks, appended in order.

## Failure semantics (loud, never silent)

- MODIFIED or REMOVED naming a heading absent from the spec is an error.
- ADDED duplicating an existing heading is an error.
- These are the concurrency-conflict surfaces: two deltas racing on the same
  requirement must conflict visibly and be re-planned, not auto-merged.

## Brownfield accretion

Spec only what a plan touches; the corpus accretes where change happens.
Legacy behavior without a spec is not a defect -- it is unaccreted territory.

## Phase B (deferred; not yet wired)

Plan-declared deltas, an audit grammar pre-pass routing into the existing
`specification-drift` category, and the fold running inside the seal (after
PASS only) with the folded hash recorded in the ledger entry.
