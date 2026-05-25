# Plan: Phase 102 — PyPI Publication Hardening P1 (GH #118 partial)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #118 P1 controls per `docs/research-brief-gh118-pypi-hardening-2026-05-24.md`

**high_risk_target**: true

**impact_assessment**: This phase adds the dependency + evidence layer of supply-chain integrity to the release pipeline that Phase 101 split into build/publish jobs. Failure modes touched: (1) unpinned transitive dependency drift could publish a release built against a different dep tree than tested -- mitigated by hash-pinned `requirements-release.txt` consumed under `pip install --require-hashes` in the build job; (2) a malicious or vulnerable dependency entering via PR could ship to PyPI -- mitigated by the new `dependency-review-action` workflow blocking such PRs at review time; (3) a published artifact has no machine-readable provenance record for downstream consumers or auditors -- mitigated by SBOM generation (`cyclonedx-py`) + evidence bundle (action SHAs, lockfile hash, GITHUB_SHA, artifact SHA-256) attached to the GitHub release; (4) workflow / manifest / lockfile changes could merge without informed review -- mitigated by CODEOWNERS attaching required-reviewer enforcement to those paths. SSDF: PO.4.1, PS.2.1, PS.3.1, PS.3.2, PW.4.1, PW.4.4, RV.1.1. EU AI Act / NIST AI RMF: out of scope (supply-chain hardening, not AI behavior).

**boundaries**:
- limitations: P1 scope only. Adds `requirements-release.in` + `requirements-release.txt` (hash-pinned via pip-tools, consumed under `pip install --require-hashes`) to the build job. Adds `.github/CODEOWNERS` covering `/.github/workflows/`, `/pyproject.toml`, `/requirements-release.*`, `/qor/reliability/intent_lock.py`, `/qor/scripts/configure_pypi_environment.py`. Adds `.github/workflows/pr-dependency-review.yml` running `actions/dependency-review-action` on PRs that touch dependency-bearing files. Adds SBOM generation step (`cyclonedx-py`) in build job; adds evidence-bundle assembly step in publish job; attaches SBOM + SHA256SUMS + evidence.json to a GitHub release in the publish job.
- non_goals: post-publish PyPI pull-back verification (P2/Phase 103); cooling-period doctrine `qor/references/doctrine-dependency-admission.md` (P2/Phase 103); admin-bypass disable (still not API-exposed; UI follow-up); Action major-version bumps; Dependabot config for github-actions ecosystem (separate hygiene phase); broadening single-reviewer protection on `pypi` env (broaden as team grows, not in this phase); **hash-pinning the SBOM tool (`cyclonedx-bom`) itself** -- pragmatic deferral after lockfile generation: `cyclonedx-bom`'s transitive set (35 packages including `lxml`'s ~120 wheel hashes) would exceed the Section 4 Razor file budget (~250 lines) and push the lockfile past readable-diff size. The SBOM tool produces *metadata about* the released artifact, not the artifact itself; its install is lower-risk than the build pipeline producer. P1 hash-pins the producer (`build`); the SBOM tool gets a standard `pip install cyclonedx-bom` in CI. A future phase may revisit if cyclonedx-bom's surface stabilizes.
- exclusions: no changes to the build/publish job split topology established in Phase 101; no changes to SHA-pinned action versions (additions of `cyclonedx-py` action via `pip install` only, not a new third-party Action); no changes to `pyproject.toml` runtime dependencies (`jsonschema`, `PyYAML`) -- the lockfile is for build-time `build` package only.

## Open Questions

None. Research brief + Phase 101 ledger entry mapped the four P1 deliverables. User confirmed cluster scope and live `gh api` authorization in Phase 101 carries forward.

## Feature Inventory Touches

Empty. Workflow additions + new config files + tests.
`feature_inventory_touches`: `[]`.

## Design notes

### Lockfile architecture

`requirements-release.in` declares top-level build-time dep (`build`). `requirements-release.txt` is generated via `pip-compile --generate-hashes` and committed. CI's build job runs `pip install --require-hashes -r requirements-release.txt` (instead of bare `pip install build`). The lockfile covers `build` + its 3 transitive deps (`colorama`, `packaging`, `pyproject-hooks`) all hash-pinned to SHA-256. Regeneration is a documented operator step; the lockfile is treated as source-of-truth under CODEOWNERS protection.

### CODEOWNERS

Phase 102 ships with a single owner (`@Knapp-Kevin`) attached to the security-critical surfaces: workflow files, pyproject.toml, the new lockfile pair, the intent-lock script, the env-config script. Broaden once a maintainer team is provisioned.

### dependency-review workflow

New `.github/workflows/pr-dependency-review.yml` triggers on PR events that touch `pyproject.toml`, `requirements-release.txt`, or `.github/workflows/**`. Runs `actions/dependency-review-action` (SHA-pinned to v4) with default settings: fail on `high` severity, comment summary on the PR. License-allowlist deferred to a future hygiene phase.

