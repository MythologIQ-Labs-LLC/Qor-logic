# Skill Lifecycle Patterns Reference

## Skill Lifecycle States

### State Machine
```
Discovered > Loading > Loaded > Active > Inactive
                                          |
                                          v
                                        Loaded (can reactivate)

Any state > Error > Loading (retry)
```

### State Definitions
| State | Description | Resources |
|-------|-------------|-----------|
| Discovered | Metadata parsed, not loaded | Minimal (metadata only) |
| Loading | Content being read and validated | Temporary I/O |
| Loaded | Ready to activate, content in memory | Memory for content |
| Active | Executing, responding to requests | Full runtime resources |
| Inactive | Suspended, state preserved | Persisted state only |
| Error | Failed, awaiting retry or removal | Error context for diagnosis |

### Valid Transitions
| From | To | Trigger |
|------|----|---------|
| Discovered | Loading | Explicit load request or auto-load |
| Loading | Loaded | Content validated successfully |
| Loading | Error | Validation or I/O failure |
| Loaded | Active | Activation request |
| Active | Inactive | Deactivation request or timeout |
| Inactive | Loaded | Ready for reactivation |
| Error | Loading | Retry request |

## Skill Registry Design

### Registry Responsibilities
- Discover available skills by scanning directories/manifests
- Store metadata for all discovered skills
- Track loaded/active state per skill
- Resolve dependencies between skills
- Enforce uniqueness (no duplicate skill names)

### Metadata Schema
| Field | Required | Description |
|-------|----------|-------------|
| name | Yes | Unique identifier |
| description | Yes | Short description (< 100 words) |
| version | Yes | Semantic version |
| target_agent | No | Primary agent this skill serves |
| permissions | No | Required capabilities |
| dependencies | No | Other skills or agents required |
| priority | No | Loading priority (lower = first) |
| activation_conditions | No | When to auto-activate |

### Discovery Process
1. Scan skill directories for manifest files
2. Parse metadata from frontmatter or config
3. Validate required fields present
4. Check for version conflicts with existing skills
5. Register in skill map (name > metadata)
6. Emit discovery event

## Progressive Loading

### Tier 1: Metadata (Always Loaded)
- Skill name, description, version
- Target agent and compatibility
- Permissions and dependencies
- Priority and activation conditions
- Cost: ~100 words per skill, negligible memory

### Tier 2: Core Instructions (On-Demand)
- Complete skill content (< 5K words)
- Primary workflows and procedures
- Integration patterns
- Error handling instructions
- Cost: loaded when skill activated, unloaded when deactivated

### Tier 3: Resources (As-Needed)
- Scripts for executable operations
- Reference data for domain knowledge
- Templates and assets
- Large documentation (> 10K words)
- Cost: loaded only when specific resource requested

### Loading Decision Framework
| Situation | Load Tier |
|-----------|-----------|
| Application startup | Tier 1 for all skills |
| User opens skill-related feature | Tier 2 for that skill |
| Skill executes operation needing resource | Tier 3 for that resource |
| Memory pressure | Unload Tier 3 first, then Tier 2 |
| Skill deactivated | Unload Tier 3 and Tier 2, keep Tier 1 |

## Dependency Resolution

### Dependency Types
| Type | Format | Meaning |
|------|--------|---------|
| Skill | `skill:name` | Another skill must be loaded first |
| Agent | `agent:name` | Specific agent must be available |
| Permission | `perm:read` | Capability must be granted |
| External | `ext:service` | External service must be reachable |

### Resolution Algorithm
1. Build dependency graph (directed acyclic graph)
2. Detect cycles (reject if found)
3. Topological sort for loading order
4. Load dependencies before dependents
5. Fail skill if any dependency unavailable (with clear error message)

### Conflict Handling
| Conflict | Resolution |
|----------|-----------|
| Version mismatch | Use highest compatible version |
| Circular dependency | Reject both skills, report error |
| Missing dependency | Defer loading, retry when dependency available |
| Permission denied | Block activation, notify user |

## Skill Coordination

