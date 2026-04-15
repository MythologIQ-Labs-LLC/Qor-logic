# Git Hooks Installation

One-time setup per clone:

```bash
git config core.hooksPath .githooks
```

This wires `.githooks/pre-commit` (and any future hooks) into your local git. The hook files are tracked in the repo, so everyone stays consistent.

## What's installed

### `.githooks/pre-commit`

Blocks direct edits to `qor/dist/**` unless you set `BUILD_REGEN=1`. `qor/dist/` is generated output from `qor/scripts/compile.py` — you edit the sources under `qor/skills/` or `qor/agents/`, then regenerate.

**Normal workflow** (no dist changes):

```bash
git add qor/skills/...
git commit -m "feat: new skill"    # hook is silent
```

**Regenerating dist**:

```bash
# Edit source first
vim qor/skills/governance/qor-audit/SKILL.md

# Regenerate
BUILD_REGEN=1 python qor/scripts/compile.py

# Stage + commit with the env flag set
BUILD_REGEN=1 git add qor/skills/ qor/dist/
BUILD_REGEN=1 git commit -m "feat: update audit skill + regen dist"
```

The hook logs the bypass to `.qor/override.log` for audit trail.

## Bypassing the hook

Don't. The CI drift check (`qor/scripts/check_variant_drift.py`) runs regardless and will fail the commit server-side if dist doesn't match the sources. If you need to skip the local hook temporarily for some reason, `git commit --no-verify` works — but CI will still catch you.

## Uninstalling

```bash
git config --unset core.hooksPath
```
