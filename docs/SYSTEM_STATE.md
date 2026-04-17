# Qorlogic System State

**Snapshot**: 2026-04-17
**Chain Status**: ACTIVE (80 entries, last seal: 637210056ea... at v0.16.0)
**Phase**: Phase 25 sealed. Prompt resilience doctrine applied to 11 skills (autonomy: autonomous | interactive). `qorlogic seed` scaffolds governance workspaces. Three-tier communication model (`technical` / `standard` / `plain`) live via `/qor-tone` + `qorlogic init --tone`. SG-Phase25-A (test-scope gap) and SG-Phase25-B (ghost feature via metadata) both closed.

## Authoritative source

All canonical Qor content lives under `qor/`. Variant outputs (`claude`, `kilo-code`, `codex`) are deferred until Phase 2 re-introduces the compile pipeline.

## File Tree

```
G:/MythologIQ/Qorlogic/
├── qor/                                   Single source of truth
│   ├── skills/
│   │   ├── governance/                    Gate & audit authority
│   │   │   ├── qor-audit/
│   │   │   ├── qor-validate/
│   │   │   ├── qor-substantiate/
│   │   │   ├── qor-shadow-process/        (stub — full impl deferred)
│   │   │   └── qor-governance-compliance/
│   │   ├── sdlc/                          Research → implement cycle
│   │   │   ├── qor-research/
│   │   │   ├── qor-plan/
│   │   │   ├── qor-implement/
│   │   │   ├── qor-refactor/
│   │   │   ├── qor-debug/
│   │   │   └── qor-remediate/             (stub — absorbs qor-course-correct)
│   │   ├── memory/                        State tracking & documentation
│   │   │   ├── qor-status/
│   │   │   ├── qor-document/
│   │   │   ├── qor-organize/
│   │   │   ├── log-decision.md
│   │   │   ├── track-shadow-genome.md
│   │   │   └── qor-docs-technical-writing/
│   │   ├── meta/                          Bootstrapping & repo management
│   │   │   ├── qor-bootstrap/
│   │   │   ├── qor-help/
│   │   │   ├── qor-repo-audit/
│   │   │   ├── qor-repo-release/
│   │   │   ├── qor-repo-scaffold/
│   │   │   ├── qor-meta-log-decision/
│   │   │   └── qor-meta-track-shadow/
│   │   └── custom/                        (reserved; empty until qor-scoped custom content identified)
│   │
│   ├── agents/
│   │   ├── governance/                    qor-governor, qor-judge
│   │   ├── sdlc/                          qor-specialist, qor-strategist, qor-fixer,
│   │   │                                  qor-ux-evaluator, project-planner
│   │   ├── memory/                        qor-technical-writer, documentation-scribe,
│   │   │                                  learning-capture
│   │   └── meta/                          agent-architect, system-architect, build-doctor
│   │
│   ├── vendor/
│   │   ├── agents/                        7 generic specialists + third-party/ (wshobson-agents)
│   │   └── skills/                        ~65 third-party skills (frameworks, integrations,
│   │                                      tauri/, chrome-devtools/, custom/, _system/, agents/)
│   │
│   ├── scripts/
│   │   ├── ledger_hash.py                 Content/chain hashing + manifest generation + verify
│   │   ├── calculate-session-seal.py      Session seal utility
│   │   ├── legacy/                        Pre-migration pipeline (process-skills.py,
│   │   │                                  compile-*.py, admit-skill.py, gate-skill-matrix.py,
│   │   │                                  intent-lock.py)
│   │   └── utilities/                     Assorted utility scripts
│   │
│   ├── references/                        Doctrine + patterns + qor-* examples
│   ├── experimental/                      Non-canonical research (tauri2-state, tauri-launcher, etc.)
│   └── templates/                         Doc templates (ARCHITECTURE_PLAN, CONCEPT, SYSTEM_STATE, etc.)
│
├── docs/
│   ├── META_LEDGER.md                     Hash-chained governance ledger (18 entries)
│   ├── SHADOW_GENOME.md                   Audit-verdict failure records (5 entries)
│   ├── PROCESS_SHADOW_GENOME.md           Process-level failure log (JSONL append-only)
│   ├── SYSTEM_STATE.md                    This file
│   ├── SKILL_REGISTRY.md                  Category-organized skill index
│   ├── ARCHITECTURE_PLAN.md
│   ├── BACKLOG.md
│   ├── CONCEPT.md
│   ├── SKILL_AUDIT_CHECKLIST.md
│   ├── Lessons-Learned/
│   ├── plan-qor-*.md                      Migration plan iterations (v1, v2, v3, final, minimal, deferred)
│   ├── migration-manifest-pre.json        Phase 1.5 pre-move manifest (2176 paths)
│   ├── migration-manifest-post.json       Phase 1.5 post-move manifest (1458 paths)
│   ├── MERKLE_ITERATION_GUIDE.md
│   ├── SHIELD_SELF_AUDIT.md
│   └── archive/2026-04-15/                Pre-migration snapshots (ingest, processed, compiled,
│                                          deployable_state, kilo-code)
│
├── .qor/                                  Runtime state (gitignored)
│   └── migration-discards.log             First-source-wins discard record
│
├── pyproject.toml                         Python 3.11+, pytest config, jsonschema runtime dep
├── .gitignore
└── README.md
```

## Ledger chain head

- Entry #18 MIGRATION-COMPLETE
- Chain hash: `7c41dbc944f53a2663de190ba14bdbc2c5fa5b81ecb8f5d3dffc67d32d9a8b18`
- Verification: `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` → all 18 entries OK

## Deferred

Tooling phases (compile pipeline, gate chain runtime, shadow threshold automation, cross-repo collector, platform detect, full validation suite) are tracked in `docs/plan-qor-tooling-deferred.md` for subsequent, scope-limited plans.

## Advisory-gate overrides carried

One sev-1 `gate_override` event logged in `docs/PROCESS_SHADOW_GENOME.md` against the 5-round audit loop verdicts on the full plan. User-approved per `/qor-debug` analysis. Remaining violations (V-1..V-5) are addressed in `plan-qor-ssot-minimal.md` or explicitly carried as known risk.
