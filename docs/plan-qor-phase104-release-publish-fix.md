# Plan: Phase 104 — Release publish-step fix + Dependabot config (v0.72.0 hotfix)

**change_class**: hotfix

**doc_tier**: standard

**originating_remediation**: Phase 101-103 cluster published a release workflow where the build job placed non-distribution files (SHA256SUMS in Phase 101; SBOM and evidence.json in Phase 102+) inside `dist/`. `pypa/gh-action-pypi-publish` uploads every file in `dist/`, so it tried to upload `SHA256SUMS` and failed with `InvalidDistribution: Unknown distribution format: 'SHA256SUMS'`. All three releases (v0.69.0, v0.70.0, v0.71.0) failed at the publish step; nothing reached PyPI. Phase 104 fixes the bug and ships the cluster work plus the Dependabot carry-forward as v0.72.0.

**high_risk_target**: true

**impact_assessment**: This phase modifies the same release publish workflow Phase 101 created. Failure modes touched: (1) repeat of the original bug — mitigated by adding a structural test asserting the publish step uses a separate `packages-dir` containing only distribution files; (2) accidental inclusion of yet more non-dist files in future phases — mitigated by the same test which inverts to verify the prepared publish dir excludes specific known non-dist names. SSDF: PS.2.1, PS.3.1, RV.1.1. EU AI Act / NIST AI RMF: out of scope (supply-chain fix).

**boundaries**:
- limitations: Hotfix scope only. Adds a step that copies only `*.whl` and `*.tar.gz` from `dist/` to a sibling `dist-publish/` directory; points `pypa/gh-action-pypi-publish` at `dist-publish/` via its `packages-dir` parameter. Downstream evidence-assembly + pull-back + `gh release create` steps continue to operate on `dist/` (which still contains the auxiliary files). Folds the previously-staged Dependabot configuration (`.github/dependabot.yml`) into the same hotfix branch so the carry-forward from the cluster lands in one PR. Bumps version 0.71.0 -> 0.72.0; CHANGELOG entry documents the v0.69-v0.71 publish failures and the Phase 104 fix.
- non_goals: rewriting the per-version v0.69/v0.70/v0.71 tags or commits (the user-confirmed recovery path is a single v0.72.0 hotfix; the failed tags remain as historical artifacts); deleting the failed remote tags (leave them as a paper trail of the failed first-attempt publish workflow); broaden CODEOWNERS reviewer pool; cyclonedx-bom hash-pinning; automated dependency-admission lint (still deferred carry-forward).
- exclusions: no changes to SHA pins or workflow topology established in Phase 101; no changes to the lockfile/CODEOWNERS established in Phase 102; no changes to the pull-back step or doctrine established in Phase 103; no version reuse on PyPI (versions 0.69.0/0.70.0/0.71.0 are skipped on PyPI; v0.72.0 is the next published version).

## Open Questions

None. User confirmed Path 1 (hotfix as v0.72.0) when shown the recovery option matrix.

## Feature Inventory Touches

Empty. Workflow edit + Dependabot config + ledger + tests.
`feature_inventory_touches`: `[]`.

## Design notes

### The bug

`pypa/gh-action-pypi-publish` (v1.14.0 SHA-pinned) uploads every file in its `packages-dir` (default `dist/`) to PyPI. In the Phase 101+ build job, `dist/` contains:

- Phase 101: `*.whl`, `*.tar.gz`, `SHA256SUMS`
- Phase 102: + `sbom.json`, `evidence.json`
- Phase 103: same as Phase 102 (evidence.json is assembled in the publish job before the publish step, also into `dist/`)

The publish step fails on the first non-distribution file it encounters. Observed failure for v0.69.0:

```
Checking dist/qor_logic-0.69.0-py3-none-any.whl: PASSED
Checking dist/SHA256SUMS: ERROR InvalidDistribution: Unknown distribution format: 'SHA256SUMS'
```

### The fix

Add a step **between** `Assemble evidence bundle` and `pypa/gh-action-pypi-publish` that:
1. Creates a sibling `dist-publish/` directory
2. Copies only `*.whl` and `*.tar.gz` from `dist/`

Point the publish action at `dist-publish/` via `with.packages-dir: dist-publish/`. Downstream steps (pull-back, evidence-attach, gh release create) keep reading from `dist/`.

```yaml
      - name: Prepare publish-only directory (Phase 104 fix)
        run: |
          set -euo pipefail
          mkdir -p dist-publish
          cp dist/*.whl dist/*.tar.gz dist-publish/
          ls -la dist-publish/
      - uses: pypa/gh-action-pypi-publish@cef221092ed1bacb1cc03d23a2d87d1d172e277b  # v1.14.0
        with:
          packages-dir: dist-publish/
```

