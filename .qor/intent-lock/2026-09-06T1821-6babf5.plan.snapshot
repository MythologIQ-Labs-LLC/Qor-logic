# Phase 267 -- make the discarded validation actually fire

**change_class**: hotfix
**iteration**: 5
**risk_grade**: L2
**closes**: GH #441, GH #448

Iterations 1 through 4 were vetoed. This document is rewritten rather than
patched: by iteration 4 it described four designs at once, because each revision
was edited onto the last. The design history is in Limitations.

## Problem

Three defects, one shape: a guard is called and its answer is thrown away.

### P1: `_validate_data` returns, two of its three callers assume it raises

`validate_gate_artifact._validate_data` returns `list[str]` and never raises.

| site | treats result as | correct |
|---|---|---|
| `validate_gate_artifact.py:194` | `errs = ...; if errs: raise` | yes |
| `audit_history.py:53` (`append`) | bare call, discarded | **no** |
| `audit_history.py:86` (`read`) | `try: ... except Exception: raise` | **no** |

`append`'s docstring says "Validate and append". It does not validate. `read`'s
handler raises `ValueError("Schema violation in {path} at line {line_num}")` --
the right error for the right reason, which can never fire because the call it
guards does not raise. Executed: `read` returns a record with no `ts`.

GH #441, whose title names both halves: "append accepts schema-invalid records,
and read's guard cannot fire". This phase closes the first by making `append`
raise and the second by REMOVING the guard rather than making it fire, for the
reason in D1. That is a deliberate asymmetric close and is stated here so the
issue is not recorded as fixed in a way it was not. (The issue body is empty --
two characters -- so the title is the whole specification.)

### P2: Phase 266 turned a tolerated bad row into a crash

`stall_walk.session_signature_timestamps` (Phase 266, GH #447, shipped in
v0.169.2) is the first consumer to index `record["ts"]`. Executed against a
history containing one schema-invalid row:

```
count_session_signature_totals            OK
session_signature_timestamps (Phase 266)  KeyError: 'ts'
check_session_total (at threshold)        KeyError: 'ts'
check                                     OK
```

A malformed row that was previously inert now aborts `/qor-audit` Step 0.5 and
`/qor-plan` Step 2c.

**The guarantee that made this look safe does not exist, and it is in three
places including shipped code.** The Phase 266 plan asserted it, ledger entry
#751 recorded it, and `stall_walk.py:119-121` carries it in the accessor's own
docstring:

> `ts` is schema-required with a pinned pattern and re-validated per line by
> `audit_history.read`, so no record reaching here can lack one.

`read` does not validate. That is a docstring promising behaviour its dependency
does not have -- the defect class GH #447 was filed for, one level down, shipped
by the phase that fixed GH #447. An independent reviewer supplied that
justification and both parties read `audit_history.py:86` without noticing the
call it wraps cannot raise.

### P3: `check_session_total` builds a path before validating

`check` validates first (`cycle_count_escalator.py:72`, carrying a
`GAP-SEC-05/07` comment). Its sibling does not. Executed:

```
check("../evil")                -> ValueError
check_session_total("../evil")  -> None, after attempting the traversed read
```

GH #448. Phase 266 added a `_suppression_active` call to `check_session_total`
and that helper validates, but only AFTER the unvalidated read, so it does not
close this.

## Design

### D1: `append` fails closed; `read` stays permissive and says so

Making both sides strict was iteration 1's design and it silently retires a
documented control. `audit.schema.json` carries
`allOf: [{if verdict == VETO, then required: [findings_categories]}]`, so a VETO
row without categories is schema-invalid. That is exactly the shape
`findings_signature.LEGACY_SENTINEL` recognises -- pre-Phase-37 audits -- and all
three consumers branch on it (`stall_walk.py:58`, `:98`, `:131`). A strict `read`
makes those branches unreachable, retiring behaviour documented at
`stall_walk.py:17`, `findings_signature.py:9-12`,
`doctrine-governance-enforcement.md:264` and
`qor-audit/references/phase37-subpasses.md:270`.

The split is therefore asymmetric:

- **`append` raises** on a schema-invalid record. It governs writes; nothing
  should create a row the schema rejects. This is what GH #441 asks for.
- **`read` does not validate**, and stops pretending to. Its inert `try/except`
  is removed and its docstring states that it parses without validating, because
  tolerating historical and foreign rows is why `LEGACY_SENTINEL` exists.

