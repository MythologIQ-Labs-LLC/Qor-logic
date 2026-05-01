# Plan: Phase 56 — Secret-scanning gate at /qor-substantiate Step 4

**change_class**: feature

**doc_tier**: standard

**terms_introduced**:
- term: secret-scanning gate
  home: qor/references/doctrine-eu-ai-act.md
- term: gitleaks-compatible findings
  home: qor/references/doctrine-eu-ai-act.md

**boundaries**:
- limitations:
  - Regex-pattern detection only (no entropy heuristics, no probabilistic ML detection). High-entropy random strings that don't match any catalog pattern will not be flagged. Phase 57+ may add entropy scoring as an extension.
  - Allowlist is a literal-substring exclusion set; it does not understand context (e.g., `secret_key = "REDACTED"` would be flagged unless `REDACTED` is in the allowlist).
  - Scan is run at substantiate Step 4 over **staged content** for the seal commit; pre-staged uncommitted changes are not in scope (they will be rescanned next seal cycle if staged).
  - Findings JSON format follows gitleaks v8 schema for downstream tool compatibility, but the scanner itself is not gitleaks — it's a hand-rolled regex catalog. Operators wanting gitleaks-grade detection should run `gitleaks detect` separately.
- non_goals:
  - Live Git history scanning (gitleaks-style full-history sweep). Substantiate-time scan covers only the seal commit's staged set.
  - Encrypted secret detection (e.g., AES-encrypted blobs). Out of scope.
  - GitHub secret-scanning API integration. Out of scope; downstream consumers can use both signals independently.
  - Auto-redaction or `git-filter-repo`-style purge. Phase 56 detects and BLOCKS; remediation is operator-driven.
- exclusions:
  - Retroactive scanning of historical seal commits. Forward-only enforcement (Phase 56+ seals).
  - Modifying any existing skill bodies beyond `/qor-substantiate` Step 4 wiring.

## Sprint context

Phase 56 of the five-phase compliance sprint started at Phase 53. Closes the originally-optional Priority 6 (NIST AI 600-1 §2.10 / OWASP LLM Top 10 LLM06 — Sensitive Information Disclosure). After Phase 56 ships, all six framework gaps from `docs/research-brief-prompt-logic-frameworks-2026-04-30.md` are closed:

| Phase | Status | Closes |
|---|---|---|
| 53 | sealed v0.39.0 | LLM01 + DRIFT-1/2 + OWASP LOW-4 |
| 54 | sealed v0.40.0 | EU AI Act Art. 13/14/50 + AI RMF + LLM08 |
| 55 | sealed v0.41.0 | LLM05 + LLM07 + AI RMF GV-6.1/MG-3.1 |
| **56 (this plan)** | drafting | LLM06 + AI 600-1 §2.10 |

This is the **structural countermeasure plan** for the existing Cedar policy `forbid has_hardcoded_secrets` rule on `Code::"production"` — that rule has been on the books since Phase 23 with no actual scanner driving the boolean attribute. Phase 56 wires the scanner.

## Open Questions

1. **Scan scope**: at substantiate Step 4 the scanner reads (a) only files in `git diff --cached --name-only` (the staged set for the seal commit), (b) the staged set plus the META_LEDGER and CHANGELOG in the worktree, or (c) the entire worktree. Default: **(a)** — staged set only matches the existing release-doc-currency check semantics and minimizes false positives from old test fixtures. Files containing example secrets (e.g., `tests/test_*` test fixtures) are out-of-scope unless staged.
2. **Allowlist source-of-truth**: the literal-substring allowlist lives in (a) `qor/scripts/secret_scanner.py` `_ALLOWLIST` frozenset constant, (b) `qor/policies/secret_allowlist.txt` data file, (c) `qor/gates/schema/secret_allowlist.schema.json` validated config. Default: **(a)** — frozenset constant; same single-source-of-truth pattern as `_CANONICAL_TOOLS` and `CANARIES`. Test reads the constant for round-trip integrity.
3. **Findings JSON output path**: (a) `dist/secrets.findings.json` (parallels `dist/sbom.cdx.json` Phase 55 pattern), (b) `.qor/gates/<sid>/secrets.findings.json` (sidecar to gate dir), (c) operator-supplied via `--out`. Default: **(c) with (a) as default value** — `--out dist/secrets.findings.json` matches Phase 55 SBOM convention; operator can override.

Defaults will be encoded unless overridden during audit.

## Phase 1: Secret-scanner module + allowlist + canonical pattern catalog

### Affected Files

