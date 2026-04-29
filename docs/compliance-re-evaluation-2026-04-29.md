# Compliance Re-evaluation — 2026-04-29 (post-Phase-48)

**Scope**: NIST SP 800-218A (SSDF) alignment + OWASP Top 10 (2021) governance posture as of v0.35.0.

**Method**: static grep + test-suite run + doctrine review + Cedar policy audit + ledger-evidence inspection.

## Summary

| Framework | Result | Gaps |
|---|---|---|
| NIST SSDF (alignment) | PASS — doctrine + tests + skills present | **G-1**: zero `**SSDF Practices**:` tags in 160-entry ledger; evidence-collection contract from Phase 23 doctrine §"Evidence Collection" never operationalized in any seal |
| OWASP Top 10 (applicable) | PASS — A03/A04/A05/A08 surfaces clean; 142/142 security tests green | **G-2**: doctrine doesn't yet acknowledge Phase 48's new attack surface (`/qor-help --stuck` filesystem read of operator-controlled session_id path) |
| Attribution-trailer signal/noise | DRIFTING — canonical form already inconsistent across recent phases | **G-3**: Phase 48 commits dropped the `🤖 Authored via Qor-logic SDLC` line; Phase 47 kept it; CHANGELOG attribution line (`_Built via [Qor-logic SDLC]._`) used 0 times despite being canonical. No tiered policy distinguishes high-signal seal commits from low-signal plan/audit/implement commits, so de-facto compaction happens silently |
| README badge currency | DRIFTED — multiple phases skipped Phase 33 release-doc-currency rule | **G-4**: README badges showed `Tests: 817 passing` (was 838) and `Ledger: 157 entries sealed` (was 160) at audit time — three phases stale. Phase 33 doctrine §"release-doc currency" requires `feature` and `breaking` phases to update README.md badges. Phases 45/46/48 each shipped without the README update; only Phase 47 followed it. PyPI badge is dynamic (queries shields.io live; 3-hour CDN cache); literal-count badges drift silently |
| Cedar policy enforcement | PASS — 4 forbid rules active (A03/A04/A05/A08) | None |
| Static grep | CLEAN — no `shell=True`, no `pickle.load`, no `eval`/`exec`, no unsafe `yaml.load`, no hardcoded secrets | None |
| Subprocess invocations | CLEAN — all 11 production callsites use argv-form list arguments | None |
| Test coverage | 838 passed, 1 skipped, 4 deselected; 142 security/compliance tests green twice | None |

**Verdict**: Audit-clearance posture maintained. Two non-blocking gaps documented; both are governance-bookkeeping (NOT runtime security) and remediable in a single follow-up phase.

## NIST SSDF — practice-by-practice

### PO — Prepare the Organization

| Practice | Status | Evidence |
|---|---|---|
| PO.1.1 Define security requirements | OK | `/qor-bootstrap` skill; doctrine in repo |
| PO.1.2 Implement roles & responsibilities | OK | `qor/gates/delegation-table.md`; skill handoff matrix |
| PO.1.3 Implement supporting toolchains | OK | `CLAUDE.md` + 14 doctrine files under `qor/references/` |
| PO.1.4 Define criteria for security checks | OK | `qor/gates/chain.md` + Cedar policies |

### PS — Protect the Software

| Practice | Status | Evidence |
|---|---|---|
| PS.1.1 Protect all forms of code | OK | Shadow genome countermeasures doctrine; SG-016 through SG-038 catalogued |
| PS.2.1 Archive and protect each release | OK | Merkle seal in META_LEDGER; chain integrity verified entries #152–#160 |
| PS.3.1 Protect integrity of dev tools | OK | `qor/reliability/` — intent_lock, skill_admission, gate_skill_matrix, seal_entry_check |
| PS.3.2 Monitor development infrastructure | OK | `/qor-audit` 8-pass tribunal; Phase 47 `seal_entry_check` is the eighth structural countermeasure |

**Phase 47/48 delta**: PS.3.1 strengthened by `seal_entry_check.py` (Phase 47); PS.2.1 chain integrity holds across the 8 entries added in Phases 46–48.

### PW — Produce Well-Secured Software

| Practice | Status | Evidence |
|---|---|---|
| PW.1.1 Design software to meet security requirements | OK | `/qor-plan` Step 2b grounding protocol; `/qor-audit` Test Functionality Pass (Phase 46) |
| PW.4.1 Review and analyze human-readable code | OK | `/qor-audit` adversarial 8-pass review; Phase 46 added Test Functionality Pass between Section 4 Razor and Dependency |
| PW.5.1 Test executable code | OK | `qor/references/doctrine-test-discipline.md` Rule 1 (TDD) + Rule 2 (green tests = done); Phase 46 doctrine-test-functionality augments with the "invoke the unit" mandate |
| PW.7.1 Configure software to have secure settings | OK | Cedar policy engine (`qor/policy/`) with 4 forbid rules |
| PW.9.1 Verify third-party components | OK | `/qor-audit` Dependency Audit pass; `pyproject.toml` has zero runtime deps (vanilla Python) |

