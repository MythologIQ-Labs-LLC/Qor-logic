---
profile: claude-code-solo
host: claude-code
capabilities:
  codex-plugin: false
  agent-teams: false
  mcp-servers: []
---

# Profile: claude-code-solo

Baseline Claude Code environment with no Codex plugin and no Agent Teams tooling. Skills operate in solo mode; audit runs without adversarial counter-argument pass; plan and implement execute sequentially.

## When to use

- Fresh Claude Code install
- No paid Codex subscription
- Development environments where deterministic sequential execution is preferred

## Shortfalls

When a skill's `enhances_with` lists `codex-plugin` or `agent-teams`, the skill emits a `capability_shortfall` shadow event (severity 2) documenting the unavailability. Repeated shortfalls contribute to the Process Shadow Genome threshold.