**This is a design statement, not a side effect.** After this phase the legacy
row shape is unproducible through the public writer and exists only as
pre-existing or foreign input. The four tests that seed it through `append` must
seed it by direct file write instead, which is what turns them into tests of a
read-side tolerance rather than of a round trip.

### D2: the accessors are allowed to disagree

`count_session_signature_totals` never touches `ts` and counts a VETO row that
lacks one. Executed, forcing agreement via a shared filtered iterator changes
that function's answer:

```
counter today                                {'51b783fe8051a55a': 2}
counter under a ts-filtering shared iterator {'51b783fe8051a55a': 1}
```

A signature could fall from `ESCALATION_THRESHOLD` to below it, so an escalation
that fires today would go silent. The counter is therefore untouched.
`session_signature_timestamps` collects `ts` only where usable, giving
`len(stamps[sig]) <= totals[sig]`, with equality on every row this repository has
written.

**"Usable" is defined here because four earlier drafts used the word without
defining it.** A `ts` is usable when the key is present AND its value matches the
schema pattern `^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$`. The
pattern matters, not only presence: the list is sorted lexicographically and
indexed positionally, so a malformed value would sort wrongly and anchor wrongly
rather than merely being extra.

**A third function keeps a third policy and this plan does not change it.**
`_walk_backward` reads `record.get("ts", "")` (`stall_walk.py:64`), tolerating a
missing value as empty string. After this phase the consecutive mode tolerates,
the counter ignores, and the timestamp accessor omits. Converting `_walk_backward`
would change `check`'s streak behaviour, which is out of scope for a fix to
`check_session_total`. Named so the divergence is stated rather than discovered.

### D3: the anchor degrades rather than the check being skipped

The K-window anchor `stamps[sig][-ESCALATION_THRESHOLD]` raises on a short list.
An earlier draft skipped the suppression check when the list was short and called
that "an escalation the operator can decline". Traced, that is false in exactly
the case it describes: `keep = True` without reading the marker, so an operator
can record a decline that does nothing, with no in-band escape. That is the
mirror of the defect entry #753 vetoed.

Degrade the anchor instead:

```python
if len(ts_list) >= ESCALATION_THRESHOLD:
    anchor = ts_list[-ESCALATION_THRESHOLD]
elif ts_list:
    anchor = ts_list[0]
else:
    anchor = None
keep = not _suppression_active(session_id, anchor, inclusive=True)
```

`_suppression_active` already returns `False` when its anchor is `None`
(`cycle_count_escalator.py:59-60`), so the empty case yields "not suppressed"
through existing code with no special case, and a decline is effective whenever
any anchor exists. The safe direction survives and the inert decline is gone.

### D4: `check_session_total` validates first

`session.validate_session_id(session_id)` as its first statement, matching
`check`. GH #448.

## Scope boundary

Not in scope, each named because this phase makes it more visible rather than
because it leaves it worse:

- Retiring `LEGACY_SENTINEL`. D1 preserves it deliberately.
- Converting `_walk_backward` to a shared `ts` policy. D2 states the divergence.
- Making the escalators degrade rather than propagate on a corrupt history file.
  Both modes already propagate every other error from `read`.
- `_validate_data`'s signature. Returning a list is a legitimate contract that
  one of its three callers uses correctly.

## Tests

### Existing tests this phase must change, derived by execution

The complete set was obtained by applying the strict `append` and running the
full suite, not by enumeration. Two hand-built lists produced three and then
four; the derived answer is five, and the fifth is a class neither list held.

| test | why it reddens | change |
|---|---|---|
| `test_stall_walk.py::test_run_resets_on_legacy_record` | seeds a legacy VETO through `append` | seed by direct file write |
| `test_cycle_count_escalator.py::test_legacy_records_do_not_escalate` | same | seed by direct file write |
| `test_cycle_count_escalator.py::test_session_signature_timestamps_are_sorted_and_exclude_pass_and_legacy` | same, and it is Phase 266's own test | seed by direct file write |
| `test_session_total_signature_count.py::test_legacy_sentinel_excluded` | same | seed by direct file write |
| `test_audit_history.py::test_append_creates_jsonl_record` | **different class**: fixture uses `session_id="s1"` and the schema requires `minLength: 3` | use a conforming id |

The fifth is not a legacy case and is not evidence about the legacy design. It is
a fixture that has always been schema-invalid and was accepted only because
`append` never checked.

### New tests

