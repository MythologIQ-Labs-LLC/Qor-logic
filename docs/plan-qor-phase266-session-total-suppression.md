# Phase 266 -- honour the suppression marker in session-total escalation

**change_class**: hotfix
**iteration**: 9
**risk_grade**: L2
**closes**: GH #447

## Problem

`cycle_count_escalator.check_session_total` documents that it honours the
escalation-suppression marker. It never reads it.

```python
def _suppression_active(session_id: str, first_match_ts: str | None) -> bool:
    session.validate_session_id(session_id)
    if first_match_ts is None:
        return False              # always taken from check_session_total
    marker = _workdir.root() / ".qor" / "session" / session_id / "escalation_suppressed"
    ...
```

`check_session_total` calls it as `_suppression_active(session_id, None)`
(`qor/scripts/cycle_count_escalator.py:77`), so the guard short-circuits and the
marker file is never opened. Its docstring at `:69` says "Respects the same
suppression marker as `check`."

Confirmed by execution: `cce._suppression_active("<any valid sid>", None)`
returns `False` whether or not the marker exists.

Both escalation modes are surfaced together at `/qor-audit` Step 0.5 and
`/qor-plan` Step 2c, and the documented operator path on a false positive is to
decline, which calls `orchestration_override.record` and writes the marker. For
the consecutive-streak mode the decline sticks. For the session-total mode it
does not: the recommendation re-fires on the next audit in the same session, and
each decline appends another severity-2 `orchestration_override` event to the
Process Shadow Genome.

The operator therefore has no way to decline a session-total escalation once.
The only exit is to let the signature streak break naturally, which the
session-total counter is specifically built never to do -- it does not reset.

## Why it survived

No test covers suppression BEHAVIOUR in session-total mode. Two tests touch
suppression: `tests/test_cycle_count_escalator.py:108` exercises the
consecutive-streak `check`, and `tests/test_session_id_path_safety.py:34-38`
asserts that `_suppression_active` rejects a traversal session id. Neither
reaches `check_session_total`. Phase 69 added `check_session_total` alongside it and copied the
suppression line without the timestamp that makes it work.

## Design

### D1: the K-window anchor

`_suppression_active` returns `marker_ts > first_match_ts` and accepts any
string, so the caller may pass ANY element of a signature's contributing
timestamp list. Iterations 1 through 3 treated the oldest and newest elements as
the only options and were vetoed at entry #750 for it; the interior of that list
is available and one interior point is better than either end.

Let a signature's contributing timestamps be `t1 < ... < tN` and let
`K = ESCALATION_THRESHOLD = 3`. **Anchor on `t[N-K+1]`, the oldest member of the
most recent K occurrences.** The index is always valid because the anchor is only
evaluated once `N >= K`.

The operator declines at some count `n0`, and `orchestration_override.record`
writes the marker with `now_iso()`, so `M > t[n0]`. Suppression then holds while
`M > t[N-K+1]`, that is while `N <= n0 + K - 1`, and lapses at `N = n0 + K`.

Measured, seeding one signature to three occurrences and declining at N=3:

```
N=3  anchor=10:00:00Z  suppressed=True   count_at_marker=3
N=4  anchor=10:01:00Z  suppressed=True   count_at_marker=3
N=5  anchor=10:02:00Z  suppressed=True   count_at_marker=3
N=6  anchor=10:11:00Z  suppressed=False  count_at_marker=3
N=7  anchor=10:12:00Z  suppressed=False  count_at_marker=3
```

Three properties, each of which one of the rejected anchors lacked:

- **It satisfies GH #447.** The operator declines once and gets silence, which
  the newest anchor did not deliver.
- **It survives the Step 0.5 against Step Z ordering.** The escalator runs before
  the audit and the audit appends its own record after, taking the count to
  `n0 + 1`; `n0 + 1 <= n0 + K - 1` for `K = 3`, so the declining audit does not
  defeat its own marker. This is what killed iteration 2.
- **It re-arms.** Silence ends after `K` further occurrences rather than lasting
  the session, which is what made iteration 3's oldest anchor unacceptable.

The count at decline time needs no new field: it is recoverable as
`len([ts for ts in contributing if ts < marker_ts])`, stable at 3 in every row
above. Entry #750 asserted that re-arming required a marker format change. That
assertion was false and is corrected in that entry.

