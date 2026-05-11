# Doctrine: Per-feature TDD-Light

This doctrine extends `doctrine-test-discipline.md` (per-unit TDD-Light) with a second layer: per-feature TDD-Light. Both layers coexist.

## Per-unit vs per-feature

**Per-unit TDD-Light** (existing, governed by `doctrine-test-discipline.md` and enforced at `/qor-implement` Step 5): one minimal failing test before implementing a helper, function, or unit. The test invokes the unit under test (function call, CLI subprocess, helper render, parser pass) and asserts against its output.

**Per-feature TDD-Light** (this doctrine, enforced at `/qor-implement` Step 5 alongside the per-unit layer): for every entry in the plan's `feature_inventory_touches`, author the failing feature-level test FIRST at the path declared in the plan, with the assertion declared in the plan. Run it red. Implement. Run it green.

Per-unit covers helpers introduced inside the feature. Per-feature covers the user-touchable surface (routes, commands, UI events, services). Both must be red before code is written.

## The two layers in one implementation

Worked sketch (a developer adding `POST /api/marketplace/install/<id>`):

1. Plan declares `feature_inventory_touches`:
   ```yaml
   - entry_id: FX091
     operation: NEW
     test_path: tests/test_marketplace_route.py
     test_descriptor: POST /api/marketplace/install/<id> returns 200 with nonce structure
   ```
2. `/qor-audit` Feature Test Coverage Pass verifies the descriptor survives the SG-035 acceptance question. PASS or VETO.
3. `/qor-implement` Step 5:
   - **Per-feature** (this doctrine): author `tests/test_marketplace_route.py` with the route-level test. Run it. RED.
   - **Per-unit** (existing): author `tests/test_marketplace_installer.py` with a helper-level test for `MarketplaceInstaller.install()`. Run it. RED.
   - Implement `MarketplaceInstaller.install()`. Per-unit test goes GREEN. Per-feature test still RED.
   - Wire route handler. Per-feature test goes GREEN.
4. `/qor-implement` Step 12.5: FEATURE_INDEX gains FX091 row with status `verified`, test_path `tests/test_marketplace_route.py`.

## SG-035 acceptance question (extended)

> If the feature were silently broken but the test artifact still existed, would this assertion fail?

The per-unit layer originally applied this to function/helper-level tests. The per-feature layer applies the same scrutiny to feature-level tests. Tests that only assert presence (file exists; function defined; string substring present) cannot answer "yes" to this question. Per the per-feature layer:

- "POST /api/marketplace/install/<id> returns 200 with nonce structure" — passes (asserts behavior).
- "marketplace install route exists" — fails (asserts presence only).

`/qor-audit` Feature Test Coverage Pass routes failures to category `feature-test-undeclared`.

## Why this is upstream of the seal-time regression gate

`doctrine-feature-inventory.md` defines a substantiate-time gate that catches features regressing from `verified` to `unverified` since the prior seal. That gate protects *baseline* coverage from rot. Per-feature TDD-Light protects *new* coverage from never existing in the first place: a feature cannot enter the build path without a feature-level test that was red before the code was written.

A repo that adopts only the substantiate-time gate still allows new untested features to ship in the current phase (caught at the next seal, but the rework cost is already paid). A repo that adopts only per-feature TDD-Light still allows old features to silently rot. Both gates close both directions.

Source incidents: GH #40 (seal-time gate) and GH #41 (this doctrine; declared upstream of #40 by its filer).