### Multi-Agent Coordination
- Skills may span multiple agents (primary + supporting)
- Primary agent owns the skill execution
- Supporting agents provide capabilities via message passing
- Coordinator tracks which agents participate in each workflow

### Workflow Execution
1. Receive skill execution request with parameters
2. Identify participating agents from skill metadata
3. Create coordination context (shared state for this execution)
4. Execute workflow steps in defined order
5. Collect results from each step
6. Return aggregated result

### Event-Driven Communication
| Event | Emitter | Consumers |
|-------|---------|-----------|
| skill-loaded | Registry | UI, coordinator |
| skill-activated | Lifecycle manager | Agents, UI |
| skill-executed | Coordinator | Logger, metrics |
| skill-failed | Coordinator | Error handler, UI |
| skill-deactivated | Lifecycle manager | Agents, UI |

## Validation and Security

### Validation Checklist
- [ ] Required metadata fields present and non-empty
- [ ] Version follows semantic versioning
- [ ] Requested permissions are in allowed list
- [ ] Dependencies reference known skills/agents
- [ ] External dependencies from trusted sources only
- [ ] Content free of injection patterns (script tags, data URIs)
- [ ] File size within limits

### Permission Model
| Permission | Scope | Risk |
|-----------|-------|------|
| agent:read | Read agent state | Low |
| agent:write | Modify agent state | Medium |
| system:read | Read system info | Low |
| file:read | Read user files | Medium |
| file:write | Write user files | High |
| network | External API access | High |

### Security Principles
- Validate all skill inputs before execution
- Skills cannot escalate beyond granted permissions
- Sandbox skill execution (limit file system, network access)
- Log all skill actions for audit trail
- Allow users to revoke skill permissions at any time

## Performance Monitoring

### Key Metrics
| Metric | Threshold | Action if Exceeded |
|--------|-----------|-------------------|
| Load time | < 200ms | Optimize content size, add caching |
| Execution time (avg) | < 100ms | Profile and optimize hot paths |
| Memory usage | < 10MB per skill | Unload unused resources |
| Error rate | < 5% | Investigate root cause, fix or disable |

### Optimization Strategies
- Cache parsed skill content (avoid re-parsing)
- Preload skills based on usage patterns
- Lazy-load Tier 3 resources
- Unload inactive skills after timeout
- Batch skill operations where possible

### Performance Monitoring Checklist
- [ ] Load times recorded per skill
- [ ] Execution times tracked with rolling averages
- [ ] Memory usage monitored per skill
- [ ] Error counts and rates tracked
- [ ] Optimization triggered when thresholds exceeded
- [ ] Metrics exposed for dashboards/alerting

## Skill Development Checklist

### Creation
- [ ] Unique name, clear description
- [ ] Version set (start at 0.1.0)
- [ ] Target agent identified
- [ ] Permissions minimized (least privilege)
- [ ] Dependencies declared explicitly

### Validation
- [ ] Metadata passes schema validation
- [ ] Content within size limits
- [ ] Dependencies resolvable
- [ ] Permissions grantable
- [ ] Manual testing in target agent context

### Deployment
- [ ] Placed in skill discovery directory
- [ ] Registry discovers and indexes
- [ ] Activation tested (loads without errors)
- [ ] Deactivation tested (cleans up resources)
- [ ] Error scenarios tested (graceful failure)

### Deprecation
- [ ] Mark as deprecated in metadata
- [ ] Log warning when loaded
- [ ] Identify replacement skill
- [ ] Migration guide provided
- [ ] Remove after grace period

## Integration Patterns

### React Integration
- Provide context/provider for skill state management
- Custom hook: `useSkill(name)` returns { skill, isActive, load, activate, deactivate }
- Update UI reactively when skill state changes
- Show loading states during skill transitions

### Event Integration
- Listen for skill lifecycle events to update UI
- Emit user actions as events for skill consumption
- Use typed event payloads for safety
- Clean up event listeners on component unmount

### Error Handling
- Wrap skill operations in try-catch
- Show user-friendly error messages (not stack traces)
- Offer retry for transient failures
- Offer disable for persistent failures
- Log detailed errors for debugging
