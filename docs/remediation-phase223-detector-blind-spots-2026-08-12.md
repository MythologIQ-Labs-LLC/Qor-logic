# Remediation Proposal — Phase 223 detector blind spots

**iteration**: 3 (amends iter-2 per the reviewer's F1 supplement; VETO stands at ledger #574)

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
three I wrote in this phase's audit reports, and every seal for roughly 196
phases — was produced by a detector that has not seen an audit entry in 487
ledger entries. `SG-InertControl-A`, inside the control whose job was to catch
what produced this remediation.

**This is a missed consumer, not an unnoticed convention change.** Two sibling
ledger parsers know the current label; one does not:

```
qor/reliability/seal_entry_check.py:38   r"(GATE TRIBUNAL|IMPLEMENTATION|SESSION SEAL)"
qor/scripts/meta_ledger_walker.py:91     if "AUDIT" in label or "GATE TRIBUNAL" in label or ...
qor/scripts/veto_pattern.py:50           elif entry_type == "AUDIT":
```

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

**Closure enforcer**: `qor.scripts.veto_pattern`

## Finding 2 — the recurrence was there, at threshold, twice

Iteration 1 said "no two alike, so neither detector fired." That is true of
signature *sets* and false as a diagnosis. Per category:

```
$ python -c "...Counter over audit_history.jsonl findings_categories"
ESCALATION_THRESHOLD = 3
  specification-drift: 3   <-- AT THRESHOLD
  test-failure: 3          <-- AT THRESHOLD
  infrastructure-mismatch: 2
```

Two categories reached the escalation threshold exactly. The failure did not
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

**Proposal (gate).** Count per category alongside per signature-set in
`cycle_count_escalator.check_session_total`. That would have fired at iteration 4
on `specification-drift` reaching 3, using existing plumbing and no new module.

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
`False` against that pattern. So the remedy must extend the **artifact surface**,
the **citation form** (two-line transcript, prose-separated path), and the
**extension set** — not the surface alone.

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

**Closure enforcer**: `cannot-automate: the distinction between an executed and a transcribed citation is not recoverable from artifact text alone; it requires either a re-run at authoring time or an explicit inherited-from marker, and which of those to build is the implementing phase's decision rather than this proposal's`

## Finding 5 — the remediation classifier cannot see five of its own event types

Three events were appended for this session; one classified.

Schema enum has 11 types. `remediate_pattern_match.PATTERN_RULES` references six.
Without a classifier pattern: **degradation, repeated_veto_pattern,
gate_skipped_prerequisite_absent, governance-state-loss** — and, per the review,
**plan-replay**, which `classify` also falls through: `_maybe_append_plan_replay`
derives its own pattern from `stall_walk` with `"event_ids": []` and never
references the group's events. Five, not four.

`repeated_veto_pattern` is the type `veto_pattern` emits, so even a repaired
Finding-1 detector would reach a classifier with no pattern for it.

**Three** Shadow Genome candidates stand past the thresholds their own entries
set: `SG-TranscribedEvidence-A` at four observations,
`SG-VacuousSelfValidation-A` at two, and `SG-InertControl-A` --
`docs/SHADOW_GENOME.md:1395` reads "Candidate SG family entry if it recurs,"
first observed at Phase 217. Finding 1 is that recurrence, and a cleaner instance
than the original: the remediation that exists because a control could not fire
was produced by a session in which the control that should have caught it could
not fire.

**Proposal (doctrine + gate).** Reconcile the classifier pattern set with the
schema enum — a pattern per type, or a documented reason a type is deliberately
non-actionable. Promote both SG candidates in the same pass.

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
