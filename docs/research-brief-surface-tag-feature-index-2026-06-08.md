# Research Brief

**Date**: 2026-06-08
**Analyst**: The Qor-logic Analyst
**Target**: GH #196 — per-feature `Surface` tag enforcement in the `/qor-substantiate` FEATURE_INDEX verification pass
**Scope**: How the change affects (1) qor-logic systems independently and (2) qor-logic in concert with the FailSafe application

---

## Executive Summary

GH #196 asks to extend the existing FEATURE_INDEX verification pass so that, *when a repo's `FEATURE_INDEX.md` declares a `Surface` column*, each non-`n/a` feature must also carry a `surface` value (and resolve its release). Grounded against source, the change is a **schema-optional, additive, WARN-first capability extension** — not a behavior change to any existing gate. The blast radius on qor-logic *itself* is effectively zero today: qor-logic's own repo has **no `FEATURE_INDEX.md`** (confirmed: `ls docs/FEATURE_INDEX.md` → absent; `governance-health` → `MISSING`), so it disclosed-skips the entire pass and a fortiori the new sub-check. The change is therefore a pure **framework capability** that only bites in consumer repos (FailSafe) that adopt both the index and the column. The data is FailSafe's (FailSafe#206); the gate is qor-logic's. Two latent issues surfaced: (a) a classification drift between `governance_health` (treats `FEATURE_INDEX.md` as *required*) and `doctrine-feature-inventory.md` (declares it *optional*), and (b) a V1→V2 sequencing contract that must hold across the two repos to avoid breaking FailSafe's seal.

## Findings

### Implementation surface (what code/docs the change touches)

- **Gate logic**: `qor/scripts/feature_index_verify.py` — `parse_index_rows()` (`qor/scripts/feature_index_verify.py:37`), `tally()` (`:79`), `IndexSummary` (`:27`), `main()` ABORT/`--warn-only`/`--override` (`:130`). The parser is **header-driven**: it lowercases the header row and zips header names to cells (`qor/scripts/feature_index_verify.py:55`–`:62`). It already tolerates extra trailing columns (`:60` `if len(cells) < len(header): continue`). **Consequence**: a `Surface` column becomes available as `row.get("surface")` with *no parser change* required to read it; the new V1 work is a presence lint over that key, not a parse-engine change.
- **Skill wiring**: `qor/skills/governance/qor-substantiate/SKILL.md:360`–`:375` ("FEATURE_INDEX verification pass (Phase 73 wiring; GH #40)"). The new sub-check slots in as steps 1–6 already enumerate test-path/invocation/pass + the regression ABORT.
- **Schema**: `qor/gates/schema/feature_index.schema.json` has `"additionalProperties": false` (`:7`). Adding a governed `surface` property **requires a schema edit** or programmatic row-validators reject any row carrying it. This is a coupled V1 change.
- **Worked example**: `qor/templates/FEATURE_INDEX.example.md` — must gain a `Surface` column to remain a valid demonstration once the doctrine documents it (pinned by `tests/test_feature_index_example_template.py`).
- **Doctrine**: `qor/references/doctrine-feature-inventory.md` defines the canonical 6-column format (`:11`) and the status enum; it already reserves V2 column extensions (`:15` "status: deprecated (V2 extension)"). `Surface` is naturally documented there as an optional 7th column.

### qor-logic independent effects

