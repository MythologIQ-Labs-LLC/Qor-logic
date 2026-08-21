# FEATURE_INDEX (consumer-contract fixture: partial-migration)

Consumer-contract fixture (GH #358): "partial-migration" state. The header
declares the Surface column (Phase 138 / GH #196 convention), but only
some rows have actually been migrated to carry a Surface tag. FX920 is
migrated (tagged); FX921 predates the migration and its Surface cell is
still empty. This is exactly the state
qor.scripts.feature_index_verify.surface_lint()'s `untagged` list already
detects and reports as a WARN-only finding.

| ID | Name | Source-of-truth file:line | Doc citation | Test path | Surface | Verification status |
|---|---|---|---|---|---|---|
| FX920 | Migrated route (Surface tagged) | src/example/migrated.py:8 | docs/example.md | tests/test_migrated.py | route | verified |
| FX921 | Legacy route (pre-migration, untagged) | src/example/legacy.py:12 | docs/example.md | tests/test_legacy.py |  | verified |

## Last seal tally

`Total: 2 / verified: 2 / unverified: 0 / n/a: 0` (fixture only).
