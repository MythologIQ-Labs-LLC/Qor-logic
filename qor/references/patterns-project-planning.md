# Project Planning Patterns Reference

## Requirements Analysis

### Gathering Methods
| Method | Best For |
|--------|----------|
| User stories | Capturing user intent and value |
| Use cases | Detailed interaction flows |
| Stakeholder interviews | Uncovering unstated needs |
| Prototyping | Validating assumptions early |
| Observation | Understanding real workflows |

### Requirements Types
- **Functional**: What the system does (features, behaviors, interactions)
- **Non-Functional**: How the system performs (speed, security, accessibility, scalability)
- **Constraints**: What limits the solution (budget, timeline, technology, compliance)

### Prioritization: MoSCoW Method
| Priority | Meaning | Guidance |
|----------|---------|----------|
| **Must** | Non-negotiable for release | Fails without it |
| **Should** | Important but not critical | Workaround exists |
| **Could** | Nice-to-have enhancement | Include if time allows |
| **Won't** | Explicitly excluded from scope | Document for future |

### Traceability
- Link every requirement to: implementation (code), test (verification), documentation
- Track status: Proposed > Approved > Implemented > Verified
- Flag orphan code (no requirement) and unimplemented requirements

## Work Breakdown

### Hierarchy
```
Epic (large initiative, months)
  Feature (deliverable capability, weeks)
    Story (user-visible increment, days)
      Task (developer action, hours)
```

### Estimation
| Technique | When to Use |
|-----------|-------------|
| T-shirt sizing (S/M/L/XL) | Early planning, relative comparison |
| Story points | Sprint planning, velocity tracking |
| Time-based (hours) | Individual task assignments |
| Three-point (optimistic/likely/pessimistic) | Risk-sensitive estimates |

### Estimation Checklist
- [ ] Broken into tasks under 8 hours each
- [ ] Dependencies identified between tasks
- [ ] Unknowns flagged as spikes (time-boxed research)
- [ ] Buffer added for integration and testing (20-30%)
- [ ] Historical velocity used to calibrate

### Wiring vs Building Decision
Before estimating implementation:
- **Wiring** (2-4 hours): Existing code exists but is disconnected. Connect it.
- **Building** (20-40 hours): No implementation exists. Create from scratch.
- Always search the codebase before assuming "building" is needed.

## Risk Assessment

### Risk Matrix
```
Impact       Low        Medium      High
Probability
High         Monitor    Mitigate    Urgent Action
Medium       Accept     Mitigate    Mitigate
Low          Accept     Monitor     Monitor
```

### Risk Register Template
| Risk | Impact | Probability | Mitigation | Owner | Status |
|------|--------|-------------|------------|-------|--------|
| [Description] | H/M/L | H/M/L | [Strategy] | [Name] | Open/Mitigated/Realized |

### Common Risk Categories
- **Technical**: Unproven technology, performance unknowns, integration complexity
- **Resource**: Key person dependency, skill gaps, capacity constraints
- **Schedule**: Dependency delays, scope creep, estimation errors
- **External**: Third-party API changes, vendor reliability, regulatory changes
- **Quality**: Insufficient testing, accessibility gaps, security vulnerabilities

### Mitigation Strategies
| Strategy | Description |
|----------|-------------|
| Avoid | Change plan to eliminate risk |
| Mitigate | Reduce probability or impact |
| Transfer | Shift risk to third party (insurance, SLA) |
| Accept | Acknowledge and plan contingency |

## Sprint Planning

### Sprint Structure
1. **Goal**: One sentence describing what the sprint achieves
2. **Committed Work**: Prioritized backlog items with estimates
3. **Capacity**: Available person-hours minus meetings/overhead (typically 60-70%)
4. **Risks**: Known blockers and mitigation plans
5. **Definition of Done**: Criteria for each item to be considered complete

### Definition of Done Checklist
- [ ] Code complete and peer reviewed
- [ ] Unit and integration tests written and passing
- [ ] Documentation updated (API docs, user docs if applicable)
- [ ] Accessibility verified (if UI change)
- [ ] No regressions in existing tests
- [ ] Merged to main branch

