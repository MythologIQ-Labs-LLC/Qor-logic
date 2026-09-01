# Plan: canonicalize the plan-artifact `terms` field (GH #394)

**change_class**: hotfix

**doc_tier**: standard

**terms**:
- term: terms_introduced (retired alias)
  home: qor/gates/schema/plan.schema.json

**boundaries**:
- limitations: [does not retro-migrate historical `.qor/gates/**/plan*.json` artifacts or `docs/plan-qor-phase*.md` files that already used `terms_introduced`; those are frozen sealed records, and git history is their archive]
- non_goals: [does not touch `doc_integrity.py`'s read path (`plan.get("terms", [])` was already correct); does not change `derive_phase_metadata`/version tooling]
- exclusions: [does not run the full `/qor-audit` -> `/qor-implement` -> `/qor-substantiate` Merkle-sealing ceremony for this cycle -- see PR body]

## Problem

`qor/gates/schema/plan.schema.json` defines the canonical plan-artifact field
as `terms` (an array of `{term, home}`), and `qor/scripts/doc_integrity.py`
reads exactly that key (`plan.get("terms", [])`) when running the glossary
check at `/qor-substantiate` Step 4.7.

`qor/skills/sdlc/qor-plan/SKILL.md` and its
`references/step-extensions.md` companion, plus
`qor/references/doctrine-documentation-integrity.md` and
`qor/references/doctrine-ideation-readiness.md`, all instructed the operator
dialogue and the plan-doc template to use a different field name,
`terms_introduced`. Because `plan.schema.json` sets
`additionalProperties: true`, a plan artifact authored exactly per those
instructions validated cleanly while `doc_integrity`'s glossary check saw an
empty declared-terms list -- the gate inspected nothing and reported success.
Multiple already-sealed plan artifacts under `.qor/gates/**/plan*.json`
carry this exact key, confirming the mismatch was live, not hypothetical.

## Fix

1. `qor/gates/schema/plan.schema.json`: add a top-level `not: {required:
   [terms_introduced]}` rule so a payload carrying the retired alias fails
   schema validation instead of silently passing through
   `additionalProperties: true`.
2. `qor/skills/sdlc/qor-plan/SKILL.md`,
   `qor/skills/sdlc/qor-plan/references/step-extensions.md`,
   `qor/references/doctrine-documentation-integrity.md`,
   `qor/references/doctrine-ideation-readiness.md`: rename every
   `terms_introduced` reference to the schema-canonical `terms`, so newly
   authored plans stop reproducing the mismatch.
3. Regenerate `qor/dist/variants/**` via
   `BUILD_REGEN=1 python qor/scripts/dist_compile.py` so the compiled
   per-tool skill copies stay in sync with the edited source skill
   (`qor/scripts/check_variant_drift.py` was red before this step, clean
   after).

`doc_integrity.py` itself is unchanged: its `plan.get("terms", [])` read was
already correct. The defect was entirely in what the authoring surface told
operators/agents to write, not in what the check reads.

## Tests (written first; confirmed red before the schema fix, green after)

- `tests/test_plan_schema_doc_integrity.py::test_plan_schema_rejects_terms_introduced_alias`
  -- schema-level negative probe: a payload declaring `terms_introduced`
  must fail `jsonschema.validate`. Failed with "DID NOT RAISE" against
  unmodified `main`; passes after the schema `not` rule.
- `tests/test_doc_integrity.py::test_run_all_checks_from_plan_raises_on_unregistered_term`
  -- positive regression: the full `run_all_checks_from_plan(plan,
  repo_root)` entry point (not just `check_glossary`'s explicit
  `declared_terms` list argument, which already had coverage) must raise
  when a plan declares an unregistered term under the canonical `terms`
  key. Already passed against unmodified `main` (documents that
  `doc_integrity.py`'s read path was never the bug); kept as permanent
  regression coverage for the entry point.
- `tests/test_doc_integrity.py::test_run_all_checks_from_plan_ignores_terms_introduced_alias`
  -- documents, as an explicit non-goal, that a plan carrying only the
  retired `terms_introduced` key evaluates to zero declared terms at the
  `doc_integrity` layer (matching pre-fix behavior); the actual protection
  now lives at the schema boundary (probe above), which prevents such a
  payload from ever reaching this function as a sealed gate artifact.

## Validation

- `python -m pytest tests/test_plan_schema_doc_integrity.py tests/test_doc_integrity.py -q`
  -- 26 passed, run three times for determinism.
- `python -m pytest -q` (full suite) -- 3161 passed, 4 skipped, 4 deselected,
  no failures.
- `python -m ruff check qor/ tests/` -- all checks passed.
- `python -m qor.scripts.check_variant_drift` -- `OK: 406 files, no drift`
  after the `BUILD_REGEN=1` recompile (was `DRIFT DETECTED: 10
  difference(s)` before it).
- `python -m qor.scripts.publication_boundary_lint` -- `0 finding(s)`.

## CI commands

- `python -m pytest -q`
- `python -m ruff check qor/ tests/`
- `python -m qor.scripts.check_variant_drift`
