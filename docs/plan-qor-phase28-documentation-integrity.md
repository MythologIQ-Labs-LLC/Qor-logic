# Plan: Phase 28 - Documentation Integrity Doctrine + Enforcement

**change_class**: feature

**doc_tier**: standard

**doc_tier_downgrade_note**: Amended from `system` to `standard` at substantiate time. Step 4.7 (the check this plan introduces) correctly flagged that Qor-logic lacks `docs/{architecture,lifecycle,operations,policies}.md` required by `system` tier. Building those four docs is out of scope for Phase 28. The downgrade is evidence that the doctrine is working: a plan's tier claim must match repo reality, and `standard` is the honest claim (README + glossary both exist). Raising to `system` awaits a future phase that authors the four missing docs.

**terms_introduced**:
- term: Doc Tier                   | home: qor/references/doctrine-documentation-integrity.md
- term: Glossary Entry             | home: qor/references/doctrine-documentation-integrity.md
- term: Concept Home               | home: qor/references/doctrine-documentation-integrity.md
- term: Orphan Concept             | home: qor/references/doctrine-documentation-integrity.md
- term: Doc Integrity Check Surface | home: qor/references/doctrine-documentation-integrity.md

**boundaries**:
- limitations:
  - Term-drift grep (check-surface D) and cross-doc conflict detection (check-surface E) are explicitly out of scope for this plan; captured as follow-on doctrine extensions.
  - Does not attempt automated concept-home inference; `home:` is author-declared.
- non_goals:
  - Auto-generating the glossary from code annotations.
  - Machine translation of definitions; multi-language glossary.
  - Retroactive glossary backfill for pre-Phase-28 terminology outside GAP-REPO-02/03/04 scope.
- exclusions:
  - Plans declaring `doc_tier: legacy` bypass all doc-integrity checks; rationale is mandatory and enforced by test (see Phase 2).
  - Skill-reference docs outside `qor/references/` (e.g., `qor/gates/schema/*.schema.json`) carry no terms subject to glossary hygiene.

**Target Version**: next minor bump after current tag (governed by Step 7.5 of /qor-substantiate).

**Basis**: `RESEARCH_BRIEF.md` (session-local, phase 28 recon bundle; 18 CONFIRMED + 2 PARTIAL gaps).

**Decisions locked in dialogue**:

- Tier model: `minimal | standard | system | legacy` (tier declared per plan).
- Glossary format: markdown with required per-term frontmatter; glossary IS the concept map (one artifact, `home:` + `referenced_by:` fields).
- Enforcement: `/qor-substantiate` blocks hard on tier-required violations (raises `ValueError` per `changelog_stamp.py` precedent); `/qor-plan` + `/qor-audit` warn only. `legacy` tier is the sole documented escape.
- Check surface: topology presence + glossary hygiene + orphan scan. Term-drift grep and cross-doc-conflict detection are follow-on plans, not in-scope.

## Open Questions

1. Glossary canonical path: `qor/references/glossary.md` (co-located with doctrines) vs `docs/GLOSSARY.md` (co-located with other docs)? Plan assumes `qor/references/glossary.md` for discoverability from skill-referenced doctrines; confirm before Phase 1.
2. Per-term frontmatter delimiter: HTML comments (`<!-- term: X -->`) parse cleanly with `doc_integrity.py` but look odd in rendered markdown; alternative is a YAML fence (`\`\`\`yaml` block) at the top of each term section. Plan assumes YAML fence; confirm before Phase 1.
3. Phase 3 dogfood scope: fix GAP-REPO-01 (workflow-bundles phase list) and GAP-REPO-02/03/04 (glossary fill-in for Phase/Gate/Shadow Genome) in this plan, OR defer to a separate phase/29 plan that runs the upgraded skills against this repo? Plan assumes in-scope (Phase 3 dogfoods); confirm before Phase 3.

## Phase 1: Authority Layer

Establish the doctrine, the glossary bootstrap, the plan-schema extension, and the `doc_integrity.py` module. Nothing downstream depends on anything else until this phase lands.

### Affected Files