- `tests/test_secret_scanner.py` — NEW: locks the canonical pattern catalog + allowlist + scan API.
- `tests/test_secret_scanner_findings_format.py` — NEW: locks the gitleaks-v8-compatible findings JSON shape.
- `qor/scripts/secret_scanner.py` — NEW (~150 LOC): pure-Python scanner. Public API:
  - `Pattern` frozen dataclass: `(name: str, regex: re.Pattern, severity: int, description: str)`.
  - `PATTERNS: tuple[Pattern, ...]` — single source of truth, ~12-15 entries covering: AWS access key (`AKIA[0-9A-Z]{16}`), AWS secret key (`[A-Za-z0-9/+=]{40}`-context-anchored), GitHub PAT (`ghp_[A-Za-z0-9]{36}` and `github_pat_[A-Za-z0-9_]{82}`), GitHub OAuth (`gho_[A-Za-z0-9]{36}`), private SSH key (`-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----`), Stripe live key (`sk_live_[A-Za-z0-9]{24,}`), Slack token (`xox[baprs]-[A-Za-z0-9-]{10,}`), Google API key (`AIza[A-Za-z0-9_-]{35}`), Anthropic key (`sk-ant-[A-Za-z0-9_-]{90,}`), generic high-entropy assignment (`(?:secret|token|api_key|password)\s*=\s*["'][A-Za-z0-9/+=_-]{20,}["']`), private-key URL (`https?://[^:]+:[^@]+@`).
  - `_ALLOWLIST: frozenset[str]` — literal-substring exclusion set. Initial seed: `("YOUR_API_KEY_HERE", "REDACTED", "EXAMPLE_SECRET", "AKIAIOSFODNN7EXAMPLE", "claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5", "ai_provenance", "permitted_tools", "permitted_subagents", "model_compatibility", "min_model_capability", "OverrideFrictionRequired", "compute_skill_admission_attributes")`. The Cedar/schema attribute names are seeded because they pattern-match the generic high-entropy assignment regex but are not secrets.
  - `Finding` frozen dataclass: `(file: str, line: int, pattern_name: str, severity: int, matched_text_redacted: str)`. `matched_text_redacted` shows first 4 + last 2 chars with `...` between to allow audit without leaking the secret in the findings file.
  - `scan(path: Path) -> list[Finding]` — scans a single file.
  - `scan_paths(paths: list[Path]) -> list[Finding]` — scans multiple; aggregates findings.
  - `scan_staged(repo_root: Path) -> list[Finding]` — runs `git diff --cached --name-only` via argv-form subprocess; scans the resulting paths. Per Open Question 1 default.
  - `to_gitleaks_json(findings: list[Finding]) -> list[dict]` — converts to gitleaks v8 schema (`Description`, `RuleID`, `File`, `Line`, `Match`, `Secret` redacted, `Tags`).
  - CLI entry point: `python -m qor.scripts.secret_scanner [--staged | --files PATH...] [--out PATH] [--allowlist-extra TOKEN]`. Exit 0 on no findings; exit 1 on any finding (BLOCK); exit 2 on input rejection.

### Changes

The pattern catalog is the canonical secret-class taxonomy. Each pattern has a name (used as gitleaks `RuleID`), a regex, a severity (3 for high-confidence patterns like AWS access keys; 2 for medium-confidence like generic assignments), and a description.

`scan` opens each file and walks lines, applying every pattern. A line that matches AND does not contain any allowlist substring is a finding. Lines containing allowlisted substrings are silently passed (false-positive class).

`Finding.matched_text_redacted` reduces the visible match to `<first4>...<last2>` so the findings file can be committed/shared without leaking the secret. Original match is never persisted.

`scan_staged` invokes `git diff --cached --name-only --diff-filter=AM` (added/modified) via argv-form subprocess, then scans each path. Skips paths that don't exist (deleted) or are binary (heuristic: first 8KB contains null byte).

CLI exits 1 (BLOCK) on any finding to make the scanner usable as a substantiate gate.

### Unit Tests

