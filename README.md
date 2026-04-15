<p align="center">
  <strong>QoreLogic</strong><br>
  Canonical S.H.I.E.L.D. Skills Repository
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-BSL--1.1-orange" alt="License: BSL-1.1">
  <img src="https://img.shields.io/badge/SSoT-qor/-blue" alt="SSoT: qor/">
  <img src="https://img.shields.io/badge/Ledger-Entry%20%2319-green" alt="Ledger: Entry #19">
</p>

---

## SSoT layout (as of 2026-04-15)

All canonical content lives under **`qor/`**. Legacy pipeline directories (`ingest/`, `kilo-code/`, `deployable state/`, `processed/`, `compiled/`) have been retired; snapshots preserved under `docs/archive/2026-04-15/`.

```
qor/
  skills/<category>/     governance, sdlc, memory, meta, custom
  agents/<category>/     governance, sdlc, memory, meta
  vendor/                third-party skills and agents (~65 + wshobson)
  scripts/               ledger_hash.py, utilities/, legacy/
  references/            doctrine + patterns + ql-* examples
  experimental/          non-canonical research
  templates/             doc templates
```

See `docs/SYSTEM_STATE.md` for the full tree and `docs/SKILL_REGISTRY.md` for the category-organized skill index.

## Quick Start

### Claude Code

Hand-copy any skill directory you want from `qor/skills/<category>/<skill>/` into your project's `.claude/skills/`:

```bash
cp -r qor/skills/governance/qor-audit /path/to/your-project/.claude/skills/
```

Each skill is a self-contained `SKILL.md` file (with optional `references/` subdirectory). Claude Code discovers and loads these automatically.

Agents live at `qor/agents/<category>/<name>.md` — copy into `.claude/agents/` similarly.

### Kilocode

Same source; hand-copy `qor/skills/<category>/<skill>/` into your project's `.kilo/skills/`.

### Automated variant output (coming)

A compile pipeline that re-emits `qor/dist/variants/{claude,kilo-code,codex}/` from the `qor/skills/` SSoT is tracked in `docs/plan-qor-tooling-deferred.md` (Phase 2). Until then, consume directly from `qor/`.

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
Qor-logic/
  qor/                   <-- SSoT; edit here
    skills/
      governance/          qor-audit, qor-validate, qor-substantiate, qor-shadow-process,
                           qore-governance-compliance
      sdlc/                qor-research, qor-plan, qor-implement, qor-refactor, qor-debug,
                           qor-remediate
      memory/              qor-status, qor-document, qor-organize, log-decision,
                           track-shadow-genome, qore-docs-technical-writing
      meta/                qor-bootstrap, qor-help, qor-repo-audit, qor-repo-release,
                           qor-repo-scaffold, qore-meta-*
      custom/              (reserved for qor-scoped custom content)
    agents/
      governance/          qor-governor, qor-judge
      sdlc/                qor-specialist, qor-strategist, qor-fixer, qor-ux-evaluator,
                           project-planner
      memory/              qor-technical-writer, documentation-scribe, learning-capture
      meta/                agent-architect, system-architect, build-doctor
    vendor/
      agents/              7 generic specialists + third-party/ (wshobson-agents)
      skills/              ~65 third-party skill packs (tauri/, chrome-devtools/, custom/,
                           _system/, agents/, plus flat framework skills)
    scripts/
      ledger_hash.py       Content/chain hashing, manifest generation, chain verify
      calculate-session-seal.py
      legacy/              Pre-migration pipeline (preserved for reference)
      utilities/           Assorted utility scripts
    references/            Doctrine + patterns + ql-* examples
    experimental/          Non-canonical research (tauri2-*, tauri-launcher, build-doctor)
    templates/             Doc templates (ARCHITECTURE_PLAN, CONCEPT, SYSTEM_STATE, ...)
  docs/
    META_LEDGER.md         Hash-chained governance ledger (20 entries sealed)
    SHADOW_GENOME.md       Audit-verdict failure records
    PROCESS_SHADOW_GENOME.md  Process-failure log (JSONL append-only)
    SYSTEM_STATE.md        Current system snapshot
    SKILL_REGISTRY.md      Category-organized skill index
    plan-qor-*.md          Migration plan history
    migration-manifest-*.json
    archive/2026-04-15/    Pre-migration snapshots
  pyproject.toml           Python 3.11+, pytest, jsonschema
  README.md
