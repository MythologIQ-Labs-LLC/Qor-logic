# Remediation Proposal — Phase 223 detector blind spots

**iteration**: 5 (amends iter-4 per ledger #576 VETO)

**Date**: 2026-08-12
**Governor**: The Qor-logic Governor
**Trigger**: Operator invocation after four VETOs on one plan (ledger #570, #571, #572, #573)
**Scope**: Process only. No code-level defect is proposed here; that is `/qor-debug`'s domain.

---

## What happened

Four audit iterations on `docs/plan-qor-phase223-grep-evidence-truth.md`, mandating
counts 3, 3, 1, 2. Findings closed steadily and the substance converged. No process
control surfaced any of it.

Iteration 1 of this proposal diagnosed that as "every detector is keyed on
sameness." That was wrong in two directions, and the corrections are the substance
of this iteration: one detector has been structurally inert for ~196 phases, and
the recurrence the proposal said did not happen **did** happen, at threshold,
twice.

---

## Finding 1 — `veto_pattern` has not seen an audit entry since Entry #86

`veto_pattern` is not signature-keyed. Iteration 1 said it was; the word
"signature" does not appear in the module. It parses `docs/META_LEDGER.md`, counts
AUDIT entries per phase, filters to phases that also carry a SEAL entry, and fires
when the last two **sealed** phases each took more than one audit pass.

It counts an entry only when the parsed entry type is exactly `AUDIT`:

```
$ grep -cE "^### Entry #[0-9]+: AUDIT" docs/META_LEDGER.md
10
$ grep -cE "^### Entry #[0-9]+: GATE TRIBUNAL" docs/META_LEDGER.md
184
$ grep -oE "^### Entry #[0-9]+: AUDIT" docs/META_LEDGER.md | tail -1
### Entry #86: AUDIT
```

The ledger convention changed to "GATE TRIBUNAL" at Entry #86. **184 of 194 audit
entries are invisible to it.** Its view of the ledger stops at phase 27; current
work is phase 223.

```
$ python -c "...parse_phase_audit_counts(ledger)"
22 -> 1   24 -> 3   25 -> 3   26 -> 1   27 -> 2
```

Every `No repeated-VETO pattern detected in the last 2 sealed phases` line — the
three I wrote in this phase's audit reports, and every **audit report** for
roughly 196 phases (`render_advisory_text` fills the audit-time Process Pattern
Advisory slot, not a seal-time one) — was produced by a detector that has not seen an audit entry since #86. `SG-InertControl-A`, inside the control whose job was to catch
what produced this remediation.

**This is a missed consumer, not an unnoticed convention change.** Two sibling
ledger parsers know the current label; one does not:

Grep-evidence, executed 2026-08-12 at `2d356ec`. Paired on Finding 4's grounds --
an evidence statement asserts execution by the artifact carrying it, and these
three were unmarked through iteration 4:

```
git show 2d356ec:qor/reliability/seal_entry_check.py | grep -nE 'GATE TRIBUNAL' -> 38:    r"(GATE TRIBUNAL|IMPLEMENTATION|SESSION SEAL)"
git show 2d356ec:qor/scripts/meta_ledger_walker.py | grep -nE 'GATE TRIBUNAL' -> 91:    if "AUDIT" in label or "GATE TRIBUNAL" in label or "SESSION SEAL" in label or "SEAL" in label:
git show 2d356ec:qor/scripts/veto_pattern.py | grep -nE 'entry_type == .AUDIT.' -> 50:        elif entry_type == "AUDIT":
```

The pairing satisfies the contract Finding 3 proposes and remains **unenforced**
by it: `_ld_blocks` requires a Locked Decisions or Citation Inventory heading,
this document has neither, and no remediation proposal will. So this block is a
worked example of the design fork rather than an instance of the gap -- the
obligation is met for a reader while the enforcement question stays open.

**And the write side and read side are the same skill.**
`qor/skills/governance/qor-audit/SKILL.md:557` instructs: "add GATE TRIBUNAL entry
with verdict, content hash, chain hash." That skill then invokes the detector
requiring `AUDIT`. `/qor-audit` has been writing entries in a format its own
advisory cannot read.

**The suite could not have caught it.** All 11 tests in
`tests/test_veto_pattern_detector.py` use inline strings or synthetic fixtures;
`grep -c META_LEDGER` returns 0. And the test whose stated job is to enumerate
which entry types count -- `test_parse_ignores_non_audit_entries_in_counts`,
covering AUDIT, REFACTOR, IMPLEMENT, SESSION SEAL -- omits the only type actually
in use. It predates the convention change and nothing re-derived it. A control
whose correctness is asserted only against material it authored itself: the same
shape this phase has produced four times.

**A second gap survives the parser fix.** `test_parse_skips_unsealed_phase` locks
the sealed-only filter deliberately. Even with the parser corrected, Phase 223 is
unsealed and contributes nothing; the detector would have read phases 221 and 222
and still printed "No repeated-VETO pattern detected" throughout. It could only
fire after sealing, when escalation is moot.

**Proposal (gate), sequenced.** (1) Fix the parser to recognize the current
convention. (2) Add the in-flight condition -- a live VETO count is exactly what
the sealed-window design cannot supply. (3) Add a test binding the detector to the
real ledger, asserting `parse_phase_audit_counts` is non-empty above phase 200. A
synthetic-fixture suite cannot catch a format divergence by construction, which is
the whole lesson. The parser fix alone restores accurate reporting on history that
no longer needs escalating.

**Closure enforcers**: `qor.scripts.veto_pattern` and
`tests/test_veto_pattern_detector.py`

Two, because step (3) — the test binding the detector to the real ledger — is the
part of this remedy that prevents recurrence, and the entire mechanism of the
failure was a synthetic suite passing green over a dead parser for 196 phases. A
single module enforcer would leave the anti-recurrence step unguarded.

## Finding 2 — the recurrence was there, at threshold, twice

Iteration 1 said "no two alike, so neither detector fired." That is true of
signature *sets* and false as a diagnosis. Per category:

Counted over **the four plan audits, ledger #570 through #573** — a fixed set of
named entries, not a live file:

```
#570  infrastructure-mismatch, specification-drift, test-failure
#571  specification-drift, test-failure
#572  test-failure
#573  infrastructure-mismatch, specification-drift

specification-drift 3   test-failure 3   infrastructure-mismatch 2
ESCALATION_THRESHOLD = 3
```

Two categories reached the threshold exactly.

**Why the source is named this way.** Iterations 2 and 3 cited a `Counter` over
`.qor/gates/<sid>/audit_history.jsonl`. That file is append-only and `/qor-audit`
writes to it, so each review of this document invalidated the figure the document
carried: iteration 2 printed 3/3/2 over 4 records (correct when executed, ledger
#575 V1), the review pass appended a fifth and made it 4/3/3, and drafting this
correction to say 4/3/3 was itself invalidated by the iteration-3 verdict
appending a sixth, which reads 5/3/4.

Three successive figures, each true when run, each falsified by the act of
reviewing the document asserting it. Re-execution discipline does not fix this;
the source does. **The verdict-category lines of these four named entries are stable, and the
range is written explicitly so any drift is detectable by re-reading them.** The
stronger claim iteration 4 made — that no future audit alters them — is false by
this phase's own conduct: entry #572 was amended mid-phase (META_LEDGER.md:17404).
That amendment touched narrative prose, not the `**Verdict**:` line the count
reads, so the fix survives; but the accurate statement is detectability, not
immunity. This moves the evidence from a source the *checking* process mutates to
one the *authoring* process can amend, which is a large improvement and not a
wash.

That is the concrete form of Finding 4's obligation, and the clearest instance
this phase produced of evidence over a source the checking process mutates.

On the categories themselves: the failure did not
mutate — two thirds of it repeated. What dissolved the repetition is
`findings_signature.compute_record`, which hashes the sorted category *set* into
one opaque token, so three occurrences of `specification-drift` land in three
different buckets.

`cycle_count_escalator` is correctly signature-keyed and its silence follows
directly from that hashing. It is also where the cheap fix lives: it is already
session-scoped, already holds the threshold, and already walks the same records.

**Priority.** With `veto_pattern` inert, this is the only signal in the entire
detector layer that was both live and at threshold during Phase 223.
`check_session_total` was reading real session data with two categories sitting
exactly on `ESCALATION_THRESHOLD = 3`, dissolved only by set-hashing. It is the
single place a working escalation could have come from.

**Proposal (gate), two clauses.** (1) Count per category alongside per
signature-set in `check_session_total` — that would have fired at iteration 4 on
`specification-drift` reaching 3, using existing plumbing and no new module.
(2) **Emit a `repeated_veto_pattern` event on fire.** `cycle_count_escalator`
references neither `shadow_process` nor `append_event`, so a fire is a return
value and nothing more. Clause (2) serves three findings at once: it makes this
detector's fire durable, it gives Finding 1's repaired detector the same
guarantee, and it supplies Finding 5's classifier the event type it has no
pattern for.

Iteration 4 asserted this absence "belongs to Finding 5's family and is proposed
with it." **It was not.** F5's proposal reconciles a classifier pattern set — it
reads events that exist and does nothing about a detector that never writes one.
A sentence asserted coverage the proposal set did not contain, and the event
recording the fire would have closed on it (#576 V1). That is the shape correctly
diagnosed for F4's `cannot-automate` one iteration earlier, landing this time in
the Process Shadow Genome itself.

**Current state, and the detector has since fired on its own.**
`findings_signature.compute_record` sorts the category set, so the iteration-4
plan verdict and the iteration-1 remediation verdict — `{infrastructure-mismatch,
specification-drift}` in either order — hash identically to `ebde687b6b884205`.
The iteration-3 remediation verdict carried the same pair, taking
`stall_walk.run` to a streak of **3** against `ESCALATION_THRESHOLD = 3`:

```
$ python -c "...stall_walk.run(sid); cce.check(sid); cce.check_session_total(sid)"
streak: (3, 'ebde687b6b884205', ...)
check():               EscalationRecommendation(suggested_skill='/qor-remediate', escalation_reason='cycle-count', cycle_count=3)
check_session_total(): EscalationRecommendation(suggested_skill='/qor-remediate', escalation_reason='session-total', cycle_count=3)
```

So the premise "no two alike" holds for the four plan audits and is false across
the session as it now stands. Three consequences worth recording:

1. **This is the only signal any detector in this layer produced during the whole
   phase**, and it confirms this finding empirically rather than by argument. The
   categories were not selected to produce it — choosing a different set to stay
   under threshold would have been gaming a detector inside a remediation about
   detectors that do not fire.
2. **The fire leaves no trace of its own.** `cycle_count_escalator` references
   neither `shadow_process` nor `append_event`; it returns a recommendation and
   emits nothing. The one detector fire of the phase would have been a return
   value discarded at end of call. The event was appended by hand. That absence
   is closed by this finding's own clause (2), not by Finding 5.
3. **It recommends a skill already in progress.** `suggested_skill` is
   `/qor-remediate` while remediation is the current phase. The escalator has no
   representation for that state.

**Closure enforcer**: `qor.scripts.cycle_count_escalator`

## Finding 3 — audit reports are exempt from the citation discipline they enforce

The iteration-4 VETO turned on a `file:line` citation whose cited line did not
hold its quoted content:

```
$ sed -n '170p' .agent/staging/phase223-iter1-AUDIT_REPORT.md
| Filter-Stage Ordering | PASS | pairing lookup has no ordering dependency |

$ grep -c "Secret-scanning gate" .agent/staging/phase223-iter1-AUDIT_REPORT.md
0
```

`plan_grep_lint` enforces citation-evidence pairing on **plans**. Audit reports
carry citations of the same kind, feed the same readers, and are checked by
nothing. The artifact that adjudicates citation truth is the one artifact whose
citations no control examines.

**Propagation, corrected.** Iteration 1 said the citation propagated through four
artifacts "re-quoted at each step." Three: the audit report, ledger #572, and plan
iteration 4. Plan iteration 3 said *"Both halves were verified by shell at the
iteration-2 audit"* — a misattribution with no line number and no file, which is a
different defect. The `line 170` citation first appears in iteration 4.

Iteration 1 of this proposal took the four-artifact count verbatim from ledger
#573 without re-checking it — **inside the finding about re-quoting claims without
re-checking them.** That is a fourth observation of `SG-TranscribedEvidence-A`,
and iteration 1 counted three.

**Proposal (doctrine + gate), widened per the review.** Surface-widening alone is
insufficient. The citation that motivated this finding would evade a `--report`
check in all three of its forms:

| form | why it evades |
|---|---|
| audit report, two-line shell transcript | neither `_EVIDENCE_RE` nor `_EVIDENCE_STMT_RE` parses a `$ cmd` / `output` pair |
| plan iteration 4, prose | "recorded at line 170 of \`path\`" separates path from line; `_FILE_LINE_RE` cannot match |
| either artifact, `.md` path | `_FILE_LINE_RE` is `\b[\w./-]+\.(?:py\|ts\|tsx\|sql\|rs\|go\|js):\d+\b` — `.md` is not in the set |

Verified: `report.md:170` and `.agent/staging/...AUDIT_REPORT.md:170` both return
`False` against that pattern. So the remedy must extend three axes, not one:

| axis | what it must cover |
|---|---|
| artifact class | plans, audit reports, **and remediation proposals** |
| citation form | two-line shell transcript, prose-separated path |
| extension set | `.md` alongside the code extensions |

The artifact-class axis was self-caught during pre-verification of iteration 3:
this document carries three matchable `file:line` citations with zero evidence
statements, and F3 as then drafted widened to plans and audit reports only. The
document arguing that audit reports escape the contract escaped it itself, one
class over.

**A second gap survives the artifact-class fix.** `_ld_blocks` scans for
`^#+\s.*(locked decision|citation inventory)`; this document has no such heading
and no future remediation proposal will, because the form has no Locked
Decisions. So `check_citation_evidence` would no-op on a widened surface exactly
as it does now. Either the region-scoping assumption changes for artifact classes
with no LD convention, or remediation proposals gain a Citation Inventory
section. That is a design fork and it belongs here rather than in the implementing
phase's lap.

**And one form no static widening reaches.** A compound invocation whose output is
attributed to the wrong member — real command, real line number, real quoted
text, false file — is well-formed by every check above. Only re-execution catches
it, which is why F4's mechanism is automatable and why F3 and F4 share an
enforcer.

**Closure enforcer**: `qor.scripts.plan_grep_lint`

## Finding 4 — nothing distinguishes a citation that was executed from one that was read

Finding 3 names the mechanism precisely and iteration 1 attached no proposal to
it. A citation copied from artifact A into artifact B carries no marker separating
"I ran this" from "I read this somewhere." Every control here checks whether a
citation is well-formed and paired; none checks whether the artifact asserting it
executed it.

This is live, not theoretical: iteration 1 of this proposal inherited an
unverified count from ledger #573 while describing that exact failure.

**Proposal (doctrine).** State the contract — an evidence statement asserts
execution by the artifact carrying it, and an inherited citation must be re-run or
marked as inherited. The mechanism is a design question for the implementing
phase; naming the obligation is this proposal's job.

**Closure enforcer**: `qor.scripts.plan_grep_lint`

Iteration 3 used `cannot-automate` here. That was a deferral wearing an
impossibility's clothes (#575 V2): the justification named two mechanisms, both
automatable — a re-run at authoring time, which is exactly what Phase 223's
`reproduces()` does, and an inherited-from marker, which is a presence lint. The
tell was the clause "which of those to build is the implementing phase's
decision," which is *not-yet-decided*, not cannot-automate. An event closed under
that form flips to `addressed` with no executable guard, which is
`SG-InertControl-A` one layer up, inside the proposal that promotes
`SG-InertControl-A`. F3 and F4 are the same mechanism family and share an
enforcer.

## Finding 5 — the remediation classifier cannot see five of its own event types

Four events were appended for this session; one classified.

Schema enum has 11 types. `remediate_pattern_match.PATTERN_RULES` references six.
Without a classifier pattern: **degradation, repeated_veto_pattern,
gate_skipped_prerequisite_absent, governance-state-loss** — and, per the review,
**plan-replay**, which `classify` also falls through: `_maybe_append_plan_replay`
derives its own pattern from `stall_walk` with `"event_ids": []` and never
references the group's events. Five, not four.

`repeated_veto_pattern` is the type `veto_pattern` emits, so even a repaired
Finding-1 detector would reach a classifier with no pattern for it.

**Three** Shadow Genome candidates stand past the thresholds their own entries
set: `SG-TranscribedEvidence-A` at **five** observations — the
`audit_history.jsonl` figure resolves as both, sequentially: iteration 2 of this
proposal executed the Counter over the four records then extant and printed a
true `3/3/2` (record 5 carries `ts 03:56:15Z`, later than that authoring), which
is time-of-check/time-of-use; iteration 3 then carried the figure forward without
re-running it, by which time five records existed, and that is transcription. The
origin was honest and the propagation was not, so it counts —
`SG-VacuousSelfValidation-A` at **three**, this document's own artifact-class escape being the third, and `SG-InertControl-A` --
`docs/SHADOW_GENOME.md:1395` reads "Candidate SG family entry if it recurs,"
first observed at Phase 217. Finding 1 is that recurrence, and a cleaner instance
than the original: the remediation that exists because a control could not fire
was produced by a session in which the control that should have caught it could
not fire.

**Proposal (doctrine + gate).** Reconcile the classifier pattern set with the
schema enum — a pattern per type, or a documented reason a type is deliberately
non-actionable. Promote all three SG candidates in the same pass.

**Closure enforcer**: `qor.scripts.remediate_pattern_match`

## Finding 6 — the Option B reviewer's capability was never established

`audit_risk_score` mandated Option B on all four iterations. The dispatched
reviewer had no shell. I pinned a freeze attestation as a content hash it could
not compute; it substituted a structural check and said so. Ancestor-revision
claims went to me for verification in three consecutive rounds.

**Corrected per the review.** Iteration 1 said "every mandating finding required
Judge re-verification before adoption." That is an overstatement. Most needed no
shell: the wrong-test-file finding was one grep returning zero, the
zero-citations-in-the-LD-region finding was one grep, the untested-dedup finding
was reading a test list, and the fixture contradiction was internal to the
document. I chose to re-verify everything, which was sound, but the shell gap did
not make re-derivation necessary for most findings.

**And the omission matters more.** The highest-severity finding of the phase — the
false `line 170` citation, the founding-defect recurrence — was found **without a
shell**, with Read and Grep. The dispatch error is real; its cost is smaller than
iteration 1 claimed.

**Proposal (skill).** `/qor-audit` Step 1.a requires a dispatched Option B reviewer
to declare its available toolset in its first response, and forbids the Judge from
pinning a verification outside that set.

**Closure enforcer**: `/qor-audit Step 1`

---

## What is not proposed

**Not abandoning the Phase 223 plan.** Its substance converged; two small findings
remain. This is about the process that took four rounds to surface a defect
authored in round two.

**Not relaxing any gate.** Every VETO in this phase was correct.

**Not a code change.** All six proposals are skill, gate, or doctrine changes.

---

## Honest note on who is proposing this

I authored the false citation in Finding 3, read the detector silence as
convergence across three audit reports, made the dispatch error in Finding 6, and
then — in iteration 1 of this very proposal — mischaracterized `veto_pattern`,
missed that two categories hit the escalation threshold, and re-quoted an
unverified propagation count from a prior artifact inside the finding about
re-quoting unverified claims.

The review pass also found that iteration 1 over-owned: its self-blame was more
precise than its tooling analysis, which had the same practical effect as
self-serving framing would have, because the tooling half is the part that ships.

The operator halted plan iteration and invoked remediation. The independent
reviewer then VETOed the remediation. Both interventions came from outside my
own assessment, and both were correct.

---

_Remediation is advisory until reviewed. These events remain `addressed_pending`;
the flip to `addressed` requires a PASS review pass._
