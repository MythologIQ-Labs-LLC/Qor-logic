---
name: security-permission-audit
description: Security and permissions auditing for Hearthlink. Use when adding consent checks, auth guards, audit logging, or SecureVault interactions for Tauri commands.
---

# Security and Permission Audit

## Workflow

1. Confirm authentication via `require_auth!` in Rust commands.
2. For sensitive actions, validate consented permissions against required permissions.
3. Use `SecureVault` audit logging for install, execution, or data access events.
4. Update frontend flows to surface permission prompts and pass consented permissions.
5. Update E2E mocks/tests for auth + consent paths.

## Repo touchpoints

- Auth guards: `src-tauri/src/guards.rs`, `src-tauri/src/auth/*`
- Secure vault: `src-tauri/src/secure_vault.rs`, `src-tauri/src/vault/*`
- Synapse security: `src-tauri/src/synapse/*`, `src/components/synapse/*`
- Frontend consent: `src/components/synapse/PermissionConsentModal.tsx`
- E2E tests: `tests/e2e/security/*`, `tests/e2e/mocks/tauri-commands.ts`

## Checks

- Ensure all required permissions are consented before install/execute.
- Log audit events with consistent metadata keys for compliance reviews.
- Avoid leaking sensitive info in error messages.

## Scope Boundary

**In scope**
- Consent checks, auth guards, audit logging, and SecureVault-related security flow validation.

**Out of scope**
- Editing Tauri capability/CSP files as the primary task (use `tauri2-security-permissions`).
- Generic plugin setup without explicit security/consent requirements (use `tauri2-plugin-integration`).
