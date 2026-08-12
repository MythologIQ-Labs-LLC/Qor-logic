# Fixture: a ladder with an empty Command cell and an out-of-vocabulary Policy

Two independent defects so each raise path can be exercised. `parse_ladder` must
raise naming the offending step rather than skipping the row, because a parser
that drops rows silently is a control that cannot fire.

### Step 4.6: Reliability Sweep

| Step | Gate | Command | Policy | Records | Notes |
|---|---|---|---|---|---|
| 4.6 | intent_lock | `qor-logic reliability intent_lock verify --session "$SESSION_ID" \|\| ABORT` | ABORT | intent_lock_state | fine |
| 4.6.5 | secret_scanner |  | ABORT | secret_scanner | empty Command cell |
| 4.6.9 | skill_size_budget_lint | `qor-logic scripts skill_size_budget_lint --skills-root qor/skills \|\| true` | advisory | skill_size_budget | Policy outside the closed set |

### Step 4.7: Next Step

Terminates the ladder region.
