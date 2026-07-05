# Plan: Phase 165 - Autonomous QA nightly self-check (GH #250 part a/c; closes GH #240)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**: (none)

**boundaries**:
- limitations: The nightly ladder runs read-only checks that are valid on a bare checkout of `main`; branch-context signals (merge-velocity, workspace-fragility) and plan-scoped doc-integrity are excluded from v1. The Tests badge check runs with `--skip-tests` (no dev-collect in the aggregate; the badge is verified at seal time).
- non_goals: No `qor/cli.py` change (383 lines, over the 250 razor; the canonical invocation is the generic runner `qor-logic scripts status_json` -- documented on GH #240 at close); no --dry-run modes for mutating commands (deferred to the follow-on phase that closes #250); no notification channels beyond GitHub issues.
- exclusions: Doctrine files, FEATURE_INDEX, glossary untouched except /qor-document currency updates at seal.

## Open Questions

(none)

## Origin

Research brief docs/research-brief-autonomous-qa-nightly-2026-07-04.md (ledger entry #382, session `2026-07-04T0729-4d0fb9`). Pattern source: an external QA exemplar's drift-detection (workflow lines 3-111; drift-check.sh self-test lines 7-76 with three validation gates; JSON-last-line contract lines 91-115).

## Locked Decisions

- **LD-1: check ladder (six in-process checks + packaging smoke as a workflow step).**
  `grep -nE '^def main' qor/scripts/governance_health.py -> 256`; `qor/scripts/ledger_hash.py -> 552 (subcommand verify)`; `qor/scripts/seal_artifacts.py -> 147 (--check --skip-tests)`; `qor/reliability/gate_chain_completeness.py -> 90`; `qor/scripts/gate_provenance.py -> 233 (verify-committed)`; `qor/scripts/governance_index.py -> 180 (--cross-check-ledger)`. All return int exit codes and print text -- the aggregator captures both.
- **LD-2: no scheduled workflow or `issues: write` exists today.**
  `grep -rn 'schedule:' .github/workflows/ -> no matches`; `grep -rn 'issues: write' .github/workflows/ -> no matches` (release.yml publish job carries `id-token`/`contents`/`actions` only).
- **LD-3: generic runner invocation, no CLI growth.**
  `qor-logic scripts <module>` executes any `qor/scripts/*.py` `main()` (Phase 90 contract; Phase 164 precedent with `seal_artifacts`). `qor/cli.py` stays untouched.
- **LD-4: issue-lifecycle idioms ported verbatim from the reference.**
  `an external QA exemplar's drift-detection workflow (lines 70-111)`: search `gh issue list --search "<title-key>" --json number --limit 1 --state open | jq '.[0].number // empty'`; comment-if-exists; `gh issue create --title --body --label` if not; `gh issue close N --comment` when clear.
- **LD-5: SHA-pinned actions per repo convention.**
  `grep -nE 'uses: actions/(checkout|setup-python)@' .github/workflows/ci.yml -> checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 (v6.0.3), setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405 (v6.2.0)`.
- **LD-6: packaging smoke reuses the registered CI command form.**
  `grep -n 'test_packaging_install' docs/plan-qor-phase89-ci-commands-reconciliation.md -> python -m pytest tests/test_packaging_install.py -v -m integration` (already in the CI-surface registry; the nightly reuses the identical string).

## Phase 1: Aggregate status runner (TDD first)

### Affected Files

- tests/test_status_json.py - NEW; behavioral tests of the aggregator against synthetic check registries
- qor/scripts/status_json.py - NEW; check registry + in-process runner + JSON emitter + `--self-test`

### Changes

`qor/scripts/status_json.py` (target <200 lines, functions <=40):

- `Check` dataclass: `id: str`, `argv: list[str]` (module-main argv form) OR `fn: callable` -- normalized to a zero-arg callable returning `(exit_code, output_text)`.
- `run_check(check) -> dict` -- executes with `contextlib.redirect_stdout/stderr` capture around the module `main(argv)` call; catches `SystemExit` and any exception (exception => exit 3, summary = first line of the error); returns `{id, ok, exit, summary}` where summary is the first non-empty output line truncated to 200 chars.
- `default_registry(repo_root) -> list[Check]` -- the six LD-1 checks with their argv.
- `run_all(checks) -> dict` -- `{schema_version: '1', ts: <UTC ISO>, checks: [...], overall_ok: all(ok)}`.
- `main(argv) -> int` -- default mode: run the registry, print human lines (`OK/FAIL <id>: <summary>`) then exactly one JSON object as the FINAL line (the external exemplar's grep-extractable contract); exit 0 iff overall_ok. `--self-test`: run `run_all` over a synthetic two-entry registry (one passing fn, one failing fn), assert JSON shape + overall_ok False + per-check exits, print `self-test PASSED`, exit 0 (exit 1 with the failed assertion otherwise). `--repo-root` supported.

### Unit Tests

- tests/test_status_json.py::test_run_check_captures_exit_and_summary - a passing fn-check returns ok=True exit=0 with first output line as summary
- tests/test_status_json.py::test_run_check_failure_and_exception_paths - a failing check returns ok=False with its exit code; a raising check returns exit=3 with the error text in summary
- tests/test_status_json.py::test_run_all_shape_and_overall - synthetic pass+fail registry: JSON has schema_version/ts/checks/overall_ok, overall_ok False; all-pass registry: overall_ok True
- tests/test_status_json.py::test_main_emits_json_as_final_line_and_exit_codes - main() over an injected registry prints parseable JSON as the last stdout line; exit 1 on any failure, 0 on all-pass
- tests/test_status_json.py::test_default_registry_ids_unique_and_argv_wellformed - registry ids are unique and every argv names an importable module (importlib.util.find_spec on the -m target)
- tests/test_status_json.py::test_self_test_mode_passes - `main(['--self-test'])` returns 0 and prints the PASSED marker

## Phase 2: Nightly workflow + wiring

### Affected Files

- tests/test_nightly_health_wiring.py - NEW; structural properties of the workflow file
- .github/workflows/nightly-health.yml - NEW; scheduled self-check with automatic issue lifecycle
- docs/plan-qor-phase89-ci-commands-reconciliation.md - CI-surface registry rows for the two new commands (forward-maintenance pattern)

### Changes

`nightly-health.yml`:

- `on: schedule: [cron: '0 9 * * *']` + `workflow_dispatch`; top-level `permissions: contents: read, issues: write`.
- One job `nightly-health` on ubuntu-latest: SHA-pinned checkout (fetch-depth 0, fetch-tags) + setup-python 3.12 (LD-5); `pip install -e ".[dev]"`.
- Steps: (1) `python -m qor.scripts.status_json --self-test` (checker validates itself first, fail-fast); (2) `python -m qor.scripts.status_json --repo-root .` with exit captured `|| RC=$?`, JSON extracted `grep '^{' | tail -1` into `$GITHUB_OUTPUT`, full text into `$GITHUB_STEP_SUMMARY`; (3) `python -m pytest tests/test_packaging_install.py -v -m integration` with exit folded into the same health verdict (LD-6); (4) on any failure: LD-4 lifecycle with title key `Nightly governance health` and labels `bug`, `governance` (comment carries UTC timestamp + the JSON payload); (5) on all-pass: close any open title-key issue with a resolved comment.

### Unit Tests

- tests/test_nightly_health_wiring.py::test_workflow_declares_schedule_dispatch_and_permissions - parses the YAML text and asserts the `schedule` cron, `workflow_dispatch`, `issues: write`, and that no other permission exceeds `contents: read`
- tests/test_nightly_health_wiring.py::test_workflow_runs_self_test_before_status_and_uses_lifecycle_idioms - step order: `--self-test` precedes the status run; the lifecycle steps contain `gh issue list --search`, `gh issue create`, `gh issue close`, and the title key appears in both create and close paths

## Feature Inventory Touches

(empty -- governance tooling and CI automation only; no user-touchable `src/` feature)

## Definition of Done

### Deliverable: status_json aggregate runner

- **D1**: One deterministic command reports all bare-checkout governance health as machine-readable JSON (closes GH #240).
- **D2**: `qor/scripts/status_json.py` <=200 lines, stdlib only, functions <=40 lines; final-line JSON contract.
- **D3**: GH #240 closed with the invocation documented; ledger seal entry cites this plan; CHANGELOG via /qor-document.
- **D4**: `test_main_emits_json_as_final_line_and_exit_codes` observes exit 1 + parseable final-line JSON on a failing registry and exit 0 on a passing one.

### Deliverable: nightly-health workflow

- **D1**: Governance health is verified nightly with zero operator engagement; drift opens/updates a GitHub issue and recovery closes it (GH #250 part a).
- **D2**: `.github/workflows/nightly-health.yml` per Phase 2 spec; SHA-pinned actions; `issues: write` scoped to this workflow only.
- **D3**: Phase 89 CI-surface registry rows added; #250 progress comment posted at cycle end (issue stays open for the dry-run follow-on).
- **D4**: `test_workflow_runs_self_test_before_status_and_uses_lifecycle_idioms` fails when the self-test step, lifecycle idioms, or title key are removed.
- **D4.d** (runtime): the schedule cannot fire inside this phase; first live run occurs post-merge. **Follow-up phase**: verified via `workflow_dispatch` invocation recorded in the #250 progress comment after merge.

## CI Commands

- `python -m pytest tests/test_status_json.py tests/test_nightly_health_wiring.py -q` -- new-test determinism (run twice)
- `python -m pytest -q` -- full suite regression
- `python -m qor.scripts.status_json --self-test` -- checker self-validation
- `python -m qor.scripts.status_json --repo-root .` -- aggregate health on this tree
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase165-autonomous-qa-nightly.md` -- plan-text consistency
