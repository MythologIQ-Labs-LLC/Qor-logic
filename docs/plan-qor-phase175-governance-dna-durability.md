# Plan: Phase 175 - Governance-DNA durability (GH #267)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**: (none)

**boundaries**:
- limitations: The snapshot survives accidental deletion of `docs/` state and `git clean -fd`; it does NOT survive `git clean -fdx` (the backup dir is gitignored and `-x` removes ignored files) -- the doctrine states this plainly. Non-forgeable durability is out of scope; the snapshot is an operator convenience, not evidence.
- non_goals: No automatic restore (routing surfaces the option; the operator restores deliberately); no SKILL.md prose changes (byte budget: both big skills within 70 bytes of EXCEEDED); no change to seed/bootstrap semantics for genuinely-new workspaces.
- exclusions: BACKLOG/FEATURE_INDEX/GOVERNANCE_INDEX are scaffold-owned (seed-recoverable) and excluded from the snapshot set; consumer-side incident remediation already done per GH #267.

## Open Questions

(none)

## Origin

Research brief docs/research-brief-governance-dna-durability-2026-07-13.md (ledger entry #418, session `2026-07-13T0515-117975`); GH #267.

## Locked Decisions

- **LD-1: the trigger is a first-write-of-session hook in the governed write path, not skill prose.**
  `grep -nE 'def write_gate_artifact' qor/scripts/gate_chain.py -> 241`; every gate-writing skill funnels through it under the QOR_SKILL_ACTIVE check. Byte budgets forbid prose: `qor-substantiate/SKILL.md` 40,929 / `qor-audit/SKILL.md` 40,890 vs EXCEEDED 40,960 (`grep -nE 'EXCEEDED_BYTES' qor/scripts/skill_size_budget_lint.py -> 24`). Hook posture is best-effort/fail-open, mirroring `_fire_gate_written_hook` (`grep -nE 'def _fire_gate_written_hook' qor/scripts/gate_chain.py -> 310`): a failed backup warns, never aborts a governed write.
- **LD-2: snapshot set is the five DNA files, keyed off the health-gate constants.**
  `grep -nE '^REQUIRED_ARTIFACTS' qor/scripts/governance_health.py -> 44`; the five non-scaffold DNA files (META_LEDGER, CONCEPT, ARCHITECTURE_PLAN, SYSTEM_STATE, SHADOW_GENOME) are the loss surface named in GH #267; BACKLOG/FEATURE_INDEX/GOVERNANCE_INDEX are scaffold-owned (`grep -nE '^SCAFFOLD_OWNED' qor/scripts/governance_health.py -> 57`) and seed-recoverable.
- **LD-3: routing fix threads prior-initialization evidence through the existing classify chain.**
  `grep -nE 'def _classify_missing' qor/scripts/governance_health.py -> 94`; callers: `_classify_one` (line 177) and the profile loop (line 205); external test callers use `_classify_one(base, rel, initialized)` (tests/test_governance_health_post_anchor_tolerance.py:38, tests/test_feature_index_present_and_verifies.py:18) so `_classify_one`'s positional signature is preserved and evidence is computed lazily inside `_classify_missing` via a new `prior_evidence` keyword with a `None` default computed at the check loop. Evidence sources: `git log -1 -- docs/META_LEDGER.md` (list-argv subprocess, check=False, 5s timeout) OR a non-empty `.agent/local-backup/governance/`.
- **LD-4: previously-initialized-now-missing classifies MISSING with a restore route, never UNINITIALIZED.**
  `grep -nE '_NEXT_BOOTSTRAP = ' qor/scripts/governance_health.py -> 81`. New `_NEXT_RESTORE` legal_next names `qor-logic scripts governance_snapshot restore` + git-history restore, then `/qor-remediate`; the doctrine invariant "DAMAGED/INCOMPLETE never seeded" is unchanged and the genuinely-new-workspace path (no evidence) still returns UNINITIALIZED/bootstrap.
- **LD-5: `governance-state-loss` joins the shadow-event enum; emission is restore-time, not health-check-time.**
  `qor/gates/schema/shadow_event.schema.json` enum currently lacks it (verified); the health gate runs at every skill entry, so emitting there would spam severity-3 events -- `governance_snapshot restore` emits exactly one per restore. Additive amendment to a registered schema; `gate_schema_freeze_lint` compares registry presence, not content (`qor/scripts/gate_schema_freeze_lint.py`), and no test locks the enum's exact contents (grep verified).
- **LD-6: backup location is `.agent/local-backup/governance/<session_id>/`, gitignored.**
  `.gitignore` currently has no `.agent` entry (verified); the dir gains an ignore line so operator-local backups are never tracked or published. Idempotency marker `.complete` inside the session backup dir gates one copy per session.

## Phase 1: Snapshot helper (TDD first)

### Affected Files

- tests/test_governance_snapshot.py - NEW; behavioral tests for backup, idempotency, restore + event emission, prior-initialization evidence, CLI exit codes
- qor/scripts/governance_snapshot.py - NEW; DNA_FILES constant, backup_dir, ensure_session_backup, restore, prior_initialization_evidence, main

### Changes

`governance_snapshot.py` (<180 lines, stdlib + shadow_process reuse): `DNA_FILES = ("docs/META_LEDGER.md", "docs/CONCEPT.md", "docs/ARCHITECTURE_PLAN.md", "docs/SYSTEM_STATE.md", "docs/SHADOW_GENOME.md")`. `backup_dir(base, session_id) -> Path` joins `.agent/local-backup/governance/<sid>` after `session.validate_session_id`. `ensure_session_backup(base, session_id) -> Path | None`: returns existing dir when `.complete` marker present; otherwise copies each existing DNA file byte-for-byte, writes `.complete` (JSON manifest: relpath -> sha256, copied ts passed in by caller), returns the dir; catches OSError and returns None (fail-open contract). `restore(base, source_dir, force=False) -> list[dict]`: copies each file present in source back to `docs/` with a NO-CLOBBER default -- a destination file that already exists is skipped (reported `{path, action: "skipped-exists"}`) unless `force=True`, so a restore can never silently destroy state newer than the snapshot; returns per-file `{path, sha256, action}` report, and appends ONE severity-3 `governance-state-loss` shadow event (attribution UPSTREAM) recording the restored set. `prior_initialization_evidence(base) -> str | None`: backup-dir check first (no subprocess), then `git log -1 --format=%H -- docs/META_LEDGER.md` (list argv, check=False, timeout=5, cwd=base); returns a one-line evidence string or None. `main(argv)`: `backup --session <sid>`, `restore --from <dir>`, `evidence` subcommands; exit 0/1.

### Unit Tests

- tests/test_governance_snapshot.py::test_backup_copies_dna_files_byte_identical - after ensure_session_backup, each existing DNA file in the backup dir hashes identically to the source
- tests/test_governance_snapshot.py::test_backup_is_idempotent_per_session - mutate a source file after the first backup; the second ensure_session_backup call returns without re-copying (backup bytes unchanged, marker preserved)
- tests/test_governance_snapshot.py::test_backup_tolerates_missing_files - a base with only 3 of 5 DNA files backs those 3 up and records them in the manifest; no raise
- tests/test_governance_snapshot.py::test_restore_returns_byte_identical_report_and_emits_event - delete the source files, restore from backup, assert bytes match the pre-delete hashes AND exactly one governance-state-loss event (severity 3) appended to the shadow log (QOR_ROOT-redirected)
- tests/test_governance_snapshot.py::test_prior_evidence_from_git_history - tmp git repo with a committed-then-deleted ledger: evidence string names git history; a bare tmp dir returns None
- tests/test_governance_snapshot.py::test_prior_evidence_from_backup_dir - no git repo, but a populated backup dir: evidence string names the backup path
- tests/test_governance_snapshot.py::test_restore_no_clobber_skips_existing_files - restoring onto a base where a DNA file still exists leaves that file's bytes untouched and reports it skipped; `force=True` overwrites
- tests/test_governance_snapshot.py::test_cli_backup_and_restore_exit_codes - main(["backup","--session",sid]) exits 0 and creates the dir; restore from a missing dir exits 1

## Phase 2: Write-path hook + recovery-aware routing (TDD first)

### Affected Files

- tests/test_governance_snapshot.py - hook + routing test group (same file)
- tests/test_governance_health.py - two routing cases appended
- qor/scripts/gate_chain.py - `_ensure_dna_backup(sid)` best-effort call at the top of the authorized write path
- qor/scripts/governance_health.py - `_NEXT_RESTORE`; `_classify_missing(rel_path, initialized, prior_evidence=None)`; evidence computed once per `check_governance_health` run only when not initialized
- qor/gates/schema/shadow_event.schema.json - enum gains `governance-state-loss`
- .gitignore - `.agent/local-backup/` entry

### Changes

`gate_chain.write_gate_artifact`: after `sid` resolution and before `vga.write_artifact`, call `_ensure_dna_backup(sid)` -- a 6-line module function that lazily imports governance_snapshot, calls `ensure_session_backup(_workdir.root(), sid)` inside `try/except Exception` with a stderr WARN on failure (KeyboardInterrupt/SystemExit propagate, matching the Phase 57 hook invariant). `governance_health`: `_classify_missing` gains `prior_evidence: str | None = None`; when `not initialized and prior_evidence`, return `ArtifactFinding(rel_path, ArtifactStatus.MISSING, f"previously initialized ({prior_evidence}); governance state lost", _NEXT_RESTORE)`; `check_governance_health` computes evidence once (only when `not initialized`) and threads it through `_classify_one` via keyword. Schema enum + .gitignore lines are one-line additive edits.

### Unit Tests

- tests/test_governance_snapshot.py::test_write_gate_artifact_triggers_session_backup - a gate write under a tmp QOR_ROOT creates `.agent/local-backup/governance/<sid>/` containing the DNA files present
- tests/test_governance_snapshot.py::test_backup_failure_never_breaks_gate_write - monkeypatch ensure_session_backup to raise; write_gate_artifact still persists the artifact and returns its path
- tests/test_governance_health.py::test_previously_initialized_loss_routes_to_restore_not_bootstrap - tmp git repo with committed-then-deleted DNA: finding status MISSING, legal_next names governance_snapshot restore and /qor-remediate, and does NOT contain "bootstrap"
- tests/test_governance_health.py::test_never_initialized_workspace_still_routes_to_bootstrap - bare tmp dir (no git history, no backup): UNINITIALIZED with the bootstrap legal_next (regression lock on the unchanged path)
- tests/test_governance_snapshot.py::test_state_loss_event_validates_against_schema - the event appended by restore validates against shadow_event.schema.json (proves the enum amendment)

## Phase 3: Doctrine

### Affected Files

- qor/references/doctrine-governance-enforcement.md - new section: governance-state durability (snapshot lifecycle, git clean hazard, restore procedure)

### Changes

New numbered section documenting: which five files are snapshotted and when (first governed gate write per session); where (`.agent/local-backup/governance/<sid>/`, gitignored); the `git clean` hazard table (`-fd` spares the tracked docs/ set in this repo but destroys gitignored consumer state; `-fdx` also destroys the backups -- the snapshot narrows, not eliminates, the loss window); the restore procedure (`qor-logic scripts governance_snapshot restore --from <dir>` then `/qor-remediate`); the routing rule (previously-initialized-now-missing is MISSING/restore, never UNINITIALIZED/bootstrap); the `governance-state-loss` event contract (restore-time, severity 3). Prose stays descriptive (no glossary definition patterns).

## Feature Inventory Touches

(empty -- governance tooling; no user-touchable feature row in FEATURE_INDEX.md)

## Definition of Done

### Deliverable: governance-DNA durability

- **D1**: A month-long silent loss cannot recur undetected with bootstrap as the suggested recovery: every gate-writing session leaves a same-session snapshot, and the health gate distinguishes prior-initialization loss from a genuinely new workspace, routing to restore-then-remediate (GH #267).
- **D2**: `qor/scripts/governance_snapshot.py` (backup/restore/evidence + CLI, fail-open contract); `gate_chain._ensure_dna_backup` hook; `governance_health._classify_missing(prior_evidence=...)` + `_NEXT_RESTORE`; schema enum + .gitignore additive lines. No SKILL.md byte added.
- **D3**: Ledger entries for plan/audit/implement/seal; doctrine section shipped; GH #267 disposition recorded with the restore-routing rationale; no new gate schema (shadow_event amendment is registered-schema additive).
- **D4**: `test_rerun...` n/a -- the binding observations are `test_previously_initialized_loss_routes_to_restore_not_bootstrap` (routing), `test_backup_failure_never_breaks_gate_write` (fail-open write path), and `test_restore_returns_byte_identical_report_and_emits_event` (recovery fidelity + taxonomy).

## CI Commands

- `python -m pytest tests/test_governance_snapshot.py tests/test_governance_health.py -q` - focused suite (run twice for determinism)
- `python -m pytest -q` - full suite; locks the write-path hook against every gate-writing test and the health-gate consumers
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - ledger chain integrity across the phase's entries
