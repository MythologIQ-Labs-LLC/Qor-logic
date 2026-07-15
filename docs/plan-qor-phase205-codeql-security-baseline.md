# Plan: Fail-closed CodeQL security baseline (Qortara ecosystem)

**change_class**: governance

**doc_tier**: minimal

**originating_remediation**: MythologIQ-Labs-LLC/qortara-sdlc#41

## Objective

Add a pinned, least-privilege Python CodeQL workflow to Qor-logic, preserve the repository's existing Linux and Windows test matrix and dependency review, and require an accepted exact-head code-scanning result before merge.

## Scope

### Affected files

- `.github/workflows/codeql.yml` - add Python `security-extended` analysis with immutable action pins, path filters, weekly cost justification, and exact-ref concurrency.
- `.github/workflows/ci.yml` - retain the canonical pytest command while emitting JUnit evidence artifacts for every operating-system and Python-version matrix cell.
- `tests/test_merge_velocity_check.py` - make synthetic Git history deterministic with `--allow-empty` while preserving the complete existing test suite.
- `docs/plan-qor-phase205-codeql-security-baseline.md` - bind intent and merge criteria.
- `.qor/gates/<session>/` - record plan, audit, implementation, and substantiation evidence.
- `docs/META_LEDGER.md` - append one plan-bound SESSION SEAL through the canonical ledger emitter.

### Non-goals

- No dependency changes.
- No runtime product behavior changes.
- No reduction of existing CI, dependency-review, ledger, provenance, or governance controls.
- No administrative merge bypass, advisory waiver, or personal-access-token substitution.
- No changes to Bicameral or repositories outside MythologIQ Labs' Qortara scope.

## Controls

1. CodeQL runs for Python on pull requests, pushes to `main`, manual dispatch, and one justified weekly schedule.
2. CodeQL uses `security-extended` queries and immutable action revisions.
3. Workflow permissions remain read-only except `security-events: write` for SARIF publication.
4. Existing pytest commands remain textually unchanged; JUnit is supplied through `PYTEST_ADDOPTS` so the sealed CI command contract remains intact.
5. Synthetic merge-history tests create the intended DAG deterministically across Python and Git versions.
6. Merge is allowed only when CodeQL publication, dependency review, citation lint, and the full exact-head CI matrix pass.

## Repository configuration prerequisite

GitHub Code Security and code scanning must accept SARIF for the repository. A locally generated clean CodeQL database is not merge evidence until GitHub publishes the result.

## Validation

- `python -m pytest tests/ -v`
- `python qor/scripts/check_variant_drift.py`
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md`
- `python -m qor.reliability.seal_entry_check --ledger docs/META_LEDGER.md --auto`
- Existing PR Dependency Review
- Exact-head CodeQL publication

## Definition of Done

- CodeQL and every existing required workflow pass on the same exact head.
- The PR body cites this plan, the generated ledger entry number, and the generated 64-character Merkle seal.
- Gate artifacts and ledger chain verify after commit.
- No bypass, ignored advisory, or unrelated scope expansion is introduced.
