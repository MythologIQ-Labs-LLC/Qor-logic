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

When a skill's `enhances_with` lists a capability that is unavailable AND has no declared substitute, the skill emits a `capability_shortfall` shadow event (severity 2). Phase 252 (GH #411): a capability listed in `qor_platform.FALLBACKS` reports `satisfied-by-fallback` from `qor_platform.availability()` and emits NO shortfall -- `agent-teams` is covered by host-native subagent dispatch, which does the governance work the capability exists to do. Reserving the event for capabilities with no viable substitute is what makes it worth its severity. Repeated shortfalls contribute to the Process Shadow Genome threshold.
