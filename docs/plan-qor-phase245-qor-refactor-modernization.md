# Plan: Modernize /qor-refactor around behavior-preserving simplification (GH #392, Tranche A)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #392

**boundaries**:
- limitations: Tranche A modernizes the `/qor-refactor` contract only; the `/qor-implement` lightweight simplification profile is a follow-up tranche of GH #392.
- non_goals: no new `/qor-simplify` skill; no automatic line-count minimization; no change to product intent, public behavior, architecture, security policy, or governance decisions under the guise of cleanup; no opportunistic whole-repository cleanup from a changeset scope.
- exclusions: `/qor-harden` and its taxonomy were delivered by Phase 244 and are consumed here by reference, not re-implemented.

## Open Questions

None.

## Locked Decisions

**LD-1: Behavior preservation is the primary invariant.** The rewritten `qor/skills/sdlc/qor-refactor/SKILL.md` centers the seven-question Simplification Test, explicit post-refactor verification fields (behavior preserved YES/NO/INCONCLUSIVE; complexity reduced; clarity improved; contract weakened; scope exceeded; checks executed), and `NO REFACTOR REQUIRED` as a valid successful outcome. Verified: `grep -n "NO REFACTOR REQUIRED" qor/skills/sdlc/qor-refactor/SKILL.md` -> declared as a success path.

**LD-2: Declared scope modes.** `changeset` (recommended post-implementation default), `focused`, `component`, `explicit`; a narrower scope never silently widens into unrelated legacy code. Verified: `grep -n "Do not silently expand" qor/skills/sdlc/qor-refactor/SKILL.md` -> containment rule present.

**LD-3: Environment discovery replaces JS/TS assumptions.** Hard requirements on `package.json`/`main.tsx`/`console.log`/vanilla-JS replacement are removed or demoted to explicitly illustrative examples in `references/qor-refactor-examples.md`; the skill directs discovery of the target environment's own conventions. Verified: `grep -n "package.json" qor/skills/sdlc/qor-refactor/SKILL.md` -> two mentions remain, both non-normative (the do-not-assume disclaimer and a multi-ecosystem example list naming Cargo.toml/pyproject.toml/go.mod/pom.xml alongside it).

**LD-4: Harden boundary consumed by reference (integration addendum after Phase 244 landed).** The skill declares the `/qor-harden` authority boundary: harden discovers/confirms; refactor owns confirmed structurally-scoped behavior-preserving `IQ-COMPLEX`/`IQ-CONTEXT`/`IQ-MAINTAIN` repairs per the remediation profile in `qor/references/implementation-quality-sweep.md`; uncertain failure routes to `/qor-debug`; architecture/intent exceeds refactor authority. The relay's Tranche A predated Phase 244 and correctly refused to fabricate the taxonomy; this promotion adds the linkage now that the canonical surfaces exist.

## Phase 1: Contract rewrite (delivered by the relay implementation, promoted here)

### Affected Files

- `tests/test_qor_refactor_scope_modernization.py` - 11 behavioral contract tests (scope modes, Simplification Test structure, verification fields, JS/TS-hardcoding removal, over-simplification protection, and the Phase 244 harden-boundary binding test added at promotion).
- `qor/skills/sdlc/qor-refactor/SKILL.md` - rewritten contract per LD-1..LD-4.
- `qor/skills/sdlc/qor-refactor/references/qor-refactor-examples.md` - examples labeled illustrative, non-normative; report templates for the Simplification Test, post-refactor verification, and NO REFACTOR REQUIRED.
- `qor/dist/manifest.json`, `qor/dist/variants/**` - recompiled variants (406 files, drift clean).

### Unit Tests

- `tests/test_qor_refactor_scope_modernization.py` - asserts the delivered contracts by reading the skill's declared rules and binding the harden boundary to the canonical sweep so the two surfaces cannot drift silently.

## Definition of Done

### Deliverable: modernized /qor-refactor contract

- **D1**: `/qor-refactor` is rewritten around behavior-preserving simplification rather than raw metric compliance, per GH #392 Tranche A.
- **D2**: The four files above; registry/help/delegation surfaces unchanged (the skill's identity and routing are stable).
- **D3**: This phase's tribunal/implement/seal ledger entries; PR #393 cites this plan and the Merkle seal; GH #392 remains open for the /qor-implement tranche with the residual declared.
- **D4**: Focused suite 11/11; full suite green twice for determinism.

## CI Commands

- `python -m pytest tests/test_qor_refactor_scope_modernization.py -q`
- `python -m qor.scripts.publication_boundary_lint`
- `python -m pytest tests/ -q`

**ci_commands**:
- `python -m pytest tests/test_qor_refactor_scope_modernization.py -q`
- `python -m qor.scripts.publication_boundary_lint`
- `python -m pytest tests/ -q`

## Governance note

The Tranche A rewrite was implemented and tested green by a relay session that disclosed its skipped ceremony and correctly refused to fabricate the then-absent /qor-harden taxonomy. Per the Phase 235 precedent this promotion completes the governance honestly on the integrated head: every fact recorded in the gate artifacts and this plan is a true, independently-verifiable description of delivered work, and the harden linkage is added now that Phase 244's canonical surfaces exist.
