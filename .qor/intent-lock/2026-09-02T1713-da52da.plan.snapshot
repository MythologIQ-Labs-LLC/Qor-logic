# Plan: canonicalize the plan-artifact `terms` field (GH #394)

**change_class**: hotfix

**doc_tier**: standard

**terms**: []

This phase introduces no new domain vocabulary. The retired alias names a
schema key rather than a glossary term, so registering it would be wrong; the
empty declaration is the claim that nothing needs registering. (Tribunal
ground V-1, entry #672: the prior text declared the retired key here as though
it were a term, which `check_glossary` rejects -- the plan failed the very gate
it arms.)

**boundaries**:
- limitations: [does not retro-migrate historical `.qor/gates/**/plan*.json` artifacts or `docs/plan-qor-phase*.md` files that already used `terms_introduced`. Migration is not merely unnecessary but **wrong**: each sealed artifact carries a `.provenance` sidecar whose `payload_sha256` binds its exact bytes, so rewriting the key would trade a schema failure for an evidence-integrity failure. The earlier wording of this line claimed those artifacts were "frozen sealed records" that nothing re-reads; that was false and is corrected in scope item 4 below]
- non_goals: [does not touch `doc_integrity.py`'s read path (`plan.get("terms", [])` was already correct); does not change `derive_phase_metadata`/version tooling; **does not close the omission route** -- `terms` stays absent from schema `required`, so an artifact declaring neither key still validates and still yields an empty declared-terms list. This phase closes the alias route only. The residual is filed as GH #414 with a proposed `doc_tier`-conditional requirement, so it keeps its record rather than disappearing when #394 closes (tribunal ground V-2, entry #672)]
- exclusions: [the diff was authored outside the governed ceremony in a prior session, as PR #403 discloses; the ceremony is being retrofitted onto that existing diff in this cycle rather than skipped -- gate tribunal at entry #672, Step 0 plan-artifact override recorded as event `ec10c35008ec172e1a9407df621dfddf8e50c768a42d88bad4f439ec771f1d07`]

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

4. `qor/scripts/validate_gate_artifact.py`, `qor/reliability/gate_chain_completeness.py`
   and `qor/scripts/evidence_bundle.py`: make sealed-history verification exempt
   from prohibition rules added after the fact. `validate_one` gains a
   keyword-only `sealed_history` flag; when set, the loaded schema is validated
   with its top-level `not` clause removed. Both sealed-history consumers pass
   `sealed_history=True`: `gate_chain_completeness.check`, and
   `evidence_bundle._gate_artifacts` (whose session is operator-selected per
   `evidence_bundle.py:52` and therefore reaches sealed phases). Current-session
   call sites are deliberately unchanged -- `gate_chain.py:101,127,143` read
   artifacts authored under the current schema, where full validation is correct.

`doc_integrity.py` itself is unchanged: its `plan.get("terms", [])` read was
already correct. The defect was entirely in what the authoring surface told
operators/agents to write, not in what the check reads.

## Scope item 4: why the schema rule alone is unshippable

Discovered at seal time by `/qor-substantiate` Step 7.8, after the iteration-2
PASS. `gate_chain_completeness` walks every SESSION SEAL entry with phase >= 52
and runs `validate_gate_artifact.validate_one` against the **current** schema.
Eight already-sealed plan artifacts across phases 187, 191 and 192 carry
`terms_introduced`, so the new `not` rule retroactively invalidates them:

```
FAIL: gate-chain incomplete; 3 missing artifacts:
  phase 187: .../plan.json: <root>: {...} should not be valid under
             {'required': ['terms_introduced'], ...}
```

That check is fail-closed at every seal, so scope items 1-3 shipped alone would
mean no seal in this repository ever completes again -- including the seal that
ships them. This is a release blocker, not a nicety.

The correct boundary is not a phase number but a role distinction. Every entry
`gate_chain_completeness` walks is by definition already sealed; the check's
purpose (per its own docstring and GAP-GOV-14) is detecting skill-protocol
bypass -- a missing, empty, malformed, or structurally incomplete artifact.
A prohibition introduced later says nothing about whether the protocol was
followed at the time. Enforcement of a new prohibition belongs at authoring
time, where `gate_chain.write_gate_artifact` already validates the full current
schema before writing; that path is forward-only by construction and is what
rejects a new alias-carrying payload.

So `sealed_history=True` removes only the top-level `not` clause. `required`,
`type`, `properties` and `$ref` still apply, because those describe what a plan
artifact always had to be. GAP-GOV-14 is preserved exactly: an empty, malformed,
or required-field-missing artifact still fails completeness. The exemption is
narrow by construction and generalizes to every future schema tightening rather
than needing a new constant each time.

Two consumers, not one. `gate_chain_completeness` fails closed at seal time;
`evidence_bundle` fails open into a document. Both read sealed history, so both
take the flag. Tribunal ground V-3 (entry #676) caught the second one after the
first amendment named only the first.

Same defect family as the `MARKUP_COMPAT_BOUNDARY` finding in
`docs/research-brief-open-repository-issues-2026-09-02.md`, approached from the
opposite direction: there an absolute boundary silently forgives unverifiable
history; here its absence retroactively condemns valid history. Both are sealed
evidence re-judged against today's rules.

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

### Scope item 4 tests (written first)

- `tests/test_gate_chain_completeness_sealed_history.py::test_validate_one_rejects_retired_alias_by_default`
  -- a plan payload carrying `terms_introduced` must fail `validate_one(...)`
  with the default (authoring-time) posture. Guards against the exemption
  leaking into the authoring path.
- `tests/test_gate_chain_completeness_sealed_history.py::test_validate_one_sealed_history_exempts_prohibition_rules`
  -- the same payload must pass under `sealed_history=True`. Red before the flag
  exists.
- `tests/test_gate_chain_completeness_sealed_history.py::test_sealed_history_still_rejects_structurally_invalid_artifact`
  -- an artifact missing a schema-`required` field must fail even under
  `sealed_history=True`, proving the exemption is narrow and GAP-GOV-14 holds.
- `tests/test_gate_chain_completeness_sealed_history.py::test_check_passes_with_alias_carrying_sealed_artifact`
  -- `gate_chain_completeness.check` over a fixture ledger whose sealed session
  holds an alias-carrying plan artifact must return `ok=True`. This is the
  end-to-end regression for the seal-time abort.
- `tests/test_gate_chain_completeness_sealed_history.py::test_evidence_bundle_marks_alias_carrying_sealed_artifact_valid`
  -- `evidence_bundle` over a sealed session holding an alias-carrying plan
  artifact must report that artifact `valid: true`. Closes tribunal ground V-3
  (entry #676): an evidence packet attesting a sealed gate chain must not call a
  validly sealed artifact invalid over a prohibition introduced after it was
  written.

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

## CI Commands

- `python -m pytest -q`
- `python -m ruff check qor/ tests/`
- `python -m qor.scripts.check_variant_drift`