**The same-second cases are fixed, not disclaimed.** `now_iso()` formats to whole
seconds, so a decline can share a second with a contributing record. Iterations 4
and 5 disclaimed this on the grounds that fixing it "means changing the marker's
time resolution, which `check` shares". That is false, and it is the third false
impossibility this plan has used to justify not doing something -- after
iteration 3's "the marker's format allows only two anchors" and entry #750's "a
better timestamp cannot fix a missing field". `check_session_total` need not
delegate its comparison semantics to a helper shared with `check`; it can ask for
an inclusive comparison. `_suppression_active` gains `inclusive: bool = False`,
and the cumulative mode passes `inclusive=True`, so it compares `marker >= anchor`
while `check` keeps `marker > anchor` untouched.

Measured across the four cases that matter, `gt` being today's `>` and `ge` the
proposed `>=`:

```
normal, M strictly between t3 and t4 (n0=3)
  N=3 gt=True  ge=True    N=4 gt=True  ge=True
  N=5 gt=True  ge=True    N=6 gt=False ge=False      identical
pairwise collision, M == t[n0]
  N=3 gt=True  ge=True    N=4 gt=True  ge=True
  N=5 gt=False ge=True    N=6 gt=False ge=False      gt lapses one early; ge correct
same-second K-tuple, decline inside it
  N=4 gt=False ge=True                                gt misses suppression; ge holds
marker strictly older than the anchor (T2's direction)
  N=3 gt=False ge=False                               unchanged
```

`>=` reproduces `>` exactly in the normal case, repairs the one-occurrence-early
lapse in the pairwise case, and removes the missed suppression in the K-tuple
case, while preserving the direction T2 pins.

**And the corpus question this plan named but did not answer, now answered.**
Iteration 5 said the invariant worth checking was the absence of a same-second
K-tuple rather than a pair, and then checked neither. Measured across the 188
session histories with the synthetic fixture excluded: **zero signatures with a
same-second pair, zero with a same-second K-tuple.** The fix is therefore
precautionary rather than corrective; nothing in the repository's history exercises
it. That is stated so the next reader does not mistake a guard for a repair.

### D2: add a sibling accessor, do not widen the existing return type

`stall_walk.count_session_signature_totals` returns `dict[str, int]` and has
exactly one production consumer (`cycle_count_escalator.py:71`), but its shape is
asserted at `tests/test_session_total_signature_count.py:70,80,99,116,132,149`
and `tests/test_findings_signature_schema_parity.py:101` -- seven call sites. Widening it to return tuples
would redden those tests for no behavioural reason.

Instead add `stall_walk.session_signature_timestamps(session_id) -> dict[str, list[str]]`
returning the contributing `ts` list per signature SORTED ascending, walking the same
records under the same exclusions (PASS records skipped, LEGACY-sentinel
skipped). Returning the list rather than a single chosen timestamp keeps the
anchor decision in the escalator, where the threshold constant lives, and lets a
test address any element.
`count_session_signature_totals` is left byte-identical.

Both functions then walk `audit_history.read` separately. That is one extra read
of a file that is already read twice per check; the duplication is accepted in
exchange for not touching a pinned return type. If a future phase needs a third
projection, that is the point to extract a shared `_session_signature_stats`.

### D3: filter suppressed signatures, THEN select the winner

Entry #750's second blocking ground was that a suppressed winner masks every
other over-threshold signature, because `check_session_total` selects one winner
and returns `None` when it is suppressed. That is a property of the control flow,
not of the anchor, and no choice of anchor repairs it. The selection must filter
first:

```python
totals = stall_walk.count_session_signature_totals(session_id)
if not totals:
    return None
over_threshold = [(sig, n) for sig, n in totals.items() if n >= ESCALATION_THRESHOLD]
if not over_threshold:
    return None
stamps = stall_walk.session_signature_timestamps(session_id)
live = [
    (sig, n) for sig, n in over_threshold
    if not _suppression_active(
        session_id, stamps[sig][-ESCALATION_THRESHOLD], inclusive=True
    )
]
if not live:
    return None
live.sort(key=lambda item: (-item[1], item[0]))
signature, count = live[0]
```

Measured on the two-signature fixture that produced the veto, with the marker
written when only the first signature had crossed:

