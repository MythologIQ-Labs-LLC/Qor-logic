# Plan: Phase 298 - Close Dependency Review SBOM path coverage gap

**change_class**: hotfix

**doc_tier**: standard

**Issue**: GH #511

**Current base**: `15729311f9f4d55d5dad2db004b972415c39432c`

## Problem

The repository's `PR Dependency Review` workflow is intended to block unsafe dependency changes, but its `pull_request.paths` filter watches only `pyproject.toml`, `requirements-release.txt`, and workflow files.

The governed root dependency surface is broader:

- `requirements-release.in`
- `requirements-release.txt`
- `requirements-sbom.in`
- `requirements-sbom.txt`

PR #496 changes only `requirements-sbom.txt`. Because that path is absent from the filter, neither `actions/dependency-review-action` nor the hard-fail dependency-admission cooling-period check can execute. The existing regression test preserves the same blind spot.

PR #512 already demonstrated the bounded workflow/test correction, but that PR used a non-canonical `fix/...` branch and a non-phase plan filename. Qor's canonical `current_phase_plan_path()` resolver therefore cannot admit it to `/qor-audit`. Phase 298 recomposes the same correction into the governance runtime's canonical branch/plan shape, starting plan-first so the normal audit -> implement sequence remains intact.

## Locked Decisions

### LD-1: both dependency inputs and generated locks are gate-bearing

A dependency can enter through an `.in` declaration or through a generated `.txt` lock update. Both are supply-chain-relevant and both must trigger Dependency Review.

### LD-2: the workflow path set is explicit and complete

`pull_request.paths` must cover all five governed root dependency-bearing files:

- `pyproject.toml`
- `requirements-release.in`
- `requirements-release.txt`
- `requirements-sbom.in`
- `requirements-sbom.txt`

Workflow self-coverage through `.github/workflows/**` remains required.

### LD-3: policy semantics do not change

This slice does not change dependency versions, `fail-on-severity`, the cooling-period policy, override semantics, or the dependency-review action pin. It repairs trigger coverage only.

### LD-4: #496 remains blocked until the repaired gate can run

The absence of a Dependency Review run on #496 is evidence that the gate did not execute, not evidence that the dependency change passed. Re-evaluate #496 only after this correction is accepted on `main` and its workflow can trigger on `requirements-sbom.txt`.

### LD-5: canonical governance shape is part of the fix

The work lives on `phase/298-dependency-review-sbom-path-coverage` and this file is the canonical `docs/plan-qor-phase298-*.md` plan consumed by Qor's phase resolver. The branch remains plan-only until `/qor-audit` returns PASS. Only then should `/qor-implement` apply the already-bounded workflow/test changes under TDD-Light.

No ledger, gate, intent-lock, HMAC, or Merkle evidence is hand-authored through GitHub. Admission must pass the repository's real `/qor-audit` and `/qor-substantiate` path on a writable checkout.

## Affected Files

Planned implementation after PASS:

- `.github/workflows/pr-dependency-review.yml`
- `tests/test_pr_dependency_review_workflow.py`

Current planning artifact:

- `docs/plan-qor-phase298-dependency-review-sbom-path-coverage.md`

## Test Contract

Before changing the workflow, extend `tests/test_pr_dependency_review_workflow.py::test_workflow_triggers_on_dependency_paths` so it requires all five governed root dependency paths and verify that test fails against the pre-fix workflow. Then add the missing paths and verify the focused test passes.

Existing tests must continue to require the SHA-pinned dependency-review action, workflow self-coverage, hard-fail cooling-period behavior, and `high` severity enforcement.

## CI Commands

- `python -m pytest tests/test_pr_dependency_review_workflow.py -q`
- `python -m pytest tests/ -q`
- `python -m qor.scripts.check_variant_drift`
- `python -m qor.scripts.publication_boundary_lint`

## Non-goals

- dependency version changes;
- dependency-policy redesign;
- weakening or bypassing Dependency Review;
- merging #496 through the pre-fix enforcement gap;
- hand-issuing governance evidence;
- unrelated repository cleanup.

## Definition of Done

- GH #511 acceptance criteria are satisfied;
- PRs changing `requirements-release.in`, `requirements-release.txt`, `requirements-sbom.in`, `requirements-sbom.txt`, or `pyproject.toml` trigger `PR Dependency Review`;
- workflow self-coverage remains intact;
- the regression test locks the complete governed dependency path set;
- exact-head CI, SAST, and PR Dependency Review pass after implementation;
- the canonical Phase 298 branch/plan enters the real Qor audit/implement/substantiation runtime in order;
- promotion occurs only after truthful current-revision governance evidence exists.
