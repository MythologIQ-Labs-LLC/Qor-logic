# Research Brief

**Date**: 2026-07-13T08:38:00Z
**Analyst**: The Qor-logic Analyst
**Target**: GH #263 -- intent_lock PASS-verdict regex rejects markdown-heading verdict lines with an unhelpful error
**Scope**: the anchored regex's rationale, in-the-wild verdict forms, safe widening, error UX

---

## Executive Summary

`intent_lock._audit_has_pass` (qor/reliability/intent_lock.py:59, verified
live) accepts `Verdict: PASS` / `**Verdict**: PASS` on its own line but
rejects markdown-HEADING forms like `## VERDICT: PASS`, failing with the
uninformative "ERROR: audit not PASS" (line 82). Heading forms are in real
production use: the Phase 173 audit report in THIS repository carried
`## VERDICT: PASS` and hit exactly this rejection live (the incident is
recorded in entry #411's session and in the operator memory that seeded this
issue). Headings are STRUCTURAL markdown, not prose -- they cannot appear
inside a narrative sentence -- so an `^#{0,6}\s*` prefix preserves the Phase
53 LOW-4 anti-prose anchoring entirely. Pair the widening with a
format-hint error for the remaining mismatch class.

## Findings

### F1. The regex and its safety rationale (verified live)

- `qor/reliability/intent_lock.py:59`:
  `^\**(?:Verdict|VERDICT)\**\s*[:\-]\s*\**PASS\**\s*$` (MULTILINE). Docstring
  (48-54): the anchors exist to reject prose false-positives ("If the test
  does not PASS, ..."), replacing a pre-Phase-53 loose `VERDICT.*PASS`.
- Error at line 82: `ERROR: audit not PASS` -- indistinguishable between
  "verdict is VETO/absent" and "verdict present but in a rejected format".

### F2. In-the-wild forms

- Recent audit reports carry BOTH `**Verdict**: PASS` (header field) and
  `## VERDICT: PASS` (section heading) -- the Phase 173 report used both after
  the live rejection forced adding the field form. Both are legitimate
  structural declarations; only one parses today.

### F3. Safe widening + consistency

- `^#{0,6}\s*` before the existing pattern admits h1-h6 headings only;
  leading-whitespace rejection (indented prose) and same-line anchoring are
  preserved -- the LOW-4 concern (prose substrings) cannot produce a line
  both starting with `#{0,6}` at column 0 AND ending after PASS.
- The only other verdict parser (`meta_ledger_walker._VERDICT`, bold-form,
  value-extracting, different input class: META_LEDGER entries) is
  intentionally distinct -- no synchronization needed (recorded so the
  disposition can answer the consistency question).
- Error UX: when the anchored match fails but a loose case-insensitive
  `verdict.*pass` exists in the body, the error names the expected canonical
  forms -- distinguishing format-mismatch from genuinely-not-PASS.

### F4. Test gap

- `tests/test_intent_lock_anchored_pass_check.py` covers plain/bold/dash/
  uppercase/prose-reject/indent-reject/VETO -- zero heading-form coverage.

## Blueprint Alignment

| Contract claim | Actual finding | Status |
|----------------|---------------|--------|
| Phase 53 LOW-4: no prose false-positives | Preserved by the heading prefix (structural, not prose) | MATCH |
| Production verdict forms parse | `## VERDICT: PASS` rejected (bit Phase 173 live) | DRIFT (the fix) |

## Recommendations

1. (P0) Widen the regex with `#{0,6}\s*` heading prefix; keep everything else.
2. (P0) Heading-form accept tests (h2/h3) + prose/indent reject regression
   locks; a format-hint error test.
3. (P1) Error message: on anchored-miss with loose verdict-ish content
   present, print the expected forms.

## Updated Knowledge

The operator memory entry on manual seal mechanics gets superseded for gotcha 1
once this ships (recorded at disposition).

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
