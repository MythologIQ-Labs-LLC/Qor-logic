---
profile: claude-code-with-codex
host: claude-code
capabilities:
  codex-plugin: true
  agent-teams: false
  mcp-servers: []
---

# Profile: claude-code-with-codex

Claude Code with the Codex plugin installed. `qor-audit` runs in adversarial mode: the plan is passed to Codex for independent counter-argument generation, and the result is synthesized back into the audit report.

## When to use

- Paid Codex subscription available and installed in Claude Code
- Plan-stage scrutiny matters (architecture decisions, security-adjacent work)
- Diminishing-returns audit loops (shift second-opinion load to a different model)

## Integration (future wiring)

`qor-audit` will inspect `is_available("codex-plugin")` and, when true, delegate a structured critique request. The contract:

- Input: `{plan_path, plan_content_hash, codebase_snapshot_refs}` (schema: `qor/gates/schema/audit.schema.json` input section — TBD)
- Output: `{critiques: [{severity, claim_challenged, counter_evidence, recommended_gap}], confidence}`

Skill-layer wiring is a future task.
