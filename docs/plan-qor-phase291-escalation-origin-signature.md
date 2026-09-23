# Plan: escalation payloads carry no collapsing key, so escalations of one condition count separately

**change_class**: hotfix

**doc_tier**: standard

**boundaries**:
- limitations: Only `qor/scripts/check_shadow_threshold.py` changes. No caller
  of `_signature`/`collapsed_severity`/`sweep` changes its call signature.
- non_goals: No change to `STALE_DAYS`, `THRESHOLD`, or the stale-expiry rule
  for severity 1-2 events (GH #484 is scoped to severity >=3 escalation
  collapsing only). No change to `_pending_discount_applies` or the
  `superseded` chain-collapsing rule Phase 285 shipped (GH #484's own body:
  "Phase 285 bounded the quantity. This is the remaining 15").
- exclusions: No change to `write_marker`/`remove_marker`/`main`'s CLI
  surface. No backfill/migration of existing log entries: GH #484 states
  "There are currently zero escalation events in the log", confirmed live
  (`python -c "from qor.scripts import shadow_process as sp, check_shadow_threshold as cst; print(len([e for e in sp.read_all_events() if e['event_type']==cst.ESCALATION_EVENT]))"` -> `0`), so the new field reaches every escalation that will ever exist without a legacy-shape branch needing exercise against real data.

## Recomposition note

This is the identical design/implementation previously sealed as Phase 289
(`Qor-logic` PR #491, branch `phase/289-escalation-origin-signature`,
session `2026-09-16T0321-901b4c`, ledger Entries #796/#797 against base
`f3e069b`). Phase 290 (PR #492, "GH #482; ancestor-reachability is not
CI-success") independently forked from the same `f3e069b` base, sealed its
own Entries #796/#797, and merged to `main` first (merge commit
`d37c192c91d6bee95c7fccb14896eb4554b10469`), so Phase 289's own ledger
entries, `pyproject.toml` version target (`0.174.1`), and
`docs/SYSTEM_STATE.md` snapshot collide with what is now actually on `main`
rather than merging cleanly. Per owner direction (PR #491 comment
`5790286173`, 2026-09-23): PR #491 and its branch are preserved as
historical evidence rather than force-merged or rebased in place; this is a
fresh phase/session recomposing the same code+test diff (verified
byte-for-byte via `git diff f3e069b 1435d5cc -- qor/scripts/check_shadow_threshold.py tests/test_escalation_origin_signature.py tests/test_escalation_supersedes.py`,
then `git apply --check` against fresh `d37c192c`: applies cleanly, no
conflict) against current `main`, with fresh ledger numbering, version
target, and citations. The design rationale (LD-1 through LD-5 below) is
unchanged from Phase 289's own independent technical review (PR #491
comment `5258796141`, exact-head COMMENT review, no blocking finding).

## Open Questions

None.

## Locked Decisions

### LD-1: `_signature` gives every escalation a unique key today, defeating collapse

`git show d37c192c:qor/scripts/check_shadow_threshold.py | grep -n 'def _signature\|details.get("gate")\|hashlib.sha256' -> observed:
93:def _signature(event: dict) -> tuple:
113:    key = details.get("gate") or details.get("capability") or details.get("pattern")
116:        key = "details:" + hashlib.sha256(blob).hexdigest()[:12]`
confirms `_signature` resolves `details.get("gate") or details.get("capability")
or details.get("pattern")`, falling back to a sha256 digest of the full
details blob when none is present.

`git show d37c192c:qor/scripts/check_shadow_threshold.py | grep -n 'def sweep\|elif e\["severity"\] >= 3\|aged_entry_id' -> observed:
40:def sweep(events: list[dict], now: datetime) -> tuple[list[dict], list[dict], int]:
63:        elif e["severity"] >= 3 and e["id"] not in existing_escalations:
71:                    "aged_entry_id": e["id"],`
confirms an escalation's own `details` is always
`{"aged_entry_id", "aged_skill", "age_days"}` — none of
`gate`/`capability`/`pattern` — so every escalation falls to the digest
branch, and `aged_entry_id` (unique per source event) makes that digest
unique per escalation. GH #484's own measurement: four `degradation`
escalations sharing one `gate` should contribute one severity-5 slot, not
four (20).

### LD-2: the escalation signature must not collide with a live plain event's own signature

