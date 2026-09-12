# Research Brief

**Date**: 2026-09-11
**Analyst**: The Qor-logic Analyst
**Target**: an advisory-first boundary control on the outbound filing path -- what "advisory" means mechanically here, what the identity anchor must be, and what such a control would actually report
**Scope**: the `create_shadow_issue` filing path; the advisory precedent in this repository; the root-divergence defect that vetoed the blocking design; the measured finding rate

---

## Executive Summary

The justification that carried three plan iterations belongs to a different
channel than the one the plan guards. The seven-of-seven leak rate is the failure
rate of **hand-filed** reports. The guarded path -- `create_shadow_issue` -- has
run in production once, filed GH #439, and was clean.

An advisory control on that path reports **zero findings** against the live
corpus today, with all seventeen of the operator's overlay terms active. So
shipping it advisory costs nothing, blocks nothing, and is the only way to
measure a rate that has never been measured on the path in question.

The root divergence that produced the third VETO has a structural fix rather than
a patched one: the identity anchor must be the directory the events were read
from, because `shadow_log()` already derives from `root()`. Anchoring identity
anywhere else -- git toplevel, working directory -- permits terms from one
repository to guard a body composed from another's events.

One live defect surfaced: `merge_velocity_check --override` raises `ValueError`
and cannot run. It was cited by a vetoed plan as the precedent for a logged
escape.

## Findings

### 1. The guarded path has run, and it filed clean

`create_shadow_issue.py:366` composes its title as
`f"[qor-shadow] Process threshold breach — {n} events, sev {s}"`. GH #439 in this
tracker is titled `[qor-shadow] Process threshold breach — 10 events, sev 15`, a
byte-for-byte match, created 2026-09-04.

So the path is live, not hypothetical. Its recorded leak rate is **0 of 1**, and
that one filing was self-destined -- this repository into its own tracker, where
naming itself is permitted (`doctrine-publication-boundary.md:31`).

### 2. The seven-of-seven rate is about a different channel

The prior brief established that `~/.qor/repos.json` is absent on this host, so
the fleet collector has never run, and the seven upstream reports were filed by
hand. Thirty-five events carry `issue_url` values of the form `companion-line#N`
-- an anonymized placeholder, not a URL this tracker issued.

That figure has justified every iteration of the filing-guard plan. It measures
the hand-filing channel, which a reporting skill would serve and which
`create_shadow_issue` is not. Attaching it to the guarded path is the same
proxy-subject error this session has recorded repeatedly: a correct measurement
about the wrong subject.

The guard remains worth building -- consumers run these scripts, and a preventive
control on a path that has not yet leaked is cheaper than a corrective one after
it has. But it is preventive, and the plan should say so rather than inheriting a
rate it did not earn.

### 3. An advisory control reports nothing today

Measured against `build_body` over the 74 unaddressed events (a 591-line body),
with origin and destination both `MythologIQ-Labs-LLC/Qor-logic` and the
operator's seventeen overlay terms live:

| | |
|---|---|
| derived terms, dropped as self-reference | 2 |
| overlay terms surviving | 17 |
| **advisory findings on the live body** | **0** |

The over-refusal residue that dominated three planning rounds -- `qor` at 126
substring findings, `audit` at 81 -- is a property of *hypothetical consumers
whose checkout name collides with this repository's vocabulary*, not of the path
that runs. On the real path the control is silent.

That is the argument for advisory-first stated as a measurement rather than a
preference: there is no measured harm to prevent, so a blocking control cannot be
calibrated, and an escape cannot be sized. Ship it advisory, collect the rate,
and let a later phase decide with data.

### 4. The identity anchor must be the event source

The third VETO's blocking finding was that identity and events can resolve to
different repositories. The mechanism:

> `grep -n 'LOCAL_LOG_PATH = ' qor/scripts/shadow_process.py` -> `26:LOCAL_LOG_PATH = _workdir.shadow_log()`
> `grep -n 'return root()' qor/workdir.py` -> `42:    return root() / "docs" / "PROCESS_SHADOW_GENOME.md"`

