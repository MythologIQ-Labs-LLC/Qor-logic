# AUDIT REPORT — Phase 56: Secret-scanning gate at /qor-substantiate Step 4

**Verdict**: **PASS**
**Risk grade**: L2 (security-relevant; closes long-standing Cedar-attribute gap from Phase 23)
**Plan**: `docs/plan-qor-phase56-secret-scanning-gate.md`
**Session**: `2026-05-01T1825-c495a9`
**Auditor**: The QorLogic Judge (adversarial mode: solo — codex-plugin not declared; capability shortfall logged to shadow genome)
**Audit timestamp**: 2026-05-01T19:00:00Z

---

## Step 0 — Gate check

- Plan artifact present: `.qor/gates/2026-05-01T1825-c495a9/plan.json` ✓
- Schema-valid against `qor/gates/schema/plan.schema.json` ✓
- `change_class: feature` declared (bold-form) ✓
- `ai_provenance.human_oversight: absent` per Phase 54 doctrine ✓
- `terms_introduced` declares 2 new terms with `home: qor/references/doctrine-eu-ai-act.md` ✓
- `boundaries` block well-formed (limitations + non_goals + exclusions) ✓

## Step 0.6 — Pre-audit lints (Phase 55 deliverables)

| Lint                          | Exit | Verdict |
|-------------------------------|------|---------|
| `plan_test_lint`              | 0    | CLEAN   |
| `plan_grep_lint`              | 0    | CLEAN   |
| `prompt_injection_canaries`   | 0    | CLEAN   |

The Phase 55 cross-session-recurring-pattern remediation (presence-only-test detector + infrastructure-mismatch detector) finds nothing in this plan. Phase 56 self-application clean.

---

## Pass 1 — Security audit (L3 violations)

| Check                                              | Status |
|----------------------------------------------------|--------|
| No placeholder auth logic                          | PASS   |
| No hardcoded credentials/secrets                   | PASS   |
| No bypassed security checks                        | PASS   |
| No mock authentication returns                     | PASS   |
| No `// security: disabled for testing` markers     | PASS   |

The plan introduces a structural gate that BLOCKS on detection (fail-closed posture). No L3 violations.

## Pass 2 — OWASP Top 10 (2021)

- **A03 Injection**: `scan_staged` invokes `subprocess.run` with explicit list-form argv `["git", "diff", "--cached", "--name-only", "--diff-filter=AM"]` — no `shell=True`, no string interpolation. Behavior locked by `test_scan_staged_invokes_git_diff_cached_argv_form` (monkeypatch + assert exact argv). PASS.
- **A04 Insecure Design**: BLOCK on detection (CLI exit 1 + non-zero propagates to `|| ABORT` in substantiate Step 4.6.5). No silent drop, no fail-open. PASS.
- **A05 Security Misconfiguration**: `Finding.matched_text_redacted` reduces visible match to `<first4>...<last2>` so the JSON findings file may be committed/shared without leaking secrets. Behavior locked by `test_scan_returns_finding_with_redacted_match` and `test_to_gitleaks_json_secret_field_is_redacted`. PASS.
- **A08 Software/Data Integrity**: stdlib-only (`re`, `subprocess`, `pathlib`, `json`, `dataclasses`). No pickle, no `eval`, no `exec`, no `yaml.load`. PASS.

## Pass 3 — OWASP LLM Top 10 (2025)

- **LLM06 Sensitive Information Disclosure**: This plan IS the LLM06 closure. PASS by definition.

## Pass 4 — Ghost UI

N/A. Phase 56 ships a pure-Python CLI scanner module + skill-prose wiring. No UI. PASS.

## Pass 5 — Section 4 Razor (Simplicity)

| Check                  | Limit | Phase 56 declares | Status |
|------------------------|-------|-------------------|--------|
| Max function lines     | 40    | per-function (scan, scan_paths, scan_staged, to_gitleaks_json, redact, CLI main) — each scoped to single concern | PASS |
| Max file lines         | 250   | `secret_scanner.py ~150 LOC` (declared)        | PASS   |
| Max nesting depth      | 3     | line-walk + per-pattern apply (2 levels)       | PASS   |
| Nested ternaries       | 0     | none in declared signatures                    | PASS   |

