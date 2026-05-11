# Plan: Phase 56 - Federated ledger entry identity

**change_class**: feature

**doc_tier**: system

**originating_remediation**: GH #51

**terms_introduced**:
- term: ledger entry UID
  home: qor/scripts/ledger_entry_id.py
- term: federated ledger fragment
  home: qor/scripts/ledger_fragment.py
- term: canonical ledger ordering
  home: qor/references/doctrine-governance-enforcement.md

**boundaries**:
- limitations:
  - V1 keeps the human-readable `Entry #N` headings after canonicalization.
  - V1 solves concurrent worker writes by moving workers to fragments; final META_LEDGER materialization remains a single canonicalization step.
- non_goals:
  - Distributed consensus.
  - Cross-repository ledger replication.
  - Removing `docs/META_LEDGER.md`.
- exclusions:
  - No change to existing historical ledger entries.

## Open Questions

None.

## Phase 1: Stable entry UID helper

### Affected Files

- `qor/scripts/ledger_entry_id.py` - NEW.
- `tests/test_ledger_entry_id.py` - NEW.

### Changes

Create a deterministic helper:

```python
def make_entry_uid(*, ts: str, session_id: str, target: str, content_hash: str) -> str: ...
def validate_entry_uid(value: str) -> str: ...
```

UID format is `le_<16 hex>` where the hex is derived from SHA256 over the input tuple. The UID is stable for a worker fragment and does not depend on sequential `Entry #N` allocation.

### Unit Tests

- `test_make_entry_uid_is_stable`
- `test_make_entry_uid_changes_when_content_hash_changes`
- `test_validate_entry_uid_accepts_helper_output`
- `test_validate_entry_uid_rejects_sequential_number`

## Phase 2: Worker fragments instead of concurrent direct ledger writes

### Affected Files

- `qor/scripts/ledger_fragment.py` - NEW.
- `qor/references/doctrine-governance-enforcement.md` - document fragment write discipline.
- `tests/test_ledger_fragment.py` - NEW.

### Changes

Create fragment helpers:

```python
@dataclass(frozen=True)
class LedgerFragment:
    uid: str
    ts: str
    session_id: str
    title: str
    body: str
    content_hash: str

def write_fragment(root: Path, fragment: LedgerFragment) -> Path: ...
def read_fragments(root: Path) -> tuple[LedgerFragment, ...]: ...
```

Fragments live under `.qor/ledger/fragments/<uid>.json`. Worker sessions write fragments only. They do not guess the next `Entry #N`.

### Unit Tests

- `test_write_fragment_uses_uid_filename`
- `test_write_fragment_refuses_duplicate_uid_with_different_body`
- `test_read_fragments_sorts_by_timestamp_then_uid`
- `test_fragment_content_hash_must_match_body`

## Phase 3: Canonicalization assigns display numbers once

### Affected Files

- `qor/scripts/ledger_hash.py` - add fragment canonicalization entry point.
- `qor/skills/governance/qor-substantiate/SKILL.md` - instruct federation workers to emit fragments and the sealing worker to canonicalize.
- `tests/test_ledger_fragment_canonicalization.py` - NEW.

### Changes

Add:

```python
def canonicalize_fragments(ledger_path: Path, fragment_root: Path) -> int: ...
```

The function reads pending fragments, sorts by `(ts, uid)`, appends them to `docs/META_LEDGER.md` with the next display number, recalculates the chain, and archives consumed fragments to `.qor/ledger/fragments/consumed/`.

Sequential numbers become presentation only. The UID is the cross-worker identity.

### Unit Tests

- `test_canonicalize_assigns_contiguous_display_numbers`
- `test_canonicalize_order_is_stable_for_same_timestamp`
- `test_canonicalize_archives_consumed_fragments`
- `test_verify_chain_passes_after_canonicalization`

## CI Commands

- `python -m pytest tests/test_ledger_entry_id.py tests/test_ledger_fragment.py tests/test_ledger_fragment_canonicalization.py -v`
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py`
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase56-federated-ledger-entry-identity.md`
