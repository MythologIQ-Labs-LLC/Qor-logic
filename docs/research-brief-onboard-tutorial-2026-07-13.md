# Research Brief

**Date**: 2026-07-13T12:58:00Z
**Analyst**: The Qor-logic Analyst
**Target**: GH #241 -- /qor-onboard tutorial mode (full gate chain on one small real change)
**Scope**: skill-corpus conventions for a new workflow bundle; registration surfaces; term-definition discipline

---

## Executive Summary

GH #241 is fully unimplemented: no `/qor-onboard` skill exists (only
`/qor-onboard-codebase`, which is EXTERNAL-codebase intake -- a different job).
The issue's adoption-cost framing is directionally right and numerically stale
(the glossary now has 113 terms, not 36; staleness strengthens the case). The
smallest compliant shape is a new meta workflow bundle that orchestrates the
existing six-phase chain on ONE operator-confirmed trivial change with
narration, keeping all prose in references/ (progressive disclosure) and
linking every doctrine term to its glossary entry instead of prose-defining it
(term-drift discipline).

## Findings

### No tutorial surface exists; the near-name skill does a different job
- qor/skills/meta/qor-onboard-codebase/SKILL.md:1-40 -- workflow bundle for
  absorbing an EXTERNAL codebase (phases [research, organize, audit, plan]);
  its Purpose line and When-to-use are intake, not tutorial. 6,126 bytes.
- No qor-onboard directory anywhere under qor/skills/ (glob verified).

### Bundle conventions the new skill must follow
- Frontmatter shape from the sibling bundle: `type: workflow-bundle`,
  `phases: [...]`, `checkpoints: [...]`, `budget:` with max_phases /
  abort_on_token_threshold / max_iterations_per_phase (SKILL.md:1-22).
- qor/gates/delegation-table.md workflow-bundle section: bundles do NO
  analysis themselves, only orchestration; each phase delegates to its
  single-purpose skill.
- Registration surfaces: docs/SKILL_REGISTRY.md meta section (29 skills
  total today; snapshot header line 3), README badge `Skills-29` (README.md:14),
  delegation-table bundle row. gate_skill_matrix and skill_admission discover
  the skill automatically from the corpus walk (no manual matrix edit).
- dist_compile propagates the new skill to all six variants automatically;
  the cline command-count test computes from source lists (no count edit).

### Term-definition discipline is the load-bearing risk
- The issue asks for "every doctrine term defined at first use". Prose of the
  form "<Term> is/means/refers to X" REGISTERS as a divergent glossary
  definition in doc_integrity's term-drift check (the Phase 135/178 gotcha;
  ABORTs the seal). The tutorial must therefore LINK each term to its
  glossary home at first use, never restate a definition.
- The glossary has 113 entries (grep -c "^term:" qor/references/glossary.md);
  the tutorial narration references the ones on the chain's happy path.

### Acceptance is an operator-executed flow; tests observe the testable core
- The issue's acceptance ("fresh repo + seed + /qor-onboard -> sealed Entry #2
  with every phase artifact") is an LLM-executed session, not a pytest
  subject. The testable core: admission admits the skill, the matrix resolves
  its handoffs (Broken: 0), the structural contract holds (bundle frontmatter,
  six-phase order, references/ files cited from SKILL.md), registry/badge
  surfaces are consistent, and the narration files carry no definitional
  prose for glossary terms.
- Precedent: skill-corpus phases test structure + admission + matrix, not
  LLM behavior (the wiring-test convention).

## Blueprint Alignment

| Blueprint Claim | Actual Finding | Status |
|----------------|---------------|--------|
| Issue: "extend /qor-onboard-codebase" as an option | that bundle is external-intake; a tutorial mode would complect two jobs | DRIFT (new skill is the un-braided shape) |
| Issue: "36-doctrine vocabulary" | 113 glossary terms today | DRIFT (stale; strengthens the adoption-cost case) |
| Issue: sealed "Entry #2" on a fresh repo | seed produces the genesis entry; the first governed cycle produces the next entries | MATCH (acceptance intent: first REAL sealed cycle) |

## Recommendations

1. (P1) New meta workflow bundle `qor/skills/meta/qor-onboard/SKILL.md`
   (~6-8 KB): phases [ideate, research, plan, audit, implement, substantiate],
   operator checkpoints after ideate (change selection) and after audit;
   Review Boundary honored (substantiate to local hold). All narration prose
   in references/.
2. (P1) references/: `tutorial-narration.md` (per-phase narration script;
   glossary-link-at-first-use rule stated once) and `improvement-scan.md`
   (candidate classes for the small safe change: doc typo, stale badge,
   missing docstring, orphan link; risk criteria; operator confirms).
3. (P1) Registration: SKILL_REGISTRY meta row + section count, README badge
   30, delegation-table bundle row.
4. (P2) tests/test_qor_onboard_skill.py: admission admits; matrix stays
   Broken: 0; structural contract (frontmatter type/phases order, references
   cited); no-definitional-prose guard over the three new markdown files.

## Updated Knowledge

Tutorial narration is a LINKING discipline, not a defining one: the glossary
stays the single definition home; skills reference it.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
