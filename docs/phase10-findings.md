# Phase 10 — E2E Findings

**Date**: 2026-04-15
**Test suite**: `tests/test_e2e.py` (9 tests, all passing)
**Total tests**: 117/117 (108 prior + 9 e2e)

Findings discovered while writing cross-module integration tests, plus workflow-bundle opportunities surfaced from grep + skill review.

## Gaps discovered

### Gap #1 — Adversarial mode requires detected.host, ignores declared.host_declared

**Location**: `qor/scripts/qor_audit_runtime.py::should_run_adversarial_mode`
**Surfaced in**: `tests/test_e2e.py::test_platform_marker_affects_audit_runtime`

`should_run_adversarial_mode` checks `qplat.current()["detected"]["host"] == "claude-code"`. `detected.host` is computed from env vars (`CLAUDE_PROJECT_DIR`) by `qor_platform.detect_host()`. Profile declarations populate `declared.host_declared` separately — they do NOT influence detection.

**Implication**: A user who applies `claude-code-with-codex` profile inside a harness that doesn't set `CLAUDE_PROJECT_DIR` (some test runners, CI containers, bare Codex CLI) will silently fall back to solo mode. The user's explicit choice is overridden by environment absence.

**Two valid stances**:
- **Detect-first (current)**: codex-plugin only runs in actual claude-code runtime; declaration without runtime is meaningless. Safe but surprising.
- **Declare-respects (alternative)**: if user explicitly applied a claude-code profile, trust the declaration; let it override detection. User-friendly but can produce wrong attempts.

**Recommendation**: Document the current behavior in `qor/platform/detect.md` and `qor/scripts/qor_audit_runtime.py`. Future Phase 11 may add an `enforce_declared` flag to allow user override.

**Status**: documented; no code change this phase.

### Gap #2 — No CLI to manually mark events `addressed=true` without an issue URL

**Location**: `qor/scripts/create_shadow_issue.py` (`--flip-only` requires URL)

Operators who resolve a process issue via direct action (not via GitHub issue) have no clean way to flip events. `--flip-only` requires `--URL`; `addressed_reason="resolved_without_issue"` exists in the schema but no script writes it.

**Recommendation**: Add `--mark-resolved` flag to `create_shadow_issue.py` that sets `addressed_reason="remediated"` with no URL. Future scope.

### Gap #3 — `tests/fixtures/skill_samples/` declared in plan but not authored

**Location**: `docs/plan-qor-ssot-minimal.md` referenced fixtures; never created.

E2E tests build inline fixtures via `tmp_path` instead. Acceptable for now, but if e2e suite expands, dedicated fixtures would centralize sample skill content.

**Recommendation**: Defer until next major test expansion. Inline fixtures are working.

### Gap #4 — `qor-deep-audit` is migrated but not yet test-covered

**Location**: `qor/skills/meta/qor-deep-audit/SKILL.md` (and recon/remediate sub-bundles)

These skills are markdown-only; their behavior is documented but not exercised. A bundle test would simulate a fixture-repo recon → brief → remediate flow with mocked subagent invocations.

**Recommendation**: Defer to a future phase that builds bundle-execution test infrastructure (subagent mocking is non-trivial).

### Gap #5 — Override log (`.qor/override.log`) is append-only with no rotation

**Location**: `.githooks/pre-commit`

The hook appends every BUILD_REGEN bypass forever. After many regenerations the log grows unbounded. Low-priority, but unbounded files violate token-efficiency doctrine indirectly (if any tool reads the log).

**Recommendation**: Add log rotation or a periodic compaction. Defer.

## Workflow-bundle opportunities

Per `qor/gates/workflow-bundles.md` "When to write a bundle" criteria (4+ skills, repeated invocation, mechanical decision points).

### Bundle candidate A — `qor-onboard-codebase` (HIGH value)

**Trigger**: absorbing an external codebase, evaluating an unfamiliar project.
**Phases**: `qor-research` → `qor-organize` → `qor-audit` → `qor-plan` (4 phases, common pattern)
**Checkpoints**: after-research, after-organize, after-audit
**Decomposition**: not needed (4 phases is manageable)
**Effort**: Small — the chain is well-understood; bundle is mostly orchestration prose.
**Recommend**: yes, build in next phase if onboarding workflows recur.

### Bundle candidate B — `qor-process-review-cycle` (MEDIUM value)

**Trigger**: periodic process health check (weekly/monthly).
**Phases**: `qor-shadow-process` (sweep) → `qor-remediate` (act) → `qor-audit` (verify proposed remediation) (3 phases)
**Checkpoints**: after-shadow-sweep (review findings before acting), after-remediate
**Decomposition**: not needed
**Effort**: Small.
**Recommend**: yes if process audits are run on a schedule.

### Bundle candidate C — `qor-release-cycle` (MEDIUM value)

**Trigger**: shipping a release.
**Phases**: `qor-validate` → `qor-substantiate` (re-seal) → `qor-repo-release` (3 phases)
**Checkpoints**: after-validate
**Decomposition**: not needed
**Effort**: Small.
**Recommend**: useful but only if release cadence justifies bundling.

### Bundle candidate D — `qor-bootstrap-flow` (LOW value, marginal)

**Trigger**: first-time setup.
**Phases**: `qor-repo-scaffold` → `qor-bootstrap` → `qor-organize` (3 phases)
**Checkpoints**: after-scaffold (operator confirms scaffolded structure before bootstrap)
**Effort**: Trivial.
**Recommend**: only if first-time setup happens often. Probably skip.

### Anti-bundles (do NOT build)

- `qor-everything` — kitchen-sink bundle. Fails the "mechanical decision points" test; too many branches.
- `qor-debug-then-fix` — `qor-debug` already names its handoffs per delegation table; bundling adds no value.
- `qor-audit-then-implement` — too thin (2 phases, already implicit in chain).

## Doctrine adherence check

E2E tests intentionally exercised the doctrines:

- ✅ Token-efficiency: tests reference modules by name, mock subprocess calls instead of running real binaries, use `tmp_path` instead of repo state.
- ✅ Delegation table: tests verify `should_run_adversarial_mode` correctly delegates to the platform marker (not inlined).
- ✅ Workflow-bundles: bundle SKILL.md files were not directly tested (markdown), but the underlying primitives bundles invoke (gate_chain, shadow_process) are now end-to-end verified.
- ✅ Session: tests confirm session id propagates through every module that consumes it.

## Recommended next phases

1. **Phase 11A** (small): Implement Gap #2 (`--mark-resolved` flag).
2. **Phase 11B** (small): Bundle candidate A (`qor-onboard-codebase`).
3. **Phase 11C** (small): Bundle candidate B (`qor-process-review-cycle`).
4. **Phase 12** (medium): Bundle execution test infrastructure (subagent mocking) → enables Gap #4 closure.

Each is independently scope-limited, per the lesson from the audit-loop incident: small surfaces produce fewer amendment-drift defects.
