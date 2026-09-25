# Plan: Phase 298 - Close Dependency Review SBOM path coverage gap

**change_class**: hotfix

**doc_tier**: minimal

**Issue**: GH #511

**Current base**: `15729311f9f4d55d5dad2db004b972415c39432c`

## Open Questions

None.

## Problem

The repository's `PR Dependency Review` workflow is intended to block unsafe dependency changes, but its `pull_request.paths` filter watches only `pyproject.toml`, `requirements-release.txt`, and workflow files.

The governed root dependency surface is broader:

- `requirements-release.in`
- `requirements-release.txt`
- `requirements-sbom.in`
- `requirements-sbom.txt`

PR #496 changes only `requirements-sbom.txt`. Because that path is absent from the filter, neither `actions/dependency-review-action` nor the hard-fail dependency-admission cooling-period check can execute. The existing regression test preserves the same blind spot.

PR #512 demonstrated the bounded workflow/test correction, but its non-phase branch and plan filename could not enter Qor's canonical audit resolver. Phase 298 recomposes the same correction in canonical governance shape and starts plan-first so the normal audit -> implement -> substantiate sequence remains intact.

## Locked Decisions

### LD-1: both dependency inputs and generated locks are gate-bearing

A dependency can enter through an `.in` declaration or through a generated `.txt` lock update. Both are supply-chain-relevant and both must trigger Dependency Review.

The current base proves the trigger surface is incomplete:

`git show 15729311f9f4d55d5dad2db004b972415c39432c:.github/workflows/pr-dependency-review.yml | grep -nE 'pyproject.toml|requirements-(release|sbom)'` -> `9:      - "pyproject.toml"` and `10:      - "requirements-release.txt"`; there are no `requirements-release.in`, `requirements-sbom.in`, or `requirements-sbom.txt` matches.

### LD-2: the workflow path set is explicit and complete

`pull_request.paths` must cover all five governed root dependency-bearing files:

- `pyproject.toml`
- `requirements-release.in`
- `requirements-release.txt`
- `requirements-sbom.in`
- `requirements-sbom.txt`

Workflow self-coverage through `.github/workflows/**` remains required.

The current regression confirms it only requires the incomplete subset:

`git show 15729311f9f4d55d5dad2db004b972415c39432c:tests/test_pr_dependency_review_workflow.py | grep -nE 'required_paths = '` -> `54:    required_paths = {"pyproject.toml", "requirements-release.txt"}`.

### LD-3: policy semantics do not change

This slice does not change dependency versions, `fail-on-severity`, the cooling-period policy, override semantics, or the dependency-review action pin. It repairs trigger coverage only.

### LD-4: #496 remains blocked until the repaired gate can run

The absence of a Dependency Review run on #496 is evidence that the gate did not execute, not evidence that the dependency change passed. Re-evaluate #496 only after this correction is accepted on `main` and its workflow can trigger on `requirements-sbom.txt`.

### LD-5: canonical governance shape is part of the fix

The work lives on `phase/298-dependency-review-sbom-path-coverage` and this file is the canonical `docs/plan-qor-phase298-*.md` plan consumed by Qor's phase resolver. The branch remains plan-only until `/qor-audit` returns PASS. Only then may `/qor-implement` apply the bounded workflow/test changes under TDD-Light.

The resolver contract on the current base is explicit:

`git show 15729311f9f4d55d5dad2db004b972415c39432c:qor/scripts/governance_helpers.py | grep -nE '_BRANCH_PHASE_RE =|def current_phase_plan_path|Not on a phase branch|plan-qor-phase\{nn\}'` -> `23:_BRANCH_PHASE_RE = re.compile(r"^phase/(\d+)-")`, `57:def current_phase_plan_path(docs_dir: Path | None = None) -> Path:`, `62:        raise InterdictionError(f"Not on a phase branch: {branch!r}")`, `64:    candidates = sorted(docs_dir.glob(f"plan-qor-phase{nn}*.md"))`.

No ledger, gate, intent-lock, HMAC, or Merkle evidence is hand-authored through GitHub. Admission must pass the repository's real `/qor-audit` and `/qor-substantiate` path on a writable checkout.

## Feature Inventory Touches

Empty. This is workflow/test maintenance and introduces no `src/` or user-touchable product feature surface.

`feature_inventory_touches`: `[]`.

## Phase 1: Regression test

### Affected Files

- `tests/test_pr_dependency_review_workflow.py` - strengthen the dependency-path trigger regression.

### Changes

Expand `test_workflow_triggers_on_dependency_paths` so its required path set includes all five governed root dependency-bearing files while retaining the existing assertion that `.github/workflows/**` remains covered.

### Unit Tests

- `tests/test_pr_dependency_review_workflow.py::test_workflow_triggers_on_dependency_paths` - parses the real workflow YAML and fails when any governed dependency path is absent. Run this test against the pre-fix workflow and observe RED before changing workflow logic.

## Phase 2: Workflow trigger coverage

### Affected Files

- `.github/workflows/pr-dependency-review.yml` - add the three missing dependency-bearing root paths.

### Changes

Add exactly:

- `requirements-release.in`
- `requirements-sbom.in`
- `requirements-sbom.txt`

Preserve every existing trigger path and all job semantics unchanged.

### Unit Tests

- Re-run `tests/test_pr_dependency_review_workflow.py::test_workflow_triggers_on_dependency_paths` after the workflow edit and observe GREEN.
- Run the full `tests/test_pr_dependency_review_workflow.py` file to prove the action remains SHA-pinned, `fail-on-severity: high` remains intact, workflow self-coverage remains intact, and the cooling-period check stays hard-fail.

## Definition of Done

### Deliverable: complete Dependency Review root-path coverage

- **D1**: every governed root dependency declaration or lockfile change enters `PR Dependency Review` rather than bypassing it by path filtering.
- **D2**: `.github/workflows/pr-dependency-review.yml` names `pyproject.toml`, `requirements-release.in`, `requirements-release.txt`, `requirements-sbom.in`, and `requirements-sbom.txt` under `pull_request.paths`, while preserving `.github/workflows/**` and all existing job semantics.
- **D3**: Phase 298 follows canonical phase branch/plan resolution and receives truthful current-revision audit/substantiation evidence before promotion; no governance evidence is synthesized through the GitHub API.
- **D4**: `tests/test_pr_dependency_review_workflow.py::test_workflow_triggers_on_dependency_paths` is RED before the workflow edit and GREEN afterward, and the full workflow test file passes on the implemented revision.

## CI Commands

- `python -m pytest tests/test_pr_dependency_review_workflow.py -q` - verifies the complete trigger set and unchanged dependency-review enforcement semantics.
- `python -m pytest tests/ -q` - verifies repository regression safety.
- `python -m qor.scripts.check_variant_drift` - verifies installed/generated variant consistency.
- `python -m qor.scripts.publication_boundary_lint` - verifies the publication-boundary surface remains clean.

## Non-goals

- dependency version changes;
- dependency-policy redesign;
- weakening or bypassing Dependency Review;
- merging #496 through the pre-fix enforcement gap;
- hand-issuing governance evidence;
- unrelated repository cleanup.
