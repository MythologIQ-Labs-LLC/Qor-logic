---
name: <app-name>-skill-framework
description: Foundational skill framework and architecture for creating host-app-specific agent skills that integrate seamlessly with the multi-agent ecosystem.
license: BSL-1.1
---

# the host project Skill Framework

This skill provides the foundational architecture, patterns, and templates for creating host-app-specific agent skills that integrate seamlessly with the multi-agent ecosystem.

## the host project Skill Architecture

### Core Principles

#### 1. Agent-Centric Design
the host project skills are designed around specific agent personas with distinct roles, personalities, and capabilities:
- **Alden**: Primary assistant, task management, proactive help
- **Vault**: Knowledge management, information retrieval, organization
- **Arbiter**: Security monitoring, threat detection, incident response
- **Synapse**: Learning patterns, behavior analysis, adaptation

#### 2. Multi-Agent Coordination
Skills must support inter-agent communication and collaboration:
- Direct agent-to-agent messaging via Rust backend
- Event-driven communication for real-time coordination
- Shared context and state management
- Task delegation and specialization

#### 3. Desktop-First Integration
Skills leverage the host project's Tauri architecture:
- Rust backend commands with proper error handling
- TypeScript bridges for type-safe frontend communication
- IPC (Inter-Process Communication) patterns
- Local-first data storage with SQLite

#### 4. Accessibility-First Design
All skills must meet the host project's accessibility requirements:
- WCAG 2.1 AA compliance
- ADHD-optimized interactions
- Screen reader compatibility
- Keyboard navigation support
- Cognitive load reduction

## Skill Structure Template

### Directory Structure
```
skill-name/
├── SKILL.md                    # Required: Main skill definition
├── scripts/                     # Optional: Executable code
│   ├── init_skill.py          # Skill initialization
│   ├── package_skill.py        # Skill packaging
│   └── [domain-specific].py    # Domain logic scripts
├── references/                  # Optional: Documentation
│   ├── domain-knowledge.md     # Domain expertise
│   ├── api-specs.md          # API documentation
│   └── workflow-guides.md    # Process documentation
└── assets/                     # Optional: Resources
    ├── templates/              # Output templates
    ├── icons/                 # UI assets
    └── schemas/                # Data schemas
```

### SKILL.md Template

```markdown
---
name: [skill-name-in-kebab-case]
description: [Clear description of what this skill does and when Claude should use it. Include target agent and primary use cases.]
license: [license-name]
allowed-tools: [tool1, tool2, ...]  # Optional: For Claude Code
metadata:
  target-agent: [alden|vault|arbiter|synapse]
  skill-category: [category]
  version: "1.0.0"
  compatibility: ["host-project>=1.3.0"]
---

# [Skill Name]

## Overview
[Brief description of the skill's purpose and value proposition]

## Target Agent
- **Agent**: [Primary agent this skill enhances]
- **Integration**: How it connects to existing agent capabilities
- **Personality Alignment**: How skill complements agent's persona

## Core Capabilities

### Capability 1: [Name]
**Description**: What this capability does
**Use Cases**: When users would trigger this
**Implementation**: Technical approach

### Capability 2: [Name]
**Description**: What this capability does
**Use Cases**: When users would trigger this
**Implementation**: Technical approach

## the host project Integration

### Backend Integration (Rust)
```rust
// Command handler registration
#[tauri::command]
async fn [agent]_[skill_name]_[action](
    state: State<'_, AppState>,
    params: [SkillParams],
) -> Result<[ResponseType], String> {
    // Validate input
    validate_params(&params)?;
    
    // Get agent context
    let mut agent_context = state.get_agent_context("[agent]", &params.user_id).await?;
    
    // Execute skill logic
    let result = execute_skill_logic(&params, &mut agent_context).await?;
    
    // Update agent state
    agent_context.update_from_skill(&result).await?;
    
    Ok(result)
}

