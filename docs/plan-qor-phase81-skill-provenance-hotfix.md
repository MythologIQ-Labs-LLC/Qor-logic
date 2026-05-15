# Plan: Phase 81 - qor-governance-compliance provenance frontmatter hotfix (GH #77)

**change_class**: hotfix

**doc_tier**: minimal

**originating_remediation**: GH #77 -- two installed skill files fail F244/FX359 provenance schema in the FailSafe extension's release pipeline. Of the two, ONLY `qor-governance-compliance` is sourced from this repo (`qor/skills/governance/qor-governance-compliance/SKILL.md`). The other (`qor-compliance`) is NOT in Qor-logic -- no occurrence in `qor/skills/`, `qor/dist/`, or anywhere else in the tree -- so it must be from a different source (likely FailSafe's own skills bundle) and is out of scope for this repo. Phase 81 closes the in-scope half; cross-reference to file the qor-compliance half against FailSafe.

**terms_introduced**: (none)

**boundaries**:
- limitations:
  - V1 hotfix scope: minimal frontmatter edit + one regression test. No new doctrine, no new glossary terms.
  - Single-file source-of-truth fix; `qor/scripts/dist_compile` regenerates dist variants from the corrected source.
- non_goals:
  - No fix for `qor-compliance` (NOT in this repo; file separately against FailSafe upstream).
  - No org-spelling normalization across other skills (mixed `MythologIQ` / `MythologIQ-Labs-LLC` usage in repo; tracked separately if surfaced as a defect).
  - No schema extension; F244/FX359 is the consumer-side schema, not a Qor-logic governance contract.
- exclusions:
  - No changes to other governance skills.
  - No CI workflow changes.

## Open Questions

None. GH #77 specifies the exact missing fields (`metadata.source.repository`, `metadata.source.path`) and the schema's URL requirement (`https?://` prefix). Repository value resolved to `https://github.com/MythologIQ-Labs-LLC/Qor-logic` per the canonical git remote (this repo is the actual source-of-truth for the skill, not FailSafe).

## Feature Inventory Touches

| FEATURE_INDEX entry | Operation | Test descriptor |
|---|---|---|
| qor-governance-compliance frontmatter provenance | MODIFIED | tests/test_qor_governance_compliance_provenance.py asserts metadata.source.repository (https URL) + metadata.source.path are present |

## Phase 1: Add metadata.source nested block

### Affected Files

- `qor/skills/governance/qor-governance-compliance/SKILL.md` -- amend YAML frontmatter to add `metadata.source.repository` (URL to this repo) and `metadata.source.path` (path within this repo). Existing `metadata.category` retained.
- `tests/test_qor_governance_compliance_provenance.py` -- NEW. 2 tests: F244/FX359 required fields present; repository is an `https?://` URL.

### Changes

Replace the current `metadata:` block:

```yaml
metadata:
  category: governance
```

with:

```yaml
metadata:
  category: governance
  author: MythologIQ Labs, LLC
  source:
    repository: https://github.com/MythologIQ-Labs-LLC/Qor-logic
    path: qor/skills/governance/qor-governance-compliance
```

Order in the YAML stream is preserved otherwise: `name`, `metadata`, `description`, `creator`, `license`, `phase`, `tone_aware`, `gate_reads`, `gate_writes` continue to appear in their current positions. The existing top-level `creator: MythologIQ Labs, LLC` and `phase: governance` already satisfy the FX359 contract; only `metadata.source` was missing.

### Unit Tests

- `tests/test_qor_governance_compliance_provenance.py::test_metadata_source_block_present` -- reads `qor/skills/governance/qor-governance-compliance/SKILL.md`, parses YAML frontmatter, asserts `metadata.source.repository` and `metadata.source.path` are present.
- `tests/test_qor_governance_compliance_provenance.py::test_metadata_source_repository_is_https_url` -- asserts `metadata.source.repository` matches `https?://` prefix per F244/FX359 schema requirement.

## CI Commands

- `python -m pytest tests/test_qor_governance_compliance_provenance.py -v` -- validates Phase 81 tests.
- `python -m qor.scripts.dist_compile` -- regenerates dist variants from the corrected source so installer copies the fixed frontmatter.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase81-skill-provenance-hotfix.md` -- self-application.
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py` -- full suite.
