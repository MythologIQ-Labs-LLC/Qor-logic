# RESEARCH_BRIEF: Documentation-Integrity Enforcement in Qor-logic Skills

**Session:** recon-doc-integrity-2026-04-17
**Target:** Qor-logic skill prompts (not this repo's own docs)
**Scope:** Identify where skill prompts fail to *generate and enforce* documentation-integrity patterns (topology, glossary, concept→artifact mapping, cross-doc consistency, coverage, boundaries, reading flow, terminology). Repo state serves as dogfood evidence.
**Status:** Phase 3 verification complete (3 rounds). Ready for handoff.

---

## Executive Summary

Qor-logic skill prompts currently produce code-correct, plan-correct, substantiation-sealed output, but they do **not** require or verify that the consuming repo's documentation behaves as a coherent system. The repo itself exhibits the symptom class:

- 5 canonical documentation artifacts missing or degraded (CONTRIBUTING, root CHANGELOG, OPERATIONS, GLOSSARY, concept→artifact MAP).
- 14+ domain terms in use with no registry; the word **"Phase"** carries 3 unrelated meanings across SDLC / skill steps / execution stages with no disambiguator.
- 23 of ~30 doctrines/patterns are reachable but orphaned from any declared entry point.
- `workflow-bundles.md` phase list omits `validate` and `remediate` — contradicts `chain.md` master list.
- 3 concepts (Doctrines layer, Shadow Genome, change_class) have split or absent homes.
- No skill currently mandates boundary declarations (limitations, non-goals, unsupported scenarios).

**Risk grade: B+ on machinery, D+ on wayfinding.** The fix is not to patch this repo — it is to upgrade the skill prompts so any repo running Qor-logic through full lifecycle ends up with system-shaped documentation. This repo will improve as a byproduct.

**Top-5 most critical prompt gaps:**

1. `GAP-PROMPT-01` — `/qor-plan` does not require plans to declare a `doc_tier` and a `concept → artifact → reference` mapping block.
2. `GAP-PROMPT-02` — No doctrine exists for documentation integrity; no gate reads one.
3. `GAP-PROMPT-03` — `/qor-substantiate` does not verify glossary presence, term-drift, or orphan concepts; seal passes on docs that violate integrity.
4. `GAP-PROMPT-04` — `/qor-audit` has no rubric for cross-doc consistency (conflicts between docs go unflagged).
5. `GAP-PROMPT-05` — No skill enforces "every transition in the system must be explained somewhere" (coverage rule).

---

## Gap Categories

### Category A — Missing Doctrine
`GAP-PROMPT-DOCTRINE-*`: there is no `doctrine-documentation-integrity.md`. All other gaps trace back to the absence of this authority.

### Category B — Plan-layer gaps
`GAP-PROMPT-PLAN-*`: `/qor-plan` does not require doc-integrity declarations in the plan itself, which is the only point where enforcement can be asserted without runtime.

### Category C — Substantiate-layer gaps
`GAP-PROMPT-SUB-*`: `/qor-substantiate` does not verify the claims a plan should have made (glossary, topology, mapping).

### Category D — Audit-layer gaps
`GAP-PROMPT-AUDIT-*`: `/qor-audit` has no rubric for cross-doc consistency, orphan concepts, or terminology drift.

### Category E — Terminology / self-consistency gaps (this repo, dogfood)
`GAP-REPO-*`: places where Qor-logic itself violates the integrity it should be enforcing. Fixed as byproduct, not as primary work.

---

## Gap IDs

### Category A — Doctrine

| ID | Gap | Severity | Effort | Blocks-GA | Evidence (file:line) |
|---|---|---|---|---|---|
| `GAP-PROMPT-DOCTRINE-01` | No `doctrine-documentation-integrity.md` defining the canonical patterns (topology, glossary, concept→artifact map, boundaries, reading order, coverage, terminology, consistency). All downstream gaps depend on this. | CRIT | M | YES | `qor/references/` (13 doctrines; none cover doc integrity) |

### Category B — Plan-layer

| ID | Gap | Severity | Effort | Blocks-GA | Evidence |
|---|---|---|---|---|---|
| `GAP-PROMPT-PLAN-01` | `/qor-plan` does not require plans to declare `doc_tier: minimal\|standard\|system` and a corresponding topology-requirements block. | HIGH | S | YES | `qor/skills/sdlc/qor-plan/SKILL.md` (no such requirement) |
| `GAP-PROMPT-PLAN-02` | `/qor-plan` does not require a `concept → artifact → reference` mapping block for new concepts introduced by the plan. | HIGH | S | YES | same |
| `GAP-PROMPT-PLAN-03` | `/qor-plan` does not require plans to declare `limitations`, `non_goals`, `exclusions` for the feature being planned. | MED | S | NO | same |
| `GAP-PROMPT-PLAN-04` | `/qor-plan` does not require plans to list **terms introduced** with canonical definitions (forces glossary maintenance). | HIGH | S | YES | same |
| `GAP-PROMPT-PLAN-05` | `/qor-plan` plan schema in `qor/gates/schema/plan.schema.json` (referenced in Step Z) does not validate doc-integrity fields. | HIGH | S | YES | `qor/skills/sdlc/qor-plan/SKILL.md` Step Z references schema; schema itself untouched |

### Category C — Substantiate-layer

| ID | Gap | Severity | Effort | Blocks-GA | Evidence |
|---|---|---|---|---|---|
| `GAP-PROMPT-SUB-01` | `/qor-substantiate` does not verify that terms declared in the plan are present in the canonical glossary and used consistently. | HIGH | M | YES | `qor/skills/governance/qor-substantiate/SKILL.md` (no glossary check step) |
| `GAP-PROMPT-SUB-02` | `/qor-substantiate` does not verify topology requirements asserted by the plan (e.g., "plan declared `doc_tier: standard` → verify glossary.md + architecture.md exist"). | HIGH | M | YES | same |
| `GAP-PROMPT-SUB-03` | `/qor-substantiate` does not verify concept→artifact mapping promises from the plan (new concept X introduced → has a home file → referenced from at least one consumer). | HIGH | M | YES | same |
| `GAP-PROMPT-SUB-04` | No helper script `qor/scripts/doc_integrity.py` to mechanize these checks (parallel to `changelog_stamp.py`). | MED | M | NO | `qor/scripts/` (no such script) |

### Category D — Audit-layer

| ID | Gap | Severity | Effort | Blocks-GA | Evidence |
|---|---|---|---|---|---|
| `GAP-PROMPT-AUDIT-01` | `/qor-audit` has no rubric entry for cross-doc consistency (same concept defined differently in multiple files). | MED | S | NO | `qor/skills/governance/qor-audit/SKILL.md` |
| `GAP-PROMPT-AUDIT-02` | `/qor-audit` does not flag orphan concepts (used in N places, defined nowhere) or orphan docs (nothing links to them). | MED | S | NO | same |
| `GAP-PROMPT-AUDIT-03` | `/qor-audit` does not check whether a plan that introduces a new concept has corresponding glossary + home updates. | MED | S | NO | same |

### Category E — Repo dogfood (byproduct, not primary)

| ID | Gap | Severity | Effort | Blocks-GA | Evidence |
|---|---|---|---|---|---|
| `GAP-REPO-01` | `qor/gates/workflow-bundles.md` phase list omits `validate` and `remediate`; contradicts `qor/gates/chain.md:9`. | HIGH | XS | NO | Cross-doc consistency vector finding #2 |
| `GAP-REPO-02` | "Phase" has 3 unrelated senses (SDLC / skill-step / execution-stage) with no canonical disambiguator. | HIGH | S | NO | Terminology vector: `chain.md:9` vs `qor-specialist.md:201` vs `SYSTEM_STATE.md:9` |
| `GAP-REPO-03` | No `qor/references/glossary.md`. | HIGH | S | NO | Topology + Terminology vectors |
| `GAP-REPO-04` | No concept→artifact map. 3 orphan-risk concepts: Doctrines layer, Shadow Genome (3-way split), change_class (tests orphaned from doctrine). | HIGH | S | NO | Concept-mapping vector |
| `GAP-REPO-05` | CLAUDE.md uses bare backtick paths instead of markdown links; 23 of ~30 doctrines/patterns orphan from README/CLAUDE.md. | MED | XS | NO | Reading-flow vector |
| `GAP-REPO-06` | `change_class` vs `change_type` inconsistency; `<phase>` XML tag case inconsistent with YAML frontmatter. | LOW | XS | NO | Cross-doc vector |
| `GAP-REPO-07` | No CONTRIBUTING.md, no root CHANGELOG.md, no OPERATIONS.md. | MED | S | NO | Topology vector |

---

## Summary Matrix

| ID | Category | Severity | Effort | Blocks-GA | Status |
|---|---|---|---|---|---|
| GAP-PROMPT-DOCTRINE-01 | Doctrine | CRIT | M | YES | CONFIRMED |
| GAP-PROMPT-PLAN-01 | Plan | HIGH | S | YES | CONFIRMED |
| GAP-PROMPT-PLAN-02 | Plan | HIGH | S | YES | CONFIRMED |
| GAP-PROMPT-PLAN-03 | Plan | MED | S | NO | CONFIRMED |
| GAP-PROMPT-PLAN-04 | Plan | HIGH | S | YES | CONFIRMED |
| GAP-PROMPT-PLAN-05 | Plan | HIGH | S | YES | CONFIRMED |
| GAP-PROMPT-SUB-01 | Substantiate | HIGH | M | YES | CONFIRMED |
| GAP-PROMPT-SUB-02 | Substantiate | HIGH | M | YES | PARTIAL |
| GAP-PROMPT-SUB-03 | Substantiate | HIGH | M | YES | CONFIRMED |
| GAP-PROMPT-SUB-04 | Substantiate | MED | M | NO | CONFIRMED (script absent) |
| GAP-PROMPT-AUDIT-01 | Audit | MED | S | NO | CONFIRMED |
| GAP-PROMPT-AUDIT-02 | Audit | MED | S | NO | PARTIAL |
| GAP-PROMPT-AUDIT-03 | Audit | MED | S | NO | CONFIRMED |
| GAP-REPO-01 | Repo dogfood | HIGH→MED | XS | NO | CONFIRMED (example, not canon — reduced) |
| GAP-REPO-02 | Repo dogfood | HIGH | S | NO | CONFIRMED |
| GAP-REPO-03 | Repo dogfood | HIGH | S | NO | CONFIRMED |
| GAP-REPO-04 | Repo dogfood | HIGH | S | NO | CONFIRMED |
| GAP-REPO-05 | Repo dogfood | MED | XS | NO | CONFIRMED |
| GAP-REPO-06 | Repo dogfood | LOW | XS | NO | CONFIRMED |
| GAP-REPO-07 | Repo dogfood | MED | S | NO | CONFIRMED |

---

## Sprint Plan (ordered for remediation)

### Sprint 1 — Authority layer (foundation, enables everything else)
- `GAP-PROMPT-DOCTRINE-01` — author `doctrine-documentation-integrity.md`: define tiers (`minimal|standard|system`), the 8 patterns, canonical checks, failure modes.
- `GAP-PROMPT-PLAN-05` — extend `qor/gates/schema/plan.schema.json` with doc-integrity fields.

### Sprint 2 — Plan-layer enforcement (WHERE enforcement lives)
- `GAP-PROMPT-PLAN-01` — require `doc_tier` in plan frontmatter.
- `GAP-PROMPT-PLAN-02` — require `concepts:` block (concept → home → references).
- `GAP-PROMPT-PLAN-04` — require `terms:` block for new terms.
- `GAP-PROMPT-PLAN-03` — require `boundaries:` block.

### Sprint 3 — Substantiate-layer verification (gates pass or fail)
- `GAP-PROMPT-SUB-04` — build `qor/scripts/doc_integrity.py` (glossary check, topology check, mapping check, orphan scan). Tests first.
- `GAP-PROMPT-SUB-02`, `SUB-03`, `SUB-01` — wire `/qor-substantiate` to invoke the script; fail-fast on violations.

### Sprint 4 — Audit rubric (catches drift between plans)
- `GAP-PROMPT-AUDIT-01`, `AUDIT-02`, `AUDIT-03` — extend `/qor-audit` checklist.

### Sprint 5 — Dogfood this repo (byproduct)
- `GAP-REPO-01` → `GAP-REPO-07` — run the freshly-upgraded skills against Qor-logic itself. The repo now passes its own gates. If it doesn't, the prompts aren't strong enough — iterate.

**Prerequisite chain:** Sprint 1 → Sprint 2 → Sprint 3 → Sprint 4 → Sprint 5. Do not parallelize; each sprint asserts the previous sprint's contract.

---

## Open Questions (resolved in verification)

1. ~~Is `qor/gates/schema/plan.schema.json` actually present?~~ **RESOLVED:** YES — 9 schema files exist under `qor/gates/schema/` (audit, implement, plan, remediate, repos_config, research, substantiate, validate, shadow_event). The concept-mapping subagent's "not found" note was a **HALLUCINATION** (Round-2 hallucination scan confirms: files glob-visible, subagent just didn't look). Resolution: `plan.schema.json` currently has 5 required fields (`phase`, `ts`, `session_id`, `plan_path`, `phases`) plus optional `open_questions`. Doc-integrity fields need to be added here per GAP-PROMPT-PLAN-05.
2. ~~Does `qor/scripts/` follow a convention for helper scripts?~~ **RESOLVED:** YES — 23 Python modules present, including `changelog_stamp.py`, `gate_chain.py`, `session.py`, `shadow_process.py`, `governance_helpers.py`. `doc_integrity.py` should follow the same pattern: module with public functions, raises `ValueError` on violations, called from SKILL.md step blocks.
3. Tier model (A tiered / B fixed-with-escape / C strict): **still open** — design decision for the paused `/qor-plan` dialogue, not a verification question.

