---
description: Resume governance after third-party skill usage and reconcile any drift
---

# /ql-resume - Resume Governance Protocol

## Purpose

Resume a sibling governance repository governance after using third-party skills. This workflow:

1. Detects what changed during the pause (drift detection)
2. Logs `GOVERNANCE_RESUMED` to the ledger
3. Creates a new sealed checkpoint
4. Optionally triggers Sentinel audit on changed files

## Usage

```
/ql-resume [--audit]
```

**Options:**

- `--audit`: Also trigger Sentinel audit on all files that changed during pause

## Workflow Steps

### 1. Load Pause Checkpoint

Read `.agent/checkpoints/latest.yaml` and verify:

- `checkpoint.paused: true`
- Checkpoint is sealed

If not paused, inform user:

```markdown
## ℹ️ Governance Not Paused

No active pause detected. Normal governance is already in effect.
If you need to pause governance, use:
```

/ql-pause [reason]

```

```

### 2. Calculate Current State

```powershell
# Current git state
$currentGitHead = git rev-parse HEAD
$currentGitStatus = if ((git status --porcelain) -eq $null) { "clean" } else { "dirty" }

# Current manifold
$currentManifold = @{} # Same calculation as ql-pause
```

### 3. Detect Drift

Compare current state to pause checkpoint:

```powershell
$drift = @{
    git_commits = git log --oneline $pauseCheckpoint.git_head..$currentGitHead
    manifold_delta = @{}
    files_changed = git diff --name-only $pauseCheckpoint.git_head HEAD
}

# Calculate manifold deltas
foreach ($folder in $currentManifold.Keys) {
    $before = $pauseCheckpoint.manifold[$folder]
    $after = $currentManifold[$folder]
    if ($before -and $after) {
        $drift.manifold_delta[$folder] = @{
            file_count_delta = $after.file_count - $before.file_count
            bytes_delta = $after.total_bytes - $before.total_bytes
        }
    }
}
```

### 4. Generate Drift Report

```markdown
## 📊 Drift Report

**Pause Duration:** {duration}
**Git Commits During Pause:** {count}

### File Changes

| Folder | Files Δ | Bytes Δ |
| ------ | ------- | ------- |
| src    | +5      | +12,340 |
| docs   | +1      | +2,100  |

### Changed Files

- `src/components/NewWidget.tsx` (added)
- `src/utils/helper.ts` (modified)
- `docs/API.md` (modified)

### Classification

- **L1 (Routine):** 4 files
- **L2 (Functional):** 2 files
- **L3 (Critical):** 0 files
```

### 5. Log to Ledger

Append `GOVERNANCE_RESUMED` event:

- `eventType: "GOVERNANCE_RESUMED"`
- `payload: { drift_summary, files_changed, pause_duration }`
- Agent DID: `user:sovereign`

If significant drift detected, also log `EXTERNAL_DRIFT`:

- `eventType: "EXTERNAL_DRIFT"`
- `payload: { files, manifold_delta, source: "third_party_skill" }`

### 6. Seal New Checkpoint

Create new checkpoint with:

- `checkpoint.paused: false`
- `checkpoint.sealed: true`
- Updated manifold
- Updated snapshot

Archive previous checkpoint to `.agent/checkpoints/archive/`.

### 7. Optional: Trigger Audit

If `--audit` flag provided:

```powershell
foreach ($file in $drift.files_changed) {
    # Queue for Sentinel audit
    sibling-product.auditFile($file)
}
```

### 8. Confirm to User

```markdown
## ✅ Governance Resumed

**Pause Duration:** 45 minutes
**Files Changed:** 6
**Drift Logged:** Yes (Entry #{id})
**New Checkpoint:** {hash}

Governance is now active. All subsequent changes will be tracked normally.

{if --audit}
**Audit Queued:** 6 files submitted to Sentinel for review.
{/if}
```

## Drift Classification

| Drift Type      | Trigger         | Action                         |
| --------------- | --------------- | ------------------------------ |
| **None**        | No changes      | Log resume, seal checkpoint    |
| **Minor**       | <5 files, no L3 | Log `EXTERNAL_DRIFT`, continue |
| **Significant** | ≥5 files or L2  | Log + suggest `--audit`        |
| **Critical**    | Any L3 detected | Log + auto-queue L3 for review |

## Agent Accountability Note

> [!IMPORTANT]
> If drift analysis reveals that an AI agent made changes during the pause
> (detectable via commit author, file patterns, or Sentinel logs), those
> changes are logged as `AGENT_UNTRACKED_CHANGE` with trust impact.

## Related

- [/ql-pause](ql-pause.md) - Pause governance for third-party skills
