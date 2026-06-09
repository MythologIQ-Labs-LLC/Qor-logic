# Plan: Phase 145 -- wire the #201 validity gate into the seal path (fail-closed)

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

None. Follow-on to GH #201 (operator comment, verified against 0.106.0): the Phase 140 helpers
`ledger_hash.assert_sealable_text` / `normalize_punctuation` shipped but the gate is only wired into
the *fragment* path (`ledger_fragment.write_fragment`, `canonicalize_fragments`). The actual seal
path -- `/qor-substantiate` editing `docs/META_LEDGER.md` directly -- does not traverse that path, so
a SESSION SEAL entry can still be written with non-ASCII / non-UTF-8 bytes (the #201 corruption
class). `qor.reliability.seal_entry_check` already runs at `/qor-substantiate` Step 7.7
(`qor/skills/governance/qor-substantiate/SKILL.md:71,510`), so strengthening it makes the seal
fail-closed with no skill-prompt or variant change.

## Phase 1: make seal_entry_check reject an unsealable latest entry

### Affected Files

- `tests/test_seal_entry_sealable.py` (NEW) - behavior tests.
- `qor/reliability/seal_entry_check.py` - fail-closed on a non-UTF-8 ledger; validate the latest
  entry block is ASCII via `assert_sealable_text`.

### Changes

`seal_entry_check.py`:
- Wrap the `Path(ledger_path).read_text(encoding="utf-8")` in `try/except UnicodeDecodeError`; on
  failure return `SealEntryResult(ok=False, errors=["ledger is not valid UTF-8: <exc>"])` (so the
  invalid-UTF-8 #201 case fails the gate cleanly instead of raising an uncaught decode error).
- `_parse_latest_entry` returns the latest entry's `block` text (already computed as
  `text[last.start():]`). In `check`, after the existing chain checks, run
  `assert_sealable_text(latest["block"], label=f"entry #{latest['entry_num']} body")` inside
  `try/except ValueError`; on `ValueError` append the message to `errors` (non-ASCII -> seal aborts).

The `/qor-substantiate` Step 7.7 invocation is unchanged; it now aborts the seal when the just-written
SESSION SEAL entry carries non-ASCII / invalid-UTF-8 bytes -- closing the #201 seal-path gap.

### Unit Tests

- `tests/test_seal_entry_sealable.py`:
  - `test_non_ascii_latest_entry_fails` - a synthetic ledger whose latest SESSION SEAL entry body
    contains a U+2014 returns `ok=False` with a reason naming `U+2014` (invoke `check`, assert the
    result + message).
  - `test_clean_ascii_latest_entry_passes` - a synthetic ASCII SESSION SEAL entry with a consistent
    chain hash returns `ok=True` (regression: the gate does not reject clean seals).
  - `test_invalid_utf8_ledger_fails_closed` - a ledger file written with raw invalid-UTF-8 bytes
    (e.g. `0x92`) makes `check` return `ok=False` (not raise `UnicodeDecodeError`).

## Definition of Done

### Deliverable: D-seal-gate

- **D1**: the seal step rejects a SESSION SEAL entry containing non-ASCII / invalid-UTF-8 bytes.
- **D2**: `seal_entry_check.check` wraps the read and validates the latest entry via
  `assert_sealable_text`; `_parse_latest_entry` exposes the entry block.
- **D3**: ledger SEAL records the #201 follow-on; no doctrine/term change (minimal tier).
- **D4**: `test_non_ascii_latest_entry_fails` (ok=False + U+2014) + `test_invalid_utf8_ledger_fails_closed`
  (ok=False, no crash) + `test_clean_ascii_latest_entry_passes` (regression).

## CI Commands

- `python -m pytest tests/test_seal_entry_sealable.py tests/test_seal_entry_check.py -q` -- new + existing seal-entry tests.
- `python -m pytest -q` -- full suite green.
