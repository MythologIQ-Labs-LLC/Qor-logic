# Research Brief — GH #118 PyPI Publication Hardening

**Date**: 2026-05-24
**Analyst**: The Qor-logic Analyst
**Target**: Supply-chain controls for `qor-logic` PyPI trusted publishing (open GitHub issue scope)
**Scope**: Release-evidence, publication-authority, workflow-immutability, dependency-admission, IOC review per issue #118 acceptance criteria

---

## Executive Summary

Only one open issue exists (#118). It demands four control categories for PyPI trusted publishing: publication authority, workflow immutability, dependency admission, release evidence. **Twelve of thirteen explicit acceptance items currently DRIFT from desired state.** IOC sweep returned clean (5/5 PASS). The existing release-ancestry verification logic referenced by the issue is present at `release.yml:26-32` and `qor/reliability/intent_lock.py` and must be preserved as the reference implementation. Two HIGH-severity gaps drive risk: unpinned third-party Actions (tag refs only, not SHA-pinned) and a fully unpinned dependency chain (no lockfile, range-pinned PyPI deps).

## Findings

### 1. Publication Authority

#### Finding 1a: PyPI environment exists but has no protection rules
- **Location**: GitHub repo environment `pypi` (created 2026-04-16T14:49:42Z)
- **Source**: `gh api repos/MythologIQ-Labs-LLC/Qor-logic/environments`
- **Actual state**: `"protection_rules": []`, `"deployment_branch_policy": null`, `"can_admins_bypass": true`
- **Required**: Required reviewers and/or branch policy gating publication
- **Status**: **DRIFT (HIGH)** — environment is declared in `release.yml:20` (`environment: pypi`) but enforces nothing

#### Finding 1b: `id-token: write` scoped at workflow level, not publish job
- **Location**: `.github/workflows/release.yml:9-11`
- **Actual**:
  ```yaml
  permissions:
    id-token: write
    contents: read
  ```
  (workflow-level; applies to all jobs and all steps)
- **Required**: `id-token: write` only on final publish job/step; build job should run with `contents: read` only
- **Status**: **DRIFT** — currently the checkout, build, and publish steps all hold the OIDC mint permission

#### Finding 1c: Build and publish in single job; no artifact handoff
- **Location**: `.github/workflows/release.yml:18-39`
- **Actual**: One `build-and-publish` job runs `python -m build` then `pypa/gh-action-pypi-publish` in the same job. No `upload-artifact`/`download-artifact` and no hash verification between produce and publish.
- **Required**: Build artifacts in unprivileged job, upload, then publish in a separately-privileged job that re-verifies artifact hashes before upload
- **Status**: **DRIFT**

### 2. Workflow Immutability

#### Finding 2a: Third-party Actions tag-pinned, not SHA-pinned
- **Location**: `.github/workflows/release.yml` (3 actions), `.github/workflows/ci.yml` (2 actions repeated across 3 jobs), `.github/workflows/pr-lint.yml` (2 actions)
- **Actual pins**:
  - `actions/checkout@v4` (mutable tag)
  - `actions/setup-python@v5` (mutable tag)
  - `pypa/gh-action-pypi-publish@release/v1` (mutable branch ref — worst of three)
- **Required**: Full 40-char commit SHA with `# v4.x.x` comment annotation
- **Status**: **DRIFT (HIGH)** — `pypa/gh-action-pypi-publish@release/v1` is a branch ref, which is mutable on every push to that branch by the action maintainer

#### Finding 2b: No CODEOWNERS file
- **Location**: `**/CODEOWNERS` glob returned no matches
- **Required**: CODEOWNERS protecting `.github/workflows/**`, `pyproject.toml`, and any future lockfile
- **Status**: **DRIFT**

#### Finding 2c: Publish job uses pip cache (untrusted cache surface)
- **Location**: `.github/workflows/release.yml:33-36`
- **Actual**: `cache: pip` enabled on the same job that holds `id-token: write`
- **Required**: Privileged publish job must not consume restorable cache state
- **Status**: **DRIFT** — cache should be disabled on the publish job (or moved to a separate unprivileged build job)

### 3. Dependency Admission

#### Finding 3a: No dependency-review workflow
- **Location**: No matches in `.github/workflows/` for `dependency-review-action`
- **Required**: `actions/dependency-review-action` enforced on PRs touching dependencies
- **Status**: **DRIFT**

#### Finding 3b: No lockfile; dependencies range-pinned
- **Location**: `pyproject.toml:25,28` and `.github/workflows/release.yml:37`
- **Actual**:
  - Runtime: `dependencies = ["jsonschema>=4", "PyYAML>=6"]` (unbounded upper)
  - Dev: `dev = ["pytest>=8"]` (unbounded upper)
  - Build step: `pip install build` (no version, no hash)
  - No `requirements.txt`, no `uv.lock`, no `pip-tools` artefact (verified via `**/*.lock` glob — only `.claude/scheduled_tasks.lock` and a doc lock unrelated to packaging)
- **Required**: Deterministic, hash-pinned install in the release pipeline
- **Status**: **DRIFT (HIGH)** — combined with 2a, the publish job has no integrity anchor on its own dependency tree

#### Finding 3c: No cooling-period policy
- **Location**: No policy doc found in `qor/references/` or `docs/`
- **Required**: Stated minimum age before a newly-published transitive dependency may enter the release dependency tree
- **Status**: **DRIFT**

### 4. Release Evidence

#### Finding 4a: No SBOM / artifact-hash / evidence-bundle production
- **Location**: `.github/workflows/release.yml:38-39`
- **Actual**: `python -m build` then `pypa/gh-action-pypi-publish` — no `cyclonedx`/`syft` invocation, no `sha256sum dist/*` recording, no GitHub release with attached evidence
- **Required**: Produce SBOM, record artifact hashes, attach evidence bundle to GitHub release for each `v*.*.*` tag
- **Status**: **DRIFT**

#### Finding 4b: No post-publish verification
- **Location**: `.github/workflows/release.yml` (workflow ends at publish step)
- **Actual**: No step that downloads from PyPI and compares hash to local `dist/*` outputs
- **Required**: Post-publish pull-back and hash compare
- **Status**: **DRIFT**

#### Finding 4c: No recording of workflow SHA, action SHAs, lockfile hashes
- **Location**: Workflow run logs only; no persisted artefact in repo or release
- **Required**: Per-release record of `GITHUB_SHA`, resolved action commit SHAs, and lockfile hash (once a lockfile exists)
- **Status**: **DRIFT**

### 5. IOC Review

| Indicator | Result |
|---|---|
| `setup_bun.js` | NOT FOUND (PASS) |
| `bun_environment.js` | NOT FOUND (PASS) |
| `/tmp/transformers.pyz` (any `transformers.pyz`) | NOT FOUND (PASS) |
| Unexpected release mutations | None observed — workflow history shows tag-driven publishes consistent with `v*.*.*` (PASS) |
| Unexpected publication events | None (PASS) |

### 6. Existing Reference Implementation (preserve)

The issue states: *"This repository already contains release ancestry verification logic and should act as the reference implementation."* Confirmed components, all to remain in place:

- **Tag-reachable-from-main guard**: `.github/workflows/release.yml:26-32` (`git merge-base --is-ancestor` check; refuses publish if tag commit not in `origin/main` history)
- **Intent Lock**: `qor/reliability/intent_lock.py:1-30` (SHA-256 fingerprint of plan + audit + HEAD captured at audit time, re-verified at substantiate time)
- **Substantiate tag-push timing**: `tests/test_substantiate_tag_push_timing.py`, `tests/test_release_workflow_guard.py` (regression coverage for the ancestry guard)
- **Gate-chain completeness**: `.github/workflows/ci.yml:56-74` (`gate_chain_completeness --phase-min 52` — refuses merge if sealed phases lack gate artifacts)

These provide the *commit-ancestry* leg of supply-chain integrity; #118 demands the *artifact-ancestry* leg (SBOM, hashes, post-publish verify) and the *workflow-ancestry* leg (SHA pins, lockfile, CODEOWNERS) on top.

## Blueprint Alignment

| Blueprint Claim | Actual Finding | Status |
|---|---|---|
| `release.yml` enforces release-ancestry guard | Tag-reachable-from-main step present | MATCH |
| `environment: pypi` gates publication | Environment exists but has zero protection rules | DRIFT |
| Third-party Actions are version-pinned | All Actions tag-pinned (`@v4`/`@v5`/`@release/v1`), not SHA-pinned | DRIFT |
| Dependencies are deterministically installed | No lockfile; range pins; `pip install build` unpinned | DRIFT |
| Publish job runs with least privilege | `id-token: write` granted workflow-wide; cache enabled on publish | DRIFT |
| Release produces audit-grade evidence | No SBOM, no artifact-hash record, no post-publish verify | DRIFT |
| CODEOWNERS protects workflows/manifests | No CODEOWNERS file exists | DRIFT |

## Recommendations

Recommendations are advisory; routing to `/qor-plan` is the Governor's call. Ordered by exploit risk × ease of remediation:

1. **(P0, low effort) SHA-pin all third-party Actions across the three workflow files.** Replace `actions/checkout@v4` etc. with full commit SHAs plus `# v4.x.x` annotation. Add a Dependabot config for `github-actions` ecosystem to manage updates.
2. **(P0, low effort) Configure environment protection on `pypi`.** Require at least one reviewer; set deployment branch policy to `v*.*.*` tag refs only; disable admin bypass.
3. **(P0, medium effort) Split `build-and-publish` into two jobs.** Build job: `contents: read` only, `cache: pip` allowed, uploads `dist/` artifact. Publish job: depends on build, no cache, `id-token: write`, downloads artifact, re-verifies SHA-256 of each `dist/*` file against a manifest produced by build job, then runs `pypa/gh-action-pypi-publish` (SHA-pinned).
4. **(P1, medium effort) Introduce hash-pinned install for the publish job.** Generate `requirements-release.txt` (or equivalent) with `--require-hashes`; install with `pip install --require-hashes -r requirements-release.txt` in the publish job. Build step (`pip install build`) gets the same treatment.
5. **(P1, low effort) Add CODEOWNERS.** Owners required for `.github/workflows/**`, `pyproject.toml`, `requirements-release.txt` (once created), and `qor/reliability/intent_lock.py`.
6. **(P1, medium effort) Generate SBOM + hash manifest + GitHub release evidence bundle.** Add `cyclonedx-py` (or `syft`) invocation in build job; publish job attaches SBOM, `SHA256SUMS`, resolved action SHAs, and `GITHUB_SHA` to a `gh release create` step post-publish.
7. **(P1, low effort) Add `actions/dependency-review-action` to a new `pr-dependency-review.yml`** triggering on PRs that touch `pyproject.toml`, `requirements-release.txt`, or `.github/workflows/**`.
8. **(P2, low effort) Add post-publish verification step** in publish job: pull just-published version from PyPI, compute SHA-256, compare to manifest, fail loud on mismatch.
9. **(P2, doc-only) Author cooling-period doctrine.** New `qor/references/doctrine-dependency-admission.md` defining minimum age threshold for new transitive dependencies and procedure for emergency overrides.

## Updated Knowledge

New entries to add to `docs/SHADOW_GENOME.md` (narrative archaeology, supply-chain section):

- **2026-05-24 — Supply-chain gap inventory (GH #118 scope)**: PyPI publish workflow inherits release-ancestry guard but lacks artifact-ancestry and workflow-ancestry controls. Twelve of thirteen acceptance criteria DRIFT at investigation time. No active IOCs. The `pypi` GitHub environment was created 2026-04-16 but never had protection rules attached — a classic "structure exists, policy absent" pattern (same anti-pattern shape as the gate-chain bypass that drove Phase 52).

---

_Research complete. Findings are advisory — implementation decisions remain with the Governor._
