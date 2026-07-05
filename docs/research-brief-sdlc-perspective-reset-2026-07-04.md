# Research Brief: SDLC Perspective Reset + Autonomous QA Investment

**Date**: 2026-07-04
**Analyst**: The Qor-logic Analyst
**Target**: Qor-logic process efficacy, the MythologIQ governance estate, an external QA workspace's repos, and an external agent-governance toolkit
**Scope**: (1) Are we over-invested in our own process ceremony? (2) Does the QA/remediate cycle burn tokens disproportionately? (3) How do we extend Qor-logic into real autonomous QA that does not assume heavy user engagement?

---

## Executive Summary

The operator's token-burn intuition holds up under evidence: of the last ~60 phases (104-163), roughly 83% hardened the governance machinery itself, first-pass audit VETO rate runs ~33% (211 VETO mentions across 377 ledger entries), and 51% of ledger entries reference remediate/debug/course-correct workflows. The dominant burn vector has a signature: prose doctrine that fails to prevent recurrence (SG-038 recurred 4+ times after codification) plus a seal-fragile test class (badges, freshness, keyword wiring) that breaks on nearly every seal. The external reference repos (an external QA exemplar, external agent-governance toolkit) converge on the same counter-pattern: replace prose rules and ceremony-heavy review with deterministic, fail-closed, executable checks that run without a human -- and reserve ceremony for genuinely high-risk changes.

## Findings

### 1. Process efficacy inside Qor-logic (the "married to process" question)