```
OVER: [('31501b86', 3), ('51b783fe', 3)]
winner-only (vetoed D3): None
filter-then-select     : 51b783fe
   31501b86 suppressed: True
   51b783fe suppressed: False
```

The declined signature stays silent and the one the operator never saw is
reported.

**The accessor must sort, and ascending order is not inherited.** `audit_history.read`
returns records "in file order" by its own docstring
(`qor/scripts/audit_history.py:63-64`) and nothing in `append` enforces monotonic
`ts`. The codebase already treats file order as untrustworthy: `_walk_backward`
sorts explicitly at `qor/scripts/stall_walk.py:48` for this reason. So
`session_signature_timestamps` establishes ascending order by sorting each list
before returning it; appending in read order would leave `stamps[sig][-K]`
addressing the wrong element on a single out-of-order record, silently, with no
exception and no red test. T6 therefore seeds out-of-order records, or it asserts
a property nothing could violate.

`stamps[sig][-K]` is safe, but not because the two accessors "apply identical
filters" -- that is the property the implementation must achieve, not an argument
that it has. The guarantee is structural: `ts` is in the audit artifact schema's
`required` list with a pinned `^....-..-..T..:..:..Z$` pattern
(`qor/gates/schema/audit.schema.json:7,10`), and `audit_history.read` re-validates
every line against that schema (`qor/scripts/audit_history.py:86`), so no record
reaching either accessor can lack a well-formed `ts`. Indexing `[-K]` is then safe
because `n >= K` is the filter that admitted the signature.

**Implementation constraint, stated because the trap is in the same file.**
`stall_walk._list_break_artifacts` uses the defensive idiom `ts = payload.get("ts")`
followed by `if ts:` at `qor/scripts/stall_walk.py:35-37`. The new accessor MUST NOT
copy it. A conditional append there is a filter `count_session_signature_totals`
does not have, so the timestamp list would be shorter than the count for that
signature and `[-K]` would silently address the wrong element or raise
`IndexError`. The accessor appends `record["ts"]` unconditionally for every record
the counter counts.

### D4: correct the docstring, and correct the doctrine it points at

`_suppression_active` (`qor/scripts/cycle_count_escalator.py:32-40`) has NO
docstring today, and this phase gives it two comparison semantics behind a flag.
That is the founding defect of this cluster repeated at one level down: GH #447
exists because `check_session_total`'s docstring promised behaviour its body did
not have, and an undocumented helper carrying a mode switch is the same hazard
with nothing written to be wrong. It gains a docstring stating both semantics --
`inclusive=False` compares `marker > anchor` for the consecutive mode,
`inclusive=True` compares `marker >= anchor` for the cumulative mode, and the
argument is the run anchor in the first case and the K-window floor in the second.

`check_session_total`'s docstring at `:69` says "Respects the same suppression
marker as `check`." After this phase it respects the same marker FILE under
different semantics, so the sentence is replaced rather than left to become
technically true: suppression is per signature, anchored on the K-window floor,
and re-arms after `K` further occurrences. It is not "per winning signature" --
that phrasing belonged to the vetoed winner-then-suppress order and D3 removes it.

`qor/references/doctrine-governance-enforcement.md` section 10.5 states that
`_suppression_active` checks the marker against the run's `first_match_ts` and
that "if the marker is newer, the escalation is suppressed for the remainder of
the session". The second half is false for `check` today, independently of this
phase: a PASS or implement break resets the run and advances `first_match_ts` past
the marker, so the escalation re-fires. Measured at entry #750, `first_match_ts`
moves from `10:00:00Z` to `10:04:00Z` across a PASS. The sentence is corrected in
this phase because this phase changes the neighbouring behaviour and would
otherwise leave the doctrine describing two modes it now matches neither of.

## Scope boundary

Not in scope: the adjacent finding recorded in GH #447 that
`orchestration_override.record` puts an interpolated `reason` into event details,
so `/qor-plan`'s `f"user override: {result.errors}"` declines never collapse
under `check_shadow_threshold.collapsed_severity`. That is a separate defect in a
separate module with a separate blast radius, and folding it in would make this
patch a two-module change. It stays on #447 after this phase closes the
suppression half, or moves to its own issue.

