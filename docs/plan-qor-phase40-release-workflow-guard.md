# Plan: Phase 40 — release workflow main-reachability guard

**change_class**: hotfix
**target_version**: v0.28.1
**doc_tier**: minimal
**pass**: 1

**Scope**: One workflow-step addition. Hotfix for pre-existing latent defect that allowed pre-merge publishes to PyPI for v0.24.1, v0.25.0, and v0.28.0.

**Rationale**: `.github/workflows/release.yml` publishes to PyPI on any `v*.*.*` tag push, with no check that the tag's commit is reachable from `origin/main`. This allowed tags pushed from unmerged branches to ship to PyPI. Historical incidents: v0.24.1 (PR #6 open), v0.25.0 (PR #7 open), v0.28.0 (PR #8 open at push time). The procedural-surface freeze established in v0.28.0 is undermined if workflow gates are absent.

## Open Questions

None.

## Phase 1 — workflow guard

### Affected Files

- `.github/workflows/release.yml` — add "Verify tag reachable from main" step immediately after `actions/checkout@v4`, before any publish step.
- `tests/test_release_workflow_guard.py` — NEW. Structural lint: workflow file contains the guard step.

### Changes

`release.yml` step addition (after `actions/checkout@v4`, before `python -m build`):

```yaml
      - name: Verify tag reachable from main
        run: |
          git fetch origin main --depth=100
          if ! git merge-base --is-ancestor "$GITHUB_SHA" origin/main; then
            echo "::error::Tag ${GITHUB_REF_NAME} points at ${GITHUB_SHA} which is not reachable from origin/main. Publish refused."
            exit 1
          fi
```

- `fetch-depth: 0` on the checkout step already ensures full history is present; `git fetch origin main` refreshes the main ref.
- `merge-base --is-ancestor` exits 0 iff `$GITHUB_SHA` is an ancestor of `origin/main` (i.e., the tag's commit has been merged to main).
- On failure, the job exits non-zero with a clear `::error::` annotation. No PyPI upload occurs because subsequent steps do not run.

### Unit Tests (TDD — written first)

- `tests/test_release_workflow_guard.py::test_release_workflow_has_main_reachability_guard` — NEW. Parses `release.yml` as YAML; asserts the `build-and-publish` job contains a step whose `run` block calls `git merge-base --is-ancestor` against `origin/main`.
- `tests/test_release_workflow_guard.py::test_release_workflow_guard_runs_before_publish` — NEW. Asserts the guard step's index in the job's `steps` list is less than the `pypa/gh-action-pypi-publish` step's index.

## CI Commands

- `pytest tests/test_release_workflow_guard.py` — targeted
- `pytest` — full suite at seal
- `python -m qor.reliability.gate_skill_matrix` — handoff integrity (no skill changes; should be unchanged)
