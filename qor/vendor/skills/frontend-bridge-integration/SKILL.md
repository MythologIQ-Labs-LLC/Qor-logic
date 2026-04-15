---
name: frontend-bridge-integration
description: Frontend bridge integration for Hearthlink. Use when wiring React/TypeScript bridges to Tauri commands, aligning IPC payload shapes, and updating UI consumers of bridge props.
---

# Frontend Bridge Integration

## Workflow

1. Identify the Rust command signature and expected payload shape.
2. Update the relevant bridge in `src/bridges/*.ts` to match the command name and payload schema.
3. If the command is authenticated, build the request to align with `AuthenticatedRequest` (flattened payload + `auth_token`).
4. Update shared types in `src/types/agents.ts` and re-export in `src/bridges/index.ts` if needed.
5. Update UI components to consume new props or return shapes.
6. Adjust E2E mocks in `tests/e2e/mocks/tauri-commands.ts` to keep tests stable.

## Repo touchpoints

- Bridges: `src/bridges/*.ts`, `src/bridges/**/ipc.ts`
- Shared types: `src/types/agents.ts`
- Components: `src/components/**`
- E2E mocks: `tests/e2e/mocks/tauri-commands.ts`

## Checks

- Ensure types match Rust casing (snake_case vs camelCase) and any serde renames.
- Avoid breaking UI by returning new required fields without defaults.

## Scope Boundary

**In scope**
- React/TypeScript bridge layer updates and UI consumer alignment.

**Out of scope**
- Rust command declaration/registration and invoke handler edits as primary task (use `tauri-ipc-wiring`).
