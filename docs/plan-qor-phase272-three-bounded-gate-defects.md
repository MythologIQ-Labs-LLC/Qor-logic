# Phase 272: two bounded defects, and a gate change deferred

**change_class**: hotfix
**Issues**: GH #426, GH #433 (GH #424 deferred, see below)
**Iteration**: 2 (iteration 1 VETOed; D1 deferred, D3 inverted)
**Session**: 2026-09-08T0215-322b7e

## Scope note

Two independent defects, each reproduced by execution. They share no mechanism and are batched only because each is bounded and neither changes what any gate decides -- D2 rewrites one marker instead of all, D3 corrects two message strings. Per the standing rule, that earns one review round. A third defect was scoped in and removed: it changes what authorizes an intent-lock capture, which is not bounded, and it is deferred below.

## D1 is DEFERRED to its own phase (GH #424 stays open)

Scoped into this batch as a bounded fix; the audit established it is not one. It changes what authorizes an intent-lock capture, and its own history shows that getting the diagnostic wrong costs a live rejection. Three findings, each verified by execution:

- **The drafted predicate enumerated verdict words** as `(PASS|VETO|FAIL)`, so a report reading `Verdict: BLOCKED` alongside a quoted canonical `Verdict: PASS` yields `["PASS"]` and AUTHORIZES. The hole GH #424 reports, narrower. Third phase running in which an enumeration stood where a rule belonged.
- **The proposed factoring inverted the gate.** Returning collected verdicts instead of a bool makes `not ["VETO"]` false at `intent_lock.py:154`, so a VETO report would proceed and write the lock.
- **The refusal would have diagnosed the wrong fault.** `_verdict_hint`'s loose probe at `:84` matches a conflicting report on its quoted line, so the operator is told their canonical formatting is non-canonical. `_verdict_hint` was never in this plan's Affected files.

Its constraint set is preserved as the starting research for that phase: one module-level collector both functions reach; the new branch PREPENDED before the loose probe; `audit not PASS` retained as a substring; the loose probe kept and narrowed rather than deleted; the branch keyed on the collector being non-empty rather than on any looser probe, because `tests/test_intent_lock_anchored_pass_check.py:144-148` asserts `"canonical form" not in err` and a broad key breaks it.

## D2: advance rewrites every marker, not the current one (GH #426)

`governance_index.advance_last_reviewed` calls `_ADVANCE_RE.sub()` with no count, so every `**Last Reviewed**:` line is restamped. The docstring says "Rewrite every", so the behaviour is documented and the documentation is what is wrong.

The fix is `count=1`, and the question is WHICH one. The issue's reproduction shows the current stanza first at `:3`, with older ones below. First-match is therefore the current stanza in the observed layout, and it is also what `_LAST_REVIEWED_RE` at `:26` already treats as authoritative when `stale-tier1` reads a single date from the file.

```python
    new = _ADVANCE_RE.sub(rf"\g<1>{date_str}", text, count=1)
```

Consistency with the staleness check is the argument, not layout convention: `check` reads the FIRST marker to decide freshness, so `advance` must write the one `check` reads or the two disagree about which marker is current.

## D3: two misleading messages about a class that works correctly (GH #433)

**The issue's premise is refuted and the fix is not what it asked for.** `_compute_new` raising on `governance` is the GUARD, not a defect. Verified:

```
is_release_class('governance')  -> False
NON_RELEASE_CLASSES             -> frozenset({'governance'})
schema description              -> "the explicit non-release / version-not-applicable class" (GH #282)
sealed plans declaring it       -> phases 212, 214, 215, 240, all survived
```

A governance cycle reaches `version_applicability.validate`, is classified version-not-applicable, and the bump step skips; `_compute_new` is reached only for release classes. The ledger records one such phase explicitly as "version-not-applicable; no version bump or tag". So the plan's original premise -- that such a plan dies after the ledger entry exists -- is false on the live route, and the reporter's caller is reaching semver arithmetic without passing through `is_release_class`.