- `qor/scripts/tests/test_doc_integrity.py` - NEW; drives `doc_integrity.py` API shape.
- `qor/scripts/tests/test_plan_schema.py` - NEW (or extend existing schema test); asserts new optional fields validate.
- `qor/scripts/tests/test_glossary_parse.py` - NEW; asserts glossary frontmatter parse.
- `qor/references/doctrine-documentation-integrity.md` - NEW; defines tiers, required artifacts per tier, glossary frontmatter schema, check surface, escape via `legacy`, failure-mode table.
- `qor/references/glossary.md` - NEW (bootstrap only: `Doctrine`, `Doc Tier`, `Glossary Entry`, `Concept Home`, `Orphan Concept`). Qor-logic-wide glossary fill-in deferred to Phase 3.
- `qor/gates/schema/plan.schema.json` - MODIFY; add optional `doc_tier` (enum), `terms` (array of `{term, home}`), `boundaries` (`{limitations, non_goals, exclusions}`). All optional; existing plans validate unchanged. No `concepts` alias (glossary IS the concept map per Q3 decision; alias dropped to prevent prose-code drift).
- `qor/scripts/doc_integrity.py` - NEW; public API: `check_topology(tier, repo_root) -> None`, `check_glossary(glossary_path, declared_terms) -> None`, `check_orphans(glossary_path) -> None`, `parse_glossary(path) -> list[Entry]`. All YAML parsing uses `yaml.safe_load` (never `yaml.load`); parser rejects documents containing custom tags (`!!python/object` etc.) to satisfy A08 Software/Data Integrity per SG-Phase24-B. Each raises `ValueError` on violation (no return codes).

### Changes

