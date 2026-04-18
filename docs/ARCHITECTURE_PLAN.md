# Architecture Plan

> **Note**: This file is the legacy risk-graded plan template referenced by
> `/qor-audit` Step 2 and `/qor-substantiate` Step 2. For system architecture
> (layer stack, component relationships, extension points), see
> **[docs/architecture.md](architecture.md)** (the Phase 30 system-tier doc).
>
> ARCHITECTURE_PLAN.md remains as a pre-phase risk template; architecture.md
> is the canonical architecture reference.

## Risk Grade: L2

### Risk Assessment

- [ ] Contains security/auth logic -> L3
- [x] Modifies existing workflows -> L2 (skill compilation affects governance behavior)
- [ ] UI-only changes -> L1

## Three-Layer Pipeline

```
ingest/                          ← Raw skills dumped here (any format)
  ├── third-party/               ← Skills from external sources
  ├── internal/                  ← Skills authored internally
  └── experimental/              ← Work-in-progress skills

processed/                       ← S.H.I.E.L.D. compliant (canonical)
  ├── qor-bootstrap.md
  ├── qor-plan.md
  ├── qor-audit.md
  ├── qor-implement.md
  ├── qor-substantiate.md
  ├── qor-debug.md
  ├── qor-course-correct.md       ← NEW: drift recovery
  └── ...

compiled/                        ← LLM-specific output
  ├── .claude/
  │   └── skills/{name}/SKILL.md
  ├── .agent/
  │   └── workflows/{name}.md
  └── .kilocode/
      └── workflows/{name}.md
```

## Personas (Skill Actors)

| Persona | Role | Skills |
|---------|------|--------|
| Governor | Planning, alignment, routing | qor-bootstrap, qor-plan, qor-repo-release |
| Judge | Audit, substantiation, verdicts | qor-audit, qor-substantiate, qor-validate |
| Specialist | Implementation, precision build | qor-implement, qor-refactor |
| Fixer | Debugging, root-cause analysis | qor-debug |
| Navigator | Drift recovery, course correction | qor-course-correct |
| Strategist | Research, evidence gathering | qor-research |

## Processing Rules

Every processed skill MUST have:
1. `<skill>` trigger block with phase and persona
2. Execution protocol with numbered steps
3. Constraints section (NEVER/ALWAYS rules)
4. Success criteria (checkboxes)
5. Integration section (how it connects to S.H.I.E.L.D.)

## Compilation Targets

| Target | Format | Output Path |
|--------|--------|-------------|
| Claude Code | SKILL.md with YAML frontmatter | compiled/.claude/skills/{name}/SKILL.md |
| Agent Workflows | Markdown with workflow headers | compiled/.agent/workflows/{name}.md |
| Kilocode | Markdown with kilocode headers | compiled/.kilocode/workflows/{name}.md |

## Collaborative Design Integration

All planning skills (qor-bootstrap, qor-plan) MUST include:
- One question at a time dialogue
- Multiple choice preferred
- 2-3 approach proposals with trade-offs
- Incremental design validation (200-300 word sections)
- YAGNI enforcement

## Section 4 Razor Pre-Check

- [x] All planned functions <= 40 lines (scripts only)
- [x] All planned files <= 250 lines (skill files)
- [x] No planned nesting > 3 levels

---

*Blueprint sealed. Awaiting GATE tribunal.*
