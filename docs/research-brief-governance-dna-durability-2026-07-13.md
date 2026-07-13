# Research Brief

**Date**: 2026-07-13T05:17:00Z
**Analyst**: The Qor-logic Analyst
**Target**: GH #267 -- local-only governance DNA files have no durability mechanism
**Scope**: governance-health classification gap, backup/restore infrastructure absence,
snapshot trigger placement under the skill-size budget, event-taxonomy fit

---

## Executive Summary

A consumer repository lost its five gitignored governance DNA files to `git clean`
and the loss went undetected for a month because nothing snapshots them, and
governance-health classifies total loss as UNINITIALIZED -- routing toward
bootstrap, which would have destroyed the recoverable history. All load-bearing
claims verified against source. Key design constraint discovered: BOTH big
governance SKILL.md files sit within 70 bytes of the 40 KB EXCEEDED budget, so the
backup-on-write trigger cannot be new skill prose -- it must live in the Python
write path the skills already call.

## Findings

### F1. The classification gap is binary initialization detection

- `qor/scripts/governance_health.py:87-91` (`_is_initialized`): a workspace is
  "initialized" iff `docs/META_LEDGER.md` or a `_PROJECT_DNA` file EXISTS NOW.
  Total loss of all DNA files therefore reads as never-initialized.
- `qor/scripts/governance_health.py:94-98` (`_classify_missing`): `not initialized`
  -> `UNINITIALIZED` with `legal_next = _NEXT_BOOTSTRAP` (line 81) -- the exact
  routing the incident report calls destructive. No branch consults git history or
  any backup location.
- In THIS repository the DNA files are tracked (git ls-files confirms; `.gitignore`
  has no `docs/` or `.agent` entries), so the loss scenario applies to CONSUMER
  workspaces where operators keep them local-only. Any fix must work for both.

### F2. Zero backup/snapshot infrastructure exists

- `grep -rn "local-backup|backup_dna|governance_snapshot" qor --include=*.py`: 0
  hits. No backup-on-write, no session-close snapshot, no restore helper.
- `.agent/` currently holds only `staging/` (transient); `.agent/local-backup/` is
  net-new surface. `.agent` is not gitignored in this repo (verified), so the new
  path must be added to `.gitignore` (backups are operator-local state, and in
  consumer repos they must survive `git clean -fdx` no better than the originals --
  the snapshot's value is against ACCIDENTAL clean of docs/, and `git clean -fd`
  without `-x` spares ignored files only when untracked-ignored; therefore the
  doctrine must state plainly which loss classes the snapshot does and does not
  survive).

### F3. The snapshot trigger cannot be skill prose (byte budget)

- `qor/skills/governance/qor-substantiate/SKILL.md` = 40,929 bytes; EXCEEDED
  threshold = 40,960 (`qor/scripts/skill_size_budget_lint.py:23-24`): 31 bytes of
  headroom. `qor-audit/SKILL.md` = 40,890 (70 bytes). Even a one-line snapshot
  step exceeds the budget.
- Structural alternative verified: every gate-writing skill already funnels
  through `gate_chain.write_gate_artifact` (`qor/scripts/gate_chain.py:241`) under
  the QOR_SKILL_ACTIVE provenance check. A first-write-of-session hook there is
  zero SKILL.md bytes, cannot drift out of prose, and covers substantiate, audit,
  remediate, research, plan, implement alike.
- Hook posture: best-effort (WARN on failure, never breaks the governed write) --
  mirrors the Phase 57 gate-written hook's fail-open contract at
  `qor/scripts/gate_chain.py:306-329`; a failed BACKUP must not abort a seal.

### F4. Event taxonomy

- `qor/gates/schema/shadow_event.schema.json` event_type enum (10 values) lacks
  `governance-state-loss` (verified). The incident used `degradation`. The enum is
  closed by design ("no other escape hatch -- deliberate schema amendment",
  doctrine-governance-enforcement). Adding one value is an additive amendment to a
  REGISTERED schema; `gate_schema_freeze_lint` compares registry presence, not
  content, so no freeze friction.

### F5. Reusable infrastructure

- Session identity: `qor/scripts/session.py` (`current()`, SESSION_ID_PATTERN) --
  names the per-session backup dir.
- Prior-initialization evidence: `git log -1 -- docs/META_LEDGER.md` (cheap,
  read-only) OR non-empty `.agent/local-backup/governance/`.
- Test conventions: `tests/test_governance_health.py` covers the current taxonomy
  (bare workspace -> UNINITIALIZED at line 27-31; initialized-missing at 34-39);
  no test covers previously-initialized-now-missing -- the new behavioral cases
  slot beside them.

## Blueprint Alignment

`docs/ARCHITECTURE_PLAN.md` is silent on durability; operative contracts are
`qor/references/doctrine-governance-enforcement.md` (routing invariants, section
"No Ungoverned Path Forward") and the health-gate taxonomy.

| Contract claim | Actual finding | Status |
|----------------|---------------|--------|
| Doctrine: UNINITIALIZED may seed/bootstrap | Total post-loss state classifies as UNINITIALIZED -> bootstrap over recoverable history | DRIFT (the defect: loss is indistinguishable from newness) |
| Doctrine: DAMAGED/INCOMPLETE never seeded | Unchanged; the fix adds a restore route, does not weaken this | MATCH |
| Skill budget: WARN 25 KB / EXCEEDED 40 KB | Both big skills within 70 bytes of EXCEEDED; prose trigger impossible | MATCH (constraint honored by the write-path design) |

## Recommendations

1. (P0) `qor/scripts/governance_snapshot.py`: `backup(base, session_id)` copies the
   five DNA files to `.agent/local-backup/governance/<session_id>/` (idempotent via
   a completion marker), `restore(base, source_dir)` copies back with byte-hash
   report, `prior_initialization_evidence(base)` returns git-history/backup-dir
   evidence. CLI verbs via the generic `qor-logic scripts` runner.
2. (P0) First-write-of-session hook in `gate_chain.write_gate_artifact`
   (best-effort, fail-open, zero skill-prose bytes).
3. (P0) `governance_health._classify_missing`: when not "initialized" but prior
   initialization evidence exists, classify MISSING with a new
   restore-then-remediate `legal_next` -- never UNINITIALIZED/bootstrap.
4. (P1) Add `governance-state-loss` to the shadow-event enum; the health gate emits
   it (severity 3) when it detects the loss state.
5. (P1) Doctrine section: `git clean` hazard, snapshot lifecycle, which loss
   classes the snapshot does/does not survive, restore procedure.
6. (P2) `.gitignore` gains `.agent/local-backup/`.

## Updated Knowledge

No Shadow Genome entry (incident already recorded in GH #267 with a remediation
gate artifact on the consumer side). Doctrine touch-point lands with the plan.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