Not in scope: GH #448, the missing `session.validate_session_id` at the head of
`check_session_total`. `check` validates before building a path and its sibling
does not, confirmed by execution: `check("../evil")` raises `ValueError` while
`check_session_total("../evil")` returns `None` having already attempted the
traversed read. This phase adds a `_suppression_active` call, and that helper
validates, so a traversal id would raise AFTER the unvalidated read rather than
before it. That is not a fix and must not be recorded as one.

Not in scope: any new escalation mode. The scope-count proposal in
`.qor/gates/2026-09-05T0227-eb46ab/remediate-iter4.json` is blocked on this fix
but is not part of it.

## Tests (written first)

Entry #750's reviewer found that none of iterations 1-3's tests discriminated the
anchors: at `N = K` the K-window floor and the oldest contributing record are the
SAME timestamp, so every test passed under both designs. The table below is built
so that at least one case separates each rejected design from the chosen one.

`tests/test_cycle_count_escalator.py` patches `audit_history._workdir.gate_dir`,
`stall_walk._workdir.gate_dir` and `cycle_count_escalator._workdir.root`, which is
the correct set, but its `_check` helper calls `check`. A sibling `_check_total`
helper calling `check_session_total` under the same three patches is added first;
without it none of T1-T8 can be written in the file the plan names.

| # | Test | Discriminates |
|---|---|---|
| T1 | `test_session_total_decline_suppresses_at_threshold` | red today: the marker is never read |
| T2 | `test_session_total_marker_older_than_anchor_does_not_suppress` | pins direction; a fix that always suppresses fails here |
| T3 | `test_session_total_suppression_survives_the_declining_audits_own_record` | at `N = n0 + 1`, still suppressed -- **fails under the newest anchor** (iteration 2) |
| T4 | `test_session_total_escalation_rearms_after_k_further_occurrences` | at `N = n0 + K`, fires again -- **fails under the oldest anchor** (iterations 1 and 3) |
| T5 | `test_declined_signature_does_not_mask_an_undeclined_one` | two signatures at threshold, one declined; asserts the OTHER is returned -- **fails under the vetoed winner-only D3** |
| T6 | `test_session_signature_timestamps_are_sorted_and_exclude_pass_and_legacy` | seeds records whose file order is NOT ascending; vacuous without that |
| T7 | `test_count_session_signature_totals_is_unchanged` | guards D2 |
| T8 | `test_same_second_decline_still_suppresses` | marker equal to the anchor. Red TODAY for T1's reason -- the marker is never read at all -- and red again if the anchor and filter land WITHOUT `inclusive=True`. Those are two different reds and only the second one tests the flag; an implementer must confirm it fails at the intermediate commit, not just at HEAD. The only test covering a case the corpus never produces |

T3 and T4 are the pair that made the previous iterations untestable. Together they
bracket the K-window: suppression must hold at `n0 + 1` and must not hold at
`n0 + K`. No single-endpoint anchor satisfies both.

**The bracketing is conditional, and the condition is the test's own construction.**
These tests write the marker directly rather than through
`orchestration_override.record`, as the existing suppression test already does at
`tests/test_cycle_count_escalator.py:116-118`, so the marker timestamp is chosen by
the author. T3 and T4 MUST seed the marker strictly between the `n0`-th and
`(n0+1)`-th contributing record. The natural shortcut -- seed all N records, then
write the marker -- puts the marker after every record and destroys the
discrimination:

```
M between t3 and t4:
  T3 (N=4, expect suppressed)  kwindow=True  newest=False  oldest=True   -> newest FAILS
  T4 (N=6, expect fires)       kwindow=False newest=False  oldest=True   -> oldest FAILS
M after all records:
  T3 (N=4, expect suppressed)  kwindow=True  newest=True   oldest=True   -> nothing fails
  T4 (N=6, expect fires)       kwindow=True  newest=True   oldest=True   -> everything fails
```

T4's failure under a late marker is loud: it reddens under the chosen anchor too,
so an implementer taking the shortcut is stopped. T3's is silent -- it stays green
and quietly discriminates nothing, which is precisely how iterations 1 through 3
came to have six tests and no coverage. The ordering is the load-bearing part of
these two tests, not the assertion.

T7 is weak by construction, since D2 leaves the function untouched; it is kept
only as a tripwire against a later refactor folding the two accessors together,
and the plan does not claim it is red beforehand. T2 is also green beforehand and
is labelled as such rather than being counted as test-first coverage.

## Affected files

