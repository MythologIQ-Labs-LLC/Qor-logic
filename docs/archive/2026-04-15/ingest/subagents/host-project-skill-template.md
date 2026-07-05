---
name: <app-name>-skill-template
description: Template for creating host-app-specific agent skills with proper integration, accessibility, and multi-agent coordination.
license: BSL-1.1
---

# the host project Skill Template

## Overview
Replace this section with a brief description of what your skill does and its value to the host project users.

## Target Agent
- **Agent**: [alden|vault|arbiter|synapse]
- **Integration**: How this skill enhances the target agent's capabilities
- **Personality Alignment**: How the skill complements the agent's persona and behavior patterns

## Core Capabilities

### Capability 1: [Capability Name]
**Description**: Clear description of what this capability does
**Use Cases**: Specific scenarios where users would trigger this capability
**Implementation**: Technical approach and considerations

### Capability 2: [Capability Name]
**Description**: Clear description of what this capability does
**Use Cases**: Specific scenarios where users would trigger this capability
**Implementation**: Technical approach and considerations

## the host project Integration

### Backend Implementation (Rust)

#### Command Handler
```rust
use serde::{Deserialize, Serialize};
use tauri::State;

#[derive(Debug, Serialize, Deserialize)]
pub struct SkillParams {
    pub user_id: String,
    pub action: SkillAction,
    #[serde(flatten)]
    pub action_params: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(tag = "action")]
pub enum SkillAction {
    #[serde(rename = "action_name")]
    ActionName,
    // Add more actions as needed
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SkillResponse {
    pub success: bool,
    pub data: serde_json::Value,
    pub message: String,
}

#[tauri::command]
async fn agent_skill_action(
    state: State<'_, AppState>,
    params: SkillParams,
) -> Result<SkillResponse, String> {
    // Validate input
    validate_params(&params)?;
    
    // Get agent context
    let mut agent_context = state.get_agent_context("agent", &params.user_id).await?;
    
    // Execute skill logic
    let result = execute_skill_logic(&params, &mut agent_context).await?;
    
    // Update agent state
    agent_context.update_from_skill(&result).await?;
    
    Ok(result)
}

async fn execute_skill_logic(
    params: &SkillParams,
    context: &mut AgentContext,
) -> Result<SkillResponse, Error> {
    match params.action {
        SkillAction::ActionName => {
            // Implement your skill logic here
            execute_action_name(&params.action_params, context).await
        }
        _ => Err(Error::UnsupportedAction(
            format!("Action {:?} not supported", params.action)
        )),
    }
}
```

#### State Management
```rust
impl AgentContext {
    pub fn update_from_skill(&mut self, result: &SkillResponse) -> Result<(), Error> {
        // Update agent state based on skill execution
        match result.data["update_type"].as_str() {
            Some("knowledge") => {
                // Update knowledge base
                self.knowledge_base.push(parse_knowledge_item(&result.data)?);
            }
            Some("preferences") => {
                // Update user preferences
                self.preferences.insert(
                    "skill_preference".to_string(),
                    result.data["preference"].clone(),
                );
            }
            _ => {
                // Handle other update types
            }
        }
        
        // Update last activity timestamp
        self.last_activity = SystemTime::now();
        
        Ok(())
    }
}
```

### Frontend Integration (TypeScript)

#### Bridge Extension
```typescript
import { BaseBridge } from './BaseBridge';

export interface SkillParams {
    userId: string;
    action: SkillAction;
    actionParams: Record<string, any>;
}

export interface SkillResponse {
    success: boolean;
    data: any;
    message: string;
}

export enum SkillAction {
    ActionName = 'action_name',
    // Add more actions as needed
}

export class AgentSkillBridge extends BaseBridge {
    static async executeAction(params: SkillParams): Promise<SkillResponse> {
        return this.send('agent_skill_action', params);
    }
    
    static async getSkillStatus(userId: string): Promise<SkillStatus> {
        return this.send('agent_skill_status', { userId });
    }
    
    static async configureSkill(config: SkillConfig): Promise<boolean> {
        return this.send('agent_skill_configure', config);
    }
}
```

