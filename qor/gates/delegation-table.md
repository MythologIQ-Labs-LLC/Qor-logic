# Qor Skill Delegation Table

**Doctrine**: Skills name skills explicitly. When skill X detects condition Y, the legal next action is invoking skill Z — not reinventing Z's process inline.

This table is the single source of truth for cross-skill handoffs. Every `/qor-*` skill must consult this when emitting "next action" guidance.

## Delegation matrix

| Detector | Condition | Delegate to | Rationale |
|---|---|---|---|
| `qor-audit` | Section 4 Razor violation (functions >40 lines, files >250 lines, nesting >3, ternaries) | `/qor-refactor` | refactor owns file-internal logic shape |
| `qor-audit` | Orphan file detected | `/qor-organize` | organize owns project-level structure |
| `qor-audit` | Macro-level architecture breach (cyclic deps, mixed domains, layering reversal) | `/qor-organize` | structural concerns are organize's domain |
| `qor-audit` | PASS verdict | `/qor-implement` | next phase in chain |
| `qor-audit` | VETO with security L3 | `/qor-debug` (root cause) then `/qor-refactor` or `/qor-implement` | security findings need diagnosis before fix |
| `qor-research` | Research complete | `/qor-plan` | next phase in chain |
| `qor-research` | Project-structure questions surface | `/qor-organize` | restructuring is organize's domain, not plan's |
| `qor-plan` | Plan complete | `/qor-audit` | next phase in chain |
| `qor-plan` | Architectural restructuring needed | `/qor-organize` | organize owns directory topology |
| `qor-implement` | Implementation complete | `/qor-substantiate` | next phase in chain |
| `qor-implement` | Mid-implement Razor bloat detected | `/qor-refactor` | refactor enforces Section 4 |
| `qor-implement` | Regression / hallucination / degradation detected | `/qor-debug` | debug owns root-cause analysis |
| `qor-refactor` | File-internal refactor reveals project-level issue | `/qor-organize` | scope escalation; organize handles project shape |
| `qor-refactor` | Refactor complete | `/qor-audit` (re-audit) or `/qor-substantiate` (if mid-implement) | depends on entry point |
| `qor-substantiate` | Section 4 violation detected post-build | `/qor-refactor` | enforce Razor before sealing |
| `qor-substantiate` | Reality != Promise (missing files, broken tests) | `/qor-debug` (diagnose) then return to `/qor-implement` | diagnose root cause; don't reseal until fixed |
| `qor-substantiate` | PASS verdict | `/qor-validate` (if formal validation phase needed) or `/qor-repo-release` | sealed; ready for downstream |
| `qor-validate` | Repeat failure across cycles (3+ same root cause) | `/qor-remediate` | process-level concern, not code-level |
| `qor-debug` | Root cause is process gap (gate skipped, capability shortfall) | `/qor-remediate` | code is fine; the workflow needs adjustment |
| `qor-debug` | Root cause is code defect | `/qor-implement` (with fix scoped) or `/qor-refactor` | per defect class |
| any phase | Process Shadow Genome threshold (sev sum >= 10) | `/qor-remediate` | auto-triggered by `qor/scripts/check_shadow_threshold.py` |
| any phase | Capability shortfall (codex-plugin, agent-teams missing on host that supports them) | log via `qor_platform.is_available` + `shadow_process.append_event` | non-blocking; logged for trend analysis |

## Cross-cutting skills (no fixed handoff)

These skills are invokable from any phase. They have no chain prior, no chain successor — they're tools, not stages.

| Skill | When to invoke | Notes |
|---|---|---|
| `/qor-status` | Any time | Diagnose lifecycle stage + next action; pure read |
| `/qor-tone` | Any time | Session-level communication tier selector (technical / standard / plain) |
| `/qor-document` | Any time | Author / update governance docs |
| `/qor-organize` | Any time (also as destination from `qor-audit` Orphan/Macro VETO) | Project-level structure |
| `/qor-debug` | After any phase that emits regression / hallucination / degradation | Cross-cutting diagnosis |
| `/qor-help` | Any time | Command catalog (display-only) |
| `/qor-shadow-process` | Auto-invoked by override paths and capability-shortfall handlers | Append-only shadow event recorder |
| `/qor-governance-compliance` | Periodic governance audit; before release | Workspace hygiene + sensitive file checks |
| `/qor-docs-technical-writing` | Documentation needs structured authoring | Migrated qore-* skill |
| `/qor-meta-log-decision` | Major decision points (ADR-style) | Migrated qore-* skill |
| `/qor-meta-track-shadow` | Cross-cycle pattern detection | Migrated qore-* skill |

## Repo-level meta skills (workspace lifecycle)

These operate on the workspace itself, outside per-feature SDLC chains.

| Skill | When to invoke | Notes |
|---|---|---|
| `/qor-bootstrap` | New workspace genesis | Originator; creates ledger Genesis entry |
| `/qor-repo-scaffold` | New repo from template | Pre-bootstrap |
| `/qor-repo-audit` | Repo-level audit (not per-feature) | Independent of SDLC chain |
| `/qor-repo-release` | Release ceremony | After substantiate + validate PASS; consumes accumulated release doc |

## Workflow bundles (multi-skill orchestration)

Bundles are not invoked AS handoff destinations — operators invoke them directly. Listed here for traceability.

| Bundle | First constituent | When to invoke directly |
|---|---|---|
| `/qor-deep-audit` | (decomposed; runs recon then remediate) | Pre-release readiness, large tech-debt sweeps |
| `/qor-deep-audit-recon` | `/qor-research` (subagents) | Investigation only; ends at RESEARCH_BRIEF |
| `/qor-deep-audit-remediate` | `/qor-plan` | Action half; consumes RESEARCH_BRIEF |
| `/qor-onboard-codebase` | `/qor-research` | Inheriting / merging an external codebase |
| `/qor-process-review-cycle` | `check_shadow_threshold.py` | Periodic process health check |

## Anti-patterns this prevents

- **Inline reinvention**: `qor-audit` says "fix the 60-line function" without naming `/qor-refactor`. Reader interprets this as "do it yourself" rather than invoking the dedicated skill.
- **Process invention in implementation**: `qor-implement` notices file is bloating, inlines its own Section 4 enforcement instead of pausing to `/qor-refactor`.
- **Code-level fix for process problem**: regression keeps recurring; team writes more tests when the actual issue is the gate sequence (skipped audit, missing capability). `/qor-remediate` is the right tool.
- **Scope creep within a skill**: `qor-refactor` notices the project is structurally a mess; instead of escalating to `/qor-organize`, it tries to do project-level reshaping inside a file-internal pass.

## Update protocol

When a new skill is added or an existing skill gains a new failure mode, update this table BEFORE wiring the new SKILL.md. Skills must reference this table; the table must not lag the skills.

## Verification

`grep -E "^\| .qor-" qor/gates/delegation-table.md` returns the matrix rows. CI gate (future): every chain skill's SKILL.md must reference at least one row from this table.
