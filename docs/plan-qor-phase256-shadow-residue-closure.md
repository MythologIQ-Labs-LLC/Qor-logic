# Plan: honest closure of the shadow-genome residue, and the emitter fix that keeps it closed

**change_class**: feature

**doc_tier**: standard

**terms**: []

No new domain vocabulary. `permanent_skips` is a config key, not a governance term.

**boundaries**:
- limitations: [does not lower the threshold, does not change `collapsed_severity`, and does not close any event whose defect is still live; the severity that remains after this pass stays open and is enumerated below]
- non_goals: [does not build an enforcer for the `merge-on-green` override; does not resolve whether a recorded `gate_override` should count as debt at all, which is a separate design question raised at the end]
- exclusions: [no change to the two-stage `mark_addressed_pending` -> `mark_addressed` flip or to `_validate_closure_enforcer`'s four accepted forms]

## Problem

The collapsed severity is 63 against a threshold of 10. Two things are wrong
with it, and only one of them is this repository's debt.

**First, five signatures are owned by the private companion line.** They describe
an orchestrator that amends a plan while a reviewer is auditing it, a mandated
reviewer that goes idle without delivering its verdict, an implementation
performed as a governed edit sequence so `intent_lock verify` had no referent and
exited 0, and two faces of the installed-corpus drift. None is repairable by any
change to this repository. `deferred_upstream` was added in Phase 253 for exactly
this, and `mark_deferred_upstream` requires a non-empty `issue_url` so that a
transfer of ownership is recorded rather than asserted.

**Second, three signatures re-emit on every cycle.** `data_api_acl_lint` skips at
every seal because this repository ships no SQL migrations. The FEATURE_INDEX
surface lint skips at every seal because this repository's index header declares
no `Surface` column -- that gate exists for a consuming repository. `codex-plugin`
records a shortfall at every audit because no external reviewer is configured on
this host. Closing those events is a treadmill: the next seal writes new ones
with the same signature.

A pass that only flipped the existing events would leave the second problem
entirely intact and would have to be re-run every phase. That is the half-measure
this repository rejects, so the emitter is fixed in the same phase.

## Fix

### 1. Declared permanent skips (the durable half)

`.qorlogic/config.json` gains a `permanent_skips` section mapping a gate or
capability name to the justification for why no enforcer will ever satisfy it
here:

```json
"permanent_skips": {
  "data_api_acl_lint": "This repository ships no SQL migrations, so the Data-API grant and definer-view scan has no subject; the scanner prints a disclosed SKIP and exits 0 by design."
}
```

`shadow_process.append_event` consults it at emit time. When the event's
discriminator -- `details.gate`, else `details.capability`, the same chain
`check_shadow_threshold._signature` uses -- names a declared permanent skip, the
event is stamped closed on emission: `addressed: true`, `addressed_reason:
"remediated"`, `addressed_pending: true`, `addressed_ts`, and `closure_enforcer:
"cannot-automate: <the declared justification>"`.

`append_event` is the choke point every emitter passes through, including the
ones the operator writes by hand from a skill step, so the fix does not have to
be repeated in `feature_index_verify`, `governance_index`,
`skill_size_budget_lint`, and the Phase 75 hand-emit path separately.

#### The restriction that keeps this from being a second, unguarded closure road (tribunal ground V-1)

Two-stage closure exists because `addressed: true` is a strong claim.
`mark_addressed` refuses to flip anything without a PASS review artifact for the
named remediate gate, and `mark_deferred_upstream` refuses without a destination.
An emit-time stamp reaches the same terminal state with neither, gated only by a
key in a tracked config file that no gate protects -- and "only the operator edits
config" is a statement about who edits a file, not a control.

So the mechanism is bounded to the event types that report an *absence*:

```python
_CLOSABLE_ON_EMISSION = frozenset({
    "gate_skipped_prerequisite_absent",
    "capability_shortfall",
})
```

A declaration has no effect on any other event type. `degradation`,
`regression`, `hallucination`, `gate_override`, and `repeated_veto_pattern`
report that something went wrong, and they keep the attested path, which is what
the attested path is for. Without this bound,
`permanent_skips: {"intent_lock": "<fifty characters of anything>"}` would
silently close every future intent-lock skip -- the exact gate whose false PASS
is one of the five events this plan defers upstream.

Three further properties make this a disclosure channel and not a mute button:

- **the event is still written.** Phase 75's disclosed-skip exists so a skipped
  gate is visible; suppressing the record would restore the silence it was built
  to remove. Only its debt accrual changes.
- **the justification is required and at least 50 characters**, matching
  `_validate_closure_enforcer`'s `cannot-automate:` form, and it is carried into
  the event verbatim so the reason travels with the record.
- **a malformed declaration raises rather than degrades.** A key whose
  justification is too short raises `PermanentSkipDeclarationError` at emit time.
  Silently ignoring a bad declaration would let a typo restore the treadmill with
  nobody learning of it.

Only the operator can declare a permanent skip, because only the operator can say
that a property of the repository is permanent. A gate cannot exempt itself.

### 2. Closure of the existing residue

| signature | sev | disposition | destination or enforcer |
|---|---|---|---|
| `degradation` / concurrent-edit-during-audit | 4 | deferred_upstream | new companion-line issue |
| `degradation` / delegated-review-delivery-failure | 3 | deferred_upstream | new companion-line issue |
| `gate_skipped_prerequisite_absent` / intent_lock | 3 | deferred_upstream | new companion-line issue |
| `capability_shortfall` / qor-namespace-resolution | 3 | deferred_upstream | existing namespace-collision issue |
| `gate_skipped_prerequisite_absent` / instruction_hygiene_lint | 1 | deferred_upstream | existing namespace-collision issue |
| `hallucination` / invented-artifact-path | 4 | remediated | `qor.scripts.plan_grep_lint:check_plan` |
| `regression` / gate-artifact hand-edit | 3 | remediated | `tests/test_gate_provenance.py` |
| `gate_skipped_prerequisite_absent` / data_api_acl_lint | 1 | cannot-automate | declared permanent skip |
| `gate_skipped_prerequisite_absent` / feature_index_surface_lint | 1 | cannot-automate | declared permanent skip |
| `capability_shortfall` / agent-teams | 2 | cannot-automate | declared permanent skip |

The three new companion-line issues are filed during implement, before any event
is flipped, so no event is closed against a destination that does not yet exist.

Three closures need their evidence stated rather than asserted:

- **the hallucination event** is the one Phase 255 built the missing enforcer for.
  `_REFERENCE_PATH_RE` now drives a loop emitting `reference-path-missing`, and a
  live-corpus test pins the two genuine broken citations it finds across 277
  plans. Phase 255 deliberately left this flip to a separate pass; this is it.
- **the regression event** (sealed gate artifacts hand-edited without re-signing
  their sidecars) has both halves discharged. The damage is gone: 0
  payload-digest failures across 787 committed sidecars. The recurrence is
  caught: `.github/workflows/ci.yml:147` runs `gate_provenance verify-committed
  --phase-min 158` keylessly on every PR, and `tests/test_gate_provenance.py`
  proves that step fails on artifact tamper and on a missing sidecar rather than
  merely passing when nothing is wrong.
- **the agent-teams shortfall** is a declared permanent skip rather than a
  repair (tribunal ground V-3). `qor_platform.FALLBACKS` maps it to host-native
  subagent dispatch and `availability()` reports `satisfied-by-fallback`, so the
  absent capability costs no function -- but neither
  `qor_audit_runtime.emit_capability_shortfall` nor `/qor-implement` Step 1.a
  consults `availability()`, so the emitter is still live. Closing it as
  `remediated` would repair nothing durable and would schedule a failure into
  this plan's own anti-recurrence test at the next firing. As a declared
  permanent skip the closure survives the emitter.

### 3. Recording the upstream destination without publishing it

The operator's instruction is that deferring upstream must mean a real issue
exists. The publication boundary is that a tracked artifact in this public
repository must not identify an outside repository, and it is mechanically
enforced: `publication_boundary_lint._GH_URL_RE` matches any
`github.com/<owner>/<repo>` other than this one, both genome files are tracked,
and CI runs the structural detectors. A live companion-line URL written into
`docs/PROCESS_SHADOW_GENOME.md` would republish exactly the class of reference
the GH #260 sweep removed.

Both hold at once, because the substance of the instruction is that the work is
really tracked, not that a particular string shape appears:

- the three new issues are **really filed**, and the two existing ones already
  exist;
- the `issue_url` recorded in the tracked genome is the **anonymized stable
  reference** the boundary doctrine's "delete or anonymize" remedy prescribes;
- the true URL mapping is written to `.qor/private/upstream-issues.json`, which
  is inside the already-gitignored private area, so the operator can resolve any
  reference to its issue and nothing resolvable is published.

This costs a public reader nothing they had: a private-line URL 404s for them
whatever its shape, so the anonymized form loses no verification that ever
existed while the boundary keeps what it protects.

### 4. What deliberately stays open

Nothing in this group is closed here:

- `capability_shortfall` / codex-plugin (severity 2). Removed from the closure at
  tribunal ground V-2: `external_reviewer.command` is a key this repository ships
  and reads (`qor/scripts/external_reviewer.py`, Phase 123), so the capability is
  unconfigured, not unobtainable. `cannot-automate:` asserts that nothing will
  ever repair it, which the config contradicts. The event keeps saying what is
  true -- 29 solo audits over two months, no adversarial engine -- and the Option
  B mandate is a compensating control, not a substitute for one.
- `gate_override` / merge-on-green (severity 3). A PR was admin-merged with a
  check still pending and landed a red main. The remedy is real and no mechanical
  enforcer exists for it. Building one is outside this phase; closing it without
  one would be the closing-on-prose failure.
- `repeated_veto_pattern` (three signatures). The detector fired correctly.
  Phase 254 gave the emitter a `pattern` classifier so future firings collapse,
  but these three predate it.
- the `gate_override` disclosures. Each is a recorded, justified operator
  decision on a phase that has since sealed.

That last group raises a question this phase does not answer. A `gate_override`
carrying `override_authority: user` and a written justification is a *completed*
oversight action, logged because EU AI Act Art. 14 and AI-RMF MANAGE-1.1 require
it -- not outstanding work. Counting it as unaddressed debt means the more
diligently the operator discloses, the worse the health number reads, which is a
pressure in the wrong direction. Changing what the threshold counts is a
governance design change that deserves its own adversarial pass, not a rider on a
closure pass.

## Measured effect

Current collapsed severity is **63** across 33 unaddressed signatures, measured
with `check_shadow_threshold.collapsed_severity` over `read_all_events()` -- 134
events, local plus upstream genome, the same population the CLI uses.

The dispositions above account for **25**: 14 deferred upstream, 7 remediated
(the hallucination and the gate-artifact regression), 4 declared permanent. The
projected result was **38**. Both figures moved against this phase after the
tribunal: V-2 returned 2 severity to the open column, and V-3 moved 2 more from a
repair claim to a declared permanence.

The implement pass **measured 38**, across 23 signatures and 60 unaddressed
events -- still far above the threshold of 10. The projection was labelled as one
until it was measured because three severity figures earlier in this arc were
asserted from reasoning rather than measured, and all three were optimistic.

What remains is now legible rather than mixed: one unconfigured host capability,
one override with a real remedy and no enforcer, three correct detector firings,
and eighteen recorded operator disclosures.

## Tests (written first)

- `tests/test_permanent_skips.py::test_declared_skip_is_closed_on_emission`
  -- `append_event` with a `gate_skipped_prerequisite_absent` naming a declared
  gate produces an event that reads back `addressed: true` with the declared
  justification inside its `closure_enforcer`. Red before the fix: it reads back
  unaddressed.
- `::test_undeclared_skip_still_accrues`
  -- the same call for a gate absent from the config reads back
  `addressed: false`. Without this the change is a blanket amnesty.
- `::test_capability_discriminator_is_honored`
  -- a `capability_shortfall` whose `details` carries `capability` and no `gate`
  is matched, since `codex-plugin` and `agent-teams` arrive in that shape.
- `::test_short_justification_raises`
  -- a declaration under 50 characters raises `PermanentSkipDeclarationError`
  rather than being ignored.
- `::test_declared_key_cannot_close_a_defect_event`
  -- a `degradation` event whose `details.gate` names a declared permanent skip
  still reads back `addressed: false`. This is the test that makes the V-1
  restriction a control rather than prose; without it the bound is a sentence in
  a plan.
- `::test_declared_skip_still_reaches_the_log`
  -- the event is present in the log after emission. This is the test that fails
  if the fix ever becomes suppression.
- `tests/test_shadow_residue_disposition.py::test_every_deferred_upstream_event_names_a_destination`
  -- over the live genome, every `deferred_upstream` event carries a non-empty
  `issue_url`. Enforces the operator's instruction mechanically.
- `::test_deferred_upstream_destinations_are_publication_safe`
  -- no `deferred_upstream` `issue_url` contains a `github.com/<owner>/<repo>`
  naming a repository other than this one, checked with the lint's own
  `_GH_URL_RE` so the two controls cannot drift apart.
- `::test_every_deferred_reference_resolves_in_the_private_mapping`
  -- every anonymized reference recorded in the genome has an entry in
  `.qor/private/upstream-issues.json`, so an anonymized destination cannot become
  an unresolvable one. Skipped when the private file is absent, which is the
  CI-environment-honest branch: that path is gitignored and does not exist there.
- `::test_closed_residue_signatures_do_not_reappear_unaddressed`
  -- for the seven non-permanent signatures closed here, no unaddressed event
  with that signature remains. The three permanent-skip signatures are excluded
  by name because their emitters keep firing by design, which is precisely the
  distinction this phase exists to draw.

Every test invokes the unit -- `append_event`, or `_signature` over live events
-- and asserts on returned state, not on file contents.

## Validation

- `python -m pytest tests/test_permanent_skips.py tests/test_shadow_residue_disposition.py -q` -- run twice for determinism
- `python -m pytest -q` (full suite)
- `python -m ruff check qor/ tests/`
- `qor-logic-plus scripts check_shadow_threshold` -- record the measured post-closure figure and correct the Measured effect section against it
- `python -m qor.scripts.publication_boundary_lint` -- must stay at 0 findings
- `python -m qor.scripts.check_variant_drift`

## CI Commands

- `python -m pytest -q`
- `python -m ruff check qor/ tests/`
- `python -m qor.scripts.check_variant_drift`
