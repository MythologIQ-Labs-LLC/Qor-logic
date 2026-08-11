# Research Brief

**Date**: 2026-08-11
**Analyst**: The Qor-logic Analyst
**Target**: GH #324 -- manually-driven phases skip their artifact-writing steps
**Scope**: Why four identical overrides produced no escalation

---

## Executive Summary

The recurrence is not one defect but **three independent mechanisms**, each
sufficient on its own to let a repeated override pass unnoticed. Every one was
verified by running it rather than reading it.

1. `override_friction` counts **per session**. The pattern is per *gate*, across
   sessions, and no counter watches that axis.
2. The friction check lives inside `gate_chain.emit_gate_override`. An override
   recorded by calling `shadow_process.append_event` directly -- which is what
   every one of the four did -- never reaches it.
3. `intent_lock`'s ABORT exists only in skill prose. It is **not** in CI, unlike
   six sibling gates, so nothing mechanical stops a seal that lacks a lock.

The three compose into the observed behaviour exactly: the gates that forced
compliance were the CI-enforced ones, and the gate that was narrated past four
times was the one with no mechanical backing.

## Findings

### 1. Per-session counting is blind to a per-gate pattern

`override_friction.DEFAULT_THRESHOLD = 3`, counted by `session_id`. Measured
against the live log:

| session | overrides | friction |
|---|---|---|
| `...1904-581fb2` (Phase 219) | 3 | would fire |
| `...1304-400282` (Phase 218) | 2 | silent |
| `2026-08-01T1437-73f42e` | 2 | silent |

Per gate, across sessions:

| gate | overrides |
|---|---|
| `intent_lock` | **4** |
| `plan_artifact_backfill` | 2 |

A phase rotates its session, so a per-phase-recurring override resets the
counter every time. Four identical overrides is the exact shape the mechanism
cannot see, and the shape most worth seeing: one override is judgment, four is a
routine.

### 2. The friction check is bypassed by the recording path actually used

`gate_chain.py:165-169` consults `override_friction.check` and raises
`OverrideFrictionRequired`. `shadow_process.append_event` does not:

```
grep -n "override_friction|friction" qor/scripts/shadow_process.py  ->  (no matches)
```

All four `intent_lock` overrides were recorded with `append_event` directly,
because that is what an operator reaches for when disclosing a gate they have
already decided to pass. The friction mechanism is attached to one recording
path and the disclosure habit uses the other.

Note the consequence: Phase 219's session reached three overrides and *would*
have fired -- and did not, because none of them went through the checking path.
The one case where the existing control should have engaged is the one where the
bypass is clearest.

### 3. `intent_lock` has no mechanical enforcement

CI enforces six gates:

```
gate_chain_completeness, ledger_base_currency, seal_entry_check,
gate_provenance, publication_boundary_lint, seal_artifacts
```

`intent_lock` is absent. Its ABORT is a line in `qor-substantiate/SKILL.md`.

This predicts the observed asymmetry precisely. A missing `implement.json`
**forced** a backfill, because `gate_chain_completeness` runs in CI and fails the
merge. A missing intent lock produced a paragraph of disclosure and the seal
continued, because nothing downstream disagreed.

The distinction is not prose-versus-code -- both are code. It is whether the
check runs somewhere the operator is not the one deciding.

### 4. The intent lock is the one artifact that cannot be honestly backfilled

`plan.json` and `implement.json` record content derivable from artifacts already
bound by hash, so a disclosed backfill states true facts about a phase that did
run.

The intent lock observes a *window*: plan and audit unchanged between
implementation start and seal. Captured afterward it observes nothing, and
capturing it anyway would be the `SG-UnfalsifiedRemedy-A` shape -- an artifact
that looks like evidence of something never watched.

All four occurrences correctly refused to back-date it and verified the
substantive claim by other means. That is the right handling of one occurrence
and an admission of a broken control by the fourth.

## Blueprint Alignment

| Claim | Finding | Status |
|---|---|---|
| Repeated overrides escalate | per-session counter, per-gate pattern | **DRIFT** |
| Friction guards gate overrides | only via `emit_gate_override` | **DRIFT** |
| `intent_lock` ABORT is enforced | skill prose only; not in CI | **DRIFT** |
| Backfilling is always dishonest | true only for the intent lock | DRIFT -- narrower |

## Recommendations

1. **Count per gate as well as per session.** A same-gate override recurring
   across sessions is the signal; the existing per-session threshold stays.
2. **Route disclosure through the checking path**, or move the friction check to
   `append_event` so the recording habit cannot bypass it. Attaching a control to
   one of two entry points is the same shape as `_REQUIRED_PHASES` reused as a
   verification scope.
3. **Do not add `intent_lock` to CI.** CI has no session and no lock; the check
   is inherently local. The honest move is to make its absence *visible in the
   seal record* -- as a first-class field rather than a prose paragraph -- so a
   reader can count occurrences without grepping shadow events.
4. **Distinguish backfillable from non-backfillable artifacts** in the override
   vocabulary. Treating all three identically obscured that one of them was a
   different kind of loss.

## Updated Knowledge

Candidate Shadow Genome framing: **a control attached to one of several
equivalent entry points**. `override_friction` guards `emit_gate_override` but
not `append_event`; `_REQUIRED_PHASES` guarded four artifact names but not their
iteration siblings (#321). Both pass while the property they assert is false, and
both were found only by exercising the unguarded path.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
