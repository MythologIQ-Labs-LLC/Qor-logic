# Plan: Phase 163 — gate release publish on CI success for the tagged SHA

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

None. Approach fixed by operator: require the `CI` workflow's `success`
conclusion for the tagged commit's SHA before building/publishing; no
test-re-run.

## Problem

`release.yml` has `build` -> `publish` and **no test gate**. The publish is
gated only by tag-reachability-from-`main` and the manual `pypi` environment
approval. Nothing structurally couples a publish to the tests passing on the
tagged commit -- the only coupling was the operator verifying PR CI before
approving, which is discipline, not structure (and has failed). Verified:

> `grep -nE "pytest|test" .github/workflows/release.yml` -> (no test step)
> `.github/workflows/release.yml:61` -> `publish: needs: build` (build != tests)

A broken `main` (post-merge interaction) or an early approval would ship
untested code; the existing PyPI pull-back check only proves the published bytes
equal the built bytes, never that they pass tests.

## Phase 1: pure CI-success evaluator + release.yml double-gate

### Affected Files

- `tests/test_release_ci_gate.py` - NEW. Behavioral tests for the pure
  evaluator + the CLI exit code, plus structural assertions that release.yml
  wires the gate into both jobs before the publish/build work.
- `qor/scripts/release_ci_gate.py` - NEW. Pure `evaluate(runs, head_sha)` +
  a `main` that reads the `gh api` workflow-runs JSON from stdin and exits 1
  when no successful CI run exists for the SHA. Stdlib only (no network in the
  module -- the workflow performs the authenticated `gh api` call and pipes the
  result in, keeping the decision logic unit-testable).
- `.github/workflows/release.yml` - EDIT. Add a "Verify CI succeeded for this
  SHA" step to BOTH the `build` job (early fail) and the `publish` job
  (enforcement gate), each before that job's real work; add `actions: read` to
  both jobs' permissions so the `gh api` runs-list call is authorized. No new
  job (the immutability test requires `jobs == {build, publish}`), no new
  `uses:` action, no `id-token` change.

### Changes

`release_ci_gate.py`:

- `evaluate(runs, head_sha) -> GateResult` — pure. `runs` is the parsed
  `gh api .../workflows/ci.yml/runs?head_sha=<sha>` payload (dict with
  `workflow_runs`, or a bare list). Returns ok iff at least one run has
  `head_sha == head_sha` and `conclusion == "success"`; otherwise a finding
  naming what was found (in-progress / failure / none).
- `main(argv)` — `--sha <sha>` (required); reads the runs JSON from stdin;
  `evaluate`; print `OK`/`REFUSE`; exit 0 on ok, 1 otherwise (fail-closed).

`release.yml` step (both jobs), after the existing tag-reachability guard:

```
- name: Verify CI succeeded for this SHA (<build|publish>-side gate)
  env: { GH_TOKEN: ${{ github.token }} }
  run: |
    SHA=$(git rev-parse HEAD)
    gh api "/repos/${GITHUB_REPOSITORY}/actions/workflows/ci.yml/runs?head_sha=${SHA}&per_page=100" \
      | python -m qor.scripts.release_ci_gate --sha "$SHA"
```

The module runs from the checked-out repo root (`python -m qor.scripts...`
resolves the source tree; stdlib-only, so no install needed). Fail-closed: an
absent/failed/in-progress CI run for the SHA exits 1 and stops the job, so a
publish cannot proceed on un-green code regardless of approval timing.

### Unit Tests

- `tests/test_release_ci_gate.py`:
  - `test_evaluate_ok_when_success_run_for_sha` — a `workflow_runs` list with a
    `{head_sha: S, conclusion: success}` entry → `ok` True.
  - `test_evaluate_fails_when_only_failure_run` — same SHA but
    `conclusion: failure` → `ok` False.
  - `test_evaluate_fails_when_run_in_progress` — `conclusion: null`,
    `status: in_progress` → `ok` False (not yet green).
  - `test_evaluate_fails_when_run_is_for_a_different_sha` — success run but for a
    different `head_sha` → `ok` False.
  - `test_evaluate_fails_on_no_runs` — empty `workflow_runs` → `ok` False.
  - `test_main_exits_zero_on_success_via_stdin` — feed a success-run JSON on
    stdin; `main(["--sha", S])` returns 0.
  - `test_main_exits_one_on_no_success_via_stdin` — feed an in-progress-run JSON;
    `main(["--sha", S])` returns 1.
  - `test_release_yml_wires_gate_into_both_jobs` — parse `release.yml`; a step
    running `qor.scripts.release_ci_gate` exists in `build` AND `publish`.
  - `test_release_yml_gate_precedes_publish` — in the publish job, the gate step
    index is less than the `pypa/gh-action-pypi-publish` step index.

## Definition of Done

### Deliverable: release CI-success gate

- **D1**: A publish cannot proceed unless the `CI` workflow concluded `success`
  for the exact tagged commit -- structural, not dependent on approval timing.
- **D2**: `qor/scripts/release_ci_gate.py` (`evaluate`, `main`); release.yml gate
  step in both jobs; `actions: read` added to both jobs.
- **D3**: Ledger SESSION SEAL records the release-gate hotfix; CHANGELOG `### Fixed`.
- **D4**: `tests/test_release_ci_gate.py::test_evaluate_fails_when_run_in_progress`
  and `::test_release_yml_wires_gate_into_both_jobs` pass.

## CI Commands

- `python -m pytest tests/test_release_ci_gate.py -v` — evaluator + wiring.
- `python -m pytest tests/test_release_workflow_immutability.py tests/test_release_workflow_guard.py -v` — release.yml properties still hold.
- `python -m pytest tests/ -q` — full suite stays green.