#### React Component
```typescript
import React, { useState, useEffect } from 'react';
import { AgentSkillBridge, SkillParams, SkillAction } from '@/bridges/AgentSkillBridge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface SkillComponentProps {
    userId: string;
    onSkillUpdate?: (result: SkillResponse) => void;
}

export function SkillComponent({ userId, onSkillUpdate }: SkillComponentProps) {
    const [status, setStatus] = useState<SkillStatus | null>(null);
    const [results, setResults] = useState<SkillResponse[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    
    useEffect(() => {
        loadSkillStatus();
    }, [userId]);
    
    const loadSkillStatus = async () => {
        try {
            const skillStatus = await AgentSkillBridge.getSkillStatus(userId);
            setStatus(skillStatus);
        } catch (error) {
            console.error('Failed to load skill status:', error);
        }
    };
    
    const handleAction = async (action: SkillAction, params: any = {}) => {
        setIsLoading(true);
        try {
            const result = await AgentSkillBridge.executeAction({
                userId,
                action,
                actionParams: params,
            });
            
            setResults(prev => [...prev, result]);
            onSkillUpdate?.(result);
            
            // Refresh status after action
            await loadSkillStatus();
        } catch (error) {
            console.error('Skill action failed:', error);
        } finally {
            setIsLoading(false);
        }
    };
    
    return (
        <div className="skill-container p-4 space-y-4">
            <Card>
                <Card.Header>
                    <h2 className="text-2xl font-bold">Skill Name</h2>
                    {status && (
                        <div className="flex items-center gap-2">
                            <div className={`w-3 h-3 rounded-full ${
                                status.active ? 'bg-green-500' : 'bg-gray-400'
                            }`} />
                            <span className="text-sm text-gray-600">
                                {status.active ? 'Active' : 'Inactive'}
                            </span>
                        </div>
                    )}
                </Card.Header>
                <Card.Content>
                    <div className="space-y-4">
                        {/* Skill Actions */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <Button
                                onClick={() => handleAction(SkillAction.ActionName)}
                                disabled={isLoading}
                                className="w-full"
                                aria-label="Execute action name"
                            >
                                {isLoading ? 'Executing...' : 'Action Name'}
                            </Button>
                            
                            {/* Add more action buttons as needed */}
                        </div>
                        
                        {/* Results Display */}
                        {results.length > 0 && (
                            <div className="mt-4">
                                <h3 className="text-lg font-semibold mb-2">Results</h3>
                                <div className="space-y-2">
                                    {results.map((result, index) => (
                                        <div
                                            key={index}
                                            className={`p-3 rounded-lg ${
                                                result.success ? 'bg-green-50' : 'bg-red-50'
                                            }`}
                                        >
                                            <div className="flex items-center gap-2">
                                                <div className={`w-2 h-2 rounded-full ${
                                                    result.success ? 'bg-green-500' : 'bg-red-500'
                                                }`} />
                                                <span className="text-sm font-medium">
                                                    {result.success ? 'Success' : 'Error'}
                                                </span>
                                            </div>
                                            <p className="text-sm text-gray-700 mt-1">
                                                {result.message}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </Card.Content>
                </Card>
            </div>
        </div>
    );
}
```

## Multi-Agent Coordination

### Agent Communication
```rust
// Coordinate with other agents when needed
async fn coordinate_with_vault(
    query: &str,
    user_id: &str,
    state: Arc<AppState>,
) -> Result<Option<VaultResponse>, Error> {
    // Get Vault agent context
    let vault_context = state.get_agent_context("vault", &user_id).await?;
    
    // Query Vault for information
    let vault_response = vault_context.search_knowledge(query).await?;
    
    Ok(Some(vault_response))
}

async fn notify_arbiter(
    event_type: SecurityEvent,
    details: &SecurityEventDetails,
    user_id: &str,
    state: Arc<AppState>,
) -> Result<(), Error> {
    // Get Arbiter agent context
    let arbiter_context = state.get_agent_context("arbiter", &user_id).await?;
    
    // Report security event to Arbiter
    arbiter_context.report_security_event(event_type, details).await?;
    
    Ok(())
}
```

