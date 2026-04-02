<p align="center">
  <strong>QoreLogic</strong><br>
  Canonical S.H.I.E.L.D. Skills Repository
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-BSL--1.1-orange" alt="License: BSL-1.1">
  <img src="https://img.shields.io/badge/Skills-17-blue" alt="Skills: 17">
  <img src="https://img.shields.io/badge/Agents-8-green" alt="Agents: 8">
</p>

---

Single source of truth for all governance skills used by LLM agents across MythologIQ projects. Skills are authored once, validated through a structured pipeline, and compiled to proprietary deployable formats for Claude Code and Kilocode.

## Quick Start

### Claude Code

Copy the deployable skills and agents into your project's `.claude/` directory:

```
deployable state/claude/
  skills/    ->  your-project/.claude/skills/
  agents/    ->  your-project/.claude/agents/
```

Each skill is a self-contained `SKILL.md` file inside a named directory (e.g. `qor-plan/SKILL.md`). Each agent is a single `.md` file (e.g. `qor-governor.md`). Claude Code discovers and loads these files automatically.

See [`deployable state/claude/`](deployable%20state/claude/) for the full 17-skill, 8-agent suite ready to drop in.

### Kilocode

Copy the deployable skills and agents into your project's `.kilo/` directory:

```
deployable state/kilo-code/
  qor-*/      ->  your-project/.kilo/skills/qor-*/
  agents/     ->  your-project/.kilo/agents/
```

Alternatively, the same compiled output lives at [`kilo-code/`](kilo-code/) in the repository root.

Each skill directory contains a `SKILL.md` (with optional `references/` subdirectory for bundled reference material). Each agent is a single `.md` file. Kilocode discovers and loads these files via its skill resolution system.

See [`deployable state/kilo-code/`](deployable%20state/kilo-code/) for the full 17-skill, 8-agent suite ready to drop in.

## Proprietary Formats

Both Claude Code and Kilocode consume Markdown files with YAML frontmatter and structured XML sections. The format is identical across targets.

### Skill File Structure (`SKILL.md`)

```
qor-plan/
  SKILL.md          <-- skill definition (YAML frontmatter + structured body)
  references/       <-- optional bundled reference docs
    some-ref.md
```

**YAML Frontmatter:**

| Field | Description |
|-------|-------------|
| `name` | Skill identifier (e.g. `qor-plan`) |
| `description` | One-line summary used by the LLM for skill routing |
| `metadata.category` | Classification (e.g. `development`, `governance`) |
| `metadata.author` | Originating author or org |
| `metadata.source` | Repository URL and source path |

**Body Structure (XML-annotated sections):**

| Section | Purpose |
|---------|---------|
| `<skill>` | Trigger, phase, persona, and output declaration |
| Purpose | What the skill does and when to invoke it |
| Core Principles | Domain-specific rules and constraints |
| Execution Protocol | Step-by-step procedure the agent follows |
| Constraints | Hard rules that must not be violated |
| Success Criteria | Verifiable conditions for completion |
| Integration | How this skill hands off to other skills |

### Agent File Structure (`qor-*.md`)

```
agents/
  qor-governor.md   <-- agent persona definition
  qor-judge.md
  ...
```

**YAML Frontmatter:**

| Field | Description |
|-------|-------------|
| `name` | Agent identifier |
| `description` | One-line summary |
| `tools` | Allowed tool set (e.g. `Read, Glob, Grep, Edit, Write, Bash`) |
| `model` | Model override or `inherit` |

**Body Structure (XML-annotated sections):**

| Section | Purpose |
|---------|---------|
| `<agent>` | Agent name, description, and tool declarations |
| Persona | Behavioral identity and domain expertise |
| Principles | Decision-making guidelines |
| Execution Pattern | How the agent reasons and operates |
| Handoff Protocol | When and how to transfer control |

## Repository Structure

```
QoreLogic/
  deployable state/       <-- READY-TO-DEPLOY outputs (copy these)
    claude/                 Claude Code format
      skills/               17 governance skills
      agents/               8 agent personas
    kilo-code/              Kilocode format
      qor-*/                17 governance skills (one per directory)
      agents/               8 agent personas
  kilo-code/              <-- Same compiled output, repo-root mirror
    qor-*/
  .claude/                 Claude Code skills loaded in this repo
  ingest/                  Raw skill sources
    internal/               Governance skills, agents, references
    third-party/            External agent definitions
    experimental/           Work-in-progress
  processed/               Pipeline-normalized skills
  compiled/                Intermediate compilation output
  scripts/                 Pipeline tooling
  docs/                    Architecture, registry, audit checklists
```

## Pipeline

```
ingest/ -> processed/ -> compiled/ -> deployable state/
```

