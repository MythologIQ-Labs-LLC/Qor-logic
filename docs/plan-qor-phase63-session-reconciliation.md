# Plan: Phase 63 — Session reconciliation: rebase + renumber onto origin/main

**change_class**: breaking

**doc_tier**: system

**originating_remediation**: divergence discovered during qor-debug worktree inspection — local main is 55 commits ahead AND 45 commits behind origin/main; my session's Phase 45-61 collides with upstream's Phase 49-58 in numbering AND version space.

**terms_introduced**:
- term: session reconciliation
  home: qor/references/doctrine-governance-enforcement.md
- term: rebase + renumber protocol
  home: docs/plan-qor-phase63-session-reconciliation.md
- term: chain-rewrite event
  home: docs/META_LEDGER.md

**boundaries**:
- limitations:
  - This plan **breaks the META_LEDGER chain** between Entry #148 (Phase 45 seal) and Entry #164 (Phase 61 seal). Those 17 entries are abandoned. Replayed entries get fresh numbers + chain hashes derived from upstream's last entry.
  - Tags v0.45.0 through v0.59.0 (plus v0.54.1 hotfix) are abandoned and deleted post-reconciliation. New tags re-issue starting from upstream's last shipped version.
  - The reconciliation branch DOES NOT preserve session commit hashes. Cherry-pick or rebase rewrites all SHAs.
- non_goals:
  - Recovering chain-hash continuity across the rewrite (the rewrite IS the discontinuity; documented in the closing seal entry).
  - Merging Phase 59 ideation work from worktree `busy-williams-270b35` into this phase (handled as a separate post-reconciliation phase or operator-decision).
- exclusions:
  - No changes to source code semantics. Reconciliation preserves the WHAT of session deliverables (GH issue closures, prompt compiler, qor-debug remediation) and only changes the WHERE (renumbered phases + tags + ledger entries).
  - No changes to worktree commit history. Worktrees stay untouched until the operator separately decides their fate.

## Open Questions

