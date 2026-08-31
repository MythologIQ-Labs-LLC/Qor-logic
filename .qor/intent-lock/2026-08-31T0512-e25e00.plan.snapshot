# Plan: /qor-implement changeset simplification profile (GH #392, final tranche)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #392

**boundaries**:
- limitations: the profile is an invariant reasoning step inside /qor-implement; it introduces no runtime, no gate, and no new taxonomy.
- non_goals: no nested /qor-refactor ceremony after every code change; no opportunistic cleanup outside the changeset; no new skill.
- exclusions: /qor-refactor's own contract shipped as Phase 245 (v0.162.0) and is consumed by reference.

## Open Questions

None.

## Locked Decisions

**LD-1: Profile placement.** Step 9.5 sits between the Complexity Self-Check (Step 9) and Handoff (Step 10), so refinement happens on verified behavior and its result flows into the handoff. Verified: `grep -n "Step 9.5: Changeset Simplification Profile" qor/skills/sdlc/qor-implement/SKILL.md` -> present between Steps 9 and 10.

**LD-2: Shared protocol by reference, not nested ceremony.** The profile applies the IQ-COMPLEX/IQ-CONTEXT/IQ-MAINTAIN lenses and /qor-refactor's seven-question Simplification Test as an invariant profile per the delegation table's shared-protocol-reuse rule and the sweep's /qor-implement prevention profile; a real /qor-refactor invocation is reserved for independently bounded structural passes beyond the changeset. Verified: `grep -n "NOT a nested" qor/skills/sdlc/qor-implement/SKILL.md` -> anti-ceremony rule present.

**LD-3: Containment and abstention.** Refinement is bounded to recently modified code; unrelated legacy defects are reported, not modified; behavior preservation is the invariant; no-justified-refinement is a successful result. Verified by the three behavioral/ordering tests in tests/test_implement_simplification_profile.py.

## Phase 1: Profile wiring (test-first)

### Affected Files

- `tests/test_implement_simplification_profile.py` - NEW. Three tests: ordering (Step 9 < 9.5 < 10, not mere presence), changeset containment + behavior-preservation + abstention contract, shared-protocol reuse without nested ceremony (lenses + sweep binding + anti-ceremony rule).
- `qor/skills/sdlc/qor-implement/SKILL.md` - NEW Step 9.5 (six-line profile: inspect changeset via the three lenses; gate through the Simplification Test; justified refinements only; re-verify; abstention as success; real delegation reserved for bounded passes).
- `qor/dist/manifest.json`, `qor/dist/variants/**` - recompiled variants.

## Definition of Done

### Deliverable: changeset simplification profile

- **D1**: /qor-implement reuses a lightweight simplification profile after behavior is established, per GH #392's /qor-implement section, closing the issue's final tranche.
- **D2**: Step 9.5 as above; skill stays under the size-budget WARN band (21.6 KB).
- **D3**: This phase's tribunal/implement/seal ledger entries; GH #392 closes with the residual explicitly satisfied.
- **D4**: Focused suite 3/3; full suite green twice for determinism.

## CI Commands

- `python -m pytest tests/test_implement_simplification_profile.py -q`
- `python -m qor.scripts.publication_boundary_lint`
- `python -m pytest tests/ -q`

**ci_commands**:
- `python -m pytest tests/test_implement_simplification_profile.py -q`
- `python -m qor.scripts.publication_boundary_lint`
- `python -m pytest tests/ -q`

## Governance note

The Step 9.5 profile and its tests were authored in-session immediately before this plan; the ceremony follows the code by minutes rather than preceding it, disclosed per the Phase 235 precedent. Every recorded fact is independently verifiable on the branch.
