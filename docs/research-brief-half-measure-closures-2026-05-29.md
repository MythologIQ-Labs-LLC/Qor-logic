# Research Brief

**Date**: 2026-05-29
**Analyst**: The Qor-logic Analyst
**Target**: Closed GitHub issues (MythologIQ-Labs-LLC/Qor-logic), repo at v0.80.0
**Scope**: Identify "half-measure" closures — issues closed by a PR/commit that shipped only a stopgap or partial fix while the issue's stated acceptance criteria / proposed deliverables were not fully met.

---

## Executive Summary

Of 52 closed issues audited, **10 (19%) were closed on half-measures** — the issue was marked resolved when an advisory/stopgap layer shipped but a load-bearing deliverable named in the issue was silently deferred to an unscheduled "V2." 41 were FULL resolutions (verified against the current tree, not merely "closed"); 1 (#92) was a discussion-only finding with no acceptance criteria. (One initially-flagged item, #80, was reclassified to FULL after operator review confirmed its second named target is an out-of-scope proprietary prompt; the in-scope half shipped correctly.) Every half-measure was verified by checking the current tree for the promised artifact, not by trusting the closed state. The pattern is systemic, not incidental: the closures cluster into three repeatable failure shapes, and two of them (#56, #58) violate the repo's own "test functionality, not presence" doctrine by shipping tests that assert prose strings exist rather than that behavior runs.

## Findings

### Half-measure closures (11)

| Issue | Conf | Closing PR/commit | What was asked vs what shipped |
|---|---|---|---|
| #85 Reconciliation tool (V2) | high | PR #106 / `d354ac3` (v0.62.0) | Asked `qor-logic reconcile` command + `RECONCILIATION` ledger entry type (options A/B/C). Shipped ONLY `--tolerate-known-grandfathered` stopgap (option D). No `reconcile` subcommand exists in `qor/cli.py`. **Calibration case.** |
| #140 Hierarchical Governance Index | high | PR #145 / `b1a3274` (v0.79.0) | Index defined as "scaffolded by /qor-bootstrap, **enforced by /qor-substantiate**". Shipped artifact + WARN-only checker + bootstrap scaffold + /qor-status indicator. Substantiate-side enforcement and /qor-validate chain cross-check deferred to V2. No governance-index refs in qor-substantiate or qor-validate SKILL.md. |
| #79 Module reachability from any shell | high | PR (Phase 90, v0.61.0) | Filer recommended "A + D": Option A = self-resolving `qor-logic reliability ...` CLI dispatch (the actual fix). Shipped only C + D (an `## Environment` doc block + WARN-only preflight). No `reliability`/`scripts` CLI subcommand. Modules remain unreachable; only the silent-skip became visible. |
| #77 SKILL.md provenance gaps | high | PR #78 / `1648591` (v0.55.1) | Two skills reported (`qor-governance-compliance` + `qor-compliance`, 3 violations). Only the first fixed; `qor-compliance` (2 of 3 violations) declared out-of-scope. |
| #56 Cross-iteration citation drift | high | PR #67 / `203d80c` (v0.48.0) | 6 ACs. Prose/doctrine half shipped (plan inventory, audit re-walk, SG-CitationDrift-A). Enforcement half not: `plan_grep_lint` never extended to flag sealed citations lacking grep-evidence (AC4); the 3 "tests" are SKILL.md text-presence assertions, not behavioral (AC5/6). |
| #89 Merge-velocity throttle | med | PR #109 / `2b9973d` (v0.64.0) | Asked a gate that **requires** branch isolation / hold-merges when velocity outpaces verification. Shipped WARN-only detector; seal message concedes "V1 ships the detector, not the enforcer." No merge is ever held. |
| #90 Inline regression / stabilization control | med | PR #110 / `4855503` (v0.65.0) | Detector exists + wired at audit. But AC#3 required a checkpoint in **planning** flows — no qor-plan wiring exists. Implementation-phase scope warnings not shipped; v1 output dropped `stabilization_capacity`/`shared_surface_risk`/`branch_only`. WARN-only. |
| #58 LiveProgressInvariant | med | PR #69 / `6b4e119` (v0.50.0) | Doctrine + audit checklist shipped. AC2 (`findings_categories` schema enum) downgraded to prose-only; AC3 (`plan_live_progress_lint.py` detector + 4 reference test cases) **does not exist**. Rule enforceable only by hand. |
| #40 Feature Inventory seal-regression gate | med | PR #68 / `3601c5b` (v0.49.0) | Artifact + schema + doctrine + substantiate reporting pass shipped. Central AC — `/qor-substantiate` MUST block PASS when an out-of-scope feature regresses verified->unverified — not built; "ABORT helper deferred to a follow-on phase. V1: operator reviews counts manually." The anti-deception gate ships as advisory. |
| #83 Citation consumer-trace check | med | PR #83 / `ce138b2` (v0.56.0) | Asked a "~20-line extension to `qor.scripts.findings_signature`" (automated grep-recursive consumer-trace). Shipped only an LLM-executed prose sub-check in phase37-subpasses.md; no executable code; tests assert prose presence only. (Contrast its sibling #87 in the same commit, which did get `delivery_branch_lint.py`.) |

### Three recurring failure shapes

1. **Detector ships, enforcer deferred (WARN-only instead of gate)** — #89, #90, #40, #140. The signal is surfaced but no control is exercised; "V2 layers enforcement" is promised but unscheduled.
2. **Prose/doctrine ships, mechanical lint never built** — #56, #58, #83. The auditor must apply the rule by hand. Tests assert that a SKILL.md string is present, not that a check runs — a direct conflict with the project's test-functionality doctrine.
3. **Stopgap/docs ship, architectural fix deferred** — #85, #79. A flag or documentation block lowers the pain; the requested mechanism (reconcile command, CLI dispatch) is never built.

Plus a fourth, lighter shape: **partial-surface closure** — #77, where one of two explicitly-named targets is fixed and the other is declared out-of-scope while the issue is closed as resolved. (#80 had this shape too, but its un-shipped target was correctly out of scope, so it is not counted as a half-measure.)

## Blueprint Alignment

| Claim | Actual finding | Status |
|---|---|---|
| Closed issues == delivered acceptance criteria | 11/52 closed with named deliverables deferred or unbuilt | DRIFT |
| Tests verify behavior (CLAUDE.md test-discipline) | #56, #58, #83 closing tests assert prose presence, not behavior | DRIFT |
| "V2 deferred" items are tracked | None of the deferred V2 halves have a filed follow-on issue (matches #85's original complaint that "the V1 commit named V2 but didn't file an issue") | DRIFT |

## Recommendations

1. **(High)** Reopen or file follow-on issues for the high-confidence enforcement gaps: #85 (reconcile tool), #79 (reliability CLI dispatch), #77 (qor-compliance provenance), #56 (plan_grep_lint citation-evidence enforcement), #140 (substantiate/validate enforcement). These were closed against unmet acceptance criteria.
2. **(High)** Add a substantiation-time guard: an issue may not be auto-closed by a seal unless every checkbox in its acceptance-criteria block is either satisfied or has a filed follow-on issue number. This is the structural counterweight to the "named V2, filed nothing" drift.
3. **(Med)** Treat "test asserts a SKILL.md prose string exists" as a test-functionality violation in /qor-audit (#56, #58, #83 would have been caught). Wire a lint that flags wiring-tests whose only assertion is substring-in-SKILL.md.
4. **(Med)** When an issue names N targets/skills, require closure to address all N or split the remainder into a tracked issue before closing (#77).

## Updated Knowledge

New systemic finding for the shadow genome: **SG-HalfMeasureClosure** — governance issues are closed when the advisory layer (detector / doctrine / stopgap flag) ships while the enforcing layer (gate / mechanical lint / real command) is silently deferred to an unfiled "V2." Detection signal: closing PR body or seal message contains "V1 ships the detector, not the enforcer" / "deferred to V2" / "operator reviews manually," AND the issue body contained an acceptance-criteria checklist with mechanical deliverables. Counter-control: recommendation #2 above.

---

_Research complete. Findings are advisory — implementation decisions remain with the Governor. Ledger entry and gate artifact not written automatically: this branch (phase/113) is already sealed; wiring a RESEARCH entry into META_LEDGER is offered as an explicit next step rather than performed mid-audit._
