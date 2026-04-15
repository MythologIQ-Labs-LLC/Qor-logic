---
profile: codex-standalone
host: codex-standalone
capabilities:
  codex-plugin: true
  agent-teams: false
  mcp-servers: []
---

# Profile: codex-standalone

Codex CLI as the primary harness (no Claude Code wrapping). `codex-plugin` is technically "self" — the host is Codex — but the declaration is consistent so skills written for the Codex-adversarial audit pattern still resolve correctly (in this mode, "Codex" is the base agent, not a sub-agent).

## When to use

- Codex CLI is the active harness
- Skills consumed from `qor/dist/variants/codex/` (currently a stub — future work)

## Status

**Reserved profile.** Codex variant output is not yet emitted by `compile.py` (only `.gitkeep` in `qor/dist/variants/codex/`). Profile is authored so the declaration surface is stable; wiring arrives with the Codex variant compiler in a future phase.
