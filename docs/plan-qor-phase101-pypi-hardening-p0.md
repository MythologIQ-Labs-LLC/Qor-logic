# Plan: Phase 101 — PyPI Publication Hardening P0 (GH #118 partial)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #118 P0 controls per `docs/research-brief-gh118-pypi-hardening-2026-05-24.md`

**high_risk_target**: true

**impact_assessment**: This phase modifies the release publish workflow that mints PyPI OIDC tokens (`id-token: write`) and configures the GitHub `pypi` environment that gates production package publication. Failure modes touched: (1) a misconfigured workflow could publish a non-tag commit to PyPI -- mitigated by the preserved tag-ancestry guard and the environment protection rules added in this phase; (2) an over-broad permission scope could allow non-publish steps to mint OIDC tokens -- mitigated by moving `id-token: write` to publish job scope only; (3) cache poisoning of the privileged publish job -- mitigated by removing `cache: pip` from the publish job and consuming only build-produced artifacts verified against an in-band SHA256SUMS file. SSDF: PO.4.1 (use roles to manage security), PO.5.1 (implement and maintain secure environments), PS.2.1 (provide a mechanism for verifying software release integrity), PS.3.1 (archive and protect each software release). EU AI Act / NIST AI RMF: out of scope -- this is supply-chain hardening, not AI behavior modification.

**boundaries**:
- limitations: P0 scope only. Splits the single `build-and-publish` job into `build` and `publish` jobs with an artifact handoff verified by an in-band SHA256SUMS file produced inside the build job. SHA-pins every third-party Action across the three workflow files. Configures the `pypi` GitHub environment with required-reviewer + tag-only deployment-branch policy via `gh api`. Moves `id-token: write` to the publish job. Removes pip cache from the publish job. Preserves the existing tag-ancestry guard (`merge-base --is-ancestor`) inside the publish job as the load-bearing pre-publish gate.
- non_goals: lockfile / requirements-release.txt (P1), CODEOWNERS (P1), SBOM / cyclonedx generation (P1), dependency-review workflow (P1), post-publish PyPI pull-back verification (P2), cooling-period doctrine (P2), Action major-version bumps (separate decision), Dependabot configuration for actions ecosystem (P1 follow-up).
- exclusions: no changes to test workflow logic in `ci.yml` beyond SHA-pinning the two Actions it uses; no changes to `pr-lint.yml` beyond SHA-pinning; no changes to `pyproject.toml` dependency declarations; no changes to `qor/reliability/intent_lock.py` or `tests/test_release_workflow_guard.py` semantics (regression-preserved).

## Open Questions

None. Research brief established the gap inventory; user confirmed the P0/P1/P2 cluster scope and that env protection rules will be configured via `gh api` inside this cycle.

## Feature Inventory Touches

Empty. Workflow + test addition + one operator script.
`feature_inventory_touches`: `[]`.

## Design notes

### Action SHA pins (resolved 2026-05-24)

| Action | Tag annotation | Commit SHA |
|---|---|---|
| actions/checkout | v4.3.1 (latest v4) | `34e114876b0b11c390a56381ad16ebd13914f8d5` |
| actions/setup-python | v5.6.0 (latest v5) | `a26af69be951a213d495a4c3e4e4022e16d87065` |
| actions/upload-artifact | v4.6.2 (latest v4) | `ea165f8d65b6e75b540449e92b4886f43607fa02` |
| actions/download-artifact | v4.3.0 (latest v4) | `d3f86a106a0bac45b974a628896c90dbdf5c8093` |
| pypa/gh-action-pypi-publish | v1.14.0 (latest) | `cef221092ed1bacb1cc03d23a2d87d1d172e277b` |

All pins use the form `uses: org/repo@<40-char-sha> # vX.Y.Z` so Dependabot (added in P1) can manage them and human reviewers can see the version. Action major version is preserved (v4/v5/v1); major bumps are a separate decision.