## Verification log

### Round 1 — CRIT/HIGH gap confirm (file:line)

| Gap | Status | Evidence |
|---|---|---|
| GAP-PROMPT-DOCTRINE-01 | CONFIRMED | `qor/references/doctrine-*.md` — 13 files, none cover doc integrity |
| GAP-PROMPT-PLAN-01 | CONFIRMED | `qor/skills/sdlc/qor-plan/SKILL.md:119-146` plan structure has Open Questions + Phases + Affected Files + Changes + Unit Tests; no `doc_tier` |
| GAP-PROMPT-PLAN-02 | CONFIRMED | same file; no concept→artifact block in Plan Structure |
| GAP-PROMPT-PLAN-03 | CONFIRMED | same file; no `boundaries:` / limitations / non-goals section |
| GAP-PROMPT-PLAN-04 | CONFIRMED | same file; no `terms:` block |
| GAP-PROMPT-PLAN-05 | CONFIRMED | `qor/gates/schema/plan.schema.json:7` required = `[phase, ts, session_id, plan_path, phases]`; no doc-integrity fields |
| GAP-PROMPT-SUB-01 | CONFIRMED | `qor/skills/governance/qor-substantiate/SKILL.md` — no step reads glossary or checks term drift |
| GAP-PROMPT-SUB-02 | **PARTIAL** | Step 3 Reality Audit (line 103-117) checks file-tree match against ARCHITECTURE_PLAN.md, but doctrine-level topology not checked. Reality=Promise is file-level only. |
| GAP-PROMPT-SUB-03 | CONFIRMED | same file; no concept→artifact mapping verification |
| GAP-PROMPT-AUDIT-01 | CONFIRMED | `qor/skills/governance/qor-audit/SKILL.md:91-209` 8 audit passes (Security, OWASP, Ghost UI, Razor, Dependency, Macro-Arch, Orphan); none check cross-doc terminology consistency |
| GAP-PROMPT-AUDIT-02 | **PARTIAL** | Macro-Level pass (line 178-194) has "Single source of truth for shared types/config" — but this is code-level, not doc concept mapping. Orphan Detection (line 196-208) covers file-build-path orphans, not concept orphans. |
| GAP-PROMPT-AUDIT-03 | CONFIRMED | no audit pass verifies plan-introduced concepts have glossary/home updates |
| GAP-REPO-01 | CONFIRMED | `qor/gates/workflow-bundles.md:23` example shows `phases: [research, plan, audit, implement, substantiate]` — missing `validate` + `remediate` vs chain.md master. **Reduced severity note:** this is an EXAMPLE bundle metadata, not a canonical definition. Still confusing for readers building new bundles. |
| GAP-REPO-02 | CONFIRMED | "Phase" senses verified across 3 files |
| GAP-REPO-03 | CONFIRMED | `Glob qor/references/glossary*.md` → no results |
| GAP-REPO-04 | CONFIRMED | `docs/SHADOW_GENOME.md` exists (narrative); `qor/references/doctrine-shadow-genome-countermeasures.md` exists (structured SG-IDs); runtime events log to third location — 3-way split |