- `tests/test_secret_scanner.py`:
  - `test_scan_detects_aws_access_key` — feed `AKIAIOSFODNN7VARIANT` (random 16 alphanumeric); assert finding with `pattern_name == "aws-access-key"`.
  - `test_scan_skips_aws_access_key_in_allowlist` — feed `AKIAIOSFODNN7EXAMPLE`; assert no finding (allowlisted).
  - `test_scan_detects_github_pat_classic_format` — feed `ghp_` + 36 chars; assert finding.
  - `test_scan_detects_github_pat_finegrained_format` — feed `github_pat_` + 82 chars; assert finding.
  - `test_scan_detects_private_ssh_key_header` — feed `-----BEGIN OPENSSH PRIVATE KEY-----`; assert finding.
  - `test_scan_detects_anthropic_key` — feed `sk-ant-` + 95 chars; assert finding.
  - `test_scan_detects_generic_high_entropy_assignment` — feed `secret_key = "abcDEF123ghiJKL456mnoPQR789"`; assert finding.
  - `test_scan_skips_known_attribute_name_pattern` — feed `permitted_tools = "Read, Grep, Bash, Edit, Write, Agent"` (resembles assignment but allowlisted). Assert no finding.
  - `test_scan_returns_finding_with_redacted_match` — assert `Finding.matched_text_redacted` form: first 4 chars + `...` + last 2 chars.
  - `test_scan_returns_finding_with_correct_line_number` — secret on line 5; assert `Finding.line == 5`.
  - `test_scan_paths_aggregates_findings_across_multiple_files` — two files, one finding each; assert returns 2 findings.
  - `test_scan_paths_skips_binary_files` — binary fixture (null byte in first 8KB); assert no finding (skipped).
  - `test_scan_staged_invokes_git_diff_cached_argv_form` — monkeypatch `subprocess.run`; assert called with `["git", "diff", "--cached", "--name-only", "--diff-filter=AM"]`.
  - `test_scan_staged_returns_empty_when_nothing_staged` — fixture mock returns empty stdout; assert `scan_staged` returns `[]`.
  - `test_patterns_catalog_is_frozen` — assert `PATTERNS` is `tuple`; assert each `Pattern` is `frozen=True`.
  - `test_allowlist_is_frozen_and_contains_known_seeds` — assert `_ALLOWLIST` is frozenset; assert known seeds present (`REDACTED`, `EXAMPLE_SECRET`, `AKIAIOSFODNN7EXAMPLE`, `permitted_tools`).
  - `test_cli_exit_1_on_finding_via_subprocess` — fixture file with planted secret; subprocess invocation; assert exit code 1, stderr contains `BLOCK`.
  - `test_cli_exit_0_on_clean_via_subprocess` — clean fixture; assert exit 0.
  - `test_cli_exit_2_on_invalid_input` — `--files /nonexistent/path`; assert exit 2.
- `tests/test_secret_scanner_findings_format.py`:
  - `test_to_gitleaks_json_emits_required_v8_fields` — invoke `to_gitleaks_json([finding])`; assert dict has keys `{Description, RuleID, File, Line, Match, Secret, Tags}`.
  - `test_to_gitleaks_json_secret_field_is_redacted` — assert the JSON output `Secret` field is the redacted form, not the original match.
  - `test_to_gitleaks_json_handles_empty_finding_list` — invoke with `[]`; assert returns `[]`.
  - `test_to_gitleaks_json_tags_field_includes_severity` — assert `Tags` contains a `severity:N` token derived from `Pattern.severity`.

## Phase 2: Substantiate Step 4 wiring + reliability sweep extension

### Affected Files

- `tests/test_substantiate_step_4_secret_scan_wiring.py` — NEW: locks the substantiate skill prose contains the canonical `python -m qor.scripts.secret_scanner --staged --out dist/secrets.findings.json` invocation in Step 4.
- `tests/test_substantiate_secret_scan_aborts_on_finding.py` — NEW: drives the scan via subprocess against a fixture worktree containing a staged secret; asserts the subprocess returns non-zero exit (BLOCK).
- `qor/skills/governance/qor-substantiate/SKILL.md` — APPEND new substep `### Step 4.6.5: Secret-scanning gate (Phase 56 wiring)` between the existing reliability sweep at Step 4.6 and the existing Step 4.7 documentation integrity check. Bash one-liner:
  ```bash
  python -m qor.scripts.secret_scanner --staged --out dist/secrets.findings.json || ABORT
  ```
  ABORT semantics on non-zero exit (existing reliability-sweep contract). Operator must remediate detected secrets before re-running substantiate. Findings JSON written to `dist/secrets.findings.json` for downstream tooling consumption.
