# QoreLogic Meta Ledger
<!-- qor:meta-ledger-schema=1 -->

Consumer-contract fixture (GH #358): "malformed" state. This file carries
real AUDIT/SEAL content -- it is not empty -- but every entry heading below
has been corrupted (missing the `#N:` numbering the parser requires), so
meta_ledger_walker.walk() returns zero records against it. A consumer that
treats "zero records" as "no governance to report" would silently misreport
this ledger as clean. The correct behavior is to notice real content is
present and flag the read as untrusted/malformed rather than empty.

---

## Entry AUDIT (heading corrupted -- no "### Entry #N:" prefix)

**Timestamp**: 2026-08-01T10:00:00Z
**Phase**: GATE
**Type**: AUDIT
**Target**: `docs/plan-corrupted-heading.md`
**Verdict**: VETO
**Findings categories**: razor-overage

**Decision**: This entry has real governance content but an unparseable heading.

---

## Entry SEAL (heading corrupted -- no "### Entry #N:" prefix)

**Timestamp**: 2026-08-01T12:00:00Z
**Phase**: SUBSTANTIATE
**Type**: SEAL
**Target**: `docs/plan-corrupted-heading.md`
**Verdict**: PASS

**Decision**: Also unparseable; the heading regex never matches either block.

---