The separation is the structural countermeasure: `dist/` is the *assembly* directory; `dist-publish/` is the *delivery* directory. Files added to `dist/` by future phases never leak into the publish payload.

### Dependabot config carry-forward

`.github/dependabot.yml` was authored as a separate hygiene PR (#122) but closed because the PR-citation-lint requires a plan file path + Merkle seal, neither of which a standalone hygiene PR carried. Folding it into this hotfix's commit attaches it to Phase 104's plan + seal, clearing the lint.

### Test surface

Two new test functions on the workflow-immutability assertions, plus the existing Phase 101/102/103 tests remain unchanged.

1. `test_release_workflow_publish_uses_separate_packages_dir` -- publish step uses `with.packages-dir` pointing at a path that is NOT `dist/` (defense-in-depth: any value other than `dist/` is acceptable, the prepare step is the actual control)
2. `test_release_workflow_publish_only_dir_excludes_non_dist_files` -- the prepare step asserts: copies `*.whl` and `*.tar.gz` only; does NOT copy `SHA256SUMS`, `sbom.json`, or `evidence.json` into `dist-publish/`
3. `test_dependabot_config_exists_for_actions_and_pip` -- NEW; asserts `.github/dependabot.yml` declares updates for both `github-actions` and `pip` ecosystems

## Phase 1: release.yml fix + Dependabot config + tests

### Affected Files

- `.github/workflows/release.yml` -- amended. Add `Prepare publish-only directory` step; add `with.packages-dir: dist-publish/` to the pypa-publish step. No other changes.
- `.github/dependabot.yml` -- NEW (carry-forward from closed PR #122). Weekly schedule for github-actions and pip ecosystems.
- `tests/test_release_workflow_immutability.py` -- amended. +2 tests on the publish-only directory pattern.
- `tests/test_dependabot_config.py` -- NEW. 3 tests asserting Dependabot config validity.
- `docs/plan-qor-phase104-release-publish-fix.md` -- NEW. This plan.

### Unit Tests

- `tests/test_release_workflow_immutability.py` (amended)
  - `test_release_workflow_publish_uses_separate_packages_dir`
  - `test_release_workflow_publish_only_dir_excludes_non_dist_files`
- `tests/test_dependabot_config.py` (NEW)
  - `test_dependabot_config_file_exists`
  - `test_dependabot_config_covers_actions_and_pip_ecosystems`
  - `test_dependabot_config_uses_supported_schedule_intervals`

## Definition of Done

### Deliverable D-104.1: release workflow publish-step fix

- **D1**: `release.yml` publish job carries a `Prepare publish-only directory` step that copies only `*.whl` and `*.tar.gz` from `dist/` to `dist-publish/`, immediately before the pypa-publish step.
- **D2**: pypa-publish step declares `with.packages-dir: dist-publish/`.
- **D3**: `test_release_workflow_publish_uses_separate_packages_dir` and `test_release_workflow_publish_only_dir_excludes_non_dist_files` pass.

### Deliverable D-104.2: Dependabot carry-forward

- **D1**: `.github/dependabot.yml` exists with `github-actions` and `pip` ecosystem entries, weekly schedule.
- **D2**: All three `test_dependabot_config*` tests pass.

## CI Coverage Exemptions

None.

## CI Commands

- `python -m pytest tests/test_release_workflow_immutability.py -q` -- amended for Phase 104.
- `python -m pytest tests/test_dependabot_config.py -q` -- Phase 104 Dependabot config tests.
- `python -m pytest tests/ -v` -- full regression.
- `python qor/scripts/check_variant_drift.py` -- ci.yml.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` -- ci.yml.
- `python -m pytest tests/test_packaging_install.py -v -m integration` -- install-smoke.
- `python -m qor.reliability.gate_chain_completeness --phase-min 52` -- gate-chain.
- `python qor/scripts/pr_citation_lint.py` -- pr-lint.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase104-release-publish-fix.md` -- plan-internal.
- `python -m qor.scripts.ci_coverage_lint --plan docs/plan-qor-phase104-release-publish-fix.md --workflows-dir .github/workflows` -- Phase 89 ci-coverage.
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase104-release-publish-fix.md` -- Phase 92 DoD check.
- `python -m qor.scripts.skill_size_budget_lint --skills-root qor/skills` -- Phase 95 skill-corpus-budget lint (WARN-only).
