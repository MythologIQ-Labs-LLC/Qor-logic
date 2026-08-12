# Fixture: a ladder whose module prerequisite disagrees with the Step Prerequisites table

The 4.6.5 row names a truncated variant of the real module. The consistency check
must report the disagreement rather than accepting either spelling.

The deliberately-wrong value lives only in this fixture. A non-existent module
path written into plan prose is indistinguishable from a bad citation, both to
`plan_grep_lint` and to a reader.

## Step Prerequisites

| Step | Requires | Notes |
|---|---|---|
| 4.6.5 secret_scanner | module:qor.scripts.secret_scan | truncated on purpose |

## Execution Protocol

The H2 boundary matters: `parse_step_prerequisites` scopes its table to the
`## Step Prerequisites` section and stops at the next H2, not the next H3. The
live skill has `## Execution Protocol` between the two tables, so the ladder is
out of its reach; a fixture without that boundary would let the prerequisites
parser swallow the ladder table and would not model the real file.

### Step 4.6: Reliability Sweep

| Step | Gate | Command | Policy | Records | Notes |
|---|---|---|---|---|---|
| 4.6.5 | secret_scanner | `qor-logic scripts secret_scanner --staged \|\| ABORT` | ABORT | secret_scanner | requires `module:qor.scripts.secret_scanner` |

### Step 4.7: Next Step

Terminates the ladder region.
