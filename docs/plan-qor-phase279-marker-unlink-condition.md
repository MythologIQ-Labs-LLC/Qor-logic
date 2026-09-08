# Phase 279: the marker's writer owns its removal

**change_class**: hotfix
**Issues**: GH #472
**Research**: docs/research-brief-marker-unlink-condition-2026-09-08.md
**Iteration**: 4 (three prior VETOs; the authoritative count is `audit-iterN.json` plus `audit_history.jsonl`, which this line only restates)
**Session**: 2026-09-08T2149-c86342

## Scope note

`create_shadow_issue --flip-only` deletes the breach marker unconditionally, discarding the `flipped` count it just printed. A well-formed id matching no event flips nothing, destroys the breach record, and returns 0 -- so the next run finds nothing to do for a legitimate reason, indistinguishable from a clean state.

One deletion is removed. No new condition is added, because the command has no inputs from which a correct condition could be computed.

## D1: `--flip-only` stops removing the marker

```python
flipped = flip_events_only(log, target_ids, args.flip_only)
print(f"Flipped {flipped} event(s) in {log}")
if MARKER_PATH.exists():        # <- removed
    MARKER_PATH.unlink()        # <- removed
return 0
```

The marker asserts that the unaddressed severity sum exceeds the threshold. Deleting it claims the breach is over. `--flip-only` cannot support that claim, on three measured grounds:

