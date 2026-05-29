# Governance Index

**Last Reviewed**: 2026-05-29

A single authoritative map of every governance artifact in Qor-logic, organized
into six freshness tiers with explicit drift contracts. A stale entry here is
itself a Tier 1 drift bug, so the index is self-policing. See
`qor/references/doctrine-governance-index.md` for the model and contracts.

## Tier 1 — Canonical Source

MUST be current at every cycle close. Drift signal: wrong version / wrong state / missing recent entries.

| Artifact | Path | Freshness marker |
|----------|------|------------------|
| Meta Ledger | `docs/META_LEDGER.md` | latest sealed entry |
| System State | `docs/SYSTEM_STATE.md` | latest phase snapshot |
| Concept | `docs/CONCEPT.md` | stable |
| Architecture Plan | `docs/ARCHITECTURE_PLAN.md` | stable |
| Shadow Genome | `docs/SHADOW_GENOME.md` | open failures current |
| Backlog | `docs/BACKLOG.md` | open items current |
| Feature Index | `docs/FEATURE_INDEX.md` | every feature has a test |
| Changelog | `CHANGELOG.md` | latest release stamped |
| README | `README.md` | badges current |

## Tier 2 — Doctrine & Policy

Stable; changes are explicit doctrine events. Drift signal: rules contradict each other or operator memory.

| Artifact | Path |
|----------|------|
| Shadow-genome countermeasures | `qor/references/doctrine-shadow-genome-countermeasures.md` |
| Governance enforcement | `qor/references/doctrine-governance-enforcement.md` |
| Prompt resilience | `qor/references/doctrine-prompt-resilience.md` |
| Governance index | `qor/references/doctrine-governance-index.md` |
| Glossary | `qor/references/glossary.md` |
| Operator drop-in | `CLAUDE.md` |
| Contributor guide | `CONTRIBUTING.md` |
| Attribution policy | `ATTRIBUTION.md` |

## Tier 3 — Active Initiative

Live until close; ages out at substantiate. Drift signal: shipped feature still tracked as pending.

| Artifact | Path | Opened |
|----------|------|--------|
| _none open_ | `.qor/session/` | n/a |

## Tier 4 — Per-Plan Artifact

Live for plan duration; archived at substantiate. Drift signal: plan shipped but artifact still presents as open.

| Artifact | Path | Plan |
|----------|------|------|
| Plans (all) | `docs/plan-*.md` | per-phase / legacy |

## Tier 5 — Reference Material

Informational, slow-drift. Drift signal: factual claims diverge from current code.

| Artifact | Path |
|----------|------|
| Doctrine references | `qor/references/*.md` |
| Process notes | `docs/PROCESS_*.md` |
| System-tier docs | `docs/architecture.md`, `docs/lifecycle.md`, `docs/operations.md`, `docs/policies.md` |
| Research briefs | `docs/research-brief-*.md`, `docs/RESEARCH_BRIEF.md` |
| Roadmaps | `docs/roadmap-*.md` |
| Audits & compliance | `docs/*-audit-*.md`, `docs/security-audit-*.md`, `docs/compliance-*.md` |
| Reconciliation & drift triage | `docs/reconciliation-*.md`, `docs/phase*.md` |
| Cluster memos | `docs/cluster-*.md` |
| Skill registry & audits | `docs/SKILL_*.md`, `docs/SHIELD_*.md` |
| Guides | `docs/MERKLE_ITERATION_GUIDE.md`, `docs/hooks-install.md` |

## Tier 6 — Archived

Frozen historical record. Drift signal: none (frozen).

| Archive | Path |
|---------|------|
| Historical docs | `docs/archive/` |

## How to add a governance artifact

1. Create the file in the same commit that registers it here.
2. Add a row to the tier whose freshness contract matches the file's lifecycle.
3. Refresh **Last Reviewed** above.

## How to retire a governance artifact

1. Move the file to the Tier 6 archive path.
2. Move its row from its live tier to Tier 6 (or delete it if superseded).
3. Refresh **Last Reviewed** above.
