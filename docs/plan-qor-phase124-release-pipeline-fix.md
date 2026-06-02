# Plan: Release pipeline fix — unblock tag releases + manual dispatch for the backlog

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: Fixes the broken release trigger and adds a manual dispatch path. Two edits to `.github/workflows/release.yml`: (1) remove `paths-ignore` from the `on.push.tags` trigger (GitHub skips path-filtered `push` workflows on tag pushes, which has silently skipped every release since v0.85); (2) add `workflow_dispatch` with a `tag` input so the *fixed* workflow (from the default branch) can build+publish a historical tag whose own commit still carries the broken trigger. Both jobs check out the resolved ref and derive VERSION + the reachability guard from the checked-out HEAD. The publish/verify/SBOM/evidence steps and all SHA-pinned actions are unchanged.
- non_goals: Re-tagging historical seal commits; changing the version-from-pyproject build; altering the PyPI environment / OIDC; republishing already-published versions (<= v0.84.0).
- exclusions: n/a (CI-config + tests only).

## Open Questions

None. Root cause confirmed: `paths-ignore` on a tag-only push (no file diff) makes GitHub skip the Release workflow; introduced with the #142 Actions bump after v0.84.0, so v0.85-v0.90 never released. Because a tag push runs the workflow file *from the tagged commit* (which still has the broken trigger), the historical backlog is published via `workflow_dispatch -f tag=<vX.Y.Z>` (runs the corrected workflow from `main`, checks out the tag to build the right version). Removing `paths-ignore` repairs future seal-tag pushes.

## Context

CI gates on `main` are green and seal tags v0.85-v0.90 exist (v0.87-v0.90 pushed), but GH Releases + PyPI are stuck at v0.84.0: six sealed versions are unpublished. The Release workflow has not fired on any tag since v0.85 due to the `paths-ignore` trigger interaction. This phase repairs the delivery gate and provides the dispatch path to clear the backlog.

## Feature Inventory Touches

(`docs/FEATURE_INDEX.md` absent; declared for traceability. CI-config + tests only.)

- entry_id: `n/a` · operation: `NEW` · test_path: `tests/test_release_workflow_dispatch.py` · test_descriptor: `release.yml on.push.tags has no paths-ignore, declares workflow_dispatch with a tag input, and both build+publish jobs check out the resolved ref (inputs.tag || github.ref_name)`

## Phase 1: release.yml trigger fix + dispatch

### Affected Files

- `tests/test_release_workflow_dispatch.py` - NEW. Structural/functional assertions on the parsed workflow YAML (see Unit Tests). Written first; red before the edit.
- `.github/workflows/release.yml` - remove `paths-ignore` from `on.push.tags`; add `on.workflow_dispatch.inputs.tag`; both jobs: `actions/checkout` `with: ref: ${{ inputs.tag || github.ref_name }}`; replace `${GITHUB_REF_NAME}` VERSION/release-name derivation with a resolved `REF` (`${{ inputs.tag || github.ref_name }}`); reachability guard checks `git rev-parse HEAD` (the checked-out tag commit) instead of `${GITHUB_SHA}` so dispatch validates the tag, not the dispatch branch.

### Changes

The `on` block becomes:

```yaml
on:
  push:
    tags: ['v*.*.*']
  workflow_dispatch:
    inputs:
      tag:
        description: "Existing tag to build + publish (e.g. v0.87.0)"
        required: true
        type: string
```

Each job's checkout gains `ref: ${{ inputs.tag || github.ref_name }}`; the reachability guard becomes `SHA=$(git rev-parse HEAD); git merge-base --is-ancestor "$SHA" origin/main || exit 1`; VERSION and `gh release create` use `REF="${{ inputs.tag || github.ref_name }}"`. Preserves: split build/publish jobs, both reachability guards (guard-before-publish), SHA-pinned `uses:` with `# vX.Y.Z` annotations, PyPI pull-back verification, evidence bundle.

### Unit Tests

- `tests/test_release_workflow_dispatch.py::test_tag_trigger_has_no_paths_ignore` - load release.yml; assert `on.push.tags` exists and `on.push` has no `paths-ignore` key (the fix; the bug was its presence).
- `::test_workflow_dispatch_with_tag_input` - assert `on.workflow_dispatch.inputs.tag` exists with `required: true`.
- `::test_both_jobs_checkout_resolved_ref` - assert the first `actions/checkout` step in BOTH `build` and `publish` jobs sets `with.ref` to a value containing `inputs.tag`.
- `::test_reachability_guard_uses_checked_out_head` - assert both jobs still contain a reachability guard and it references `git rev-parse HEAD` (validates the tag under dispatch, not the trigger branch).
- `::test_actions_still_sha_pinned` - assert every `uses:` in release.yml matches `owner/repo@<40-hex>` (immutability preserved by the edit; guards against accidental un-pinning).

## Definition of Done

### Deliverable: release pipeline fix

- **D1**: tag pushes again trigger the Release workflow, and any historical tag can be published via `workflow_dispatch -f tag=<vX.Y.Z>`.
- **D2**: `release.yml` `on.push.tags` has no `paths-ignore`; `workflow_dispatch.inputs.tag` present; both jobs checkout `${{ inputs.tag || github.ref_name }}`; guard uses `git rev-parse HEAD`.
- **D3**: META_LEDGER seal entry; version bump; existing `test_release_workflow_immutability.py` + `test_release_workflow_guard.py` still green.
- **D4**: `tests/test_release_workflow_dispatch.py::test_tag_trigger_has_no_paths_ignore` + `::test_workflow_dispatch_with_tag_input` + `::test_both_jobs_checkout_resolved_ref`.

### Deliverable: backlog publish (post-merge, operator-gated)

- **D1**: v0.85-v0.90 published to PyPI + GH Releases via dispatch after the fix is on `main`.
- **D4.d**: not unit-testable (live PyPI publish). **Follow-up**: executed manually post-merge as `gh workflow run release.yml -f tag=vX.Y.Z` per version, verified via the workflow's own PyPI pull-back gate.

## CI Commands

- `python -m pytest tests/test_release_workflow_dispatch.py tests/test_release_workflow_immutability.py tests/test_release_workflow_guard.py -q` — new + preserved workflow contracts.
- `python -m pytest -q` — full suite green before substantiate.
