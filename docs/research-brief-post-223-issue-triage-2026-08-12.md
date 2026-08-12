# Research Brief

**Date**: 2026-08-12
**Analyst**: The Qor-logic Analyst
**Target**: the five open GitHub issues (#332, #333, #334, #320, #286) after the Phase 223 seal
**Scope**: verify each issue's central claim against the code it names, then order the work

---

## Executive Summary

All three issues filed after the Phase 223 seal are confirmed against source. #334 is
confirmed and is **stronger than filed**: the badge-versus-ledger ordering is uniform
across every seal, not intermittent, and the same manual workaround is already on record
at Phase 215. #333 and #332 are confirmed exactly as written. #320 and #286 were triaged
earlier and neither has crossed its entry condition. One correction of record: #334's
stated precondition ("Phase 222 did not hit it, so the ordering is not uniform") is
contradicted by the code, which inverts the open question it asks.

## Findings

### Category 1: #334 -- the ordering is uniform, and the workaround has a precedent

**The ordering claim is confirmed.** `seal_artifacts --check` runs at Step 6.5
(`qor/skills/governance/qor-substantiate/SKILL.md:365`) and the SESSION SEAL entry is
appended at Step 7 (`:399`). Reading Steps 7.4 through 7.9 (`:411-524`) end to end, no
step re-runs `seal_artifacts --write` after the append and before the seal commit. Step
7.5 bumps the version, Step 7.6 stamps the CHANGELOG, Step 7.7 verifies the entry, Step
7.8 checks gate-chain completeness, Step 7.9 folds the spec. None regenerates the badge.

**Intermittency cannot come from divergent counters.** Both the write path and the check
path route through one function: `qor/scripts/seal_artifacts.py:117` sets
`counts["ledger"] = badge_currency.count_ledger_entries(...)` for the write, and `:195-197`
passes the same ledger path into the check. There is a single counter, so the badge and
the gate always agree about what "an entry" is. The drift is therefore structural: badge
is written at count N, the seal appends to N+1, and the gate reads consistent because the
entry it would have counted does not exist yet.

**This is at least the second occurrence, not the first.** Commit `851c9f4`,
`fix: regenerate README ledger badge after the seal entry landed`, sits between the Phase
215 and Phase 216 seals. Phase 223's `08f594a` is the same band-aid applied again eight
phases later.

**The CI step has been live the whole time.** `seal-artifacts currency`
(`.github/workflows/ci.yml:96`) was added at Phase 164 (`b10b247`, 2026-07-04), so
roughly fifty-eight sealed phases have run under it.

**Correction of record.** #334 states that Phase 222 did not hit the defect and concludes
"something about the ordering is not uniform across seals -- worth establishing before
fixing." The code says the ordering is uniform. The question that actually needs
answering is the inverse: given a structural drift-by-one on every seal, why did most
runs go green. The likeliest mechanism, **not verified here**, is that a later commit on
the branch happens to re-run `--write` after the entry landed, absorbing the drift before
CI evaluates the branch tip. That should be established, but it does not gate the fix:
generating an artifact after all of its inputs exist is correct regardless of which runs
were lucky.

**Fix shape.** Ordering, not logic. Add a `--write` then `--check` pair after Step 7 and
before the seal commit. Pin it with a test that seals a fixture repo and asserts the
README ledger badge equals the post-seal entry count. Nothing tests the two steps'
relative position today.

### Category 2: #333 -- confirmed, and it is the Phase 223 defect class one control over

**One enforcer per batch is confirmed.**
`qor/scripts/remediate_mark_addressed.py:157-163` declares
`mark_addressed(event_ids: list[str], session_id, review_pass_artifact_path,
remediate_gate_path, closure_enforcer: str, repo_root=None)`. The scalar
`closure_enforcer` is validated once at `:174` and written into every event in the batch
at `:184`.

**The irreversibility is confirmed.** `_flip_event_fields:97` guards with
`if event["id"] in target and not event["addressed"]`. An event that has already flipped
is skipped on every subsequent call, so a correcting re-run mutates nothing. There is no
other write path in the module.

**The ambiguous zero is confirmed.** `:106` returns `(flipped, missing_ids)`. An
already-addressed event yields `(0, [])`, which is byte-identical to the return for a
call that matched nothing. "Already done" and "did nothing" are indistinguishable to the
caller.

**Why this matters beyond the four events.** `sg_closure_lint` reported `40 / 0 uncited`
at the Phase 223 seal. That count is satisfied by a citation being present. Three of the
four events closed in that same phase cite `qor.scripts.cycle_count_escalator`, which
does not guard them; their proposals in
`.qor/gates/2026-08-12T0214-799d77/remediate-iter6.json` each name a different enforcer.
This is precisely the presence-versus-truth gap Phase 223 (GH #330) closed for plan
citations, surviving in an adjacent control. A closure log that reports zero uncited
while carrying wrong citations is not a weaker version of the control; it is the control
reporting the wrong answer.

**Fix shape.** Accept a `{event_id: enforcer}` mapping, validating each value against the
same four accepted forms, and keep the scalar signature as the case where all events
share one enforcer. The corrective path for already-closed events needs a design
decision: mutating a closed event in place contradicts the log's evidentiary role, so
appending a correction event that supersedes the citation is the governance-correct
shape. That decision belongs in the plan, not in the fix.

### Category 3: #332 -- confirmed, and the lock already has the precedent for its own fix

**The lock stores a digest and nothing else.** `qor/reliability/intent_lock.py:123`
writes `"plan_hash": _hash_file(plan)` into the fingerprint. Verification at `:153` is
`if not plan.is_file() or _hash_file(plan) != data["plan_hash"]`. Byte-identity or
nothing. When the audited bytes were never committed, the referent is unrecoverable and
the Phase 218 equivalence proof is unavailable by construction, exactly as the issue
states.

**The module already relaxed one dimension from equality to a provable relation.**
`:167-171` does not require the captured HEAD to equal the current HEAD. It requires
`git merge-base --is-ancestor captured_head HEAD` -- reachability, not identity. That is
direct in-module precedent for the issue's Directions 1 and 3: a lock dimension can be
verified as an authorized relation rather than as byte-identity, and this codebase has
already done it once for the commit dimension.

**The structural conflict is real and will recur.** An audit that carries corrections
into implementation is doing the right thing (it avoids binding a PASS to a document it
did not audit). An implementer that applies them changes the plan. The lock captured at
implement entry then fails at seal. Ninth override of this class on record, on a gate
with no CI enforcement, which is why it stays resolvable by the party it constrains.

**Fix shape.** Direction 3 (store enough to prove equivalence -- the audited content, or a
diff against a committed ref) is the smallest change that converts a recurring override
into a decidable question. Direction 1 (the verdict authorizes a structured bounded delta)
is stronger but requires changing the audit's output contract. This is the heaviest of the
three and should not be rushed into the same phase as the other two.

### Category 4: #320 and #286 -- neither has crossed its entry condition

**#320** was re-triaged today in `docs/research-brief-post-222-issue-triage-2026-08-12.md`
and its acceptance criteria amended in the issue itself. It stays closed to work until V1
produces a non-zero drift count in the *edited* class. Six seals have produced zero such
observations; the one non-zero count on record is the *replaced* class, a packaging
condition. No new evidence since this morning.

**#286** is unblocked -- the three extended-governance-line authorities it consumes
shipped as that line's phase 225 -- but none of those three issues is closed, and roughly
twenty named behaviours there remain without tests. Binding lifecycle-gate semantics to a
contract still in motion buys a rework. The earlier recommendation ("unblocked, but not
next") holds unchanged.

## Blueprint Alignment

| Blueprint claim | Actual finding | Status |
|---|---|---|
| Seal artifacts are regenerated from truth, then checked against truth (Phase 164 generate-not-assert) | Regenerated at Step 6 from pre-seal truth; checked at Step 6.5; the seal entry lands at Step 7 after both | DRIFT |
| Badge currency is enforced fail-closed for release classes at Step 6.5 | Enforced, but structurally blind to the entry the seal itself adds | DRIFT |
| An SG event closes as `remediated` only with an executable enforcer that guards it (Phase 166, GH #249) | An enforcer is required and validated, but one value is applied to a whole batch, so it need not guard the event it is attached to | DRIFT |
| `intent_lock` binds implementation to the audited plan | Binds to a digest of a file that may never have been committed; unprovable when the referent is gone | DRIFT |
| Citation evidence is truth, not presence (Phase 223, GH #330) | Established for plan `file:line` citations; `sg_closure_lint` still scores enforcer citations on presence | DRIFT |
| Governance health, gate chain, and ledger chain are intact at HEAD | `governance-health` OK on all eight artifacts; `governance-index` clean; `seal_artifacts --check` OK | MATCH |

Five DRIFT findings. All five are the same shape: a control that verifies the presence or
the digest of a thing rather than the thing.

## Recommendations

Ordered. The first has a real dependency on the other two.

1. **#334 first, and alone (P0).** It is the only one of the three whose fix is ordering
   rather than semantics, it has the highest certainty, and it is load-bearing for
   everything after it: until it lands, every seal today repeats the Phase 215/223
   band-aid. Fixing it first makes the subsequent phases' seals clean by construction.
   Suggested `change_class: fix`. Deliverables: move a `--write`/`--check` pair to after
   Step 7; add the fixture-repo ordering test; record the "why did most runs go green"
   question as an open note rather than blocking on it.

2. **#333 second (P1).** Same defect class Phase 223 just closed, in a control that is
   currently reporting `40 / 0 uncited` over at least three wrong citations. The mapping
   signature is mechanical; the correction path for already-closed events is the design
   decision the plan must settle (append-a-correction, not mutate-in-place). Also worth
   fixing in the same pass: make the `(0, [])` return distinguishable between
   "already addressed" and "no such event". Suggested `change_class: feature`.

3. **#332 third, and planned before implemented (P2).** Confirmed and doctrinally the
   heaviest. Direction 3 is the smallest decidable change, and `intent_lock.py:167-171`
   supplies the in-module precedent for relaxing a lock dimension to a provable relation.
   This deserves its own plan and its own audit rather than a slot at the end of a
   bundled phase.

4. **#320 and #286 stay open and untouched.** Neither entry condition is met. Revisit
   #320 when a drift count lands in the edited class; revisit #286 when the extended line
   pins a contract version.

**Today's execution plan.** Phase 224 = #334, planned, audited, implemented, sealed. If
the day still has room after the seal, Phase 225 = #333. #332 gets a plan only, so its
design decision is made deliberately rather than under seal pressure.

**One thing to carry into the Phase 224 plan.** Three of the five DRIFT rows above are
instances of one pattern, and Phase 223 named it for a fourth. A doctrine note that a
governance control must state what it verifies -- presence, digest, or truth -- and that
presence-only is a declared ceiling rather than an unstated default, would give the next
audit something to check the next control against. Cheap to write, and it is the
generalization the last three phases keep re-deriving.

## Updated Knowledge

Added to `docs/SHADOW_GENOME.md`: the artifact-before-its-input ordering pattern, its two
recorded occurrences (Phase 215 `851c9f4`, Phase 223 `08f594a`), and why a gate that runs
before the state it grades cannot see the drift it exists to catch.

Corrected in this brief: #334's premise that the seal ordering varies between phases. It
does not; the drift is structural on every seal, and the open question is why most CI runs
went green rather than why one went red.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
