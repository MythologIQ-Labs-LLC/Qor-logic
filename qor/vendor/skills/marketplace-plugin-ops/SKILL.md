---
name: marketplace-plugin-ops
description: Marketplace and plugin operations for Hearthlink. Use when editing marketplace catalog parsing, install/uninstall flows, local plugin scanning, or the marketplace UI/bridge.
---

# Marketplace and Plugin Ops

## Workflow

1. Check marketplace Rust module and catalog parsing logic.
2. Validate install/uninstall paths, filesystem locations, and error handling.
3. Enforce permission consent and audit logging for installs.
4. Update TS bridge and UI (`SkillMarketplace`) to match payloads and statuses.
5. Update mocks for marketplace commands and related E2E tests.

## Repo touchpoints

- Rust marketplace: `src-tauri/src/synapse/marketplace.rs`, `src-tauri/src/synapse/marketplace_catalog.json`
- Rust invoke wiring: `src-tauri/src/invoke_handler_debug.inc`, `src-tauri/src/invoke_handler_release.inc`
- TS bridge: `src/bridges/MarketplaceBridge.ts`
- UI: `src/components/mimic/SkillMarketplace.tsx`, `src/components/synapse/PluginMarketplace.tsx`
- E2E mocks: `tests/e2e/mocks/tauri-commands.ts`

## Checks

- Ensure consented permissions cover required permissions before install.
- Keep `InstallStatus` unions aligned across Rust and TS.
- Confirm local plugin scan dir and catalog path are stable across environments.
