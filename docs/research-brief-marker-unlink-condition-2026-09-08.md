# Research brief: a command deletes a record it never reads

**Date**: 2026-09-08
**Session**: 2026-09-08T2149-c86342
**Issues**: GH #472

## The defect

`create_shadow_issue --flip-only` removes the breach marker unconditionally:

```python
flipped = flip_events_only(log, target_ids, args.flip_only)
print(f"Flipped {flipped} event(s) in {log}")
if MARKER_PATH.exists():
    MARKER_PATH.unlink()
return 0
```

`flipped` is printed and discarded. The marker is deleted whether it is 0 or 50, and the command returns 0.

Phase 278 narrowed the trigger by validating ids, so a malformed id now aborts before reaching this line. It did not remove it: a **well-formed** id matching no event still flips nothing, still deletes the marker, and still reports success.

## What the marker means

`check_shadow_threshold` owns it. It writes the marker when the unaddressed severity sum breaches the threshold, and calls `remove_marker()` in exactly two places: when there are no events at all, and when the sum has fallen below the threshold.

So the marker asserts one thing: **the unaddressed severity sum currently exceeds the threshold.** It is derived state, recomputable from the log at any time.

Deleting it is a claim that the breach is over.

## `--flip-only` is not entitled to make that claim

Three measurements, and the third is decisive:

1. **It never reads the marker.** `collect_shadow_genomes.py` contains **zero** references to the marker path or its name.
2. **Its ids have no relationship to the marker's.** The collector builds them with `by_repo[e["source_repo"]].append(e["id"])` from events it gathered across repositories, then invokes `--flip-only` once per repo with `cwd` set to that repo. The marker in that repo was written from that repo's own severity sum, which the collector never consulted.
3. **Its own sibling declines to do this.** The issue-creation path at the other unlink site is guarded:

   ```python
   if MARKER_PATH.exists() and not args.events:
   ```

   It removes the marker only when it ran *off* the marker. When the operator names ids explicitly, it deliberately leaves the marker alone. And `--flip-only` **requires** `--events` -- so under its sibling's own rule it should never remove the marker, and it always does.

The two sites disagree about the same file, and the guarded one has the better argument.

## Why "unlink when flipped > 0" is not the fix

The obvious remedy is wrong for the same reason the current code is. Flipping 1 of 10 breach events leaves the breach standing, so a `flipped > 0` condition still deletes a marker whose claim is still true. The count of events flipped is not evidence about the severity sum.

Any condition computed from `flipped` alone is a proxy for a threshold comparison this command has no inputs for.

## What nothing depends on

- **No test pins it.** `tests/test_shadow.py:250` asserts the marker is removed, but that is the issue-creation path running off the marker -- the guarded site, which is correct and stays. Nothing asserts removal after `--flip-only`.
- **No skill invokes `--flip-only`.** Its only caller is the cross-repo collector, and its `--help` says so.
- The collector branches on the return code and parses a count from stdout; it never inspects the marker.

## The cost of leaving the marker

Removal returns to the writer, which is skill-invoked rather than scheduled (`qor-process-review-cycle`, `qor-shadow-process`, `qor-remediate`), so a marker whose breach has cleared can persist until the next such run.

Consequence, measured against the code path: `create_shadow_issue`'s default path would load that marker, find its events already addressed, print "No matching unaddressed events. Nothing to do." and exit 0. Wasteful, not wrong.

The asymmetry is what settles it. **A marker persisting after the breach clears is noise. A marker deleted while the breach is real destroys the record of it**, and the next run then finds nothing to do for a legitimate reason -- indistinguishable from a clean state.

## Out of scope

- Whether `check_shadow_threshold` should be scheduled rather than skill-invoked.
- The issue-creation path's unlink, which is guarded and correct.
- GH #459's family (#461, #463) -- guards that exist and are not reached.
