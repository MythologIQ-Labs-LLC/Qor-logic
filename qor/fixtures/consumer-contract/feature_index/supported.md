# FEATURE_INDEX (consumer-contract fixture: supported)

Consumer-contract fixture (GH #358): "supported" state. Every row below is
schema-valid: verified rows cite a real test path, the n/a row carries a
rationale, and the Surface column is fully populated.

| ID | Name | Source-of-truth file:line | Doc citation | Test path | Surface | Verification status |
|---|---|---|---|---|---|---|
| FX901 | Example route handler | src/example/route.py:10 | docs/example.md | tests/test_example_route.py | route | verified |
| FX902 | Example settings card | src/example/card.tsx:20 | docs/example.md#card | tests/test_example_card.spec.ts | settings-card | verified |
| FX903 | Example creative surface | src/example/canvas.tsx | docs/example.md#canvas | - |  | n/a |

## n/a rationales

- **FX903**: creative canvas surface is a human-judgment surface; automated tests cannot validate subjective creative output.

## Last seal tally

`Total: 3 / verified: 2 / unverified: 0 / n/a: 1` (fixture only).
