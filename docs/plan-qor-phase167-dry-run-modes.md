# Plan: Phase 167 - Dry-run modes for mutating commands (closes GH #250)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**: (none)

**boundaries**:
- limitations: Dry-run guards WRITES only; reads, rendering, and validation execute identically (errors must surface the same way in both modes). Internal automation call sites (`session.rotate()` from gate/orchestration modules, `changelog_backends.stamp` from substantiate) keep their default `dry_run=False` behavior unchanged.
- non_goals: No behavior change to `install` (already has `--dry-run`); no new notification channels; no nightly-health change (read-only ladder unaffected).
- exclusions: Doctrine/CHANGELOG updates via /qor-document at seal; no glossary terms.

## Open Questions

(none)

## Origin

Research brief docs/research-brief-dry-run-modes-2026-07-04.md (ledger entry #390, session `2026-07-04T1514-caa2a3`); GH #250 part b (final scope item; umbrella #247). Output convention: the external polling tool's `[dry] would <action>` pattern (an external QA exemplar's polling tool:196-243 -- reads always execute, writes guarded, `[dry]` log prefix).

## Locked Decisions

- **LD-1: seal_artifacts writes funnel through `_write_atomic`.**
  `grep -n '_write_atomic' qor/scripts/seal_artifacts.py -> definition + exactly 2 call sites inside update_files (README, SYSTEM_STATE)`; renderers pure. `update_files(..., dry_run=False)` guards both calls; `main` gains `--dry-run` (valid only with `--write`).
- **LD-2: reconcile has three write sites across two files.**
  `grep -n 'write_text' qor/cli_handlers/reconcile.py -> :31 (proposal JSON in do_propose), :69 (proposal status in do_authorize)`; `grep -n 'write_text' qor/scripts/reconcile.py -> :122 (ledger append in append_reconciliation_entry)`. `append_reconciliation_entry` gains `dry_run=False`; both subparsers gain `--dry-run` (cli_handlers-local argparse; `qor/cli.py` untouched for reconcile).
- **LD-3: changelog stamping is library-only.**
  `grep -n 'os.replace' qor/scripts/changelog_stamp.py -> :75`; `qor/scripts/changelog_backends.py -> :49`. Both gain `dry_run=False`; ALL validation (missing/empty Unreleased, version collision, format detection) still raises in dry-run.
- **LD-4: session rotate stays internal; operators get `session_tool`.**
  `grep -n '_atomic_write(MARKER_PATH' qor/scripts/session.py -> :105 inside rotate()`; rotate() is called by gate/orchestration modules where a dry-run signal has no meaning. NEW `qor/scripts/session_tool.py` (generic-runner module): `current` (prints the active session id or `none`) and `rotate [--dry-run]` (dry: `[dry] would rotate session: <old> -> <new-id-preview>` without writing; wet: delegates to `session.rotate()`).
- **LD-5: governance-index write funnels through `advance_last_reviewed`.**
  `grep -n 'write_text' qor/scripts/governance_index.py -> single site inside advance_last_reviewed (~:118)`; function gains `dry_run=False`, module `main` gains `--dry-run`; the `qor/cli.py` wrapper forwards argv so no wrapper logic changes.
- **LD-6: uninstall mirrors install's existing dry-run.**
  `grep -n 'dry_run' qor/cli.py qor/install.py -> install --dry-run exists (cli.py ~:158; install.py ~:76)`; uninstall unlinks at `install.py:103` (`_remove_file_and_empty_parents`) + `:137` (install record). `_do_uninstall(..., dry_run=False)` + `--dry-run` flag on the uninstall subparser (+1 line on the grandfathered cli.py, mirroring install's flag).
- **LD-7: caller enumeration for changed signatures.**
  `update_files`: callers = seal_artifacts.main + tests/test_seal_artifacts.py (defaulted param, no updates needed). `append_reconciliation_entry`: callers = do_authorize + reconcile tests (defaulted). `stamp`/`apply_stamp`: callers = substantiate skill prose + release handlers + tests (defaulted). `_do_uninstall`: caller = cli.py dispatch (updated). All new params are keyword-with-default -- no existing call site breaks; the SG-AffectedFilesContract-A surface is additive-only.

## Phase 1: Dry-run guards (TDD first)

### Affected Files

- tests/test_dry_run_modes.py - NEW; behavioral tests: for each surface, dry-run performs zero mutation AND prints the `[dry]` preview AND validation errors surface identically
- qor/scripts/seal_artifacts.py - `update_files(dry_run=...)` + `--dry-run` flag (LD-1)
- qor/scripts/reconcile.py - `append_reconciliation_entry(dry_run=...)` (LD-2)
- qor/cli_handlers/reconcile.py - `--dry-run` on propose/authorize subparsers, threaded to both write sites (LD-2)
- qor/scripts/changelog_stamp.py - `apply_stamp(dry_run=...)` (LD-3)
- qor/scripts/changelog_backends.py - `stamp(dry_run=...)` threading both backends (LD-3)
- qor/scripts/session_tool.py - NEW; `current` / `rotate [--dry-run]` operator command (LD-4)
- qor/scripts/governance_index.py - `advance_last_reviewed(dry_run=...)` + `--dry-run` flag (LD-5)
- qor/install.py - `_do_uninstall(dry_run=...)` guarding both unlink sites (LD-6)
- qor/cli.py - `--dry-run` on the uninstall subparser only (+1 line, mirrors install) (LD-6)

### Changes

Uniform contract per surface: compute/render/validate exactly as wet mode; guard every write/unlink/os.replace behind `if not dry_run:`; in dry mode print one `[dry] would <action> <target>` line per suppressed mutation; exit codes unchanged (dry-run of a valid operation exits 0; validation failures raise/exit identically to wet mode).

### Unit Tests

- tests/test_dry_run_modes.py::test_seal_artifacts_dry_run_previews_without_writing - tmp repo: `main(['--write','--dry-run',...])` exits 0, prints `[dry] would write` for both files, file bytes unchanged; wet run then mutates
- tests/test_dry_run_modes.py::test_reconcile_propose_and_authorize_dry_run - tmp ledger fixture: propose --dry-run writes no proposal file but prints the preview; authorize --dry-run leaves ledger byte-identical and proposal status unchanged, printing both `[dry]` lines
- tests/test_dry_run_modes.py::test_changelog_stamp_dry_run_preserves_file_and_still_validates - dry stamp leaves CHANGELOG bytes unchanged and prints the preview; dry stamp on an EMPTY Unreleased still raises ValueError (validation identical)
- tests/test_dry_run_modes.py::test_session_tool_rotate_dry_run_does_not_move_marker - tmp marker: `session_tool.main(['rotate','--dry-run'])` prints `[dry] would rotate` and the marker file is unchanged; wet rotate changes it; `current` prints the active id
- tests/test_dry_run_modes.py::test_governance_index_advance_dry_run - tmp index: dry advance prints the old->new preview, file unchanged; wet advance rewrites the date
- tests/test_dry_run_modes.py::test_uninstall_dry_run_lists_without_removing - tmp install layout + record: dry uninstall prints `[dry] Would remove N files`, all files + record still exist; wet uninstall removes them

## Feature Inventory Touches

(empty -- governance tooling only; no user-touchable `src/` feature)

## Definition of Done

### Deliverable: dry-run contract across the six surfaces

- **D1**: Every mutating CLI surface can rehearse safely: reads and validation identical, zero side effects, `[dry]` preview of every suppressed mutation (GH #250 part b; the external polling tool's safety pattern).
- **D2**: Keyword-defaulted `dry_run` parameters at the write funnels named in LD-1..LD-6; new `session_tool` module; +1 line on cli.py (uninstall flag only).
- **D3**: GH #250 closes at full scope in this phase's PR (parts a/c shipped Phase 165 with live evidence); CHANGELOG + doctrine currency via /qor-document.
- **D4**: Each of the 6 tests observes BOTH halves -- zero mutation in dry mode AND real mutation in wet mode -- plus identical validation failure for the changelog surface.

## CI Commands

- `python -m pytest tests/test_dry_run_modes.py -q` -- new-test determinism (run twice)
- `python -m pytest -q` -- full suite regression
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase167-dry-run-modes.md` -- plan-text consistency
