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

## 5. Documentation Currency (Phase 31 wiring)

`/qor-substantiate` Step 6.5 invokes `doc_integrity_strict.check_documentation_currency` against the implement gate artifact. The heuristic fires when:

- `files_touched` contains at least one file matching `qor/skills/**/SKILL.md`, `qor/references/doctrine-*.md`, `qor/gates/schema/*.json`, or `qor/scripts/*.py`
- AND none of `docs/architecture.md`, `docs/lifecycle.md`, `docs/operations.md`, `docs/policies.md` are in `files_touched`.

The helper returns a warning list (non-empty iff fired). Phase 31 wires WARN semantics: the operator sees the warnings, decides whether they're spurious (trivial code change; no doc update warranted) or legitimate (new concept; doc must reflect), and either continues seal or pauses to amend the system-tier docs.

Strict-mode upgrade (BLOCK instead of WARN) is deferred to a future phase when the heuristic's false-positive rate is known from production use.

**Rationale**: Phase 30 authored the four system-tier docs, but without a seal-time check the docs drift silently as future phases modify skills/doctrines/scripts. Step 6.5 prevents silent drift by raising a prompt whenever a phase's delta plausibly affects the documented story.

**Anti-pattern**: do NOT add every file-type to the trigger list. The heuristic's signal degrades if it fires on test edits, dist variants, or ledger updates. Keep the trigger set scoped to source-of-truth locations.

### 5a. Release-doc coverage (Phase 33 wiring)

The term **release_docs** names README.md and CHANGELOG.md — the user-facing narrative docs whose content carries release-specific claims (feature highlights, version badges, changelog sections) that go stale when a release ships without updating them.

`check_documentation_currency` takes an optional third argument `plan_payload: dict | None = None`. When `plan_payload["change_class"]` is `"feature"` or `"breaking"` (the release-class set), the check additionally requires both `README.md` and `CHANGELOG.md` to appear in `files_touched`. Missing either emits a `Release-path change (change_class=...) without updating <doc>` warning. `change_class="hotfix"` is exempt (hotfixes can skip release-notes authoring; a separate rule TBD if hotfix README drift becomes a pattern).

Trigger lives on the plan artifact's declared `change_class` rather than the implement artifact's `files_touched`. This matters because the only file whose presence would reliably signal "this is a release" — `pyproject.toml` — is bumped by `/qor-substantiate` Step 7.5 AFTER the currency check runs at Step 6.5, so it would never appear in `implement.files_touched`. Gating on `plan_payload.change_class` makes the rule fire during the phase that introduces it (self-dogfood — see SG-Phase28-A) and on every subsequent release phase.

**Countermeasure history**: SG-Phase32-B (README's static `## What's new in v0.22.0` heading survived Phase 32's seal at v0.23.0). Two-layer fix: (a) README rewritten to be version-agnostic at Phase 32 close; (b) this Phase 33 rule catches forgotten README/CHANGELOG updates during release authoring.

## 6. Check-surface extensions: strict-mode (Phase 31)

`doc_integrity.run_all_checks_from_plan` accepts a `strict: bool = False` kwarg. When `True`, the composite additionally invokes `doc_integrity_strict.check_term_drift` (Check Surface D) and `doc_integrity_strict.check_cross_doc_conflicts` (Check Surface E). Both raise `ValueError` on the first finding when strict.

Scope fences (Phase 31 wiring):

- `.py`, `.json`, `.toml`, `.cedar` files excluded.
- `vendor/`, `fixtures/`, `dist/` directories excluded.
- Doctrine-peer exclusion: if a term's `home:` is a `doctrine-*.md` file, usage in OTHER `doctrine-*.md` files is not drift (cross-doctrine references are normal prose).
- Home-directory-peer exclusion: if term's `home:` sits in directory X, usage in X's other files is not drift.
- Per-entry `scope_exclude: []` list in glossary frontmatter.

**Strict mode is live at `/qor-substantiate` Step 4.7 as of Phase 32** via `run_all_checks_from_plan(..., strict=True)`. Lenient mode (default) remains the mode for the ad-hoc drift report CLI and any future skill that wants advisory output. Phase 32 delivered the zero-finding baseline that made live wiring viable: docs/*.md archive-by-default (except the 4 system-tier docs), README + CHANGELOG excluded as narrative entry points, targeted `referenced_by:` adoption for high-usage terms.
