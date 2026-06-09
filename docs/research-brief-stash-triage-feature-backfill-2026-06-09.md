# Research Brief

**Date**: 2026-06-09
**Analyst**: The Qor-logic Analyst
**Target**: (1) the 10 residual git stashes; (2) the 3 `unverified` FEATURE_INDEX rows (`uninstall`, `list`, `info`) and the test surface needed to backfill them.
**Scope**: stash disposition (droppable cruft vs unincorporated work) + verifying-test design for FX002/FX003/FX005.

---

## Executive Summary

All 10 residual stashes are droppable cruft from superseded phase branches (phase/45 through phase/90 era); every file they carry is a dist/install/transient artifact, with one stale 1-line `CLAUDE.md` edit (stash@{5}, phase-65 era) long superseded by 80+ subsequent phases. None contain unincorporated source work; the set is safe to clear. On the backfill: `uninstall` (FX002) is a DRIFT finding -- it already has a verifying test (`tests/test_cli_install_gemini.py::test_gemini_uninstall_cleans_commands_dir`) but the FEATURE_INDEX row marks it `unverified` with an empty `Test path`. Only `list` (FX003) and `info` (FX005) genuinely lack tests; each needs one behavioral test invoking the handler and asserting output. Backfill = 1 inventory correction + 2 new tests, taking FEATURE_INDEX from 14/17 to 17/17 verified.

## Findings

### Category 1: Stash disposition

Confirmed via `git stash show --stat` + `git stash show --name-only` on each of the 10 entries. Filtering each file list against the artifact-path set (`qor/dist/`, `.claude/`, `.kilo/`, `.codex/`, `.gemini/`, `.agent/staging/`, `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md`) leaves:

| Stash | Origin phase | Non-artifact residue | Disposition |
|---|---|---|---|
| stash@{0}, {1} | restore/phase-89 dist-drift | none (variant `manifest.json` only) | drop |
| stash@{2} | phase/70 | none (`.agent/staging/AUDIT_REPORT.md` only) | drop |
| stash@{3} | phase/67 | none (AUDIT_REPORT + shadow-genome doc) | drop |
| stash@{4} | phase/66 | none (AUDIT_REPORT + shadow-genome doc) | drop |
| stash@{5} | phase/65 | 1-line `CLAUDE.md` (phase-65 era) | drop -- superseded |
| stash@{6} | phase/59 | none (install artifacts + dist skill recompile) | drop |
| stash@{7} | phase/51 | none ("wip -- superseded by Phase 52") | drop |
| stash@{8}, {9} | phase/46, phase/45 | none (dist `manifest.json` only) | drop |

The only source-tree file in any stash is the stash@{5} `CLAUDE.md` line from the phase-65 era; `CLAUDE.md` has since been rewritten across 80+ phases (token-efficiency doctrine, test-discipline, governance-flow sections all post-date it), so the stashed line is dead. The large insertion counts (stash@{5} 632, stash@{6} 592, stash@{7} 205) are install-artifact and per-host dist recompile churn (manifest timestamps + regenerated skill bodies), not stranded feature work. The `PROCESS_SHADOW_GENOME_UPSTREAM.md` lines are the `sess-1` test-pollution class already pruned in Phase 143.

### Category 2: backfill targets (FEATURE_INDEX FX002/FX003/FX005)

- **FX002 `uninstall`** -- impl `qor/install.py:114 _do_uninstall(...)`; parser `qor/cli.py:157`. Existing coverage: `tests/test_cli_install_gemini.py:59 test_gemini_uninstall_cleans_commands_dir` runs `_do_install` then `_do_uninstall` and asserts the commands dir is cleaned (also referenced by `tests/test_phase21_harness.py`). This is a behavioral test, not presence-only. The FEATURE_INDEX row is therefore stale (DRIFT, see Blueprint Alignment).

- **FX003 `list`** -- impl `qor/install.py:171 _do_list(args)` dispatching to `_list_available()` (`:142`) and `_list_installed(host, scope)` (`:158`); parser `qor/cli.py:162` accepts `--available` / `--installed` / `--host` / `--scope`. No test invokes `_do_list` / `_list_available` / `_list_installed` (grep over `tests/` returns nothing). Backfill test: invoke `_do_list` with an `--available` namespace, capture stdout, assert rc==0 and that the output enumerates real packaged skills (e.g. contains `qor-plan`); repeat for `--installed` against a tmp install root.

- **FX005 `info`** -- impl `qor/cli.py:25 _do_info(args)`: resolves `<dist_root>/variants/claude/skills/<name>/SKILL.md` (or `<name>.md`), prints the first 500 chars and returns 0; prints `Skill <name> not found` to stderr and returns 1 on miss. Parser `qor/cli.py:177`. No test invokes `_do_info`. Backfill test: build a tmp dist root with one known SKILL.md, invoke `_do_info` with that name, assert rc==0 and the printed body; invoke with a bogus name, assert rc==1 and the stderr message.

## Blueprint Alignment

The inventory under audit is `docs/FEATURE_INDEX.md` (the FEATURE_INDEX doctrine treats it as the source of truth for the CLI surface).

| Blueprint Claim | Actual Finding | Status |
|----------------|---------------|--------|
| FX002 `uninstall` is `unverified`, no `Test path` | `test_gemini_uninstall_cleans_commands_dir` exercises `_do_uninstall` behaviorally | DRIFT |
| FX003 `list` is `unverified` | No test invokes `_do_list` / `_list_available` / `_list_installed` | MATCH |
| FX005 `info` is `unverified` | No test invokes `_do_info` | MATCH |
| 10 stashes may hold unincorporated work | All 10 are dist/install/transient cruft; no source work | MATCH (no risk) |

## Recommendations

1. **[P2 housekeeping]** Drop all 10 stashes (`git stash clear`, or individual `git stash drop` if a paper trail per-entry is wanted). No cycle; no governance artifact. Verified no unincorporated source work.
2. **[P1 backfill]** Run one small governed cycle (`change_class: hotfix`, doc_tier minimal) that: (a) corrects FX002 to `verified` citing the existing gemini uninstall test (DRIFT fix, no new test); (b) adds a behavioral test for `_do_list` (available + installed paths) and flips FX003 to `verified`; (c) adds a behavioral test for `_do_info` (found + not-found) and flips FX005 to `verified`. FEATURE_INDEX moves 14/17 -> 17/17 verified. Both new tests must invoke the handler and assert output/return code (not presence-only), per `qor/references/doctrine-test-functionality.md`, and run twice to confirm determinism.

## Updated Knowledge

No SHADOW_GENOME or doctrine correction required. One inventory-accuracy lesson worth carrying: a freshly authored FEATURE_INDEX (Phase 144) can mark a feature `unverified` when coverage already exists under a differently-named test (here, the uninstall path is verified by an install-suite test, not a dedicated `test_uninstall`). The `feature_index_verify` tally trusts the row's `Test path`; an empty path reads as unverified even when behavior is covered. Future FEATURE_INDEX authoring should grep for the handler symbol across `tests/` before marking a row `unverified`.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
