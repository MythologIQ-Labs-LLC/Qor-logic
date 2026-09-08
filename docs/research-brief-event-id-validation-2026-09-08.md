# Research brief: a validator that ships, is tested, and guards nothing

**Date**: 2026-09-08
**Session**: 2026-09-08T1956-274e42
**Issues**: GH #459

## The defect

`create_shadow_issue.validate_event_id` is defined at line 26, has its own regex at line 23, is covered by tests, and is **called from no production path**. Grepped repo-wide: the only occurrences of `validate_event_id` and `_EVENT_ID_RE` are the definition and its own tests.

Meanwhile the module has **four** places that build the set of event ids to act on, and none validates:

| entry point | line | source |
|---|---|---|
| `--mark-resolved` | 230 | `set(args.events.split(","))` |
| `--flip-only` | 239 | `set(args.events.split(","))` |
| issue-creation path | 250 | `set(args.events.split(","))` |
| marker file | 254 | `set(marker["event_ids"])` |

An earlier version of this brief said "two", naming only the last two and citing them at 249 and 253 -- which are `if args.events:` and `marker = load_marker()`. The count and both line numbers were wrong, and the plan restated them, so correcting one document would not have caught the other.

The issue-creation and marker paths feed `selected = [e for e in all_events if e["id"] in target_ids ...]`. An id matching no real event produces an empty selection, and the code then prints "No matching unaddressed events. Nothing to do." and **returns 0** -- a breached governance threshold reporting success.

**`--flip-only` is worse than that.** At 243-244 it unlinks the breach marker unconditionally, discarding the `flipped` count it just printed. A malformed id flips nothing, deletes the breach record, and returns 0, so the next run finds nothing to do for a legitimate reason. That is destructive rather than merely silent, it is reachable through the same unvalidated ids, and it is **not fixed by validation** -- a well-formed id matching no event does the same thing. Filed as GH #472.

## What Phase 273 fixed, and what it left

Phase 273 (GH #454) made `load_marker` reject a marker whose `event_ids` is not a list. That closed the worst *type* case -- a JSON string, where `set("evt-1")` yields a set of characters. It did not look at the elements.

Measured against the current tree:

| `event_ids` | `load_marker` | the unused `validate_event_id` |
|---|---|---|
| `"evt-1"` (a string) | rejects | would reject |
| `["evt-1", "evt-2"]` | **accepts** | would reject |
| `[12345]` | **accepts** | would reject |
| `["a" * 32]` (truncated) | **accepts** | would reject |
| `["A" * 64]` (uppercase) | **accepts** | would reject |
| `["a" * 64]` (valid) | accepts | would accept |

Four malformed shapes pass the type guard, reach the set, match nothing, and exit 0.

## Wiring it rejects no real id -- but ids are not what gets validated

Measured against the live logs at the time of writing: **151 of 151** event ids match `^[a-f0-9]{64}$`, which is structurally guaranteed by `shadow_process.compute_id` returning `sha256(...).hexdigest()`. No legitimate id would be refused.

**That measurement does not license the conclusion an earlier draft drew from it.** It stated "measured cost: zero" as though validation would run on ids. On the three `--events` paths, validation runs on **split elements**, which is a different population:

| `--events` value | `.split(",")` | elements failing `^[a-f0-9]{64}$` |
|---|---|---|
| `"<id>"` | `['<id>']` | 0 |
| `"<id>,"` | `['<id>', '']` | **1** |
| `" <id> , <id> "` | `[' <id> ', ' <id> ']` | **2** |
| `""` | `['']` | **1** |

A trailing comma is current, working behaviour -- verified: `--mark-resolved --events "<id>,"` prints "Marked 1 event(s) resolved" and exits 0. Validating split elements naively converts that into an abort. The structural guarantee about ids says nothing about the argument string an operator types.

So normalization has to precede validation, and the two are different concerns: a trailing comma is a formatting artifact of the separator, not an id the operator named.

## The validator is not itself total

`_EVENT_ID_RE.match(12345)` raises `TypeError`, not `ValueError`. The docstring says *"Raises ValueError on invalid."* So the one function whose job is to make a malformed id loud has a failure mode its own contract does not describe, and a caller catching `ValueError` -- the documented contract -- would not catch an integer.

That matters because the integer case is exactly the one a hand-edited or machine-generated marker produces.

## Why this shape recurs

This is the third instance this session of the same family: a guard that exists and is not reached (#459), a gate wired but producing no observable effect (#463), and a validator scoped to author-declared inputs (#461). In each, the artifact exists, its tests pass, and the property it names is unenforced at the point that matters.

The distinguishing feature here is that the remedy is unusually cheap: the function, its regex, and its tests already exist. Only the call is missing.

## Out of scope

- **#463** -- whether wired gates run at all. Adjacent, structural, not answered by adding a call.
- **#461** -- the stale-commitment gate's author-declared scope.
- The `--events` flag's other arguments, and the marker's remaining fields beyond `event_ids`.
