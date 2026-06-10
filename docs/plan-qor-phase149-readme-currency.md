# Plan: Phase 149 -- README currency (doc-only)

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

None. A `/qor-document` thorough review of the two Qor-authored READMEs (`README.md`,
`qor/reliability/README.md`) found `qor/reliability/README.md` fully current and three operator-approved
edits to `README.md`. Doc-only: no code, no new dependency, no behavior change. The kilo-code folder
correction is a factual bug fix (the PyPI-facing README pointed installers at the wrong directory).

## Phase 1: apply the three approved README edits

### Affected Files

- `README.md` - (1) kilo-code install folder `./.kilo-code/` -> `./.kilo/`; (2) link the downstream-enforcement-SDK doc + note the Phase-148 `compliance enforce` verdict/status semantics in the CLI Reference; (3) add a `docs/FEATURE_INDEX.md` row to the Entry-points + governance table.

### Changes

1. **Bug fix** (`README.md` host-layout table): the `kilo-code` host resolves to base `.kilo`
   (`qor/hosts.py:68` -- `_scoped_base(".kilo", scope)`), not `.kilo-code`; the table's Default-folder
   column is corrected to `./.kilo/skills/`, `./.kilo/agents/`.
2. **Currency** (CLI Reference): append a comment beneath `compliance enforce` noting the explicit
   verdict (`enforced`/`failed`/`no_op`) + per-control `status` (pass/fail/skip/disclosed) + disclosed-skip,
   and pointing to `qor/references/downstream-enforcement-sdk.md` (the Phase-148 surface, previously
   undocumented in the README; cited as FX013's doc in FEATURE_INDEX).
3. **Completeness** (Entry-points + governance table): add a `docs/FEATURE_INDEX.md` row (17 verified
   features), which previously shipped unreferenced.

### Verification (doc-only; no unit added)

Doc-currency correction, not a code change -- no new test. Evidence: the kilo-code claim is grep-verified
against `qor/hosts.py:68` (`resolve('kilo-code').base.name == '.kilo'`); both new links resolve on disk
(`docs/FEATURE_INDEX.md`, `qor/references/downstream-enforcement-sdk.md`); the README is ASCII-clean
(0 non-ASCII chars). README badge currency is preserved (no test added -> Tests badge unchanged at 2410;
Ledger badge advances with the seal entry).

## Definition of Done

### Deliverable: D-readme-currency

- **D1**: the PyPI-facing README no longer points installers at a non-existent kilo-code host directory and surfaces the Phase-148 enforce semantics + SDK doc.
- **D2**: `README.md` host table row matches `qor/hosts.py` resolution; the SDK-doc link + FEATURE_INDEX row are present; README stays ASCII-clean.
- **D3**: ledger SEAL records the doc-currency pass; badge currency preserved.
- **D4.d**: doc-only correction; no runtime unit to assert. **Follow-up phase**: none required (grep-verified against `qor/hosts.py:68`; links resolve; ASCII-clean).

## CI Commands

- `python -m pytest tests/test_readme_badge_currency.py tests/test_doc_integrity*.py -q` -- README badge + doc-integrity gates.
- `python -m pytest -q` -- full suite green.
