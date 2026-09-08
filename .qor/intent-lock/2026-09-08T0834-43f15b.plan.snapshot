# Phase 273: a loader that crashes three ways, and a contract nothing tests

**change_class**: hotfix
**Issues**: GH #454, GH #444
**Iteration**: 2 (iteration 1 VETOed)
**Session**: 2026-09-08T0834-43f15b

## Scope note

Two bounded defects. D1 changes one function's failure handling; D2 adds tests to an existing contract and changes no behaviour at all. Neither alters what any gate decides, so this earns one review round under the standing depth rule.

## D1: `create_shadow_issue.load_marker` handles absent and nothing else (GH #454)

`qor/scripts/create_shadow_issue.py:53-56` guards `exists()` and then calls `json.loads` unguarded. Measured, three distinct failures rather than the one filed:

| marker state | today |
|---|---|
| truncated write | `JSONDecodeError`, unhandled traceback |
| **non-dict JSON** (`[]`) | **returns a list, no error** |
| UTF-16 bytes | `UnicodeDecodeError`, unhandled traceback |

The non-dict case is the one worth naming: it returns cleanly and fails later at the first subscript, away from the cause. That is the shape GH #429 closed elsewhere in this repository.

**The fix is not the one GH #429 got, and the difference is the point.** `qor_platform.current` was made total because its callers sit in gate-writing paths with a correct degraded answer. This loader has neither property: its absent case already exits (`raise SystemExit`), so there is no established "keep going" value, and its caller creates a shadow issue rather than writing a gate artifact. Returning `None` here would push the failure one frame further from its cause, which is the defect rather than the cure.

So it exits, and says which of the three happened:

```python
def load_marker() -> dict:
    if not MARKER_PATH.exists():
        raise SystemExit(f"No marker at {MARKER_PATH}. Run check_shadow_threshold.py first.")
    try:
        raw = MARKER_PATH.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise SystemExit(f"Marker at {MARKER_PATH} is not UTF-8 ({exc}); remove it and re-run "
                         "check_shadow_threshold.py.")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Marker at {MARKER_PATH} is not readable JSON ({exc}); remove it and "
                         "re-run check_shadow_threshold.py.")
    if not isinstance(data, dict):
        raise SystemExit(f"Marker at {MARKER_PATH} parsed as {type(data).__name__}, expected an "
                         "object; remove it and re-run check_shadow_threshold.py.")
    missing = [k for k in ("event_ids", "threshold", "breach_ts") if k not in data]
    if missing:
        raise SystemExit(f"Marker at {MARKER_PATH} is missing {', '.join(missing)}; remove it and "
                         "re-run check_shadow_threshold.py.")
    if not isinstance(data["event_ids"], list):
        raise SystemExit(f"Marker at {MARKER_PATH} has event_ids as "
                         f"{type(data['event_ids']).__name__}, expected a list; remove it and "
                         "re-run check_shadow_threshold.py.")
    return data
```

**Why the typing is asymmetric.** `event_ids` gets an `isinstance` check; `threshold` and `breach_ts` get presence only. That is by consequence, not oversight: a wrong-typed `event_ids` silently DECOMPOSES into a character set and produces a wrong governance verdict, while a wrong-typed `threshold` or `breach_ts` interpolates into an issue body and produces a visibly odd line that no one acts on. The three fields checked are the ones this reader dereferences -- `event_ids` at `:206`, `threshold` and `breach_ts` via `build_body` at `:65-67` -- and not the writer's full payload, so the guard cannot drift as that payload grows. Checking `severity_sum`, `event_count` or `next_action` would be owning a schema this function does not own.

**The shape check is not optional, and iteration 1 missed the worst mode by omitting it.** `main` does `set(marker["event_ids"])` at `:206`. A dict marker whose `event_ids` is a JSON string passes an `isinstance(data, dict)` guard, yields a set of CHARACTERS, matches no event, and `main` prints "No matching unaddressed events. Nothing to do." and returns **0**. Measured: `set("evt-1")` is `{'v','e','t','1','-'}`.

**A breached threshold reports success.** That is a silent wrong answer, strictly worse than the three tracebacks iteration 1 enumerated, and it is the plan's own stated rule -- name the case that returns cleanly and fails later -- applied to a case the plan did not name. Missing keys are the same shape one frame later: `marker['threshold']` and `marker['breach_ts']` raise a bare `KeyError` from `build_body`.

Enumerated rather than a broad catch, deliberately, and this is the opposite call from the two phases before it. Those wrapped calls into external state whose contract was TOTALITY, where a list cannot be right because it predicts an open set. This function's contract is the opposite: it must distinguish the outcomes in the table above and tell the operator which, and no broad catch can distinguish anything. The unenumerated remainder -- a permissions error, a disappearing file -- propagates, which is correct for an environment fault in a script the operator runs directly.

Every message names the same remedy, because it is the same one: the marker is a cache that `check_shadow_threshold` regenerates.

## D2: the no-raw-diagnostics contract is pinned one layer below the surfaces it names (GH #444)

Phase 182 removed raw `FAIL` / `TAINTED` tokens from governance-health output because they contradicted an OK verdict when they reached the CLI, the JSON payload, and the nightly summary. The decision is recorded in the docstring at `governance_health.py:128-132`.

The only assertion guarding it calls `_classify_one`, which RETURNS the reason. The reason reaches an operator at `governance_health.py:319`, where findings are printed, and at `:311`, where they are embedded in the JSON payload that `status_json` truncates into a summary and the nightly workflow posts into an issue body.

