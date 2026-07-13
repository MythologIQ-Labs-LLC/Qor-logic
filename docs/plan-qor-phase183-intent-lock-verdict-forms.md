# Plan: Phase 183 - Intent lock accepts heading verdict forms (GH #263)

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

(none)

## Origin

Research brief docs/research-brief-intent-lock-verdict-forms-2026-07-13.md (ledger entry #450, session `2026-07-13T0837-ef73c7`); GH #263 (the rejection bit this repository's own Phase 173 tribunal live).

## Locked Decisions

- **LD-1: widen with a heading prefix only.**
  `grep -nE 'Verdict\|VERDICT' qor/reliability/intent_lock.py -> 59` (the anchored pattern). New pattern: `^#{0,6}\s*\**(?:Verdict|VERDICT)\**\s*[:\-]\s*\**PASS\**\s*$`. Headings are structural markdown (a prose sentence cannot start at column 0 with `#` and end after PASS), so the Phase 53 LOW-4 anti-prose rationale (docstring 48-54) is preserved byte-for-byte in spirit: prose-substring and indented-line rejections unchanged.
- **LD-2: the error distinguishes format-mismatch from not-PASS.**
  `grep -nE 'audit not PASS' qor/reliability/intent_lock.py -> 82`. On anchored miss, a loose case-insensitive probe (`verdict[^\n]*pass`) decides the message: present -> "ERROR: audit verdict line found but not in a canonical form; expected 'Verdict: PASS' (bold or #-heading forms accepted) on its own line"; absent -> the current "ERROR: audit not PASS". The loose probe affects ONLY the message, never the verdict decision.
- **LD-3: no other parser changes.**
  `meta_ledger_walker._VERDICT` extracts verdict VALUES from META_LEDGER entries (different input class, bold-form by ledger convention) -- intentionally distinct, recorded for the disposition.

## Phase 1: Widen + hint (TDD first)

### Affected Files

- tests/test_intent_lock_anchored_pass_check.py - heading accept tests + regression locks + hint test appended
- qor/reliability/intent_lock.py - pattern per LD-1; error branch per LD-2

### Changes

Pattern updated in `_audit_has_pass` (docstring gains one sentence naming the heading acceptance). The capture path's failure branch reads the body once (already read by `_audit_has_pass`; reuse via a small refactor returning the body or re-read -- keep it simple: a `_verdict_hint(audit_path)` helper performing the loose probe for the message).

### Unit Tests

- tests/test_intent_lock_anchored_pass_check.py::test_audit_body_with_h2_heading_verdict_passes - `## VERDICT: PASS` accepted (the GH #263 acceptance; red today)
- tests/test_intent_lock_anchored_pass_check.py::test_audit_body_with_h3_mixed_case_heading_passes - `### Verdict: PASS` accepted
- tests/test_intent_lock_anchored_pass_check.py::test_prose_and_indented_rejections_unchanged - the LOW-4 prose sentence and an indented verdict line still reject (regression locks re-asserted post-widening)
- tests/test_intent_lock_anchored_pass_check.py::test_capture_error_hints_at_format_when_verdict_present - capture on an audit whose only verdict line is `Verdict -> PASS` (unsupported separator) exits 1 with the format-hint message; on an audit with no verdict content the message stays "audit not PASS"

## Feature Inventory Touches

(empty -- reliability tooling)

## Definition of Done

### Deliverable: production verdict forms parse

- **D1**: An audit report declaring its verdict as a markdown heading locks without the operator diagnosing an opaque error (GH #263; the Phase 173 live incident class closed).
- **D2**: LD-1 pattern + LD-2 hint; prose/indent rejections regression-locked.
- **D3**: Ledger entries for plan/audit/implement/seal; GH #263 disposition records LD-3.
- **D4**: `test_audit_body_with_h2_heading_verdict_passes` (red today) and `test_capture_error_hints_at_format_when_verdict_present` observe the behaviors.

## CI Commands

- `python -m pytest tests/test_intent_lock_anchored_pass_check.py tests/test_reliability_scripts.py -q` - focused suite (run twice for determinism)
- `python -m pytest -q` - full suite
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - ledger chain integrity across the phase's entries
