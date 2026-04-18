# Qor-logic Glossary

Canonical term registry. Each entry is a YAML fence with required fields
`term`, `definition`, `home`; optional `aliases`, `referenced_by`,
`introduced_in_plan`. Parsed by `qor/scripts/doc_integrity.py` using
`yaml.safe_load`.

An entry is simultaneously a term definition AND a concept map entry: `home:`
names the authoritative file for the concept; `referenced_by:` names the
consumers. No separate concept-map artifact exists.

Phase 28 bootstrap scope: five foundational terms. Full Qor-logic terminology
(`Phase`, `Gate`, `Shadow Genome`, etc.) lands in Phase 3 dogfood expansion.

---

```yaml
term: Doctrine
definition: A canonical rule document in qor/references/ that skills cite as authority. Doctrines are binding on the phases that cite them; they evolve through plans, not ad-hoc edits.
home: qor/references/doctrine-documentation-integrity.md
referenced_by:
  - CLAUDE.md
  - qor/gates/delegation-table.md
  - qor/skills/sdlc/qor-plan/SKILL.md
  - CONTRIBUTING.md
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Doc Tier
definition: A per-plan declaration (minimal, standard, system, or legacy) that selects which documentation artifacts are required at substantiate time.
home: qor/references/doctrine-documentation-integrity.md
aliases:
  - doc_tier
referenced_by:
  - qor/skills/sdlc/qor-plan/SKILL.md
  - qor/gates/schema/plan.schema.json
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Glossary Entry
definition: A YAML-fence record in qor/references/glossary.md defining one canonical term and naming its concept home.
home: qor/references/doctrine-documentation-integrity.md
referenced_by:
  - qor/scripts/doc_integrity.py
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Concept Home
definition: The file path where a concept is canonically defined. Every glossary entry declares its home; orphan detection verifies the path resolves.
home: qor/references/doctrine-documentation-integrity.md
referenced_by:
  - qor/references/glossary.md
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Orphan Concept
definition: A glossary entry with no referenced_by consumers that was not introduced in the current session's plan. Detected by check_orphans and raises at substantiate time.
home: qor/references/doctrine-documentation-integrity.md
referenced_by:
  - qor/scripts/doc_integrity.py
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Doc Integrity Check Surface
definition: The three checks performed by doc_integrity.py at substantiate time -- topology presence, glossary hygiene, orphan scan. Term-drift grep (D) and cross-doc conflict detection (E) are documented as out-of-scope extensions.
home: qor/references/doctrine-documentation-integrity.md
referenced_by:
  - qor/references/doctrine-documentation-integrity.md
introduced_in_plan: phase28-documentation-integrity
```

## Qor-logic canonical terms (Phase 28 Phase 3 dogfood expansion)

Closes GAP-REPO-02/03/04 from `RESEARCH_BRIEF.md`: the three-way "Phase" ambiguity, the missing glossary, and the Shadow Genome three-way split.

```yaml
term: Phase (SDLC)
definition: One stage in the governance lifecycle -- research, plan, audit, implement, substantiate, validate, or remediate. Governed by qor/gates/chain.md. Not to be confused with skill-step "Phase N" (plan-internal structure) or execution-stage labels like TDD / BUILD / CLEANUP.
home: qor/gates/chain.md
referenced_by:
  - CLAUDE.md
  - qor/gates/delegation-table.md
  - docs/META_LEDGER.md
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Gate
definition: A prior-phase artifact check at the boundary between two SDLC phases. Implemented by gate_chain.check_prior_artifact; override permitted but logged as severity-1 shadow event.
home: qor/gates/chain.md
aliases:
  - Gate Artifact
referenced_by:
  - qor/skills/sdlc/qor-plan/SKILL.md
  - qor/skills/governance/qor-audit/SKILL.md
  - qor/skills/governance/qor-substantiate/SKILL.md
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Shadow Genome
definition: The event-logging substrate for governance-relevant observations (gate overrides, capability shortfalls, degradations, repeated-VETO patterns). Structured events live in JSONL under qor/dist/.shadow/; narrative patterns with countermeasures live in this doctrine file.
home: qor/references/doctrine-shadow-genome-countermeasures.md
aliases:
  - Process Shadow Genome
referenced_by:
  - docs/SHADOW_GENOME.md
  - qor/scripts/shadow_process.py
  - qor/skills/governance/qor-audit/SKILL.md
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Substantiate
definition: The final governance phase that verifies Reality equals Promise, bumps version, stamps changelog, and produces the session's Merkle seal.
home: qor/skills/governance/qor-substantiate/SKILL.md
aliases:
  - Seal
referenced_by:
  - qor/gates/chain.md
  - qor/references/doctrine-governance-enforcement.md
  - docs/META_LEDGER.md
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Workflow Bundle
definition: A meta-skill that orchestrates a sequence of single-purpose skills under one trigger, with declared checkpoints and a budget for graceful abort.
home: qor/gates/workflow-bundles.md
referenced_by:
  - CLAUDE.md
  - qor/skills/meta/qor-deep-audit/SKILL.md
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: change_class
definition: A per-plan declaration of version impact -- hotfix, feature, or breaking. Governs the version bump performed at substantiate time by governance_helpers.bump_version.
home: qor/references/doctrine-governance-enforcement.md
referenced_by:
  - CLAUDE.md
  - qor/skills/sdlc/qor-plan/SKILL.md
  - qor/skills/governance/qor-substantiate/SKILL.md
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Delegation Table
definition: The single source of truth for cross-skill handoffs. Skills name their successor skill explicitly per the table, never invent routing inline.
home: qor/gates/delegation-table.md
referenced_by:
  - CLAUDE.md
  - qor/references/doctrine-audit-report-language.md
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Complecting
definition: Rich Hickey's term for braiding independent concerns together (state with time, data with behavior, config with code). Qor-logic's /qor-plan skill treats complecting as a design smell to detect and unwind.
home: qor/skills/sdlc/qor-plan/SKILL.md
referenced_by:
  - qor/skills/sdlc/qor-plan/SKILL.md
introduced_in_plan: phase28-documentation-integrity
```

