# Plan: Phase 150 -- Audit Sprint A integrity binding (enforcement core)

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

None. Implements the enforcement core of GH #210 (audit Sprint A) -- the production-gap audit headline.
Operator decision settled: `content_hash` binds to the **plan file** (V1; the current authoring
convention) and is now ENFORCED by recomputation at seal, forward-only. Scoped to three bounded
enforcement fixes in the reliability/gate-chain layer; deferred (logged, follow-on): GAP-GOV-02
(delete the dead `calculate-session-seal.py` -- cascades into SKILL.md + doctrine re-pointing + dist
recompile), GAP-GOV-05 (skill-phase provenance is a self-asserted env string -- needs a non-forgeable
signal), GAP-GOV-03 (TOCTOU gate-pass vs committed bytes -- skill-prose), GAP-GOV-09 + GAP-CQ-02
(`verify()` skip + decompose -- pair, riskier).

## Phase 1: bind content_hash to the plan at seal (GAP-GOV-01)

### Affected Files

- `qor/reliability/seal_entry_check.py` - parse the entry's `**Plan**:` path; recompute and compare.
- `tests/test_seal_entry_content_hash_binding.py` (NEW).

### Changes

`_parse_latest_entry` additionally extracts the `**Plan**: <path>` field into `latest["plan_path"]`
(regex `^\*\*Plan\*\*:\s*(\S+)`). `check(ledger_path, phase_num, repo_root=None)`: after the existing
chain checks, when `latest["plan_path"]` is present, resolve it against `repo_root` (default
`ledger_path.parent.parent`), and compare `ledger_hash.content_hash(plan)` to the entry's recorded
`content_hash`. On mismatch append an error naming recorded vs recomputed (8-char prefixes) -> seal
fails. If the named plan file is absent, append an error (a seal that cites a missing plan is invalid).
This binds the just-sealed entry's `content_hash` to the actual plan bytes; it is forward-only by
construction (`check` only inspects the latest entry, run at the current phase's seal -- existing
entries are never recomputed).

### Unit Tests

- `tests/test_seal_entry_content_hash_binding.py`:
  - `test_matching_content_hash_passes` - a synthetic ledger whose latest SESSION SEAL entry records `content_hash == sha256(plan)` (plan written to a tmp repo) returns `ok=True`.
  - `test_tampered_content_hash_fails` - same entry with a content_hash that does NOT match the plan bytes returns `ok=False` with a reason naming the recorded vs recomputed prefixes.
  - `test_missing_plan_file_fails` - an entry citing a plan path that does not exist returns `ok=False`.

## Phase 2: gate the provenance env bypass (GAP-GOV-04) + validate gate-artifact content (GAP-GOV-14)

### Affected Files

- `qor/scripts/gate_chain.py` - `QOR_GATE_PROVENANCE_OPTIONAL` honored only under pytest.
- `qor/reliability/gate_chain_completeness.py` - validate each artifact's content + schema, not just existence.
- `tests/test_gate_provenance_bypass_pytest_only.py` (NEW), `tests/test_gate_chain_completeness.py` (extend).

### Changes

`gate_chain.py`: add `_pytest_active()` returning `"PYTEST_CURRENT_TEST" in os.environ`. The bypass
guard becomes `if not (os.environ.get("QOR_GATE_PROVENANCE_OPTIONAL") and _pytest_active())` -- so the
documented "tests only" escape hatch is honored only when a test is actually running; in any
non-pytest process the provenance binding is enforced regardless of the env var. `gate_chain_completeness.check`:
replace `if not artifact.is_file()` with `errs = validate_gate_artifact.validate_one(required, artifact)`
and record `f"{sid}/{required}.json: {errs[0]}"` when non-empty -- so an empty / malformed / schema-invalid
gate file no longer satisfies completeness (closes the existence-only hole; the self-reported session id
still names the dir, but the files must now be schema-valid artifacts).

### Unit Tests

- `tests/test_gate_provenance_bypass_pytest_only.py`:
  - `test_bypass_ignored_outside_pytest` - monkeypatch `_pytest_active` -> False, set `QOR_GATE_PROVENANCE_OPTIONAL=1`, call `write_gate_artifact` with no `QOR_SKILL_ACTIVE` -> raises `ProvenanceError`.
  - `test_bypass_honored_under_pytest` - monkeypatch `_pytest_active` -> True with the env set -> the call proceeds (no ProvenanceError).
- `tests/test_gate_chain_completeness.py`:
  - `test_empty_artifact_file_fails_completeness` - a sealed phase whose `plan.json` is present but empty/invalid JSON is reported missing/invalid by `check` (not a pass).

## Definition of Done

### Deliverable: D-integrity-binding

- **D1**: a SESSION SEAL whose `content_hash` does not match its plan bytes fails the seal; the env provenance bypass cannot be used outside tests; an empty/invalid gate artifact no longer satisfies gate-chain completeness.
- **D2**: `seal_entry_check.check` recomputes + compares plan `content_hash`; `gate_chain._pytest_active` guards the bypass; `gate_chain_completeness.check` uses `validate_one`.
- **D3**: ledger SEAL records the Sprint A enforcement core (GAP-GOV-01/04/14); GOV-02/05/03/09 deferred with rationale.
- **D4**: `test_tampered_content_hash_fails` (ok=False, recorded vs recomputed) + `test_missing_plan_file_fails` + `test_bypass_ignored_outside_pytest` (ProvenanceError) + `test_empty_artifact_file_fails_completeness`.

## CI Commands

- `python -m pytest tests/test_seal_entry_content_hash_binding.py tests/test_gate_provenance_bypass_pytest_only.py tests/test_gate_chain_completeness.py tests/test_seal_entry_sealable.py -q` -- new + existing seal/gate tests (run twice).
- `python -m pytest -q` -- full suite green.
