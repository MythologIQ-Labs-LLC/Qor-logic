# Doctrine: OWASP Top 10 Governance Integration

Maps applicable OWASP Top 10 (2021) categories to Qor-logic governance decisions. Each category includes the governance check, the enforcement mechanism, and a worked example from the Phase 23 security audit.

## Applicable Categories

### A03 -- Injection

**Governance check**: All subprocess calls use list-form argv; no `shell=True`; user-supplied values validated before use in path construction or command arguments.

**Enforcement**: Cedar policy `owasp_enforcement.cedar` forbids `has_shell_true`. Static grep test in `test_owasp_governance.py`.

**Worked example**: LOW-2 (session_id) and LOW-3 (event_id) -- unvalidated strings used in path construction and `gh` argv. Fixed by adding regex validation before use.

**Skill-prose worked example (Phase 50)**: `/qor-help --stuck` reads `.qor/gates/<session_id>/*.json` where `session_id` is the operator-controlled marker file `.qor/session/current`. The runtime validator `qor.scripts.session.SESSION_ID_PATTERN` exists (Phase 23 LOW-2 fix) but is enforced only when `qor.scripts.session.current()` is invoked. Skill prose that bypasses the helper and reads the marker directly fails open on corrupted markers — operator-controlled paths reach `glob()` without sanitization. **Mitigation**: skill prose MUST cite `qor.scripts.session.current()` (or the equivalent canonical helper) before any filesystem operation on operator-controlled identifiers. The runtime validator alone is insufficient; the skill prose layer must route the LLM through the helper. Locked by `tests/test_skill_prose_filesystem_validation.py::test_skills_referencing_qor_gates_cite_session_validator`.

### A04 -- Insecure Design

**Governance check**: No fail-open on error; no silent drops of security events. All error paths must log or raise, never silently continue.

**Enforcement**: `/qor-audit` OWASP pass checks for bare `except: pass` and silent `continue` in error handlers.

**Worked example**: MEDIUM-2 -- `read_events()` silently dropped malformed JSONL lines. Fixed by emitting `WARN` to stderr per skipped line.

### A05 -- Security Misconfiguration

**Governance check**: No hardcoded secrets; temp files use secure permissions; config paths validated before use as working directories.

**Enforcement**: Cedar policy forbids `has_hardcoded_secrets`. Static grep for common secret patterns.

**Worked example**: MEDIUM-1 -- `collect_shadow_genomes.py` used repo path from config as subprocess `cwd` without validating it contained expected directory markers. Fixed by checking for `qor/` or `docs/` directory.

### A08 -- Software and Data Integrity Failures

**Governance check**: No unsafe deserialization (`pickle.load`, `eval`, `exec`, `yaml.load` without `SafeLoader`). Cryptographic chain hashes use unambiguous separators to prevent length-extension confusion.

**Enforcement**: Cedar policy forbids `has_unsafe_deserialization`. Static grep test. Chain hash uses `|` separator (LOW-1).

**Worked example**: LOW-1 -- `chain_hash()` concatenated content + prev without separator, making `SHA256("ab" + "cd")` indistinguishable from `SHA256("a" + "bcd")`. Fixed by inserting `|` separator; legacy format preserved for backward-compatible verification.

## Non-Applicable Categories

The following OWASP categories are not directly applicable to Qor-logic (a prompt-logic library, not a web application):

- A01 Broken Access Control -- no user-facing access control
- A02 Cryptographic Failures -- hashes are integrity checks, not encryption
- A06 Vulnerable Components -- addressed by dependency audit pass
- A07 Auth Failures -- no authentication system
- A09 Security Logging -- addressed by shadow genome
- A10 SSRF -- no outbound HTTP from library code

## References

- `docs/security-audit-2026-04-16.md` -- baseline findings
- `qor/policies/owasp_enforcement.cedar` -- Cedar enforcement rules
- `qor/references/doctrine-shadow-genome-countermeasures.md` -- SG patterns
- `qor/skills/governance/qor-audit/SKILL.md` -- OWASP Top 10 Pass
