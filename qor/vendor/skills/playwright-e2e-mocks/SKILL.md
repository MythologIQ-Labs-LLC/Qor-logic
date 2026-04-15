---
name: playwright-e2e-mocks
description: Playwright E2E authoring and Tauri mock reliability for Hearthlink. Use when updating tests, selectors, or IPC mocks under tests/e2e.
---

# Playwright E2E and Tauri Mocks

## Workflow

1. Use shared selectors from `tests/e2e/selectors.ts` where possible.
2. Update `tests/e2e/mocks/tauri-commands.ts` to match new IPC commands and payload shapes.
3. Keep mock responses consistent with UI expectations (field names, statuses, ids).
4. Favor `Helpers.waitForAppReady(page)` instead of raw timeouts.
5. Keep tests resilient: avoid brittle selectors and hard-coded timing.

## Repo touchpoints

- Mocks: `tests/e2e/mocks/tauri-commands.ts`
- Test setup: `tests/e2e/setup.ts`, `tests/e2e/utils/*`
- Selectors: `tests/e2e/selectors.ts`
- Tests: `tests/e2e/*.spec.ts`

## Checks

- Ensure mocks unwrap `AuthenticatedRequest` payloads if needed.
- Verify toasts and UI states with assertions rather than timeouts.

## Scope Boundary

**In scope**
- Playwright test authoring, selectors, and Tauri mock reliability under `tests/e2e`.

**Out of scope**
- Broader Tauri 2.x validation planning outside E2E test layers (use `tauri2-testing-validation`).
