# Research Brief

**Date**: 2026-08-17
**Analyst**: The Qor-logic Analyst
**Target**: PR #338 (`fix/stabilization-286-332-333-336-337`, draft, red CI) compared against the VETOed Phase 225 plan (`docs/plan-qor-phase225-citation-truth-driver.md`, iteration 1)
**Scope**: overlap map; which vehicle carries the GH #336 canonical grep-n truth-checking work; root causes of the five CI test failures and the PR Citation Lint failure on #338; remediation path for a governed cycle

---

## Executive Summary

PR #338 and the Phase 225 plan implement the same core idea for GH #336 -- adjudicate every canonical grep-n evidence statement on its own account -- and both miss the defect the Phase 225 VETO identified as dominant: `_EVIDENCE_STMT_RE` cannot parse the two-span citation style every recent real plan uses (verified by execution: no match), and in the one-span style it swallows the closing backtick into the observed text, so even true statements are flagged `evidence-not-reproducible` (verified by execution: `observed == "beta\`"`). Of #338's five CI test failures, two are that backtick capture defeating its own new tests, one is the doctrine ceiling test firing exactly as VETO F1 predicted, and two are legacy fixtures newly adjudicated under a changed citation-key contract. The PR Citation Lint failure is not a defect: #338 was authored outside the governed cycle and has no plan, ledger entry, or seal to cite. Recommendation: the governed Phase 225 cycle carries #336 (plan iteration 2, amended per VETO F1-F6 plus the deltas below); #338's disjoint, green GH #333 work is salvageable; #338's #336 commits should be superseded, not merged.

## Findings

### 1. Overlap map

PR #338 contains four commits in two disjoint pairs:

