# Plan: Phase 64 - Seal hash integrity gate, substantiate wiring

**change_class**: hotfix

**doc_tier**: system

**originating_remediation**: GH #48 (Phase 59 Phase 2 dropped during Phase 60 session-consolidation; `qor/scripts/hash_guard.py` shipped to main but never wired into `qor/skills/governance/qor-substantiate/SKILL.md`).

**terms_introduced**: none. Phase 59 plan already homed `seal hash integrity gate`, `hash evidence`, and `HashEvidence`; this plan reuses those homes without renaming.

**boundaries**:
- limitations:
  - V1 wires the existing `hash_guard` helper into `/qor-substantiate` Step 6.8 only. It does not change the Step 7 Merkle-seal computation path or add new hash modes.
  - V1 validates locally produced hash strings before they enter the ledger body. Remote attestation is out of scope (matches Phase 59 plan limitation).
- non_goals:
  - Adding new validators beyond `validate_sha256` and `require_toolkit_modules` already exposed by `qor/scripts/hash_guard.py`.
  - Modifying `qor/scripts/ledger_hash.py` verification behavior (Phase 59 Phase 3 landed; tests pass).
- exclusions:
  - No changes to prompt compiler behavior.
  - No changes to `qor/reliability/seal_entry_check.py` (it already runs at Step 7.7 after Step 7).
  - No retroactive ledger edits.

**scope_expansion_2026-05-14**: two surgical fixes folded into Phase 64 after the initial implementation pass uncovered them as blockers/sharpness gaps for the very `/qor-substantiate` Step 4.7 the gate must coexist with:
1. **`qor/scripts/doc_integrity.py:218` strict-mode import bug** (pre-existing since Phase 31). Bare `import doc_integrity_strict` resolved only when `sys.path` happened to include `qor/scripts/`. From `/qor-substantiate` Step 4.7 the call raised `ModuleNotFoundError` before doc-integrity checks could fire, masking the actual integrity surface. Fix is a one-line conversion to the package import.
2. **Step 6.8 Preparation prose** (sharpness gap, not blocker). The Phase 59 plan's original wording assumed the four hash variables would already exist when Step 6.8 ran; in practice they are computed during Step 7 itself. Added a Preparation paragraph telling the operator to invoke the canonical hash-producing helpers (`hash_guard.hash_file`, `ledger_hash.content_hash`, `ledger_hash.chain_hash`) before the validation block, so Step 6.8 validates real digests rather than undefined variables.

## Open Questions

None. The Phase 59 plan already passed audit at `.qor/gates/2026-05-11T1500-phase59/audit.json`; this plan reuses its design intent and lands the dropped Phase 2 wiring.

## Phase 1: Substantiate SKILL.md gains Step 6.8 (Seal Hash Integrity Gate)

### Affected Files

- `tests/test_substantiate_hash_integrity_step.py` - NEW. Behavior-focused unit tests that assert the SKILL.md prose binds the gate (presence + ordering + abort semantics + field coverage).
- `qor/skills/governance/qor-substantiate/SKILL.md` - add Step 6.8 between Step 6.5 (Documentation Currency Check) and Step 7 (Final Merkle Seal). Step 6.8 invokes `hash_guard.require_toolkit_modules` for the seal-critical module set, then validates the four seal-critical hash values via `hash_guard.validate_sha256`.
- `qor/references/doctrine-governance-enforcement.md` - new subsection under existing seal-integrity content documenting Step 6.8 as a fail-closed gate (no override path; no Phase 47 skip semantics).

### Changes

`tests/test_substantiate_hash_integrity_step.py` is written FIRST and fails red on initial run because the substantiate SKILL.md has no Step 6.8 text yet. The four tests below MUST drive the prose authoring; do not start the SKILL.md edit until the tests are committed-staged and red.

`qor/skills/governance/qor-substantiate/SKILL.md` gains the following new step verbatim (with the exact heading text shown so the test assertions are stable):