`compute_production_attributes` declared as a thin wrapper over `secret_scanner.scan_text(content)` returning a single-key dict — well within razor.

## Pass 6 — Test functionality (presence-vs-behavior)

Each test described in the plan asserts a behavioral input → output relationship, not mere artifact existence:

- **Phase 1 tests** (19 tests): every test feeds concrete input (`AKIA...VARIANT`, `ghp_` + 36 chars, `permitted_tools = "..."`, etc.) and asserts behavior (`Finding` produced or skipped, `pattern_name` correct, exit code 0/1/2). No "does file X exist" tests.
- **Phase 2 tests** (6 tests): `test_substantiate_skill_invokes_secret_scanner_at_step_4_6_5` is framed as a Phase-50 co-occurrence behavior invariant ("any SKILL.md whose phase: substantiate MUST invoke …"), conditional on actual frontmatter — the admissible class. Companion behavior tests (`test_substantiate_secret_scan_blocks_seal_when_finding_present`, `test_compute_production_attributes_returns_has_hardcoded_secrets`) provide the functional proof.
- **Phase 3 tests** (4 tests): `test_doctrine_eu_ai_act_declares_secret_scanning_section_with_non_empty_body` requires non-empty body + literal mention of `LLM06` / `AI 600-1 §2.10` / `gitleaks` — not a presence-only check.

Negative-path coverage present: `test_scan_skips_aws_access_key_in_allowlist`, `test_scan_paths_skips_binary_files`, `test_scan_staged_returns_empty_when_nothing_staged`, `test_cli_exit_2_on_invalid_input`. PASS.

## Pass 7 — Dependency audit

| Package                   | Status   |
|---------------------------|----------|
| `re` (stdlib)             | PASS     |
| `subprocess` (stdlib)     | PASS     |
| `pathlib` (stdlib)        | PASS     |
| `json` (stdlib)           | PASS     |
| `dataclasses` (stdlib)    | PASS     |
| `argparse` (stdlib, CLI)  | PASS     |

Zero new runtime dependencies. Honors stdlib-only doctrine (`pyproject.toml` runtime deps remain locked). PASS.

## Pass 8 — Macro-level architecture

- **Module placement**: `secret_scanner` lives in `qor/scripts/` matching Phase 53 (`prompt_injection_canaries`), Phase 54 (`ai_provenance`), Phase 55 (`sbom_emit`, `model_pinning_lint`, `plan_test_lint`, `plan_grep_lint`). Convention-aligned.
- **Cedar attribute computation**: new `compute_production_attributes` in `qor/policy/resource_attributes.py` is the symmetric helper to the existing `compute_governance_attributes` (Phase 53) and `compute_skill_admission_attributes` (Phase 55). Single-source-of-truth pattern preserved.
- **No cyclic deps**: scanner is leaf module (no imports from `qor.policy.*`); `compute_production_attributes` depends on scanner (one-direction); skill prose invokes scanner via `python -m`. Clean.
- **Layering**: scripts ← policy ← skill-prose. No reverse imports.
- **No domain-mixing in any single file**: scanner contains scanning concerns only; resource_attributes contains attribute computation only; doctrine contains doctrine only.

PASS.

## Pass 9 — Orphan / build-path verification

| Proposed artifact                                         | Connection                                                        | Status     |
|-----------------------------------------------------------|-------------------------------------------------------------------|------------|
| `qor/scripts/secret_scanner.py`                           | `python -m qor.scripts.secret_scanner` + imported by tests + by `compute_production_attributes` | Connected  |
| `qor/policy/resource_attributes.py` (extension)           | already imported by Cedar-attribute callers                       | Connected  |
| `qor/skills/governance/qor-substantiate/SKILL.md` (edit)  | already in skill registry                                         | Connected  |
| `qor/references/doctrine-eu-ai-act.md` (append)           | read by `test_doctrine_eu_ai_act_declares_secret_scanning_section_with_non_empty_body` and existing doctrine-anchored tests | Connected  |
| `qor/references/glossary.md` (append)                     | read by `test_glossary_round_trips_against_phase56_terms`         | Connected  |
| `qor/references/doctrine-shadow-genome-countermeasures.md` (append SG-SecretLeakAtSeal-A) | already in SG catalog                  | Connected  |
| `qor/policies/owasp_enforcement.cedar` (existing rule wired) | rule existed since Phase 23; Phase 56 wires the boolean         | Connected  |
| `qor/scripts/sprint_progress.py` (extension)              | invoked by Phase 54 sprint-progress CLI                           | Connected  |
| All `tests/test_*.py` files                                | discovered by pytest                                              | Connected  |

