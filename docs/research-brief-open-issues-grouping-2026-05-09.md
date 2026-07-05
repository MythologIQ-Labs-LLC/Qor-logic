# Research Brief — Open-Issue Phase Grouping

**Date**: 2026-05-09
**Analyst**: The Qor-logic Analyst
**Target**: All 9 open GitHub issues on `MythologIQ-Labs-LLC/Qor-logic` (#38, #39, #40, #41, #42, #43, #44, #45, #46) plus operator-raised backlog item B23 (qor-logic install-freshness check)
**Scope**: Read each issue body; map every concrete change to actual repo surfaces (skills, scripts, schemas, doctrine); identify shared surfaces and dependencies; propose multi-effort phase groupings that minimize repeated touches of the same files.

---

## Executive Summary

The 9 open issues collapse cleanly into **5 multi-effort phases** plus one backlog item. Three drivers determined the groupings: (a) shared edit surface (skills, schemas, doctrine), (b) explicit dependency between issues, (c) thematic coherence so the seal entry reads as one discipline rather than scattered fixes. Two issues (#42 and #46) have a hard sequence (V2 depends on V1). Two issues (#40 and #41) self-identify as paired (#41 is upstream of #40). Four issues (#42, #44, #45, plus implicitly #43) all touch `qor-audit` and the `audit.json` schema. #38 and #39 are structurally independent of the rest.

No DRIFT detected between issue claims and current repo state. All referenced surfaces (skills, scripts, schemas) exist where the issues say they do; no upstream version of `plan_text_consistency_lint.py` exists yet (consistent with #42's premise).

---

## Findings

### F1 — `qor-audit` is the highest-traffic surface across the open issues

**File:line citations**:
- `qor/skills/governance/qor-audit/SKILL.md` (touched by #42, #44, #45, indirectly #41)
- `qor/gates/schema/audit.schema.json` (touched by #42, #44, #45)
- `qor/scripts/cycle_count_escalator.py` (touched by #43)

Four of the nine issues edit the same skill and three edit the same schema. Spreading them across separate phases would mean three audit-skill amendments in three branches with three separate review cycles, each re-touching steps 0, 0.6, and 3. Bundling them lets one schema bump cover all three field additions (`target_content_hash`, `originating_remediation`, `plan_text_consistency_lint_findings`).

### F2 — `plan_text_consistency_lint` is a hard sequence (#42 → #46)

**File:line citations**:
- `qor/scripts/plan_text_consistency_lint.py` — does not exist upstream yet (verified via `Glob qor/scripts/plan_*lint*.py` → no matches).
- `qor/skills/sdlc/qor-plan/SKILL.md` Step 5 review checklist (target of #42 edit 1).
- `qor/references/doctrine-shadow-genome-countermeasures.md` (target of #42 edit 3).

#46 explicitly scopes itself as "V2 backlog for `plan_text_consistency_lint`, sealed at the sibling consumer workspace's META_LEDGER #206 (V1) per upstream-adoption issue #42." V2 cannot land before V1 is upstream. They must be sequenced; bundling them in a single mega-phase would breach the project's "one discipline per phase" pattern visible in `git log --oneline -20` (each phase ships one named feature).

### F3 — #40 + #41 are operator-paired by construction

**File:line citations**:
- Issue #41 body: "this issue establishes the upstream-of-code enforcement that prevents regressions from being introduced in the first place. Both are needed."
- Both edit `qor-plan` Step 7, `qor-audit` Step 3, `qor-implement` Step 5/12.5, and `qor-substantiate` Step 6.
- Both introduce overlapping artifacts: `FEATURE_INDEX.md` (#40) + `feature_inventory_touches` schema field on `plan.schema.json` (#41).

The same operator filed both within 2 days from the same sibling-product v5 incident. #40 fixes seal-time symptoms; #41 fixes the upstream cause. Implementing them separately would mean two passes over the same four skill bodies and a contradictory intermediate state where one gate exists without the other.

### F4 — #38 stands alone but pairs thematically with B23 (host-repo posture)

**File:line citations**:
- `qor/skills/governance/qor-substantiate/SKILL.md` (steps 4.6, 4.6.5, 4.7, 7.4, 7.5, 7.6, 7.7, 7.8, 8.5, 9.5.5 per #38 reproduction table).
- `.qor/workspace.json` archetype detection (already present per `/qor-organize`, cited in #38 proposal option 2).
- Doctrine: `qor/references/doctrine-governance-enforcement.md` (would gain new section on capability-declared steps).
- B23 (BACKLOG line 102 area): "Prompts must self-verify qor-logic installation freshness."

Both #38 and B23 ask the same question: "is the host repo correctly equipped for the cycle that's about to run?" #38 covers per-step prerequisite presence; B23 covers per-cycle install version. They share doctrine surface (governance-enforcement), share session-start checking patterns, and a single `qor.scripts.host_capability` (or similar) module could expose both checks. Bundling them into one phase delivers "host-repo posture" as a coherent unit.

### F5 — #39 is a greenfield subsystem, not a skill amendment

**File:line citations**:
- Proposed package: `qor_logic/compiler/`, `qor_logic/governance/`, `qor_logic/providers/`, `qor_logic/evaluation/` (none exist; verified via `Glob qor_logic/**`).
- Issue body's own §"Initial Implementation Plan" is already 5 internal phases.

#39 introduces an entire subsystem orthogonal to the skill lifecycle. It shares zero edit surface with the other 8 issues. Bundling it with anything else would dilute both initiatives. It is also large enough that the issue itself proposes 5 sequential internal phases — meaning it IS already a multi-effort phase, just not bundled with other issue numbers.

### F6 — `cycle_count_escalator.py` (#43) is bundle-eligible with the lint work

**File:line citations**:
- `qor/scripts/cycle_count_escalator.py` (verified exists via Glob).
- Doctrine: `qor/references/doctrine-governance-enforcement.md` §10.4 cited in #43 body.
- Issue #43 body: "Cycle-count escalation is the framework's safety net for operator recurring blind spots."

#43 reads the same META_LEDGER signature data that `plan_text_consistency_lint` will start emitting via `findings_categories`. Pairing #43 with #46 (V2 lint) lets the session-arc escalator land at the same time the lint becomes precise enough to feed it clean signatures (V2 eliminates the V1 false-positive class per #46.V2.1). Keeping #43 in the V2 wave also keeps it after the V1 lint adoption (#42), which would otherwise leak noisy signatures into the new tracker dimension.

---

## Blueprint Alignment

| Blueprint Claim | Actual Finding | Status |
|----------------|---------------|--------|
| #42: `qor-plan` Step 5 has a review checklist amenable to a new lint instruction | `qor/skills/sdlc/qor-plan/SKILL.md` exists with Step 5 surface (verified path) | MATCH |
| #42: `qor-audit` Step 0.6 hosts pre-audit lints alongside `plan_test_lint` and `plan_grep_lint` | `qor/skills/governance/qor-audit/SKILL.md` exists; lint conventions established by prior phases | MATCH |
| #42: `qor/scripts/plan_text_consistency_lint.py` does not exist upstream | Confirmed via `Glob qor/scripts/plan_*lint*.py` — no matches | MATCH |
| #43: `qor/scripts/cycle_count_escalator.py` exists and currently uses per-artifact threshold | File verified to exist via Glob | MATCH (functional internals not re-verified at line level) |
| #43: doctrine §10.4 governs escalator behavior | `qor/references/doctrine-governance-enforcement.md` exists; section number not byte-checked | MATCH (file presence) |
| #44: plan.schema.json supports declaring `originating_remediation` field | `qor/gates/schema/plan.schema.json` exists; #44 explicitly says field "would need formal schema-side declaration upstream" | MATCH (issue concedes new field needed) |
| #45: `audit.json` lacks `target_content_hash` field | `qor/gates/schema/audit.schema.json` exists; field absence consistent with issue's premise | MATCH (issue explicitly proposes the field) |
| #40, #41: skills exist at `qor/skills/sdlc/qor-{plan,implement}` and `qor/skills/governance/qor-{audit,substantiate}` | All 4 SKILL.md files verified via Glob | MATCH |
| #38: `qor.scripts.secret_scanner`, `qor.scripts.doc_integrity`, `qor.scripts.dist_compile`, etc. are Python modules used by substantiate | Not directly re-verified (issue cites them by module name; substantiate skill body would name them) | UNVERIFIED (not load-bearing for grouping decision) |
| #39: `qor_logic/` package does not exist | No `qor_logic/` directory found; current package is `qor/` | MATCH (greenfield) |

No DRIFT detected. One UNVERIFIED row (does not affect grouping recommendation).

---

## Recommendations

### Proposed Phase Groupings

| Phase | Issues | Theme | Sequence rationale |
|---|---|---|---|
| **α** "qor-audit hardening + plan_text_consistency_lint V1" | #42, #44, #45 | All edit `qor-audit` Step 0/0.6/3 and `audit.schema.json`. One schema bump covers three field additions. | First — establishes the lint and the audit short-circuit/self-application gates that subsequent work depends on. |
| **β** "Plan-quality maturation: session-arc escalation + lint V2" | #43, #46 | V2 lint cleans signatures; session-arc tracker consumes them. | After α (V2 depends on V1; escalator wants clean signatures). |
| **γ** "Feature-level TDD + Inventory Discipline" | #40, #41 | Operator-paired by construction; both edit the same 4 skills. | Independent of α/β; can run in parallel branch if capacity exists, else any order after α. |
| **δ** "Host-repo posture: substantiate portability + install-freshness" | #38 + B23 | Both ask "is the host repo equipped for this cycle?" Share session-start check patterns. | Independent of α/β/γ. Highest leverage for non-Python consumer adoption. |
| **ε** "Target-Aware Governed Prompt Compilation" | #39 | Greenfield subsystem; already a 5-phase internal plan in the issue body. | Independent. Largest scope; should own its own branch family. |

**Total**: 5 multi-effort phases consuming 9 GitHub issues + 1 backlog item (B23). No issue is split across phases. No phase contains an issue whose dependencies live in a later phase.

### Priority ordering (recommended)

1. **α** — closes the active recurring discipline gap that filed 4 of the 9 issues; smallest schema risk; unblocks β.
2. **γ** — closes the sibling-product v5 incident class; independent; high-value for any consumer using SHIELD substantiation.
3. **δ** — unlocks non-Python consumer adoption; pairs the open `Architecture Proposal`-class B23 work with the pre-existing #38.
4. **β** — depends on α; can wait until α has shipped and stabilized.
5. **ε** — largest scope; deserves its own roadmap track once the lifecycle skills are stable.

### Phase artifacts each phase will produce

- **α**: amended `qor-audit` SKILL.md; amended `qor-plan` SKILL.md Step 5; new `qor/scripts/plan_text_consistency_lint.py`; `audit.schema.json` v+1 with three optional fields; new SG entry under `doctrine-shadow-genome-countermeasures.md`.
- **β**: amended `cycle_count_escalator.py` with session-level dimension; amended `plan_text_consistency_lint.py` to V2 (identity grouping, dep_name kind, --apply mode); doctrine update for V2 semantics.
- **γ**: new `qor/references/doctrine-feature-inventory.md`; new `qor/references/doctrine-feature-tdd.md`; `plan.schema.json` v+1 with `feature_inventory_touches`; amended `qor-plan`, `qor-audit`, `qor-implement`, `qor-substantiate` SKILL.md; new `qor/gates/schema/feature_index.schema.json`; one worked example `FEATURE_INDEX.md`.
- **δ**: new `qor.scripts.host_capability` (or similar); each substantiate step gains a `requires:` declaration; capability-skip events emitted to Process Shadow Genome; new `qor.scripts.qor_logic_freshness_check` (B23) hooked at session start across all lifecycle skills.
- **ε**: 5 internal phases per #39 body — IR + single-target compiler; governance gate; rulepack registry; execution modes; evaluation loop. Track separately.

---

## Updated Knowledge

Add to `docs/SHADOW_GENOME.md` (or the analyst's working notes if SG entries are gated):

> **Pattern observed (2026-05-09)**: The sibling consumer workspace (a downstream Qor-logic consumer) filed 5 of the 9 open issues from a single session (2026-05-08T1610-21dfe5). All 5 (#42, #43, #44, #45, #46) describe the same root: framework discipline that would have caught the recurring failure pattern is not load-bearing because it isn't yet runnable upstream. This is the #44 pattern at meta-level: the framework cannot apply its own newest disciplines to its own framework-improvement plans until those disciplines are ported upstream. The α-bundle is the structural answer.

No update needed to existing doctrine. Phase sequencing recommendation lives in this brief and in `docs/BACKLOG.md` once the operator schedules.

---

_Research complete. Findings are advisory — implementation decisions remain with the Governor._
