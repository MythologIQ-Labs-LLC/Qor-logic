# Research Brief

**Date**: 2026-05-29
**Analyst**: The Qor-logic Analyst
**Target**: Verification & Closure Integrity feature (GH #166 QA discipline + #158 acceptance-criteria close guard); ideation session `2026-05-29T0252-f6486c`
**Scope**: Resolve four load-bearing unknowns before planning: (1) security-tooling salvage, (2) compact QA-evidence gate artifact, (3) overlap boundaries vs #155/#86/#108/#162, (4) close-guard criteria parsing. Honor the context-lean / progressive-disclosure constraint.

---

## Executive Summary

The biggest finding is a **scope reframe**: this should NOT be built as a new QA "discipline/skill" with four fresh pillars. Research shows the capability is almost entirely the **fail-closed promotion plus seal-time wiring of surfaces that already exist** — the deferred D4 tier of the #86 Definition of Done, the deferred FEATURE_INDEX ABORT helper (#155/#40), and the existing runtime-contract walk (#108) which is the de-facto stability pillar. Two QA sub-pillars (secret-scan, dependency/SBOM) are already live and blocking; OWASP is already governed; **SAST is the only genuine net-new gap**. The three quarantined "security skills" are prose-only stubs with zero runnable code and are not worth salvaging. The close guard is feasible but its "met-ness" signal must come from a compact `qa.json` evidence artifact, not from checkbox state — and it should ship WARN-first because it sits on the seal control path. This reframe directly serves the context-lean constraint: far less new prose, mostly wiring.

## Findings

### 1. Security-tooling salvage — assumption was pessimistic; most pillars already exist

- The three targets (`owasp-top10-auditor`, `sbom-risk-scanner`, `security-permission-audit`) are **prose-only `SKILL.md` stubs archived under `docs/archive/2026-04-15/ingest/...`**; none ship a single `.py`/`.sh`. `security-permission-audit` is Hearthlink/Tauri-specific (`qor/vendor/skills/security-permission-audit/SKILL.md:10-22`) and off-target. Salvage value: **LOW**.
- Already live and gating:
  - **secret-scan**: `qor/scripts/secret_scanner.py` (gitleaks-v8 schema, no new deps), wired as a BLOCKING gate at `qor/skills/governance/qor-substantiate/SKILL.md:67,291-298` (Step 4.6.5).
  - **dependency/SBOM**: `qor/scripts/sbom_emit.py` (CycloneDX 1.5) + `qor release sbom` (`qor/cli_handlers/release.py:12-31`) + `.github/workflows/pr-dependency-review.yml:28-31` (fail-on-high) + `qor/scripts/dependency_admission_lint.py:1-35`.
  - **OWASP**: `qor/references/doctrine-owasp-governance.md` + `qor/policies/owasp_enforcement.cedar` + the `/qor-audit` OWASP pass (A03/A04/A05/A08).
- **SAST is not covered** anywhere live (no semgrep/bandit/CodeQL). This is the only sub-pillar needing net-new authoring + a real tool dependency.

### 2. Compact QA-evidence gate artifact (`qa.json`) — conventions confirmed, shape proposed

- Common gate envelope across all schemas: `phase` (const), `ts` (ISO-Z regex), `session_id` (minLength 3), optional `ai_provenance` (`$ref _provenance.schema.json`); all schemas set `additionalProperties: true` (e.g. `qor/gates/schema/substantiate.schema.json:9-12,24`, `audit.schema.json:6,49`).
- Compact conventions: short verdict enums (`PASS|FAIL` at `substantiate.schema.json:12`), evidence referenced by **path** not inlined (`report_path` at `audit.schema.json:16`), per-item status objects (`validate.schema.json:13-24`).
- Proposed minimal `qa.json`: envelope + `verdict: PASS|FAIL` + `pillars{regression,security,stability,coverage}` where each pillar = `{status: pass|fail|skip, evidence: <path>, metric?, note?}`. Logs stay on disk. Skeleton captured in the planning notes.
- Read path for the close guard: `gate_chain.read_phase_artifact("qa", session_id=sid)` (`qor/scripts/gate_chain.py:170`); `qa` is **off-CHAIN** (like `remediate`; `gate_chain.py:28`) so it is read directly, not via `check_prior_artifact`.
- Registration: drop `qor/gates/schema/qa.schema.json` (auto-discovered by glob at `qor/scripts/validate_gate_artifact.py:34`) AND add `"qa"` to the `PHASES` list (`validate_gate_artifact.py:53-63`). For a real operator decision on the verdict, also add `"qa"` to `_OPERATOR_DECISION_PHASES` (`qor/scripts/ai_provenance.py:29`); otherwise provenance must be `absent`.

### 3. Overlap boundaries — CONSOLIDATE, do not build parallel

| Surface | Exists today (file:line) | REUSE | ADD |
|---|---|---|---|
| #86 DoD | `dod_record.py:153` parse_plan, `dod_check.py:93,116`, `doctrine-definition-of-done.md:11-22,62-70`; wired substantiate Step 4.6.7 (`qor-substantiate/SKILL.md:314-323`, WARN `|| true`) | D4 "empirical/runtime verification" tier is the **home** for QA-evidence+close-guard; reuse `DodRecord`/`check_plan` + the 4.6.7 slot | The deferred **D4 empirical-execution check** (`doctrine-definition-of-done.md:66`): cross-ref D4-declared test names vs pytest output; fail when a named test did not run/pass |
| #155/#40 regression | `feature_index_verify.py:75` `tally`->`newly_unverified`; `feature_index.schema.json`; surfaced at `qor-substantiate/SKILL.md:380-390` | `tally()`, `read/write_seal_snapshot` (`:105,:119`), the verified/unverified/n/a vocab | The **PASS-blocking ABORT** (confirmed absent: no `main()`/argparse/`__main__`/`--exit-on-any`). Deferred-language cite: `qor-substantiate/SKILL.md:392` |
| #108 runtime-contract | `runtime_contract_walk.py`, `reachability_probe.py`; `audit-runtime-contract-walk.md`, `recon-reachability-probe.md:24-107`; wired audit Step 3 (`qor-audit/SKILL.md:447-450`, WARN) + recon (`qor-deep-audit-recon/SKILL.md:48,76`) | This **is the partial stability/smoke pillar**; reuse the import-graph walk + 5-check probe as evidence | A **seal-time re-invocation** (today it only runs pre-implement, WARN-only) |
| #162 progressive-disclosure | `skill_size_budget_lint.py:23-24` (WARN 25KB/EXCEEDED 40KB); wired substantiate Step 4.6.9 (`qor-substantiate/SKILL.md:335-340`, `|| true`) | Use as-is as the **budget guardrail** on the new prose | Nothing functional; it is a constraint ON this work, not a surface to merge |

**Biggest duplication risk:** authoring a fresh "QA gate" as a new Step 4.6.x that re-implements plan-section parsing (`dod_record.parse_plan`), test-result cross-reference, and verified->unverified diffing (`feature_index_verify.tally`). Avoid by framing the work as: (1) DoD-V2 D4 empirical check beside `dod_check.py`; (2) the deferred CLI + ABORT on top of `feature_index_verify.tally`; (3) seal-time re-invoke of `runtime_contract_walk`.

### 4. Close-guard criteria parsing — feasible; met-ness comes from `qa.json`, ship WARN-first

- No `gh issue close` / `Closes #` in the seal flow today; GitHub auto-closes when a PR body `Closes #NNN` merges (`qor-substantiate/SKILL.md:635`). Hook point: a new **Step 4.6.10** reliability gate, modeled on the 4.6.7 `dod_check` envelope, per the append-only ladder invariant (`qor-substantiate/SKILL.md:43`).
- No Markdown-checkbox parser exists (greenfield), but reuse: section-slice + fence-strip from `dod_record.py:68,90` (`_strip_fenced_code_blocks`, `_extract_section_body`), the line-scan idiom from `plan_test_lint.py:69-84`, and the WARN-only CLI envelope from `dod_check.py:116`. Checkbox regex: `^\s*[-*]\s+\[([ xX])\]\s+(.+)$`.
- Issue/linked-PR data: `gh issue view N --json body,state,closedByPullRequestsReferences`; follow-on discovery: `gh issue list --search "in:body #N"` (idiom from `qor-research/SKILL.md:63-66`). File follow-ons by reusing `create_shadow_issue.create_issue` (`qor/scripts/create_shadow_issue.py:93`); auth/fallback via `ensure_gh_auth` (`:39`) + Phase 75 SKIP when `gh` absent.
- Prose-not-behavior secondary lint: a plan-text presence detector exists (`plan_test_lint.py:29-38`; audit pass `qor-audit/SKILL.md:374`) but a **test-source** scanner (open `tests/*.py`, flag assertions that only check substring-in-SKILL.md) is **net-new** (it can reuse the `_PRESENCE_PATTERNS` vocabulary).

## Blueprint (ideation) alignment

| Ideation assumption | Finding | Status |
|---|---|---|
| Quarantined security tooling is salvageable/wireable (med, non-blocking) | Stubs are prose-only, zero code; most sub-pillars already live; only SAST is new | **DRIFT (favorable)** — assumption obsolete; reuse live components, author SAST only |
| QA evidence representable as a compact gate artifact (med) | Yes — `qa.json` envelope + per-pillar status/evidence-pointer; read via `read_phase_artifact` | MATCH (confirmed) |
| Context-lean structure can carry 4 pillars without blind spots (BLOCKING) | Reframe to "wire existing surfaces" means minimal new prose; budget lint already enforces | MATCH (de-risked) |
| Absorb #155/#86 rather than build parallel (high) | Strongly confirmed; D4 + FEATURE_INDEX ABORT are the named homes | MATCH (sharpened) |
| Close guard checks "met or split" | Checkbox state cannot prove met-ness at close; met-ness must come from `qa.json`; unmet boxes need linked follow-on | **DRIFT (refinement)** — two inputs: qa verdict PASS + unmet->follow-on |

## Recommendations

1. **(High) Reframe the plan**: deliver as the fail-closed completion + seal-time wiring of existing surfaces, NOT a new pillar skill. Three concrete deliverables: (a) DoD-V2 D4 empirical-execution check beside `dod_check.py`; (b) FEATURE_INDEX ABORT CLI on `feature_index_verify.tally`; (c) seal-time re-invocation of `runtime_contract_walk`.
2. **(High) `qa.json` evidence artifact** as the integration spine: regression (feature_index diff), security (existing secret-scan + SBOM/dep + OWASP, plus new SAST), stability (runtime-contract walk), coverage (new). Register `qa` phase per Finding 2.
3. **(High) Close guard (#158) ships WARN-first** (downgrade-to-comment), reading `qa.json` for met-ness and `gh` for unmet->follow-on; tighten to BLOCK after false-positive rate is measured. It sits on the seal control path (L3 escalation trigger per ideation).
4. **(Med) Security pillar v1**: wire secret-scan + SBOM/dep + OWASP from live components; author SAST fresh (pick bandit or semgrep) as the one new dependency. Do NOT resurrect the quarantined stubs.
5. **(Med) AC-format fallback**: when an issue has no machine-checkable checklist, ALLOW + WARN (do not block legitimate closures). This is the dominant correctness risk.
6. **(Med) Prose-not-behavior test-source lint** is net-new; scope it as a distinct deliverable reusing `plan_test_lint` patterns.

## Updated Knowledge

Candidate doctrine note (for `qor/references/`): the **Verification & Closure Integrity** capability is realized as DoD tier D4 (empirical execution) + the FEATURE_INDEX regression ABORT + seal-time runtime-contract re-walk, surfaced through an off-chain `qa.json` gate artifact and enforced by a WARN-first acceptance-criteria close guard. Reinforces SG-HalfMeasureClosure: prefer fail-closed promotion of existing WARN-only surfaces over net-new parallel gates.

---

_Research complete. Findings are advisory; implementation decisions remain with the Governor. Next phase: /qor-plan._