```

## Pipeline (current state)

- **Edit**: `qor/skills/<category>/<skill>/SKILL.md` — canonical source.
- **Consume**: hand-copy directories into your project's `.claude/skills/` or `.kilo/skills/`.
- **Verify chain**: `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` — all entries OK.

## Pipeline (deferred)

A compile pipeline (`qor/scripts/compile.py`) that regenerates per-variant outputs under `qor/dist/variants/{claude,kilo-code,codex}/` from the SSoT is tracked in [`docs/plan-qor-tooling-deferred.md`](docs/plan-qor-tooling-deferred.md) (Phase 2). Pre-commit hook + CI drift check will prevent hand-edits to generated variants once Phase 2 ships.

Until then: no build step required — consume `qor/skills/` directly.

## Governance Skills

| Skill | Trigger | Phase | Persona | Category |
|-------|---------|-------|---------|----------|
| qor-audit | `/qor-audit` | GATE | Judge | governance |
| qor-validate | `/qor-validate` | ANY | Judge | governance |
| qor-substantiate | `/qor-substantiate` | SUBSTANTIATE | Judge | governance |
| qor-shadow-process | `/qor-shadow-process` | CROSS-CUTTING | Judge | governance (stub) |
| qor-research | `/qor-research` | RESEARCH | Analyst | sdlc |
| qor-plan | `/qor-plan` | PLAN | Governor | sdlc |
| qor-implement | `/qor-implement` | IMPLEMENT | Specialist | sdlc |
| qor-refactor | `/qor-refactor` | IMPLEMENT | Specialist | sdlc |
| qor-debug | `/qor-debug` | IMPL/SUBST/GATE | Fixer | sdlc |
| qor-remediate | `/qor-remediate` | RECOVER | Governor | sdlc (stub, absorbs qor-course-correct) |
| qor-status | `/qor-status` | ANY | Governor | memory |
| qor-document | `/qor-document` | DELIVER/IMPL | Tech Writer | memory |
| qor-organize | `/qor-organize` | ORGANIZE | Governor | memory |
| qor-bootstrap | `/qor-bootstrap` | ALIGN + ENCODE | Governor | meta |
| qor-help | `/qor-help` | ANY | Governor | meta |
| qor-repo-audit | `/qor-repo-audit` | AUDIT | Judge | meta |
| qor-repo-release | `/qor-repo-release` | DELIVER | Governor | meta |
| qor-repo-scaffold | `/qor-repo-scaffold` | IMPLEMENT | Specialist | meta |

### Lifecycle Coverage

```
ALIGN -> ENCODE -> PLAN -> GATE -> IMPLEMENT -> SUBSTANTIATE -> DELIVER
```

Cross-cutting: RESEARCH, DEBUG, STATUS, VALIDATE, ORGANIZE, RECOVER.

## Agent Personas

| Persona | Role |
|---------|------|
| qor-governor | Senior Architect -- ALIGN, ENCODE, LEDGER (`qor/agents/governance/`) |
| qor-judge | Security Auditor -- GATE, PASS/VETO (`qor/agents/governance/`) |
| qor-specialist | Implementation Expert -- ENCODE, VERIFY (`qor/agents/sdlc/`) |
| qor-strategist | Strategic planning and architecture (`qor/agents/sdlc/`) |
| qor-fixer | Diagnostic Specialist -- 4-layer root-cause (`qor/agents/sdlc/`) |
| qor-ux-evaluator | UI/UX testing -- Playwright, accessibility (`qor/agents/sdlc/`) |
| qor-technical-writer | Documentation quality -- README, API, changelog (`qor/agents/memory/`) |

Plus: `project-planner` (sdlc), `documentation-scribe`, `learning-capture` (memory), `agent-architect`, `system-architect`, `build-doctor` (meta).

Vendor agents (non-qor-scoped): `accessibility-specialist`, `code-reviewer`, `devops-engineer`, `tauri-launcher`, `ui-correction-specialist`, `ultimate-debugger`, `voice-integration-specialist` under `qor/vendor/agents/`, plus the wshobson-agents category collection under `qor/vendor/agents/third-party/`.

## Quality Gate

Every governance skill must pass the audit checklist defined in [`docs/SKILL_AUDIT_CHECKLIST.md`](docs/SKILL_AUDIT_CHECKLIST.md):

1. **Structural Compliance** -- trigger block, execution protocol, constraints, success criteria, integration section
2. **Content Quality** -- clear purpose, concrete actions, verifiable criteria, no project-specific references
3. **Lifecycle Coherence** -- correct phase/persona, valid handoff chains, no circular routing
4. **Section 4 Razor + Code Quality Doctrine** -- 40-line function limit, 250-line file limit, max nesting 3
5. **Collaborative Design** -- one-question-at-a-time dialogue, 2-3 approach proposals, YAGNI enforcement

Verdicts: PASS, CONDITIONAL (minor issues with fix plan), or FAIL.

## AI Code Quality Doctrine

Reference: `qor/references/doctrine-code-quality.md`

- **Semantic functions** -- pure, no side effects, single responsibility
- **Pragmatic functions** -- orchestration with documented side effects
- **Brand types** -- domain primitives over bare String/Uuid
- **Anti-slop** -- no generic names (`process`, `handle`, `manage`) without domain qualifier; no nested ternaries; enums over optional fields for mutually exclusive states

## License

BSL-1.1