- `57eb632` + `bd63317` (GH #333, `qor/scripts/remediate_mark_addressed.py` + `tests/test_remediate_per_event_enforcers.py`): per-event closure-enforcer mapping. **No overlap with Phase 225** -- the plan excludes #333 explicitly (`docs/plan-qor-phase225-citation-truth-driver.md:12`). All its tests pass in the failing CI run.
- `b902dc5` + `d637b21` (GH #336, `qor/scripts/plan_grep_lint.py` + `tests/test_plan_grep_canonical_truth.py`): first-class truth-checking of canonical statements. **Direct overlap** with Phase 225 plan Phases 1-3: same target function (`check_citation_evidence`), same count change (`count_truth_checked` counts examined targets, not just the demand set), same kind-ceiling move (`grep-n evidence` into `TRUTH_CHECKED_KINDS`).

### 2. Root causes of the five CI test failures (run 32024552666)

**2a. Trailing-backtick capture (2 failures, both in #338's own new tests).**
`_EVIDENCE_STMT_RE`'s observed group is `[^\n]*` (`qor/scripts/plan_grep_lint.py:109-112` on the branch; pattern unchanged from main). Against the one-span style the fixture uses -- `` `git show v1.0.0:sample.py | grep -nE 'beta' -> 2:beta` `` -- the group captures `beta\`` including the closing backtick. `reproduces` strips whitespace only, so a true statement compares `"beta\`" != "beta"` and is flagged `evidence-not-reproducible`. Verified by executing the regex. Fails `test_canonical_grep_statement_is_truth_checked_without_bare_file_line` and `test_bare_file_line_and_matching_statement_count_once` (`tests/test_plan_grep_canonical_truth.py:30, :69` on the branch). The two negative-path siblings pass only because they expect a finding of the kind the defect happens to produce.

**2b. Doctrine ceiling divergence (1 failure) -- VETO F1 realized.**
#338 changed `TRUTH_CHECKED_KINDS` to `("file:line", "grep-n evidence")` and renamed a presence-only kind to `"bare git show <ref>:<path>"` without amending the doctrine. The binding doctrine text at `qor/references/doctrine-shadow-genome-countermeasures.md:285` still reads "Truth-checked kinds: `file:line`. Presence-only kinds: `migration filename`, `git show <ref>:<path>`." `tests/test_doctrine_citation_pairing.py::test_the_lint_ceiling_matches_the_doctrine_kinds` (`:54`) compares the two and fails: "doctrine names truth-checked {'file:line'}; the lint reports {'file:line', 'grep-n evidence'}". This is the exact failure mode the Phase 225 VETO's F1 predicted ("turn the ceiling test red the moment `PRESENCE_ONLY_KINDS` changes").

**2c. Citation-key contract change against legacy fixtures (2 failures).**
The new first-class adjudication reports a statement's own finding under a ref-prefixed key via `_statement_citation` (`<ref>:<path>:<line>`), and adjudicates statements no bare citation demands:

- `tests/test_plan_grep_lint_citation_evidence.py:110` -- the fixture's illustrative statement names fake ref `abc123`, which now resolves to nothing and emits `evidence-unresolvable` with citation `abc123:x/20240101_init.sql:1` ahead of the expected `unpaired-citation`.
- `tests/test_plan_grep_citation_pairing.py:96` -- the fixture pins ref `2d356ec` line 97 against the *current working tree's* line 97 (`:92` reads the live file). #338's own comment-stripping shifted `plan_grep_lint.py` from 304 to 281 lines, so the fixture statement no longer reproduces and emits an extra ref-prefixed finding. This fixture is live-state-coupled and breaks any time the module's lines move; it needs a deliberate rewrite regardless of vehicle.

### 3. PR Citation Lint failure (runs 32024612925 et al.)

The lint reports the PR body missing: plan file path (`docs/plan-qor-phase<NN>-<slug>.md`), ledger entry reference, and Merkle seal hash, per `qor/references/doctrine-governance-enforcement.md` section 6. These citations cannot exist because **#338 was authored outside the governed cycle** -- no `/qor-plan`, no `/qor-audit` verdict, no `/qor-substantiate` seal, no ledger entry. The lint is enforcement working as designed, not a defect to patch. The only remediation that produces the missing citations is running the cycle.

### 4. The dominant defect remains unfixed in both vehicles (VETO F3)

Verified by execution against the unchanged `_EVIDENCE_STMT_RE`:

- Two-span corpus style (used by the Phase 224 and 225 plans): `` `git show <ref>:<path> | grep -nE '<pat>'` -> `NN:text` `` -- **no match at all**; such plans parse to zero evidence statements.
- One-span style: matches, but with the trailing-backtick capture of finding 2a.
- The doctrine's mandated form (`doctrine-shadow-genome-countermeasures.md:285`) is `-> <exact observed text>` with **no** `NN:` prefix -- unparseable by construction.

Neither the Phase 225 plan (VETO F3: named two suppressors, missed this one) nor PR #338 (regex untouched) addresses it. Any iteration-2 plan must treat the statement grammar itself -- span styles, backtick delimiters, and the doctrine's mandated form -- as the primary deliverable, or the enforcer keeps checking a form nobody writes.

### 5. Remaining VETO findings against #338 as a hypothetical vehicle

- **F5 territory untriggered but unresolved**: #338 does not touch `_FILE_LINE_RE` (still `py|ts|tsx|sql|rs|go|js`), so markdown/doc citations -- the majority surface per the plan's own measurement (`docs/plan-qor-phase225-citation-truth-driver.md:21-23`) -- remain invisible to the demand set. Half of #336's measured zero is untreated.
- **F6 razor**: the branch module is 281 lines against the 250 ceiling (down from 304, achieved almost entirely by deleting explanatory comments rather than extracting structure). Still over; `check_citation_evidence` grew.
- **F1/F2 phantom targets**: #338 avoided the invented doctrine path and test name, confirming those were plan-text defects only.

## Blueprint Alignment

| Claim | Actual Finding | Status |
|---|---|---|
| Phase 225 plan: "the parser already handles the mandated form correctly" (plan `:11`, `:16`) | Two-span style: no match; one-span: trailing backtick corrupts `observed`; doctrine form: unparseable | DRIFT (= VETO F3) |
| Phase 225 plan Phase 3 targets `doctrine-citation-pairing.md` | File does not exist; binding text at `doctrine-shadow-genome-countermeasures.md:285` | DRIFT (= VETO F1) |
| PR #338 body: "wrong lines/text and unresolvable targets produce explicit findings" | Implemented, but under a new ref-prefixed citation contract legacy tests do not encode | PARTIAL |
| PR #338 body: "behavioral coverage includes ... backward compatibility" | 4 of 5 citation-area tests fail, including 2 of its own | DRIFT |
| PR #338 (#333 half): per-event closure enforcers with all-or-nothing validation | Tests pass; scope disjoint from Phase 225 | MATCH |

## Recommendations

1. **Vehicle for #336: the governed Phase 225 cycle** (this branch), as plan iteration 2 amended per VETO F1-F6, with the statement-grammar fix (finding 4) promoted to the primary deliverable and #338's sound structural ideas (first-class adjudication loop, examined-target counting) absorbed with attribution to the PR. Priority: high.
2. **Do not merge #338 as-is.** Salvage the #333 pair (`57eb632`, `bd63317`) -- disjoint and green -- into a governed phase of its own (or a second phase of the same cycle). Supersede the #336 pair. Disposition of the PR itself (close vs. repoint after seal) is an operator decision.
3. **No code remediation for the PR Citation Lint failure.** It is the governance surface catching an out-of-cycle mutation; the governed cycle produces the missing citations.
4. **Plan iteration 2 must additionally cover**: doctrine amendment at `doctrine-shadow-genome-countermeasures.md:285` in the same phase as the kind-ceiling change; extension parity between `_FILE_LINE_RE` and `_WT_PATH_RE` (VETO F5); razor extraction to bring the module under 250 lines structurally; a stated citation-key contract (ref-prefixed vs. bare) with the legacy tests updated deliberately; and a rewrite of the live-state-coupled fixture at `tests/test_plan_grep_citation_pairing.py:92`.

## Updated Knowledge

- The evidence-statement grammar has three incompatible writings in the wild: the doctrine's mandated form (no `NN:`), the one-span code-fence form (parses with corrupted `observed`), and the two-span form real plans use (does not parse). This tri-state mismatch is the root of GH #336's measured zero and belongs in the doctrine amendment.
- A process observation for the operator (not logged as a Shadow Genome event by this research pass): stabilization work on the governance enforcer itself was pushed to a PR outside the governed cycle, and the PR Citation Lint caught it structurally. The enforcement layer worked.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
