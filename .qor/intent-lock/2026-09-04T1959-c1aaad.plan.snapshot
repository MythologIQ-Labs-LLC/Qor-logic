# Plan: Bind the findings-category mirror

**change_class**: hotfix

**doc_tier**: minimal

**iteration**: 2 (amends iteration 1 for three findings from independent review: a test description that would have produced a vacuous test, a grep quotation narrower than the command's output, and an imprecise reference)

**originating_remediation**: GH #437

**boundaries**:
- limitations:
  - The parity test binds two of the three copies of this vocabulary. The third is prose: the audit-pass-to-category mapping table in `qor/skills/governance/qor-audit/SKILL.md`, which describes itself as a closed 12-value enum and holds 12 rows against the schema's 15, omitting `feature-test-undeclared` and `live-progress-fake`. That copy determines whether an auditor can emit a value at all, and its staleness is the defect recorded at META_LEDGER entry #735. It is left unbound here deliberately: binding prose to a schema is a different mechanism than set parity, and doing it requires a skill edit with its own dist-regeneration and headroom consequences.
  - Closing the drift does not make the category reachable from an audit run; the mapping table in the audit skill is a separate surface and is out of scope here.
- non_goals:
  - Any change to what `/qor-audit` emits, to its passes, or to its mapping table.
  - Removing the mirror. Deriving the frozenset from the schema at import time is a larger change with a stdlib-only and import-cost question behind it; binding the two is the smaller fix that stops the bleeding.
- exclusions:
  - The `scope-overgeneralization` category and the `plan_absolute_claim_lint` work. Phase 261 reached its attempt cap at META_LEDGER entry #735; this phase is a prerequisite for that work, not a resumption of it.
  - GH #438 and GH #440.

## Scoping

One defect, two files. The scope is deliberately this small: the preceding phase spent seven iterations failing on the breadth of its own claims, and a plan with almost no surface has almost nothing to be wrong about.

## Open Questions

None.

## Phase 1: Bind the two sources

### Affected Files

- `tests/test_findings_signature_schema_parity.py` NEW - the binding assertion and the regression it closes
- `qor/scripts/findings_signature.py` - add the missing value to `_VALID_CATEGORIES`

### Locked Decisions

**LD-1. The two sources have drifted and the drift is reachable from a documented VETO.** `findings_signature._VALID_CATEGORIES` is a hand-maintained mirror of the `findings_categories` enum in `audit.schema.json`. The schema carries 15 values, the frozenset 14, and the missing one is `feature-test-undeclared`.

- `git show 9bb10b61:qor/scripts/findings_signature.py | grep -nE '_VALID_CATEGORIES'` -> `28:_VALID_CATEGORIES = frozenset({`
- `git show 9bb10b61:qor/gates/schema/audit.schema.json | grep -nE 'feature-test-undeclared'` -> `45:          "feature-test-undeclared",`

That value is not hypothetical. The audit skill names it at line 54 as item 9 of its Critical Invariants, and again at line 447 as the category a Feature Test Declaration Pass violation must carry; neither line can be quoted as observed text here because both contain inline code formatting. So a correct audit can emit it.

**LD-2. The consequence is a raise inside the escalation check, not a missed count.** `compute_record` raises `UnmappedCategoryError` on any category outside the frozenset, and `stall_walk` calls it without a guard:

- `git show 9bb10b61:qor/scripts/stall_walk.py | grep -nE 'compute_record'` -> `57:        sig = findings_signature.compute_record(record)`
- `git show 9bb10b61:qor/scripts/stall_walk.py | grep -nE 'compute_record'` -> `97:        sig = findings_signature.compute_record(record)`

Both call sites, because that is what the cited command returns. Iteration 1 quoted only the first, which understated the reach: the raise is not confined to one escalator entry point. Line 97 is the one declared test 3 drives.

`stall_walk` is what `cycle_count_escalator.check` and `check_session_total` invoke, which run at `/qor-plan` Step 2c and `/qor-audit` Step 0.5. So the first audit emitting that category does not merely fail to escalate; the next cycle's escalation check raises.

**LD-3. Add the value, and bind the sources so the next divergence fails rather than hides.** The fix is one frozenset member. The test is the part that matters, and the reason it is missing is measurable: searching the whole `tests/` tree for `_VALID_CATEGORIES` returns zero files, so nothing compares the two sources and the suite stays green as they diverge.

- `git show 9bb10b61:qor/scripts/findings_signature.py | grep -nE 'class UnmappedCategoryError'` -> `46:class UnmappedCategoryError(ValueError):`

One *file* references both surfaces, in two separate tests: `tests/test_audit_gate_emits_findings_categories.py` imports the exception from `findings_signature` in one test and asserts one value's membership in the schema enum in another. No single test touches both. Either way, membership of one value is not parity of two sets, and both would pass unchanged across any divergence that keeps that value present.

The alternative -- deriving `_VALID_CATEGORIES` from the schema at import time -- removes the mirror rather than guarding it, and is the better long-run shape. It is not taken here because it changes an import-time cost and a stdlib-only surface for a module three gate paths depend on, and that trade deserves its own phase rather than riding along on a hotfix.

### Changes

`_VALID_CATEGORIES` gains `"feature-test-undeclared"`. Nothing else in the module changes.

The new test file asserts set equality between the schema enum and the frozenset, and separately asserts that `compute_record` accepts a record carrying the previously-missing value.

### Unit Tests

- `tests/test_findings_signature_schema_parity.py::test_schema_enum_and_valid_categories_are_identical` - loads `qor/gates/schema/audit.schema.json`, extracts `properties.findings_categories.items.enum`, and asserts set equality with `findings_signature._VALID_CATEGORIES`. Red before the change: the sets differ by one member.
- `tests/test_findings_signature_schema_parity.py::test_compute_record_accepts_every_schema_category` - for each value in the schema enum, builds a VETO record carrying only that category and asserts `compute_record` returns a signature rather than raising. Red before the change on `feature-test-undeclared`. This is the assertion that matches what the escalator actually does, rather than comparing two collections and inferring the behaviour.
- `tests/test_findings_signature_schema_parity.py::test_stall_walk_survives_every_schema_category` - seeds one VETO record per schema category, each with a distinct `ts`, through `audit_history.append`, then drives `stall_walk.count_session_signature_totals` and asserts it returns. Red before the change, and the only declared test exercising the call path GH #437 describes rather than the function in isolation.

  The seeding path is stated because getting it wrong produces a green vacuous test rather than a failure. `count_session_signature_totals` reads a single JSONL, not a directory of per-record artifacts:

  - `git show 9bb10b61:qor/scripts/audit_history.py | grep -nE 'history_path'` -> `30:    """Return the audit history JSONL path for the given session."""`

  Writing per-category `.json` files into the gate directory yields an empty history, so the function returns `{}` and the test passes before the change while asserting nothing. The test therefore reuses the existing isolation fixture pattern from `tests/test_session_total_signature_count.py`, which monkeypatches **both** `validate_gate_artifact.GATES_DIR` and `qor.workdir.gate_dir` at once. Patching only one leaves the other resolving to the live tree, which is the regression class `tests/test_gate_dir_hygiene.py` exists for, and a partially-isolated run would write into the real gate directory under a session id the conftest sweep does not match.

## Definition of Done

### Deliverable: bound findings-category mirror

- **D1**: Every category the audit schema admits can be signed, and a future divergence between the two sources fails a test rather than surfacing as a raise inside an escalation check.
- **D2**: `findings_signature._VALID_CATEGORIES` equals the schema enum as a set.
- **D3**: No governance artifact changes. GH #437 is closed by this phase and cited in the seal entry.
- **D4**: All three declared tests pass and all three are red beforehand, each for its own stated reason: set inequality, a raise on one value, and a raise propagating through `stall_walk`.

## Feature Inventory Touches

None. This phase touches no user-facing command surface; it repairs an internal invariant between a schema and its mirror.

## CI Commands

- `python -m pytest tests/test_findings_signature_schema_parity.py -v` - the new suite; run twice to confirm determinism
- `python -m pytest tests/test_findings_signature.py tests/test_stall_walk.py tests/test_session_total_signature_count.py tests/test_audit_gate_emits_findings_categories.py -v` - the existing suites over the changed module and its call path
- `python -m pytest -q` - full suite; no regression
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - chain integrity
- `ruff check .` - lint
