# Research Brief

**Date**: 2026-08-18
**Analyst**: The Qor-logic Analyst
**Target**: GH #352 (CI-side intent-lock verification for sealed sessions)
**Scope**: what is now verifiable in CI; the walker to reuse; check semantics per artifact class

---

## Executive Summary

Phase 231 made the prerequisite real: two sealed sessions (231, 232) have committed lock records and snapshots (`git ls-files` confirms all six files tracked). The verification walker pattern already exists -- `gate_chain_completeness._extract_seal_sessions(text, phase_min)` maps SEAL entries to session ids and its CI job is the natural host. A new `qor.reliability.intent_lock_committed` checks, for every sealed session at or above the phase-231 grandfather boundary: the record and both snapshots are present in the checkout, each snapshot's LF-normalized sha256 equals its recorded hash (self-consistency), and the recorded `plan_hash` equals the hash of the committed plan file (referent match -- checkable for the plan, whose file persists; the audit report is overwritten each phase, so its snapshot IS the preserved referent and self-consistency is the whole check). Exit 1 on any failure; one step added to the existing `gate-chain-completeness` CI job. This closes #16798's asymmetry for every session going forward: the lock's guarantee stops depending on the person it constrains.

## Findings

### 1. Committed evidence, verified

`git ls-files` shows all six files for sessions `2026-08-17T2339-3385b4` (phase 231) and `2026-08-18T0249-c4b1be` (phase 232) tracked -- the seal_stage force-add working across two seals. Legacy sessions (phase < 231) have no committed evidence by design; the boundary is a constant in the checker, mirroring the phase-52 grandfather in the sibling gate.

### 2. Check semantics per artifact

- Record present; both snapshots present -- absence is a ceremony failure.
- `sha256(normalized(snapshot)) == recorded hash` for plan and audit -- tamper evidence (this is exactly the binding the #344 incident broke, now CI-checked).
- `recorded plan_hash == _hash_file(committed plan at recorded plan_path)` -- the referent match; feasible because the plan file persists after seal. The audit report path is reused by every later phase, so referent-matching it would false-fail immediately; the snapshot is its preserved referent (stated in the module docstring, not silently skipped).

### 3. Reuse surface

- `gate_chain_completeness._extract_seal_sessions` (line 33) parses SEAL entries to `{phase: session}` -- reused, not reimplemented.
- `intent_lock._hash_file` / `_normalized` are the canonical hashers -- imported, not duplicated.
- CI host: the `gate-chain-completeness` job (ci.yml:76) already checks sealed-state invariants with a full-history checkout and `pip install -e ".[dev]"`; one `python -m qor.reliability.intent_lock_committed` step follows the existing two.

### 4. Live-repo test honesty

The repo's own tracked evidence makes a live test environment-honest (full checkout carries the files; no operator-local paths): the real ledger walked at phase_min 231 must verify clean, and that test is the anti-recurrence binding in the same spirit as the veto-pattern ledger test.

## Blueprint Alignment

| Claim | Actual Finding | Status |
|---|---|---|
| #352: committed artifacts make a CI job possible | Two sealed sessions' evidence tracked; walker and hashers shipped | MATCH |
| #352: legacy must never be swept in | phase_min boundary constant; legacy dirs untracked anyway | MATCH |

## Recommendations

1. Phase 233 (feature): `qor/reliability/intent_lock_committed.py` + behavioral tests (tmp-repo valid/tampered/missing + live-repo clean) + one CI step.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