### Event-Driven Updates
```typescript
// Listen for events from other agents
useEffect(() => {
    const handleSkillEvent = (event: CustomEvent) => {
        const { type, data } = event.detail;
        
        switch (type) {
            case 'knowledge_updated':
                // Refresh knowledge display
                refreshKnowledgeDisplay();
                break;
            case 'security_event':
                // Handle security notifications
                handleSecurityNotification(data);
                break;
            case 'task_completed':
                // Update task status
                updateTaskStatus(data);
                break;
        }
    };
    
    window.addEventListener('skill_event', handleSkillEvent);
    
    return () => {
        window.removeEventListener('skill_event', handleSkillEvent);
    };
}, []);
```

## Accessibility Implementation

### WCAG 2.1 AA Compliance
```typescript
// Accessible button component
const AccessibleButton: React.FC<{
    onClick: () => void;
    children: React.ReactNode;
    disabled?: boolean;
    ariaLabel?: string;
    description?: string;
}> = ({ onClick, children, disabled = false, ariaLabel, description }) => {
    return (
        <button
            onClick={onClick}
            disabled={disabled}
            aria-label={ariaLabel}
            aria-describedby={description ? 'btn-desc' : undefined}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg 
                     hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 
                     disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors duration-200"
        >
            {children}
        </button>
        {description && (
            <div id="btn-desc" className="sr-only">
                {description}
            </div>
        )}
    );
};

// Screen reader announcements
const announceToScreenReader = (message: string) => {
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', 'polite');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    // Remove after announcement
    setTimeout(() => {
        document.body.removeChild(announcement);
    }, 1000);
};
```

### ADHD Optimization
```typescript
// Progressive disclosure for complex information
const ProgressiveDisclosure: React.FC<{
    title: string;
    children: React.ReactNode;
}> = ({ title, children }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    
    return (
        <div className="border rounded-lg">
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full px-4 py-3 text-left font-semibold 
                         hover:bg-gray-50 focus:ring-2 focus:ring-blue-500
                         transition-colors duration-200"
                aria-expanded={isExpanded}
                aria-controls={`disclosure-content-${title.replace(/\s+/g, '-').toLowerCase()}`}
            >
                <span className="mr-2">{isExpanded ? '▼' : '▶'}</span>
                {title}
            </button>
            
            {isExpanded && (
                <div
                    id={`disclosure-content-${title.replace(/\s+/g, '-').toLowerCase()}`}
                    className="px-4 py-3 border-t"
                >
                    {children}
                </div>
            )}
        </div>
    );
};
```

## Testing Framework

### Unit Tests (Rust)
```rust
#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    
    #[tokio::test]
    async fn test_skill_action_validation() {
        let params = SkillParams {
            user_id: "test_user".to_string(),
            action: SkillAction::ActionName,
            action_params: json!({"test": "value"}),
        };
        
        assert!(validate_params(&params).is_ok());
    }
    
    #[tokio::test]
    async fn test_skill_logic_execution() {
        let mut context = AgentContext::new("agent", "test_user");
        let params = SkillParams {
            user_id: "test_user".to_string(),
            action: SkillAction::ActionName,
            action_params: json!({}),
        };
        
        let result = execute_skill_logic(&params, &mut context).await.unwrap();
        
        assert!(result.success);
        assert!(!result.message.is_empty());
    }
}
```

### Integration Tests (TypeScript)
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SkillComponent } from './SkillComponent';