- **Phase composition (entries #278-377)**: ~50 of 60 recent phases hardened governance machinery (seal integrity, citation drift, merge velocity, provenance binding); ~5 test/CI mechanics; ~5 docs/process; ~0 outward-facing capability. Caveat: Qor-logic's product IS governance machinery, so some of this is legitimate capability -- but the ratio of "fixing our own gates" to "new operator-visible capability" is the warning sign.
- **Doctrine does not self-enforce**: SG-038 (prose/code enumeration drift) recurred in phases 15, 17a, 19, 20, and again in 28 -- after codification (docs/SHADOW_GENOME.md lines 346-391, 548, 598). SG-036 (new doctrine not load-bearing in phase N+1) repeated the same way. Writing a rule down has measurably NOT prevented its recurrence; only executable enforcement has.
- **Gate overhead per change**: the chain in qor/scripts/gate_chain.py:28 mandates research -> plan -> audit -> implement -> substantiate -> validate for every change regardless of size. With ~33% first-pass VETO, an average change traverses ~8 gate evaluations. A one-line hotfix and an L3 security change pay the same ceremony tax.
- **Seal-fragile test class**: 404 test files vs 183 source files (~2.2:1); an estimated 50-60% test the governance machinery itself. The badge/freshness/keyword/doc-currency class breaks on nearly every seal (bit phases 121/122/123, 140), forcing remediation loops that verify formatting, not behavior. These assert generated-artifact state rather than behavior -- they test what a generator could simply produce.
- **Remediation recursion**: Phase 122 added a "seal-time regression gate fail-closed" -- a fix to the test-fixing machinery. The remediation layer has itself required remediation, which matches the operator's "persistent band-aid" description.

**Verdict**: Directionally confirmed. The precise token counts are not recoverable from the ledger, but the structural evidence (VETO rate, remediation mention rate, phase composition, fragile-test recurrence) all point the same way: the process currently optimizes for its own integrity faster than it delivers capability, and the marginal governance rule now costs more than it saves.

### 2. The MythologIQ governance estate (fragmentation check)

14+ repos carry governance artifacts. Three families:

- **S.H.I.E.L.D. dogfood** (seven sibling governance repositories): faithful copies of the canonical system. One sibling consumer workspace has the largest gate archive (104 sessions, active 2026-07-04); another sibling repository carries ledger-migration tooling (scripts/migrate_ledger_v0_14.py handles 3 legacy hash formats); two more implement SQLite ledger backends with import/export CLIs.
- **External mutation-classification doctrine (M0-M5)** (a sibling repo family): orthogonal innovation, not a fork. Mutation classes M1-M5 with authority ceilings A0-A5 (fine-grained change governance), tracked-governance-docs exception (`.qor/` tracked, HMAC keys never), and a PUBLIC-repo governance mirroring pattern (public repos gitignore `.qor/`, CI syncs artifacts to a private factory mirror) -- documented in a sibling repository's docs/governance/PUBLIC_REPO_GOVERNANCE_AGGREGATION.md.
- **Specialty** (one sibling repo is a central audit hub; one runs four-agent self-application; three more are minimal or stale).

Fragmentation grade: moderate. The S.H.I.E.L.D. copies are cohesive; the risk is not divergence but duplication -- every repo re-solves ledger migration, gate storage, and mirror problems locally instead of consuming them from the Qor-logic dist.

### 3. Autonomous QA patterns from an external QA workspace

The external QA exemplar's repos demonstrate QA that runs without a human in the loop:

- **Executable lints over prose rules**: an external QA exemplar's RLS-migration lint script statically parses every SQL migration and fails CI when a public table lacks RLS, with an allowlist file documenting intentional exceptions with reasons. The lint's parsing functions are exported and unit-tested (tests/lint-migration-rls.test.ts). This closed a recurring security regression class permanently -- the exact outcome Qor-logic's prose doctrine keeps failing to achieve for SG-038.
- **Scheduled drift detection with automatic issue lifecycle**: an external QA exemplar's drift-detection workflow runs daily, compares staging/prod migration state, and creates/updates/closes GitHub issues automatically (scripts/drift-check.sh, with a --self-test mode).
- **Risk-stratified coverage**: vite.config.ts lines 26-42 -- a 2% global coverage floor with 90-95% overrides on security-critical modules. Rigor where risk lives; no busywork elsewhere.
- **Regression-guard tests named for their issue** (tests/e2e/smoke.spec.ts lines 18-22): each guard cites the PR/issue it locks, so future maintainers cannot silently remove it.
- **Smoke tests with proactive error collection**: Playwright attaches page-error listeners before navigation, filters expected auth errors, and hard-fails on ReferenceError classes.
- **Dry-run rehearsal for irreversible ops** (the external exemplar's polling tool, lines 196+): the full pipeline executes with zero side effects.
- **Secrets scanning with differential test suppression** (an external QA exemplar's secrets-scan script): high-confidence key formats always scanned; env-assignment patterns exempt in test files only.

### 4. External external agent-governance toolkit patterns

- **Deterministic, fail-closed enforcement with no LLM in the decision loop** (docs/adr/0004, 0013): sub-millisecond YAML-rule evaluation; every evaluation error denies with audit. Qor-logic's audits, by contrast, put an LLM judge in every loop -- expensive and probabilistic.
- **Runtime enforcement over pre-approval ceremony**: governance intercepts actual actions rather than gating intent documents. Failures surface live, not at the next audit pass.
- **Reconstructible Decision BOM** (docs/adr/0018, agentmesh/governance/decision_bom.py): decision context reconstructed on demand from existing observability signals (audit log, trust scores, policy records, OTel traces) instead of writing ceremonial artifacts per phase. Zero hot-path overhead.
- **Graduated execution rings** (AGENT-HYPERVISOR-EXECUTION-CONTROL-1.0.md): Ring 3 sandbox by default, Ring 1/0 require trust >0.95 plus consensus. Privilege scales with demonstrated trust and irreversibility -- the runtime analogue of the external doctrine's M1-M5 classes.
- **Formal specs + conformance suites**: 992 conformance tests against 10 RFC 2119 specs keep multi-language implementations honest.
- **Validation of the Merkle approach**: the toolkit independently chose SHA-256 hash-chained audit entries (docs/adr/0017) -- Qor-logic's ledger design is on the right track; the delta lies in what gets chained (runtime decisions vs. ceremony artifacts).

## Blueprint Alignment

| Blueprint/doctrine claim | Actual finding | Status |
|---|---|---|
| Gate chain protects delivery quality | It does -- but at a flat 6-gate cost for every change size, with ~33% first-pass VETO producing ~8 evaluations per change | DRIFT (cost model) |
| Shadow Genome codification prevents recurrence | SG-038 recurred 4+ times post-codification; SG-036 twice; only executable checks have stuck | DRIFT |
| Test discipline = quality (404 tests) | ~50-60% of the suite asserts governance-artifact state (badges, freshness, keywords) rather than behavior; this class breaks on nearly every seal | DRIFT (test-functionality doctrine violated by our own suite) |
| META_LEDGER Merkle chain as integrity spine | Independently validated -- an external agent-governance toolkit's ADR 0017 converged on the same design | MATCH |
| Qor-logic as reusable SDLC package across the estate | 14+ repos consume it, but each re-solves migration/mirroring/storage locally; a sibling family extended rather than forked | PARTIAL MATCH |

## Recommendations

Priority-ordered; each attacks a measured burn vector.

1. **Risk-tiered gate depth (adopt the external doctrine's M1-M5 classes into S.H.I.E.L.D.)** [HIGH]. Classify each change (M1 docs-typo ... M5 security/irreversible) at plan time; let M1-M2 traverse a short chain (plan -> implement -> substantiate) while M4-M5 keep the full ceremony + adversarial audit. Directly reduces the ~8-evaluations-per-change overhead for the majority of changes. Reference: a sibling repository GOVERNANCE_DOC_TRACKING_PROPAGATION.md; toolkit execution rings.
2. **Kill the seal-fragile test class by generating instead of asserting** [HIGH]. Badges, freshness headers, keyword wiring, changelog stamps: make substantiate/apply_stamp deterministically GENERATE these artifacts, and keep only a single idempotence test (generator output == committed state). Stops the phases-121/122/123/140 recurrence class outright; largest single remediation-loop eliminator.
3. **"Doctrine that can be a lint must become a lint"** [HIGH]. Standing rule: an SG entry may only close with either (a) an executable check wired into CI/substantiate, or (b) an explicit recorded decision that it cannot be automated. Model: an external QA exemplar repo lint-migration-rls.mjs (exported, unit-tested lint functions + allowlist-with-reasons). SG-038's four recurrences are the proof this pays.
4. **Autonomous QA layer (new capability track, not more gates)** [HIGH]. (a) Scheduled drift/health workflow that runs governance-health, doc-integrity, ledger verification, and installed-package smoke (pip install + CLI invocation) nightly and auto-opens/closes GH issues (an external QA exemplar's drift-detection lifecycle); (b) dry-run mode for every mutating qor CLI command; (c) regression-guard tests named for their GH issue. All three run with zero operator engagement.
5. **Reconstruct evidence, do not multiply artifacts** [MEDIUM]. Before adding any new per-phase artifact, prefer the Decision-BOM posture: derive audit evidence on demand from signals already recorded (ledger, gate JSONs, provenance sidecars, git). Freeze net-new ceremony artifacts unless an L3 risk demands them.
6. **Risk-stratified test rigor** [MEDIUM]. Set high coverage/behavioral bars on seal, hash, provenance, and release-gate modules; drop the flat expectation elsewhere (an external QA exemplar's vite.config.ts override pattern).
7. **Estate consolidation into the dist** [MEDIUM]. Absorb into Qor-logic proper: ledger migration tooling (a sibling governance repository), PUBLIC-repo governance mirroring (a sibling repository), and eventually a queryable SQLite ledger adapter (sibling repository references). Stops 14 repos re-solving the same problems.
8. **Machinery-vs-capability ratio on the dashboard** [LOW]. Tag each phase at plan time as machinery/capability/docs and surface the rolling ratio in /qor-status -- the early-warning light for re-entering the self-hardening loop.

## Updated Knowledge

- New evidence for the governance corpus: prose codification alone has a 0-for-4 record against SG-038 recurrence; enforcement doctrine should route pattern closures toward executable checks (candidate doctrine amendment: test-discipline / governance-enforcement references).
- No existing doctrine file was edited in this pass -- findings are advisory and strategic; doctrine changes route through /qor-plan per governance flow.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