| File | Change |
|---|---|
| `qor/scripts/stall_walk.py` | add `session_signature_timestamps`; `count_session_signature_totals` untouched |
| `qor/scripts/cycle_count_escalator.py` | give `_suppression_active` a docstring covering both comparison semantics; add `inclusive: bool = False` to it; anchor on the K-window floor `stamps[sig][-K]` with `inclusive=True`; filter suppressed signatures out of `over_threshold` BEFORE sorting and selecting, per D3 -- not the vetoed winner-then-suppress order |
| `tests/test_cycle_count_escalator.py` | add `_check_total` helper; T1-T8, with T3/T4 seeding the marker between the `n0`-th and `(n0+1)`-th record and T6 seeding out-of-order records |
| `qor/references/doctrine-governance-enforcement.md` | rewrite section 10.5 to describe BOTH modes -- correcting its claim that a marker suppresses "for the remainder of the session", false for `check` whose run resets, AND stating `check_session_total`'s K-window semantics, so that line 278's "Same suppression marker applies (10.5)" resolves to a description covering the mode it points from |
| `tests/test_session_total_signature_count.py` | extend `isolate_gates_dir` to patch `_workdir.root` to `tmp_path` exactly, since `workdir.gate_dir()` is `root()/".qor"/"gates"` and the fixture pins that path; without it the two existing `check_session_total` tests stat the real repo root once this phase makes the marker load-bearing |

Five files, three behavioural changes -- the K-window anchor, the filter-then-select
selection order, and the inclusive comparison -- and no public signature removed or
altered. `_suppression_active` gains a keyword argument with a default that
preserves every existing call site.

## CI Commands

```
python -m pytest tests/test_cycle_count_escalator.py tests/test_session_total_signature_count.py tests/test_findings_signature_schema_parity.py tests/test_stall_walk.py tests/test_orchestration_override.py tests/test_session_total_escalator_skill_wiring.py -q
python -m pytest -q
```

The second is required, not optional: this repository's seal step writes badges
and a SYSTEM_STATE header that freshness tests assert against, so the full suite
must be re-run after substantiation as well as before it.

## Limitations stated

- T8's discrimination is not observable from a green run at HEAD. It is red today
  for T1's reason, the marker is never read at all, and red again only if the
  anchor and filter-then-select land WITHOUT `inclusive=True`. Only that second
  red exercises the flag, so the implementer must confirm T8 fails at the
  intermediate commit. A final all-green run does not establish it, and no
  artifact in this phase records it; it is a discipline the implementer owes,
  stated here because it has nowhere else to live.
- A decline suppresses that signature for `K - 1` further occurrences and then
  re-arms. A second signature crossing the threshold escalates on its own and
  needs its own decline; unlike iterations 1 through 3, that is now covered, by
  T5, and it is covered because the vetoed design got it wrong rather than
  because a fixture exhibits it. No real session in the corpus has ever had two
  signatures at three or more, so T5's scenario is synthetic by necessity.
- Design history, kept because it is the evidence for the chosen anchor rather
  than an apology for it. Iteration 1 anchored on the oldest contributing record
  and justified it by a claimed equivalence to `check`; execution refuted the
  equivalence. Iteration 2 switched to the newest record; tracing the skill's
  step order showed the declining audit's own record defeats it. Iteration 3
  returned to the oldest anchor and asserted the marker's format admitted only
  those two options; entry #750 vetoed it for masking undeclined signatures, and
  then had to be amended because that assertion was false too. Iteration 4 takes
  the interior anchor the first three argued did not exist, and adds the
  selection-order change no anchor could have supplied.
- `session_signature_timestamps` walks `audit_history.read` a second time per
  check. Measured cost is not stated here because it has not been measured; the
  file is a session-local JSONL of at most a few dozen records, and the claim
  made is only that the duplication exists, not that it is negligible.
- The comparison remains a lexicographic string comparison of ISO timestamps,
  which is correct for the `%Y-%m-%dT%H:%M:%SZ` form `shadow_process.now_iso`
  emits and would break on a mixed-offset format; no record in the corpus carries
  one. Iteration 7 changes the comparison OPERATOR for the cumulative mode, from
  `>` to `>=`, so the earlier wording "is not being changed here" no longer holds
  and has been replaced. What is unchanged is the string-comparison basis and
  `check`'s use of `>`.
