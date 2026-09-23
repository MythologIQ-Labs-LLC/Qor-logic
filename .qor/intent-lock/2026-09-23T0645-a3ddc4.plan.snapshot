# Plan: Recompose GH #477 dialect accessor fix on current main

**change_class**: hotfix

**doc_tier**: standard

**Origin**: GH #477 and historical PR #493.

**Current base**: `d37c192c91d6bee95c7fccb14896eb4554b10469` after PR #492 landed.

## Problem Contract

`qor/scripts/reconcile.py` consumes hash patterns owned by `qor.scripts.ledger_dialect`, but two call sites still interpret the owner's private capture-group layout directly as `group(1) or group(2)`. The dialect recognizes a third bare-line 64-hex form through `ledger_dialect.hash_value(match)`. A valid third-form `Previous Hash` can therefore collapse into a `None` bucket during residual detection, and a valid third-form `Chain Hash` can be treated as absent during backward chain recovery.

Historical PR #493 implemented and tested this correction against an earlier base. PR #492 has since landed and changed release/version/seal state, making #493 non-mergeable. The implementation itself remains valuable, but its historical version, ledger, seal, generated-distribution, and currentness claims must not be replayed onto a different base.

## Change Contract

### Authorized scope

- Import `ledger_dialect` in `qor/scripts/reconcile.py`.
- Replace the two direct capture-group reads with `ledger_dialect.hash_value(match)`.
- Add behavioral regression tests proving:
  - a bare-line `Previous Hash` groups with the equivalent backticked value;
  - a bare-line `Chain Hash` is recovered by `_last_chain_hash`.

### Explicit exclusions

- No version bump in this recomposition slice before current-base audit/substantiation.
- No historical ledger, seal, gate-artifact, intent-lock, README badge, SYSTEM_STATE, or generated manifest replay from PR #493.
- No narrowing of accepted ledger dialects.
- No Qortara Logic migration.
- No unrelated reconciliation refactor.

## Locked Decisions

### LD-1: The dialect owner remains the sole interpreter of capture-group layout

Callers may use the exported regexes, but they must obtain the matched value through `ledger_dialect.hash_value(match)`. The capture-group positions remain an implementation detail of the owner.

### LD-2: Preserve every currently accepted dialect form

This is a consumer correction, not a parser contraction. Existing backticked and equals-prefixed forms remain unchanged while the already-supported bare-line form becomes correctly readable by reconciliation.

### LD-3: Historical PR #493 evidence is provenance, not current promotion authority

The prior PASS, tests, seal, and review remain truthful for the revision they covered. They do not establish current fitness after `main` advanced. This branch therefore carries the semantic implementation and tests only, with fresh CI and formal `/qor-audit` required before promotion.

## Affected Files

- `qor/scripts/reconcile.py`
- `tests/test_reconcile.py`

## Definition of Done

- D1: `detect_residual` reads a third-form `Previous Hash` through `ledger_dialect.hash_value` and groups it with an equivalent backticked value.
- D2: `_recorded_chain_hash` reads a third-form `Chain Hash` through `ledger_dialect.hash_value`.
- D3: The two GH #477 regression tests are behavioral and green.
- D4: Existing reconciliation tests remain green.
- D5: Full repository CI is green on the exact current branch head.
- D6: Formal `/qor-audit` evaluates this current-base plan before promotion.

## Feature Inventory Touches

Empty. This fixes internal ledger reconciliation semantics and its tests only.

## CI Commands

- `python -m pytest tests/test_reconcile.py -q`
- `python -m pytest tests/ -q`
- `ruff check qor/scripts/reconcile.py tests/test_reconcile.py`
- `python -m qor.scripts.check_variant_drift`
- `python -m qor.scripts.publication_boundary_lint`

## Promotion Rule

Do not merge from historical PR #493 evidence. Merge only after this current-main recomposition has exact-head CI and the required current-base governance evidence.