# FEATURE_INDEX (consumer-contract fixture: malformed)

Consumer-contract fixture (GH #358): "malformed" state. Row FX910 declares
status `n/a` but this file's "n/a rationales" section (below) has no entry
for it. qor.gates.schema.feature_index.schema.json requires `n_a_rationale`
whenever `status` is `n/a`; building the schema-shaped envelope for FX910
from this row fails validation.

| ID | Name | Source-of-truth file:line | Doc citation | Test path | Surface | Verification status |
|---|---|---|---|---|---|---|
| FX910 | Undocumented n/a row | src/example/orphan.py:5 | - | - |  | n/a |

## n/a rationales

_(intentionally empty -- FX910 has no rationale entry; this is the defect)_

## Last seal tally

`Total: 1 / verified: 0 / unverified: 0 / n/a: 1` (fixture only).