describe('SkillComponent Integration', () => {
    it('should render with accessibility features', async () => {
        render(<SkillComponent userId="test-user" />);
        
        // Check for proper ARIA labels
        const button = screen.getByRole('button', { name: /action name/i });
        expect(button).toHaveAttribute('aria-label');
        
        // Check for keyboard navigation
        button.focus();
        expect(button).toHaveFocus();
    });
    
    it('should handle skill actions', async () => {
        const onSkillUpdate = jest.fn();
        render(<SkillComponent userId="test-user" onSkillUpdate={onSkillUpdate} />);
        
        const button = screen.getByRole('button', { name: /action name/i });
        fireEvent.click(button);
        
        await waitFor(() => {
            expect(onSkillUpdate).toHaveBeenCalledWith(
                expect.objectContaining({
                    success: expect.any(Boolean),
                    data: expect.any(Object),
                    message: expect.any(String),
                })
            );
        });
    });
});
```

## Performance Optimization

### Efficient Context Management
```rust
// Implement caching for frequently accessed data
use std::collections::HashMap;
use tokio::sync::RwLock;

pub struct SkillCache {
    cache: Arc<RwLock<HashMap<String, CachedData>>>,
}

impl SkillCache {
    pub async fn get_or_compute<F, T>(&self, key: &str, compute: F) -> Result<T, Error>
    where
        F: FnOnce() -> Result<T, Error>,
    {
        // Try to get from cache first
        {
            let cache = self.cache.read().await;
            if let Some(data) = cache.get(key) {
                if !data.is_expired() {
                    return Ok(data.value.clone());
                }
            }
        }
        
        // Compute and cache result
        let result = compute()?;
        {
            let mut cache = self.cache.write().await;
            cache.insert(key.to_string(), CachedData::new(result));
        }
        
        Ok(result)
    }
}
```

### Bundle Size Optimization
```typescript
// Lazy load skill components
const LazySkillComponent = React.lazy(() => import('./SkillComponent'));

// Use dynamic imports for large dependencies
const loadHeavyDependency = async () => {
    const module = await import('./heavy-dependency');
    return module.default;
};

// Code splitting for better performance
const SkillRouter = () => (
    <Suspense fallback={<div>Loading skill...</div>}>
        <Routes>
            <Route path="/skill" element={<LazySkillComponent />} />
        </Routes>
    </Suspense>
);
```

## Security Implementation

### Input Validation
```rust
use regex::Regex;
use validator::ValidateLength;

pub fn validate_skill_input(input: &str) -> Result<(), ValidationError> {
    // Check for dangerous patterns
    let dangerous_patterns = vec![
        Regex::new(r"<script").unwrap(),
        Regex::new(r"javascript:").unwrap(),
        Regex::new(r"data:text/html").unwrap(),
    ];
    
    for pattern in &dangerous_patterns {
        if pattern.is_match(input) {
            return Err(ValidationError::DangerousInput);
        }
    }
    
    // Validate length
    if !ValidateLength::max_length(1000).validate(input) {
        return Err(ValidationError::TooLong);
    }
    
    Ok(())
}
```

### Data Encryption
```rust
use aes_gcm::{Aes256Gcm, Key, Nonce};
use aes_gcm::aead::{Aead, NewAead};

pub fn encrypt_sensitive_data(data: &[u8], key: &[u8; 32]) -> Result<Vec<u8>, CryptoError> {
    let cipher = Aes256Gcm::new(Key::from_slice(key));
    let nonce = Nonce::from_slice(&generate_nonce());
    
    cipher
        .encrypt(nonce, data)
        .map_err(|_| CryptoError::EncryptionFailed)
}
```

## Deployment

### Package Configuration
```json
{
  "name": "skill-name",
  "version": "1.0.0",
  "description": "Skill description",
  "targetAgent": "agent-name",
  "compatibility": {
    "<app-name>": ">=1.3.0"
  },
  "permissions": [
    "agent:read",
    "agent:write"
  ],
  "assets": {
    "templates": ["./assets/templates/"],
    "schemas": ["./assets/schemas/"]
  }
}
```

### Installation Script
```python
import json
import zipfile
import os
from pathlib import Path

