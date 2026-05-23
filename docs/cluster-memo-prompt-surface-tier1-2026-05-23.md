# Cluster Memo — Prompt-Surface Remediation Tier 1 (Phases 96-100)

**Date**: 2026-05-23
**Source brief**: `docs/research-brief-prompt-surface-tier1-2026-05-23.md`
**Cluster spans**: Phase 96 → Phase 100
**Cluster owner**: Qor-logic SDLC Orchestrator
**Status**: ratified — execution begins with Phase 96

This memo is a **sequencing artifact**, not a sealable phase plan. It coordinates the five sub-plans that consume the Tier 1 prompt-surface research brief. Each sub-plan is its own `/qor-plan` invocation, its own `plan-qor-phase*.md` file, its own branch, its own audit, its own implementation, and its own seal. There is no cluster-level CI Commands block, no cluster-level Definition of Done, no cluster-level Merkle entry. The cluster's seal is the chain of five per-phase seals.

---

## Sequence (ratified)

| Phase | Surface | Class | Why this position |
|---|---|---|---|
| 96 | GH #108 V1 — recon Reachability Probe | Feature (V1 visibility) | Most-cited surface; ships first so V2 has operator evidence by Phase 99 |
| 97 | F8 — SKILL_REGISTRY per-category drift | Chore (snapshot currency) | Smallest, lowest-coupling; clears a finding masked by total-cancellation before later phases touch the registry |
| 98 | F5+F6 — meta-skill example blocks → `references/` | Chore (progressive disclosure) | Independent of GH #108; consumes Entry #6 fragment decision inline |
| 99 | GH #108 V2 — `/qor-audit` Runtime Contract Walk | Feature (V2 enforcement) | Requires V1 operator evidence; binding-VETO surface so must follow V1 |
| 100 | F4 — Critical Invariants summaries | Chore (additive prose) | Must follow Phase 99 so the new V2 VETO is included in the invariant block from the start (avoids amendment cycle) |

Cross-coupling rationale is documented per-finding in the source brief; the key constraint is **F4 after GH #108 V2** to avoid amending the freshly-written Critical Invariants block as soon as V2 lands.

---

## Per-phase outputs

### Phase 96 — GH #108 V1
- **Branch**: `phase/96-recon-reachability-probe`
- **Closes**: GH #108 (partially — V1 visibility layer only; V2 closes at Phase 99)
- **Scope**: new `qor/scripts/reachability_probe.py` (~250 LOC); `/qor-deep-audit-recon` Phase 3 prose extension (new Round 0); `SG-GrepShapedRunclaim-A` doctrine entry; canonical-repo dogfooding anchor
- **Change class**: feature (minor bump → v0.67.0)
- **DoD tier**: per Phase 92 DoD doctrine (declared in the plan file)

### Phase 97 — F8
- **Branch**: `phase/97-skill-registry-per-category-drift`
- **Closes**: F8 finding (internal review tracker)
- **Scope**: reconcile sdlc +1, memory -2, meta +1 in `qor/skills/SKILL_REGISTRY.md`; add per-category badge currency test that can't be masked by total cancellation
- **Change class**: patch (v0.67.1)

### Phase 98 — F5+F6
- **Branch**: `phase/98-meta-skill-examples-to-references`
- **Closes**: F5+F6 findings (internal review tracker)
- **Scope**: move `qor/skills/meta/qor-meta-log-decision/SKILL.md` Examples block (lines 292-435) to `qor/skills/meta/qor-meta-log-decision/references/example-decision-entries.md`; same for `qor-meta-track-shadow` Examples block (lines 156-219) → `references/example-shadow-genome-events.md`; resolve stranded Entry #6 fragment per Decision Point in plan
- **Decision Point in plan**: Entry #6 fragment at `qor/skills/meta/qor-meta-log-decision/SKILL.md:437` — Option A delete; Option B move to references/; default B (progressive disclosure)
- **Change class**: patch (v0.67.2)

