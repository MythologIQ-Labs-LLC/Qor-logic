# QoreLogic Meta Ledger
<!-- qor:meta-ledger-schema=1 -->

Consumer-contract fixture (GH #358): "stale" state. Current schema marker,
well-formed entries, but the latest entry timestamp predates this
manifest's stated as_of (2026-08-21T00:00:00Z) by roughly a year -- a
consumer should surface this as stale rather than treat it as fresh
evidence.

---

### Entry #1: GENESIS

**Timestamp**: 2025-06-01T09:00:00Z
**Phase**: BOOTSTRAP
**Type**: GENESIS
**Author**: Governor
**Iteration**: 0

**Decision**: Project DNA initialized.

---

### Entry #2: SEAL

**Timestamp**: 2025-07-14T16:00:00Z
**Phase**: SUBSTANTIATE
**Type**: SEAL
**Target**: `docs/plan-legacy-feature.md`
**Verdict**: PASS
**Author**: Governor
**Iteration**: 1

**Decision**: Substantiated once; no ledger activity since.

---