Zero orphans. PASS.

## Pass 10 — Infrastructure alignment

`plan_grep_lint` (Phase 55) returned EXIT=0. Spot checks confirm:

- `compute_governance_attributes` referenced as **existing** ✓ (line 50 of `qor/policy/resource_attributes.py`)
- `compute_skill_admission_attributes` referenced as **existing** ✓ (line 111)
- `compute_production_attributes` declared **NEW** ✓ (no current definition; appropriate)
- `forbid has_hardcoded_secrets` referenced as **existing** ✓ (line 30 of `qor/policies/owasp_enforcement.cedar`)
- Phase 33 seal-tag pattern, Phase 50 co-occurrence model, Phase 53 canary-scan idiom, Phase 55 SBOM convention — all referenced consistently with current state.

PASS.

## Pass 11 — Prompt-injection canary scan (Phase 53 self-application)

`prompt_injection_canaries --mask-code-blocks --files docs/plan-qor-phase56-secret-scanning-gate.md` returned EXIT=0. No canary patterns in plan prose. PASS.

## Pass 12 — Self-application meta-coherence

- Phase 56 introduces a self-application test (`test_secret_scanner_clean_against_phase56_plan_and_doctrine`) that runs the new scanner against this plan + the new doctrine + the new test files, asserting empty findings. This forces the doctrine prose to use the redaction discipline its own scanner enforces — meta-coherent.
- `test_phase56_implement_gate_carries_ai_provenance` carries the Phase 54 provenance discipline forward.
- `test_pre_audit_lints_clean_against_phase56_plan` asserts forward-compatibility with the Phase 55 lints (this audit just confirmed: clean).

PASS.

---

## Open question resolutions (from plan)

1. **Scan scope**: default **(a) staged set only**. Approved.
2. **Allowlist source**: default **(a) frozenset constant in `secret_scanner.py`**. Approved (matches `_CANONICAL_TOOLS` and Phase 53 `CANARIES` pattern).
3. **Findings JSON output**: default **`--out dist/secrets.findings.json`** (operator-overridable). Approved (matches Phase 55 SBOM convention).

## Verdict

**PASS** — Phase 56 may proceed to `/qor-implement`.

### Risk grade rationale (L2)

- L2 because Phase 56 wires a new pre-seal gate that ABORTs substantiate on findings. Behavior change is operator-visible (substantiate may now block where it previously sealed) but failure-mode is fail-closed and operator-actionable (remediate flagged secret → re-stage → re-run).
- Not L3: no production-traffic security gap is introduced; the gate adds a check that did not exist.
- Not L1: Cedar policy gains a real signal (the `has_hardcoded_secrets` boolean was previously always False), so post-Phase-56 audit semantics shift for any future code that triggers it.

### Mandated next action

`/qor-implement` per `qor/gates/chain.md`. Phase 56 begins with `tests/test_secret_scanner.py` (TDD), then `qor/scripts/secret_scanner.py`, then Phase 2 wiring, then Phase 3 doctrine.

### Notes for implement phase

- Per CLAUDE.md test discipline: write the failing test first; tests run twice in a row to confirm determinism.
- Phase 53/54/55 attribution-trailer discipline applies (canonical co-author trailer in commit message). Phase 53's omission was caught by `test_attribution_tiered_usage` and required a local-only amend; do not repeat.
- Phase 17 intent-lock will fingerprint plan + this audit + HEAD at /qor-implement Step 5.5; preserve through to substantiate Step 4.6.
- Final substantiate must invoke the new Step 4.6.5 against itself (the seal commit must scan clean) — meta-coherence enforced.
