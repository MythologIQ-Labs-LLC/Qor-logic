# Research Brief

**Date**: 2026-08-17
**Analyst**: The Qor-logic Analyst
**Target**: `/qor-audit` reviewer-toolset declaration (GH #342 held item two; shadow event `7b2ed33a...`; original specification at `.qor/gates/2026-08-12T0214-799d77/remediate-iter6.json` proposal [5])
**Scope**: where the contract lands; corpus constraints; repointment mechanics; testable surface

---

## Executive Summary

The Phase 223 remediation specified: "a dispatched Option B reviewer declares its available toolset in its first response, and the Judge may not pin a verification outside that set" -- because the mandated reviewer had no shell across four iterations while a freeze attestation was pinned as a content hash it could not compute. Verified at v0.148.1: no toolset-declaration language exists anywhere in the qor-audit skill directory (the #342 verification's greps, re-run). The contract belongs in `references/adversarial-mode.md` (the Option B dispatch protocol's home, 9.1 KB) with a one-line anchor in SKILL.md Step 1 -- the skill file is at 38.5 KB against the 25 KB WARN ceiling, so prose must go to the reference per the progressive-disclosure discipline. The repointment of `7b2ed33a` to `/qor-audit Step 1` becomes true when the anchor lands in that step.

## Findings

### 1. The gap, verified

- Greps for toolset/declare/first-response language over `qor/skills/governance/qor-audit/` find only the capability-shortfall fallback machinery (the #342 evidence, re-confirmed at v0.148.1).
- The Option B dispatch protocol lives at `references/adversarial-mode.md` (operator dispatch options at line 105); SKILL.md Step 1 (heading at line 180) already delegates its adversarial-mode detail there at lines 198/222 -- the anchor pattern to follow.

### 2. Corpus constraints

- `skill_size_budget_lint`: qor-audit SKILL.md at 38.5 KB (WARN band). One anchor sentence maximum in SKILL.md; the contract body goes to the reference (SG-SkillCorpusGrowth-A discipline).
- Five wiring tests bind qor-audit SKILL.md tokens (external-reviewer, plan-text-consistency, runtime-principal, session-total-escalator, spec-delta); all assert presence of THEIR tokens -- an additive anchor breaks none.

### 3. Contract shape (from the original proposal, sharpened for enforcement)

1. The dispatch prompt MUST instruct the reviewer to open its report by declaring its available toolset (shell, git, repository file access, network).
2. The Judge maps each mandating finding's verification to the declared set. A verification the reviewer could not have executed is not pinnable as reviewer-verified: the orchestrating agent re-executes it, or the finding carries PLAUSIBLE (not CONFIRMED) status until re-executed.
3. The audit report's Mode line records the declared toolset (the Phase 225-227 reports' "with shell access" phrasing, made mandatory).

### 4. Testable surface

Prose contracts get wiring tests in this repo (presence of the load-bearing tokens at their declared homes). Two tests: the reference section exists with its binding sentence, and SKILL.md Step 1 anchors it. Both are red before the amendment. Behavioral enforcement (a lint over dispatch prompts) is not in scope -- there is no machine-readable dispatch-prompt artifact to lint; noted as the same V1-disclosure/V2-enforcement posture as other prose contracts.

### 5. Repointment mechanics

Same pattern as Phase 227: `correct_closure_enforcers({7b2ed33a: "/qor-audit Step 1"})` under a reviews-remediate PASS attestation, executed only after the amendment is green -- the gate-step citation names the step that then carries the anchor. Artifact paths written repo-relative (the #344 publication-boundary lesson).

## Blueprint Alignment

| Claim | Actual Finding | Status |
|---|---|---|
| iter6 [5]: no toolset requirement exists in the skill | Re-verified at v0.148.1 | MATCH |
| #342: repointment must land with the shipping phase | This phase ships the mechanism and the repoint together | MATCH |

## Recommendations

1. Phase 228 (feature): the contract in `adversarial-mode.md`, the anchor in Step 1, two wiring tests, the repointment. After it seals, #342's remaining items are the escalator enhancements (enhancement, not debt) and the reopening-vs-acceptance decision, which the shipped state resolves toward documented acceptance.

## Updated Knowledge

Phase 225's backtick normalization means an evidence statement cannot quote an observed line that itself contains backticks (the observed text loses them; the file line keeps them; `reproduces` compares strictly). Declared partially in Phase 225's boundaries (grep patterns); the observed-text half surfaced here. Plan anchors must use backtick-free lines; a fold-in candidate for the next plan_grep_lint phase.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