`grep -n "def test_a_superseded_event_does_not_claim_its_signature_slot" -A 15 tests/test_escalation_supersedes.py`
pins: a superseded original (`gate="g"`) plus its escalation, plus a live
sibling event also `gate="g"`, must total 8 (escalation's 5 + sibling's 3),
not 5. The escalation and the sibling must therefore never share a
`_signature` result even when the escalation's origin condition is the same
`gate` the sibling carries. Any fix that returns the origin's raw
`(event_type, key)` tuple unchanged for an escalation breaks this test by
construction (the escalation would then equal the sibling's own signature).
The escalation's signature must be a distinct value derived from the origin,
never the origin's own tuple.

### LD-3: GH #484 documents two ways this was already gotten wrong once

Quoted in the issue body: "The key discarded half the discrimination" (a
key built from the origin's second tuple element alone re-merges two
distinct `event_type`s sharing one `gate`/`capability`/`pattern`, e.g. the
live `("gate_skipped_prerequisite_absent", "intent_lock")` closed signature
-- `grep -n 'gate_skipped_prerequisite_absent.*intent_lock' tests/test_shadow_residue_disposition.py -> 40:    ("gate_skipped_prerequisite_absent", "intent_lock"),`
-- must stay distinguishable from a hypothetical
`("gate_override", "intent_lock")`), and
"The key compounded across generations" (prefixing a growing `escalated:`
string onto the previous key on each escalation-of-escalation never
stabilizes, so a chain never collapses with a fresh single-generation
escalation of the same root condition). Both must be true simultaneously:
full origin discrimination (event_type + key), and generation-invariance (an
escalation's stored origin is always the *root* disclosed event's own
signature, never a wrapped signature of its immediate parent).

### LD-4: `_signature` has exactly one production caller and two test-file callers

`grep -rn "_signature(" --include=*.py .` outside `tests/` shows only the
definition (line 93) and its one call site inside `collapsed_severity`
(line 189). `grep -rln "cst\._signature"` tests/` shows
`tests/test_shadow_residue_disposition.py` and
`tests/test_signature_discrimination.py`. Both are read-only (build a set
of signatures, or assert `_signature(event)[1] == ...`); neither constructs
an `ESCALATION_EVENT`-shaped event, so a behavior change scoped to
`event_type == ESCALATION_EVENT` cannot affect either.

### LD-5: `sweep` builds every new escalation from `e`, the source event, in hand

`git show d37c192c:qor/scripts/check_shadow_threshold.py | grep -n 'elif e\["severity"\] >= 3\|new_event = {' -> observed:
63:        elif e["severity"] >= 3 and e["id"] not in existing_escalations:
64:            new_event = {`
shows the `elif e["severity"] >= 3` branch already holds a reference to `e`
(the event being escalated) at the exact point `new_event["details"]` is
assembled. `e` is the correct and only input needed to compute the
escalation's origin signature — including when `e` is itself a prior
escalation (the chain case LD-3 names), since `e`'s own `details` already
carries whatever origin signature *it* was given at its own creation.

## Phase 1: pin the current (defective) and target behavior in tests

### Affected Files

- `tests/test_escalation_origin_signature.py` - NEW.

### Changes

None yet; tests only, against the current implementation, so the target-
behavior assertions are observably red first.

### Unit Tests

All in the new file. Each builds events with the existing `_event`/
`_escalation_of`-style literal dict shape already used by
`tests/test_escalation_supersedes.py` (no shared fixture import, to keep
this file readable standalone per that file's own convention).

- `test_escalations_of_the_same_root_condition_collapse` - two distinct
  source events, same `event_type="degradation"` and `details={"gate": "g"}`,
  different `id`s; each has its own escalation (as `sweep` would produce,
  with an `origin_signature` field). `collapsed_severity` over both
  escalations (sources omitted, as a chain's superseded originals would be)
  totals 5, not 10. Red before: each escalation's `details` differs only in
  `aged_entry_id`, so today's digest fallback makes them unique and the
  total is 10.
- `test_escalations_of_different_root_event_types_sharing_a_key_do_not_collapse`
  - the LD-3 negative control: two source events, `event_type="gate_override"`
  and `event_type="gate_skipped_prerequisite_absent"`, both
  `details={"gate": "intent_lock"}`; each escalated. Total is 10, not 5.
  This is the test the issue says the obvious positive-only test "cannot
  catch": it must keep failing red if a fix keys collapse on `key` alone
  without `event_type`.
- `test_escalation_of_an_escalation_carries_the_root_signature_unchanged` -
  a source event is escalated (escalation 1), then escalation 1 is itself
  escalated (escalation 2, `sweep`'s own aging-out-an-escalation path,
  already exercised structurally by
  `test_a_chain_of_escalations_counts_only_its_live_tip`). Escalation 2's
  stored origin signature equals escalation 1's stored origin signature
  exactly (same 2-tuple, no nesting, no string growth) — asserted directly
  on the `details` payload, not inferred from a severity total.
  Red before: no `origin_signature` field exists to compare.
- `test_a_three_generation_chain_collapses_with_a_fresh_single_generation_escalation_of_the_same_root`
  - builds a 3-generation escalation chain (escalation 1 -> 2 -> 3, only 3
  live/unsuperseded) rooted at `("degradation", "g")`, and separately a
  fresh single-generation escalation of a *different* source event that
  shares the same root `("degradation", "g")`. `collapsed_severity` over
  {chain's live tip, fresh escalation} totals 5, not 10 — proving
  generation-depth is invisible to collapsing, not merely non-growing.
- `test_a_superseded_event_does_not_claim_its_signature_slot` (moved/adapted
  from `tests/test_escalation_supersedes.py`, updated to build its escalation
  with the new `origin_signature`-bearing shape) - re-pins LD-2 under the
  new shape specifically, since the existing copy of this test in
  `test_escalation_supersedes.py` uses the old shape and would pass
  trivially (both before and after) without exercising the new field at
  all.

## Phase 2: implement the origin-signature collapsing key

### Affected Files

- `qor/scripts/check_shadow_threshold.py` - add `_base_signature`, add
  `_origin_signature`, rewrite `_signature` in terms of both, extend the
  `sweep` escalation-construction branch to compute and store
  `details["origin_signature"]`.
- `tests/test_escalation_supersedes.py` - update the `_escalation_of` helper
  to include `origin_signature` in the dict it returns (computed via
  `cst._origin_signature(source)`), so the file's own header comment ("The
  shape `sweep` appends") stays true. No assertion in this file changes
  value: LD-2's collision-avoidance property means every existing total in
  this file is unaffected by the new field's presence (traced per-test
  against the Phase 2 design in this plan's own review, not re-derived at
  audit time).

### Changes

`_base_signature(event)`: the exact body `_signature` has today (lines
93-117 of `d37c192c`'s copy) unchanged, renamed. This is the signature an
event would have judged purely on its own `details`, with no escalation
ancestry considered.

`_origin_signature(event)`: if `event["event_type"] == ESCALATION_EVENT` and
`"origin_signature" in (event.get("details") or {})`, return that stored
2-list as a tuple, unchanged (LD-5: propagate, never recompute from the
escalation's own `aged_entry_id`-bearing details — that recomputation is
exactly the digest-uniqueness LD-1 names). Otherwise return
`_base_signature(event)`. This is the function `sweep` calls on `e` when
building a new escalation, so an escalation-of-an-escalation resolves to the
same root every generation (LD-3's second half) without recursion depth or
string concatenation.

`_signature(event)`: if `event["event_type"] == ESCALATION_EVENT` and
`"origin_signature" in (event.get("details") or {})`, return
`(ESCALATION_EVENT, _origin_signature(event))` — a 2-tuple whose first
element is the escalation's own type (never the origin's), so it can never
equal a live plain event's own `_base_signature`/`_signature` result (LD-2:
first elements always differ, since a plain event's first element is its own
`event_type`, never `ESCALATION_EVENT`, for any event this repository
emits). Otherwise (no stored origin — a legacy-shaped or synthetic
escalation, or any non-escalation event) return `_base_signature(event)`,
identical to today's behavior.

`sweep`'s escalation-construction branch (`elif e["severity"] >= 3 ...`):
after building `new_event`, set
`new_event["details"]["origin_signature"] = list(_origin_signature(e))`
before appending to `new_escalations`. `_origin_signature(e)` is called
before `new_event["id"]` is computed via `shadow_process.compute_id`, so the
new field participates in the id hash like every other field already does
(no special-casing needed there).

### Unit Tests

Phase 1's file, now green. No new tests in this phase; this phase exists to
turn Phase 1 red to green with the smallest change, per this repository's
TDD-Light discipline.

## Definition of Done

### Deliverable: escalations of one condition collapse to one contribution

- **D1**: `_signature` returns `(ESCALATION_EVENT, origin_signature)` for an
  escalation carrying a stored origin, so two escalations of the same root
  condition occupy the same `seen` slot in `collapsed_severity`.
- **D2**: `_origin_signature` reads a stored origin back unchanged rather
  than recomputing one from the escalation's own volatile details, so any
  depth of escalation-of-escalation resolves to the same root.
- **D3**: `test_escalations_of_the_same_root_condition_collapse` -- two
  escalations of the same root total 5, not 10 (observed before: 10).
- **D4**:
  `test_a_three_generation_chain_collapses_with_a_fresh_single_generation_escalation_of_the_same_root`
  -- a 3-generation escalation chain's live tip collapses with a fresh
  single-generation escalation of the same root, proving generation depth
  is invisible to collapsing, not merely non-growing.

### Deliverable: full discrimination is preserved

- **D1**: an escalation's signature always leads with `ESCALATION_EVENT`, so
  it can never equal a live plain event's own `_base_signature`.
- **D2**: `_origin_signature` returns the full `(event_type, key)` pair, not
  `key` alone, so two root conditions sharing a key but differing in
  `event_type` stay distinguishable after escalation.
- **D3**:
  `test_escalations_of_different_root_event_types_sharing_a_key_do_not_collapse`
  -- two such escalations total 10, not 5 (the negative control the issue
  says the obvious positive-only test misses).
- **D4**: `test_a_superseded_event_does_not_claim_its_signature_slot` (new
  shape) -- an escalated original plus a live plain sibling sharing its gate
  still total 8, not 5.

## Feature Inventory Touches

Empty. This plan touches `qor/scripts/` and `tests/` only.

## CI Commands

- `python -m pytest tests/test_escalation_origin_signature.py tests/test_escalation_supersedes.py tests/test_signature_discrimination.py tests/test_shadow_residue_disposition.py tests/test_shadow.py -q`
- `python -m pytest -q` (full suite, twice, for determinism per this
  repository's mandatory test discipline)
- `ruff check qor/scripts/check_shadow_threshold.py tests/test_escalation_origin_signature.py tests/test_escalation_supersedes.py`