| # | Test | Status before |
|---|---|---|
| T1 | `test_append_rejects_a_veto_without_findings_categories` | red |
| T2 | `test_append_rejects_a_malformed_ts` | red |
| T3 | `test_append_rejects_a_short_session_id` | red; pins the fifth-test class |
| T4 | `test_read_tolerates_a_row_that_append_would_reject` | green before for the wrong reason (the handler is inert), green after for the right one (tolerance is the contract). Fails if a later change makes `read` strict |
| T5 | `test_legacy_row_written_directly_still_classifies_legacy` | green before; pins that D1's asymmetry preserved the control |
| T6 | `test_a_veto_without_ts_still_counts_but_yields_no_timestamp` | red; pins D2's asymmetry and fails if a future change filters the counter |
| T7 | `test_a_malformed_ts_value_is_omitted_not_sorted` | red; pins the "usable" definition against presence-only |
| T8 | `test_a_short_list_anchors_on_its_first_element_and_a_decline_takes_effect` | red; pins D3 against the inert-decline defect |
| T9 | `test_check_session_total_rejects_a_traversal_session_id` | red; GH #448, in `test_session_id_path_safety.py` beside the `_suppression_active` traversal test at `:34`; no `check` traversal test exists there |

T4 and T5 are green beforehand and are labelled as such rather than counted as
test-first coverage. T8 is the one that would have caught D3's earlier form.

## Affected files

| File | Change |
|---|---|
| `qor/scripts/audit_history.py` | `append` checks the return and raises; `read` loses the inert handler and its docstring states it does not validate |
| `qor/scripts/stall_walk.py` | `session_signature_timestamps` collects usable `ts` only; its false docstring guarantee replaced; `count_session_signature_totals` and `_walk_backward` untouched |
| `qor/scripts/cycle_count_escalator.py` | `validate_session_id` first in `check_session_total`; degraded anchor per D3 |
| `tests/test_audit_history.py` | conforming session id |
| `tests/test_stall_walk.py` | legacy row seeded by direct write |
| `tests/test_cycle_count_escalator.py` | two legacy rows seeded by direct write; T8 |
| `tests/test_session_total_signature_count.py` | legacy row seeded by direct write |
| `tests/test_session_id_path_safety.py` | T9 |
| `tests/test_audit_history_validation.py` | new; T1-T7 |
| `docs/META_LEDGER.md` | amend entry #751's false structural claim |

Three production files, six test files. The production change is four behaviours:
a raise in `append`, a removed handler in `read`, a filtered collection plus
corrected docstring in `stall_walk`, and a validation call plus degraded anchor in
`cycle_count_escalator`.

## CI Commands

```
python -m pytest tests/test_audit_history.py tests/test_audit_history_validation.py tests/test_session_id_path_safety.py tests/test_cycle_count_escalator.py tests/test_stall_walk.py tests/test_session_total_signature_count.py tests/test_provenance_iteration_scope.py -q
python -m pytest -q
```

The full suite is required: `audit_history.append` is called by
`gate_chain.write_gate_artifact`, so a stricter writer can redden tests far from
this change. The derived red set above was produced that way. The experiment applied the
strict `append` only, which is one of this phase's four production changes, so it
is evidence that the `append` half's red set is complete and not evidence about
the other three. Those are argued inert in D1 to D3 and confirmed by the CI
command, not by that run.

## Limitations stated

- `read` stays permissive by design, so a history file may contain rows this code
  would refuse to write. The asymmetry is deliberate and preserves the legacy
  sentinel; it is also a contract a maintainer could find surprising, which is
  why T4 and T5 pin both halves.
- The two accessors may disagree in length by design. The difference is consumed
  in exactly one place, the K-window anchor, and is guarded there.
- Three functions now hold three `ts` policies: `_walk_backward` tolerates,
  `count_session_signature_totals` ignores, `session_signature_timestamps` omits.
  Stated in D2, not reconciled.
- Corpus figures name their exclusion. The real corpus is **259 rows across 188
  session directories**; a further **1502 rows** live in the gitignored synthetic
  fixture `.qor/gates/sess-12345/`. All 259 and all 1502 validate clean, so
  `append` failing closed breaks nothing already written. An earlier draft quoted
  the combined 1761 without naming the exclusion -- the same defect recorded
  against this session's remediation cluster, repeated a day after it was written
  down.
- Iterations 1 through 4 were vetoed on: silently retiring the legacy sentinel,
  specifying a test that cannot be written, a shared iterator that changed the
  counter's answer, and a guard that made a decline inert. Each was a claim
  asserted without being tested, and each was found by a reviewer holding Read,
  Grep and Glob only.
