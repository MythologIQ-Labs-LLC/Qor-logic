---
name: skill-lifecycle-ops
description: Synapse skill lifecycle operations for Hearthlink. Use when working on skill registry, resolution, instance management, execution, or related UI and tests.
---

# Skill Lifecycle Operations

## Workflow

1. Check registry/listing commands in `src-tauri/src/synapse/commands.rs` and related skill modules.
2. Ensure instance creation, enable/disable, and execution paths are wired in Rust and TS bridges.
3. Update UI panels in `src/components/skills/*` or `src/components/mimic/*` as needed.
4. Keep skill types aligned in `src/types/agents.ts`.
5. Update E2E tests such as `tests/e2e/skill-system.spec.ts` and mocks.

## Repo touchpoints

- Rust skill system: `src-tauri/src/synapse/skills/*`, `src-tauri/src/synapse/commands.rs`
- TS bridge: `src/bridges/SynapseBridge.ts`
- UI: `src/components/skills/*`, `src/components/mimic/*`
- Types: `src/types/agents.ts`
- E2E: `tests/e2e/skill-system.spec.ts`, `tests/e2e/mocks/tauri-commands.ts`

## Checks

- Maintain consistent `skill_id`, `instance_id`, and `agent_id` usage.
- Ensure execution logs and history return shapes used by UI.

## Scope Boundary

**In scope**
- Skill registry, resolution, instance lifecycle, and execution pipeline operations.

**Out of scope**
- Choosing which skill should be used for a user prompt (use `aegis-skill-router`).