Mapping `governance` to a patch bump was drafted and is rejected: it would put two contradicting definitions of the class inside the module the version gate delegates to, and `_compute_new` has three callers (`governance_helpers:111`, `version_applicability:61`, `version_backends:59`), so it would arm a bump across all three version manifests.

What ships is the two message defects the investigation actually found:

1. `governance_helpers.parse_change_class` at `:74-76` tells the operator the canonical form is `<hotfix|feature|breaking>` while `_CHANGE_CLASS_RE` at `:19-22` accepts four. A plan declaring `governance` that trips the bold-format check is told the class does not exist.
2. `_compute_new` raises `unknown change_class` for a value the schema declares valid. It becomes a named refusal saying the class is non-release and must not reach a bump -- which is what a caller that arrived here wrongly needs to hear. Behaviour is unchanged: it still raises.

## Tests

| Test | Pins | Red before |
|---|---|---|
| `test_advance_rewrites_only_the_first_marker` | GH #426 | yes |
| `test_advance_leaves_older_stanza_dates_intact` | the narrative pairing the issue is about | yes |
| `test_advance_writes_the_marker_check_reads` | advance and check agree on which is current | no |
| `test_parse_change_class_error_names_every_accepted_class` | the message matches the regex that rejects | yes |
| `test_compute_new_names_governance_as_non_release` | the refusal says why, not "unknown" | yes |
| `test_every_declared_class_is_classified_and_computes_iff_release` | the partition, not the instance: every enum value is in exactly one of the two sets, and computes a version iff release | no |

An enum-iterating row was drafted and dropped: asserting every change_class can compute a version pins exactly the proposition GH #282 rejected, and would make correct behaviour a failure for whoever adds a second non-release class.

## Affected files

- `qor/scripts/governance_index.py` (D2)
- `qor/scripts/governance_helpers.py` (D3)
- `tests/test_governance_index_enforcement.py` (advance coverage at `:65-72`), `tests/test_dry_run_modes.py` (`:148-154`), `tests/test_governance_helpers.py`, `tests/test_version_applicability.py`

## Reach

- **D2** is called at `governance_index.py:164` from the substantiate path with the seal date. Changing it to one marker changes what this repository's own index records at the next seal, which is the intended effect.
- **D3 touches messages only.** `_compute_new` has three callers (`governance_helpers:111`, `version_applicability:61`, `version_backends:59`) and its behaviour is unchanged at all three: it still raises for non-release classes. `parse_change_class` has its own callers and its return value is unchanged.

## CI Commands

```
python -m pytest tests/test_governance_index_enforcement.py tests/test_governance_helpers.py tests/test_dry_run_modes.py tests/test_version_applicability.py -q
python -m qor.reliability.intent_lock verify --session 2026-09-08T0215-322b7e
python -m qor.scripts.governance_health --profile skill-entry
python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md
python -m qor.scripts.seal_artifacts --check --skip-tests --repo-root .
python -m qor.scripts.publication_boundary_lint
python -m qor.scripts.gate_provenance verify-committed
python -m pytest -q
```

## Limitations

- D2 assumes the current stanza is first. The issue's reproduction shows that layout and `check` already reads the first marker, so advance and check agree either way; a consumer whose index puts the current stanza last would advance the wrong one, and nothing in the artifact declares which position is current.
- **A residual GH #433 exposes and this phase does not fix.** `version_applicability.is_release_class` is membership in `RELEASE_CLASSES`, so any value it does not recognise returns False and is silently treated as version-not-applicable: a fifth schema class added without being classified would ship with no version and no tag, and nothing today would notice. Making it raise is a behaviour change and would break this batch's scope line that nothing here changes what a gate decides. The new partition test goes red the moment such a class is added, which is the containment this phase can afford.
- D3 changes no behaviour. GH #433 asked for a version mapping and does not get one; it closes with the corrected analysis and the two message fixes, which is less than it requested and is stated as such on the issue.
