# Reference: qor-meta-log-decision invocation examples (Phase 98, F5+F6)

Three concrete examples of `/qor-meta-log-decision` invocations
covering the L2 and L3 risk-grade authority paths. Moved out of
`SKILL.md` per the progressive-disclosure doctrine
(`SG-SkillCorpusGrowth-A`) so the skill body stays lean while the
example detail remains available for operators who need it.

## Example 1: Architecture Decision (L2)

**Command:**
```
/qor-meta-log-decision ARCHITECTURE "Use SQLite for Phases 1-2" "KISS - no proven bottleneck" L2
```

**Output:**
```markdown
✅ Meta-Ledger Updated: Entry #5

**Decision Type:** ARCHITECTURE (L2)
**Decision:** Use SQLite for Phases 1-2
**Approver:** Lead Reviewer
**Status:** APPROVED (L2 - Lead Reviewer authority)

**Hash Chain:** ✅ Integrity verified
**File Updated:** docs/META_LEDGER.md

**Next Steps:**
- Implementation can proceed
- No user approval required (L2)
```

## Example 2: Security Decision (L3)

**Command:**
```
/qor-meta-log-decision SECURITY "Migrate passphrase to platform keystore" "Fix CRITICAL vulnerability" L3
```

**Output:**
```markdown
⚠️ Meta-Ledger Updated: Entry #6 (PENDING APPROVAL)

**Decision Type:** SECURITY (L3 CRITICAL)
**Decision:** Migrate passphrase storage to platform keystore
**Impact:** Fixes CRITICAL security vulnerability (plaintext master passphrase)

**Status:** CONDITIONAL - Awaiting user approval
**Approval Required By:** 2025-12-25 16:00:00 UTC (24 hours)

**Rationale:**
Current plaintext storage at ~/.qor/security/identity.secret creates single point of compromise. Platform keystore (Windows Credential Manager, macOS Keychain, Linux Secret Service) provides OS-level encryption and access control.

**Trade-offs:**
- **Accepting:** Platform dependency, different implementation per OS
- **Gaining:** Hardware-backed encryption, audit trail, no plaintext secrets

**Reversibility:** Low - migration one-way, manual keystore deletion needed to rollback

**User Action Required:**
Please review and respond with:
- "APPROVED: Entry #6" to proceed with implementation
- "CONDITIONAL: Entry #6 - {concerns}" to request changes
- "REJECTED: Entry #6 - {rationale}" to block implementation

**File Updated:** docs/META_LEDGER.md (entry marked CONDITIONAL)
```

## Example 3: Scope Change (L2)

**Command:**
```
/qor-meta-log-decision SCOPE_CHANGE "Defer PyVeritas to Phase 3" "Focus on validated features first" L2
```

**Output:**
```markdown
✅ Meta-Ledger Updated: Entry #7

**Decision Type:** SCOPE_CHANGE (L2)
**Decision:** Defer PyVeritas implementation to Phase 3 (Week 9+)
**Approver:** Lead Reviewer
**Status:** APPROVED

**Rationale:**
PyVeritas is aspirational (80% accuracy per research, not validated). Focus Phases 1-2 on working features (CBMC wrapper, Z3 integration) with proven ROI. Re-evaluate PyVeritas after baseline comparison in Week 5.

**Impact:**
- Phase 1-2: Tier 3 verification uses CBMC + Z3 (proven tools)
- Phase 3: Evaluate PyVeritas based on validation data
- Documentation: Update to reflect current vs. planned status

**Timeline Impact:** None - removes unproven work from critical path

**Hash Chain:** ✅ Integrity verified
**File Updated:** docs/META_LEDGER.md
```

## Cross-references

- `qor/skills/meta/qor-meta-log-decision/SKILL.md` — the parent skill body.
- `qor/references/doctrine-shadow-genome-countermeasures.md` `SG-SkillCorpusGrowth-A` — the progressive-disclosure doctrine that drove this move.
- `docs/plan-qor-phase98-meta-skill-examples-to-references.md` — the sealed Phase 98 plan.
