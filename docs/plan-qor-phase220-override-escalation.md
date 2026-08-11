# Plan: override escalation (Phase 220, GH #324)

**change_class**: feature

**doc_tier**: system

**terms_introduced**: per-gate override recurrence

**boundaries**:
- limitations: This makes a repeated override visible and costly. It cannot make
  the operator capture an intent lock at the right moment; nothing in a local
  toolkit can. What it can do is stop the fourth occurrence from looking like
  the first.
- non_goals: No CI job for `intent_lock`. CI has no session and no lock, so the
  check is inherently local; adding it would be theatre. No removal of the
  override path -- disclosed override is a legitimate operator action and the
  defect is that recurrence was invisible, not that override exists.
- exclusions: #314, #320, #286 are out of scope.

## Open Questions

None.

## Locked Decisions

**LD-1 — Count per gate as well as per session.**

`git show HEAD:qor/scripts/override_friction.py | grep -n 'DEFAULT_THRESHOLD' -> 22:DEFAULT_THRESHOLD = 3`

Measured against the live log: the per-session counter reads 3 / 2 / 2 across
this session's phases while `intent_lock` stands at **4 across sessions**. Every
phase rotates its session, so a per-phase-recurring override resets the counter
each time.

The existing per-session threshold is kept -- it catches a phase in trouble. A
per-gate cross-session count is added, because that is the axis on which "one
override is judgment, four is a routine" becomes visible.

**The per-gate threshold is 3**, reusing `DEFAULT_THRESHOLD`. Same number,
different axis, and the reasoning is symmetric: one override is judgment, two is
plausibly coincidence, three is a habit forming.

Checked against what actually happened rather than chosen in the abstract -- at 3
the escalation fires on the `intent_lock` override in Phase 218, one phase before
a human noticed the pattern by reading the log. At 2 it fires in Phase 217, which
is too eager: the second occurrence of anything in a governed repository is
common and escalating there would produce the alarm fatigue Phase 217 was sealed
to remove. At 4 it fires exactly when I already knew, which is no help.

A single constant governs both axes, so an operator who tunes one does not
silently leave the other at a value they never chose.

**LD-2 — The bypass is the more important half.**

`git show HEAD:qor/scripts/gate_chain.py | grep -n 'override_friction.check' -> 167:    friction = override_friction.check(session_id)`

The friction check lives in `emit_gate_override`. `shadow_process.append_event`
has none, and all four `intent_lock` overrides used `append_event` directly --
because that is what an operator reaches for when disclosing a gate they have
already decided to pass.

Phase 219's session reached three overrides and would have fired. It did not,
because none of the three went through the checking path. Raising the
sensitivity of a control nothing calls would change nothing.

