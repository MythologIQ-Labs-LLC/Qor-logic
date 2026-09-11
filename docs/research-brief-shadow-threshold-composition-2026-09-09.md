# Research Brief

**Date**: 2026-09-09
**Analyst**: The Qor-logic Analyst
**Target**: the Process Shadow Genome threshold; the codex-plugin capability_shortfall cluster; the remediation proposal committed at 710aaf82
**Scope**: re-verify the facts grounding a planned remediation phase before that phase is written

---

## Executive Summary

The remediation proposal this phase was to implement rests on a false premise, and
this brief retracts it. The proposal states that the threshold is dominated by a
class its own remediation path cannot classify, citing the codex-plugin cluster at
40 percent of the backlog and 43 percent of severity. Those figures are correct
about the **raw** event log and wrong about the number that fires the gate.

`check_shadow_threshold._signature` already collapses recurrences across sessions
on `(event_type, gate|capability|pattern)`. Under that collapse the 29 codex events
contribute **2 of 47**, not 43 percent. The mechanism the proposal wanted to add
already exists, one module over, and has been working the whole time.

The threshold's 47 is spread across **29 distinct signatures**, the largest
contributing 3. There is no dominant class. The deferral loop is therefore not
caused by a measurement artifact; it is caused by there being 29 genuinely
unaddressed process signatures that nobody has worked.

The planned phase should not proceed as scoped.

## Findings

### 1. Cluster figures re-measured and unchanged

Live log, this session: 72 unaddressed events, raw severity 134. The codex-plugin
cluster is 29 events across 29 distinct `session_id` values, every one severity 2,
every one emitted by `qor-audit` -- 40 percent of the backlog and 43 percent of raw
severity. All figures match the prior session's. Nothing moved.

### 2. Those shares do not describe the gate

`qor/scripts/check_shadow_threshold.py:88` sums via `collapsed_severity`, not raw
addition. Measured: raw 134, collapsed 47, and `check_shadow_threshold` reports
`BREACH: severity sum 47 >= threshold 10`.

Per-signature contribution to the 47, measured:

| contribution | events | signature |
|---|---|---|
| 3 | 6 | `('degradation', 'scope-widening ...')` |
| 3 | 1 | `('repeated_veto_pattern', 'details:b71e6397ef3f')` |
| 3 | 1 | three further `repeated_veto_pattern` signatures |
| **2** | **29** | **`('capability_shortfall', 'codex-plugin')`** |
| 2 | 2 | `('gate_override', 'post_audit_plan_amendment')` |
| 2 | 1 | four `orchestration_override` signatures |
| 1 | 6 | `('gate_override', 'intent_lock')` |

29 signatures in total; maximum contribution 3. The codex cluster is one of them,
contributing 2. **It is not the driver and never was.**

### 3. The cross-session mechanism already exists

`check_shadow_threshold._signature` (`:90-115`):

> `key = details.get("gate") or details.get("capability") or details.get("pattern")`

Session is absent from that key by construction. Measured on a live codex event,
its signature is `('capability_shortfall', 'codex-plugin')` -- all 29 occurrences
share it.

Its docstring records the calibration history directly: Phase 253 keyed only on
`gate`/`capability`, so events carrying neither collapsed by `event_type` alone
and unrelated defects merged; Phase 254 added the details digest because "a rule
that hides real debt produces a number that looks better."

The proposal's second change -- add cross-session recurrence detection -- would
reimplement this. The precedent was cited in the prior analysis and its substance
was not read.

### 4. The classifier gap is real, and small

`remediate_read_context.py:27` keys groups on `(event_type, skill, session_id)`.
`remediate_pattern_match.py:38-40` fires capability-shortfall aggregation at `>= 3`
within one group. Measured against the live log: 59 groups, 10 classifications, 18
events classified, all 29 codex groups of size 1, and **zero codex events
classified**.

So the gap exists exactly as described. What does not follow is the consequence the
proposal drew from it. An unclassifiable class worth 2 of 47 does not explain four
deferrals of the threshold route.

### 5. The pending discount bought nothing

`_pending_discount_applies` (`:120-143`) requires `event["closure_enforcer"]` and
validates it. Measured on a codex event flipped last session: `addressed_pending`
is `True`, `closure_enforcer` is `None`, details carry only `capability` and
`reason`. `mark_addressed_pending` sets the pending flag and does not propagate the
proposal's enforcer onto the events, so the discount is refused.

Defensible for a stage-1 flip -- the discount is supposed to cost evidence -- but it
means last session's flip of 29 events changed no number. Whether any writer ever
populates `closure_enforcer` on an event is unresolved and outside this scope.

### 6. The disclosure has two owners

`/qor-audit` Step 1.a emits `capability_shortfall` for `codex-plugin` on every
invocation; `/qor-enterprise-environment-adapter` probes the same capability set as
part of its host profile. Both describe the same unchanging host fact. That
duplication is real and is a legitimate tidiness finding about **log volume** -- 29
identical rows -- but it is not a threshold finding.

## Blueprint Alignment

| Claim | Actual finding | Status |
|---|---|---|
| The threshold is dominated by the codex cluster (proposal, 710aaf82) | It contributes 2 of 47 across 29 signatures | **DRIFT -- retracted** |
| Cross-session recurrence detection must be added | `check_shadow_threshold._signature` already implements it | **DRIFT -- would duplicate** |
| The classifier cannot classify the codex cluster | Confirmed: 29 groups of 1, 0 classified | MATCH |
| Each of four deferrals was individually correct | Still true, but for a different reason than stated | PARTIAL |
| Marking 29 events pending reduced the signal | Discount refused; no number changed | **DRIFT** |

## Recommendations

1. **P0 -- do not implement the proposal as written.** Its second change duplicates
   an existing mechanism and its rationale misattributes the threshold.
2. **P0 -- correct the committed proposal.** `.qor/gates/2026-09-09T1940-cdb23b/remediate.json`
   is on `main` carrying the retracted premise. A wrong rationale in a governance
   artifact is worse than no artifact, because the next reader inherits it.
3. **P1 -- the real question is calibration, not classification.** A threshold of 10
   against a repository that legitimately carries 29 distinct signatures fires
   permanently. Either the signatures get worked, or the threshold is recalibrated
   to a level that means something. That is an operator decision and this brief
   does not pre-empt it.
4. **P2 -- the emission duplication stands on its own merits.** 29 identical rows
   for one unchanging host fact is worth fixing as log hygiene, sized honestly as
   such, and not as a threshold repair.

## Updated Knowledge

For `docs/SHADOW_GENOME.md`: a measurement can be correct, reproduced, and still
attached to the wrong denominator. The 40/43 percent figures were re-derived three
times across two sessions and never once checked against the number the gate
actually reads. What made the error durable is that both numbers describe the same
events -- raw sum and collapsed sum -- so every re-measurement of the cluster
confirmed the figure without ever testing the claim built on it.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
