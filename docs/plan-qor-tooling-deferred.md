# Plan: Qor Tooling (Deferred — post-SSoT)

**Status**: Deferred stub. Do not implement until `plan-qor-ssot-minimal.md` completes and the SSoT migration is validated.

## Scope

Tooling phases deferred out of the minimal SSoT migration to avoid amendment-drift during active plan authoring. Full specifications exist in `plan-qor-migration-final.md` §Phases 2–8; this stub tracks which phases are carried forward.

## Deferred phases

| Phase | Purpose | Source spec |
|---|---|---|
| **2** | Build pipeline: `compile.py`, variant drift check, pre-commit hook, `qor/dist/` | `plan-qor-migration-final.md` §Phase 2 |
| **3** | Gate chain runtime: `session.py`, `validate_gate_artifact.py`, gate schemas, advisory enforcement | `plan-qor-migration-final.md` §Phase 3 |
| **4** | Full Process Shadow Genome automation: threshold trip, issue creation, severity-gated expiry, escalation idempotence | `plan-qor-migration-final.md` §Phase 4 |
| **5** | Cross-repo batch collector, `~/.qor/repos.json` config, `gh` issue creation | `plan-qor-migration-final.md` §Phase 5 |
| **6** | Platform detection, capability manifests, profiles, marker-based session tracking | `plan-qor-migration-final.md` §Phase 6 |
| **8** | End-to-end validation test suite | `plan-qor-migration-final.md` §Phase 8 |

## Replanning rules

When this stub is picked up:

1. Re-ground against post-SSoT repo state (paths have moved; any references must re-verify).
2. Split each deferred phase into its own `plan-qor-tooling-<phase>.md` — do not author a single consolidated tooling plan. Small surfaces = fewer amendment-drift defects per audit round.
3. Each sub-plan goes through `/qor-audit` independently. Hit PASS or accept override per gate chain.
4. Preserve the 5 carried violations from `PROCESS_SHADOW_GENOME.md` Entry #1 as input context — some (V-1, V-5) are already resolved in minimal; V-2, V-3, V-4 may still need design attention depending on which phase pulls them in.

## Carried violations status (from SSoT migration)

- V-1 (destinations in tree): RESOLVED in minimal plan
- V-2 (21 collisions): POLICY STATED (first-source-wins); may resurface if Phase 2 compile.py treats collisions differently
- V-3 (merge order): RESOLVED via `qor/scripts/utilities/` routing
- V-4 (R-5/R-6 deferred): POLICY STATED (default qor-scoped if qor frontmatter); Phase 1 execution will mark actual dispositions in `.qor/migration-discards.log`
- V-5 (CI grep scope): RESOLVED via narrowed targets

## Trigger

Open this stub and begin sub-plan authoring when: SSoT migration is complete, ledger Entries #17/#18/#19 are committed, and `ledger_hash.py --verify` passes.