`read_all_events()` reads those module-level constants, so the event source is
`root()` resolved at import. A vetoed plan anchored identity on
`_detect_git_root() or _workdir.root()`; `_detect_git_root` runs
`git rev-parse --show-toplevel` with no `-C` and no `cwd=`, resolving from the
process directory and short-circuiting `$QOR_ROOT` whenever any repository is
present. With `QOR_ROOT` pointing at a consumer and the command run from this
checkout, events load from the consumer while terms derive from here, every term
drops as self-reference, and the consumer's name files.

The fix is not a better root function. **Derive identity from the directory the
log was read from**, so the two cannot diverge: for `root()/docs/<log>.md`, the
anchor is the log path's grandparent. A wrong anchor then yields a body composed
from a repository the operator did not intend, which is visible, rather than a
silently disarmed guard, which is not.

### 5. The advisory shape is already this repository's idiom

`qor-audit`'s pre-audit ladder runs fourteen lints wrapped `|| true`, and
`qor-substantiate` carries WARN-only steps at 4.6.6, 4.6.7 and 4.6.9, each with a
stated V2 path to enforcement. Phase 283 shipped the nightly-health boundary step
on the same pattern: advisory now, detection later, with the operator choosing the
split.

So advisory-first needs no new convention, and the plan can cite the ladder rather
than invent a posture.

### 6. The cited escape precedent is broken

`merge_velocity_check.py:251` calls `shadow_process.append_event` with neither
`attribution=` nor `log_path=`:

> `grep -n 'append_event requires' qor/scripts/shadow_process.py` -> `122:            raise ValueError("append_event requires attribution=... or log_path=...")`

Executed with that shape, it raises. So `merge_velocity_check --override` -- the
documented escape from a fail-closed seal gate -- cannot run. A vetoed plan cited
this as "this repository already has the shape", which was true of the intent and
false of the code.

This is out of scope for the filing control and belongs in its own issue.

## Blueprint Alignment

| Claim | Finding | Status |
|---|---|---|
| The filing channel leaks at 7 of 7 | That rate is the hand-filing channel's; the guarded path is 0 of 1 | **DRIFT** |
| `create_shadow_issue` is an unexercised path | It filed GH #439 on 2026-09-04 | **DRIFT** |
| Over-refusal is the control's main risk | 0 findings on the live corpus; the residue is hypothetical-consumer-only | **DRIFT** |
| An escape is required for shippability | Required only for a *blocking* control; advisory needs none | **DRIFT** |
| `merge_velocity_check --override` demonstrates the logged-escape shape | It raises `ValueError` and cannot run | **DRIFT** |
| Identity can be derived independently of the event source | Divergence disarms the guard silently | **DRIFT** |

## Recommendations

1. **P0 -- ship advisory.** The control reports, records and files. No refusal, no
   escape, no override friction. That removes the two decisions every VETO
   clustered on and is the repository's existing idiom.
2. **P0 -- anchor identity on the log's own directory**, not on a root function.
   Divergence then cannot occur, and a misconfigured anchor produces a visibly
   wrong report rather than a silently disarmed control.
3. **P1 -- state the preventive framing.** The plan should cite 0-of-1 on the
   guarded path and attribute 7-of-7 to the hand-filing channel a later reporting
   skill serves. A phase that inherits the wrong rate will keep over-designing
   against it.
4. **P1 -- the advisory record is the deliverable.** What the control writes, and
   what reads it back, is what makes a later blocking phase possible. A control
   that warns into a void produces no calibration.
5. **P2 -- file the `merge_velocity_check --override` defect.** A fail-closed seal
   gate whose escape raises is a live governance hole, unrelated to this phase.

## Updated Knowledge

For `docs/SHADOW_GENOME.md`: a justification figure can be measured, reproduced,
cited across a dozen iterations, and attached to the wrong channel throughout. The
seven-of-seven rate survived three plan iterations, two VETOs and four independent
reviews without anyone asking which path it described -- because every reviewer
checked whether it was *true* and none checked what it was *about*. The
countermeasure is to name the subject of a rate in the same sentence that states
it: not "the channel leaks 7 of 7" but "hand-filed reports leak 7 of 7."

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
