# Research Brief

**Date**: 2026-08-11
**Analyst**: The Qor-logic Analyst
**Target**: Phase A of GH #285 — recover headroom in `qor-audit` and `qor-substantiate`
**Scope**: What can move, what must not, and what the last pass learned the hard way

---

## Executive Summary

There is far more movable material than needed — 10.3 KB unpinned in `qor-audit` and 7.8 KB in `qor-substantiate`, against 520 and 360 bytes of required headroom. Availability is not the constraint.

The constraint is that **the guardrail tests are the specification**, and static analysis under-counts them. Phase 178 ran this exact pass and its implementer discovered token locks the plan had not enumerated. Any plan here that treats its own guardrail list as complete will be wrong in the same way.

## Findings

### 1. Movable surface is ample

Computed by locating every section containing no string asserted by any of the 49 guardrail test files:

| Skill | current | needed | unpinned sections | movable |
|---|---|---|---|---|
| `qor-audit` | 39,416 B | +520 | 20 of 49 | **10,331 B** |
| `qor-substantiate` | 39,576 B | +360 | 19 of 54 | **7,757 B** |

Roughly 20× the required headroom in each file.

### 2. "Unpinned" is not the same as "safe to move"

The largest unpinned sections are operative, not explanatory: `Test Functionality Audit` (2,370 B), `Security Audit` (1,192 B), `OWASP Top 10 Pass` (935 B), `Ghost UI Audit` (886 B) in the audit skill; `Test Audit`, `Step 2.5: Version Validation`, `Step 9.6: Push/Merge Options` in the seal skill.

These are what the Judge and the seal ceremony *execute*. Relocating them would mean opening a second file to learn what to check, which trades a size problem for a usability one. Progressive disclosure moves **rationale and worked detail**; the operative instruction and its ABORT/VETO semantics stay inline with a pointer.

So the true candidate set is "unpinned **and** explanatory", which is a subset of the 10.3 / 7.8 KB — still comfortably more than 520 / 360 bytes.

### 3. Phase 178 is a proven playbook, and it carries the warning

Ledger entry #432 records the same pass on the same two files:

- Ran the parametrized headroom test **red first** (40,890 / 40,935), relocated, landed 39,355 / 39,321 — recovering 581 and 615 bytes.
- Moved ~1.5 KB of rationale per skill into **already-cited** references (`adversarial-mode.md`, `phase37-subpasses.md`, `seal-gate-ladder.md`) as appended titled subsections with inline pointers.
- Where prose was already verbatim in a reference, the inline copy was compressed to a pointer rather than appended twice.
- **"The specialist discovered and honored MORE token locks than the plan enumerated"** — a literal `|| true` required inside Step 4.6.8 prose, `option_b_required` / `Option B` tokens, hash-integrity helper names. Those sentences stayed inline, recorded under a *guardrail-is-specification* rule.

That last point is the finding that matters most. The 49-file, 49-string map computed above is a **lower bound**, not an inventory. The plan must say so and must budget for discovery during implementation rather than treating a static list as complete.

### 4. Appending to existing references avoids the glossary hazard

`doc_integrity` tracks `referenced_by` per glossary term and raises on orphan concepts (`doc_integrity.py:109-114`); the glossary carries 119 `referenced_by` entries, 104 of which name skills or reference files. Creating *new* reference files risks term-drift and orphan-concept failures at seal.

Phase 178 sidestepped this by appending to references that were already cited. The same approach here means the glossary needs no edit at all — a real simplification, and the reason not to invent new reference files for this pass.

### 5. The files have regrown since Phase 178

| Skill | Phase 178 landed | now | drift |
|---|---|---|---|
| `qor-audit` | 39,355 B | 39,416 B | +61 |
| `qor-substantiate` | 39,321 B | 39,576 B | +255 |

The lock has held — it fired during Phase 207 and forced two trims — but growth continues, and Phase 214 and Phase 213 each added inline prose. Recovering only the 520/360 bytes strictly required would put both files back at the ceiling within a few phases. Phase 178's ~1.5 KB per skill is the better target: it bought roughly a year of edits.

## Blueprint Alignment

| Claim | Finding | Status |
|---|---|---|
| Headroom recovery is possible | 10.3 / 7.8 KB unpinned | MATCH |
| A static guardrail list is sufficient | Phase 178 found locks its plan missed | DRIFT — treat as lower bound |
| New reference files are the vehicle | `doc_integrity` orphan/term-drift risk; Phase 178 appended to existing ones | DRIFT — append, do not create |
| Recovering the minimum is enough | Files regrew +61 / +255 since the last pass | DRIFT — target ~1.5 KB each |

## Recommendations

1. **Follow the Phase 178 technique exactly**: append titled subsections to already-cited references, leave an inline pointer, and compress rather than duplicate where prose already exists in the reference.
2. **Write the guardrail-is-specification rule into the plan as a Locked Decision.** A token a test asserts stays inline, full stop — even when it looks like rationale. Budget for discovering more during implementation.
3. **Run the headroom test red first**, as Phase 178 did. It is the only evidence the pass actually recovered anything.
4. **Target ~1.5 KB per skill**, not the 520/360 minimum.
5. **Do not create new reference files**, avoiding the glossary/`referenced_by` surface entirely.
6. **Verify with the focused guardrail suite plus a skill-referencing sweep**, then the full suite and a dist recompile — Phase 178's verification shape, which caught drift the focused suite alone would not.

## Updated Knowledge

No `docs/SHADOW_GENOME.md` amendment required. Phase 178's *guardrail-is-specification* rule already exists in ledger entry #432 but is not stated in any doctrine file; if this pass rediscovers it a third time, it warrants promotion out of the ledger into a durable reference.

---

_Research complete. Findings are advisory — implementation decisions remain with the Governor._