```markdown
### Step 6.8: Seal Hash Integrity Gate (Phase 64 wiring - GH #48)

Before Step 7 computes or records any seal hash, import the seal-critical
toolkit and validate every hash value that will enter the ledger body.
Missing toolkit modules or invalid hash strings ABORT substantiation.
Fail-closed: this step has no override path and is not governed by
Phase 47 skip semantics; cryptographic evidence must always be validated.

\```python
from qor.scripts.hash_guard import (
    require_toolkit_modules,
    validate_sha256,
)

require_toolkit_modules(
    ("qor.scripts.ledger_hash", "qor.scripts.hash_guard")
)

# Validate every hash value that Step 7 will write into the SESSION SEAL
# entry. Order matches the ledger entry layout.
validate_sha256(merkle_seal,   label="merkle_seal")
validate_sha256(content_hash,  label="content_hash")
validate_sha256(previous_hash, label="previous_hash")
validate_sha256(chain_hash,    label="chain_hash")
\```

Any raised `ValueError` or `RuntimeError` ABORTs substantiation. Operator
fixes the cause (install missing toolkit modules, regenerate the affected
hash via `python -m qor.scripts.ledger_hash hash <path>`, or amend the
fabricated value to a real digest) and re-runs `/qor-substantiate`.
Per `qor/references/doctrine-governance-enforcement.md` (Seal Hash
Integrity Gate subsection).
```

The placement contract: Step 6.8 sits AFTER Step 6.5 (Documentation Currency Check) and BEFORE Step 7 (Final Merkle Seal). It runs after the version bump has occurred but before any hash flows into the ledger entry body. This is the only ordering where the four hash variables exist with their post-Step-7 values yet have not entered durable storage.

`qor/references/doctrine-governance-enforcement.md` gains a new subsection titled "Seal Hash Integrity Gate" documenting:

