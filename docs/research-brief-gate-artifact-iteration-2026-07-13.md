# Research Brief

**Date**: 2026-07-13T03:36:43Z
**Analyst**: The Qor-logic Analyst
**Target**: GH #237 -- iteration-versioned gate artifacts (one seal, one immutable file)
**Scope**: gate-artifact write path, prior-artifact resolution, audit history binding,
provenance sidecars, seal-side consumers of the singleton path

---

## Executive Summary

`write_gate_artifact` persists every phase artifact at a mutable singleton path
(`.qor/gates/<sid>/<phase>.json`); a re-run of the same phase (audit VETO->PASS,
substantiate FAIL->SEAL) overwrites the prior artifact AND its provenance sidecar
in place, destroying evidence a ledger seal may already bind. A live repro in this
session confirmed the overwrite. The fix surface is small and additive: the writer
(`validate_gate_artifact.write_artifact`), the governed wrapper (`gate_chain.
write_gate_artifact`), the resolver (`check_prior_artifact` / `read_phase_artifact`),
and `audit_history.append`. All seal-side consumers read the singleton path, so the
singleton must remain as a byte-identical latest copy.

## Findings

### F1. Singleton overwrite (the defect)

- `qor/scripts/validate_gate_artifact.py:123` (`write_artifact`): validates payload,
  then writes `.qor/gates/<sid>/<phase>.json` via tempfile + `os.replace` --
  unconditional in-place overwrite. No iteration concept exists anywhere.
- `qor/scripts/gate_chain.py:239` (`write_gate_artifact`): the governed entry.
  Order of effects: provenance env check -> `vga.write_artifact` -> (audit only)
  `audit_history.append` -> `gate_provenance.write_sidecar` -> gate-written hook.
- `qor/scripts/gate_provenance.py:95` (`sidecar_path`): `with_suffix(".provenance")`
  -- the sidecar shares the singleton stem, so a re-run also overwrites
  `<phase>.provenance`. The evidence and its tamper-evidence binding die together.
- **Live repro (this session)**: two `write_gate_artifact("audit", ...)` calls
  against a scratch `QOR_ROOT` returned the identical path (`audit.json`); the
  first write's SHA-256 no longer matched after the second write; the session dir
  contained only `audit.json`, `audit.provenance`, `audit_history.jsonl`.

### F2. Prior-artifact resolution reads the singleton only

- `qor/scripts/gate_chain.py:59` (`check_prior_artifact`): resolves
  `GATES_DIR/<sid>/<prior>.json` directly (line 80).
- `qor/scripts/gate_chain.py:198` (`read_phase_artifact`): same singleton read.
- `qor/scripts/gate_chain.py:109` (`_check_short_chain_plan`) and
  `tier_guard.declared_artifacts` read `plan.json` (singleton).

### F3. Audit history has no file binding

- `qor/scripts/audit_history.py:34` (`append`): appends the payload as a JSONL row
  after schema validation; rows carry NO filename, so a history row cannot be tied
  to bytes on disk. This is the loop GH #237 item 3 closes.
- `qor/gates/schema/audit.schema.json` declares `additionalProperties: true`, so an
  added `artifact_filename` row field validates WITHOUT a schema amendment (no
  `gate_schema_freeze_lint` exposure; the registry stays untouched).

### F4. Seal-side consumers of the singleton path (compat surface)

- `qor/reliability/gate_chain_completeness.py:20,53` -- substantiate Step 7.8 + CI
  validate `<sid>/<phase>.json` per sealed session.
- `qor/scripts/gate_provenance.py:206` (`verify_committed`) -- CI merge gate
  recomputes `payload_sha256` of committed `<ph>.json` against `<ph>.provenance`.
- `qor/scripts/evidence_bundle.py:80,98,118` -- `_gate_artifacts`, `_provenance`,
  `_audit_history` all join on singleton names.
- `qor/gates/chain.md:16` -- documented artifact location contract.
- Tests locking current behavior: `tests/test_gates.py`,
  `tests/test_audit_gate_artifact.py`, `tests/test_gate_chain_audit_history.py`,
  `tests/test_audit_history.py`, `tests/test_gate_chain_provenance.py`,
  `tests/test_gate_chain_fires_hook.py`, `tests/test_evidence_bundle.py`.

### F5. Write-path invariants worth preserving

- Atomic write discipline (tempfile + `os.replace`) at
  `qor/scripts/validate_gate_artifact.py:133-141` -- keep for both file classes.
- Provenance env binding (`QOR_SKILL_ACTIVE`, Phase 52/GAP-GOV-04) at
  `qor/scripts/gate_chain.py:273-285` -- untouched by this change.
- Hook fail-open semantics (`_fire_gate_written_hook`, `gate_chain.py:302`) --
  the event's `artifact_path` should carry the exact (versioned) evidence path.
- `validate_all_current_session` (`validate_gate_artifact.py:92`) iterates
  singleton names only; unchanged behavior is acceptable (latest copy is valid).

## Blueprint Alignment

`docs/ARCHITECTURE_PLAN.md` does not specify gate-artifact storage; the operative
contract is `qor/gates/chain.md`.

| Contract claim | Actual finding | Status |
|----------------|---------------|--------|
| chain.md:16 "Runtime: `.qor/gates/<session_id>/<phase>.json`" | Matches code; but multi-iteration phases overwrite in place | MATCH (contract silent on iterations -- gap GH #237 fills) |
| chain.md:78 "Audit VETO -> implement should not proceed" | VETO->PASS re-run destroys the VETO evidence | DRIFT (evidence loss; the defect under research) |
| audit_history docstring "singleton remains authoritative" (audit_history.py:9-12) | True today; GH #237 keeps singleton as latest copy, adds immutable per-iteration files | MATCH (posture preserved additively) |

## Recommendations

1. (P0) Version the write: `write_artifact` emits `<phase>-iter<N>.json` (never
   overwrites; N = max existing + 1) and refreshes the singleton `<phase>.json` as a
   byte-identical latest copy. Return the versioned path so downstream bindings
   (sidecar, hook) reference immutable evidence.
2. (P0) Sidecar duality: write `<phase>-iter<N>.provenance` for the versioned file
   AND refresh `<phase>.provenance` beside the singleton (identical bytes ->
   identical digests keeps `verify_committed` + `evidence_bundle` green).
3. (P0) Resolution: `check_prior_artifact` / `read_phase_artifact` resolve the
   highest iteration, falling back to the singleton for legacy (pre-change) session
   dirs. No retroactive migration.
4. (P1) `audit_history.append` gains `artifact_filename` (versioned name) per row.
5. (P1) Document in `qor/gates/chain.md` (artifact locations + iteration section).
6. (P2) Regression test sealing iter-1's hash, re-running the phase, asserting the
   sealed bytes still exist and hash identically (GH #237 acceptance).

## Updated Knowledge

No Shadow Genome entry needed (no failed approach; defect already recorded as a
generalized incident in GH #237). Doctrine touch-point deferred to the plan:
`qor/gates/chain.md` is the canonical doc to amend.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