## Technical Specification

### Spec Document Structure
1. **Overview**: What problem does this solve and why now
2. **Requirements**: Functional + non-functional, with acceptance criteria
3. **Design**: Architecture, API contracts, data models, UI wireframes
4. **Implementation Plan**: Task breakdown with estimates and dependencies
5. **Testing Strategy**: How correctness will be verified
6. **Risks**: Technical risks specific to this feature
7. **Timeline**: Milestones and target dates

### Architecture Decision Record (ADR)
```
## Title: [Decision Name]
## Status: Proposed | Accepted | Deprecated | Superseded
## Context: What problem and constraints?
## Decision: What was chosen?
## Rationale: Why this option?
## Consequences: Positive, negative, trade-offs
## Alternatives: What else was considered and why rejected?
```

## Pre-Implementation Verification

### Before ANY implementation, verify:
- [ ] Searched codebase for existing implementations
- [ ] Checked for module directories matching feature name
- [ ] Read any completion/status documentation
- [ ] Checked git history for recent changes or backups
- [ ] Diagnosed WHY something doesn't work (not assumed missing)
- [ ] Estimated correctly (wiring vs building from scratch)

### Red Flags (Stop and Investigate)
- Substantial existing code directory for the feature
- Documentation says "complete" but user reports broken
- Files named `*_legacy.rs` or `*_old.rs` or `*.bak`
- Recent "backup" commits in git history
- Large line counts indicating mature implementation
- Manager/service structs already defined
- Database schemas already created

### Correct Verification Flow
1. Search for existing implementation (grep, file listing)
2. Check code size (line count indicates maturity)
3. Look for existing handlers/endpoints
4. Check wiring in entry point (is it imported/registered?)
5. Ask clarifying questions before implementing

## Stakeholder Communication

### Status Update Template
1. **Progress**: What was completed since last update
2. **Blockers**: What is preventing progress
3. **Risks**: New or escalated risks
4. **Next Steps**: What is planned next
5. **Asks**: What is needed from stakeholders

### Communication Principles
- Translate technical details to business impact
- Present trade-offs with clear pros/cons
- Manage expectations on scope and timeline proactively
- Use data (metrics, charts) over opinions
- Provide regular, predictable update cadence

## Feature Planning Template

```
# Feature: [Name]

## User Stories
- As a [user type], I want to [action] so that [benefit]

## Functional Requirements
1. The system shall [requirement]

## Non-Functional Requirements
- Performance: [metric and target]
- Accessibility: [WCAG criteria]
- Security: [considerations]

## Technical Design
- Architecture: [component diagram or description]
- Data Model: [schema changes]
- API: [interface definitions]

## Implementation Tasks
1. [ ] [Task] (estimate: Xh)

## Dependencies
- Depends on: [list]
- Blocks: [list]

## Risks
| Risk | Impact | Probability | Mitigation |

## Acceptance Criteria
- [ ] [Criterion]
- [ ] All tests passing
- [ ] Documentation updated
```

## Metrics

### Development Metrics
| Metric | What It Measures | Target |
|--------|-----------------|--------|
| Velocity | Story points per sprint | Stable trend |
| Cycle time | Idea to production | Decreasing |
| Bug density | Bugs per feature | < 1 critical/release |
| Code coverage | % of code tested | > 80% |

### Project Health Metrics
| Metric | What It Measures | Target |
|--------|-----------------|--------|
| On-time delivery | % features on schedule | > 80% |
| Scope change rate | Requirement changes per sprint | < 10% |
| Risk realization | Risks that materialized | Decreasing |
| Team satisfaction | Retrospective feedback | Improving |

## Agile Practices

### Ceremonies
| Ceremony | Purpose | Duration |
|----------|---------|----------|
| Sprint Planning | Commit to sprint goals and tasks | 1-2 hours |
| Daily Standup | Surface blockers, sync progress | 15 min |
| Sprint Review | Demo completed work to stakeholders | 1 hour |
| Retrospective | Identify improvements to process | 45 min |
| Backlog Grooming | Refine upcoming stories, estimate | 1 hour |
