# Architecture Patterns Reference

## Architectural Styles

### Layered Architecture
- Presentation > Application > Domain > Infrastructure
- Each layer depends only on the layer below
- Use when: clear separation of concerns needed, team split by layer

### Hexagonal (Ports & Adapters)
- Core domain has no external dependencies
- Ports define interfaces, adapters implement them
- Use when: need to swap infrastructure (DB, APIs) without touching business logic

### Clean Architecture
- Entities > Use Cases > Interface Adapters > Frameworks
- Dependency rule: inner layers never reference outer layers
- Use when: long-lived applications requiring testability

### Event-Driven Architecture
- Components communicate through events, not direct calls
- Variants: event notification, event-carried state transfer, event sourcing
- Use when: loose coupling, async processing, audit trails needed

## Design Principles

### SOLID
- **S** Single Responsibility: one reason to change per module
- **O** Open/Closed: extend behavior without modifying existing code
- **L** Liskov Substitution: subtypes must be substitutable for base types
- **I** Interface Segregation: prefer small, focused interfaces
- **D** Dependency Inversion: depend on abstractions, not concretions

### Supporting Principles
- **DRY**: Extract repeated logic, but avoid premature abstraction
- **KISS**: Simplest solution that meets requirements
- **YAGNI**: Do not build for speculative future needs
- **Separation of Concerns**: Each module addresses one concern
- **High Cohesion / Loose Coupling**: Related logic together, minimal dependencies between modules

## Distributed Systems Patterns

### Event Sourcing
- Store state changes as immutable events, not current state
- Rebuild state by replaying events
- Benefits: full audit trail, temporal queries, event replay
- Costs: eventual consistency, increased storage, replay complexity

### CQRS (Command Query Responsibility Segregation)
- Separate read and write models
- Commands mutate state, queries read optimized projections
- Use when: read/write patterns differ significantly

### Saga Pattern
- Coordinate distributed transactions across services
- **Choreography**: each service emits events, others react
- **Orchestration**: central coordinator manages steps
- Both require compensating actions for rollback

### Communication Patterns
| Pattern | When to Use |
|---------|-------------|
| Request-Response | Synchronous, result needed immediately |
| One-Way Messaging | Fire-and-forget, no response needed |
| Pub/Sub | Multiple consumers, decoupled producers |
| Streaming | Continuous data flow, real-time updates |

### Consistency Models
- **Strong consistency**: all reads see latest write (simplest, lowest throughput)
- **Eventual consistency**: reads converge to latest write (highest throughput)
- **CAP theorem**: choose 2 of 3 (Consistency, Availability, Partition tolerance)

## Reliability Patterns

### Circuit Breaker
- States: Closed (normal) > Open (failing, reject calls) > Half-Open (test recovery)
- Track failure count, open after threshold, attempt reset after timeout

### Retry with Backoff
- Exponential backoff: delay = base * 2^attempt
- Add jitter to prevent thundering herd
- Set max retries to avoid infinite loops

### Graceful Degradation
- Return cached data when upstream is unavailable
- Disable non-critical features under load
- Provide clear user feedback about reduced functionality

## Security Architecture

### Threat Modeling (STRIDE)
| Threat | Definition | Mitigation |
|--------|-----------|------------|
| **S**poofing | Impersonating a user or system | Authentication, signatures |
| **T**ampering | Modifying data or code | Integrity checks, signing |
| **R**epudiation | Denying an action occurred | Audit logs, timestamps |
| **I**nformation Disclosure | Exposing data | Encryption, access control |
| **D**enial of Service | Making system unavailable | Rate limiting, redundancy |
| **E**levation of Privilege | Gaining unauthorized access | Least privilege, RBAC |

### Auth Patterns
- **RBAC**: Role-Based Access Control (assign permissions to roles)
- **ABAC**: Attribute-Based Access Control (policies based on attributes)
- **JWT**: Stateless tokens for API auth (validate signature, check expiry)
- **OAuth2**: Delegated authorization for third-party access

### Data Security Checklist
- [ ] Encrypt data at rest (AES-256-GCM or similar)
- [ ] Encrypt data in transit (TLS 1.2+)
- [ ] Store secrets in OS keychain or vault, never in code
- [ ] Use parameterized queries (prevent SQL injection)
- [ ] Validate and sanitize all input
- [ ] Prevent path traversal (canonicalize + prefix check)
- [ ] Apply least-privilege file system scoping
- [ ] Maintain audit trails for sensitive operations

## Performance Engineering

### Caching Strategy
- **L1 (In-memory)**: LRU cache for hot data, low latency
- **L2 (Persistent)**: Database/disk cache for larger datasets
- Read-through: check cache first, fetch on miss, populate cache
- Set TTL based on data freshness requirements
- Invalidate on write to prevent stale data

### Optimization Checklist
- [ ] Profile before optimizing (identify actual bottlenecks)
- [ ] Optimize algorithmic complexity first (O(n) vs O(n^2))
- [ ] Batch I/O operations (reduce round trips)
- [ ] Use connection pooling for database/network
- [ ] Lazy load non-critical data
- [ ] Parallelize independent operations
- [ ] Index database columns used in WHERE/JOIN clauses

### Memory Management
- Use memory pools for frequent allocations
- Detect leaks with profiling tools
- Set resource limits and monitor usage
- Prefer stack allocation for short-lived data

## Database Design

### Schema Decisions
| Approach | When to Use |
|----------|-------------|
| Normalized (3NF) | Write-heavy, data integrity critical |
| Denormalized | Read-heavy, query performance critical |
| JSON columns | Semi-structured data, schema flexibility |
| Full-text search | Natural language queries (FTS5, Elasticsearch) |

### Migration Strategy
- Version all schema changes sequentially
- Make changes backward compatible when possible
- Test migrations against production-sized data
- Always provide rollback scripts

## Architecture Decision Records (ADR)

### Template
```
## Title: [Decision Name]
## Status: Proposed | Accepted | Deprecated | Superseded
## Context: What problem are we solving? What constraints exist?
## Decision: What did we choose?
## Consequences: What are the trade-offs?
## Alternatives Considered: What else was evaluated and why rejected?
```

## Architecture Review Checklist

- [ ] Requirements (functional + non-functional) clearly defined
- [ ] Appropriate architectural pattern selected with rationale
- [ ] Component boundaries and interfaces well-defined
- [ ] Data flow mapped end-to-end
- [ ] Security threats identified and mitigated
- [ ] Performance bottlenecks anticipated
- [ ] Error handling and recovery strategy defined
- [ ] Trade-offs documented in ADRs
- [ ] Migration path from current state defined