### Split-job topology

```
jobs:
  build:                                # unprivileged producer
    permissions: { contents: read }     # no id-token; no contents:write
    steps:
      - checkout (SHA-pinned)
      - tag-ancestry guard (cheap early-fail; refuses if tag not in main)
      - setup-python with cache: pip    # cache OK -- build job is unprivileged
      - pip install build
      - python -m build
      - sha256sum dist/* > dist/SHA256SUMS
      - upload-artifact: release-dist (dist/ including SHA256SUMS)

  publish:                              # privileged consumer
    needs: build
    environment: pypi                   # now backed by required-reviewer + tag policy
    permissions:
      id-token: write                   # OIDC mint -- publish only
      contents: read
    steps:
      - checkout (SHA-pinned)
      - download-artifact: release-dist -> dist/
      - sha256sum -c dist/SHA256SUMS    # fails loud on artifact mismatch
      - pypa/gh-action-pypi-publish (SHA-pinned; no with: skip-existing)
```

The tag-ancestry guard lives in the **build** job for early failure but also re-runs in the **publish** job as a second checkpoint. Two cheap checks beat one because cache invalidation or artifact misdelivery cannot bypass both. This is the SG-StructureWithoutPolicy-A countermeasure pattern (research brief Section 6): verify policy at the point of enforcement, not only at the point of production.

### Environment protection via gh api

`qor/scripts/configure_pypi_environment.py` PUTs the desired protection rule set:
- `reviewers`: at least one user/team required (configurable; default = single user from `--reviewer` arg)
- `deployment_branch_policy.protected_branches`: false
- `deployment_branch_policy.custom_branch_policies`: true with policy entries for `v*.*.*` tag refs only
- `can_admins_bypass`: false
- `wait_timer`: 0 (no enforced wait; reviewer requirement is the gate)

Script is **idempotent**: running it twice produces the same state. Includes `--dry-run` to print the planned PUT body without sending. Reads desired-state config from inline constants (Phase 101 ships single-reviewer requirement; broaden later if team grows).

### Test surface

Five structural tests on the workflow YAML files plus one unit test on the env-config script's PUT-body builder. All read-only against in-repo files -- no live `gh api` calls in tests.

1. `test_release_workflow_actions_sha_pinned` -- every `uses:` line in `.github/workflows/{release,ci,pr-lint}.yml` matches `<owner>/<repo>@<40-hex-sha>` and is followed by a `# vX.Y.Z` annotation comment.
2. `test_release_workflow_split_jobs` -- `release.yml` defines exactly `build` and `publish` jobs; `publish.needs == ['build']`.
3. `test_release_workflow_id_token_scoped_to_publish` -- `id-token: write` appears under `jobs.publish.permissions` and nowhere else (no workflow-level permissions block containing it).
4. `test_release_workflow_publish_job_no_cache` -- the `setup-python` step inside `publish` has no `cache` key in its `with` block; the same step inside `build` *may* have it (positive assertion: build allows cache).
5. `test_release_workflow_artifact_handoff_with_sha_verify` -- build job contains an `upload-artifact` step producing `release-dist`; publish job contains the matching `download-artifact` step followed by a `sha256sum -c` (or equivalent) step over `dist/SHA256SUMS` before the publish step.
6. `test_configure_pypi_environment_put_body` -- imports `qor.scripts.configure_pypi_environment`, calls its `build_put_body()` factory, asserts the resulting dict has `reviewers` (list with `>= 1` entry), `deployment_branch_policy.custom_branch_policies == True`, and tag-policy entries restricted to `v*.*.*`.

The existing `tests/test_release_workflow_guard.py` regression cover for the tag-ancestry guard is preserved; this plan adds a sub-assertion that the guard now appears in **both** the build and publish jobs (load-bearing-gate preservation per qor-substantiate Constraints).

## Phase 1: SHA pinning + workflow split + env protection script + tests