- **Zero effect on qor-logic's own seal.** qor-logic has not adopted FEATURE_INDEX (no `docs/FEATURE_INDEX.md`). The pass disclosed-skips (`feature_index: skip`, exit 0 — `qor/scripts/feature_index_verify.py:154`–`:156`). The Surface sub-check is doubly gated (index must exist AND declare a `Surface` column), so neither condition holds. qor-logic ships the gate without exercising it on itself — the same posture `feature_index_verify` already has as a framework tool for consumers.
- **Additive, not breaking, for existing adopters.** The "schema-optional SKIP" requirement means an adopter whose header has no `surface` key must continue to PASS unchanged: print `SKIP` + emit `gate_skipped_prerequisite_absent` + exit 0. That disclosed-skip event is an already-tested contract (`tests/test_shadow_event_gate_skipped_prerequisite_absent.py`; enumerated in `qor/gates/schema/shadow_event.schema.json`) and matches the Phase 75 declarative-tolerance convention used across the gate ladder.
- **WARN-first V1 has two copy-ready precedents.** `qor/scripts/dod_check.py` (severity always `warn`, `main()` exits 0 even with findings — `qor/scripts/dod_check.py:14`–`:18`) and `qor/scripts/procedural_fidelity.py` (severity-2 events appended to the Process Shadow Genome, no abort). The new lint should mirror: append a severity-2 shadow event, exit 0, add one entry to `qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md`.
- **V2 promotion is a known ladder move.** Removing the `|| true` (fail-closed) is the same maneuver already executed twice: `feature_index_verify` itself went WARN→fail-closed (Phase 114→122, GH #155) and `merge_velocity_check` went WARN→fail-closed (Phase 93→129, GH #153). The `--override` logged-escape (`qor/scripts/feature_index_verify.py:168`–`:183`) is the template for the V2 accepted-exception path.
- **Coupled test + doc-integrity work (per project memory).** Introducing a "Surface" concept adds a glossary term and `referenced_by` wiring; per the Phase 135 lesson, doc_integrity term-drift fails if a new reference is added without glossary wiring. Tests to extend: `tests/test_feature_index_verify_helper.py`, `tests/test_feature_index_verify_gate.py`, `tests/test_feature_index_abort.py`, `tests/test_feature_index_example_template.py`, plus a new schema test for the `surface` property. TDD-first per CLAUDE.md (failing test before code; "schema-optional SKIP" path tested both ways).

### FailSafe interaction effects

- **Split ownership, classic enforce-here / supply-there.** The Surface *data* is FailSafe's (FailSafe#206 adds the column to FailSafe-side `FEATURE_INDEX.md`); the *gate* is qor-logic's (`/qor-substantiate` is a SHIELD skill owned here, consumed by FailSafe). No runtime API coupling exists — the gate reads FailSafe's markdown; no FailSafe code calls qor-logic. The contract is purely the FEATURE_INDEX markdown format plus the gate's expectations.
- **Enforcement only bites when both land.** Until qor-logic ships the check, FailSafe's `Surface` column is ungoverned free-text the parser tolerates as an extra trailing column. The benign window is FailSafe-ships-first (WARN-only anyway). The dangerous window is the reverse at V2: if qor-logic flips **fail-closed before FailSafe populates every non-`n/a` row**, FailSafe's seal breaks. Hence WARN-first is the correct rollout, and **FailSafe must reach full surface-column coverage before qor-logic promotes V2** — the same half-measure-vs-V2 ladder discipline already in play across the cluster, here intentional (consumer adoption runway), not a deferred half-measure.
- **The net-new governed datum is narrow.** The motivating use-case is FailSafe's Development Tracker projecting per-surface lifecycle progress from FEATURE_INDEX + META_LEDGER; the "got it wrong twice" pain was that surface↔feature↔release was never governed at seal time. Of the issue's two asks, the **release** half is largely already resolvable (verification status + ledger linkage); the genuinely new governed field is **surface**. So V1's enforcement reduces to "surface-tag presence on non-`n/a` rows."
- **Version contract.** The check ships in a qor-logic release; a new gate capability is `change_class: minor` per the governance flow. FailSafe must upgrade/pin to that qor-logic version to receive enforcement. No force-coupling — adoption is pull-based.

### Latent issue surfaced (pre-existing, intersects #196)

- **`governance_health` vs doctrine classification drift.** `qor-logic governance-health --profile skill-entry` reports `docs/FEATURE_INDEX.md` as `MISSING` — "required non-scaffold artifact absent → /qor-remediate". But `doctrine-feature-inventory.md:50`–`:52` ("Repos without a FEATURE_INDEX") declares the artifact **optional** at framework level, with `tally()` returning `missing_index=True` and the seal proceeding. `/qor-substantiate` treats absence as a disclosed-skip; `governance_health` treats it as a required-artifact failure. This predates #196 but #196's "schema-optional SKIP" framing assumes the optional reading. The two should be reconciled (most likely: `governance_health` should treat FEATURE_INDEX as optional/advisory, matching doctrine).

## Blueprint Alignment

| Blueprint Claim | Actual Finding | Status |
|----------------|---------------|--------|
| ARCHITECTURE_PLAN.md describes the FEATURE_INDEX subsystem | No match for `feature.index` / `surface` / `verification pass` in `docs/ARCHITECTURE_PLAN.md`; the canonical spec is `qor/references/doctrine-feature-inventory.md`, a doctrine-level artifact | NO BLUEPRINT CLAIM (no drift) |
| FEATURE_INDEX is optional at framework level | `doctrine-feature-inventory.md:50` confirms optional; `feature_index_verify.py:154` skips when absent | MATCH |
| FEATURE_INDEX absence is a clean skip everywhere | `governance_health` classifies it `MISSING`/required → /qor-remediate | DRIFT (governance_health vs doctrine) |
| Parser requires a fixed column set | Parser is header-driven and tolerates extra columns (`feature_index_verify.py:55`–`:62`) | MATCH (additive-safe) |
| `additionalProperties: false` blocks an unschema'd `surface` field | `feature_index.schema.json:7` confirms; schema edit required for governed surface | MATCH (coupled change) |

## Recommendations

1. **(High) Ship V1 as schema-optional WARN-only.** Lint `row.get("surface")` presence on non-`n/a` rows *only when the header declares a `Surface` column*; absent column → `SKIP` + `gate_skipped_prerequisite_absent` + exit 0. Append severity-2 shadow events; never abort. Model on `dod_check.py` / `procedural_fidelity.py`.
2. **(High, coupled) Edit `feature_index.schema.json`** to add an optional `surface` property in the same change, or programmatic validators reject surface-bearing rows under `additionalProperties: false`.
3. **(High) TDD-first per CLAUDE.md.** Failing tests before code, covering: header-has-surface + row-missing-surface → WARN event; header-has-surface + all-rows-tagged → clean; header-lacks-surface → SKIP (disclosed-skip event); schema accepts/omits `surface`. Run twice for determinism.
4. **(Medium) Document `Surface` as an optional 7th column** in `doctrine-feature-inventory.md` (V2-extension subsection), update `FEATURE_INDEX.example.md`, and wire the new glossary term's `referenced_by` to avoid doc_integrity term-drift (Phase 135 lesson).
5. **(Medium) Add a seal-gate-ladder.md entry** for the new sub-check with WARN→V2 fail-closed rationale, mirroring the `feature_index_verify` Phase 114→122 promotion note.
6. **(Medium, cross-repo) Gate V2 promotion on FailSafe coverage.** Do not remove the `|| true` until FailSafe#206 reports 100% surface-tag coverage on non-`n/a` rows; otherwise FailSafe's seal breaks.
7. **(Low, separable) File a follow-on** to reconcile the `governance_health` "FEATURE_INDEX required" vs doctrine "optional" drift — out of scope for #196 but adjacent; do not fold it into this phase.

## Updated Knowledge

Added to `qor/references/doctrine-feature-inventory.md`: a "Surface column (optional V2 extension, GH #196)" subsection capturing the schema-optional/WARN-first/fail-closed-on-FailSafe-coverage contract, so the doctrine reflects the planned column ahead of implementation.

---

_Research complete. Findings are advisory — implementation decisions remain with the Governor._