**Phase 46 delta**: PW.4.1 strengthened with the Test Functionality Pass — eliminated presence-only tests as a class.

### RV — Respond to Vulnerabilities

| Practice | Status | Evidence |
|---|---|---|
| RV.1.1 Identify and confirm vulnerabilities | OK | `/qor-debug` skill |
| RV.1.2 Assess vulnerability severity | OK | Process shadow genome severity-sum threshold automation |
| RV.2.1 Analyze vulnerabilities to determine remediation | OK | `/qor-remediate` skill |
| RV.3.1 Communicate vulnerability information | OK | `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md` |

### Gap G-1: SSDF practice tags missing from ledger

**Finding**: Doctrine `qor/references/doctrine-nist-ssdf-alignment.md` §"Evidence Collection" (Phase 23 contract) declares every `/qor-substantiate` seal MUST add `**SSDF Practices**: PW.1.1, PS.1.1` tags. Current ledger: 160 entries, zero tags.

```
$ python -m qor.cli compliance report
No SSDF practice tags found in ledger. Coverage: 0
```

**Impact**: The alignment mapping in the doctrine remains as written prose, but the verifiable evidence contract is unfulfilled. An external NIST auditor reviewing this repo would see the framework alignment claim without the per-decision tag evidence.

**Severity**: doctrine-bookkeeping gap (NOT a runtime security gap). The phases themselves DO address SSDF practices — the gap is purely the tag-on-each-entry contract.

**Remediation**: a follow-up phase should:
1. Backfill SSDF tags on entries #100–#160 (most recent ~60 sealed entries; older entries grandfathered).
2. Add a `/qor-substantiate` step that emits the SSDF tag block as part of the seal entry, with a checklist mapping the phase's change_class and surfaces touched to the relevant practices.
3. Doctrine test asserting every post-tag-cutoff seal entry contains `**SSDF Practices**:`.

Estimated effort: 1 phase, change_class=feature.

## OWASP Top 10 — applicable categories

### A03 Injection

| Check | Result |
|---|---|
| `shell=True` in production code | NONE (grep: 0 hits across `qor/`) |
| Bare `subprocess.run` shell-form | NONE (all 11 production callsites use argv-form list arguments) |
| User-controlled input in path construction | All session_id and event_id values are regex-validated before use (LOW-2/LOW-3 fixes; `test_security_fixes.py` confirms) |
| `gh` CLI invocations | argv-form: `["gh", "issue", "create", ...]` and `["gh", "auth", "status"]` |
| Cedar policy `forbid has_shell_true` | Active in `owasp_enforcement.cedar` |

**Verdict**: PASS.

### A04 Insecure Design

| Check | Result |
|---|---|
| Bare `except: pass` (silent error swallowing) | NONE (grep: 0 hits; all `except` clauses catch specific exception types and log/raise) |
| Fail-open error handlers | NONE — Phase 23 MEDIUM-2 fix made `read_events()` log to stderr per skipped line |
| Cedar policy `forbid has_fail_open_error` | Active |
| `/qor-audit` OWASP pass step | Wired (line 130-141 of `qor-audit/SKILL.md`) |

**Verdict**: PASS.

### A05 Security Misconfiguration

| Check | Result |
|---|---|
| Hardcoded secrets/tokens/passwords | NONE (regex `(password\|secret\|token\|api_key)\s*=\s*['"][a-zA-Z0-9]{16,}` returns 0 hits) |
| Validated config paths used as subprocess `cwd` | YES — Phase 23 MEDIUM-1 fix; `collect_shadow_genomes.py` validates repo path before use |
| Cedar policy `forbid has_hardcoded_secrets` | Active |

**Verdict**: PASS.

### A08 Software/Data Integrity

| Check | Result |
|---|---|
| `pickle.load` / `eval` / `exec` | NONE in production code |
| `yaml.load` without `SafeLoader` | NONE — `tests/test_yaml_safe_load_discipline.py` widened scope catches planted call test PASSES |
| Chain hash uses unambiguous separator | YES — `chain_hash = SHA256(content + "|" + prev)` per Phase 23 LOW-1 |
| Legacy chain hash format | `legacy_chain_hash` preserved for backward verification |
| Cedar policy `forbid has_unsafe_deserialization` | Active |

**Verdict**: PASS.

### Non-applicable categories

