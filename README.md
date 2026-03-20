# Qorelogic -- Canonical S.H.I.E.L.D. Skills Repository

Single source of truth for all governance skills used by LLM agents across MythologIQ projects.

> BSL-1.1 Licensed | https://github.com/MythologIQ/QoreLogic

## Pipeline

```
ingest/ -> processed/ -> compiled/
```

**ingest/** -- Raw skills from any source. Organized into `internal/` (governance, agents, references), `third-party/` (external agent definitions), and `experimental/` (work-in-progress).

**processed/** -- Skills normalized to S.H.I.E.L.D. structural compliance. Every file has a trigger block, execution protocol, constraints, success criteria, and integration section.

**compiled/** -- LLM-specific output in `.claude/`, `.agent/`, and `.kilocode/` formats. Downstream projects consume only from this stage.

## Inventory

| Category | Count | Location |
|----------|-------|----------|
| Governance skills | 17 | `ingest/internal/governance/` |
| Agent personas | 6 | `ingest/internal/agents/` |
| Reference docs | 15 | `ingest/internal/references/` |
| Third-party agents | 229 | `ingest/third-party/agents/` (10 categories) |
| Pipeline scripts | 7 | `scripts/` |

## Governance Skills

| Skill | Trigger | Phase | Persona |
|-------|---------|-------|---------|
| ql-bootstrap | `/ql-bootstrap` | ALIGN + ENCODE | Governor |
| ql-plan | `/ql-plan` | PLAN | Governor |
| ql-audit | `/ql-audit` | GATE | Judge |
| ql-implement | `/ql-implement` | IMPLEMENT | Specialist |
| ql-refactor | `/ql-refactor` | IMPLEMENT | Specialist |
| ql-substantiate | `/ql-substantiate` | SUBSTANTIATE | Judge |
| ql-repo-release | `/ql-repo-release` | DELIVER | Governor |
| ql-debug | `/ql-debug` | IMPL/SUBST/GATE | Fixer |
| ql-course-correct | `/ql-course-correct` | RECOVER | Navigator |
| ql-research | `/ql-research` | RESEARCH | Analyst |
| ql-document | `/ql-document` | DELIVER/IMPL | Tech Writer |
| ql-validate | `/ql-validate` | ANY | Judge |
| ql-status | `/ql-status` | ANY | Governor |
| ql-help | `/ql-help` | ANY | Governor |
| ql-organize | `/ql-organize` | ORGANIZE | Governor |
| ql-repo-audit | `/ql-repo-audit` | AUDIT | Judge |
| ql-repo-scaffold | `/ql-repo-scaffold` | IMPLEMENT | Specialist |

### Lifecycle Coverage

```
ALIGN -> ENCODE -> PLAN -> GATE -> IMPLEMENT -> SUBSTANTIATE -> DELIVER
```

Cross-cutting: RESEARCH, DEBUG, STATUS, VALIDATE, ORGANIZE, RECOVER.

## Agent Personas

| Persona | Role |
|---------|------|
| ql-governor | Senior Architect -- ALIGN, ENCODE, LEDGER |
| ql-judge | Security Auditor -- GATE, PASS/VETO |
| ql-specialist | Implementation Expert -- ENCODE, VERIFY |
| ql-fixer | Diagnostic Specialist -- 4-layer root-cause |
| ql-technical-writer | Documentation quality -- README, API, changelog |
| ql-ux-evaluator | UI/UX testing -- Playwright, accessibility |

## Scripts

| Script | Purpose |
|--------|---------|
| `process-skills.py` | Normalize raw skills to S.H.I.E.L.D. compliance |
| `compile-claude.py` | Compile to Claude Code SKILL.md format |
| `compile-agent.py` | Compile to Agent workflow format |
| `compile-all.py` | Run all compilation targets |
| `intent-lock.py` | Lock skill intent to prevent drift |
| `admit-skill.py` | Admit a new skill into the pipeline |
| `gate-skill-matrix.py` | Validate skill matrix against registry |

## Usage

### Processing

```bash
python scripts/process-skills.py
```

Reads from `ingest/`, normalizes structure, writes to `processed/`.

### Compiling

```bash
python scripts/compile-all.py
```

Reads from `processed/`, writes LLM-specific formats to `compiled/`.

### Consuming

Downstream projects reference compiled output via the `QORELOGIC_SKILLS_PATH` environment variable:

```bash
export QORELOGIC_SKILLS_PATH="G:/MythologIQ/Qorelogic/compiled"
```

Never edit skills inside downstream project repos. All changes flow through the Qorelogic pipeline.

### Compilation Targets

| Target | Format | Output Path |
|--------|--------|-------------|
| Claude Code | SKILL.md with YAML frontmatter | `compiled/.claude/skills/{name}/SKILL.md` |
| Agent Workflows | Markdown with workflow headers | `compiled/.agent/workflows/{name}.md` |
| Kilocode | Markdown with kilocode headers | `compiled/.kilocode/workflows/{name}.md` |

## Quality Gate

Every governance skill must pass the audit checklist defined in `docs/SKILL_AUDIT_CHECKLIST.md`. The five required sections:

1. **Structural Compliance** -- trigger block, execution protocol, constraints, success criteria, integration section
2. **Content Quality** -- clear purpose, concrete actions, verifiable criteria, no project-specific references
3. **Lifecycle Coherence** -- correct phase/persona, valid handoff chains, no circular routing
4. **Section 4 Razor + Code Quality Doctrine** -- 40-line function limit, 250-line file limit, max nesting 3 (applies to code-generating skills only)
5. **Collaborative Design** -- one-question-at-a-time dialogue, 2-3 approach proposals, YAGNI enforcement (applies to planning-phase skills only)

Verdicts: PASS, CONDITIONAL (minor issues with fix plan), or FAIL.

## AI Code Quality Doctrine

Reference: `ingest/internal/references/doctrine-code-quality.md`

Governance rules for code generated by or with LLM agents:

- **Semantic functions** -- pure, no side effects, single responsibility
- **Pragmatic functions** -- orchestration with documented side effects
- **Brand types** -- domain primitives over bare String/Uuid
- **Anti-slop** -- no generic names (`process`, `handle`, `manage`) without domain qualifier; no nested ternaries; enums over optional fields for mutually exclusive states

## License

BSL-1.1