### SBOM + evidence bundle

Build job adds two new steps after `python -m build` and before SHA256SUMS:
1. `pip install --require-hashes -r requirements-sbom.txt` (separate hash-pinned lockfile for `cyclonedx-bom`)
2. `cyclonedx-py environment --of JSON --output sbom.json` -- captures the build-environment dependency tree

Publish job adds an evidence-bundle step before `pypa/gh-action-pypi-publish` that produces `evidence.json` containing:
- `git_sha`: `$GITHUB_SHA`
- `tag`: `$GITHUB_REF_NAME`
- `workflow_run_id`: `$GITHUB_RUN_ID`
- `lockfile_sha256`: SHA-256 of `requirements-release.txt`
- `artifact_sha256sums`: contents of `dist/SHA256SUMS`
- `action_pins`: declared in the bundle as the SHA pins active for this run

After `pypa/gh-action-pypi-publish`, a final step uses `gh release create` to attach `dist/*`, `sbom.json`, `evidence.json`, and `SHA256SUMS` to a GitHub release at the tag. This produces the auditable evidence-bundle trail demanded by GH #118 F-4a / F-4c.

The evidence.json schema is hand-rolled; not a JSON Schema dependency. Format is stable and downstream-readable.

### Test surface

8 new tests across two files plus one amendment.

1. `tests/test_requirements_release_lockfile.py` (NEW)
   - `test_lockfile_pins_build_with_hash` -- assert `requirements-release.txt` declares `build==<v>` with at least two `--hash=sha256:` lines
   - `test_lockfile_hashes_are_sha256_format` -- every `--hash=` line uses `sha256:` prefix + 64-hex
   - `test_lockfile_covers_known_transitive_deps` -- assert presence of expected transitive deps (`colorama`, `packaging`, `pyproject-hooks`)
   - `test_release_workflow_build_job_uses_require_hashes` -- build job step references `pip install --require-hashes -r requirements-release.txt` (replaces the prior bare `pip install build`)

2. `tests/test_pr_dependency_review_workflow.py` (NEW)
   - `test_workflow_file_exists` -- `.github/workflows/pr-dependency-review.yml` present
   - `test_workflow_uses_dependency_review_action_sha_pinned` -- step uses `actions/dependency-review-action@<40-hex-sha>` with `# vX.Y.Z` annotation
   - `test_workflow_triggers_on_dependency_paths` -- `on.pull_request.paths` includes `pyproject.toml`, `requirements-release.txt`, `.github/workflows/**`

3. `tests/test_codeowners.py` (NEW)
   - `test_codeowners_file_exists` -- `.github/CODEOWNERS` present
   - `test_codeowners_covers_workflow_dir` -- a rule covering `/.github/workflows/`
   - `test_codeowners_covers_pyproject_and_lockfile` -- rules for `/pyproject.toml` and `/requirements-release.*`
   - `test_codeowners_covers_intent_lock_and_env_config` -- rules for the security-critical scripts

4. `tests/test_release_workflow_immutability.py` (AMENDED)
   - NEW `test_release_workflow_build_job_generates_sbom` -- build job contains a `cyclonedx-py` step that produces `sbom.json`
   - NEW `test_release_workflow_publish_job_assembles_evidence_bundle` -- publish job contains a step that writes `evidence.json` containing `git_sha`, `lockfile_sha256`, `artifact_sha256sums`
   - NEW `test_release_workflow_attaches_evidence_to_github_release` -- publish job contains a `gh release create` step that attaches `dist/*`, `sbom.json`, `evidence.json`, `SHA256SUMS`

Tests run twice deterministically. The new structural assertions follow the same "policy property = behavior for declarative config" pattern established in Phase 101.

## Phase 1: lockfile + CODEOWNERS + dependency-review + SBOM/evidence + tests

### Affected Files

- `requirements-release.in` -- NEW. Top-level build deps (`build`).
- `requirements-release.txt` -- NEW. Generated lockfile (hash-pinned).
- `.github/CODEOWNERS` -- NEW. ~12 lines.
- `.github/workflows/pr-dependency-review.yml` -- NEW. ~25 lines.
- `.github/workflows/release.yml` -- AMENDED. Build job: replace `pip install build` with `pip install --require-hashes -r requirements-release.txt`; add SBOM generation step. Publish job: add evidence-bundle assembly step; add `gh release create` attaching artifacts.
- `tests/test_requirements_release_lockfile.py` -- NEW. 4 tests.
- `tests/test_pr_dependency_review_workflow.py` -- NEW. 3 tests.
- `tests/test_codeowners.py` -- NEW. 4 tests.
- `tests/test_release_workflow_immutability.py` -- AMENDED. 3 new tests.
- `docs/plan-qor-phase102-pypi-hardening-p1.md` -- NEW. This plan.

### Unit Tests

See "Test surface" above. 14 new test functions + 1 amended file.

### Changes

#### `.github/CODEOWNERS` (NEW)

