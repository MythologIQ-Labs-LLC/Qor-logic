# Plan: Phase 59 - Seal hash integrity fail-closed

> **Renumbered from Phase 54** (2026-05-11): the original Codex-authored Phase 54 collided with the in-flight Phase 54 compiler-evaluation-loop (sealed at v0.54.0, META_LEDGER #157). Renumbered to Phase 59 (next free slot after Phase 58 governance-capability-surface). All internal references updated in lockstep.

**change_class**: hotfix

**doc_tier**: system

**originating_remediation**: GH #48

**terms_introduced**:
- term: seal hash integrity gate
  home: qor/skills/governance/qor-substantiate/SKILL.md
- term: hash evidence
  home: qor/scripts/hash_guard.py
- term: HashEvidence
  home: qor/scripts/hash_guard.py

**boundaries**:
- limitations:
  - V1 validates local file and ledger hashes only. Remote artifact attestation is out of scope.
  - V1 requires the Python toolkit for cryptographic seal steps. Missing toolkit is a hard failure, not a skipped prerequisite.
- non_goals:
  - Replacing the existing ledger chain format.
  - Changing tag creation or version-bump timing.
- exclusions:
  - No changes to prompt compiler behavior.

## Open Questions

None.

## Phase 1: Hash guard helper

### Affected Files

- `qor/scripts/hash_guard.py` - NEW. Central hash validation and fail-closed helpers.
- `tests/test_hash_guard.py` - NEW.

### Changes

Create a stdlib-only helper:

```python
@dataclass(frozen=True)
class HashEvidence:
    path: str
    sha256: str
    byte_count: int

HEX_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

def hash_file(path: Path) -> HashEvidence: ...
def validate_sha256(value: str, *, label: str) -> str: ...
def require_toolkit_modules(modules: tuple[str, ...]) -> None: ...
```

`validate_sha256` raises `ValueError` for placeholders, empty strings, uppercase/non-hex characters, or non-64-length values. `require_toolkit_modules` imports each module and raises `RuntimeError` with the missing module list when any import fails.

### Unit Tests

- `test_hash_file_returns_64_lower_hex_digest`
- `test_validate_sha256_accepts_real_digest`
- `test_validate_sha256_rejects_placeholder_text`
- `test_validate_sha256_rejects_wrong_length`
- `test_validate_sha256_rejects_uppercase_digest`
- `test_require_toolkit_modules_raises_with_missing_module_names`

## Phase 2: Substantiate hard block for seal-critical hashes

### Affected Files

- `qor/skills/governance/qor-substantiate/SKILL.md` - add mandatory Step 6.8 before Final Merkle Seal.
- `qor/references/doctrine-governance-enforcement.md` - document seal-critical prerequisite semantics.
- `tests/test_substantiate_hash_integrity_step.py` - NEW.

### Changes

Add Step 6.8:

```markdown
### Step 6.8: Seal Hash Integrity Gate (Phase 59 wiring - #48)

Before Step 7 calculates or records any seal hash, import the hash toolkit and validate every hash value that will enter the ledger body. Missing toolkit modules or invalid hash strings ABORT substantiation.
```

The step uses `hash_guard.require_toolkit_modules(("qor.scripts.ledger_hash", "qor.scripts.hash_guard"))` and validates the Merkle seal, content hash, previous hash, and chain hash with `validate_sha256`. This step is not governed by Phase 47 skip semantics; cryptographic evidence is seal-critical and must fail closed.

### Unit Tests

- `test_substantiate_skill_has_seal_hash_integrity_gate`
- `test_hash_gate_precedes_final_merkle_seal`
- `test_hash_gate_says_missing_toolkit_aborts_not_skips`
- `test_hash_gate_mentions_all_ledger_hash_fields`

## Phase 3: Ledger verification rejects fabricated hashes

### Affected Files

- `qor/scripts/ledger_hash.py` - call `hash_guard.validate_sha256` on parsed hash fields.
- `tests/test_ledger_hash_validation.py` - NEW.

### Changes

When `ledger_hash.verify` parses an entry, validate every parsed content, previous, and chain hash before comparing chain semantics. Invalid format is a verification failure with a specific error, not a best-effort warning.

### Unit Tests

- `test_verify_rejects_placeholder_content_hash`
- `test_verify_rejects_placeholder_chain_hash`
- `test_verify_reports_entry_number_for_invalid_hash`
- `test_verify_still_accepts_known_good_fixture`

## CI Commands

- `python -m pytest tests/test_hash_guard.py tests/test_substantiate_hash_integrity_step.py tests/test_ledger_hash_validation.py -v`
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py`
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase59-seal-hash-integrity.md`
