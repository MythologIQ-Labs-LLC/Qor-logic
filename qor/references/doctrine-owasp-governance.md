# Doctrine: OWASP Top 10 Governance Integration

Maps applicable OWASP Top 10 (2021) categories to Qor-logic governance decisions. Each category includes the governance check, the enforcement mechanism, and a worked example from the Phase 23 security audit.

## Applicable Categories

### A03 -- Injection

**Governance check**: All subprocess calls use list-form argv; no `shell=True`; user-supplied values validated before use in path construction or command arguments.

**Enforcement**: Cedar policy `owasp_enforcement.cedar` forbids `has_shell_true`. Static grep test in `test_owasp_governance.py`.

**Worked example**: LOW-2 (session_id) and LOW-3 (event_id) -- unvalidated strings used in path construction and `gh` argv. Fixed by adding regex validation before use.

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
