# Research Brief

**Date**: 2026-08-17
**Analyst**: The Qor-logic Analyst
**Target**: `qor/scripts/veto_pattern.py` GATE TRIBUNAL blindness (shadow event `8f9c5c6e...`; GH #342 first held checkbox; original specification at `.qor/gates/2026-08-12T0214-799d77/remediate-iter6.json` proposal [0])
**Scope**: defect confirmation by execution; consumer inventory; fix shape per the original F1 specification; repointment mechanics

---

## Executive Summary

Confirmed by execution at main (`8040205`): `parse_phase_audit_counts` recognizes only `entry_type == "AUDIT"` (`veto_pattern.py:50`), the ledger has written `GATE TRIBUNAL` since Entry #86, and the live parse returns 5 sealed-phase counts with a maximum phase of 27 and zero above 200 -- the detector consulted at `/qor-audit` Step 7 has been structurally blind for roughly 200 entries while reporting "No repeated-VETO pattern" every audit. The original remediation proposal specifies the fix in three steps: recognize GATE TRIBUNAL, add an in-flight condition (the sealed-phase window cannot see the live cycle's VETOs), and add a ledger-binding anti-recurrence test. Phase 227 ships all three plus the held GH #333 repointment of `8f9c5c6e` to the test file, which becomes true in the same change that makes the test real.

## Findings

### 1. Defect, by execution

- `veto_pattern.py:50` -- `elif entry_type == "AUDIT":`; the header regex at `:30-33` captures multi-word uppercase types, so `GATE TRIBUNAL` reaches the comparison and is dropped.
- Live parse over `docs/META_LEDGER.md`: 5 counted phases, max 27, none above 200. Modern GATE TRIBUNAL descriptions carry `Phase <N>` and SESSION SEAL headers carry `SEAL`, so the phase-reference and seal halves of the parser remain correct; only the audit-type comparison is stale.
- `tests/test_veto_pattern_detector.py` (120 lines) is entirely synthetic: zero references to `META_LEDGER`, `GATE TRIBUNAL`, or any real-ledger binding -- which is why eight phases of green never surfaced the blindness.

### 2. Consumers

- `/qor-audit` Step 7 (`SKILL.md` + `qor-audit-templates.md`): calls `check(ledger_path=None, session_id=sid)` and pastes `render_advisory_text` into every audit report. Fix changes behavior of that advisory only in the direction of truthfulness; no signature change.
- `tests/test_veto_pattern_detector.py`, `tests/test_veto_pattern_event.py`: synthetic fixtures write `AUDIT` entries; they must keep passing (the fix widens acceptance, does not remove `AUDIT`).
- `tests/test_audit_language_doctrine.py`, `tests/test_audit_smoke_integration.py`: reference the module by name; sweep at implement.

### 3. In-flight condition (original step 2)

`detect_repeated_veto_pattern` restricts to SEALED phases, so the live cycle's own multi-VETO run is invisible until after its seal -- the detector can only ever warn one phase late. The proposal's remedy: treat the in-flight phase (audit entries present, no SEAL entry, phase number above the newest sealed phase) as the newest window member when it already has more than one audit pass. Session-scoped escalation remains `cycle_count_escalator`'s domain (fired-both-modes evidence lives on a different event); this condition only makes the ledger-window advisory timely.

### 4. Ledger-binding anti-recurrence test (original step 3)

The specified test binds the parser to the real `docs/META_LEDGER.md`: non-empty counts above phase 200. Red today by the defect itself. Environment-honest: asserts a stable structural property of the repo's own tracked artifact (present in any full checkout, no operator-local path, no specific entry values or hashes), so it does not repeat the live-state-hardcoding pattern -- it is the deliberate opposite of the synthetic-only suite that concealed this defect.

### 5. Repointment mechanics

`correct_closure_enforcers` (v0.148.0) under a reviews-remediate PASS attestation repoints `8f9c5c6e... -> tests/test_veto_pattern_detector.py` in the same phase that makes that citation true, per the reviews-remediate VETO's Required Next Action (ledger #597). The fourth iter6-F1 concern (per-category counting in the escalator) remains with GH #342.

## Blueprint Alignment

| Claim | Actual Finding | Status |
|---|---|---|
| iter6 [0]: "veto_pattern.py:50 matches entry_type == 'AUDIT' exactly" | Verified at main, line 50 | MATCH |
| iter6 [0]: "the parser's view stops at phase 27" | Live parse: max phase 27, zero above 200 | MATCH |
| iter6 [0]: "all 11 tests are synthetic" | File now holds fewer tests but remains fully synthetic; the concealment property is unchanged | MATCH (count drifted, property holds) |

## Recommendations

1. Phase 227 (hotfix): the three-step fix plus the repointment, tests first. The GATE TRIBUNAL recognition and ledger-binding test are small and fully specified; the in-flight condition is the only design surface.
2. Keep `AUDIT` recognition (grandfathered entries 1-85 and synthetic fixtures).

## Updated Knowledge

The advisory printed in every audit report since Entry #86 ("No repeated-VETO pattern detected in the last 2 sealed phases") was vacuously true -- the window it examined was empty. Phase 225's and 226's advisories inherit that caveat; their verdicts stand on their own merits.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
