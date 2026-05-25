# Phase 101: PyPI Publication Hardening P0 (GH #118 partial)

Closes 5 of 13 acceptance items from #118 (F-1a, F-1b, F-1c, F-2a, F-2c).

## Summary

Workflow-side controls for PyPI trusted publishing. Three independent ancestry legs of supply-chain integrity now operative (per research brief `docs/research-brief-gh118-pypi-hardening-2026-05-24.md`):

- **commit-ancestry** — existing `git merge-base --is-ancestor origin/main` guard preserved and now replicated in both jobs.
- **artifact-ancestry** (NEW) — in-band `dist/SHA256SUMS` produced by the unprivileged build job, verified via `sha256sum -c` by the privileged publish job before `pypa/gh-action-pypi-publish` runs.
- **workflow-ancestry** (NEW) — every third-party Action SHA-pinned to a 40-hex commit with `# vX.Y.Z` annotation; the `pypi` GitHub environment now backed by required-reviewer + tag-only deployment policy + prevent-self-review.

## Changes

### `.github/workflows/release.yml` — rewritten

- Split single `build-and-publish` job into `build` (unprivileged, `contents: read`, `cache: pip` allowed) and `publish` (`id-token: write`, `environment: pypi`, `needs: build`, no setup-python step, no cache).
- Build job generates `dist/SHA256SUMS` and uploads `release-dist` artifact (7-day retention).
- Publish job downloads artifact, runs `sha256sum -c SHA256SUMS`, then publishes.
- Tag-ancestry guard runs in BOTH jobs.

### Workflow Actions SHA-pinned

| Action | Pin | Annotation |
|---|---|---|
| actions/checkout | `34e114876b0b11c390a56381ad16ebd13914f8d5` | `# v4.3.1` |
| actions/setup-python | `a26af69be951a213d495a4c3e4e4022e16d87065` | `# v5.6.0` |
| actions/upload-artifact | `ea165f8d65b6e75b540449e92b4886f43607fa02` | `# v4.6.2` |
| actions/download-artifact | `d3f86a106a0bac45b974a628896c90dbdf5c8093` | `# v4.3.0` |
| pypa/gh-action-pypi-publish | `cef221092ed1bacb1cc03d23a2d87d1d172e277b` | `# v1.14.0` |

Applied to `release.yml`, `ci.yml`, `pr-lint.yml`. Worst prior pin was a mutable branch ref (`pypa/gh-action-pypi-publish@release/v1`).

### `qor/scripts/configure_pypi_environment.py` (NEW)

Idempotent gh-api wrapper that PUTs `repos/.../environments/pypi` with required-reviewer policy + tag-only deployment-branch policy + prevent-self-review. Pure factory `build_put_body()` is unit-tested in isolation; the live `gh api` call is gated behind `--dry-run`. Invoked once during this cycle; post-state verified.

### Tests (16 new + 1 amended; +47 LOC each, all green twice deterministically)

- `tests/test_release_workflow_immutability.py` (NEW, 8 tests)
- `tests/test_configure_pypi_environment.py` (NEW, 7 tests)
- `tests/test_release_workflow_guard.py` (amended: `test_tag_ancestry_guard_present_in_both_jobs`)

Full regression: 1894 passed, 1 skipped, 4 deselected.

### Documentation

- `docs/plan-qor-phase101-pypi-hardening-p0.md` (NEW)
- `docs/research-brief-gh118-pypi-hardening-2026-05-24.md` (NEW)
- `docs/META_LEDGER.md` entries #272 (research brief), #273 (audit PASS L3 iter-1), #274 (implementation), #275 (session seal v0.69.0, Merkle `ee7ccae5...`)
- `docs/SHADOW_GENOME.md` — new entry "Supply-chain Gap Inventory (GH #118 Scope)" with candidate pattern `SG-StructureWithoutPolicy-A` (second observed instance after Phase 52 gate-chain bypass)
- `docs/SYSTEM_STATE.md` — Phase 101 section
- `CHANGELOG.md` — `## [0.69.0]`
- `pyproject.toml` — `version = "0.69.0"`
- `README.md` — Tests badge 1879 → 1895; Ledger badge 271 → 275

### Live mutation

`gh api repos/MythologIQ-Labs-LLC/Qor-logic/environments/pypi` PUT + the matching deployment-branch-policies POST were executed once via the new script during this cycle. Verified post-state: `protection_rule_count == 2`, `reviewer_logins == ["Knapp-Kevin"]`, `prevent_self_review == true`, `deployment_branch_policy.custom_branch_policies == true`, single `v*.*.*` tag policy. `can_admins_bypass` remains `true` — not API-exposed for the environment PUT body; documented manual UI follow-up.

## Test plan

- [ ] CI green: `Release` workflow triggers on tag push only; build + publish jobs both reach success on next release tag
- [ ] Manual: confirm at least one reviewer is required to deploy to `pypi` environment in repo settings
- [ ] Manual: disable `can_admins_bypass` in repo settings -> Environments -> pypi (one-time UI step; not API-exposed)
- [ ] CI green: existing `ci.yml` and `pr-lint.yml` workflows pass with their new SHA-pinned Actions

## Carry-forward (cluster continuation)

Phase 102 (P1, ahead): hash-pinned `requirements-release.txt`, CODEOWNERS, SBOM + GH release evidence bundle, `dependency-review-action` workflow. Phase 103 (P2, ahead): post-publish PyPI pull-back hash compare + `qor/references/doctrine-dependency-admission.md`. Cluster closes GH #118 fully after Phase 103 seal.

## Citations

- Plan: `docs/plan-qor-phase101-pypi-hardening-p0.md`
- Audit: `.agent/staging/phase101-AUDIT_REPORT.md` (PASS, L3 iter-1)
- Research: `docs/research-brief-gh118-pypi-hardening-2026-05-24.md`
- META_LEDGER entries: #272, #273, #274, #275
- Merkle seal: `ee7ccae53d8330a8d69704e59da1086c04b9b06ec9a5207f0ba9a567bb09655e`

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