// Skill execution logic
async fn execute_skill_logic(
    params: &[SkillParams],
    context: &mut AgentContext,
) -> Result<[ResponseType], Error> {
    // Implement skill-specific logic here
    match params.action {
        Action::[Action] => {
            // Handle specific action
        }
        _ => return Err(Error::UnsupportedAction)
    }
}
```

### Frontend Integration (TypeScript)
```typescript
// Bridge extension
export class [Agent]SkillBridge extends BaseBridge {
    static async [skillAction](params: [SkillParams]): Promise<[ResponseType]> {
        return this.send('[agent]_[skill_name]_[action]', params);
    }
    
    static async get[Skill]Status(userId: string): Promise<[SkillStatus]> {
        return this.send('[agent]_[skill_name]_status', { userId });
    }
}

// React component integration
export function [Skill]Component({ userId }: [Skill]Props) {
    const [status, setStatus] = useState<[SkillStatus] | null>(null);
    const [results, setResults] = useState<[ResultType][]>([]);
    
    useEffect(() => {
        loadSkillStatus();
    }, [userId]);
    
    const handleAction = async (action: string, params: any) => {
        const result = await [Agent]SkillBridge.[skillAction]({
            userId,
            action,
            ...params
        });
        setResults(prev => [...prev, result]);
    };
    
    return (
        <div className="skill-container">
            {/* Skill UI implementation */}
        </div>
    );
}
```

## Multi-Agent Coordination

### Agent Communication
```rust
// Inter-agent communication
async fn coordinate_with_agents(
    primary_agent: &str,
    skill_action: &str,
    user_id: &str,
    state: Arc<AppState>,
) -> Result<CoordinationResponse, Error> {
    // Determine which agents need to be involved
    let required_agents = determine_required_agents(skill_action);
    
    // Create coordination task
    let coordination = CoordinationTask {
        primary_agent: primary_agent.to_string(),
        action: skill_action.to_string(),
        participating_agents: required_agents,
        user_id: user_id.to_string(),
    };
    
    // Execute coordination workflow
    let result = execute_coordination_workflow(coordination, state).await?;
    
    Ok(result)
}
```

### Event-Driven Updates
```rust
// Event emission for cross-agent updates
#[tauri::command]
async fn emit_skill_event(
    window: tauri::Window,
    event_type: SkillEventType,
    data: SkillEventData,
) -> Result<(), String> {
    let event = SkillEvent {
        type: event_type,
        data,
        timestamp: SystemTime::now(),
    };
    
    window.emit("skill_event", event)?;
    
    Ok(())
}
```

## Accessibility Integration

### WCAG 2.1 AA Compliance
- **Semantic HTML**: Use proper elements for all UI components
- **ARIA Labels**: Comprehensive labeling for screen readers
- **Keyboard Navigation**: Full keyboard access to all features
- **Color Contrast**: Minimum 4.5:1 ratio for normal text
- **Focus Management**: Logical tab order and focus indicators

### ADHD Optimization
- **Clear Visual Hierarchy**: Obvious primary actions, minimal distractions
- **Progressive Disclosure**: Complex information revealed incrementally
- **Immediate Feedback**: Instant response to user actions
- **Error Recovery**: Clear error messages with actionable guidance
- **Cognitive Load Reduction**: Break complex tasks into steps

## Testing Framework

### Unit Tests
```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[tokio::test]
    async fn test_skill_logic() {
        let mut context = AgentContext::new("test_agent", "test_user");
        let params = SkillParams {
            action: Action::TestAction,
            user_id: "test_user".to_string(),
        };
        
        let result = execute_skill_logic(&params, &mut context).await.unwrap();
        
        assert!(result.success);
        assert_eq!(result.data, expected_data);
    }
}
```

### Integration Tests
```typescript
describe('[Agent] [Skill] Integration', () => {
    it('should coordinate with other agents', async () => {
        const result = await [Agent]SkillBridge.coordinateWithAgents({
            action: 'complex_task',
            userId: 'test-user',
        });
        
        expect(result.coordination).toBeDefined();
        expect(result.participatingAgents).toContain('vault');
    });
    
    it('should handle accessibility requirements', async () => {
        // Test screen reader compatibility
        // Test keyboard navigation
        // Test focus management
    });
});
```

## Performance Considerations

### Context Management
- **Efficient Loading**: Load only necessary skill components
- **Memory Management**: Prune conversation history appropriately
- **Caching**: Cache frequently accessed data
- **Async Operations**: Non-blocking execution throughout

### Resource Optimization
- **Bundle Size**: Minimize impact on application size
- **Load Time**: Fast skill initialization
- **Memory Usage**: Monitor and limit memory consumption
- **CPU Usage**: Efficient algorithms and data structures

## Security & Privacy

### Data Protection
- **Input Validation**: Validate all user inputs
- **Sanitization**: Prevent injection attacks
- **Encryption**: Sensitive data encrypted at rest
- **Permissions**: Minimal required permissions

### Privacy by Design
- **Local Processing**: Process data locally when possible
- **Data Minimization**: Collect only necessary data
- **User Control**: Clear data management options
- **Transparency**: Open about data usage

## Deployment & Distribution

### Skill Packaging
```bash
# Package skill for distribution
python scripts/package_skill.py path/to/skill-name/