- **It never reads the marker.** The collector that invokes it contains zero references to `MARKER_PATH` or `remediate-pending`. (It does contain the word "marker" twice, at `:43` and `:78`, in an unrelated check for a `qor/` or `docs/` directory marker -- an earlier draft's "zero references to the marker" was imprecise.)
- **Its ids are unrelated to the marker's.** They come from `by_repo[e["source_repo"]]`, gathered across repositories, then applied one repo at a time with `cwd` set to that repo. The marker there was written from that repo's own severity sum, which the collector never consulted.
- **Its sibling already declines to do this.** The issue-creation path removes the marker only `if MARKER_PATH.exists() and not args.events`. `--flip-only` *requires* `--events`, so under the guard its own module already applies, it should never remove the marker.

## D2: why not "unlink when `flipped > 0`"

That is the obvious remedy and it is wrong for the same reason the current line is. Flipping 1 of 10 breach events leaves the breach standing, so `flipped > 0` still deletes a marker whose claim remains true.

`flipped` counts events. The marker's claim is about a **severity sum against a threshold**. Any condition computed from `flipped` alone is a proxy for a comparison this command has no inputs for -- it would be a different wrong answer, arrived at more confidently.

**The superset condition fails for the same reason, one level subtler.** Conditioning removal on the flipped ids covering `marker["event_ids"]` -- which would require reading the marker, a choice rather than an impossibility -- still deletes a live breach: marker `{a,b}` sev 10; event `c` sev 12 is appended afterwards, unaddressed and *not in* `event_ids`; the collector flips `{a,b}`; the superset holds; the marker is removed while the true sum is 12 against a threshold of 10. Every condition available to this command is a proxy for a comparison it lacks the inputs to make.

Recomputing the sum here was considered and rejected: it would make `create_shadow_issue` a second owner of the breach predicate that `check_shadow_threshold` already owns, which is the two-owners-of-one-property defect this repository has spent four phases closing (#282, #275, #467, #469).

## D3: the cost, stated

Removal returns entirely to the writer, which is skill-invoked rather than scheduled, so a marker whose breach has cleared can persist until the next **`qor-process-review-cycle`** or **`qor-shadow-process`** run -- the two skills that actually invoke it (`SKILL.md:75` and `SKILL.md:112`).

An earlier draft listed `qor-remediate` as a third corrector. It is not: its only reference to the writer is descriptive prose about auto-escalation at `SKILL.md:73`, and its executable steps import `remediate_read_context` and `remediate_mark_addressed` instead. The list erred in the direction that flattered this change by implying faster correction than exists.

Measuring that also cuts the other way, and the plan takes the correction rather than only the credit: `remediate_mark_addressed.py` has **zero** marker references, so `/qor-remediate` flips events to addressed and never touches the marker. That makes **three pre-existing staleness entrances** -- the guarded `:361` (the issue path leaves the marker when `--events` is given), the `--mark-resolved` workflow, and `/qor-remediate` -- and this phase's is the **fourth of four**. And because `/qor-remediate` never invokes `create_shadow_issue` either, it cannot produce the row-1 false-header issue; that requires the bare invocation documented at `qor-shadow-process/SKILL.md:119`, or a human. **Row 1's cost is narrower than an asymmetry argument alone would suggest.**

**There are two downstream branches and an earlier draft traced only one -- the branch the collector does not produce.**

**All the marker's events addressed.** The default path loads the marker, finds nothing unaddressed, prints "No matching unaddressed events. Nothing to do." and exits 0. Wasteful, not wrong.

**Partial flip -- what the collector actually produces**, since it flips only the ids it pooled at sweep time, a subset of the marker's whenever an event landed between the two runs or lives in the upstream log. Two sub-cases, and they cut opposite ways:

| marker | flipped | residual sum | today | after this phase |
|---|---|---|---|---|
| `{a,b}` sum 10, threshold 10 | `a` | 5 -- below | record destroyed; next default run exits 1 on a missing marker and routes the operator to the owner, which recomputes 5 < 10. Correct **by accident** | marker survives; an issue is filed naming `b`, titled "threshold breach" over "Severity sum: **5** (threshold 10)" -- **a header contradicting its own numbers** |
| `{a,b,c}` sum 15, threshold 10 | `a` | 10 -- still breaching | record destroyed, **the live breach becomes invisible** | marker survives; a **true** breach issue is filed naming `b` and `c` |

The second row is the case that justifies this phase, and an earlier draft argued the phase entirely from an asymmetry principle without once naming the branch where the new behaviour is affirmatively right.

The first row is a real cost and is accepted, not waved past: it is recorded in Limitations and filed as **GH #474**. That contradiction is not caused here -- it is reachable on `main` today through `:329`, which synthesises `{"threshold": 10}` for any explicit `--events` run, and through the `--mark-resolved` subset workflow documented at `qor-process-review-cycle/SKILL.md:86`. There are likewise **three** pre-existing routes to that header -- `:329`'s synthesised marker, `--mark-resolved`-then-default, and `/qor-remediate`-then-default, since a subset selection is all it takes -- and this phase's is the **fourth**. An earlier draft said "third entrance to a room with two doors", having integrated the `/qor-remediate` finding into the staleness list and not this one. The undercount ran against this phase's interest rather than for it. Correcting the header only for the stale-marker route while leaving the other three emitting the identical contradiction would be the half-measure shape.

The asymmetry still settles the core decision. **A marker persisting after the breach clears is noise; a marker deleted while the breach is real destroys the record of it**, and the second row above is exactly that.

## D4: Phase 278's placement test loses its witness, and the witness is restored

`tests/test_shadow.py:604` (`test_flip_only_with_a_malformed_id_leaves_the_marker_intact`) pins that Phase 278's validation guard runs **before** the unlink, by asserting the marker survives a malformed id. Removing the unlink makes that assertion hold no matter where the guard sits: a malformed id flips nothing either way, so `rc == 2` plus an unchanged log cannot distinguish the orderings. **The test keeps passing and stops testing anything** -- the presence-only shape, arriving through a change made two phases later rather than through the test being written badly.

The witness is restored on an observable that survives the deletion: `flip_events_only` is monkeypatched with a sentinel that raises, so *reaching* it fails the test. Placement is then pinned by whether the guard short-circuits before the flip, which stays true whatever happens to the marker.

Two corrections to that test come with this phase rather than after it:

- Its docstring ends *"a well-formed id matching no event still deletes the marker (GH #472)"*. This phase makes that false, in the test file it edits.
- It cites the unlink at `:243-244`; the actual location is `:316-317`, so the citation is **already stale on main** and this phase edits that exact region.

## D5: what this does NOT do

- **Does not touch the issue-creation path's unlink.** It is guarded by `and not args.events`, removes the marker only when it ran off that marker, and is pinned by `tests/test_shadow.py:250`. Correct as it stands.
- **Does not add a breach recomputation** anywhere (D2).
- **Does not change `check_shadow_threshold`.** Its two removal sites already implement the marker's contract.
- **Does not schedule the writer.** Whether it should run on a timer rather than by skill invocation is a real question and is not this phase's.

## Tests

Written first. Each runs twice for determinism. The red-before column is per row: the edited Phase 278 row is green before and after by construction, for the reason stated below the table.

| Test | Pins | Red before |
|---|---|---|
| `test_flip_only_with_no_matching_events_leaves_the_marker` | **the reported defect**: well-formed id, 0 flipped, marker survives, `rc == 0` | yes |
| `test_flip_only_with_matching_events_also_leaves_the_marker` | D1; removal is unconditional in the other direction too -- the command never deletes it | yes |
| `test_flip_only_still_flips_and_still_returns_zero` | no regression in what the command is *for* | no |
| `test_issue_path_still_removes_the_marker_when_run_off_it` | D5; the guarded sibling is untouched | no |
| `test_issue_path_still_leaves_the_marker_when_events_given` | the sibling's existing guard still holds | no |
| `test_flip_only_with_a_malformed_id_leaves_the_marker_intact` (**edited**) | **D4**; Phase 278's placement test, re-pinned on a raising `flip_events_only` sentinel because the marker assertion becomes vacuous. Docstring and the stale `:243-244` citation corrected in the same edit | **no** -- green before and after |

The second row matters as much as the first: after this change `--flip-only` never removes the marker, so a test that only covers the zero-flip case would leave the behaviour half-specified and invite someone to reintroduce a `flipped > 0` condition.

**The edited row is green before and after, and that is classified rather than left in the column.** Phase 278 already placed the guard correctly, so nothing about placement can be red today: on `main` a malformed id returns 2 at `:313` before `flip_events_only` at `:314`, so the sentinel is never reached and the marker survives because the unlink is never reached either. Every assertion passes now. Its job is not to catch a present defect but to replace a witness this change makes vacuous and to pin placement against a *future* move. An earlier draft marked it red-before, which would have left the implementer either mis-reporting a red observation in the substantiate record or improvising mid-implementation.

**Two constraints on the sentinel, or the remedy hollows out the same way it is fixing:**

- `monkeypatch.setattr` must use **`raising=True`** (the default). `tests/test_shadow.py` uses `raising=False` in 11 places including inside this very test, so the wrong idiom is adjacent and copyable -- and with it, renaming or inlining `flip_events_only` creates a dead attribute, the sentinel never fires, and the test hollows out again by exactly the mechanism D4 describes.
- The sentinel raises via **`pytest.fail(...)`**, an `OutcomeException` deriving from `BaseException`, so it survives any future broad `except Exception` at the call site. There is no `try` there today; relying on that absence is a weaker guarantee than not needing it.

## Affected files

- `qor/scripts/create_shadow_issue.py` (the `--flip-only` branch; two lines removed, plus a comment recording why)
- `tests/test_shadow.py` -- **additions and one edit**. Additions for the new rows; the edit re-pins Phase 278's `test_flip_only_with_a_malformed_id_leaves_the_marker_intact` at `:604` (D4), correcting its docstring and its stale `:243-244` citation. Existing marker assertions at `:118`, `:137`, `:250` are untouched.
- `CHANGELOG.md`

## Reach

- `--flip-only` no longer removes the marker. Its only caller is `collect_shadow_genomes.py:191-210`, which branches on the return code and parses a count from stdout; it never inspects the marker, so nothing it does changes.
- No skill invokes `--flip-only`; its `--help` names the cross-repo collector as its consumer.
- A marker may now persist until the next writer run (D3).
- No skill or template changes, so the dist tree is untouched.
- `hotfix`: no new capability, no new flag, no signature change -- a destructive action removed.

## CI Commands

```
python -m pytest tests/test_shadow.py tests/test_collect.py -q
python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md
python -m qor.reliability.seal_entry_check --ledger docs/META_LEDGER.md --auto
python -m qor.scripts.governance_health --profile skill-entry
python -m qor.scripts.seal_artifacts --check --skip-tests --repo-root .
python -m qor.scripts.publication_boundary_lint
python -m pytest -q
```

## Limitations

- A stale marker can outlive its breach until the writer next runs. That is the accepted side of the asymmetry in D3, not an oversight.
- **A partial flip whose residual falls below the threshold now files an issue whose header contradicts its own numbers** -- "Process threshold breach" over a severity sum below the threshold. Accepted cost, filed as **GH #474**, which also records that `:329` is a second owner of the threshold constant `check_shadow_threshold.py:31` declares. Not fixed here because the defect belongs to `build_body`'s inputs and is already reachable by three routes this phase does not touch.
- The marker remains derived state with no expiry of its own; nothing detects one that has outlived its breach except the writer recomputing.
- This removes a wrong deletion. It does not establish that the remaining deletion sites are right beyond the one it examined.
- `--flip-only` remains able to flip events in a repository whose marker it cannot see, which is its purpose; this phase only stops it acting on that marker.
