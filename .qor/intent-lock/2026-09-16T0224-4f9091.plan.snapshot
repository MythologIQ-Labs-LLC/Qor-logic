# Plan: a stale session marker is not the same as an absent one

**change_class**: hotfix

**doc_tier**: standard

**boundaries**:
- limitations: Only `qor/scripts/session.py` changes. No caller of
  `session.current()`/`session.get_or_create()` changes its call signature.
- non_goals: No change to `SESSION_TTL` itself, no TTL-refresh-on-write (GH
  #483's third "what to look at" bullet), and no change to
  `gate_chain_completeness`'s post-seal check. This phase closes the silent
  rotation at the point it happens, not the later detector.
- exclusions: No change to `rotate()` or `end_session()`; both already act on
  an explicit caller decision, not on marker age.

## Open Questions

None.

## Locked Decisions

### LD-1: "stale" and "absent" are collapsed into one boolean today

`grep -n 'def _marker_fresh' qor/scripts/session.py` -> `58:def _marker_fresh(path: Path, now: datetime) -> bool:`
`grep -n 'if _marker_fresh' qor/scripts/session.py` -> `69:    if _marker_fresh(marker, now):`
`grep -n 'if not _marker_fresh' qor/scripts/session.py` -> `82:    if not _marker_fresh(marker, now):`

`_marker_fresh` returns `False` both when the marker file does not exist and
when it exists with valid content but an mtime older than `SESSION_TTL`
(24h). `current()` returns `None` in both cases; `get_or_create()` mints and
writes a new id in both cases. GH #483 is exactly this: a marker whose
content was correct and whose gate directory held an unsealed phase's
artifacts was silently rotated (in spirit -- observed live as `current()`
returning `None`) because only its mtime had aged.

### LD-2: `_marker_fresh` is private and has exactly two call sites

`grep -rn '_marker_fresh\b' --include=*.py . | wc -l` -> `3`

All three are the definition and its two call sites shown in LD-1, and all
three are inside this module.

Both call sites are inside this module. Changing what it returns (or
replacing it) has no external caller to update.

### LD-3: the recovery condition is "does this session still have live, unsealed work"

`grep -n '^GATES_DIR = ' qor/scripts/gate_chain.py` -> `21:GATES_DIR = _workdir.gate_dir()`
`grep -n '^CHAIN = ' qor/scripts/gate_chain.py` -> `28:CHAIN = ["research", "plan", "audit", "implement", "substantiate", "validate"]`
`grep -n 'def gate_dir' qor/workdir.py` -> `35:def gate_dir() -> Path:`

A session's gate artifacts live at `<gate_dir()>/<session_id>/<phase>.json`.
A session is sealed once `substantiate.json` exists in that directory (the
seal step that also tags and closes the phase). So "this stale marker still
names live, unsealed work" is: the directory `<gate_dir()>/<sid>/` exists,
`substantiate.json` is absent from it, and at least one earlier-phase
artifact is present. That is a filesystem check with no dependency on
`gate_chain.py` or the ledger.

### LD-4: `session.py` cannot import `gate_chain.py`

`grep -n 'from qor.scripts import session' qor/scripts/gate_chain.py` -> `15:from qor.scripts import session`

`gate_chain.py` already imports `session`. Importing `gate_chain` back from
`session.py` would be a cycle, so LD-3's phase-artifact names are declared
locally in `session.py` as a small literal tuple rather than imported from
`gate_chain.CHAIN`. Four names, one place they are used; not worth a shared
module for this phase.

### LD-5: the three-state result changes behavior only for the middle state

Today: `fresh -> reuse`, `stale-or-absent -> mint new`. After: `fresh ->
reuse`, `stale-with-unsealed-work -> reuse and refresh mtime`,
`stale-without-unsealed-work -> mint new` (unchanged from today),
`absent -> mint new` (unchanged from today). `current()` mirrors this:
`fresh -> id`, `stale-with-unsealed-work -> id` (new), everything else
`-> None` (unchanged). No behavior changes for a marker that was never
written, and none for a marker that is genuinely abandoned (stale, and its
gate directory is sealed or has nothing in it).

## Phase 1: pin the behavior

### Affected Files

- `tests/test_session_marker_staleness.py` - NEW.

### Changes

None yet; tests only, against the current implementation, so each is
observably red first.

### Unit Tests

- `test_stale_valid_marker_with_unsealed_gate_dir_is_still_current` - marker
  content is a valid session_id, mtime is 25h old, `<gates>/<sid>/plan.json`
  exists and `<gates>/<sid>/substantiate.json` does not. `current()` returns
  the marker's id. Red before: returns `None`.
- `test_get_or_create_reuses_stale_valid_marker_with_unsealed_gate_dir` - same
  fixture; `get_or_create()` returns the existing id, not a freshly minted
  one. Red before: returns a new id and overwrites the marker.
- `test_get_or_create_refreshes_marker_mtime_on_reuse` - same fixture; after
  `get_or_create()`, the marker's mtime is within `SESSION_TTL` of "now" (so
  the next call in the same working session does not re-trigger recovery).
  Red before: mtime is untouched (moot before the fix, since the id changes).
