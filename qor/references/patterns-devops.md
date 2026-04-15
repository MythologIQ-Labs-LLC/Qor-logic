# DevOps Patterns Reference

## CI/CD Pipeline Design

### Pipeline Stages (Standard Order)
1. **Lint** - Static analysis, formatting checks
2. **Test** - Unit tests, integration tests
3. **Build** - Compile, bundle, optimize
4. **Sign** - Code signing for distribution
5. **Package** - Create installers/artifacts
6. **Deploy** - Push to staging/production
7. **Verify** - Post-deployment smoke tests

### Pipeline Principles
- Fail fast: run cheapest checks first (lint before build)
- Parallelize independent stages (test frontend + backend simultaneously)
- Cache dependencies aggressively (node_modules, cargo registry, build artifacts)
- Use matrix builds for cross-platform (Linux, Windows, macOS)
- Keep pipeline under 10 minutes for developer feedback loops

### Quality Gates
| Gate | Criteria | Blocks |
|------|----------|--------|
| Lint | Zero warnings, formatting clean | Build |
| Type Check | Zero type errors | Build |
| Unit Tests | 100% pass, coverage threshold met | Build |
| Integration Tests | All scenarios pass | Deploy |
| Security Scan | No critical/high vulnerabilities | Deploy |
| Performance | Benchmarks within thresholds | Release |

## Deployment Strategies

### Blue-Green Deployment
- Maintain two identical environments (blue = current, green = new)
- Deploy to green, test, switch traffic
- Rollback: switch traffic back to blue
- Use when: zero-downtime required, full environment validation needed

### Canary Deployment
- Route small percentage of traffic to new version (1% > 5% > 25% > 100%)
- Monitor error rates and performance at each stage
- Rollback: route all traffic to old version
- Use when: gradual rollout with real user validation needed

### Rolling Deployment
- Update instances one at a time
- Always maintain minimum healthy instances
- Rollback: reverse the rolling update
- Use when: resource-constrained, can tolerate brief mixed versions

### Feature Flags
- Decouple deployment from release
- Enable gradual rollout by user segment
- Kill switch for problematic features
- Clean up flags after full rollout (prevent tech debt)

## Monitoring and Alerting

### Four Golden Signals
1. **Latency** - Time to serve requests (p50, p95, p99)
2. **Traffic** - Requests per second, concurrent users
3. **Errors** - Error rate (5xx, 4xx, exceptions)
4. **Saturation** - CPU, memory, disk, network utilization

### Logging Best Practices
- Use structured logging (JSON format with consistent fields)
- Include: timestamp, level, message, correlation_id, context
- Log levels: ERROR (action needed) > WARN (investigate) > INFO (audit) > DEBUG (dev)
- Never log secrets, PII, or credentials
- Set retention policies (30d hot, 90d warm, 1y cold)

### Alerting Rules
| Severity | Criteria | Response Time |
|----------|----------|---------------|
| Critical | Service down, data loss risk | < 15 min |
| High | Degraded performance, high error rate | < 1 hour |
| Medium | Elevated warnings, capacity concerns | < 4 hours |
| Low | Non-urgent issues, optimization opportunities | Next business day |

### Alert Design Principles
- Alert on symptoms (user impact), not causes
- Include runbook link in every alert
- Avoid alert fatigue: tune thresholds, suppress duplicates
- Page only for critical/high; ticket for medium/low

## Infrastructure as Code

### Principles
- All infrastructure defined in version-controlled files
- No manual changes to environments
- Environments reproducible from code alone
- Review infrastructure changes like code changes (PR process)

### Configuration Management
| Concern | Strategy |
|---------|----------|
| Environment config | Environment variables, config files per env |
| Feature flags | Remote config service, queryable at runtime |
| Secrets | Vault/keychain, injected at deploy time, never in code |
| Build config | Compiler flags, optimization levels in build scripts |
| Runtime config | User settings stored locally, defaults in code |

## Build Optimization

### Caching Strategy
- **Dependency cache**: Cache package manager downloads between builds
- **Build cache**: Cache intermediate compilation artifacts
- **Layer cache**: (Docker) Order Dockerfile from least to most changing
- **Artifact cache**: Reuse built artifacts across pipeline stages

### Build Speed Checklist
- [ ] Dependencies cached between runs
- [ ] Incremental compilation enabled
- [ ] Parallel builds enabled (multi-core)
- [ ] Only rebuild changed modules
- [ ] Pre-built binaries for stable dependencies
- [ ] Build machine appropriately sized

### Bundle Size Optimization
- Tree-shake unused code
- Code-split by route/feature (lazy loading)
- Compress assets (images, fonts)
- Analyze bundle composition (visualizer tools)
- Set size budgets and alert on regression

## Release Process

### Release Checklist
1. [ ] Version bumped in all manifests
2. [ ] Changelog updated with user-facing changes
3. [ ] All tests passing on all platforms
4. [ ] Release candidate tested manually
5. [ ] Tag created and pushed
6. [ ] CI builds all platform artifacts
7. [ ] Artifacts signed with release certificates
8. [ ] Release notes published
9. [ ] Update server/manifest updated
10. [ ] Rollback plan documented and tested

### Semantic Versioning
- **MAJOR** (X.0.0): Breaking changes, incompatible API
- **MINOR** (0.X.0): New features, backward compatible
- **PATCH** (0.0.X): Bug fixes, no new features

## Code Signing

### Platform Matrix
| Platform | Tool | Certificate Type |
|----------|------|-----------------|
| Windows | signtool | EV Code Signing (NSIS/MSI) |
| macOS | codesign + notarytool | Developer ID + Notarization |
| Linux | GPG | Package signing key |

### Signing Checklist
- [ ] Certificates stored securely (HSM or CI secrets)
- [ ] Timestamp server used (survives certificate expiry)
- [ ] Signature verified post-sign
- [ ] Certificate rotation planned before expiry

## Auto-Update Patterns

### Update Flow
1. Check for updates periodically (daily or on launch)
2. Download update in background
3. Notify user of available update
4. User approves or defers
5. Apply update (restart required)
6. Verify update integrity before applying

### Update Safety
- Verify update signature matches trusted public key
- Support rollback if update causes issues
- Allow users to skip versions
- Provide release notes before install

## Troubleshooting Framework

### Build Failure Diagnosis
1. **Read the error message** (exact line, exact file)
2. **Check recent changes** (git diff since last successful build)
3. **Clean and rebuild** (clear caches, fresh install)
4. **Check environment** (tool versions, OS differences)
5. **Isolate** (does it fail on CI only? locally only? one platform only?)

### Common Issues
| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Dependency conflict | Lock file stale | Delete lock + reinstall |
| Platform-specific failure | Missing system library | Install OS dependencies |
| Intermittent test failure | Race condition or external dependency | Add retries, mock externals |
| Binary too large | Unused dependencies, debug symbols | Audit deps, strip binaries |
| Slow builds | No caching, full rebuilds | Enable incremental + cache |

## Health Checks

### Application Health
- **Liveness**: Is the process running? (restart if not)
- **Readiness**: Can it handle requests? (remove from rotation if not)
- **Startup**: Has it finished initializing? (wait before routing traffic)

### Dependency Health
- Check database connectivity
- Verify external API reachability
- Monitor disk space and memory
- Track certificate expiry dates
