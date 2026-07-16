# Plan: Zero-cost OSS SAST correction for the Qortara ecosystem

**change_class**: feature

**doc_tier**: minimal

**originating_remediation**: MythologIQ-Labs-LLC/qortara-sdlc#41

## Objective

Replace the Phase 205 CodeQL requirement with a zero-license-cost, repository-owned static-analysis gate while preserving Qor-logic's Linux and Windows test matrix, public dependency review, ledger chain, provenance, and exact-head merge discipline.

## Scope

### Affected files

- `.github/workflows/codeql.yml` - remove the CodeQL workflow and its `security-events: write` permission.
- `.github/workflows/oss-sast.yml` - add Semgrep Community Edition 1.169.0 with local JSON evidence and no platform login or token.
- `docs/plan-qor-phase205-zero-cost-oss-sast.md` - bind the corrected cost and security intent.
- `.qor/gates/<session>/` - record plan, audit, implementation, and substantiation evidence.
- `docs/META_LEDGER.md` - append a new immutable correction seal through the canonical ledger emitter.
- `README.md` and `docs/SYSTEM_STATE.md` - regenerate derived seal-artifact currency.

### Non-goals

- No runtime product behavior change.
- No dependency change to Qor-logic itself.
- No reduction of the existing CI, public dependency-review, ledger, provenance, citation, or governance controls.
- No paid GitHub security entitlement, Semgrep platform account, security-platform token, scheduled scanner, advisory waiver, PAT, or administrative merge bypass.
- No changes to Bicameral or repositories outside MythologIQ Labs' Qortara scope.

## Controls

1. Semgrep Community Edition is pinned to version 1.169.0 and installed directly in the Actions runner.
2. Community `p/security-audit` rules scan production sources and block only `ERROR` severity findings.
3. Documentation, tests, fixtures, vendored code, generated output, and workflow YAML are excluded from the blocking scan; their native checks remain authoritative.
4. Source and findings remain local to the runner; JSON evidence is retained as a repository artifact.
5. The scan fails directly on blocking findings or scanner failure and requires only `contents: read`.
6. Documentation-only changes do not consume scanner runs, and no recurring schedule is configured.
7. Existing pytest commands, Linux and Windows matrices, public dependency review, citation lint, ledger verification, gate-chain completeness, and provenance checks remain authoritative.
8. Derived README and SYSTEM_STATE seal artifacts are regenerated through `qor.scripts.seal_artifacts`.

## CI Commands

- `python -m pytest tests/ -v`
- `python qor/scripts/check_variant_drift.py`
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md`
- `python -m qor.reliability.seal_entry_check --ledger docs/META_LEDGER.md --auto`
- `python -m qor.scripts.seal_artifacts --check --repo-root .`
- `semgrep scan --config p/security-audit --severity ERROR --error --metrics off --json --output semgrep.json --exclude docs --exclude tests --exclude fixtures --exclude vendor --exclude node_modules --exclude target --exclude dist --exclude build --exclude .next --exclude .github .`
- Existing public PR Dependency Review

## Definition of Done

- OSS SAST and every existing required workflow pass on the same exact head.
- The PR body cites this correction plan, its generated ledger entry, and its 64-character Merkle seal.
- Gate artifacts, derived seal artifacts, and ledger chain verify after commit.
- No merge requirement depends on GitHub Code Security, paid CodeQL publication, paid dependency review, or another paid security product.
