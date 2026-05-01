// Skill admission policy for Qor-logic governance.
// A skill may be invoked only if it is registered and has frontmatter.

permit (
  principal,
  action == Action::"invoke",
  resource
) when { resource.registered == true && resource.has_frontmatter == true };

// Phase 55 (LLM07 + AI RMF GV-6.1): forbid skill invocations whose actual
// tool surface exceeds the declared permitted_tools frontmatter allowlist.
forbid (
  principal,
  action == Action::"invoke",
  resource
) when { resource.actual_tool_invocations_exceed_scope == true };

// Phase 55 (LLM07 + AI RMF GV-6.1): forbid skill invocations whose actual
// subagent_type surface exceeds the declared permitted_subagents allowlist.
forbid (
  principal,
  action == Action::"invoke",
  resource
) when { resource.actual_subagent_invocations_exceed_scope == true };
