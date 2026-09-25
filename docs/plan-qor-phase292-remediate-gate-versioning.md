# Plan: a second remediation proposal stops destroying the first

**change_class**: hotfix

**doc_tier**: standard

**boundaries**:
- limitations: This versions `remediate_emit_gate`'s output the way the other
  gate phases already are versioned. It does not add recovery for a proposal
  already destroyed by the pre-fix code, and it does not change what
  `remediate_mark_addressed` or `/qor-audit` do with the artifact once written.
- non_goals: No change to the remediate schema, to `remediate_read_context`,
  `remediate_pattern_match`, `remediate_propose`, or `remediate_mark_addressed`.
  No attempt to route `emit` through `gate_chain.write_gate_artifact`'s
  schema-validated path -- that path requires `events_addressed` /
  `proposed_changes`, fields the live caller (`remediate_propose.propose`)
  does not emit; reconciling that mismatch is a different, larger change than
  GH #446 asks for and is out of scope here.
- exclusions: No change to any already-written `.qor/gates/**/remediate.json`
  on disk. No retroactive recovery of a proposal a pre-fix session already
  overwrote -- GH #446's own observed instance is unrecoverable by
  construction (`.qor/gates/` is untracked) and stays that way.

## Open Questions

None.

## Locked Decisions

### LD-1: the defect is exactly what GH #446 describes, and it is live

Pre-fix state, cited at this phase's fork point (`f3e069b`), since this
plan's own Affected Files change the same line:

> `git show f3e069b:qor/scripts/remediate_emit_gate.py | grep -n 'out_path = out_dir'` -> `42:    out_path = out_dir / "remediate.json"`

Every other gate phase writes through `validate_gate_artifact.write_artifact`,
which composes an immutable `<phase>-iter<N>.json` before refreshing the
`<phase>.json` singleton (unchanged by this plan; cited at `HEAD`):

> `git show HEAD:qor/scripts/validate_gate_artifact.py | grep -n 'versioned = next_iteration_path'` -> `199:    versioned = next_iteration_path(phase, session_dir)`
> `git show HEAD:qor/scripts/validate_gate_artifact.py | grep -n '_atomic_write(session_dir'` -> `206:    _atomic_write(session_dir / f"{phase}.json", text)`

`remediate_emit_gate.emit` is the one gate writer that instead targets a fixed
filename with no iteration suffix. A second proposal in the same session --
the expected shape of the documented revise-and-re-emit remediation contract
-- overwrites the first unconditionally, including one a tribunal has already
audited and bound by content hash in `docs/META_LEDGER.md`. GH #446 records a
live instance of exactly this loss.

### LD-2: reuse `next_iteration_path`; do not duplicate its numbering

`validate_gate_artifact.next_iteration_path(phase, session_dir)` already
derives the next free `<phase>-iterN>.json` path from the highest existing
iteration in the directory, unchanged by this plan:

> `git show HEAD:qor/scripts/validate_gate_artifact.py | grep -n 'def next_iteration_path'` -> `169:def next_iteration_path(phase: str, session_dir: Path) -> Path:`

It is phase-parameterized and already imported nowhere outside
`validate_gate_artifact.py` itself, so calling it with `"remediate"` costs one
import and duplicates no numbering logic. The alternative -- writing a second,
independent iteration counter local to `remediate_emit_gate.py` -- would let
the two counters drift if a future phase renames or merges the schema list;
importing the existing one cannot drift from itself.

### LD-3: the singleton path and `emit`'s return value stay a fixed name

`remediate_mark_addressed.mark_addressed` takes a `remediate_gate_path`
argument that callers (and this repo's own tests,
`test_mark_addressed_requires_review_pass_artifact` and its four siblings in
`tests/test_remediate.py`) pass as the literal
`.qor/gates/<session_id>/remediate.json` path, not a versioned one:

> `git show HEAD:tests/test_remediate.py | grep -n 'remediate_gate = tmp_path / ".qor" / "gates" / "s-req-rp"'` -> `439:    remediate_gate = tmp_path / ".qor" / "gates" / "s-req-rp" / "remediate.json"`

Unlike `gate_chain.write_gate_artifact` (Phase 173, GH #237), which changed its
return value to the versioned path because its own callers read the return
value, `emit`'s callers and this repo's own downstream consumer read the fixed
singleton name. Changing what `emit` returns would silently break that
contract for no benefit GH #446 asks for. `emit` therefore keeps writing (and
returning) the singleton, now refreshed from the same immutable text as the
newly written versioned copy rather than being the only copy.

## Phase 1: version `remediate_emit_gate.emit`'s output

### Affected Files

- `qor/scripts/remediate_emit_gate.py`
- `tests/test_remediate.py`

### Changes

- Import `next_iteration_path` from `validate_gate_artifact`.
- Add a local `_atomic_write` helper (tempfile + `os.replace`, matching the
  pattern already used in this file and in `validate_gate_artifact.py`).
- `emit` computes the payload text once, writes it to
  `next_iteration_path("remediate", out_dir)` first, then writes the same text
  to the `remediate.json` singleton. Return value unchanged (LD-3).

### Unit Tests

- `test_emit_gate_second_proposal_does_not_destroy_first` -- two proposals
  emitted in the same session; both proposal texts are recoverable from the
  session directory's versioned artifacts afterward. Red against the pre-fix
  code (only the second proposal's text exists anywhere); green after.
- `test_emit_gate_versioned_paths_never_reused` -- three emissions in one
  session produce `remediate-iter1.json`, `remediate-iter2.json`,
  `remediate-iter3.json`, none re-targeted.
- `test_emit_gate_singleton_still_written_as_latest_copy` -- the unversioned
  `remediate.json` singleton still exists after multiple emissions and holds
  the latest proposal, preserving `remediate_mark_addressed`'s existing
  fixed-path contract (LD-3). Passes unmodified against the pre-fix code too,
  since that was never in question -- included as a regression pin against a
  future change accidentally moving the singleton.

## Feature Inventory Touches

Empty. This plan touches `qor/scripts/` and `tests/` only.

## Definition of Done

### Deliverable: a second proposal cannot destroy a first

- **D1**: Emitting a second remediation proposal in a session leaves the first
  proposal's content recoverable from the session directory.
- **D2**: Iteration numbering matches every other gate phase's convention
  (`<phase>-iter<N>.json`, singleton latest copy alongside it).
- **D3**: `remediate_mark_addressed`'s existing fixed-singleton-path contract
  is unchanged; all five of its existing tests in `tests/test_remediate.py`
  keep passing unmodified.
- **D4**: `test_emit_gate_second_proposal_does_not_destroy_first`, confirmed
  red before this phase's code change and green after.

## CI Commands

- `python -m pytest tests/test_remediate.py -q` -- the direct contract, run
  repeatedly for determinism.
- `python -m pytest tests/ -q` -- full suite; no other test reads
  `remediate_emit_gate` internals.
- `ruff check qor/ tests/` -- clean.
- `python -m qor.cli scripts check_variant_drift` -- no drift.
- `python -m qor.cli verify-ledger` -- chain integrity across the phase's
  entries.