```
# Phase 102 (GH #118 P1): governance for security-critical files.
# Broaden once a maintainer team is provisioned.

/.github/workflows/                          @Knapp-Kevin
/.github/CODEOWNERS                          @Knapp-Kevin
/pyproject.toml                              @Knapp-Kevin
/requirements-release.in                     @Knapp-Kevin
/requirements-release.txt                    @Knapp-Kevin
/qor/reliability/intent_lock.py              @Knapp-Kevin
/qor/scripts/configure_pypi_environment.py   @Knapp-Kevin
```

#### `.github/workflows/pr-dependency-review.yml` (NEW)

```yaml
name: PR Dependency Review

on:
  pull_request:
    paths:
      - "pyproject.toml"
      - "requirements-release.txt"
      - ".github/workflows/**"

permissions:
  contents: read
  pull-requests: write

jobs:
  dependency-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5  # v4.3.1
      - uses: actions/dependency-review-action@<SHA-pin>  # v4.X.X
        with:
          fail-on-severity: high
          comment-summary-in-pr: on-failure
```

(SHA pin resolved at implementation time via live `gh api`.)

#### `.github/workflows/release.yml` (AMEND build + publish)

Build job step changes:
- Replace `pip install build` with `pip install --require-hashes -r requirements-release.txt`
- Add post-build step: `pip install cyclonedx-bom && cyclonedx-py environment --of JSON --output dist/sbom.json` (unpinned per non_goal: SBOM tool is metadata-only, not the released artifact)
- Upload-artifact already covers `dist/` so SBOM travels with the bundle

Publish job step additions (after `sha256sum -c SHA256SUMS`, before `pypa/gh-action-pypi-publish`):
- Assemble `dist/evidence.json` with `git_sha`, `tag`, `workflow_run_id`, `lockfile_sha256`, `artifact_sha256sums`, `action_pins` (hand-rolled jq + sha256sum + env)

Publish job step additions (after `pypa/gh-action-pypi-publish`):
- `gh release create "$GITHUB_REF_NAME" dist/*.whl dist/*.tar.gz dist/sbom.json dist/evidence.json dist/SHA256SUMS --generate-notes` (gated to only create if not already present; idempotent)

## Definition of Done

### Deliverable D-102.1: Hash-pinned build lockfile

- **D1**: `requirements-release.in` + `requirements-release.txt` committed; lockfile hash-pinned via pip-compile.
- **D2**: `release.yml` build job consumes via `pip install --require-hashes`.
- **D3**: `test_lockfile_pins_build_with_hash`, `test_lockfile_hashes_are_sha256_format`, `test_lockfile_covers_known_transitive_deps`, `test_release_workflow_build_job_uses_require_hashes` all pass.

### Deliverable D-102.2: CODEOWNERS

- **D1**: `.github/CODEOWNERS` committed with rules for workflows, pyproject, lockfile pair, intent_lock, env-config script.
- **D2**: All four CODEOWNERS tests pass.

### Deliverable D-102.3: PR dependency-review workflow

- **D1**: `.github/workflows/pr-dependency-review.yml` committed; SHA-pinned to `actions/dependency-review-action`.
- **D2**: All three dependency-review tests pass.

### Deliverable D-102.4: SBOM + evidence bundle

- **D1**: Build job generates `sbom.json` via cyclonedx-py and includes it in the uploaded artifact.
- **D2**: Publish job assembles `evidence.json` containing required fields and runs `gh release create` attaching `dist/*`, SBOM, evidence, and SHA256SUMS.
- **D3**: All three new amended-file tests pass.

## CI Coverage Exemptions

None.

## CI Commands

- `python -m pytest tests/test_requirements_release_lockfile.py -q` -- Phase 102 lockfile tests.
- `python -m pytest tests/test_pr_dependency_review_workflow.py -q` -- Phase 102 dep-review workflow tests.
- `python -m pytest tests/test_codeowners.py -q` -- Phase 102 CODEOWNERS tests.
- `python -m pytest tests/test_release_workflow_immutability.py -q` -- amended Phase 101 + 3 new Phase 102 tests.
- `python -m pytest tests/ -v` -- full regression.
- `python qor/scripts/check_variant_drift.py` -- ci.yml.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` -- ci.yml.
- `python -m pytest tests/test_packaging_install.py -v -m integration` -- install-smoke.
- `python -m qor.reliability.gate_chain_completeness --phase-min 52` -- gate-chain.
- `python qor/scripts/pr_citation_lint.py` -- pr-lint.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase102-pypi-hardening-p1.md` -- plan-internal.
- `python -m qor.scripts.ci_coverage_lint --plan docs/plan-qor-phase102-pypi-hardening-p1.md --workflows-dir .github/workflows` -- Phase 89 ci-coverage.
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase102-pypi-hardening-p1.md` -- Phase 92 DoD check.
- `python -m qor.scripts.skill_size_budget_lint --skills-root qor/skills` -- Phase 95 skill-corpus-budget lint (WARN-only).