- The gate exists at `/qor-substantiate` Step 6.8.
- It uses `qor.scripts.hash_guard.require_toolkit_modules` plus `validate_sha256`.
- It is fail-closed with no override path (matching Phase 59 plan's seal-critical semantics).
- The four covered fields: `merkle_seal`, `content_hash`, `previous_hash`, `chain_hash`.
- Rationale: prevents the GH #48 failure mode (LLM-fabricated hash strings entering the META_LEDGER chain in non-Python repos).

### Unit Tests

- `tests/test_substantiate_hash_integrity_step.py::test_substantiate_skill_has_seal_hash_integrity_gate` - reads the canonical `qor/skills/governance/qor-substantiate/SKILL.md`, parses out Step 6.8 by its exact heading, and asserts that the parsed step body invokes both `require_toolkit_modules` and `validate_sha256`. Fails if the step is absent or if either invocation is missing from the body.
- `tests/test_substantiate_hash_integrity_step.py::test_hash_gate_precedes_final_merkle_seal` - parses both Step 6.8 and Step 7 headings out of the SKILL.md, computes their byte offsets, and asserts `offset(Step 6.8) < offset(Step 7)`. Fails if the gate is positioned after the seal calculation.
- `tests/test_substantiate_hash_integrity_step.py::test_hash_gate_abort_co_occurs_with_toolkit_failure_clause` - parses the Step 6.8 body and locates the sentence (period-delimited) that names the toolkit-failure condition (any of "missing toolkit", "ValueError", "RuntimeError", "invalid hash"). Asserts that same sentence contains "ABORT" and does NOT contain "skip" or "warn". This is a conditional co-occurrence invariant on the abort-semantics clause: the failure condition and the abort verb must travel together in one sentence, so loosening one without the other (e.g., adding a "skip on warn" branch next to the abort) fails the test.
- `tests/test_substantiate_hash_integrity_step.py::test_hash_gate_mentions_all_ledger_hash_fields` - asserts the Step 6.8 body names all four seal-critical hash labels (`merkle_seal`, `content_hash`, `previous_hash`, `chain_hash`) as arguments to `validate_sha256`. Prevents silent field-coverage regressions.

## Phase 2: Dist variant regeneration

### Affected Files

- `tests/test_substantiate_dist_variants_carry_hash_gate.py` - NEW. Tests that every dist variant SKILL.md carries the Step 6.8 heading after `dist_compile` runs.
- `qor/dist/variants/claude/skills/qor-substantiate/SKILL.md` - regenerated via `python -m qor.scripts.dist_compile`.
- `qor/dist/variants/codex/skills/qor-substantiate/SKILL.md` - regenerated.
- `qor/dist/variants/kilo-code/skills/qor-substantiate/SKILL.md` - regenerated.

### Changes

`tests/test_substantiate_dist_variants_carry_hash_gate.py` is written first and fails red because the dist variants do not yet carry Step 6.8. After Phase 1 lands the source SKILL.md change, run `python -m qor.scripts.dist_compile`; the variants update from source and the test passes green.

No manual edits to dist variants. The Phase 30 dist-drift contract requires variants to be regenerated from source; manually edited variants are a doctrine violation per `qor/references/doctrine-governance-enforcement.md`.

### Unit Tests

- `tests/test_substantiate_dist_variants_carry_hash_gate.py::test_claude_variant_carries_step_6_8` - reads `qor/dist/variants/claude/skills/qor-substantiate/SKILL.md`, asserts the literal heading `### Step 6.8: Seal Hash Integrity Gate` appears exactly once. Fails if dist drift.
- `tests/test_substantiate_dist_variants_carry_hash_gate.py::test_codex_variant_carries_step_6_8` - same assertion for the codex variant.
- `tests/test_substantiate_dist_variants_carry_hash_gate.py::test_kilo_code_variant_carries_step_6_8` - same assertion for the kilo-code variant.

## Phase 3: Strict-mode import fix + Step 6.8 Preparation prose

### Affected Files

- `tests/test_doc_integrity_strict_import.py` - NEW. Three regression tests covering strict-mode behavior, lenient-mode behavior, and source-text invariant.
- `qor/scripts/doc_integrity.py` - one-line fix: `import doc_integrity_strict` -> `from qor.scripts import doc_integrity_strict`.
- `qor/skills/governance/qor-substantiate/SKILL.md` - Step 6.8 gains a Preparation paragraph naming the canonical hash-producing helpers operators invoke before the validation block runs.
- `tests/test_substantiate_hash_integrity_step.py` - one new test (`test_hash_gate_preparation_names_canonical_helpers`) asserting the Preparation paragraph cites `hash_guard.hash_file`, `ledger_hash.content_hash`, and `ledger_hash.chain_hash`.

### Changes

Phase 3 is the surgical scope expansion declared in `scope_expansion_2026-05-14`. The doc_integrity fix unblocks `/qor-substantiate` Step 4.7 strict-mode execution. The Preparation paragraph closes the variable-definedness ordering ambiguity in Step 6.8.

### Unit Tests

- `tests/test_doc_integrity_strict_import.py::test_strict_mode_does_not_raise_module_not_found` - invokes `doc_integrity.run_all_checks_from_plan(plan, repo_root=".", strict=True)` from the project root; fails with the helpful diagnostic if the bare import is reintroduced. Tolerates `ValueError` (real check firing) but fails on `ModuleNotFoundError`.
- `tests/test_doc_integrity_strict_import.py::test_lenient_mode_still_skips_strict_checks` - invokes the lenient path and asserts it never imports `doc_integrity_strict`, guarding against a future refactor that hoists the import to module scope.
- `tests/test_doc_integrity_strict_import.py::test_strict_import_uses_package_path` - reads `qor/scripts/doc_integrity.py` and asserts the package-form import string is present and no bare `import doc_integrity_strict` line survives. Guards against drift in environments where `sys.path` accidentally satisfies the bare form.
- `tests/test_substantiate_hash_integrity_step.py::test_hash_gate_preparation_names_canonical_helpers` - reads the canonical SKILL.md, locates the Step 6.8 body, asserts the Preparation paragraph is present and names all three canonical helpers. Without the Preparation prose, Step 6.8 validates undefined variables and the gate becomes order-dependent dead code.

## CI Commands

- `python -m pytest tests/test_substantiate_hash_integrity_step.py tests/test_substantiate_dist_variants_carry_hash_gate.py tests/test_hash_guard.py tests/test_ledger_hash_validation.py tests/test_doc_integrity_strict_import.py -v` - validates the new substantiate-skill tests, the dist-variant tests, the existing hash_guard + ledger_hash regression tests, and the new doc_integrity strict-import regression tests.
- `python -m qor.scripts.dist_compile` - regenerates dist variants from source so Phase 2 tests can find Step 6.8 in each variant.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase64-seal-hash-substantiate-wiring.md` - lint this plan file itself for cross-section identity consistency.
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py` - full suite minus the flaky tag-coverage test that requires git history not yet sealed.
