# Research Brief: Dry-Run Modes for Mutating Commands (GH #250 part b)

**Date**: 2026-07-04
**Analyst**: The Qor-logic Analyst
**Target**: GH #250 part b -- `--dry-run` for the mutating CLI surfaces; final scope item before #250 closes
**Scope**: per-command mutation inventory, dry-run seams, CLI-growth impact, the session-rotate special case

---

## Executive Summary

Six mutating surfaces need dry-run (install already has it). Five are low/medium effort with clean seams -- each is a read-compute-write shape where the writes are already funneled through one or two call sites that a `dry_run` guard can wrap while reads and rendering still execute (the Orko `[dry] would <action>` pattern). One is architecturally awkward: `session.rotate()` is invoked internally by ~4 modules mid-automation, so a flag would have to thread through orchestration; the honest shape is a NEW operator-facing `session_tool` command (rotate/current subcommands with `--dry-run`) while the internal `rotate()` stays mutation-only. CLI growth stays within ~5 lines on the already-over-razor `qor/cli.py` (reconcile + uninstall flags); everything else lands in module `main()`s reached via the generic runner.

## Findings (mutation sites, all file:line verified)

1. **seal_artifacts --write**: writes funnel through `_write_atomic` calls inside `update_files` (qor/scripts/seal_artifacts.py:106-113); renderers are pure. Dry-run computes everything and prints `[dry] would write <path>` per changed file. Distinct from `--check` (mismatch report): dry-run previews the write set. No CLI growth (module main).
2. **reconcile propose**: single JSON write at qor/cli_handlers/reconcile.py:31; guard + `[dry] would write proposal to <path>`. Flag on the existing subparser (+1 cli_handlers line).
3. **reconcile authorize**: two writes -- ledger append inside qor/scripts/reconcile.py:122 (`append_reconciliation_entry`) and proposal-status update at qor/cli_handlers/reconcile.py:69. `append_reconciliation_entry` gains `dry_run=False`; output `[dry] would append RECONCILIATION Entry #<N>` + `[dry] would mark proposal authorized`. Medium (signature threads one level).
4. **changelog stamp**: atomic writes at qor/scripts/changelog_stamp.py:75 and qor/scripts/changelog_backends.py:49; both are library functions (no CLI surface) -- `dry_run=False` parameter, all validation (missing/empty Unreleased, version collision) still raises in dry-run, output `[dry] would stamp <path> version=<v>`.
5. **governance-index --advance-last-reviewed**: single write at qor/scripts/governance_index.py:118 inside `advance_last_reviewed`; `dry_run` guard + `[dry] would advance Last Reviewed -> <date>`. Lands in module main (generic runner); the `qor/cli.py` wrapper passes argv through, so at most 1 plumbing line.
6. **uninstall**: unlinks at qor/install.py:103 (`_remove_file_and_empty_parents`) and :137 (install record); mirrors the EXISTING install `--dry-run` (qor/install.py:76, cli.py:158) -- `[dry] Would remove <N> files` + list. +1 cli.py flag line.
7. **session rotate (special case)**: marker write at qor/scripts/session.py:105 via `_atomic_write`; `rotate()` is called internally by gate/orchestration modules during automation, where a dry-run signal has no meaning. Recommendation: leave `rotate()` untouched; add a small operator-facing module (e.g., `qor/scripts/session_tool.py` with `current`/`rotate [--dry-run]` subcommands via the generic runner) so an operator can preview `[dry] would rotate session: <old> -> <new>` without threading flags through automation.

## Blueprint Alignment

| Claim | Finding | Status |
|---|---|---|
| All 6 surfaces need the same treatment | 5 fit one pattern; session-rotate needs the operator-facing-wrapper shape instead | PARTIAL (by design) |
| Dry-run requires cli.py growth | Only reconcile (+2 flags in cli_handlers) and uninstall (+1 flag) touch argparse outside module mains; ~3-5 lines total on the grandfathered file | MATCH (bounded) |
| install needs work | Already has --dry-run (cli.py:158; install.py:76) | MATCH (no-op) |

## Recommendations

1. One phase (167) ships all six: dry_run guards + `[dry]` output on seal_artifacts/reconcile x2/changelog x2/governance_index/uninstall, plus the new `session_tool` operator command. Validation and reads ALWAYS execute in dry-run (errors must surface identically); only writes/unlinks/os.replace are guarded -- behavioral tests assert both halves (no mutation AND identical failure behavior).
2. Close #250 at full scope in this phase's PR (parts a and c shipped in Phase 165 with live runtime evidence; part b completes here).
3. Nightly-health is unaffected (read-only ladder); no workflow change, no CI-surface registry rows.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
