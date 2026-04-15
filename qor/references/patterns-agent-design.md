# Agent Design Patterns Reference

## Agent Modeling

### Agent Types
| Type | Description | When to Use |
|------|-------------|-------------|
| Reactive | Responds to stimuli, no internal state | Simple event handlers, notifications |
| Deliberative | Plans before acting, maintains goals | Complex task management, scheduling |
| Hybrid | Reactive layer + deliberative layer | Most production agents |
| Autonomous | Self-directed, initiates actions | Background monitoring, proactive assistance |

### Agent Design Checklist
1. Define the agent's single primary responsibility
2. Design personality traits appropriate to the role
3. List concrete capabilities (what it can do)
4. Define communication interfaces (user + inter-agent)
5. Specify state requirements (what it must remember)
6. Plan intelligence strategy (LLM integration, rules, both)
7. Design error handling and recovery behavior
8. Document coordination patterns with other agents

## State Machine Design

### Finite State Machine (FSM)
- Define explicit states: Idle, Active, Processing, Error, Shutdown
- Map all valid transitions between states
- Guard transitions with conditions
- Emit events on state changes for observability

### Valid Transition Matrix (Template)
```
From \ To      | Idle | Active | Processing | Error | Shutdown
Idle           |  -   |   Y    |     N      |   N   |    Y
Active         |  Y   |   -    |     Y      |   Y   |    Y
Processing     |  N   |   Y    |     -      |   Y   |    N
Error          |  Y   |   N    |     N      |   -   |    Y
Shutdown       |  N   |   N    |     N      |   N   |    -
```

### Hierarchical State Machines
- Nest sub-states within parent states (e.g., Active > Listening, Active > Responding)
- Parent state handles shared behavior
- Use when: states share common transitions or behaviors

### Behavior Trees
- Sequence: execute children in order, fail on first failure
- Selector: try children in order, succeed on first success
- Decorator: modify child behavior (retry, invert, timeout)
- Use when: complex conditional behavior with prioritization

## Communication Patterns

### Direct Messaging
- Agent A sends request to Agent B, waits for response
- Use when: result needed before proceeding
- Risk: tight coupling, cascading failures
- Mitigation: timeouts, circuit breakers, fallback responses

### Event-Based (Pub/Sub)
- Agent emits event, any interested agent subscribes
- Use when: multiple agents may react to same event
- Benefits: loose coupling, easy to add new consumers
- Risk: event ordering, eventual consistency

### Broadcast
- One agent sends message to all agents
- Use when: system-wide state changes (user login, config update)
- Keep payloads small, filter on receiver side

### Negotiation Protocol
- Agent A proposes action, Agent B accepts/rejects/counter-proposes
- Use when: conflicting goals, resource contention
- Implement timeout to prevent deadlocks

### Message Format Checklist
- [ ] Unique message ID for correlation
- [ ] Source agent identifier
- [ ] Target agent (or broadcast indicator)
- [ ] Message type / action
- [ ] Payload (typed, validated)
- [ ] Timestamp
- [ ] Version (for backward compatibility)

## Coordination Strategies

### Task Delegation
- Route tasks by category to specialized agents
- Maintain a capability registry (agent > capabilities map)
- Fallback to general agent if specialist unavailable
- Track delegation chain for debugging

### Collaborative Problem Solving
1. Primary agent receives request
2. Analyzes request, identifies needed capabilities
3. Requests input from specialist agents (parallel when possible)
4. Synthesizes responses into final answer
5. Records collaboration for learning

### Conflict Resolution
| Strategy | When to Use |
|----------|-------------|
| Priority-based | Clear hierarchy exists |
| Voting/consensus | Peer agents, democratic decision |
| First-responder | Speed matters more than optimality |
| Arbitration | Dedicated coordinator resolves disputes |

### Resource Sharing
- Shared state: use read-write locks (concurrent reads, exclusive writes)
- Resource pools: semaphores for limited resources (API rate limits)
- Message queues: buffer work for processing at agent's pace

## Agent Lifecycle Management

### Lifecycle Phases
1. **Initialization**: Load config, restore state, establish connections
2. **Activation**: Begin accepting requests, start background tasks
3. **Active Operation**: Process requests, emit events, coordinate
4. **Dormancy**: Reduce resource usage, persist state, stop background tasks
5. **Shutdown**: Complete in-flight work, persist final state, release resources

### State Persistence
- Persist agent state on every significant change
- Restore state on initialization (crash recovery)
- Include: conversation history, user preferences, pending tasks
- Prune old data based on retention policies

### Context Management
- Maintain conversation history per user per agent
- Prune history to fit context window (keep most recent)
- Summarize old context instead of discarding entirely
- Store knowledge items with embeddings for semantic retrieval

## LLM Integration Patterns

### System Prompt Design
- Define agent identity and personality in first paragraph
- Include user preferences as context
- Inject recent conversation history
- Add relevant knowledge items from retrieval
- Keep total prompt within model context limits

### Context Window Management
- Track token usage across system prompt + history + knowledge + user input
- Reserve tokens for response generation
- Prune oldest messages first, preserve system prompt
- Consider summarization for long conversations

### Response Streaming
- Stream tokens to UI for real-time feedback
- Buffer partial words for clean display
- Allow user to interrupt/cancel generation
- Accumulate full response for storage after completion

### Knowledge Retrieval (RAG)
1. Embed user query with same model used for knowledge base
2. Compute similarity (cosine) against stored embeddings
3. Retrieve top-K relevant items
4. Inject into prompt as context
5. Generate response grounded in retrieved knowledge

## Design Principles

### Single Responsibility
- Each agent has one clear purpose
- Avoid "god agents" that do everything
- Split when an agent accumulates unrelated capabilities

### Loose Coupling
- Agents communicate through well-defined interfaces
- No agent reaches into another's internal state
- Use events for cross-cutting concerns

### Autonomy
- Each agent can operate independently
- Graceful degradation when other agents are unavailable
- Local state sufficient for core functionality

### Transparency
- Users understand what agents are doing and why
- Agents explain their reasoning when asked
- Actions are auditable and traceable

### Privacy
- Agents access only data they need
- User data boundaries enforced at the interface level
- No cross-user data leakage in shared agent instances

## Agent Testing

### Test Levels
| Level | What to Test |
|-------|-------------|
| Unit | State transitions, intent parsing, response formatting |
| Integration | Agent-to-agent communication, backend calls |
| Behavioral | End-to-end user scenarios, conversation flows |
| Performance | Response latency, context window management |

### Test Checklist
- [ ] All state transitions produce correct next state
- [ ] Invalid transitions are rejected with clear errors
- [ ] Inter-agent messages are correctly formatted
- [ ] Agent recovers from errors without crashing
- [ ] Context pruning preserves critical information
- [ ] Concurrent requests handled without state corruption
- [ ] Agent shuts down cleanly with state persisted
