# Doctrine: Hierarchical Governance Index

> A single authoritative map of every governance artifact, tiered by freshness.
> One incorrect governance value can cascade into failures; the index makes
> drift mechanically visible.

## Governance Index

The **Governance Index** (`docs/GOVERNANCE_INDEX.md`) maps every governance
artifact in a Qor project to exactly one **Governance Freshness Tier**. It is a
Tier 1 canonical doc itself, so a stale index fails the next cycle's Tier 1
check — the index is self-policing.

## Governance Freshness Tier

Every governance artifact belongs to exactly one of six tiers:

| Tier | Name | Freshness contract | Drift signal |
|------|------|--------------------|--------------|
| 1 | Canonical Source | MUST be current at every cycle close | wrong version / wrong state / missing recent entries |
| 2 | Doctrine & Policy | stable; changes are explicit doctrine events | rules contradict each other or operator memory |
| 3 | Active Initiative | live until close; ages out at substantiate | shipped feature still tracked as pending |
| 4 | Per-Plan Artifact | live for plan duration; archived at substantiate | plan shipped but artifact still presents as open |
| 5 | Reference Material | informational, slow-drift | factual claims diverge from current code |
| 6 | Archived | frozen historical record | none (frozen) |

## Governance Index Drift

**Governance Index Drift** is any divergence between the index and reality. V1
ships a WARN-only checker (`python -m qor.scripts.governance_index`) detecting:

- `stale-tier1`: the index's `Last Reviewed` date predates the newest sealed
  `META_LEDGER` entry.
- `unregistered`: a governance doc on disk that no tier table names.
- `missing-index`: the index file is absent (legal next: `qor-logic seed`).

`/qor-status` surfaces a one-line drift indicator. The checker reuses the Phase
109 governance-health required-artifact registry as the default governance set
(no `paths.governance` config knob in V1).

## Drift-detection contract (full; V2 enforcement deferred)

Every cycle that writes governance SHOULD:

1. Verify Tier 1 freshness against the latest sealed ledger entry.
2. Register new artifacts in the appropriate tier in the same commit.
3. Move Tier 3 -> Tier 6 at seal (archive session-scoped artifacts).
4. Move Tier 4 -> Tier 6 at seal (archive plan + its phase reports).
5. Refresh `Last Reviewed`.

**V2 (Phase 120; GH #149) — shipped enforcement**: `/qor-substantiate` Step 4.7.5 makes the index self-policing — it **auto-advances `Last Reviewed`** to the seal date (clearing `stale-tier1` by construction) and then **fail-closes** (`|| ABORT`) on residual drift: `unregistered` (a governance doc in no tier — rule 2) and the forward-guard `tier3-unarchived` (a Tier 3 "Active Initiative" row naming a `phase <N>` already SESSION-SEALed — rules 3/4 as a detection guard rather than auto-mutation). `/qor-validate` runs `cross_check_index_against_ledger` (read-only): `stale-tier1` (Last Reviewed vs latest sealed entry) + `tier3-unarchived`. Both use `qor-logic governance-index` (`--advance-last-reviewed`/`--enforce`/`--cross-check-ledger`); absent index records a Phase 75 disclosed-skip (`gate_skipped_prerequisite_absent`) rather than aborting. Implementation: `qor/scripts/governance_index.py` (`advance_last_reviewed`, `enforce_at_seal`, `cross_check_index_against_ledger`).

**Still deferred**: a hard `/qor-implement` block on stale Tier 1, and automatic Tier 3->6 / Tier 4->6 *row mutation* (the shipped V2 detects unarchived rows but does not rewrite tier tables). V1 remains the scaffold + WARN-only `/qor-status` visibility surface (`check_index_drift`, untouched).

Maps to NIST AI RMF MAP-3.1 (trust anchor integrity) and EU AI Act Art. 12
(record-keeping integrity). Originating proposal: GH #140 (a sibling repository's 21-stale-doc
recurrence).
