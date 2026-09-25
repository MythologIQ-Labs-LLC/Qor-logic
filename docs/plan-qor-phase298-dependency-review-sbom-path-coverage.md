# Plan: Phase 298 - Close Dependency Review SBOM path coverage gap

**change_class**: hotfix

**doc_tier**: minimal

**iteration**: 2 (amends iteration 1 per the VETO at META_LEDGER entry #809, grounds V1-V2, advisories A1-A3)

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

PR #496 changes only `requirements-sbom.txt`. Because that path is absent from the filter, the workflow never starts, so neither `actions/dependency-review-action` nor the hard-fail dependency-admission cooling-period step runs. The existing regression test preserves the same blind spot.

Widening the filter alone is not sufficient. The cooling-period step invokes `dependency_admission_lint` with `--base` only, and the lint examines exactly one lockfile, `requirements-release.txt` by default. After a filter-only fix, a `requirements-sbom.txt`-only PR would run the step and pass it with zero entries examined. That vacuous pass is the residual iteration 1 left open. This plan closes it by running the admission step once per governed root lockfile.

PR #512 demonstrated the bounded workflow/test correction, but its non-phase branch and plan filename could not enter Qor's canonical audit resolver. Phase 298 recomposes the correction in canonical governance shape and starts plan-first so the normal audit -> implement -> substantiate sequence remains intact.

## Locked Decisions

### LD-1: both dependency inputs and generated locks are gate-bearing

A dependency can enter through an `.in` declaration or through a generated `.txt` lock update. Both are supply-chain-relevant and both must trigger Dependency Review.

The current base proves the trigger surface is incomplete. The filter holds exactly these two dependency-bearing entries:

`git show 15729311f9f4d55d5dad2db004b972415c39432c:.github/workflows/pr-dependency-review.yml | grep -nE '"pyproject.toml"'` -> `9:      - "pyproject.toml"`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:.github/workflows/pr-dependency-review.yml | grep -nE '"requirements-release.txt"'` -> `10:      - "requirements-release.txt"`

The pattern `requirements-(release\.in|sbom)` has no match in that file at the base.

`requirements-sbom.txt` is a real release-build input:

`git show 15729311f9f4d55d5dad2db004b972415c39432c:.github/workflows/release.yml | grep -nE 'requirements-sbom.txt'` -> `59:          pip install --require-hashes -r requirements-sbom.txt`

### LD-2: the governed path set is derived, not enumerated

The governed root dependency surface is defined mechanically as: every repository-root file matching `requirements-*.in` or `requirements-*.txt`, plus `pyproject.toml`. At the base this yields exactly five files:

- `pyproject.toml`
- `requirements-release.in`
- `requirements-release.txt`
- `requirements-sbom.in`
- `requirements-sbom.txt`

The regression derives the set from the repository root at test time, so a future `requirements-<name>.in/.txt` pair that is not added to the workflow fails the test. It also asserts the five known files are members of the derived set, so the derivation cannot silently shrink. The workflow keeps an explicit path list (no glob), and self-coverage through `.github/workflows/**` remains required.

The current regression is the enumerated-subset shape GH #511 names:

`git show 15729311f9f4d55d5dad2db004b972415c39432c:tests/test_pr_dependency_review_workflow.py | grep -nE 'required_paths = '` -> `54:    required_paths = {"pyproject.toml", "requirements-release.txt"}`

### LD-3: policy semantics do not change

This slice does not change dependency versions, `fail-on-severity`, the 14-day cooling-period threshold, override semantics (META_LEDGER entry or `dep-admit-override` label), the hard-fail posture, or the dependency-review action pin. It changes no code under `qor/`. It repairs trigger coverage and makes the existing admission step examine every governed root lockfile through the lint's existing `--lockfile` argument.

### LD-4: #496 re-evaluation criterion

The absence of a Dependency Review run on #496 is evidence that the gate did not execute, not evidence that the dependency change passed. Re-evaluate #496 only after this correction is accepted on `main` and a `PR Dependency Review` run exists on #496's current head.

Admission evidence for #496 requires both: the `actions/dependency-review-action` step ran, and the `requirements-sbom.txt` admission step's output lists a `cyclonedx-bom` row. A green `requirements-sbom.txt` step whose output is `_No lockfile bumps detected._` is not admission evidence for #496 and must not be read as such. A `violation` row fails the step; admission then follows the doctrine's override procedure or waits out the window. This plan does not decide #496.

### LD-5: canonical governance shape is part of the fix

The work lives on `phase/298-dependency-review-sbom-path-coverage` and this file is the canonical `docs/plan-qor-phase298-*.md` plan consumed by Qor's phase resolver. The branch remains plan-only until `/qor-audit` returns PASS. Only then may `/qor-implement` apply the bounded changes under TDD-Light.

The resolver contract on the current base:

`git show 15729311f9f4d55d5dad2db004b972415c39432c:qor/scripts/governance_helpers.py | grep -nE '_BRANCH_PHASE_RE ='` -> `23:_BRANCH_PHASE_RE = re.compile(r"^phase/(\d+)-")`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:qor/scripts/governance_helpers.py | grep -nE 'def current_phase_plan_path'` -> `57:def current_phase_plan_path(docs_dir: Path | None = None) -> Path:`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:qor/scripts/governance_helpers.py | grep -nE 'Not on a phase branch'` -> `62:        raise InterdictionError(f"Not on a phase branch: {branch!r}")`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:qor/scripts/governance_helpers.py | grep -nE 'plan-qor-phase\{nn\}'` -> `64:    candidates = sorted(docs_dir.glob(f"plan-qor-phase{nn}*.md"))`

No ledger, gate, intent-lock, HMAC, or Merkle evidence is hand-authored through GitHub. Admission must pass the repository's real `/qor-audit` and `/qor-substantiate` path on a writable checkout.

### LD-6: one admission step per governed root lockfile

The lint's CLI entry point reads one lockfile, named by `--lockfile`, defaulting to `requirements-release.txt`, and diffs it against the same path at `--base`:

`git show 15729311f9f4d55d5dad2db004b972415c39432c:qor/scripts/dependency_admission_lint.py | grep -nE 'add_argument\("--lockfile"'` -> `241:    p.add_argument("--lockfile", default="requirements-release.txt")`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:qor/scripts/dependency_admission_lint.py | grep -nE 'current_path = repo_root'` -> `248:    current_path = repo_root / args.lockfile`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:qor/scripts/dependency_admission_lint.py | grep -nE 'base_text = _git_show'` -> `254:    base_text = _git_show(base_ref, args.lockfile, repo_root)`

The workflow step passes `--base` only, so it examines `requirements-release.txt` alone:

`git show 15729311f9f4d55d5dad2db004b972415c39432c:.github/workflows/pr-dependency-review.yml | grep -nE 'python -m qor.scripts.dependency_admission_lint'` -> `39:          python -m qor.scripts.dependency_admission_lint \`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:.github/workflows/pr-dependency-review.yml | grep -nE 'base.sha'` -> `40:            --base "${{ github.event.pull_request.base.sha }}"`

Mechanism: replace the single admission step with one step per governed root lockfile (every root `requirements-*.txt`; today `requirements-release.txt` and `requirements-sbom.txt`), each passing `--base "${{ github.event.pull_request.base.sha }}"` and an explicit `--lockfile <name>`, none wrapped in `|| true`. The lint is not changed; it already parses a pip-compile hash lockfile regardless of its name. Separate steps are chosen over a lint that accepts several lockfiles because they reuse the existing interface and change no code. A violation in the first step fails the job before the second step runs; the job still fails, so the hard-fail posture holds.

Observed evidence that the lint parses `requirements-sbom.txt` (run 2026-09-25, lint and `_dep_admit_common` byte-identical between the base and #496's head `ac568fdf2a547332b50aeef41efe25bb70027429`; detached scratch worktree of #496's head, since removed):

- `python -m qor.scripts.dependency_admission_lint --base 15729311f9f4d55d5dad2db004b972415c39432c --lockfile requirements-sbom.txt` printed `WARN: cyclonedx-bom@7.4.0 uploaded 10 days ago (within 14d window); override absent`, the table row `| cyclonedx-bom | 7.4.0 | 10 | violation |`, and exited 1.
- The same command without `--lockfile` (the current workflow's form) printed only `| build | 1.6.0 | 29 | clean |` and exited 0. That row reflects #496's head predating `main`'s `build` bump; the sbom change was not examined.

The age value is time-dependent and is recorded as an observation, not as a test expectation.

### LD-7: residual - pyproject pins are not examined by the CLI entry point

`run_lint` accepts pyproject text, but `main` never passes it. The call spans lines 258-263 and carries these four keywords only:

`git show 15729311f9f4d55d5dad2db004b972415c39432c:qor/scripts/dependency_admission_lint.py | grep -nE 'result = run_lint\('` -> `258:    result = run_lint(`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:qor/scripts/dependency_admission_lint.py | grep -nE 'current_lockfile_text=current_text'` -> `259:        current_lockfile_text=current_text,`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:qor/scripts/dependency_admission_lint.py | grep -nE 'base_lockfile_text=base_text'` -> `260:        base_lockfile_text=base_text,`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:qor/scripts/dependency_admission_lint.py | grep -nE 'ledger_text=ledger_text,'` -> `261:        ledger_text=ledger_text,`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:qor/scripts/dependency_admission_lint.py | grep -nE 'threshold_days=args.threshold_days,'` -> `262:        threshold_days=args.threshold_days,`

So a `pyproject.toml` or `.in` change triggers the workflow (dependency-review-action runs), but the cooling-period step examines only the governed lockfiles. Wiring pyproject pins through `main` is a lint code change and is out of scope for this hotfix. The residual is declared here and in the doctrine; D1 does not claim it.

### LD-8: assumption - dependency graph recognition of `requirements-sbom.txt`

Whether the GitHub dependency graph used by `actions/dependency-review-action` recognizes a manifest named `requirements-sbom.txt` could not be verified from this host and is not cited. This plan makes no claim that the action evaluates that file. The control this plan proves for the sbom lockfile is the in-repo cooling-period step (LD-6). The action runs on every governed-path PR either way.

## Feature Inventory Touches

Empty. This is workflow/test/doctrine maintenance and introduces no `src/` or user-touchable product feature surface.

`feature_inventory_touches`: `[]`.

## Phase 1: Regression tests

### Affected Files

- `tests/test_pr_dependency_review_workflow.py` - derive the governed dependency set from the repository root; require workflow trigger coverage and per-lockfile admission coverage for it.

### Changes

Add a module-level helper `_governed_dependency_paths() -> set[str]` returning the names of repository-root files matching `requirements-*.in` or `requirements-*.txt`, plus `pyproject.toml`. Add `_KNOWN_GOVERNED = {"pyproject.toml", "requirements-release.in", "requirements-release.txt", "requirements-sbom.in", "requirements-sbom.txt"}`.

Rewrite `test_workflow_triggers_on_dependency_paths`:

- assert `_KNOWN_GOVERNED` is a subset of `_governed_dependency_paths()`;
- assert `_governed_dependency_paths()` is a subset of the parsed `on.pull_request.paths`;
- keep the existing `.github/workflows/**` self-coverage assertion.

Add `test_admission_lint_runs_for_every_governed_lockfile`:

- collect the parsed workflow steps whose `run` invokes `dependency_admission_lint`;
- extract each step's `--lockfile` argument;
- assert every governed lockfile (members of `_governed_dependency_paths()` ending in `.txt`) is named by exactly one such step;
- assert each such step's `run` contains `--base` and does not contain `|| true`.

### Unit Tests

- `tests/test_pr_dependency_review_workflow.py::test_workflow_triggers_on_dependency_paths` - parses the real workflow YAML and fails when any derived governed path, including a newly added root `requirements-*.in/.txt` file, is absent from `on.pull_request.paths`. RED against the pre-fix workflow (the three missing paths).
- `tests/test_pr_dependency_review_workflow.py::test_admission_lint_runs_for_every_governed_lockfile` - parses the real workflow YAML and fails when any governed root lockfile has no hard-fail admission step naming it. RED against the pre-fix workflow (no step passes `--lockfile`).

## Phase 2: Workflow coverage

### Affected Files

- `.github/workflows/pr-dependency-review.yml` - add the three missing dependency-bearing root paths; run the admission step once per governed root lockfile.

### Changes

Add exactly these entries under `on.pull_request.paths`:

- `requirements-release.in`
- `requirements-sbom.in`
- `requirements-sbom.txt`

Replace the single admission step with two steps, each running `python -m qor.scripts.dependency_admission_lint --base "${{ github.event.pull_request.base.sha }}" --lockfile <name>`: one for `requirements-release.txt`, one for `requirements-sbom.txt`. Neither is wrapped in `|| true`. Preserve every existing trigger path, the action pin, `fail-on-severity: high`, and the checkout/setup/install steps unchanged.

### Unit Tests

- Re-run both Phase 1 tests after the workflow edit and observe GREEN.
- Run the full `tests/test_pr_dependency_review_workflow.py` file to prove the action remains SHA-pinned, `fail-on-severity: high` remains intact, workflow self-coverage remains intact, and the admission steps stay hard-fail.

## Phase 3: Doctrine scope note

### Affected Files

- `qor/references/doctrine-dependency-admission.md` - name `requirements-sbom.txt` as a governed lockfile and record the lockfile-only scope of the CI step.

### Changes

In `## Purpose`, add `requirements-sbom.txt` (the hash-pinned SBOM toolchain lockfile installed by the release build) to the parenthetical naming the release dependency tree. After the Phase 107 paragraph, add one `**Phase 298 lockfile coverage**:` paragraph stating: the CI admission step runs once per governed root lockfile via `--lockfile`; the threshold and override procedure are unchanged; the CLI entry point does not pass `pyproject.toml` to the pyproject pin walk, so pyproject pins are not examined in CI (declared residual).

### Unit Tests

- None added. Documentation-only change; `tests/test_doctrine_dependency_admission.py` must stay green (threshold, override, workflow reference, SSDF assertions unchanged).

## Definition of Done

### Deliverable: complete Dependency Review root-path and lockfile coverage

- **D1**: every change to a governed root dependency file (derived per LD-2) triggers `PR Dependency Review`, and every governed root lockfile is examined by a hard-fail cooling-period admission step. Pyproject pin examination in CI is a declared residual (LD-7).
- **D2**: `.github/workflows/pr-dependency-review.yml` names `pyproject.toml`, `requirements-release.in`, `requirements-release.txt`, `requirements-sbom.in`, and `requirements-sbom.txt` under `pull_request.paths`, preserves `.github/workflows/**`, and carries one admission step per governed root lockfile passing `--base` and `--lockfile`; the action pin, `fail-on-severity: high`, and hard-fail posture are unchanged.
- **D3**: Phase 298 follows canonical phase branch/plan resolution and receives truthful current-revision audit/substantiation evidence before promotion; no governance evidence is synthesized through the GitHub API. The doctrine records the sbom lockfile coverage and the pyproject residual.
- **D4**: `tests/test_pr_dependency_review_workflow.py::test_workflow_triggers_on_dependency_paths` and `tests/test_pr_dependency_review_workflow.py::test_admission_lint_runs_for_every_governed_lockfile` are RED before the workflow edit and GREEN afterward, and the full workflow test file passes on the implemented revision.

## CI Commands

- `python -m pytest tests/test_pr_dependency_review_workflow.py -q` - verifies derived trigger coverage, per-lockfile admission coverage, and unchanged dependency-review enforcement semantics.
- `python -m pytest tests/test_doctrine_dependency_admission.py -q` - verifies the doctrine edit keeps its contracted content.
- `for f in requirements-release.txt requirements-sbom.txt; do python -m qor.scripts.dependency_admission_lint --base origin/main --lockfile "$f" || exit 1; done` - runs each governed-lockfile admission step's command locally. On a branch whose lockfiles equal `origin/main` the expected output is `_No lockfile bumps detected._` per lockfile; that local result is not admission evidence for #496 (LD-4).
- `python -m pytest tests/ -q` - verifies repository regression safety.
- `python qor/scripts/check_variant_drift.py` - verifies installed/generated variant consistency.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` - verifies the ledger chain.
- `python -m ruff check qor/ tests/` - lints the changed test file.
- `python -m qor.scripts.publication_boundary_lint --repo-root .` - verifies the publication-boundary surface remains clean.

## CI Coverage Exemptions

- `python -m qor.reliability.seal_entry_check` - seal-time check; runs at `/qor-substantiate`, not affected by a workflow/test/doctrine edit.
- `python -m qor.reliability.ledger_base_currency` - WARN-only ledger freshness; not affected by this plan.
- `python -m qor.reliability.gate_chain_completeness` - sealed-phase gate-chain check; runs at seal.
- `python -m qor.reliability.intent_lock_committed` - sealed-phase intent-lock check; runs at seal.
- `python -m qor.scripts.seal_artifacts` - seal-artifact currency; runs at seal.
- `python -m qor.scripts.gate_provenance` - sealed-phase provenance verify/attest; runs at seal and in CI with a secret.
- `python -m qor.scripts.status_json --self-test` - nightly health self-test; not affected by this plan.
- `tests/test_packaging_install.py` - packaging integration smoke; no packaging surface changes.

## Non-goals

- dependency version changes;
- dependency-policy redesign (threshold, override, severity);
- changes to `dependency_admission_lint` code, including wiring pyproject pins through its CLI entry point;
- weakening or bypassing Dependency Review;
- merging #496 through the pre-fix enforcement gap;
- hand-issuing governance evidence;
- unrelated repository cleanup.
