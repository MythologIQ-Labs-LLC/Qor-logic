# Research Brief

**Date**: 2026-08-11
**Analyst**: The Qor-logic Analyst
**Target**: seal-ladder structural defects; GH #314 residual
**Scope**: Whether the predicted "structural remedy" is the ladder extraction, and what is actually wrong

---

## Executive Summary

Entry #558 predicted the next phase touching `qor-substantiate` would need a
structural remedy rather than another trim. Investigating it produced a different
answer than expected: **the extraction is not viable as a wedge, and three
smaller structural defects are.**

The size pressure is real but its remedy is larger than one phase. Meanwhile the
ladder has a stranded gate, an unchecked declaration, and a constant copied three
times -- all independently wrong, all cheap, none of them about size.

## Findings

### 1. The extraction is blocked by two independent constraints

The Step 4.6.x ladder is 8,508 bytes across 10 steps -- 21% of the file and the
obvious extraction unit.

**36 of the 54 test-asserted strings live inside it.** Moving the ladder strands
them, and Phase 215's LD-1 is explicit that the guardrail tests are the
specification: a relocation pass that edits a failing assertion has proven
nothing.

**No composition mechanism exists.** `dist_compile` has no include support, so
extraction means building that first. That is a phase in its own right, not a
step inside this one.

**DRIFT against my own prior recommendation.** Two messages before this brief I
proposed the extraction as the wedge. The evidence does not support it.

### 2. Step 4.6.12 is stranded outside the ladder

Heading order in the file:

```
Step 4.6 ... 4.6.10, 4.6.13, 4.6.14
## Failure Scenarios
Step 4.6.12: Execution-continuity receipt gate
## Constraints
```

It sits at 92% through the file, inside `## Failure Scenarios`, immediately
before `## Constraints`. An operator executing the ladder in order goes 4.6.10 ->
4.6.13 -> 4.6.14 -> 4.7 and never reaches it.

It is a **fail-closed receipt gate**. It has not fired only because no plan since
Phase 216 has declared `execution_continuity`, so the defect is latent rather
than harmless -- the same shape as GH #314, a declared gate providing no
coverage.

Introduced by me in Phase 216. Placement is not test-pinned; the only assertion
naming 4.6.12 checks that the reference file carries its relocated rationale, so
the step can be moved without touching a test.

Also visible: 4.6.11 is absent entirely (the phantom of #314), and 4.6.13/4.6.14
precede 4.6.12 numerically.

### 3. The `module:` prerequisite sweep was proposed and never shipped

12 declarations, 12 resolve, and nothing enforces it. Phase 217's research
proposed the check, measured it, used it to disprove #314's premise, and shipped
no test.

A prerequisite naming a module that does not exist is exactly what #314 was filed
about. The check that disproved the specific claim was never made standing.

### 4. The headroom constant is defined once and copied three times

Canonical, documented, parametrized over both governance skills:

```python
HEADROOM_BYTES = 39 * 1024  # Phase 178 (GH #266): keep >= 1 KB under EXCEEDED
```

Three test files hardcode the literal `39936` instead -- all three added by me in
Phases 217, 219, and 220, each while wiring a step into the constrained file.

Tuning `HEADROOM_BYTES` would leave three copies silently disagreeing. This is
`SG-SingleEntryPointGuard-A` in its simplest form: a value bound to a name in one
place and to a literal in three others.

## Blueprint Alignment

| Claim | Finding | Status |
|---|---|---|
| Ladder extraction is the structural remedy | 36 pinned strings + no include mechanism | **DRIFT** |
| The size problem is this phase's to solve | remedy is larger than one phase | **DRIFT** |
| 4.6.12 is correctly placed | stranded in Failure Scenarios at 92% | **DRIFT** |
| The prerequisite sweep exists | proposed Phase 217, never shipped | **DRIFT** |
| The headroom bound has one definition | 1 constant + 3 hardcoded literals | **DRIFT** |

## Recommendations

1. **Relocate Step 4.6.12** into ladder order. Placement is unpinned, the fix is
   a move, and the gate becomes reachable by a reader following the sequence.
2. **Ship the prerequisite sweep** as a standing test over every `module:`
   declaration. Closes the GH #314 residual.
3. **Replace the three hardcoded `39936` literals** with the canonical
   `HEADROOM_BYTES` import, so the bound has one definition.
4. **Defer the size remedy with the finding recorded.** It needs its own research
   into whether the answer is a composition mechanism, a sub-skill split, or
   accepting that the seal ceremony is simply the largest skill and routing new
   gates elsewhere. Deciding that under time pressure is how the wrong one gets
   built.
5. **Do not renumber 4.6.11.** The gap is the scar of #314 and reads as history;
   closing it would erase the record of a phantom gate.

## Updated Knowledge

Two of the four findings are defects I introduced in the last four phases -- the
stranded step and the triplicated constant -- and both were introduced while
solving a *different* problem under size pressure. That is worth noting as a
pattern in its own right: work done against a tight constraint tends to leave
structural debt adjacent to the constraint.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