# Creates:
# - skill-name.zip (distribution package)
# - skill-validation.json (validation report)
# - skill-manifest.json (metadata for installer)
```

### Installation Process
```typescript
// Dynamic skill loading
async function installSkill(skillPackage: SkillPackage): Promise<boolean> {
    try {
        // Validate skill package
        const validation = await validateSkill(skillPackage);
        if (!validation.isValid) {
            throw new Error(validation.errors.join(', '));
        }
        
        // Install skill components
        await installBackendCommands(skillPackage.backend);
        await installFrontendComponents(skillPackage.frontend);
        await installAssets(skillPackage.assets);
        
        // Register with agent system
        await registerSkillWithAgent(skillPackage.metadata);
        
        return true;
    } catch (error) {
        console.error('Skill installation failed:', error);
        return false;
    }
}
```

## Skill Examples

### Example 1: Task Automation Skill
Enhances Alden with automated task creation from natural language

### Example 2: Knowledge Retrieval Skill
Enhances Vault with semantic search and knowledge synthesis

### Example 3: Security Monitoring Skill
Enhances Arbiter with threat detection and incident response

## Best Practices

### Development Guidelines
1. **Agent-First**: Always design with target agent in mind
2. **Accessibility**: WCAG compliance from the start
3. **Coordination**: Plan for multi-agent workflows
4. **Performance**: Consider desktop resource constraints
5. **Testing**: Comprehensive unit and integration tests
6. **Documentation**: Clear usage examples and API docs

### Common Patterns
1. **Command Pattern**: Consistent naming across skills
2. **Error Handling**: Graceful degradation and recovery
3. **State Management**: Consistent agent state patterns
4. **Event Systems**: Reactive updates across agents
5. **Resource Sharing**: Efficient data and asset sharing

### Integration Checklist
- [ ] Skill follows the host project agent patterns
- [ ] Implements proper error handling
- [ ] Supports accessibility requirements
- [ ] Coordinates with other agents
- [ ] Includes comprehensive tests
- [ ] Documents all interfaces
- [ ] Optimized for performance
- [ ] Validates all inputs
- [ ] Encrypts sensitive data

## Maintenance & Updates

### Version Management
- Semantic versioning (MAJOR.MINOR.PATCH)
- Backward compatibility considerations
- Migration paths for breaking changes
- Deprecation notices and timelines

### Community Contributions
- Skill contribution guidelines
- Code review process
- Testing requirements
- Documentation standards

This framework ensures all the host project skills provide consistent, accessible, and coordinated experiences that enhance the multi-agent ecosystem while maintaining the project's high standards for quality and usability.
