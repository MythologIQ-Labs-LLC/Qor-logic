---
profile: claude-code-teams
host: claude-code
capabilities:
  codex-plugin: false
  agent-teams: true
  mcp-servers: []
---

# Profile: claude-code-teams

Claude Code with Agent Teams tooling (`TeamCreate` available). `qor-plan` and `qor-implement` can fan out specialist tracks (frontend, backend, infra) in parallel with a synthesizer reconciling.

## When to use

- Large multi-domain features where sequential execution is painful
- Architecture work benefiting from diverse specialist perspectives simultaneously
- Situations where a synthesizer agent's reconciliation adds value over solo planning

## Integration (future wiring)

`qor-plan` checks `is_available("agent-teams")` and, when true, decomposes phases into per-domain tracks invoked via `TeamCreate`. Absent Teams, plan executes sequentially in solo mode.
