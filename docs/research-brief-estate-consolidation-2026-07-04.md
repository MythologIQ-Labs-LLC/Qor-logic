# Research Brief: Estate Consolidation (GH #252)

**Date**: 2026-07-04
**Analyst**: The Qor-logic Analyst
**Target**: GH #252 -- absorb estate-proven capabilities into the dist (perspective-reset rec 6; final series item)
**Scope**: the three named capabilities, absorption reality-check, honest slicing

---

## Executive Summary

The issue's premise is one-third right. Of the three named capabilities, only the **ledger migration tool** actually exists as absorbable code: a sibling governance repository's `scripts/migrate_ledger_v0_14.py` (230 lines) normalizes three legacy hash-markup formats (inline backticks; fenced blocks; session-seal labels) into the canonical form, writing to a NEW file (`--output`, input untouched) with chain-math validated on write against both the modern `SHA256(content + "|" + prev)` and legacy no-separator formulas -- the exact variance Qor-logic's own verifier tolerates read-only (`legacy_chain_hash`, ledger_hash.py:39-46) and the reason our own verify output reports "Skipped 32 entries with non-verifiable markup" (:435). The **public-repo mirroring** is DESIGN-ONLY upstream: a sibling repository's PUBLIC_REPO_GOVERNANCE_AGGREGATION.md explicitly gates execution on five unresolved maintainer decisions (auth model; intake mode; sync trigger; key provisioning/rotation; retention) and no workflow or collector exists anywhere -- there is nothing to absorb, only a design to build after the operator resolves those decisions. The **SQLite ledger adapter** is already distributed via a sibling repository's package (schema v26, 15 data + 9 edge tables, JSONL import/export with strong test coverage) -- absorbing it would duplicate a maintained distribution.

## Findings

1. **Migration tool mechanics** (a sibling repository's scripts/migrate_ledger_v0_14.py): 13 regex patterns across the three formats (:34-66); extract -> strip legacy markup -> inject canonical block (:69-124); never in-place (:198-201); chain-math checked with both formulas, mismatches REPORTED not rejected (:150-161). Gaps to close on absorption: no `--dry-run` (Phase 167 house discipline), no idempotence guarantee, exit 0 unconditionally. Qor-logic value: normalizing the 32 non-verifiable legacy entries in our own ledger (operator decision to apply; the tool never mutates in place).
2. **Mirroring is unbuilt by design**: GOVERNANCE_DOC_TRACKING_PROPAGATION.md:103-115 -- "Execution gate: design-only. No Secrets, tokens, GitHub App, governance-mirror/ directory, CI workflow... until maintainers sign off." The five open decisions (PUBLIC_REPO_GOVERNANCE_AGGREGATION.md:75-85) belong to the operator, cross-repo.
3. **SQLite adapter is a sibling repository's product**: adapters/ledger.py + cli/ledger_io.py (deterministic JSONL round-trips, `(table, created_at, id)` sort, versioned records) with 36 ledger test files. Qor-logic's honest role: document the interchange pointer, not re-ship.
4. **Landing seams in Qor-logic**: `qor/scripts/ledger_migrate.py` via the generic runner (Phase 164-169 precedent; no cli.py growth); templates ship via `qor/resources/templates/` + seed.py if the mirroring workflow ever lands. Known seed gotcha recorded upstream: `qor-logic seed` re-adds `.qor/session/` to gitignore even in tracked-`.qor` repos (GOVERNANCE_DOC_TRACKING_PROPAGATION.md:80).

## Recommendations (honest slicing)

1. **Phase 170 ships the absorbable third as code**: `qor/scripts/ledger_migrate.py` -- a sibling governance repository's transform re-homed with house discipline added: `--dry-run` (renders + reports, writes nothing), never-in-place preserved (`--output` required), idempotence (canonical input passes through byte-stable), exit 1 when unmigratable entries remain (reported, not silent), behavioral tests over all three legacy formats + round-trip verify (a migrated synthetic ledger goes from skipped to verified under `ledger_hash.verify`).
2. **Phase 170 documents the other two thirds**: a "Ledger interchange and estate patterns" section (via /qor-document) pointing SQLite work at a sibling repository's CLIs and recording the mirroring design's blocked-on-five-decisions state.
3. **#252 closes with the corrected premise recorded on the issue**: (a) absorbed as code; (b) nothing exists to absorb -- design decisions surfaced to the operator as follow-up; (c) deliberately not duplicated. This is a premise correction, not a half-measure: the two deferred items have recorded dispositions with named owners.
4. Applying the migration to Qor-logic's OWN ledger is explicitly out of scope (operator decision; L2 surface; the tool's never-in-place design makes the future application safe to rehearse).

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