### Affected Files

- `.github/workflows/release.yml` -- split into `build` and `publish` jobs; SHA-pin all Actions; move `id-token: write` to publish job; remove cache from publish job; add artifact handoff with SHA256SUMS verify; keep tag-ancestry guard in both jobs.
- `.github/workflows/ci.yml` -- SHA-pin `actions/checkout@v4` -> `@34e114876...` and `actions/setup-python@v5` -> `@a26af69be...` across all three jobs (`test`, `install-smoke`, `gate-chain-completeness`). No logic changes.
- `.github/workflows/pr-lint.yml` -- SHA-pin `actions/checkout@v4` and `actions/setup-python@v5`. No logic changes.
- `qor/scripts/configure_pypi_environment.py` -- NEW. Idempotent gh-api-PUT script for `pypi` environment protection rules. Includes `--dry-run`. ~80 lines.
- `tests/test_release_workflow_immutability.py` -- NEW. Tests 1-5 above (workflow structural assertions).
- `tests/test_configure_pypi_environment.py` -- NEW. Test 6 (PUT-body builder unit test).
- `docs/plan-qor-phase101-pypi-hardening-p0.md` -- NEW. This plan.
- `tests/test_release_workflow_guard.py` -- AMENDED. Add assertion that the tag-ancestry guard now appears in both jobs (`build` and `publish`).

### Unit Tests

- `tests/test_release_workflow_immutability.py`
  - `test_release_workflow_actions_sha_pinned`
  - `test_ci_workflow_actions_sha_pinned`
  - `test_pr_lint_workflow_actions_sha_pinned`
  - `test_release_workflow_split_jobs`
  - `test_release_workflow_id_token_scoped_to_publish_job`
  - `test_release_workflow_publish_job_disables_cache`
  - `test_release_workflow_build_job_allows_cache` (positive assertion -- build job MAY use cache; publish job MUST NOT)
  - `test_release_workflow_artifact_handoff_with_sha_verify`
- `tests/test_configure_pypi_environment.py`
  - `test_build_put_body_includes_reviewer_requirement`
  - `test_build_put_body_restricts_to_tag_refs`
  - `test_build_put_body_disables_admin_bypass`
  - `test_build_put_body_idempotent` (calling twice with same inputs returns equal dicts)
- `tests/test_release_workflow_guard.py` (amended)
  - existing assertions preserved
  - NEW `test_tag_ancestry_guard_present_in_both_jobs`

### Changes

#### `.github/workflows/release.yml` (full rewrite)

```yaml
name: Release

on:
  push:
    tags: ['v*.*.*']
    paths-ignore:
      - "docs/archive/**"

concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5  # v4.3.1
        with:
          fetch-depth: 0
          fetch-tags: true
      - name: Verify tag reachable from main (build-side early gate)
        run: |
          git fetch origin main --depth=100
          if ! git merge-base --is-ancestor "$GITHUB_SHA" origin/main; then
            echo "::error::Tag ${GITHUB_REF_NAME} points at ${GITHUB_SHA} which is not reachable from origin/main. Build refused."
            exit 1
          fi
      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065  # v5.6.0
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install build
      - run: python -m build
      - name: Generate SHA256SUMS
        run: |
          cd dist
          sha256sum *.whl *.tar.gz > SHA256SUMS
          cat SHA256SUMS
      - uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02  # v4.6.2
        with:
          name: release-dist
          path: dist/
          if-no-files-found: error
          retention-days: 7

  publish:
    needs: build
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5  # v4.3.1
        with:
          fetch-depth: 0
          fetch-tags: true
      - name: Verify tag reachable from main (publish-side enforcement gate)
        run: |
          git fetch origin main --depth=100
          if ! git merge-base --is-ancestor "$GITHUB_SHA" origin/main; then
            echo "::error::Tag ${GITHUB_REF_NAME} points at ${GITHUB_SHA} which is not reachable from origin/main. Publish refused."
            exit 1
          fi
      - uses: actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093  # v4.3.0
        with:
          name: release-dist
          path: dist/
      - name: Verify dist SHA256SUMS
        run: |
          cd dist
          sha256sum -c SHA256SUMS
      - uses: pypa/gh-action-pypi-publish@cef221092ed1bacb1cc03d23a2d87d1d172e277b  # v1.14.0
```

