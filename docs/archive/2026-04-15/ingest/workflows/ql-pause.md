---
description: Pause governance to use third-party skills with explicit consent
---

# /ql-pause - Pause Governance Protocol

## Purpose

Explicitly pause a sibling governance repository governance tracking before using third-party skills (e.g., Superpowers, external AI tools). This creates a **consent checkpoint** that:

1. Records the current system state
2. Logs `GOVERNANCE_PAUSED` to the ledger
3. Allows untracked changes without governance friction
4. Preserves user sovereignty (you can always override)

## Usage

```
/ql-pause [reason]
```

**Example:**

```
/ql-pause Using Superpowers skill for quick UI generation
```

## Workflow Steps

### 1. Create Consent Checkpoint

```powershell
# Get current git state
$gitHead = git rev-parse HEAD
$gitStatus = if ((git status --porcelain) -eq $null) { "clean" } else { "dirty" }

# Get timestamp
$timestamp = Get-Date -Format "o"
```

### 2. Calculate Current Manifold

Calculate folder-level metrics (NOT per-file hashing):

```powershell
# Manifold calculation (lightweight)
$manifold = @{}
foreach ($folder in @("src", "docs", ".agent")) {
    if (Test-Path $folder) {
        $stats = Get-ChildItem -Path $folder -Recurse -File |
            Measure-Object -Property Length -Sum
        $manifold[$folder] = @{
            file_count = $stats.Count
            total_bytes = $stats.Sum
            last_modified = (Get-ChildItem -Path $folder -Recurse -File |
                Sort-Object LastWriteTime -Descending |
                Select-Object -First 1).LastWriteTime.ToString("o")
        }
    }
}
```

### 3. Write Checkpoint File

Update `.agent/checkpoints/latest.yaml`:

```yaml
checkpoint:
  version: 1
  created: "{timestamp}"
  sealed: true
  skill_session: "ql-pause"
  paused: true
  pause_reason: "{user-provided reason}"

snapshot:
  git_head: "{gitHead}"
  git_status: "{gitStatus}"
  ledger_chain_head: "{from ledger}"
  sentinel_events_processed: "{count}"

manifold:
  src:
    file_count: { n }
    total_bytes: { n }
  # ... other folders

user_overrides:
  - timestamp: "{timestamp}"
    reason: "{user-provided reason}"
    acknowledged: true
```

### 4. Log to Ledger

Append `GOVERNANCE_PAUSED` event to the SOA ledger with:

- `eventType: "GOVERNANCE_PAUSED"`
- `payload: { reason, checkpoint_hash }`
- Agent DID: `user:sovereign` (special identifier)

### 5. Confirm to User

```markdown
## ✅ Governance Paused

**Timestamp:** {timestamp}
**Reason:** {reason}
**Checkpoint Hash:** {first 8 chars}...

You can now use third-party skills freely. When you're done:
```

/ql-resume

```

> [!NOTE]
> SentinelDaemon continues monitoring file changes, but no governance
> enforcement will occur until you resume.
```

## Important Notes

- **No Timeout**: Governance stays paused until you explicitly run `/ql-resume`
- **Agent Accountability**: AI agents cannot invoke `/ql-pause` - only users
- **Audit Trail**: All changes during pause are still logged by SentinelDaemon
- **Reconciliation**: `/ql-resume` will show you what changed during the pause

## Related

- [/ql-resume](ql-resume.md) - Resume governance and reconcile drift