- **ingest/** -- Raw skills from any source. `internal/` for governance, `third-party/` for external agents, `experimental/` for WIP.
- **processed/** -- Skills normalized to S.H.I.E.L.D. structural compliance.
- **compiled/** -- LLM-specific intermediate output.
- **deployable state/** -- Final, copy-ready artifacts for Claude Code and Kilocode.

### Pipeline Scripts

| Script | Purpose |
|--------|---------|
| `process-skills.py` | Normalize raw skills to S.H.I.E.L.D. compliance |
| `compile-claude.py` | Compile to Claude Code `SKILL.md` format |
| `compile-agent.py` | Compile to Agent workflow format |
| `compile-all.py` | Run all compilation targets |
| `intent-lock.py` | Lock skill intent to prevent drift |
| `admit-skill.py` | Admit a new skill into the pipeline |
| `gate-skill-matrix.py` | Validate skill matrix against registry |

```bash
python scripts/process-skills.py    # ingest/ -> processed/
python scripts/compile-all.py       # processed/ -> compiled/
```

Downstream projects reference compiled output via:

```bash
export QORELOGIC_SKILLS_PATH="G:/MythologIQ/Qorelogic/deployable state"
```

Never edit skills inside downstream project repos. All changes flow through the QoreLogic pipeline.

## Governance Skills

| Skill | Trigger | Phase | Persona |
|-------|---------|-------|---------|
| qor-bootstrap | `/qor-bootstrap` | ALIGN + ENCODE | Governor |
| qor-plan | `/qor-plan` | PLAN | Governor |
| qor-audit | `/qor-audit` | GATE | Judge |
| qor-implement | `/qor-implement` | IMPLEMENT | Specialist |
| qor-refactor | `/qor-refactor` | IMPLEMENT | Specialist |
| qor-substantiate | `/qor-substantiate` | SUBSTANTIATE | Judge |
| qor-repo-release | `/qor-repo-release` | DELIVER | Governor |
| qor-debug | `/qor-debug` | IMPL/SUBST/GATE | Fixer |
| qor-course-correct | `/qor-course-correct` | RECOVER | Navigator |
| qor-research | `/qor-research` | RESEARCH | Analyst |
| qor-document | `/qor-document` | DELIVER/IMPL | Tech Writer |
| qor-validate | `/qor-validate` | ANY | Judge |
| qor-status | `/qor-status` | ANY | Governor |
| qor-help | `/qor-help` | ANY | Governor |
| qor-organize | `/qor-organize` | ORGANIZE | Governor |
| qor-repo-audit | `/qor-repo-audit` | AUDIT | Judge |
| qor-repo-scaffold | `/qor-repo-scaffold` | IMPLEMENT | Specialist |

### Lifecycle Coverage

```
ALIGN -> ENCODE -> PLAN -> GATE -> IMPLEMENT -> SUBSTANTIATE -> DELIVER
```

Cross-cutting: RESEARCH, DEBUG, STATUS, VALIDATE, ORGANIZE, RECOVER.

## Agent Personas

| Persona | Role |
|---------|------|
| qor-governor | Senior Architect -- ALIGN, ENCODE, LEDGER |
| qor-judge | Security Auditor -- GATE, PASS/VETO |
| qor-specialist | Implementation Expert -- ENCODE, VERIFY |
| qor-fixer | Diagnostic Specialist -- 4-layer root-cause |
| qor-technical-writer | Documentation quality -- README, API, changelog |
| qor-ux-evaluator | UI/UX testing -- Playwright, accessibility |
| qor-strategist | Strategic planning and architecture |
| qor-ultimate-debugger | Deep diagnostic investigation |

## Quality Gate

Every governance skill must pass the audit checklist defined in [`docs/SKILL_AUDIT_CHECKLIST.md`](docs/SKILL_AUDIT_CHECKLIST.md):

1. **Structural Compliance** -- trigger block, execution protocol, constraints, success criteria, integration section
2. **Content Quality** -- clear purpose, concrete actions, verifiable criteria, no project-specific references
3. **Lifecycle Coherence** -- correct phase/persona, valid handoff chains, no circular routing
4. **Section 4 Razor + Code Quality Doctrine** -- 40-line function limit, 250-line file limit, max nesting 3
5. **Collaborative Design** -- one-question-at-a-time dialogue, 2-3 approach proposals, YAGNI enforcement

Verdicts: PASS, CONDITIONAL (minor issues with fix plan), or FAIL.

## AI Code Quality Doctrine

Reference: `ingest/internal/references/doctrine-code-quality.md`

- **Semantic functions** -- pure, no side effects, single responsibility
- **Pragmatic functions** -- orchestration with documented side effects
- **Brand types** -- domain primitives over bare String/Uuid
- **Anti-slop** -- no generic names (`process`, `handle`, `manage`) without domain qualifier; no nested ternaries; enums over optional fields for mutually exclusive states

## License

BSL-1.1
