# Plan: Phase 151 -- delete the dead session-seal hasher (GAP-GOV-02)

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

None. Follow-on to GH #210 (audit Sprint A). `qor/scripts/calculate-session-seal.py` is dead placeholder
code: a hyphenated, non-importable `__main__` script with a literal `previous_hash = "PREVIOUS_LEDGER_HASH"`
placeholder that reads paths (`src/`, `docs/CONCEPT.md`, `.agent/staging/AUDIT_REPORT.md`) which do not
exist in this repo. The production-gap audit flagged it as misleading about how seals are computed
(reinforcing the GAP-GOV-01 gap, now closed in Phase 150). It has no import coupling. Delete it and
re-point the one misleading `qor-substantiate` SKILL.md reference at the real mechanics. The historical
mention in `doctrine-governance-enforcement.md:310` is accurate history and stays.

## Phase 1: delete the dead file + re-point the doc + guard re-introduction

### Affected Files

- `qor/scripts/calculate-session-seal.py` - DELETE.
- `qor/skills/governance/qor-substantiate/SKILL.md` - replace the `Reference implementation: ...calculate-session-seal.py` line with a pointer to the real seal helpers.
- `tests/test_no_dead_session_seal_hasher.py` (NEW).

### Changes

Delete `qor/scripts/calculate-session-seal.py`. In `qor-substantiate/SKILL.md`, replace:

> Reference implementation: `.claude/commands/scripts/calculate-session-seal.py`.

with a pointer to the canonical helpers used by the real seal path:
`ledger_hash.content_hash(plan_path)` for the entry content digest, `ledger_hash.chain_hash(content,
previous)` for the chain digest, validated by the Step 6.8 hash-guard and the Step 7.7
`seal_entry_check` (which binds `content_hash` to the cited plan's bytes -- GAP-GOV-01). Recompile dist
variants (the SKILL.md change regenerates `qor/dist/variants/**`).

### Unit Tests

- `tests/test_no_dead_session_seal_hasher.py`:
  - `test_no_placeholder_hasher_in_scripts` - scan every `qor/scripts/*.py`; assert NONE contains the
    `PREVIOUS_LEDGER_HASH` placeholder literal (guards re-introduction of a placeholder hasher -- a real
    behavioral guard over the script corpus, not a presence assertion).
  - `test_calculate_session_seal_removed` - `qor/scripts/calculate-session-seal.py` no longer exists.
  - `test_substantiate_skill_does_not_cite_dead_hasher` - the `qor-substantiate` source SKILL.md no longer
    references `calculate-session-seal` (doc-currency: the misleading pointer is gone).

## Definition of Done

### Deliverable: D-gov02

- **D1**: the dead placeholder hasher is gone and the seal skill points operators at the real seal mechanics.
- **D2**: `qor/scripts/calculate-session-seal.py` deleted; SKILL.md re-pointed; dist variants recompiled.
- **D3**: ledger SEAL records GAP-GOV-02 closed; #210 advanced.
- **D4**: `test_no_placeholder_hasher_in_scripts` (no `PREVIOUS_LEDGER_HASH` in any qor/scripts) + `test_calculate_session_seal_removed` + `test_substantiate_skill_does_not_cite_dead_hasher`.

## CI Commands

- `python -m pytest tests/test_no_dead_session_seal_hasher.py -q` -- new guard tests (run twice).
- `python -m pytest -q` -- full suite green.