1. **Phase 59 ideation work in `busy-williams-270b35`** is unmerged (their Phase 59 = `/qor-ideate` v0.45.0). Should it land BEFORE or AFTER session-replay? Default: after, as a separate phase post-reconciliation. Operator may override.
2. **Session deliverables that overlap upstream**: my Phase 47 host-repo posture (#38 + B23) added `host_capability`. Upstream Phase 47 has different work. The two are independent surfaces — no semantic overlap detected — but the implementer verifies during replay. If an overlap is found, the session phase is renumbered AND re-scoped to delta-only against upstream.

## Phase 1: Pre-flight inventory + branch preservation

### Affected Files

- `docs/reconciliation-2026-05-11.md` — NEW. Per-phase comparison matrix (session phase → upstream equivalent → reconciliation decision). One row per session phase 45-61 plus the qor-debug Phase 60-61 hotfix work.
- `tests/test_reconciliation_inventory.py` — NEW. Asserts the matrix file exists and lists exactly 17 session phases + their renumbered targets.

### Changes

`docs/reconciliation-2026-05-11.md` carries a table with columns:

| Session phase | Session deliverable | Upstream phase touching same surface | Overlap? | Decision | New phase number | New version |

Decision values: `replay` (no overlap; renumber and replay), `merge` (partial overlap; consolidate session delta into one renumbered phase), `drop` (full overlap; session work duplicates upstream and is discarded).

Operator reviews the matrix before Phase 2 executes.

Branch preservation:

```bash
git branch archive/session-2026-05-09 main
```

Creates a permanent forensic reference. The session's original commit history survives on this branch even after main is rebased.

### Unit Tests

- `tests/test_reconciliation_inventory.py::test_matrix_lists_all_seventeen_session_phases` — count session-phase rows.
- `tests/test_reconciliation_inventory.py::test_matrix_decision_values_are_closed_enum` — each row has decision in `{replay, merge, drop}`.
- `tests/test_reconciliation_inventory.py::test_matrix_replay_rows_assign_unique_new_phase_numbers` — no two replayed phases get the same new number.
- `tests/test_reconciliation_inventory.py::test_archive_branch_exists` — `git rev-parse archive/session-2026-05-09` returns a valid SHA.

## Phase 2: Fetch + rebase to canonical upstream

### Affected Files

- `.git/refs/heads/main` — reset to `origin/main`.
- All session phase files under `docs/plan-qor-phase{45..61}-*.md` — physically renamed to their reconciled phase numbers (per matrix).
- `docs/META_LEDGER.md` — session entries #148-164 abandoned; replaced with replayed entries starting from upstream's last entry id + 1.
- `CHANGELOG.md` — session sections (`[0.45.0]` through `[0.59.0]` + `[0.54.1]`) removed; replayed sections appended starting from upstream's last version + 1.
- `pyproject.toml` — version reset to upstream's last shipped version (then incremented per replay phase).

### Changes

Sequence:

```bash
git fetch origin
git checkout main
git reset --hard origin/main      # canonical upstream is now main
# session work preserved on archive/session-2026-05-09 from Phase 1
```

Capture upstream's terminal state:
- `UPSTREAM_LAST_ENTRY_NUM` — read from `docs/META_LEDGER.md` largest `Entry #N`
- `UPSTREAM_LAST_CHAIN_HASH` — read from same entry's `Chain Hash` field
- `UPSTREAM_LAST_VERSION` — read from `pyproject.toml`
- `UPSTREAM_LAST_PHASE_NUM` — read from largest sealed-phase number across `git tag --list 'v*'` and `docs/plan-qor-phase*.md`

These four values seed the replay sequence in Phase 3.

### Unit Tests

- `tests/test_reconciliation_baseline.py::test_main_at_origin_after_reset` — `git rev-parse main` equals `git rev-parse origin/main`.
- `tests/test_reconciliation_baseline.py::test_session_entries_absent_after_reset` — META_LEDGER does not contain Entry #148-164 references.
- `tests/test_reconciliation_baseline.py::test_archive_branch_preserves_session_state` — `git log archive/session-2026-05-09` includes all 17 session seal commits.

## Phase 3: Per-phase replay loop

### Affected Files

- For each session phase marked `replay` in the matrix:
  - `docs/plan-qor-phase{NEW_NUM}-{session-slug}.md` — copy from archive branch with header `Phase {NEW_NUM}` substituted for `Phase {SESSION_NUM}`.
  - `qor/` source files from the session phase — cherry-pick the corresponding commit onto current main; resolve any CHANGELOG / pyproject conflicts deterministically (rewrite to new version).
  - `docs/META_LEDGER.md` — append a fresh seal entry: new `Entry #N`, new chain anchored to upstream-last-chain (or prior replay's chain).
  - `CHANGELOG.md` — append a `[NEW_VERSION]` section copied from archive with phase-number references updated.
  - New tag `v{NEW_VERSION}`.

### Changes

Replay protocol per phase (executed in original session order — 45, 46, 47, ..., 61):

1. Cherry-pick the session phase's `plan:` and `implement:` and `seal:` commits from `archive/session-2026-05-09` onto current main.
2. Resolve CHANGELOG conflict by replacing the session's `## [OLD_VERSION] - ...` section with `## [NEW_VERSION] - ...` matching this phase's reconciled identity.
3. Resolve pyproject conflict by setting version to `NEW_VERSION`.
4. Rename the plan file from `plan-qor-phase{OLD_NUM}-*.md` to `plan-qor-phase{NEW_NUM}-*.md`; update internal phase-number references via sed.
5. Append fresh META_LEDGER seal entry with computed hashes against the now-current chain head.
6. Step 6.8 self-validate the new entry's hashes via `hash_guard.validate_sha256`.
7. Create annotated tag `v{NEW_VERSION}` at the seal commit.

For phases marked `merge` in the matrix: the implementer authors a new combined plan file describing the consolidated delta and seals it as one new phase rather than replaying separately.

For phases marked `drop`: skip entirely; document in the closing seal entry that the session work was redundant.

### Unit Tests

- `tests/test_reconciliation_replay.py::test_every_replayed_phase_has_seal_entry` — for each new phase number, META_LEDGER has a corresponding seal entry.
- `tests/test_reconciliation_replay.py::test_replayed_chain_hashes_form_valid_merkle_sequence` — `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` returns 0 across all replayed entries.
- `tests/test_reconciliation_replay.py::test_every_replayed_phase_has_tag` — `git tag --list v{NEW_VERSION}` matches the new version for each non-dropped phase.
- `tests/test_reconciliation_replay.py::test_dropped_phases_documented_in_closing_seal` — closing seal entry names every dropped session phase with rationale.
- `tests/test_reconciliation_replay.py::test_changelog_sections_match_replayed_versions` — CHANGELOG has one section per non-dropped replayed phase, no orphan section references.

## Phase 4: Worktree decision + tag cleanup

### Affected Files

- `.claude/worktrees/{busy-williams-270b35, fervent-easley-26be58}` — operator inspects dirty state, archives any unique deliverables (e.g., `busy-williams/.qor/hooks/`, the Phase 59 ideation work-in-progress files), then deletes via `git worktree remove --force`.
- Local tags `v0.32.0` through `v0.44.0` (worktree-claimed) — delete after archival via `git tag -d v0.{32..44}.0`.
- Local tags `v0.45.0` through `v0.59.0` + `v0.54.1` (session-abandoned) — delete after replay completes via `git tag -d v0.{45..59}.0 v0.54.1`.
- `docs/reconciliation-2026-05-11.md` — append "Worktree archival inventory" section listing what was preserved (paths + brief description) before deletion.

### Changes

```bash
# Per worktree, capture any dirty state worth preserving
git -C .claude/worktrees/busy-williams-270b35 stash list
git -C .claude/worktrees/busy-williams-270b35 status --short  # already inspected
tar -czf archives/busy-williams-270b35-dirty-state-2026-05-11.tar.gz .claude/worktrees/busy-williams-270b35/{.qor,docs/PROCESS_SHADOW_GENOME_UPSTREAM.md}

# Then remove
git worktree remove --force .claude/worktrees/busy-williams-270b35
git worktree remove --force .claude/worktrees/fervent-easley-26be58

# Delete the abandoned tags
git tag -d v0.32.0 v0.33.0 v0.34.0 v0.35.0 v0.36.0 v0.37.0 v0.38.0 v0.39.0 v0.40.0 v0.41.0 v0.42.0 v0.43.0 v0.44.0
git tag -d v0.45.0 v0.46.0 v0.47.0 v0.48.0 v0.49.0 v0.50.0 v0.51.0 v0.52.0 v0.53.0 v0.54.0 v0.54.1 v0.55.0 v0.56.0 v0.57.0 v0.58.0 v0.58.1 v0.59.0
```

Worktree branches (`phase/52-...`, `phase/59-...`) remain in the ref namespace but no longer have working trees attached. Operator decides separately whether to delete those branches.

### Unit Tests

- `tests/test_reconciliation_cleanup.py::test_no_worktrees_remain` — `git worktree list` returns only the main worktree.
- `tests/test_reconciliation_cleanup.py::test_abandoned_session_tags_removed` — none of v0.45.0-v0.59.0 / v0.54.1 are present in `git tag --list`.
- `tests/test_reconciliation_cleanup.py::test_worktree_archival_recorded` — `docs/reconciliation-2026-05-11.md` contains a "Worktree archival inventory" section with at least one entry per removed worktree.
- `tests/test_reconciliation_cleanup.py::test_changelog_tag_coverage_passes` — `python -m pytest tests/test_changelog_tag_coverage.py` exits 0 (after old tags are deleted, the pre-existing failure resolves).

## Phase 5: Closing seal + push

### Affected Files

- `docs/META_LEDGER.md` — append CLOSING SEAL entry documenting the reconciliation event itself (the chain-rewrite). This entry chains from the last replayed phase's chain hash.
- `qor/references/doctrine-governance-enforcement.md` — new §10.10 "Session reconciliation protocol" documenting the rebase+renumber discipline so future divergences have a precedent.
- Push to remote: `git push origin main --tags`.

### Changes

Closing seal entry body:

```markdown
### Entry #{N}: SESSION RECONCILIATION SEAL

**Timestamp**: <ISO>
**Phase**: SEAL (reconciliation)
**Author**: Governor + Judge (operator-led)
**Verdict**: PASS (X tests passing)

**Scope**: Session 2026-05-09 work-stream (originally Phase 45-61) replayed onto canonical upstream (origin/main at Phase 1-58) starting at Phase {UPSTREAM_LAST + 1}. Original chain entries #148-164 abandoned; archive branch `archive/session-2026-05-09` preserves the original commit history for forensic reference.

**Chain-rewrite notice**: this entry breaks chain continuity from session entries #148-164 by design. The new chain anchors at upstream's last entry (Entry #{UPSTREAM_LAST_ENTRY_NUM}) and is sequential thereafter. Verifiers reading entries with phase numbers in [45, 61] in `archive/session-2026-05-09` should treat them as historical artifacts.

**Dropped phases**: {list with rationale}.
**Merged phases**: {list of consolidations}.
**Replayed phases**: {Phase OLD -> NEW mapping}.
**New version**: {final}. Tags v0.45.0-v0.59.0 + v0.54.1 deleted as part of the reconciliation.

**Content Hash**: ...
**Previous Hash**: ...
**Chain Hash**: ...
```

Doctrine update for future divergences:

```markdown
### §10.10 Session reconciliation protocol (Phase 63 wiring)

When a local session work-stream diverges from origin/main in phase numbering AND version space (both ahead and behind on a fork), the canonical timeline is origin/main. Session work is REBASED + RENUMBERED rather than force-pushed. The protocol:

1. Capture session state on `archive/session-{DATE}` for forensics.
2. Reset local main to origin/main.
3. Replay session phases sequentially with renumbered phase + version identifiers.
4. Each replay is a fresh META_LEDGER seal entry chained from upstream's last entry (not from any session entry).
5. Old session tags are deleted after replay completes.
6. A CLOSING SEAL documents the reconciliation event itself; the dropped chain-continuity is intentional.
```

### Unit Tests

- `tests/test_reconciliation_close.py::test_closing_seal_present` — META_LEDGER has a `SESSION RECONCILIATION SEAL` entry with phase label.
- `tests/test_reconciliation_close.py::test_closing_seal_lists_old_to_new_mapping` — entry body cites every replayed phase with old → new phase numbers.
- `tests/test_reconciliation_close.py::test_doctrine_10_10_added` — `doctrine-governance-enforcement.md` contains `§10.10 Session reconciliation protocol`.
- `tests/test_reconciliation_close.py::test_ledger_verifies_end_to_end` — `ledger_hash.verify` returns 0 across the full chain including the closing seal.
- `tests/test_reconciliation_close.py::test_local_main_matches_origin_main_after_push` — `git rev-parse main` equals `git rev-parse origin/main` (after operator pushes; this test runs post-push or is marked operator-confirmation).

## CI Commands

- `python -m pytest tests/test_reconciliation_inventory.py -v` — Phase 1 inventory shape
- `python -m pytest tests/test_reconciliation_baseline.py -v` — Phase 2 reset state
- `python -m pytest tests/test_reconciliation_replay.py -v` — Phase 3 replay coverage
- `python -m pytest tests/test_reconciliation_cleanup.py -v` — Phase 4 worktree + tag cleanup
- `python -m pytest tests/test_reconciliation_close.py -v` — Phase 5 closing seal
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py` — full suite under reconciliation-in-progress state; this deselect lifts in Phase 4
- `python -m pytest` — full suite WITHOUT deselect after Phase 4 tag cleanup (the historical deselect resolves once worktree tags are gone)
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` — verifies the replayed + closing-seal chain
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase63-session-reconciliation.md` — self-application