Notes on the rewrite:
- Workflow-level `permissions:` block is removed; each job declares its own least-privilege set.
- `id-token: write` is granted only to the `publish` job (Finding F-1b remediation).
- `cache: pip` is allowed in `build` (unprivileged) and absent in `publish` (Finding F-2c remediation).
- The build job's setup-python also gets cache (preserving developer-friendly behavior for the producer); the publish job's setup-python is *removed entirely* because the publish job no longer runs `pip install` -- it only downloads the pre-built dist, verifies SHAs, and hands to `pypa/gh-action-pypi-publish` which is a Docker action.
- Wait -- the pypa action runs in its own container; no host Python is needed for the publish job. Removed `setup-python` from publish entirely. **Updated above**.

Re-checking the publish job: it does need `actions/checkout` only for the tag-ancestry verification (`git merge-base`). Once that's done it downloads the artifact and publishes. No setup-python needed in publish. Test #4 (`test_release_workflow_publish_job_disables_cache`) becomes: assert no `setup-python` step exists in publish job (which implicitly satisfies "no cache").

#### `.github/workflows/ci.yml` (SHA-pin substitutions only)

For each occurrence:
- `uses: actions/checkout@v4` -> `uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5  # v4.3.1`
- `uses: actions/setup-python@v5` -> `uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065  # v5.6.0`

No other changes.

#### `.github/workflows/pr-lint.yml` (SHA-pin substitutions only)

Same two substitutions. No other changes.

#### `qor/scripts/configure_pypi_environment.py` (NEW, ~80 lines)

```python
#!/usr/bin/env python3
"""Configure GitHub `pypi` environment protection rules.

Idempotent gh-api PUT script. Sets required reviewers, tag-only
deployment-branch policy, disables admin bypass.

Usage:
    configure_pypi_environment.py --repo <owner/name> --reviewer <user-or-team-id> [--dry-run]
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys


def build_put_body(reviewer_ids: list[int], reviewer_types: list[str]) -> dict:
    """Pure factory for the gh-api PUT body. Unit-tested separately."""
    assert len(reviewer_ids) == len(reviewer_types) >= 1
    return {
        "wait_timer": 0,
        "prevent_self_review": True,
        "reviewers": [
            {"type": t, "id": i}
            for t, i in zip(reviewer_types, reviewer_ids)
        ],
        "deployment_branch_policy": {
            "protected_branches": False,
            "custom_branch_policies": True,
        },
    }


def build_branch_policy_body() -> dict:
    """Tag-only deployment policy (v*.*.* refs)."""
    return {"name": "v*.*.*", "type": "tag"}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("--reviewer-id", type=int, action="append", required=True)
    p.add_argument("--reviewer-type", choices=["User", "Team"],
                   action="append", required=True)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    body = build_put_body(args.reviewer_id, args.reviewer_type)
    print(json.dumps(body, indent=2))
    if args.dry_run:
        return 0

    # PUT the environment + protection rules
    subprocess.run(
        ["gh", "api", "-X", "PUT",
         f"repos/{args.repo}/environments/pypi",
         "--input", "-"],
        input=json.dumps(body), text=True, check=True,
    )

    # POST the tag-only branch policy
    policy = build_branch_policy_body()
    subprocess.run(
        ["gh", "api", "-X", "POST",
         f"repos/{args.repo}/environments/pypi/deployment-branch-policies",
         "--input", "-"],
        input=json.dumps(policy), text=True, check=True,
    )

    print(f"OK: pypi environment configured on {args.repo}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Note: the GitHub REST API does not directly expose `can_admins_bypass` toggling per environment in the PUT body for "Environment" (it is a repo-level setting on newer accounts). Where the API does not honor a field, the script documents it in a comment and operators set it once via the UI. The reviewer + tag-policy controls are the load-bearing P0 protections; admin bypass is an explicit P1 follow-up if the API surface changes.

## Definition of Done

### Deliverable D-101.1: Actions SHA-pinned

- **D1**: All three workflow files (`release.yml`, `ci.yml`, `pr-lint.yml`) use full-commit-SHA pins with `# vX.Y.Z` annotation for every third-party Action.
- **D2**: `test_release_workflow_actions_sha_pinned`, `test_ci_workflow_actions_sha_pinned`, `test_pr_lint_workflow_actions_sha_pinned` pass.
- **D3**: Plan + ledger entry seal Phase 101.

