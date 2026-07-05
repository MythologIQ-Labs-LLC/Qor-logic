---
name: ql-secure-workspace
description: Audit and repair workspace governance configuration. Ensures that proprietary folder structures are correctly isolated from generic AI skills and that privacy patterns are active.
---

# /ql-secure-workspace - Governance Hygiene Audit

<skill>
  <trigger>/ql-secure-workspace</trigger>
  <phase>ALIGN + SECURE</phase>
  <persona>Governor</persona>
  <output>Repaired <consumer-governance-dotdir>/workspace-config.json, verified .gitignore</output>
</skill>

## Purpose

Automatically detects if the current workspace matches a **proprietary archetype** (e.g., Extension Development) and ensures the governance configuration is correctly tuned to protect sensitive structures from generic reorganization or bootstrap skills.

## Execution Protocol

### Step 1: Governance Detection

The Governor executes the internal migration utility to scan for proprietary indicators:

- Source paths containing specialized workflow DNA.
- Build pipelines and transformation scripts.
- Target environment constraints.

### Step 2: Configuration Repair

If proprietary indicators are found, the Governor verifies the workspace configuration (e.g., `<consumer-governance-dotdir>/workspace-config.json`).

**Action required if:**

- File is missing.
- `organizationExclusions` are incomplete.
- `exclusionReason` is missing.

### Step 3: Privacy Verification

The Governor audits the `.gitignore` to ensure it includes the patterns defined in the workspace configuration.

## Command Execution

// turbo

1. Run the internal secure workspace command:

   ```powershell
   # Triggers the governance alignment process
   vscode.commands.executeCommand('sibling-product.secureWorkspace')
   ```

2. Report results to the user with a summary of which paths were secured.

## Constraints

- **NEVER** overwrite user-defined exclusions without confirmation.
- **ALWAYS** inform the user when a specialized structure is detected.
- **ALWAYS** provide a reason for the exclusions.

---

_Hygiene enforced by QoreLogic Governor_
