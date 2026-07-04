# Plan: Phase 171 - Correct stale action pins in release evidence (hotfix)

**change_class**: hotfix

**doc_tier**: minimal

**required_gate_artifacts**: plan, implement, substantiate (short chain per Phase 168 -- L1 risk, hotfix class; the skipped audit is evidenced by a severity-1 gate_override shadow event)

**boundaries**:
- limitations: Two literal corrections in the `evidence.json` assembly block only; no workflow logic changes.
- non_goals: No dynamic pin derivation (a future improvement); no other workflow edits (dependabot PRs #235/#236 already aligned the live pins repo-wide, including nightly-health.yml via the rebased group).
- exclusions: (none)

## Origin

Dependabot PRs #235/#236 (merged 2026-07-04) bumped `actions/checkout` to v7.0.0 (`9c091bb2...`) and `actions/setup-python` to v6.3.0 (`ece7cb06...`) across all five workflows. The `release.yml` publish job's `dist/evidence.json` provenance block hardcodes `action_pins` and now records stale values (its checkout entry `de0fac2e...` was stale even before the bump); a release built today would attest pins it does not use.

## Locked Decision

- **LD-1**: `grep -n 'uses:' .github/workflows/release.yml` -> checkout `9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0`, setup-python `ece7cb06caefa5fff74198d8649806c4678c61a1`, upload-artifact `043fb46d...` (matches evidence), download-artifact `3e5f45b2...` (matches), pypi-publish `cef22109...` (matches). Only the checkout and setup-python evidence literals (release.yml:131-132) drift. The immutability suite checks evidence FIELD presence (test_release_workflow_immutability.py:195), not pin values -- no test is red; the values are simply false provenance.

## Phase 1: Literal correction

### Affected Files

- .github/workflows/release.yml - evidence.json `action_pins`: checkout -> `9c091bb2...`, setup-python -> `ece7cb06...`

### Unit Tests

(none new -- config-literal hotfix; the 13 release-immutability property tests + full suite are the regression net, and the values are verified against LD-1's grep in the seal entry)

## Definition of Done

### Deliverable: truthful release evidence

- **D1**: The next release's `evidence.json` attests the pins actually used.
- **D2**: release.yml:131-132 literals equal the `uses:` SHAs in the same file.
- **D3**: Seal entry records the short-chain declaration + shadow event id; CHANGELOG hotfix note.
- **D4.d**: No new unit invokes this config block; verification is the LD-1 grep equality recorded at seal + the existing immutability suite green. **Follow-up phase**: dynamic pin derivation if evidence drift recurs.

## CI Commands

- `python -m pytest tests/test_release_workflow_immutability.py -q` -- immutability properties
- `python -m pytest -q` -- full suite regression
