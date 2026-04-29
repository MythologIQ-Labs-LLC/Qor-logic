# qor.reliability

Runtime reliability gates invoked from SDLC skill steps. Each gate is a pure-function helper paired with a CLI wrapper; the CLI exits non-zero on failure so skill-level `|| ABORT` patterns interdict the lifecycle.

## Gates

| Module | Skill step | Phase wired | What it catches |
|---|---|---|---|
| [`intent_lock`](intent_lock.py) | `/qor-implement` Step 5.5 (capture) and `/qor-substantiate` Step 4.6 (verify) | Phase 17 | Drift between the audit-PASS state (plan + audit + HEAD ancestry) and the substantiate-time state. Captures SHA-256 fingerprints at implement-start; re-verifies at seal. Phase 43's ancestry fix made HEAD-comparison forward-tolerant. |
| [`skill_admission`](skill_admission.py) | `/qor-substantiate` Step 4.6 | Phase 17 | Invoking skill is registered, frontmatter has required keys (`name`, `description`, `phase`), `name` matches directory basename. |
| [`gate_skill_matrix`](gate_skill_matrix.py) | `/qor-substantiate` Step 4.6 | Phase 17 | Every `/qor-*` reference across all skill bodies resolves to an extant skill. Catches handoff drift during refactors. |
| [`seal_entry_check`](seal_entry_check.py) | `/qor-substantiate` Step 7.7 | Phase 47 | Latest META_LEDGER entry is a `SESSION SEAL` for the current phase with internally-consistent chain hash. Closes SG-AdjacentState-A's bookkeeping-gap subclass — Phase 46's first substantiate sealed at v0.33.0 without writing ledger entries; the existing 4.6 gates run before Step 7's seal-entry-write so they could not catch it. |

## Invocation pattern

All gates use the same shape inside skill prompts:

```bash
python -m qor.reliability.<gate> <args> || ABORT
```

`<gate>` is the module name; `<args>` are CLI flags documented in each module's `--help`. Non-zero exit aborts the skill phase. The operator must resolve the underlying drift (re-audit, re-admit, fix handoff, append the missing seal entry, etc.) and re-run the failing skill.

## When to add a new gate

Add a gate when a SHADOW_GENOME failure pattern shows three properties:

1. **Mechanical**: the failure is detectable by reading repo state, not by judgment.
2. **Recurring**: at least one prior incident, ideally with a documented family ID (e.g., SG-AdjacentState-A).
3. **Late-binding**: the failure mode lands AFTER its corresponding skill ran, leaving a gap between "skill said it was done" and "the artifact reality matches".

The gate is the structural countermeasure. Pair it with proximity-anchored + strip-and-fail wiring tests (per [doctrine-test-functionality](../references/doctrine-test-functionality.md)) that lock the wiring against future drift.

## Step ordering matters

Each gate's location in the substantiate sequence is determined by its preconditions, not by sibling proximity. The Phase 47 audit's first three VETOs all rejected attempts to colocate `seal_entry_check` with the existing reliability gates at Step 4.6 — the seal entry does not yet exist at Step 4.6; it's written by Step 7. Step 7.7 (post-Step-7) is the only valid placement. When proposing a new gate, trace each precondition back to the skill step that establishes it.

## Layout

```
qor/reliability/
  __init__.py
  intent_lock.py        Phase 17 wiring
  skill_admission.py    Phase 17 wiring
  gate_skill_matrix.py  Phase 17 wiring
  seal_entry_check.py   Phase 47 wiring
  README.md             this file
```

Tests live at `tests/test_<module>.py` for behavioral coverage and `tests/test_substantiate_*.py` for skill-prompt wiring assertions.
