# Capability: spec-corpus

### Requirement: Corpus is current truth
The spec corpus SHALL reflect every sealed behavior change for its capabilities.

#### Scenario: Sealed change with a declared delta
- GIVEN a sealed session whose plan declared a spec delta
- WHEN the seal ceremony completes
- THEN the capability spec contains the folded requirements and the delta file is gone

### Requirement: Deltas fold only after PASS
The seal ceremony SHALL fold declared deltas only inside substantiate after the reliability gates clear.

#### Scenario: VETO session never folds
- GIVEN a session whose audit verdict is VETO
- WHEN the session ends without a seal
- THEN no delta is folded and the delta file remains

### Requirement: Conflicting deltas abort loudly
The fold MUST abort with the tree untouched when a delta names an absent requirement or duplicates an existing one.

#### Scenario: Modified target missing
- GIVEN a delta that modifies a requirement absent from the capability spec
- WHEN the fold runs
- THEN the seal aborts, the spec is unchanged, and the delta file is retained