### Round 2 — hallucination scan

- **Hallucination found:** concept-mapping subagent claimed `qor/gates/schema/*.schema.json` "not present in repo scan — either missing or not found." False — 9 schema files glob-visible.
- **Hallucination found:** topology subagent claimed `qor/skills/meta/qor-deep-audit/SKILL.md` path for delegation context; actual path is `C:\Users\krkna\.claude\skills\qor-deep-audit\SKILL.md` (user scope, not repo). Impact: low — the skill exists, just in a different location than implied. Not a blocking error for remediation.
- **No hallucination:** boundary subagent's 5×5 boundary table claim — spot-checked against CLAUDE.md line 32 ("Skip files >100 KB") and substantiate.md lines 322-330 (NEVER list). Consistent.
- **No hallucination:** cross-doc subagent's claim about `<phase>` XML tag case inconsistency — confirmed in plan SKILL.md line 21 (`<phase>PLAN</phase>`, uppercase) vs YAML frontmatter line 11 (`phase: plan`, lowercase).

### Round 3 — blast radius + sprint ordering

- **Sprint 1 blast radius (doctrine + schema):** Authoring a new doctrine is zero-blast. Extending `plan.schema.json` is **additive** (new fields optional) → zero breakage for existing plans. `additionalProperties: true` already set, so unknown fields wouldn't have broken anyway. Safe.
- **Sprint 2 blast radius (plan SKILL changes):** Adding required blocks to plan structure breaks **existing plan files** (none of them declare doc_tier/concepts/terms/boundaries). Mitigation: new plans must declare; existing plans grandfathered via explicit `doc_tier: legacy` escape hatch until re-planned. Decision required.
- **Sprint 3 blast radius (substantiate changes):** `doc_integrity.py` script is new, no coupling. `/qor-substantiate` gains new verification steps. Failing substantiation is the POINT — but we need to be careful that the first repo to run upgraded substantiate (this repo, dogfood Sprint 5) doesn't fail on existing legacy plans. The Sprint 2 grandfather clause handles it.
- **Sprint 4 blast radius:** audit rubric additions are advisory (audit passes already exist, this just adds criteria). Low risk.
- **Sprint 5 blast radius:** byproduct — fixing this repo's own gaps is the dogfood test. If prompts don't produce sound output, iterate Sprint 1-4 before declaring done.
- **Sprint ordering validated:** Sprint 1 (doctrine + schema) → Sprint 2 (plan enforcement consumes doctrine) → Sprint 3 (substantiate verifies plan claims) → Sprint 4 (audit adds drift checks between plans) → Sprint 5 (dogfood). Each asserts prior contract. No parallelization possible without breaking dependency chain.
- **Hidden dependency identified:** substantiate Step 4.5 "Skill File Integrity Check" (SKILL.md lines 149-182) is a precedent pattern for doc-integrity verification. New `doc_integrity.py` should follow same invocation style (ABORT on violation, operator fixes and retries). Do NOT invent a new failure protocol.
- **Hidden dependency identified:** substantiate Step 7.5-7.6 already invokes `governance_helpers.parse_change_class` and `changelog_stamp.apply_stamp`. `doc_integrity` hooks should slot in between Step 4.6 (Reliability Sweep) and Step 5 (Razor Check), or as Step 4.7 — place matters for which failures block which other failures.