This is the same shape as `_REQUIRED_PHASES` reused as a verification scope
(#321): a control attached to one of several equivalent entry points, passing
while the property it asserts is false.

**Friction is a cost, not a wall.** `append_event` mirrors
`emit_gate_override` exactly: it raises `OverrideFrictionRequired` when the
threshold is reached, and a re-invocation carrying a written justification
records normally.

It must not simply refuse. An override that cannot be *recorded* past the
threshold leaves the operator choosing between proceeding without disclosure and
not proceeding, and the first is strictly worse than today -- it converts a
disclosed override into an undisclosed one and destroys the evidence this phase
exists to create. This plan's subject is a control that was trained around;
making disclosure expensive without providing the justified path would train the
operator out of disclosing at all.

**LD-3 — `intent_lock` does not go into CI.**

`grep -oE 'qor\.(reliability|scripts)\.[a-z_]+' .github/workflows/ci.yml` lists
six enforced gates; `intent_lock` is absent, and that absence explains the
observed asymmetry -- a missing `implement.json` forced a backfill because
`gate_chain_completeness` fails the merge, while a missing lock produced a
paragraph and the seal continued.

The remedy is not to move it. CI has no session and no lock file; the check is
local by construction. A CI job would assert a guarantee the environment cannot
provide -- the GH #314 shape.

Instead the lock's state becomes a **first-class field in the seal record**, so a
reader counts occurrences without grepping shadow events, and a run of `absent`
values is legible in the ledger itself.

**LD-4 — Backfillable and non-backfillable overrides are different, and the
vocabulary must say so.**

`plan.json` and `implement.json` record content derivable from artifacts already
bound by hash; a disclosed backfill states true facts about a phase that did run.

The intent lock observes a *window*. Captured afterward it observes nothing, and
capturing it anyway would be the `SG-UnfalsifiedRemedy-A` shape. Treating all
three identically -- as GH #324 does -- obscured that one was a different kind of
loss.

**LD-5 — Counterfactual tests, per Phase 218 LD-5 and Phase 219 LD-6.**

Each fix ships a test that fails against `HEAD`: three same-gate overrides across
three sessions must escalate at the threshold; an override recorded via
`append_event` must be seen; a seal artifact must carry the lock state.

## Phase 1: Per-gate recurrence

### Unit Tests

- `tests/test_override_recurrence.py::test_same_gate_across_sessions_escalates` -
  the counterfactual. Three `intent_lock` overrides in three distinct sessions;
  asserts the per-gate result reports recurrence at the threshold. Fails at HEAD,
  which counts only within a session.
- `::test_two_occurrences_do_not_escalate` - the threshold is 3, so a second
  occurrence is still coincidence. Pins the value against silent drift downward,
  which would reintroduce alarm fatigue.
- `::test_per_session_threshold_still_fires` - regression; the existing axis is
  not replaced.
- `::test_distinct_gates_do_not_aggregate` - four overrides of four different
  gates is not a recurrence, or every busy session escalates and the signal is
  lost again.
- `::test_recurrence_reports_the_gate_and_count` - the result names which gate,
  so the operator is told what to fix rather than that something is wrong.

### Affected Files

- `qor/scripts/override_friction.py` - `check` gains an optional `gate`; new
  `gate_recurrence(gate, log_path=None)`.
- `tests/test_override_recurrence.py` - NEW.

## Phase 2: Close the recording bypass

### Unit Tests

- `tests/test_override_recording_paths.py::test_append_event_consults_friction` -
  the counterfactual. Records a `gate_override` through `append_event` past the
  threshold and asserts `OverrideFrictionRequired` is raised. Fails at HEAD,
  where `append_event` has no friction at all.
- `::test_justified_override_past_threshold_still_records` - the wall-versus-cost
  assertion. A re-invocation carrying a justification records normally. Without
  this, the fix would make disclosure impossible exactly when it matters and
  convert disclosed overrides into undisclosed ones.
- `::test_non_override_events_are_unaffected` - a `capability_shortfall` still
  appends freely; the check applies to overrides only.
- `::test_emit_gate_override_path_still_guarded` - regression on the path that
  already worked.

### Affected Files

- `qor/scripts/shadow_process.py` - `append_event` consults the friction check
  for `gate_override` events.
- `tests/test_override_recording_paths.py` - NEW.

### Changes

The check must not import `gate_chain` (circularity); it consults
`override_friction` directly. Where `emit_gate_override` already checked, the
second consultation is idempotent -- counting is over the log, not a counter.

`append_event` reproduces the `emit_gate_override` contract rather than inventing
a second one: raise, accept a justification, record. Two entry points with two
different friction behaviours would be the defect this phase is fixing, in a new
place.

## Phase 3: Lock state in the seal record

### Unit Tests

- `tests/test_seal_intent_lock_state.py::test_schema_accepts_lock_state` -
  `substantiate.schema.json` carries `intent_lock_state` with enum
  `verified | absent | overridden`.
- `::test_schema_rejects_unknown_state` - the enum is closed; a new state forces
  a deliberate amendment rather than draining into free text.
- `::test_seal_skill_records_the_state` - the wiring coupling, per Phase 217 and
  219 precedent: a field with no producer is a slot nothing fills.

### Affected Files

- `qor/gates/schema/substantiate.schema.json` - `intent_lock_state`.
- `qor/skills/governance/qor-substantiate/SKILL.md` - Step 4.6 records it.
  **75 bytes of slack**; measure before and after. If the addition does not fit,
  a disclosure pass runs first per Phase 219 LD-3 -- the step is not compressed
  below the point where it stops being executable.
- `tests/test_seal_intent_lock_state.py` - NEW.

## Phase 4: Record the pattern

### Affected Files

- `docs/SHADOW_GENOME.md` - a control attached to one of several equivalent
  entry points. Two observations: `override_friction` guards
  `emit_gate_override` but not `append_event`; `_REQUIRED_PHASES` guarded four
  artifact names but not their iteration siblings (#321). Both passed while the
  property they asserted was false, and both were found only by exercising the
  unguarded path. `closure_enforcer` cites
  `tests/test_override_recording_paths.py::test_append_event_consults_friction`.

## Phase 5: Verification

### Unit Tests

- The three new test modules, run twice.
- The full suite.
- `skill_size_budget_lint` with before/after for `qor-substantiate`.
- `dist_compile` zero-drift.

## Definition of Done

### Deliverable: recurrence is visible and costly

- **D1**: A fourth identical override cannot look like the first.
- **D2**: `override_friction.gate_recurrence` ships; `append_event` consults the
  friction check for override events.
- **D3**: Seal entry records that the live log showed `intent_lock` at 4 and that
  the per-session counter never fired.
- **D4**: `test_same_gate_across_sessions_escalates` and
  `test_append_event_consults_friction` both fail against `HEAD`; and
  `test_justified_override_past_threshold_still_records` proves friction is a
  cost rather than a wall.

### Deliverable: the lock's absence is legible

- **D1**: A reader can count intent-lock absences from the ledger without
  grepping shadow events.
- **D2**: `intent_lock_state` is in the substantiate schema with a closed enum
  and is recorded by the seal step.
- **D3**: Seal entry states why `intent_lock` is not moved into CI -- CI has no
  session and no lock, so a job there would assert a guarantee the environment
  cannot provide.
- **D4**: `test_seal_skill_records_the_state` fails if the wiring is removed
  while the schema field remains.

### Deliverable: nothing is weakened

- **D1**: Disclosed override remains available; recurrence is surfaced, not
  forbidden.
- **D2**: Per-session friction still fires; non-override events append freely.
- **D3**: Seal entry records the before/after size of `qor-substantiate`.
- **D4**: Full suite green; no existing test edited.

## Feature Inventory Touches

| Feature | Touch | Source-of-truth | test_descriptor |
|---|---|---|---|
| Per-gate override recurrence | NEW | `qor/scripts/override_friction.py` | `test_override_recurrence.py::test_same_gate_across_sessions_escalates` asserts three same-gate overrides across sessions report recurrence |
| Override recording-path parity | NEW | `qor/scripts/shadow_process.py` | `test_override_recording_paths.py::test_append_event_consults_friction` asserts the unguarded path now consults friction |

## CI Commands

- `python -m pytest tests/test_override_recurrence.py tests/test_override_recording_paths.py tests/test_seal_intent_lock_state.py -q` — the counterfactual tests.
- `python -m pytest tests/ -q` — full suite; the definition of done for this plan.
- `python -m ruff check qor/ tests/` — the new code is lint clean.
- `qor-logic scripts skill_size_budget_lint --skills-root qor/skills` — `qor-substantiate` stays under the lock.
- `qor-logic scripts dist_compile` — variants rebuilt with zero drift.
- `qor-logic scripts sg_closure_lint` — the new Shadow Genome entry carries an enforcer citation.
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase220-override-escalation.md` — this plan asserts each path and command identically at every site.