### Phase 99 — GH #108 V2
- **Branch**: `phase/99-audit-runtime-contract-walk`
- **Closes**: GH #108 (fully, when merged)
- **Scope**: new `qor/scripts/runtime_contract_walk.py` (~150 LOC); `/qor-audit` Step 3 Infrastructure Alignment Pass insertion; extend `SG-GrepShapedRunclaim-A` doctrine entry with V2 enforcement clause; requires operator evidence from Phase 96 V1 false-positive rate
- **Change class**: feature (minor bump → v0.68.0)
- **Prerequisite gate**: Phase 96 V1 must have produced at least one operator-validated run before Phase 99 plan can be authored

### Phase 100 — F4
- **Branch**: `phase/100-critical-invariants-summaries`
- **Closes**: F4 finding (internal review tracker)
- **Scope**: ~30 lines per skill (10-line `## Critical Invariants` block + cross-reference paragraph) added to `qor-audit/SKILL.md` and `qor-substantiate/SKILL.md`; structural-placement guard tests; sweep test ensuring no future skill in `governance/` ships without an invariants block
- **Change class**: patch (v0.68.1)
- **Must include**: the Runtime Contract Walk VETO from Phase 99 in the `qor-audit` invariants block (cross-coupling reason for sequencing)

---

## Cluster-wide constraints (apply across all five phases)

1. **Progressive disclosure** (per GH #92 corpus-growth lesson): new sub-pass prose lands in `qor/references/`, not inline in `SKILL.md`. Each phase's `qor-audit` invocation will flag bloat under the Phase 95 skill_size_budget_lint. Phase 98 explicitly applies this; Phases 96/99 must respect it.
2. **Dogfooding anchor** (per Phases 89-95 standard pattern): each phase's primary lint/check must validate against its own plan file before sealing.
3. **Pre-audit lint ladder** (Step 0.6 of `qor-audit`): if any phase adds a new lint, it extends the ladder rather than replacing entries. Phases 96 and 99 may extend; Phases 97/98/100 should not.
4. **Substantiate gate ladder** (Step 4.6 of `qor-substantiate`): same forward-only growth rule. Phase 96 V1 may add a new gate; Phase 99 V2 may extend it; Phases 97/98/100 should not.
5. **SDLC commit trailer**: every phase commit ends with `Authored via [Qor-logic SDLC]` + `Co-Authored-By:` per the standing commit policy.
6. **PR citation lint**: every phase PR body cites its plan file + ledger entry + Merkle seal. Confirmed working pattern from Phases 88-95.
7. **Standing CI fact**: seal PRs are merged via `gh pr merge --admin` due to the default ruleset. Operator confirms admin merge per phase.

---

## What this memo does NOT do

- It does not establish a new doctrine. The "cluster memo" artifact category is project bookkeeping, not governance.
- It does not pre-author any of the five sub-plans. Each `/qor-plan` invocation per phase has full latitude on internal structure.
- It does not commit the cluster to a single PR. Each phase ships its own PR per the established cadence.
- It does not bypass any gate. Each phase enters the standard plan → audit → implement → substantiate flow.

---

## Operator decisions captured at cluster open (2026-05-23)

| Decision | Choice | Rationale |
|---|---|---|
| Cycle shape | Run all 5 phases sequentially through Review Boundary | Per-phase pause for review; mirrors Phases 93-95 autonomous-but-paused pattern |
| Entry #6 fragment | Defer to Phase 98 sub-plan Decision Point | Avoids prejudging F5+F6 design; default to move-to-references |
| Plan structure | Meta-memo (this file) + 5 sub-plans | Established cadence is one-plan-per-phase; meta-memo is sequencing-only |

---

## Cross-references

- `docs/research-brief-prompt-surface-tier1-2026-05-23.md` — source brief that produced this sequencing
- `docs/META_LEDGER.md` — phase seals land here (one entry per sub-plan)
- `qor/references/doctrine-shadow-genome-countermeasures.md` — `SG-GrepShapedRunclaim-A` will be added in Phase 96
- `qor/references/doctrine-definition-of-done.md` — Phase 92 DoD applies to each sub-plan
- `qor/skills/governance/qor-substantiate/SKILL.md` — Step 4.6 ladder may grow in Phases 96/99
