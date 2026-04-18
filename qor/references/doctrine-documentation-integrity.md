# Doctrine: Documentation Integrity

> A repo's documentation must behave as a coherent system. Concepts live in
> named homes; terms have canonical definitions; plans declare what they
> introduce; substantiation verifies that declared promises land in the docs.

Scope: enforced at `/qor-substantiate` time via `qor/scripts/doc_integrity.py`.
Advisory at `/qor-plan` (warns during dialogue) and `/qor-audit` (reports drift
without VETO). Hard-blocks only at substantiation, where `Reality = Promise`
is the binding contract.

## 1. Tiers

Every plan declares a `doc_tier` that scales the doctrine to the repo's stage.

| Tier | Required artifacts |
|---|---|
| `minimal` | `README.md` |
| `standard` | `minimal` + `qor/references/glossary.md` |
| `system` | `standard` + `docs/architecture.md` + `docs/lifecycle.md` + `docs/operations.md` + `docs/policies.md` |
| `legacy` | none (bypass; requires `doc_tier_rationale` per plan schema) |

`legacy` is the sole documented escape. The schema rejects `doc_tier: legacy`
without `doc_tier_rationale`; Plan-layer dialogue emits severity-2
`doc_tier_legacy_declared` shadow events.

## 2. Glossary entry schema

Canonical location: `qor/references/glossary.md`. Entries are YAML fences
embedded in the markdown body:

```yaml
term: Phase (SDLC)
definition: A stage in the Qor governance lifecycle.
home: qor/gates/chain.md
referenced_by:
  - CLAUDE.md
  - qor/gates/delegation-table.md
introduced_in_plan: phase28-documentation-integrity
```

Required fields: `term`, `definition`, `home`. Optional: `aliases`,
`referenced_by`, `introduced_in_plan`. All YAML parsing uses `yaml.safe_load`;
documents containing custom tags (`!!python/object` etc.) are rejected
(SG-Phase24-B countermeasure).

A glossary entry is simultaneously a term definition AND a concept map entry
(`home:` names the authoritative file; `referenced_by:` names consumers).
No separate concept-map artifact exists; the glossary IS the map.

## 3. Check surface

`doc_integrity.py` exposes three public checks, each raising `ValueError` on
violation (changelog_stamp idiom; no return codes).

### `check_topology(tier, repo_root)`

Verifies that every artifact required by the tier exists at its canonical
path. Missing artifact -> `ValueError` naming the tier and the missing file.

### `check_glossary(glossary_path, declared_terms, repo_root=None)`

For every term declared in the plan's `terms` block:

- The term must have a matching glossary entry.
- The entry's `definition` must be non-empty.
- When `repo_root` is provided, the entry's `home` path must resolve.

### `check_orphans(glossary_path, current_session_plan_tag, repo_root=None)`

For every glossary entry:

- The entry's `home` must resolve (structural integrity).
- The entry must have at least one `referenced_by` consumer, OR it must have
  been `introduced_in_plan` matching the current session's plan tag (newly
  introduced concepts are allowed a grace period until their first consumer
  cites them).

An orphan is a term that was declared but never adopted: present in the
glossary, yet no doc references it and no in-flight plan introduced it.

## 4. Enforcement

| Skill | Behavior |
|---|---|
| `/qor-plan` | Warns during dialogue (Step 1b) when `doc_tier` is omitted (defaults to `standard`); warns when `system` declared without `terms_introduced`. Non-blocking. |
| `/qor-audit` | Emits a `## Documentation Drift` section in AUDIT_REPORT.md when the glossary diverges from the plan's declarations. Non-VETO. |
| `/qor-substantiate` | Step 4.7 invokes `check_topology`, `check_glossary`, `check_orphans` per the plan's declared tier. Any `ValueError` ABORTs substantiation (`legacy` tier bypasses all three checks). |

The asymmetry is deliberate: substantiation is the fail-fast gate; earlier
phases warn but continue so operators can fix drift in a single pass. There
is no silent override and no retry-with-waiver path at substantiate — the
`legacy` tier is the single documented escape, declared upfront in the plan.

## 5. Failure modes

| Symptom | Check that catches it | Operator fix |
|---|---|---|
| Plan introduces a term; glossary not updated | `check_glossary` (missing term) | Add glossary entry with `home:` and re-substantiate |
| Glossary entry has empty `definition:` | `check_glossary` | Fill in the definition |
| Glossary entry's `home:` points to a file that doesn't exist | `check_glossary` + `check_orphans` | Correct the path, or create the home file |
| Old glossary entry has no consumers and wasn't introduced in current plan | `check_orphans` | Either cite a consumer in `referenced_by:` or declare the entry stale (remove it in a follow-on plan) |
| Plan declares `doc_tier: legacy` without rationale | plan.schema.json `if-then` | Add `doc_tier_rationale` or raise the tier |
| YAML fence contains `!!python/object` or other custom tags | `parse_glossary` via `yaml.safe_load` | Rewrite the entry using plain YAML data types |

## 6. Out of scope (for Phase 28)

- **Term-drift grep** (check-surface D): full-repo grep for glossary terms,
  flagging any term used in a doc but not declared. Deferred: expensive at
  substantiate time; false-positive risk against code comments, URLs, and
  prose uses of common words.
- **Cross-doc conflict detection** (check-surface E): detecting when the same
  concept is defined differently across files. Deferred: requires semantic
  comparison beyond YAML parsing.

Both are candidates for future doctrine extensions.

## 7. Rationale

Qor-logic's machinery (gates, doctrines, scripts) was strong; its wayfinding
(glossary, concept map, index, reading order) was weak. The repo had no
glossary, "Phase" carried three unrelated meanings, 23 of 30 doctrines were
orphans from any declared entry point. This doctrine exists because a
governance framework whose documentation cannot be navigated as a system is
worse than one that does not claim to be a system at all -- the audit trail
suggests coherence that is not there.

Tiers exist because `system` enforcement is punishing for small/early repos.
Tiering scales the rule without discarding it.

Source incident: RESEARCH_BRIEF.md (Phase 28 recon; 18 CONFIRMED + 2 PARTIAL
gaps). Author's caveat captured in CLAUDE.md: physical-drive enforcement
(installed instance behavior) is out of scope; Qor-logic enforces by plan.

## 8. Upstream

- Plan schema: `qor/gates/schema/plan.schema.json` (carries `doc_tier`,
  `terms`, `boundaries`, `doc_tier_rationale` and the conditional rule
  `doc_tier == 'legacy' -> doc_tier_rationale required`).
- Mechanism: `qor/scripts/doc_integrity.py` (parser + three checks).
- Tests: `tests/test_doc_integrity.py`, `tests/test_glossary_parse.py`,
  `tests/test_plan_schema_doc_integrity.py`.
- Companion doctrines: `doctrine-test-discipline.md` (Rule 4: every rule has
  a test), `doctrine-shadow-genome-countermeasures.md` (SG-Phase24-B safe
  loader, SG-038 prose-code mismatch, SG-036 doctrine self-application).
