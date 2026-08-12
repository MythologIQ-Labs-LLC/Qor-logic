# AUDIT REPORT

**Verdict**: VETO
**Target**: docs/plan-qor-phase223-grep-evidence-truth.md

**Iteration**: 1
**Date**: 2026-08-12
**Judge**: The Qor-logic Judge
**Mode**: adversarial -- Option B independent reviewer (mandated)
**Phase**: 223 (GH #330)
**Risk Grade**: L2
**Findings categories**: `infrastructure-mismatch`, `specification-drift`, `test-failure`

---

## Mode: Option B was mandatory and was executed

`audit_risk_score` returned `option_b_required: true`, flag `high-citation-surface`,
with the explicit directive that the auditing agent must not run solo. No external
reviewer is configured. An independent reviewer with no authoring context was
dispatched against the plan and the repository, and returned fifteen findings.

**Its three mandating findings were re-verified here by execution before adoption.**
The reviewer disclosed that it had no shell and worked by establishing
`HEAD == 2d356ec` from `.git` refs and reading the working tree -- a sound
equivalence for unmodified paths, and it said so rather than implying it had run
the commands. That disclosure is why its report is usable; it is also the exact
discipline this plan exists to mechanize.

The mandate was correct. A solo audit would not have found F3.

---

## V1 -- `infrastructure-mismatch` (BINDING)

**LD-3's grep-evidence does not reproduce, under this plan's own comparison rule.**

The plan quotes line 285 of the countermeasures doctrine as exact observed output.
Measured:

```
$ git show 2d356ec:qor/references/doctrine-shadow-genome-countermeasures.md \
    | grep -nE 'MUST carry a paired grep-evidence' | wc -c
820

$ grep -A2 "MUST carry a paired grep-evidence" docs/plan-qor-phase223-grep-evidence-truth.md \
    | head -1 | wc -c
481
```

The line is 815 characters; the plan presents a partial quote as the observation,
with no ellipsis and no truncation marker.

**Correction (iteration 2 re-audit).** This report originally read "820 characters."
815 is the line length; 819 is the line with grep's `285:` prefix; 820 is `wc -c`
over that, counting the trailing newline. The figure quoted was a byte count of
command output, described as a character count of a line. Measured:
`git show 2d356ec:... | sed -n '285p' | awk '{print length($0)}'` -> `815`.
The truncation finding is unaffected -- the quote is partial at any of the three
figures -- but an unpaired number in a report that VETOes an unpaired number is
the same defect, and is recorded rather than quietly amended. Phase 1 Changes defines the check as
`observed.strip()` compared against the file line stripped -- strict equality. Under
the rule this plan proposes, LD-3 classifies as `evidence-not-reproducible`.

What was dropped is not filler. It is the sentence describing the shipped
enforcement as block-scoped -- the precise text LD-3 then paraphrases in prose
instead of quoting. The truncation removed the evidence that would have complicated
the claim built on it.

**A plan whose thesis is "cited lines must actually hold the quoted text" cannot
ship carrying a citation that is false by its own definition.**

**Required next action:** Governor: re-quote LD-3's observation in full, or narrow
the cited pattern so the match is genuinely one line. Re-run `/qor-audit`.

## V2 -- `specification-drift` (BINDING)

**The Affected Files contract names a file with none of the assertions it claims to
retarget, and omits the file that holds them all.**

Plan Phase 2: "`tests/test_plan_grep_lint.py` -- MODIFIED. Existing block-level
assertions retargeted to the pairing contract."

```
$ grep -ciE "check_citation_evidence|locked decision|evidence" tests/test_plan_grep_lint.py
0

$ grep -ciE "check_citation_evidence" tests/test_plan_grep_lint_citation_evidence.py
6
```

`tests/test_plan_grep_lint_citation_evidence.py` is the dedicated behavioral suite
for `check_citation_evidence` -- the function Phase 2 rewrites -- and it is named
nowhere in the plan. It holds the direct contract on the behavior being replaced,
including `test_no_finding_when_evidence_present`, which asserts the block-level
satisfaction Phase 2 abolishes.

Implementation would proceed against undeclared tests. This is
`SG-AffectedFilesContract-A`, already catalogued in this repository.

**Required next action:** Governor: add `tests/test_plan_grep_lint_citation_evidence.py`
to Phase 2 Affected Files and state which of its seven assertions survive the pairing
contract and which are retargeted. Re-run `/qor-audit`.

## V3 -- `specification-drift` (BINDING)

**The proposed check is inert on the document proposing it, and the plan offers that
inertness as validation.**

```
$ awk '/^## Locked Decisions/{f=1} /^## Phase 1:/{f=0} f' docs/plan-qor-phase223-grep-evidence-truth.md \
    | grep -oE "[A-Za-z0-9_./-]+\.(py|ts|tsx|sql|rs|go|js):[0-9]+" | sort -u
(no output)
```

Zero `file:line` citations in the entire Locked Decisions section. Every citation
there is the `git show <ref>:<path>` kind, which the plan itself exempts as
presence-only. Three consequences:

1. The CI command `plan_grep_lint --plan docs/plan-qor-phase223-grep-evidence-truth.md`,
   annotated **"this plan against its own new check"**, cannot fire the new check.
   It is offered as self-validation and validates nothing.
2. Deliverable-2's D1 -- "every `file:line` citation in a Locked Decision is backed
   by its own reproducible evidence" -- is satisfied vacuously.
3. Per Phase 2's own design, `reproduces` runs only on statements that are lookup
   hits for a `file:line` citation. With no such citations, **none of the plan's six
   evidence statements is ever truth-checked by its own mechanism.**

Point 3 is the mechanism by which V1 survived authoring. The plan built a check,
declared itself validated by it, and was structurally outside its scope.

**Required next action:** Governor: either cite the `file:line` kind in the Locked
Decisions so the check has a subject, or withdraw the self-validation claim from
`## CI Commands` and state plainly that the plan's own citations are presence-only.
The second is honest; the first is better. Re-run `/qor-audit`.

---

## Compounding finding (does not independently mandate, but bears on V1)

**F4 -- LD-3 over-reads the line it cites.** The title asserts the doctrine "already
specifies per-citation pairing." The cited sentence says every **LD** citing sealed
infrastructure must carry **a** paired grep-evidence statement -- per-LD, one
statement per LD. It does not say per-citation. The claim is load-bearing: it frames
this phase as closing an implementation gap rather than tightening a contract, and
Phase 3 then amends the doctrine anyway, conceding the contract changes.

This is the plan's own stated limitation, realised in the plan: *"A correctly-cited
line used to argue something it does not show still passes."* The truth check would
not catch V1's sibling defect even after V1 is fixed.

---

## Pass Results

| Pass | Result | Note |
|---|---|---|
| Prompt Injection | PASS | canaries exit 0 over 4 files |
| Version-Applicability | PASS | `feature`; v0.145.0 -> minor |
| Security (L3) | PASS | no auth, credential, or DB surface |
| OWASP Top 10 | PASS | `git show` specified list-form argv, no shell; no deserialization |
| Ghost UI / Live-Progress | N/A | no UI surface |
| Section 4 Razor | PASS | five small pure functions plus one subprocess call |
| Self-Application | **VETO** | V3 -- see below; this pass is why the verdict exists |
| Test Functionality | **VETO** | F11; V2 also bears |
| Dependency Audit | PASS | no new dependencies |
| Macro-Level Architecture | PASS | one module, no new boundary |
| Feature Test Coverage | PASS | `feature_inventory_touches` empty and justified |
| Infrastructure Alignment | **VETO** | V1; full LD re-walk below |
| Filter-Stage Ordering | PASS | pairing lookup has no ordering dependency |
| Orphan Detection | PASS | changes land in an already-wired module |
| Execution-Continuity | N/A | no `execution_continuity` block |

### Infrastructure Alignment -- full Locked Decision re-walk

| LD | Citation | Line no. | Text exact | Status |
|---|---|---|---|---|
| LD-1 | `plan_grep_lint.py:97` | correct | correct | PASS (partial grep output, unmarked -- F13) |
| LD-2 | `plan_grep_lint.py:134` | correct | correct | PASS |
| LD-2 | `plan_grep_lint.py:140` | correct | correct | PASS |
| LD-3 | doctrine `:285` | correct | **TRUNCATED (partial quote)** | **FAIL (V1)** |
| LD-4 | `plan_grep_lint.py:101` | correct | correct | PASS (partial -- F13) |
| LD-4 | `plan_grep_lint.py:99` | correct | correct | PASS (partial -- F13) |
| LD-5 | `qor-audit/SKILL.md:158` | correct | correct | PASS |
| LD-6 | `git log` | n/a | n/a | not a grep-evidence statement (F14) |

All cited paths resolve at the cited revision. No unresolvable citation.

### Self-Application detail

The reviewer's Check 2 asked whether the plan violates the pairing rule it proposes.
It does not -- it **escapes** it, which is worse and was not the anticipated shape.
The enumeration table is empty because there is nothing to pair.

---

## Advisory (non-binding, correctable in place)

| # | Finding |
|---|---|
| F5 | DoD asserts the ceiling appears in **stdout**; `plan_grep_lint.main()` prints to `sys.stderr` and no phase declares a change to it |
| F6 | Open Questions attribute span-based exclusion and finding kinds to Phase 1; both are Phase 2 mechanisms |
| F7 | Phase 3 says the doctrine names "the **two** finding kinds"; three are defined everywhere else, consistently |
| F8 | LD-2 cites a synthetic experiment with no fixture and nothing to re-run -- four citations claimed extracted, three enumerated. LD-6, four decisions later, establishes that an unrecorded counterfactual must be authored as a fixture |
| F9 | `test_resolve_line_reads_the_cited_revision` discriminates only if line 97 actually shifts; no phase commits to changing it |
| F10 | Phase 2 ships the ceiling output; its only test is listed under Phase 3 -- TDD ordering inverted |
| F11 | `test_doctrine_describes_per_citation_enforcement` exercises no unit of `plan_grep_lint`; it cannot fail on a behavior break |
| F12 | LD-5's "463 B of headroom" carries no paired evidence. Measured independently here at 39,473 B, so the figure is **true but unevidenced** -- the exact class P1 targets |
| F13 | LD-1 and LD-4 quote one of two matching lines without a truncation marker |
| F14 | LD-6 carries no grep-evidence, contradicting D3's claim that LD-1 through LD-6 all do |
| F15 | Pairing lookup remains scoped to the whole Locked Decisions block, so a citation under LD-5 can be satisfied by a statement under LD-1 |

F8 and F12 are the same defect as V1 in miniature: assertions inside Locked Decisions
carrying no re-runnable evidence. F15 is a design gap the phase should decide
deliberately rather than inherit.

---

## Documentation Drift

None. `doc_tier: system`, two terms declared with `home:` paths into an existing
doctrine, `boundaries` complete across limitations, non_goals, and exclusions.

---

## Process Pattern Advisory

<!-- qor:veto-pattern-advisory -->
No repeated-VETO pattern detected in the last 2 sealed phases.

`cycle_count_escalator.check` and `check_session_total` both return `None`.

---

## What survives

Recorded so the re-plan does not discard it:

- The core design is sound and was not challenged: parse an evidence statement into
  a value, resolve it against the revision it names, compare. LD-1, LD-2, LD-4, and
  LD-5 all reproduce, and Check 4 confirmed every claim about the existing module.
- The demonstrated gap is real -- one evidence statement satisfying an entire block
  -- and the pairing remedy addresses it.
- Phase 1's and Phase 2's fourteen test descriptions are behavioral. Two of them
  (`test_a_statement_without_an_observation_is_not_parsed`,
  `test_the_pairing_check_can_report_nothing_and_still_be_running`) are exactly the
  anti-vacuity guards this plan needed and did not apply to itself.

---

_Verdict is binding. No implementation may proceed until V1, V2, and V3 are addressed and `/qor-audit` re-run._
