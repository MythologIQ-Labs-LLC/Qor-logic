# QoreLogic Meta Ledger
<!-- qor:meta-ledger-schema=2 -->

Consumer-contract fixture (GH #358): "unsupported-version" state. The
schema marker declares version 2, one ahead of this repository's current
qor.scripts.ledger_upgrade.SCHEMA_VERSION (1). No released Qor-logic
version defines what a schema-2 ledger looks like yet; a consumer must
fail visibly rather than guess at forward compatibility.

---

### Entry #1: GENESIS

**Timestamp**: 2026-08-10T09:00:00Z
**Phase**: BOOTSTRAP
**Type**: GENESIS
**Author**: Governor
**Iteration**: 0

**Decision**: Hypothetical future-schema ledger for consumer version-floor testing.

---