- `qor/references/doctrine-eu-ai-act.md` — APPEND new section "Secret-scanning gate (Phase 56)" under Art. 50 documenting the scanner + the gitleaks-compatible JSON output + the substantiate Step 4.6.5 wiring.
- `qor/references/doctrine-shadow-genome-countermeasures.md` — APPEND new SG entry `SG-SecretLeakAtSeal-A` documenting the historical risk class + the Phase 56 countermeasure.
- `qor/policies/owasp_enforcement.cedar` — UPDATE the existing A05 `has_hardcoded_secrets` rule's enforcement boolean. The rule has existed since Phase 23 with no scanner driving the attribute; Phase 56 wires `qor.policy.resource_attributes.compute_governance_attributes` (and `compute_production_attributes` if needed — see below) to populate the boolean from `secret_scanner.scan(content)`.
- `qor/policy/resource_attributes.py` — APPEND `compute_production_attributes(path: str | Path, content: str) -> dict[str, bool]` returning `{"has_hardcoded_secrets": bool(secret_scanner.scan_text(content))}` for non-governance source files (Python, etc.). Closes the long-standing Phase 23 pattern where the Cedar attribute was declared but never computed.

### Changes

Substantiate Step 4.6.5 runs after the existing reliability sweep (Step 4.6) and before the documentation integrity check (Step 4.7). Placement matches the existing pattern of pre-seal gates that ABORT on non-zero exit.

`compute_production_attributes` is the symmetric helper to Phase 53's `compute_governance_attributes`. Both live in `qor/policy/resource_attributes.py` (the canonical per-resource-kind attribute computer). The Cedar evaluator continues to read attributes from the caller-supplied `entities` dict.

`SG-SecretLeakAtSeal-A` codifies the risk: historical seals could have committed secrets undetected. The Phase 56 substantiate gate prevents this forward; retroactive remediation is operator-driven (`gitleaks detect --source . --log-opts="--all"` for full-history sweep).

### Unit Tests

- `tests/test_substantiate_step_4_secret_scan_wiring.py`:
  - `test_substantiate_skill_invokes_secret_scanner_at_step_4_6_5` — co-occurrence behavior invariant per Phase 50 model. **Conditional rule**: any SKILL.md whose `phase:` frontmatter is `substantiate` MUST invoke `python -m qor.scripts.secret_scanner --staged` in its body. Conditional on actual substantiate-phase frontmatter.
  - `test_substantiate_step_4_6_5_uses_abort_semantics` — walks the substantiate SKILL.md; asserts the secret_scanner invocation is followed by `|| ABORT` (matches existing reliability-sweep idiom).
- `tests/test_substantiate_secret_scan_aborts_on_finding.py`:
  - `test_substantiate_secret_scan_blocks_seal_when_finding_present` — fixture worktree: stage a file containing `AKIAIOSFODNN7VARIANT`; subprocess-invoke `python -m qor.scripts.secret_scanner --staged`; assert non-zero exit + findings JSON on disk.
  - `test_substantiate_secret_scan_passes_seal_on_clean_staging` — fixture worktree with clean staging; subprocess-invoke; assert exit 0.
  - `test_compute_production_attributes_returns_has_hardcoded_secrets` — invokes the new helper; asserts `{"has_hardcoded_secrets": True}` for content with `AKIA...` pattern; `False` for clean content.
  - `test_compute_production_attributes_respects_allowlist` — invokes with content containing `permitted_tools = "Read, Grep, Bash, ..."` (resembles assignment but allowlisted); asserts `has_hardcoded_secrets` is False.
- `tests/test_resource_attributes_production_scope.py` (new):
  - `test_compute_production_attributes_returns_expected_shape` — invoke; asserts return dict has `{"has_hardcoded_secrets": bool}`.
  - `test_helper_handles_non_python_paths_via_content_only` — invoke with `path="something.md"` and content containing a secret; asserts the helper still detects from content (path is metadata, not a filter).

## Phase 3: Doctrine + glossary + self-application

### Affected Files

- `tests/test_doctrine_secret_scanning_anchored.py` — NEW: heading-tree round-trip integrity for the new secret-scanning doctrine section in `doctrine-eu-ai-act.md`.
- `tests/test_phase56_self_application.py` — NEW: 4 self-application tests verifying Phase 56 plan + ledger + scanner behavior end-to-end.
- `qor/references/doctrine-eu-ai-act.md` — APPEND `## Secret-scanning gate (Phase 56)` section with: applicability (substantiate-time enforcement; LLM06 + AI 600-1 §2.10 mapping), scanner pattern catalog summary, allowlist semantics, gitleaks-v8 output format, operator workflow (resolve flagged secrets → re-run substantiate).
- `qor/references/glossary.md` — APPEND 2 new terms: `secret-scanning gate` (substantiate-time wiring), `gitleaks-compatible findings` (output format).
- `qor/scripts/sprint_progress.py` — UPDATE: amend to recognize Phase 56 as the original optional-priority Phase 56 listing (Priority 4 in the brief). The brief's Priority 4 maps to `Phase 56 candidate: Path-currency cleanup` which Phase 53 absorbed; Phase 56 (this plan) is a NEW priority not in the original brief. Add a doctrine note: post-Phase-56-seal, sprint-progress reports 6/5 (one extra priority) — operator-readable indicator that the sprint expanded.

