# Research Brief

**Date**: 2026-08-18
**Analyst**: The Qor-logic Analyst
**Target**: GH #349 (pre-audit lint for asserted-completeness enumerations; SG-AssertedCompleteness-A countermeasure)
**Scope**: the two observed failure forms; a checkable V1 grammar; ladder wiring and size budget

---

## Executive Summary

Two same-day VETOs (ledger #593, #611) shared one shape: a plan asserted an exhaustive countable inventory that the artifact surface contradicted, and every citation-truth check passed because the citations were true while the enumeration around them was not. Both failures are mechanically re-derivable, which is the definition of a lintable class. V1 grammar covers exactly the two observed forms: a test-count claim against a pinned artifact (count `def test_` at `<ref>:<path>` and compare), and a site-count claim against an enumerated list (compare the declared N with the number of distinct `file:line` citations in the same paragraph). WARN-only in the Step 0.6 ladder per the SG-PreAuditLintGap-A convention; one ladder line fits the qor-audit skill's 1,273-byte headroom.

## Findings

### 1. The two observed forms, restated as checks

- **Form A (entry #593)**: prose like `10 behavioral tests` in the same paragraph as a `git show <ref>:<path>` naming a test file. Check: `git show ref:path | grep -c '^def test_'` vs the claimed N. The Phase 226 failure (claimed 10, artifact held 4) is caught exactly.
- **Form B (entry #611)**: prose like `all eight call sites` / `twelve ... sites` in a Locked-Decision paragraph that enumerates `file:line` citations. Check: count distinct file:line citations in the paragraph (reusing `plan_evidence._FILE_LINE_RE`) vs the claimed N. The Phase 230 failure (claimed eight, the corrected LD later enumerated twelve) is caught when the enumeration and the number disagree; a wrong count with a matching wrong list is out of V1 scope by design (that failure mode was already caught by the reviewer's independent sweep, which no static lint replaces).

### 2. Number-word handling

Both incidents wrote counts as words ("ten", "eight", "twelve"). The V1 parser accepts digits and the number words one through twenty (a fixed table; no NLP).

### 3. Wiring and budget

- Ladder site: `/qor-audit` Step 0.6, after `plan_test_lint` (SKILL.md line 157 region), `|| true` WARN-only -- the binding VETOs remain the Step 3 passes, exactly the SG-PreAuditLintGap-A posture.
- Size: qor-audit SKILL.md at 39,687 bytes with EXCEEDED at 40,960; one ladder line (~65 bytes) fits with >1,200 to spare. Relevant because #320's V2 flip will harden the EXCEEDED bound at seal.
- Existing lints named in the ladder are dispatched by module name; no registry change needed.

### 4. False-positive posture

Counts that refer to non-inventory quantities ("40 diff lines", "the 250 ceiling") must not trigger. The V1 grammar anchors on inventory nouns (`tests`, `call sites`, `sites`, `unpack sites`) adjacent to the count, which excludes every numeric in the seven recent plans by inspection except the genuine inventory claims.

## Blueprint Alignment

| Claim | Actual Finding | Status |
|---|---|---|
| #349: both failures mechanically re-derivable | Form A/B checks reproduce both VETO findings from the plan texts as-submitted | MATCH |
| Progressive-disclosure/ladder convention | One `\|\| true` line at Step 0.6; prose stays out of SKILL.md | MATCH |

## Recommendations

1. Phase 232 (feature): `qor/scripts/plan_enumeration_lint.py` with the Form A/B checks, behavioral tests (both historical failures as fixtures), and the one-line ladder wiring.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
