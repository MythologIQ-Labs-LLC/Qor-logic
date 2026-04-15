# Qorlogic Skill Registry

**Snapshot**: 2026-04-15
**Authoritative location**: `qor/skills/<category>/<skill>/`

Skills organized by functional category. Path-shown relative to repo root.

## governance/ (5)

Gate, audit, and compliance authority.

| Skill | Path | Status |
|---|---|---|
| qor-audit | `qor/skills/governance/qor-audit/` | Active |
| qor-validate | `qor/skills/governance/qor-validate/` | Active |
| qor-substantiate | `qor/skills/governance/qor-substantiate/` | Active |
| qor-shadow-process | `qor/skills/governance/qor-shadow-process/` | Stub (full impl deferred) |
| qor-governance-compliance | `qor/skills/governance/qor-governance-compliance/` | Active (migrated) |

## sdlc/ (6)

Research → plan → implement → refactor → debug → remediate cycle.

| Skill | Path | Status |
|---|---|---|
| qor-research | `qor/skills/sdlc/qor-research/` | Active |
| qor-plan | `qor/skills/sdlc/qor-plan/` | Active |
| qor-implement | `qor/skills/sdlc/qor-implement/` | Active |
| qor-refactor | `qor/skills/sdlc/qor-refactor/` | Active |
| qor-debug | `qor/skills/sdlc/qor-debug/` | Active |
| qor-remediate | `qor/skills/sdlc/qor-remediate/` | Stub (absorbs qor-course-correct) |

## memory/ (6)

State tracking, documentation, decision logs.

| Skill | Path | Status |
|---|---|---|
| qor-status | `qor/skills/memory/qor-status/` | Active |
| qor-document | `qor/skills/memory/qor-document/` | Active |
| qor-organize | `qor/skills/memory/qor-organize/` | Active |
| log-decision | `qor/skills/memory/log-decision.md` | Active (migrated) |
| track-shadow-genome | `qor/skills/memory/track-shadow-genome.md` | Active (migrated) |
| qor-docs-technical-writing | `qor/skills/memory/qor-docs-technical-writing/` | Active (migrated) |

## meta/ (7)

Bootstrapping, help, repo management, meta-tracking.

| Skill | Path | Status |
|---|---|---|
| qor-bootstrap | `qor/skills/meta/qor-bootstrap/` | Active |
| qor-help | `qor/skills/meta/qor-help/` | Active |
| qor-repo-audit | `qor/skills/meta/qor-repo-audit/` | Active |
| qor-repo-release | `qor/skills/meta/qor-repo-release/` | Active |
| qor-repo-scaffold | `qor/skills/meta/qor-repo-scaffold/` | Active |
| qor-meta-log-decision | `qor/skills/meta/qor-meta-log-decision/` | Active (migrated) |
| qor-meta-track-shadow | `qor/skills/meta/qor-meta-track-shadow/` | Active (migrated) |

## custom/ (0)

Reserved. Populated when qor-scoped custom content is identified.

## Retired

- `qor-course-correct` — absorbed into `qor-remediate`

## Agents (13 qor-scoped + 7 vendor + third-party collection)

See `qor/agents/` for qor-scoped agents (13 across governance, sdlc, memory, meta).
See `qor/vendor/agents/` for 7 generic specialists + `third-party/` (wshobson-agents category directories).

## Vendor skills

~65 third-party skill packs under `qor/vendor/skills/` — not listed per-file here. Browse the directory. Notable groupings:

- `tauri/` — Tauri 2 skill cluster (qor-tauri2-* + deferred tauri2-* with collision policy applied)
- `chrome-devtools/` — Chrome DevTools MCP audit
- `custom/` — Bundled third-party collection (LICENSE files present from ElevenLabs and wshobson-agents)
- `_system/` — openai-docs, skill-creator, skill-installer
- `agents/` — agent-management meta-skill

## Discards

See `.qor/migration-discards.log` for first-source-wins dedup record.