def install_skill(skill_package_path: str, host-project_path: str) -> bool:
    """Install skill package to the host project"""
    try:
        # Extract skill package
        with zipfile.ZipFile(skill_package_path) as zip_ref:
            zip_ref.extractall(f"{host-project_path}/skills/temp")
        
        # Read skill manifest
        with open(f"{host-project_path}/skills/temp/skill-manifest.json", 'r') as f:
            manifest = json.load(f)
        
        # Validate compatibility
        if not validate_compatibility(manifest):
            print(f"Skill {manifest['name']} is not compatible")
            return False
        
        # Install components
        install_backend_components(f"{host-project_path}/skills/temp", manifest)
        install_frontend_components(f"{host-project_path}/skills/temp", manifest)
        install_assets(f"{host-project_path}/skills/temp", manifest)
        
        # Register skill
        register_skill_with_host-project(manifest, host-project_path)
        
        # Cleanup
        shutil.rmtree(f"{host-project_path}/skills/temp")
        
        print(f"Skill {manifest['name']} installed successfully")
        return True
        
    except Exception as e:
        print(f"Failed to install skill: {e}")
        return False

def validate_compatibility(manifest: dict) -> bool:
    """Validate skill compatibility with the host project"""
    required_version = manifest.get('compatibility', {}).get('<app-name>', '0.0.0')
    # Implement version comparison logic
    return True  # Simplified for example
```

## Usage Examples

### Basic Usage
```typescript
// Using the skill in your application
import { SkillComponent } from '@/skills/skill-name';

function App() {
    return (
        <div className="app">
            <SkillComponent 
                userId="current-user"
                onSkillUpdate={(result) => {
                    console.log('Skill executed:', result);
                }}
            />
        </div>
    );
}
```

### Advanced Usage with Coordination
```typescript
// Coordinating with other agents
const handleComplexTask = async () => {
    // Step 1: Use primary skill
    const primaryResult = await AgentSkillBridge.executeAction({
        userId: 'user123',
        action: SkillAction.ComplexAnalysis,
        actionParams: { data: complexData }
    });
    
    // Step 2: Coordinate with Vault for additional context
    if (primaryResult.data.needsKnowledge) {
        const vaultResult = await VaultBridge.searchKnowledge({
            query: primaryResult.data.searchQuery,
            userId: 'user123'
        });
        
        // Step 3: Combine results
        const combinedResult = {
            primary: primaryResult,
            context: vaultResult,
            confidence: calculateConfidence(primaryResult, vaultResult)
        };
        
        // Step 4: Notify Arbiter of completion
        await ArbiterBridge.logEvent({
            type: 'skill_completed',
            details: combinedResult,
            userId: 'user123'
        });
    }
};
```

## Best Practices

### Development Guidelines
1. **Agent-First Design**: Always consider the target agent's persona and capabilities
2. **Accessibility by Default**: Build in WCAG compliance from the start
3. **Multi-Agent Awareness**: Plan for coordination from the beginning
4. **Performance Conscious**: Consider desktop resource constraints
5. **Security Focused**: Validate all inputs and encrypt sensitive data
6. **Test Thoroughly**: Unit tests for logic, integration tests for coordination
7. **Document Clearly**: Comprehensive examples and API documentation

### Common Patterns to Follow
1. **Consistent Error Handling**: Use Result<T, Error> patterns throughout
2. **Event-Driven Updates**: Emit events for cross-agent communication
3. **Context Management**: Efficiently manage agent state and conversation history
4. **Resource Sharing**: Use the host project's shared asset and template systems
5. **Progressive Enhancement**: Start with basic functionality, then add features

### Integration Checklist
- [ ] Skill follows the host project agent patterns and naming conventions
- [ ] Implements proper error handling with Result types
- [ ] Supports WCAG 2.1 AA accessibility requirements
- [ ] Coordinates with other agents through defined interfaces
- [ ] Includes comprehensive unit and integration tests
- [ ] Documents all interfaces and usage examples
- [ ] Optimized for desktop performance constraints
- [ ] Validates all inputs and sanitizes data
- [ ] Encrypts sensitive data at rest and in transit
- [ ] Uses the host project's bridge patterns for frontend integration
- [ ] Emits proper events for cross-agent communication
- [ ] Handles offline scenarios gracefully
- [ ] Provides clear error messages and recovery paths

This template provides a comprehensive foundation for creating the host project skills that integrate seamlessly with the multi-agent ecosystem while maintaining high standards for accessibility, performance, and security.