**`doctrine-documentation-integrity.md`** (canonical reference). Sections: (1) Tier table with required artifacts: `minimal = README.md`; `standard = minimal + glossary.md`; `system = standard + architecture.md + lifecycle.md + operations.md + policies.md`; `legacy` = bypass with ledger rationale. (2) Glossary entry schema (YAML-fence frontmatter: `term`, `definition`, `home` required; `aliases`, `referenced_by`, `introduced_in_plan` optional). (3) Check surface: topology presence + glossary hygiene (every declared term in plan has matching glossary entry with non-empty `definition` and valid `home` path) + orphan scan (every `home` path exists; every entry has at least one non-empty `referenced_by` OR was introduced within the current session's plan). (4) Enforcement: `/qor-substantiate` raises `ValueError` via `doc_integrity.py`; `/qor-plan` emits warnings during dialogue; `/qor-audit` emits drift-notice in audit report (non-VETO). (5) Failure-mode table (symptom -> which check catches it -> operator fix).

**`glossary.md` bootstrap**. Five entries using YAML-fence frontmatter:

```
\`\`\`yaml
term: Doctrine
definition: A canonical rule document in qor/references/ that skills cite as authority.
home: qor/references/README.md  # or the doctrine-documentation-integrity.md itself for self-reference
referenced_by: [CLAUDE.md, qor/gates/delegation-table.md]
introduced_in_plan: phase28-documentation-integrity
\`\`\`
```

Remaining bootstrap terms: `Doc Tier`, `Glossary Entry`, `Concept Home`, `Orphan Concept`. All self-reference `doctrine-documentation-integrity.md` as home.

**`plan.schema.json`** delta. Add to `properties`:

```json
"doc_tier": { "enum": ["minimal", "standard", "system", "legacy"] },
"terms": {
  "type": "array",
  "items": {
    "type": "object",
    "required": ["term", "home"],
    "properties": {
      "term": { "type": "string", "minLength": 1 },
      "home": { "type": "string", "minLength": 1 }
    }
  }
},
"boundaries": {
  "type": "object",
  "properties": {
    "limitations": { "type": "array", "items": { "type": "string" } },
    "non_goals":   { "type": "array", "items": { "type": "string" } },
    "exclusions":  { "type": "array", "items": { "type": "string" } }
  }
}
```

No new `required`. `additionalProperties: true` stays (existing plans unaffected).

**`doc_integrity.py`** structure. Module-level functions, no classes except a small `Entry` dataclass. Raises `ValueError` with operator-readable messages (per `changelog_stamp.py` idiom). No network, no subprocess, no mutation of files being checked. Idempotent.

### Unit Tests

- `test_doc_integrity.py`: 
  - `test_check_topology_minimal_raises_without_readme` - asserts `ValueError` when README missing.
  - `test_check_topology_standard_raises_without_glossary` - asserts standard-tier needs glossary.
  - `test_check_topology_system_raises_per_artifact` - parameterized over the four system artifacts.
  - `test_check_topology_legacy_no_op` - legacy tier never raises, regardless of files.
  - `test_check_glossary_raises_on_missing_term` - plan declares `Foo`, glossary has no entry -> raise.
  - `test_check_glossary_raises_on_empty_definition` - entry exists but `definition:` empty.
  - `test_check_glossary_raises_on_bad_home_path` - `home:` points to nonexistent file.
  - `test_check_orphans_raises_on_no_consumers` - entry has no `referenced_by` and was NOT `introduced_in_plan` this session.
  - `test_check_orphans_allows_new_term_with_plan_marker` - entry new in current session plan passes even without consumers yet.
- `test_plan_schema.py`:
  - `test_plan_schema_accepts_new_optional_fields` - plan artifact with `doc_tier`, `terms`, `boundaries` validates.
  - `test_plan_schema_accepts_absence_of_new_fields` - existing-shape plan still validates.
  - `test_plan_schema_rejects_invalid_doc_tier` - `doc_tier: "bogus"` fails enum.
- `test_glossary_parse.py`:
  - `test_parse_empty_glossary_ok` - no entries, no raise.
  - `test_parse_single_entry_round_trip` - entry -> `Entry(term=..., home=..., ...)` matches source.
  - `test_parse_malformed_yaml_raises_with_line_number` - operator-debuggable error.
  - `test_parse_duplicate_term_raises` - two entries same `term` field -> raise.
  - `test_parse_glossary_rejects_unsafe_tags` - YAML fence containing `!!python/object` (or any non-safe tag) raises; proves `yaml.safe_load` is in use, not `yaml.load`. Addresses SG-Phase24-B.
  - `test_yaml_safe_load_discipline_covers_doc_integrity` - after creation, verify `tests/test_yaml_safe_load_discipline.py`'s walk root includes `qor/scripts/doc_integrity.py`; widen the scanner in the same phase if it does not (SG-Phase25-A prevention).

Run tests at least twice consecutively before marking phase complete (CLAUDE.md test-discipline: confirm determinism).

## Phase 2: Plan-Skill Upgrade

Teach `/qor-plan` to dialogue about doc-integrity and record the declarations in the plan artifact. Warnings only; this phase adds *production* of doc-integrity metadata, not enforcement. Enforcement lands in Phase 3.

### Affected Files

- `qor/scripts/tests/test_plan_skill_wiring.py` - NEW (or extend existing); asserts Step Z payload writes include `doc_tier`, `terms`, `boundaries` when set.
- `qor/skills/sdlc/qor-plan/SKILL.md` - MODIFY; new Step 1b (doc-integrity dialogue), Plan Structure extension (top-matter block before Open Questions), Step Z payload additions, Constraints additions.
- `qor/skills/sdlc/qor-plan/references/step-extensions.md` - MODIFY; new "Step 1b" section with dialogue script + tier decision tree.
- `qor/references/doctrine-documentation-integrity.md` - MODIFY (from Phase 1); cross-link to the /qor-plan step that implements dialogue.

### Changes

**Plan structure extension**. Plans gain a top-matter block directly below `**change_class**:`:

```markdown
**doc_tier**: minimal | standard | system | legacy

**terms_introduced** (if any):
- term: TermName
  home: path/to/home.md

**boundaries**:
- limitations: [...]
- non_goals: [...]
- exclusions: [...]
```

Plans with `doc_tier: legacy` must include a rationale line (`**doc_tier_rationale**: ...`) that gets logged to shadow genome as severity-2 `doc_tier_legacy_declared` event.

**Step 1b (new)**: sits between Step 1 (collaborative dialogue) and Step 2 (research existing code). Dialogue script (one question at a time per skill constraint):

1. "What doc_tier applies? minimal / standard / system / legacy" - multiple-choice.
2. If minimal: skip remaining doc-integrity questions.
3. If standard/system: "Does this plan introduce any new terms (domain concepts, acronyms, canonical names)? If yes, list them."
4. "What are this feature's limitations? (things it cannot do)"
5. "What are its non-goals? (things it chooses not to do)"
6. "Any exclusions? (unsupported scenarios)"
7. If legacy: "Declare rationale for bypass; will be logged."

Dialogue warnings (not blockers):
- Tier absent from user response -> warn and default to `standard`.
- `system` tier declared but no `terms_introduced` -> warn ("system tier typically introduces concepts; continue?").
- `legacy` tier with no rationale -> warn and prompt again.

**Step Z payload** extension: plan.json now includes `doc_tier`, `terms`, `boundaries` when the plan declares them. Schema (Phase 1) accepts absence, so legacy-path plans continue to work during transition.

**Constraints additions** in `/qor-plan` SKILL.md:
- `ALWAYS` declare `doc_tier` in plan top-matter (warn if omitted; default `standard`).
- `ALWAYS` list new terms in `terms_introduced` when tier is standard or system.
- `NEVER` write the plan file without surfacing the tier decision to the operator.

### Unit Tests

- `test_plan_skill_wiring.py`:
  - `test_step_z_writes_doc_tier_when_declared` - mock plan with `doc_tier: standard` -> plan.json payload contains matching field.
  - `test_step_z_omits_doc_tier_when_undeclared` - backward-compat; no `doc_tier` in payload.
  - `test_step_z_writes_terms_array_format` - terms list serializes to schema shape.
  - `test_step_z_writes_boundaries_sub_object` - boundaries nested correctly.
  - `test_plan_legacy_tier_shadow_event_emitted` - declaring `legacy` appends shadow event with severity=2.
  - `test_plan_legacy_tier_rejected_without_rationale` - writing a plan artifact with `doc_tier: legacy` and no `doc_tier_rationale` raises `ValueError` at Step Z (mirrors `changelog_stamp.py` enforcement idiom). Addresses test-discipline Rule 4: Rule = Test.
- (No integration test of the dialogue itself; dialogue is operator-driven prose, not code under test. Unit tests target the writer and the shadow-event emitter.)

## Phase 3: Substantiate Enforcement + Audit Drift + Dogfood

Wire `doc_integrity.py` into `/qor-substantiate` as a hard-blocker. Add drift notice to `/qor-audit`. Then dogfood: fix this repo's own documented gaps using the upgraded skills. If the skills don't produce clean output against Qor-logic itself, iterate before marking phase complete.

### Affected Files

- `qor/scripts/tests/test_substantiate_doc_integrity.py` - NEW; asserts substantiate hard-blocks on violation.
- `qor/scripts/tests/test_audit_drift_notice.py` - NEW; asserts audit emits drift section without flipping verdict to VETO.
- `qor/scripts/tests/test_dogfood_glossary_coverage.py` - NEW; asserts Qor-logic's `glossary.md` (post-Phase-3 expansion) covers the terms the doctrine itself introduces plus the ones named in GAP-REPO-02.
- `qor/skills/governance/qor-substantiate/SKILL.md` - MODIFY; new Step 4.7 (Documentation Integrity Check) between Step 4.6 (Reliability Sweep) and Step 5 (Razor Check). ABORT on `ValueError`.
- `qor/skills/governance/qor-audit/SKILL.md` - MODIFY; new "Documentation Drift" pass after "Orphan Detection" but before Step 4 verdict. Non-VETO; produces a `## Documentation Drift` section in the audit report.
- `qor/skills/governance/qor-audit/references/qor-audit-templates.md` - MODIFY; template additions for the drift section.
- `qor/references/glossary.md` - MODIFY; expand with Qor-logic canonical terms. Minimum coverage to close GAP-REPO-02/03/04: `Phase (SDLC)`, `Phase (skill step)`, `Phase (execution stage)` (disambiguation; three distinct entries), `Gate`, `Gate Artifact`, `Shadow Genome`, `Process Shadow Genome` (or declare alias), `change_class`, `Governor`, `Judge`, `Substantiate`, `Seal`, `Workflow Bundle`, `Session`, `Delegation Table`, `Complecting`, `Ledger`, `Doctrine` (cross-ref Phase 1 bootstrap).
- `qor/gates/workflow-bundles.md` - MODIFY line 23; update example `phases` to match canonical `chain.md` order, OR add a comment distinguishing example-bundle from canonical-chain (closes GAP-REPO-01).
- `qor/gates/delegation-table.md` - MODIFY if needed; cross-link doctrine-documentation-integrity from the /qor-plan and /qor-substantiate rows.

### Changes

**Substantiate Step 4.7 (Documentation Integrity Check)**. Reads plan artifact (`.qor/gates/<session>/plan.json`), extracts `doc_tier`, `terms`, and calls `doc_integrity` functions in sequence:

```python
import doc_integrity
# Load plan artifact to get tier + declared terms.
plan_artifact = gate_chain.read_phase_artifact("plan", session_id=sid)
tier = plan_artifact.get("doc_tier", "legacy")  # absence -> legacy bypass
if tier == "legacy":
    # Skip all checks. Rationale already logged at plan time.
    pass
else:
    doc_integrity.check_topology(tier, repo_root=".")
    declared_terms = [t["term"] for t in plan_artifact.get("terms", [])]
    doc_integrity.check_glossary(
        glossary_path="qor/references/glossary.md",
        declared_terms=declared_terms,
    )
    doc_integrity.check_orphans(
        glossary_path="qor/references/glossary.md",
        current_session_plan_tag="phase28-documentation-integrity",  # from plan frontmatter
    )
```

Any raised `ValueError` ABORTs substantiation per SKILL.md fail-fast-only block. Operator fixes and re-runs. No silent override; no retry-with-waiver path.

**Audit "Documentation Drift" pass**. After Orphan Detection (line ~208 of qor-audit SKILL.md), add:

```markdown
#### Documentation Drift

Scan plan artifact and glossary for consistency issues. Non-VETO.

- [ ] Plan-declared terms all have glossary entries (warn if missing)
- [ ] Glossary entries `home` paths resolve (warn if broken)
- [ ] No duplicate term definitions across glossary (warn)

Output under `## Documentation Drift` in AUDIT_REPORT.md. Warnings do not flip verdict; they inform the Governor about hygiene to address in a follow-on plan.
```

Implementation invokes same `doc_integrity` functions but in `warn_mode=True` (new kwarg added in Phase 1 tests).

**Dogfood expansion of glossary.md** addresses:
- GAP-REPO-02 (Phase ambiguity) via three distinct entries: `Phase (SDLC)`, `Phase (skill step)`, `Phase (execution stage)`.
- GAP-REPO-03 (no glossary) by existing at canonical path.
- GAP-REPO-04 (Shadow Genome split) by declaring Shadow Genome home = `qor/references/doctrine-shadow-genome-countermeasures.md` and listing `docs/SHADOW_GENOME.md` and runtime-event stores as `referenced_by:` entries. One home, multiple consumers.

**GAP-REPO-01 fix** (`workflow-bundles.md:23`). Replace example `phases: [research, plan, audit, implement, substantiate]` with canonical-matching example `phases: [research, plan, audit, implement, substantiate, validate, remediate]` OR add inline comment explaining the example is truncated for brevity. Lean toward full list; removes ambiguity.

**Sequencing note**: Phase 3 deliverables land in order (tests first, then substantiate hook, then audit hook, then glossary expansion, then workflow-bundles fix). Running this phase's own substantiation exercises Step 4.7 on the plan itself - the plan declares `doc_tier: system`, introduces terms (`Doc Tier`, `Glossary Entry`, etc.) declared in the `terms_introduced` block of this very file. If the glossary expansion is incomplete at substantiate time, the substantiate ABORTs and we iterate.

### Unit Tests

- `test_substantiate_doc_integrity.py`:
  - `test_substantiate_aborts_on_missing_topology` - system-tier plan, missing architecture.md -> ABORT signal.
  - `test_substantiate_aborts_on_undeclared_term_usage` - plan declared `terms: [Foo]`, glossary lacks `Foo` -> ABORT.
  - `test_substantiate_passes_legacy_tier` - legacy tier bypasses checks cleanly.
  - `test_substantiate_reads_plan_tier_from_artifact` - verifies the integration with `gate_chain.read_phase_artifact`.
  - `test_substantiate_does_not_retry_silently` - single `ValueError` aborts; does not re-run with degraded checks.
- `test_audit_drift_notice.py`:
  - `test_audit_emits_drift_section_on_missing_term` - audit report contains `## Documentation Drift` with specific complaint.
  - `test_audit_does_not_veto_on_drift_alone` - verdict remains PASS when only drift violations present; other passes drive verdict.
  - `test_audit_drift_section_absent_when_clean` - no section emitted when glossary is clean.
- `test_dogfood_glossary_coverage.py`:
  - `test_phase_term_disambiguated` - glossary has three distinct `Phase (*)` entries.
  - `test_shadow_genome_single_home` - `Shadow Genome` entry declares a single `home` with `doctrine-shadow-genome-countermeasures.md`.
  - `test_workflow_bundles_canonical_phases_present` - `workflow-bundles.md:23` (or wherever the example sits) names `validate` and `remediate`.
  - `test_doctrine_bootstrap_terms_have_entries` - the five Phase-1 bootstrap terms exist in the expanded glossary.
  - `test_doctrine_self_substantiates` - run `doc_integrity.check_topology('system', '.')`, `check_glossary(...)`, `check_orphans(...)` against the repo AT TEST TIME; no `ValueError`. This is the dogfood assertion.

## CI Commands

Validate this plan's deliverables via:

- `python -m pytest qor/scripts/tests/test_doc_integrity.py -v --count=2` (run twice for determinism per test-discipline doctrine).
- `python -m pytest qor/scripts/tests/test_plan_schema.py qor/scripts/tests/test_glossary_parse.py -v`
- `python -m pytest qor/scripts/tests/test_plan_skill_wiring.py -v`
- `python -m pytest qor/scripts/tests/test_substantiate_doc_integrity.py qor/scripts/tests/test_audit_drift_notice.py qor/scripts/tests/test_dogfood_glossary_coverage.py -v`
- `python qor/reliability/skill-admission.py qor-substantiate` (sanity-check substantiate SKILL.md still admits after Step 4.7 insertion).
- `python qor/reliability/gate-skill-matrix.py` (sanity-check no broken handoffs after doctrine cross-links added).
- `python -c "import sys; sys.path.insert(0, 'qor/scripts'); import doc_integrity; doc_integrity.check_topology('system', '.'); doc_integrity.check_glossary('qor/references/glossary.md', []); doc_integrity.check_orphans('qor/references/glossary.md', 'phase28-documentation-integrity')"` (manual dogfood against this repo; Phase 3 deliverable - must not raise).

Each phase's tests must pass on two consecutive runs before the phase is marked complete (CLAUDE.md test-discipline).

## Self-Dogfood

Per SG-Phase28-A (doctrine-introduction plans must self-apply the rules they introduce):

- **`doc_tier` declaration satisfied**: plan top-matter declares `**doc_tier**: standard` (amended at substantiate time from `system`; see `doc_tier_downgrade_note` on line 7). Evidence: line 5.
- **Terms introduced block satisfied**: plan declares five terms with explicit `home:` paths pointing to `doctrine-documentation-integrity.md`.
- **Boundaries block satisfied**: `limitations`, `non_goals`, `exclusions` each populated with non-empty bullets.
- **Every new rule has a test**:
  - Rule "plans declare `doc_tier`" -> `test_step_z_writes_doc_tier_when_declared`.
  - Rule "legacy tier requires rationale" -> `test_plan_legacy_tier_rejected_without_rationale` (Phase 2).
  - Rule "glossary uses `yaml.safe_load`" -> `test_parse_glossary_rejects_unsafe_tags` (Phase 1).
  - Rule "every declared term has matching glossary entry" -> `test_check_glossary_raises_on_missing_term` (Phase 1).
  - Rule "every glossary `home` resolves" -> `test_check_glossary_raises_on_bad_home_path` (Phase 1).
  - Rule "substantiate blocks on violation" -> `test_substantiate_aborts_on_*` (Phase 3).
- **Enumeration cross-check**: the five bootstrap glossary terms named in Phase 1 Changes (`Doctrine`, `Doc Tier`, `Glossary Entry`, `Concept Home`, `Orphan Concept`) match the plan's `terms_introduced` block exactly (modulo `Doctrine` which is pre-existing and therefore belongs to the bootstrap set, not the new-terms set -- `Doc Integrity Check Surface` is the fifth new term introduced by this plan). Cross-check: bootstrap set = {Doctrine, Doc Tier, Glossary Entry, Concept Home, Orphan Concept}; terms_introduced set = {Doc Tier, Glossary Entry, Concept Home, Orphan Concept, Doc Integrity Check Surface}. Intersection = 4 terms shared; `Doctrine` is pre-existing foundational; `Doc Integrity Check Surface` is new in this plan.
- **No bare-word YAML/TOML/JSON** appears in this plan without naming the safe loader. `yaml.safe_load` is cited in Phase 1 `doc_integrity.py` bullet.

## Delegation

Per `qor/gates/delegation-table.md`:

- Plan complete -> `/qor-audit` (next phase).
- Phase 1 or 3 reveals that `doc_integrity.py` needs to live elsewhere (e.g., under a new `qor/integrity/` module rather than `qor/scripts/`) -> halt and invoke `/qor-organize` before continuing. Do not inline a reorganization.
- Open Question #3 flips to "defer dogfood" mid-implementation -> re-open dialogue via `/qor-plan`; do not silently drop Phase 3 deliverables.
