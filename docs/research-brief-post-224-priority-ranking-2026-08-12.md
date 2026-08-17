# Research Brief

**Date**: 2026-08-12
**Analyst**: The Qor-logic Analyst
**Target**: the six open candidates after the Phase 224 seal -- GH #336, #333, #332, #337, #320, #286
**Scope**: rank them against each other and name the next phase

---

## Executive Summary

Two candidates are the same defect class one module apart, and both are small. GH #336 wins on compounding leverage: it is the enforcer guarding every future plan's citations, it shipped one phase ago, and Phase 224 demonstrated it returning clean on a real error. GH #333 follows: three of the four enforcer citations in the entire closure corpus are wrong, and the correction surface is four events today. GH #332 is the heaviest and most recurrent but needs its own design pass. #337 is documentation-only. #320 and #286 remain below their entry conditions, unchanged.

## Findings

### #336 -- the citation enforcer does not check the mandated form

`plan_grep_lint.py:109` resolves only bare `path.ext:NN` spans; `:230` enumerates the `git show <ref>:<path>` form -- the form `/qor-plan` Step 2 mandates -- as presence-only. Phase 224's plan cited entirely in the mandated form and the lint reported `0 citation(s) truth-checked` across twelve Locked Decisions and eighteen statements.

It was demonstrated live, not theorised: LD-6 claimed line `407` against a true `405`, the lint returned exit 0, and the error was caught by re-running the grep by hand. A probe confirmed the asymmetry in both directions -- a bare `seal_artifacts.py:99999` is detected, the same wrong number inside a grep-evidence statement is not.

**Why first.** Every phase after this one authors Locked Decisions in that form. The fix is bounded -- parse the `-> <NNN>:<text>` tail and route it through the existing `resolve_line`, which already takes the ref the statement names -- and it strengthens the audit's citation guarantee for all subsequent work rather than repairing one past record. It also closes the gap that made Phase 224's mandated independent reviewer the sole verification of eighteen citations.

### #333 -- three of four enforcer citations on record are wrong

`mark_addressed` writes one `closure_enforcer` across a whole batch (`remediate_mark_addressed.py:157-163`, applied at `:184`), and `_flip_event_fields:97` guards on `not addressed`, so the mis-citation cannot be corrected through the API.

Measured, not estimated: **four** events in the entire Process Shadow Genome carry a `closure_enforcer`, and **all four** cite `qor.scripts.cycle_count_escalator`. Three of them are Phase 223 findings that mechanism does not guard. `sg_closure_lint` reports `40 entries, 0 without enforcer citation` -- presence satisfied, truth absent, in exactly the shape GH #330 closed for plan citations.

**Why second.** Seventy-five percent of the corpus is wrong, which is the strongest truth-deficit on the board, but the corpus is four events and growing slowly, so the repair cost is not escalating fast. The design decision it carries -- correcting a closed event by appending a superseding record rather than mutating an append-only log -- deserves deliberate treatment and is better taken after #336 removes a live blind spot.

### #332 -- the most recurrent gate failure, and the heaviest

Thirty-four `gate_override` events are on record; ten are intent_lock-class. Phase 224 added an eleventh condition of a different kind: the gate did not run at all. The orchestrator implemented directly rather than through `/qor-implement`, so Step 5.5 never captured a fingerprint and `verify` returned `NO LOCK` with exit 0 -- disclosed as `gate_skipped_prerequisite_absent` rather than counted as a pass.

That observation sharpens the issue. #332 frames the problem as a lock that cannot prove equivalence when the audited bytes were never committed. Phase 224 shows a second failure mode: a lock that is never captured returns success. Both stem from the same root the issue names -- the gate has no CI enforcement, so it is resolvable by the party it constrains.

`intent_lock.py:167-171` remains the in-module precedent for the fix: the HEAD dimension already verifies ancestry rather than identity.

**Why third.** Real, recurrent, and the only candidate whose fix changes a gate's contract. It wants its own plan and its own audit, not a slot behind two smaller items.

### #337 -- documentation-only

The documented staging block omits five files every seal commits. No behavioural effect; the cost is that an agent reasoning from the document alone drew a false causal conclusion during Phase 224. Worth fixing, not worth a phase of its own -- fold into whichever phase next touches that skill.

### #320 and #286 -- entry conditions still unmet

Unchanged since the 2026-08-11 and post-222 triages. #320 waits on a non-zero drift count in the *edited* class; the only non-zero count on record remains the *replaced* class. #286's upstream contracts shipped without closing and still carry roughly twenty untested behaviours. No new evidence.

## Blueprint Alignment

| Claim | Finding | Status |
|---|---|---|
| Citation evidence is truth, not presence (Phase 223) | Established for bare `file:line`; the mandated grep-evidence form is unchecked | DRIFT (#336) |
| An SG event closes only with an enforcer that guards it (Phase 166) | Enforcer required and validated, but 3 of 4 on record do not guard their event | DRIFT (#333) |
| `intent_lock` binds implementation to the audited plan | Ten overrides on record; Phase 224 shows an uncaptured lock returns success | DRIFT (#332) |
| The seal's written ceremony describes what it commits | Omits five files | DRIFT (#337) |
| Phase 224's relocation holds on merged main | `seal_artifacts --check` clean; no follow-up badge commit | MATCH |

## Recommendations

1. **Phase 225 = GH #336.** Smallest fix with compounding value; the only candidate that makes every later phase's audit stronger rather than repairing one record. `change_class: hotfix`.
2. **Phase 226 = GH #333**, including the append-a-correction design decision for already-closed events.
3. **#332 next, planned before implemented**, carrying Phase 224's uncaptured-lock observation as a second failure mode.
4. **#337 folded** into the next phase touching `qor-substantiate/SKILL.md`.
5. **#320 and #286 untouched.**

## Updated Knowledge

Phase 224 recorded `SG-PrematureArtifact-A` and `SG-VerifiedPremiseUncheckedConclusion-A`. No new pattern proposed here: the uncaptured-lock observation belongs to #332's body, not to the Shadow Genome, because it is a gap this cycle disclosed rather than a failure it committed.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