A01/A02/A06/A07/A09/A10 remain non-applicable per `qor/references/doctrine-owasp-governance.md` §"Non-Applicable Categories". Qor-logic is a prompt-logic library, not a web application; no auth surface, no encrypted storage, no inbound HTTP, no session management, no SSRF surface.

### Gap G-2: Phase 48 attack surface not yet doctrine-acknowledged

**Finding**: `/qor-help --stuck` mode (Phase 48) globs `.qor/gates/<session_id>/*.json` where `session_id` is read from `.qor/session/current`. Threat model:

- Attacker scenario: malicious actor with write access to operator's working directory replaces `.qor/session/current` content with `../../../etc/passwd` or similar.
- Mitigation already in place: `tests/test_security_fixes.py::test_low2_invalid_session_id_rejected` validates session_id against regex `[a-zA-Z0-9_-]+` BEFORE use in path construction. The validation is in `qor/scripts/session.py`.
- However: the `/qor-help --stuck` skill prose does not explicitly mandate session_id validation before the glob. The LLM running the skill SHOULD use the validated session helper, but this is doctrinal, not enforced.

**Impact**: Threat-model-equivalent to existing skill prose patterns; not a NEW vulnerability, but the doctrine `qor/references/doctrine-owasp-governance.md` §A03 should add a worked example covering markdown-skill filesystem reads.

**Severity**: doctrine-currency gap (NOT a runtime exploit — operators are inside the trust boundary, and the regex validation already exists in the helper layer).

**Remediation**: a follow-up phase should:
1. Update `/qor-help` skill prose to explicitly cite `session.validate_session_id()` (or equivalent) before the glob.
2. Add a worked example to `doctrine-owasp-governance.md` §A03: "Skill prose that performs filesystem operations with operator-controlled identifiers must validate the identifier via the canonical helper."
3. Lint test asserting any skill body that mentions `.qor/gates/<` also cites a validation helper.

Estimated effort: 1 small phase, change_class=feature, ~5 file edits + 1 new test.

## Cedar policy posture

```
$ python -m pytest tests/test_policy.py tests/test_owasp_governance.py
20 passed in 0.4s
```

4 forbid rules active in `qor/policies/owasp_enforcement.cedar` (A03/A04/A05/A08). All evaluate correctly per `tests/test_policy.py` (12 tests) and integrate with `/qor-audit` per `tests/test_owasp_governance.py` (8 tests).

## Test posture

```
838 passed, 1 skipped, 4 deselected — twice in a row (determinism)
142 security/compliance tests green
46 NIST/OWASP/policy/security tests green
```

No deselected test pertains to security/compliance.

### Gap G-3: attribution-trailer signal/noise

**Finding**: Phase 45 shipped the canonical attribution surface (`qor/scripts/attribution.py` + `ATTRIBUTION.md` + `qor/references/doctrine-attribution.md`). The canonical commit-trailer form is two lines + leading emoji:

```
🤖 Authored via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic) on [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

Measured against last 10 commits on main:

| Phase | Commits with full form | Commits with `Co-Authored-By` only | Notes |
|---|---|---|---|
| 47 | 2/2 (seal + docs polish) | — | doctrine-compliant |
| 48 | 0/4 | 4/4 (plan/audit/implement/seal) | drifted to compact form |

CHANGELOG attribution line (`_Built via [Qor-logic SDLC](url)._`) declared canonical in `ATTRIBUTION.md`; **used in zero CHANGELOG version sections**. PR-body footer canonical form (~10 lines including the audit-findings template) was used in the Phase 48 PR body but is unenforced — no test asserts PR bodies match.

**Impact**: Two failure modes risk if no policy lands:

1. **Tedious noise**: applying the full canonical trailer to every plan/audit/implement/seal commit means each phase commits 4 × 3 = 12 lines of repeated boilerplate. Operators ignore boilerplate; signal degrades. CHANGELOG entries get the per-entry attribution line if doctrine is enforced literally → narrative buried under template repetition.
2. **Silent compaction**: operators (or automation) drop lines without notice — exactly what happened across Phase 48. The doctrine's drift-guard tests (`test_attribution_docs_consistency.py`) lock the *canonical strings* but don't lock *which surfaces are required to use which form*.

**Severity**: governance-bookkeeping AND operator-UX. Not a security gap; a doctrine-currency gap that risks turning attribution into ignored noise.

**Remediation**: a follow-up phase should add a tiered usage policy to `qor/references/doctrine-attribution.md`:

| Surface | Required form | Rationale |
|---|---|---|
| **Seal commit** (`seal: phase NN ...`) | Full canonical (emoji + Qor-logic line + Co-Authored-By) | One per phase — high signal, marks the substantiated artifact |
| **Plan/audit/implement commits** | `Co-Authored-By:` only (single line) | Low signal-per-commit; the SDLC bilineage is established by the seal commit they chain into |
| **Merge commit** (auto-generated by GitHub) | Untouched | Outside the operator's authoring surface |
| **PR description footer** | Full canonical PR-body footer | One per phase — visible to reviewers, is the contextually-rich surface |
| **CHANGELOG entry** | Once per version section, immediately under the `## [X.Y.Z] - DATE` header | Reader scans CHANGELOG version-by-version, not entry-by-entry |
| **GitHub release notes** | Once per release | Same rationale |