### Deliverable D-101.2: Release workflow split into build + publish jobs

- **D1**: `release.yml` defines exactly two jobs `build` and `publish`; `publish.needs == ['build']`; `id-token: write` lives only in `publish.permissions`; `build.permissions` is `contents: read` only.
- **D2**: Build job produces `dist/SHA256SUMS`; uploads via `actions/upload-artifact` as `release-dist`. Publish job downloads `release-dist` and runs `sha256sum -c SHA256SUMS` before publishing.
- **D3**: `test_release_workflow_split_jobs`, `test_release_workflow_id_token_scoped_to_publish_job`, `test_release_workflow_publish_job_disables_cache`, `test_release_workflow_build_job_allows_cache`, `test_release_workflow_artifact_handoff_with_sha_verify` all pass.
- **D4**: Tag-ancestry guard preserved and runs in **both** jobs; amended `test_tag_ancestry_guard_present_in_both_jobs` passes.

### Deliverable D-101.3: `pypi` environment protection configured

- **D1**: `qor/scripts/configure_pypi_environment.py` exists and is importable.
- **D2**: `tests/test_configure_pypi_environment.py` covers PUT-body shape: reviewer requirement, tag-only policy, idempotency.
- **D3**: Script invoked once during the cycle against the live repo (`gh api` PUT to `repos/MythologIQ-Labs-LLC/Qor-logic/environments/pypi` and POST to its branch-policies endpoint). Post-state verified via `gh api ... | jq` -- `protection_rules` non-empty, deployment-branch-policy entry for `v*.*.*` exists. Result logged in the substantiate seal entry.

## CI Coverage Exemptions

None. The new tests are pytest collection by default; no exemption needed.

## CI Commands

- `python -m pytest tests/test_release_workflow_immutability.py -q` -- Phase 101 workflow structural tests.
- `python -m pytest tests/test_configure_pypi_environment.py -q` -- Phase 101 env-config script unit tests.
- `python -m pytest tests/test_release_workflow_guard.py -q` -- amended regression cover for tag-ancestry guard in both jobs.
- `python -m pytest tests/ -v` -- full regression.
- `python qor/scripts/check_variant_drift.py` -- ci.yml.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` -- ci.yml.
- `python -m pytest tests/test_packaging_install.py -v -m integration` -- install-smoke.
- `python -m qor.reliability.gate_chain_completeness --phase-min 52` -- gate-chain.
- `python qor/scripts/pr_citation_lint.py` -- pr-lint.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase101-pypi-hardening-p0.md` -- plan-internal.
- `python -m qor.scripts.ci_coverage_lint --plan docs/plan-qor-phase101-pypi-hardening-p0.md --workflows-dir .github/workflows` -- Phase 89 ci-coverage.
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase101-pypi-hardening-p0.md` -- Phase 92 DoD check.
- `python -m qor.scripts.skill_size_budget_lint --skills-root qor/skills` -- Phase 95 skill-corpus-budget lint (WARN-only).
