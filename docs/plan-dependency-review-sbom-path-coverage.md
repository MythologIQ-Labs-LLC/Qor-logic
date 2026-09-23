# Plan: Close Dependency Review SBOM path coverage gap

**change_class**: hotfix

**doc_tier**: standard

**Issue**: GH #511

**Current base**: `c12c7d2ef34d83b4a2c44bdb8fe5f8403f648e86`

## Problem Contract

The repository's `PR Dependency Review` workflow is intended to block unsafe dependency changes, but its `pull_request.paths` filter currently watches only `pyproject.toml`, `requirements-release.txt`, and workflow files.

The governed dependency surface is broader. The repository carries both release and SBOM input/lock pairs:

- `requirements-release.in`
- `requirements-release.txt`
- `requirements-sbom.in`
- `requirements-sbom.txt`

PR #496 changes only `requirements-sbom.txt`. Because that path is absent from the filter, the dependency-review action and the hard-fail dependency-admission cooling-period check never run. The existing workflow regression test also requires only the incomplete subset, so CI currently preserves the blind spot.

## Change Contract

### Authorized scope

- Extend `.github/workflows/pr-dependency-review.yml` so dependency review triggers for all four root dependency input/lock files plus `pyproject.toml`.
- Strengthen `tests/test_pr_dependency_review_workflow.py::test_workflow_triggers_on_dependency_paths` so the complete governed dependency path set is required.
- Preserve workflow-file self-coverage via `.github/workflows/**`.

### Explicit exclusions

- No dependency version changes in this slice.
- No change to `fail-on-severity` or cooling-period policy.
- No override-policy change.
- No merge of PR #496 until the repaired gate has an opportunity to execute against SBOM lock changes.
- No broader supply-chain redesign.

## Locked Decisions

### LD-1: Both source inputs and generated lockfiles are gate-bearing

A dependency can enter through an `.in` declaration or through a generated `.txt` lock update. Both are supply-chain-relevant and both must trigger the review workflow.

### LD-2: The test must enumerate the complete governed root path set

The regression should fail if any of the five root dependency-bearing paths is removed from `pull_request.paths`:

- `pyproject.toml`
- `requirements-release.in`
- `requirements-release.txt`
- `requirements-sbom.in`
- `requirements-sbom.txt`

### LD-3: #496 remains evidence for the defect, not an exception to it

The fact that #496 is otherwise green does not justify merging through the missing gate. It should be re-evaluated after this workflow correction lands.

## Affected Files

- `.github/workflows/pr-dependency-review.yml`
- `tests/test_pr_dependency_review_workflow.py`

## Definition of Done

- D1: PRs touching either release dependency file trigger `PR Dependency Review`.
- D2: PRs touching either SBOM dependency file trigger `PR Dependency Review`.
- D3: `pyproject.toml` and workflow self-coverage remain intact.
- D4: The workflow regression requires all governed dependency paths.
- D5: Full CI is green on the exact branch head.
- D6: Current-base governance evidence is established before promotion.

## CI Commands

- `python -m pytest tests/test_pr_dependency_review_workflow.py -q`
- `python -m pytest tests/ -q`
- `python -m qor.scripts.check_variant_drift`
- `python -m qor.scripts.publication_boundary_lint`

## Promotion Rule

Do not use the pre-fix absence of a Dependency Review run on #496 as evidence that the dependency bump passed the gate. The gate did not execute.