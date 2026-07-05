# Research Brief: Autonomous QA Nightly Self-Check (GH #250)

**Date**: 2026-07-04
**Analyst**: The Qor-logic Analyst
**Target**: GH #250 (autonomous QA layer) with GH #240 (deterministic status --json) as a discovered dependency
**Scope**: (1) exact mechanics of an external QA exemplar's drift-detection pattern to port; (2) Qor-logic's invocable health-check surface; (3) gaps between them

---

## Executive Summary

The an external QA exemplar's drift-detection workflow provides a complete, port-ready recipe: cron trigger, script self-test against ephemeral resources, JSON-on-last-line output contract, and an idempotent `gh issue` lifecycle (search by title substring + `--state open`, comment-if-exists / create-if-not, close-with-comment when clear). Qor-logic has 11 CLI-invocable read-only health checks with clean 0/1 exit codes but NO machine-readable aggregate, NO scheduled workflow, and NO `issues: write` permission anywhere -- so the load-bearing gap is a single JSON aggregate command, which is exactly open issue #240. Recommendation: one phase ships the aggregate (`status --json`, closing #240) + the nightly workflow with issue lifecycle (#250 part a); dry-run modes for the 6 mutating commands (#250 part b) go to a follow-on phase so #250 is not half-closed.

## Findings

### 1. The portable pattern (an external QA exemplar workspace)

- **Trigger + permissions**: `.github/workflows/drift-detection.yml` lines 3-12 -- `schedule: cron '0 10 * * *'` + `workflow_dispatch`; uses implicit `GITHUB_TOKEN` (needs `issues: write` when ported into a permissions-explicit repo).
- **Self-test before real check** (lines 43-46): the checker validates its own logic against ephemeral resources first; `scripts/drift-check.sh` lines 7-76 create PID-scoped throwaway state, `trap cleanup EXIT`, then assert three gates (expected-drift exit 1 + expected string; fix; expected-sync exit 0).
- **Output contract** (drift-check.sh lines 91-115): human text followed by ONE machine-readable JSON line (`{"status":"sync"|"drift", ...}`); workflow extracts with `grep '^{' | tail -1` into `$GITHUB_OUTPUT` and mirrors text into `$GITHUB_STEP_SUMMARY`.
- **Issue lifecycle** (drift-detection.yml lines 70-111): find via `gh issue list --search "<title-key>" --json number --limit 1 --state open | jq '.[0].number // empty'`; if found -> `gh issue comment N` with timestamp + JSON payload; else -> `gh issue create --title --body --label bug --label infrastructure`; when clear -> `gh issue close N --comment "Resolved as of <ts>"`. Idempotent across runs; never reopens closed issues.
- **Dry-run threading** (an external QA exemplar's polling tool, lines 196, 224-243): reads always execute; writes/state-advance/notifications guarded by `if not dry_run`; log lines carry a `[dry]` prefix.

### 2. Qor-logic's health-check surface (all citations current tree)

Eleven read-only checks invocable via CLI, all TEXT output, exit 0/1 (governance_health also 2=damaged): governance_health (qor/scripts/governance_health.py main at 256; --profile), ledger_hash verify (552), seal_artifacts --check (147; new in Phase 164), gate_chain_completeness (qor/reliability/, 90), gate_provenance verify-committed (233), governance_index --cross-check-ledger (180), badge_currency (135), install_drift_check (59), workspace_fragility_check (228), merge_velocity_check (209), plus the pytest packaging smoke (tests/test_packaging_install.py, 4 integration tests, reused by the CI install-smoke job).

- **No scheduled workflow exists** (ci.yml/release.yml/pr-lint.yml/pr-dependency-review.yml: no `schedule:`); **no workflow carries `issues: write`**.
- **No aggregate machine-readable status exists** -- `qor-logic capabilities inventory/context` emit JSON but for code-gen, not health. This is precisely GH #240's ask.
- **doc_integrity has no CLI check form** (exception-based `run_all_checks_from_plan` only, qor/scripts/doc_integrity.py:196) -- a nightly can wrap it or defer it.
- **Mutating commands lacking --dry-run** (6): seal_artifacts --write, reconcile authorize, changelog stamp, session rotate, governance-index --advance-last-reviewed, uninstall. (install and dist_compile already have --dry-run.)

### 3. Scope-integrity constraint

Closing #250 with only the workflow half would repeat the half-measure-closure pattern (docs/research-brief-half-measure-closures-2026-05-29.md: 11 of 52 issues closed on advisory/stopgap scope). #250 enumerates (a) scheduled workflow + auto issue lifecycle, (b) dry-run modes, (c) issue-named regression guards. One phase cannot razor-cleanly carry all three.

## Blueprint Alignment

| Claim | Finding | Status |
|---|---|---|
| Qor-logic checks are automatable as-is | True for invocation (11 CLI checks, clean exits) but false for aggregation (text-only) | PARTIAL |
| #250 is independent of other issues | The workflow's issue-body/JSON needs are #240's deliverable; build #240 first inside the same phase | DRIFT (dependency) |
| Nightly can reuse CI permissions | No; `issues: write` must be added on the new workflow only | MATCH (scoped) |

## Recommendations

1. **Phase 165 scope**: (a) new aggregate runner `qor/scripts/status_json.py` (or `qor-logic status --json`) executing the read-only check ladder in-process/subprocess and emitting one JSON object {schema_version, ts, checks:[{id, ok, exit, summary}], overall_ok} -- CLOSES #240; (b) new `.github/workflows/nightly-health.yml` (cron + workflow_dispatch; `issues: write`; runs status --json; `gh issue` lifecycle exactly per the external QA exemplar's idioms, title key "Nightly governance health"; step-summary mirror); (c) a --self-test mode on the aggregate runner (tmp-repo fixture, expected-fail then expected-pass, trap-free tempfile cleanup) per the drift-check discipline. ADVANCES #250 (part a+c); #250 stays open with a progress comment.
2. **Phase 166 (follow-on)**: --dry-run for the 6 mutating commands + issue-named regression guards; then #250 closes with full scope.
3. Exclude from nightly v1: merge_velocity/workspace_fragility (branch-context signals, noisy on a bare checkout of main) and doc_integrity (needs a plan artifact); include: governance_health, ledger verify, seal_artifacts --check --skip-tests, gate_chain_completeness, gate_provenance verify-committed, governance_index --cross-check-ledger, install-smoke pytest.

## Updated Knowledge

No doctrine corrections; the drift-check self-test discipline (validate the checker against synthetic state before trusting its verdict) is a candidate addition to doctrine-test-functionality at plan time.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