- `test_stale_valid_marker_with_sealed_gate_dir_still_rotates` - marker is 25h
  old, `<gates>/<sid>/substantiate.json` exists (sealed). `get_or_create()`
  mints a new id; `current()` returns `None`. Negative control: confirms the
  fix does not resurrect a completed phase's marker.
- `test_stale_valid_marker_with_no_gate_dir_still_rotates` - marker is 25h
  old, no `<gates>/<sid>/` directory exists at all. Unchanged legacy
  behavior: mint new, `current()` returns `None`. Negative control: confirms
  the fix does not treat every stale marker as recoverable.
- `test_absent_marker_is_unaffected` - no marker file. `current()` returns
  `None`, `get_or_create()` mints a new id. Unchanged legacy behavior;
  confirms "stale" and "absent" are handled by different code paths, not
  merely differently-worded versions of the same one.
- `test_fresh_marker_is_unaffected` - marker is 1h old, valid content, no
  gate dir at all. `current()` returns the id, `get_or_create()` reuses it.
  Unchanged legacy behavior for the common case.

## Phase 2: the fix

### Affected Files

- `qor/scripts/session.py` - replace `_marker_fresh` with a three-state
  `_marker_state`; add `_has_unsealed_gate_artifacts`; update `get_or_create`
  and `current`.

### Changes

```python
_GATE_PHASE_ARTIFACTS = ("research.json", "plan.json", "audit.json", "implement.json")
_SEAL_ARTIFACT = "substantiate.json"


def _marker_state(path: Path, now: datetime) -> str:
    """"absent", "stale", or "fresh" -- LD-1: these were collapsed to one bool."""
    if not path.exists():
        return "absent"
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return "fresh" if (now - mtime) < SESSION_TTL else "stale"


def _has_unsealed_gate_artifacts(session_id: str) -> bool:
    """LD-3: this session's gate dir holds phase work and no seal yet."""
    sess_dir = _workdir.gate_dir() / session_id
    if not sess_dir.is_dir() or (sess_dir / _SEAL_ARTIFACT).exists():
        return False
    return any((sess_dir / name).exists() for name in _GATE_PHASE_ARTIFACTS)
```

`get_or_create` and `current` call `_marker_state` instead of
`_marker_fresh`. On `"stale"`, both read the marker content, validate it
against `SESSION_ID_PATTERN`, and check `_has_unsealed_gate_artifacts`; on a
hit, `get_or_create` re-writes the marker (`_atomic_write`, refreshing
mtime) and returns the existing id, and `current` returns the existing id
without writing. On a miss (invalid content, sealed, or no gate dir),
behavior is exactly today's stale/absent path: `get_or_create` mints and
writes a new id, `current` returns `None`.

### Unit Tests

Phase 1's tests go green. No new tests.

## Feature Inventory Touches

Empty. This plan touches `qor/scripts/session.py` and `tests/`.

## Definition of Done

### Deliverable: a stale-but-live session marker survives a scheduled turn

- **D1**: `session.current()` and `session.get_or_create()` return the
  existing session id (not `None`, not a new id) when the marker is stale
  but its gate directory holds unsealed phase artifacts.
- **D2**: `_marker_state` returns `"absent"` / `"stale"` / `"fresh"`
  distinctly; `_has_unsealed_gate_artifacts` checks gate-dir presence,
  absence of `substantiate.json`, and presence of at least one earlier
  artifact.
- **D3**: LD-3/LD-4 record why the check is a local filesystem check rather
  than an import from `gate_chain.py`.
- **D4**: `test_stale_valid_marker_with_unsealed_gate_dir_is_still_current`,
  `test_get_or_create_reuses_stale_valid_marker_with_unsealed_gate_dir`,
  `test_get_or_create_refreshes_marker_mtime_on_reuse`. Observed before:
  `None` / new-id / n/a; after: existing id / existing id / mtime refreshed.

### Deliverable: an abandoned or never-started session still rotates

- **D1**: A sealed session's stale marker rotates on the next call; a
  never-created marker still mints on the first call; a stale marker with no
  gate directory still rotates.
- **D2**: Unchanged legacy branches in `get_or_create`/`current` for these
  cases.
- **D3**: LD-5 records that only the middle state's behavior changes.
- **D4**: `test_stale_valid_marker_with_sealed_gate_dir_still_rotates`,
  `test_stale_valid_marker_with_no_gate_dir_still_rotates`,
  `test_absent_marker_is_unaffected`, `test_fresh_marker_is_unaffected`.

## CI Commands

- `python -m pytest tests/test_session_marker_staleness.py -q` - this
  phase's own contract.
- `python -m pytest tests/test_session_rotation.py tests/test_session_marker_path_unified.py tests/test_session_id_path_safety.py -q` - existing suites owning the changed module.
- `python -m qor.scripts.publication_boundary_lint` - no boundary finding.
- `python -m pytest -q` - full suite.