Add an enforcement test: `tests/test_attribution_tiered_usage.py` walking recent commits and CHANGELOG sections, asserting the right tier is used at each surface. Strip-and-fail negative-path per Phase 46 doctrine.

Estimated effort: 1 small phase, change_class=feature, ~3 file edits + 1 new test + 1 doctrine update.

### Gap G-4: README badge currency — three phases stale

**Finding**: at audit time, README.md badges showed:

| Badge | Declared | Actual | Last correct phase |
|---|---|---|---|
| Tests | 817 passing | 838 passing | Phase 47 |
| Ledger | 157 entries sealed | 160 entries sealed | Phase 47 |
| Doctrines | 17 | 17 (correct) | — |
| Skills | 29 | 29 (correct) | — |
| Agents | 13 | 13 (correct) | — |
| PyPI | dynamic (shields.io→PyPI) | 0.35.0 live (3hr CDN cache) | dynamic |

Phases 45/46/48 each shipped as `change_class: feature`, which per Phase 33 doctrine §"release-doc currency" REQUIRES `README.md` and `CHANGELOG.md` to appear in `implement.files_touched`. Each phase updated CHANGELOG but skipped the README badge counts. Phase 47 followed the rule; Phases 45/46/48 did not.

**Impact**: external visitors land on the README and see numbers from three phases ago. Trust signal degrades; basic discipline questioned. The PyPI badge isn't broken (it's dynamic and CDN-cached), but the literal-count badges silently rot.

**Severity**: governance-bookkeeping AND public-facing trust signal. The Phase 33 doctrine is in place; enforcement is not.

**One-shot patch applied during this audit**: `Tests: 817 → 838`, `Ledger: 157 → 160` corrected in this commit cycle alongside this compliance report.

**Remediation** (durable fix, candidate Phase 52): make the test `tests/test_release_doc_currency.py` (which asserts CHANGELOG was touched on feature/breaking phases) symmetric — also assert README.md appears in `implement.files_touched`. Currently the test covers CHANGELOG but not README per `qor/scripts/doc_integrity_strict.py::check_documentation_currency`; verify and tighten if needed. Plus a static check at `/qor-substantiate` Step 6.5 that parses README badges and compares the literal counts against truth (test count via `pytest --collect-only`, ledger via `grep -c '^### Entry'`, etc.) — fails seal on mismatch.

Estimated effort: ~half-day. Could combine with Phase 49 G-3 fix in a single docs-currency phase.

## Recommended next actions

In priority order (lowest-effort highest-value first):

1. **Phase 49 candidate** (closes G-3 + G-4 together, ~1 day): docs-currency phase covering both attribution-trailer tiering AND README-badge enforcement. Both gaps share the same root cause — release-doc-currency contracts that aren't mechanically enforced — and remediating them in one phase produces one consistent test surface.
2. **Phase 50 candidate** (closes G-2, ~half-day): skill-prose filesystem-operation validation rule + lint test.
3. **Phase 51 candidate** (closes G-1, ~1 day): backfill SSDF tags on most recent ~60 ledger entries + add `/qor-substantiate` step that emits tags on every seal + doctrine test. Larger-effort but closes the only documentation-evidence gap an external auditor would request.
4. **Optional**: external compliance-auditor walkthrough using this report as the evidence package. The repo is in a clearable state across all three frameworks; the gaps above are governance-currency, not runtime-security.

## Evidence files

- This report: `docs/compliance-re-evaluation-2026-04-29.md`
- NIST doctrine: `qor/references/doctrine-nist-ssdf-alignment.md`
- OWASP doctrine: `qor/references/doctrine-owasp-governance.md`
- Cedar policies: `qor/policies/{owasp_enforcement,gate_enforcement,skill_admission}.cedar`
- Test suite: `tests/test_{nist_compliance,nist_ssdf,owasp_governance,policy,security_fixes,yaml_safe_load_discipline,release_workflow_guard}.py`
- Original Phase 23 baseline: `docs/security-audit-2026-04-16.md`

---

*Snapshot timestamp: 2026-04-29*
*Repo HEAD: post-Phase-48 merge (`12bdafa`)*
*Latest tag: v0.35.0 (PyPI: 0.35.0 published 2026-04-29T20:22:35Z)*