`tests/test_cli_governance_health.py` runs the module as a real subprocess and asserts only `returncode` at `:37` and `:45`; `stdout` appears solely inside the assertion messages. So the contract holds by construction rather than by test, at all three surfaces it names.

**Every `FAIL` and `TAINTED` message goes to stderr**, not stdout: `ledger_hash` returns `to_stderr=True` for all three error classes and the unresolved-markup failures pass `file=sys.stderr` directly. The Phase 182 docstring says the verifier calls "suppress stderr too". So an assertion on `stdout` alone cannot observe the bleed this phase exists to pin, and every D2 row asserts over `stdout + stderr`, as the existing in-process test at `test_governance_health_post_anchor_tolerance.py:143` already does.

**This phase adds no behaviour.** Three assertions, one per surface.

**The fixture matters more than the assertions, and iteration 1 named one that cannot fail.** `test_cli_exit_two_for_damaged_workspace` writes `%%% not a ledger %%%`, which `_ledger_damage` rejects at `governance_health.py:133-136` before either verifier call. Measured: it returns `('malformed ledger: no recognizable header or entries', None)`. The only code that can print `FAIL` or `TAINTED` is never reached, so deleting both `redirect` blocks would leave that fixture's output byte-identical -- a test that stays green when the guarded mechanism is removed.

D2 therefore uses an entry-bearing ledger the verifier actually rejects. The stronger of the two available shapes is the TOLERATED one at `tests/test_governance_health_post_anchor_tolerance.py:55-76`, because a raw bleed there contradicts an `OK` verdict, which is precisely the contradiction GH #268 names, rather than merely accompanying a `DAMAGED` one.

## Tests

| Test | Pins | Red before |
|---|---|---|
| `test_load_marker_exits_on_a_truncated_marker` | GH #454, the filed shape | yes |
| `test_load_marker_exits_on_non_utf8_bytes` | the Windows hand-edit shape | yes |
| `test_load_marker_exits_on_non_dict_json` | the shape that returns cleanly today | yes |
| `test_load_marker_message_names_the_regeneration_command` | the remedy reaches the operator | yes |
| `test_load_marker_exits_on_event_ids_as_a_string` | the silent-success mode: a breached threshold returned 0 | yes |
| `test_load_marker_exits_on_a_missing_required_key` | the deferred KeyError from build_body | yes |
| `test_load_marker_still_returns_a_valid_marker` | the fix does not break the good path | no |
| `test_load_marker_still_exits_when_absent` | the existing guard is preserved | no |
| `test_cli_output_carries_no_raw_fail_token` | GH #444, surface 1, over BOTH streams | no |
| `test_cli_output_carries_no_tainted_token` | surface 1, over both streams | no |
| `test_deleting_the_redirect_makes_the_fixture_bleed` | the fixture can fail; not vacuous. Shadows the MODULE-LOCAL `contextlib` name rather than patching the real module, which would affect every other consumer for the duration. Runs on the same fixture as the two rows it licenses | no |
| `test_status_json_summary_carries_no_raw_tokens` | surface 2, what the nightly posts | no |

Every D2 row is marked "no": the contract holds today and these pin it so a later change cannot re-open it silently. That is the entire point of the issue, and marking them red-before would be false.

## Affected files

- `qor/scripts/create_shadow_issue.py` (D1)
- `tests/test_shadow.py` (D1 coverage; it already monkeypatches this module's `MARKER_PATH`)
- `tests/test_cli_governance_health.py` (D2)
- `tests/conftest.py` (the entry/ledger builder D2 needs, moved from `test_governance_health_post_anchor_tolerance.py:20-48` rather than copied a third time)

## Round-trip with the writer

`check_shadow_threshold.write_marker` is the only producer, and the guards must not reject what it writes. Read before designing them, its payload is:

```
breach_ts, threshold, severity_sum, event_count, event_ids (a list), next_action
```

All three required keys are present and `event_ids` is a list, so every guard admits what this repository produces. Stated as a measurement rather than an assumption: if the writer emitted a shape these guards reject, the guards would be wrong and not the writer.

## Reach

- `load_marker` has one caller inside its own module and is not imported elsewhere; the failure mode changes from traceback to a named exit, and the good path is byte-identical.
- D2 touches no production file. If a D2 assertion fails on first run, the contract is already broken and that is a finding rather than a test defect -- stated so the result is interpreted correctly either way.
- `status_json` is asserted through its own output rather than by re-deriving what it truncates, so the test pins the surface an operator actually reads.

## CI Commands

```
python -m pytest tests/test_shadow.py tests/test_cli_governance_health.py tests/test_governance_health_post_anchor_tolerance.py -q
python -m qor.scripts.governance_health --profile skill-entry
python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md
python -m qor.reliability.seal_entry_check --ledger docs/META_LEDGER.md --auto
python -m qor.scripts.seal_artifacts --check --skip-tests --repo-root .
python -m qor.scripts.publication_boundary_lint
python -m qor.scripts.gate_provenance verify-committed
python -m pytest -q
```

## Limitations

- D1 exits rather than degrading. An operator whose marker is corrupt must delete it and re-run the threshold check; there is no automatic recovery, and that is deliberate for a cache whose regenerator is one command away.
- D1 enumerates six failure kinds: three parse faults and three shape faults. A fourth would propagate as a traceback rather than a named exit. That is the correct direction here -- an environment fault is not a corrupt cache -- but it is the opposite call from the two phases before this one, and the reason is stated in the design rather than left to be inferred.
- D2 pins three surfaces named by GH #268. The nightly workflow posts the JSON summary into an issue body; that posting step is not exercised, so the assertion is on what the workflow reads rather than on what it writes.
