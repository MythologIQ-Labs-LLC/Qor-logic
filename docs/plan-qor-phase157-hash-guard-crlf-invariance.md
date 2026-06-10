# Plan: Phase 157 - hash_guard.hash_file CRLF-invariant seal-text option (GAP-GOV-03 follow-on)

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

None. Scope is a single hardening option on one seal-relevant helper, mirroring the Phase 156 `ledger_hash.content_hash` fix.

## Context

Phase 156 made `ledger_hash.content_hash` LF-normalize before hashing, so the GOV-01 content_hash<->plan binding survives git's autocrlf conversion of the committed plan. `qor/scripts/hash_guard.hash_file` is the OTHER seal-relevant file hasher: `/qor-substantiate` Step 6.8 Preparation cites it (alongside `ledger_hash.content_hash` / `chain_hash`) as a helper an operator uses to compute real seal digests. It still hashes raw bytes (`Path(path).read_bytes()`), so a digest it produces over a text artifact drifts the same way content_hash did pre-156 once git rewrites the committed file to CRLF.

`hash_file` is also advertised as a general-purpose file hasher (its existing test hashes a `.bin` fixture), so it must stay byte-exact for binary inputs. The fix is therefore an OPT-IN normalization flag, not an unconditional change: seal-text callers pass `normalize_newlines=True`; binary callers keep the raw default.

`qor/reliability/intent_lock._hash_file` is a separate private hasher over the plan/audit GATE ARTIFACTS; it captures and re-checks within a single working copy (no git round-trip between lock and verify), so it is NOT in this fragility class and is left unchanged.

## Phase 1: Opt-in CRLF-invariant hashing in hash_file

### Affected Files

- `qor/scripts/hash_guard.py` - add `normalize_newlines: bool = False` param to `hash_file`; when True, LF-normalize bytes before hashing and report `byte_count` over the hashed (normalized) bytes.
- `qor/scripts/hash_guard.py` (module docstring) - document the new param on the `hash_file` line.

### Changes

```python
def hash_file(path: Path, *, normalize_newlines: bool = False) -> HashEvidence:
    raw = Path(path).read_bytes()
    data = raw.replace(b"\r\n", b"\n") if normalize_newlines else raw
    return HashEvidence(
        path=str(path),
        sha256=hashlib.sha256(data).hexdigest(),
        byte_count=len(data),
    )
```

Default `False` preserves every current call (binary-safe, byte-exact) and the missing-path `FileNotFoundError` still raises from `read_bytes()`. `byte_count` reflects the bytes actually hashed, so the dataclass stays internally consistent under either mode.

### Unit Tests

- `tests/test_hash_guard.py::test_hash_file_normalize_newlines_crlf_invariant` - a CRLF file and its LF twin produce the SAME `hash_file(..., normalize_newlines=True).sha256`, and that digest equals `hash_file(lf_twin).sha256` (the default of the already-LF file). Confirms the seal-text option is invariant to git's conversion.
- `tests/test_hash_guard.py::test_hash_file_default_is_byte_exact_for_crlf` - `hash_file(crlf)` (default) differs from `hash_file(lf)` and equals `sha256` of the raw CRLF bytes, with `byte_count` == raw length. Confirms binary callers are unaffected (no silent normalization).
- `tests/test_hash_guard.py::test_hash_file_normalize_byte_count_matches_hashed_bytes` - under `normalize_newlines=True` over a CRLF file, `byte_count` equals the normalized (LF) length, not the raw length, so the digest and the count describe the same bytes.

The existing `test_hash_file_returns_64_lower_hex_digest` (LF-free `.bin` fixture) and `test_hash_file_raises_on_missing_path` remain green unchanged: normalization is a no-op for newline-free content and the default is raw.

## Phase 2: Reference-doc guidance (progressive disclosure)

### Affected Files

- `qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md` - add a short note under the seal-hash material: text seal artifacts hashed via `hash_guard.hash_file` for evidence should pass `normalize_newlines=True` so the recorded digest survives git autocrlf, mirroring the Phase 156 `content_hash` fix; binary artifacts keep the raw default.

The substantiate SKILL.md Step 6.8 prose is intentionally NOT edited (the skill is 9 bytes under the 40 KB EXCEEDED budget; new sub-guidance belongs in the reference per the progressive-disclosure doctrine). The Step 6.8 self-test still finds the cited `hash_guard.hash_file` token unchanged.

### Unit Tests

None (doc-only change; the guidance is prose in a reference file, not a behavioral unit). The behavioral contract is fully covered by the Phase 1 tests.

## Definition of Done

### Deliverable: CRLF-invariant seal-text hashing option on hash_file

- **D1**: A seal-text digest produced by `hash_guard.hash_file` survives git's autocrlf conversion, closing the same fragility class Phase 156 fixed for `content_hash`, without changing binary-hash behavior.
- **D2**: `hash_file(path, *, normalize_newlines: bool = False) -> HashEvidence` in `qor/scripts/hash_guard.py`; when True it hashes `raw.replace(b"\r\n", b"\n")` and sets `byte_count` to the hashed length.
- **D3**: `qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md` documents when seal callers pass `normalize_newlines=True`; ledger entry records the Phase 157 hotfix.
- **D4**: `test_hash_file_normalize_newlines_crlf_invariant` asserts a CRLF file and its LF twin yield the same digest under the flag; `test_hash_file_default_is_byte_exact_for_crlf` asserts the default still distinguishes them.

## CI Commands

- `python -m pytest tests/test_hash_guard.py -q` - the new CRLF-invariance + binary-exact behavior and the unchanged Phase 59 contract.
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - chain still verifies clean after the seal entry.
- `python -m qor.reliability.seal_entry_check --ledger docs/META_LEDGER.md --auto` - committed-seal GOV-01 binding re-verify (Phase 156 gate).