### Changes

The new doctrine section codifies what the Phase 56 wiring delivers. Heading-tree integrity test mirrors Phase 53 / 54 doctrine round-trip pattern.

Sprint-progress reconciliation handles the brief's now-stale Phase mapping (Priority 4 → Phase 56 was the original brief assignment; Phase 53 absorbed Priority 4 via path-canonicalization; this Phase 56 ships LLM06 instead). The implementation reports `5/5 + LLM06 extension` rather than `6/5`.

### Unit Tests

- `tests/test_doctrine_secret_scanning_anchored.py`:
  - `test_doctrine_eu_ai_act_declares_secret_scanning_section_with_non_empty_body` — heading-tree integrity: `## Secret-scanning gate (Phase 56)` heading present with non-empty substantive body (>=20 chars after whitespace collapse). Body must mention `LLM06`, `AI 600-1 §2.10`, and `gitleaks` literally.
  - `test_doctrine_round_trip_against_pattern_catalog` — imports `qor.scripts.secret_scanner.PATTERNS`; reads doctrine; asserts each `Pattern.name` in the catalog is mentioned in the doctrine body OR a "see PATTERNS catalog" delegation marker is present (avoids per-pattern-rename churn while keeping the doctrine grounded).
- `tests/test_phase56_self_application.py`:
  - `test_phase56_implement_gate_carries_ai_provenance` — reads `.qor/gates/<this_session>/implement.json`; asserts `ai_provenance` field present with `human_oversight: absent`.
  - `test_secret_scanner_clean_against_phase56_plan_and_doctrine` — invokes `secret_scanner.scan(path)` against this plan, the new doctrine, and the new test files; asserts empty findings list. Meta-coherence: this plan must not contain its own canary patterns even as worked examples.
  - `test_pre_audit_lints_clean_against_phase56_plan` — invokes `plan_test_lint` and `plan_grep_lint` against this plan; asserts empty (within Phase 4 documentation context allowance from Phase 55 self-application pattern).
  - `test_glossary_round_trips_against_phase56_terms` — reads `qor/references/glossary.md`; asserts both new terms (`secret-scanning gate`, `gitleaks-compatible findings`) have entries with `home: qor/references/doctrine-eu-ai-act.md` and `introduced_in_plan: phase56-secret-scanning-gate`.

## CI Commands

- `python -m pytest tests/test_secret_scanner.py tests/test_secret_scanner_findings_format.py -v` — Phase 1 lock.
- `python -m pytest tests/test_substantiate_step_4_secret_scan_wiring.py tests/test_substantiate_secret_scan_aborts_on_finding.py tests/test_resource_attributes_production_scope.py -v` — Phase 2 lock.
- `python -m pytest tests/test_doctrine_secret_scanning_anchored.py tests/test_phase56_self_application.py -v` — Phase 3 lock.
- `python -m pytest -x` — full suite; expect 1104 + ~30 new = ~1134 passing twice (deterministic).
- `python -m qor.scripts.prompt_injection_canaries --mask-code-blocks --files docs/plan-qor-phase56-secret-scanning-gate.md docs/META_LEDGER.md qor/references/doctrine-eu-ai-act.md` — Phase 53 self-application against new plan + doctrine.
- `python -m qor.scripts.plan_test_lint --plan docs/plan-qor-phase56-secret-scanning-gate.md` — Phase 55 self-application against new plan.
- `python -m qor.scripts.plan_grep_lint --plan docs/plan-qor-phase56-secret-scanning-gate.md --repo-root .` — Phase 55 self-application.
- `python -m qor.scripts.secret_scanner --files docs/plan-qor-phase56-secret-scanning-gate.md qor/references/doctrine-eu-ai-act.md qor/scripts/secret_scanner.py qor/policy/resource_attributes.py` — Phase 56 self-application (scanner against own modules + doctrine).
- `python -m qor.reliability.skill_admission qor-substantiate` — admit modified substantiate skill.
- `python -m qor.reliability.gate_skill_matrix` — handoff integrity post-edits.
- `python -m qor.scripts.check_variant_drift` — dist parity.
- `python -m qor.scripts.badge_currency --repo-root . --ledger docs/META_LEDGER.md` — Tests + Doctrines + Ledger badges current.
