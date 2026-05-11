# Plan: Phase 57 - Audit adversary and SDK alignment

**change_class**: feature

**doc_tier**: system

**originating_remediation**: GH #50, GH #49, GH #47 follow-up

**terms_introduced**:
- term: independent adversarial reviewer
  home: qor/skills/governance/qor-audit/SKILL.md
- term: third-party SDK alignment
  home: qor/skills/governance/qor-audit/SKILL.md
- term: behavioral semantics claim
  home: qor/references/doctrine-shadow-genome-countermeasures.md

**boundaries**:
- limitations:
  - V1 codifies the reviewer contract and artifact shape. It does not require a specific external model or vendor.
  - SDK alignment checks are evidence-based: docs, local installed types, lockfiles, generated clients, or source references. Network lookup is not required.
- non_goals:
  - Fully automated SDK semantic proof.
  - Replacing human Judge disposition.
- exclusions:
  - No changes to the Phase 49 Python pipeline lint helper except documentation of how its findings enter the reviewer checklist.

## Open Questions

None.

## Phase 1: Independent reviewer contract

### Affected Files

- `qor/skills/governance/qor-audit/SKILL.md` - replace placeholder adversarial mode text with a concrete reviewer contract.
- `qor/skills/governance/qor-audit/references/adversarial-mode.md` - NEW.
- `qor/gates/schema/audit.schema.json` - add optional `adversarial_review` object.
- `tests/test_audit_adversarial_reviewer_contract.py` - NEW.

### Changes

Define a host-neutral Option B contract:

```markdown
The Judge MUST obtain an independent counter-review for L2/L3 plans and for any plan touching skills, schemas, ledger, substantiation, or audit passes. The reviewer receives the plan text and current repo evidence, then returns findings only: no implementation suggestions, no rewrite assistance.
```

The audit artifact records:

```json
"adversarial_review": {
  "required": true,
  "mode": "independent-reviewer",
  "reviewer_id": "string",
  "findings_count": 0,
  "summary": "string"
}
```

Solo audit remains allowed for L1 plans and for hosts without parallel review capability, but missing capability is logged as `capability_shortfall`.

### Unit Tests

- `test_audit_skill_requires_independent_review_for_l2_l3`
- `test_audit_skill_requires_independent_review_for_governance_surfaces`
- `test_adversarial_mode_reference_exists`
- `test_audit_schema_accepts_adversarial_review_object`
- `test_audit_schema_rejects_missing_required_adversarial_review_fields`

## Phase 2: Third-party SDK alignment pass

### Affected Files

- `qor/skills/governance/qor-audit/SKILL.md` - extend Infrastructure Alignment Pass.
- `qor/references/doctrine-shadow-genome-countermeasures.md` - add SDK behavioral-semantics countermeasure entry.
- `tests/test_audit_sdk_alignment_pass.py` - NEW.

### Changes

Extend Infrastructure Alignment with a sub-pass:

```markdown
#### Third-Party SDK Alignment

For each plan claim about an SDK, framework, generated client, API response shape, retry behavior, pagination, auth behavior, error type, or webhook/event semantic, verify the claim against local evidence. Acceptable evidence: installed package source, lockfile version plus local type definitions, generated client code, vendored docs, checked-in integration tests, or a cited operator-provided source excerpt.
```

Unsupported behavioral claims VETO as `infrastructure-mismatch`. If the claim is a dependency justification issue rather than a current-code mismatch, route to `dependency-unjustified`.

### Unit Tests

- `test_audit_skill_has_third_party_sdk_alignment_anchor`
- `test_sdk_alignment_mentions_response_retry_pagination_auth_error_event_semantics`
- `test_sdk_alignment_routes_unsupported_claims_to_infrastructure_mismatch`
- `test_sdk_alignment_allows_local_evidence_sources`

## Phase 3: Reviewer checklist includes composition defects

### Affected Files

- `qor/skills/governance/qor-audit/references/adversarial-mode.md` - include Phase 49 composition-defect questions.
- `tests/test_adversarial_mode_composition_defects.py` - NEW.

### Changes

The independent reviewer prompt includes:

- enumerate multi-stage pipelines
- identify filter preconditions and enforced invariants
- confirm pipeline order is valid
- call out external validators that are assumed but not enforced in-function

This preserves GH #47 coverage inside the independent review path, not only inside the primary Judge pass.

### Unit Tests

- `test_adversarial_mode_mentions_filter_stage_ordering`
- `test_adversarial_mode_mentions_external_validator_assumption`
- `test_adversarial_mode_routes_confirmed_composition_defects`

## CI Commands

- `python -m pytest tests/test_audit_adversarial_reviewer_contract.py tests/test_audit_sdk_alignment_pass.py tests/test_adversarial_mode_composition_defects.py -v`
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py`
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase57-audit-adversary-and-sdk-alignment.md`
