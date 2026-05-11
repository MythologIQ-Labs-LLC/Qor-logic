# Plan: Phase 55 - Implement owns documentation updates

**change_class**: feature

**doc_tier**: system

**originating_remediation**: GH #52

**terms_introduced**:
- term: documentation implementation step
  home: qor/skills/sdlc/qor-implement/SKILL.md
- term: documentation_touches
  home: qor/gates/schema/implement.schema.json

**boundaries**:
- limitations:
  - V1 requires implement-time documentation accounting, but `/qor-substantiate` remains the final verifier.
  - V1 uses plan-declared doc tier and affected files; it does not infer semantic documentation scope from arbitrary diffs.
- non_goals:
  - Removing documentation currency checks from `/qor-substantiate`.
  - Creating a documentation writer agent.
- exclusions:
  - No changes to compiler internals.

## Open Questions

None.

## Phase 1: Implement skill documentation step

### Affected Files

- `qor/skills/sdlc/qor-implement/SKILL.md` - add implement-time documentation update step before handoff.
- `qor/references/doctrine-documentation-integrity.md` - define implement ownership for doc-affecting changes.
- `tests/test_implement_documentation_step.py` - NEW.

### Changes

Add a new Step 10.2 before blocker completion:

```markdown
### Step 10.2: Documentation Implementation Step (Phase 55 wiring - #52)

If the plan's doc_tier is `standard` or `system`, or if the implementation changes any skill, doctrine, schema, CLI command, public behavior, or user-facing workflow, update the corresponding documentation in the same implementation pass.
```

The step requires the implementer to update relevant docs before Step Z writes `implement.json`. It also requires a short handoff note that lists documentation files touched or says `documentation_touches: []` with a justification.

### Unit Tests

- `test_implement_skill_has_documentation_step`
- `test_documentation_step_precedes_handoff_and_gate_artifact`
- `test_documentation_step_mentions_skill_doctrine_schema_cli_public_behavior`
- `test_documentation_step_requires_empty_justification_when_no_docs_touched`

## Phase 2: Implement artifact schema records documentation touch set

### Affected Files

- `qor/gates/schema/implement.schema.json` - add optional `documentation_touches` field.
- `qor/skills/sdlc/qor-implement/SKILL.md` - include field in Step Z payload example.
- `tests/test_implement_schema_documentation_touches.py` - NEW.

### Changes

Add schema field:

```json
"documentation_touches": {
  "type": "array",
  "items": {
    "type": "object",
    "required": ["path", "reason"],
    "properties": {
      "path": { "type": "string", "minLength": 1 },
      "reason": { "type": "string", "minLength": 1 }
    }
  }
}
```

The field is optional for existing artifacts but populated by the updated skill. Empty array means the implementer asserts no documentation-bearing concept changed.

### Unit Tests

- `test_implement_schema_accepts_documentation_touches`
- `test_implement_schema_rejects_touch_without_reason`
- `test_implement_schema_accepts_empty_documentation_touches`

## Phase 3: Substantiate consumes implement documentation evidence

### Affected Files

- `qor/skills/governance/qor-substantiate/SKILL.md` - Step 6.5 reads `documentation_touches`.
- `tests/test_substantiate_documentation_touches.py` - NEW.

### Changes

In Step 6.5, read `implement.documentation_touches`. If documentation currency warnings exist and `documentation_touches` is empty, PAUSE with a message that implementation did not own documentation updates. If warnings exist but touches are present, continue with the existing warning workflow unless a strict doc-integrity check fails.

### Unit Tests

- `test_substantiate_reads_implement_documentation_touches`
- `test_substantiate_pauses_when_doc_warnings_and_empty_touches`
- `test_substantiate_preserves_doc_integrity_hard_block`

## CI Commands

- `python -m pytest tests/test_implement_documentation_step.py tests/test_implement_schema_documentation_touches.py tests/test_substantiate_documentation_touches.py -v`
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py`
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase55-implement-documentation-lifecycle.md`
