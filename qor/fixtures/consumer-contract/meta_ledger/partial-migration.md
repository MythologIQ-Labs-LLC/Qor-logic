# QoreLogic Meta Ledger

Consumer-contract fixture (GH #358): "partial-migration" state. No
`<!-- qor:meta-ledger-schema=N -->` marker is present anywhere in this
file, so qor.scripts.ledger_upgrade.schema_version() reads it as 0
(legacy, pre-Phase-179 form) even though the ledger still holds genuinely
parseable prior entries. This is the real mid-migration shape: a
repository that has not yet run `ledger_upgrade.upgrade()`.

---

### Entry #1: GENESIS

**Timestamp**: 2026-03-01T09:00:00Z
**Phase**: BOOTSTRAP
**Type**: GENESIS
**Author**: Governor
**Iteration**: 0

**Decision**: Project DNA initialized under the pre-Phase-179 (unversioned) ledger form.

---

### Entry #2: AUDIT

**Timestamp**: 2026-03-02T11:00:00Z
**Phase**: GATE
**Type**: AUDIT
**Target**: `docs/plan-pre-migration-feature.md`
**Verdict**: PASS
**Findings signature**: LEGACY
**Author**: Judge
**Iteration**: 1

**Decision**: Cleared the gate before the schema-version marker existed.

---
