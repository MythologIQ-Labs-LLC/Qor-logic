# FEATURE_INDEX (worked example)

Tracked governance artifact enumerating every user-touchable feature. Updated by `/qor-implement` Step 12.5; tallied by `/qor-substantiate` Step 6. Format and discipline per `qor/references/doctrine-feature-inventory.md`.

| ID | Name | Source-of-truth file:line | Doc citation | Test path | Surface | Verification status |
|---|---|---|---|---|---|---|
| FX001 | Marketplace install endpoint | src/marketplace/route.py:42 | docs/marketplace.md | tests/test_marketplace_route.py | route | verified |
| FX002 | Marketplace install confirmation | src/marketplace/route.py:78 | docs/marketplace.md | — | route | unverified |
| FX003 | Settings card: voice substrate | src/settings/voice_card.tsx:15 | docs/settings.md#voice | tests/test_voice_card_presence.spec.ts | settings-card | unverified |
| FX004 | Operator-judgment surface: brainstorm UI | src/brainstorm/index.tsx | docs/brainstorm.md | — |  | n/a |
| FX005 | RiskManager updateRisk | src/risk/manager.ts:104 | docs/risk.md | tests/test_risk_manager.spec.ts | command | verified |

## n/a rationales

- **FX004**: brainstorm UI is a human-judgment surface (creative mindmapping). Automated tests cannot validate "did the user get inspired"; manual QA checklist lives at `docs/qa/brainstorm-checklist.md`.

## Status legend

- `verified`: test at cited path exists, exercises the feature (not presence-only), currently passes.
- `unverified`: no test, OR test is presence-only (fails SG-035 acceptance question), OR test currently fails.
- `n/a`: intentionally untested with rationale above.

## Last seal tally

`Total: 5 / verified: 2 / unverified: 2 / n/a: 1` (example only; live tally is computed at `/qor-substantiate` Step 6 via `feature_index_verify.tally()`).
