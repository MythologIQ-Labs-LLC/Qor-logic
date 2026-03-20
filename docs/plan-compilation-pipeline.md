# Plan: Compilation Pipeline (B2 + B3)

## Open Questions

None — target formats are defined in ARCHITECTURE_PLAN.md and validated against existing FailSafe-Pro SKILL.md files.

## Phase 1: Claude Code Compiler (B2)

### Affected Files

- `scripts/compile-claude.py` — NEW: compile processed/ → compiled/.claude/skills/{name}/SKILL.md
- `compiled/.claude/skills/` — OUTPUT directory (17 skill subdirectories)

### Changes

Create `compile-claude.py` that:

1. Reads each `processed/*.md` file
2. Parses existing YAML frontmatter (name, description)
3. Adds Claude Code fields: `user-invocable: true`, `allowed-tools: Read, Glob, Grep, Edit, Write, Bash`
4. Writes to `compiled/.claude/skills/{name}/SKILL.md`

Transformation is minimal — processed skills already have the right body format. The compiler adds Claude Code-specific YAML fields and creates the directory-per-skill structure.

Reference files (`processed/references/*.md`) are NOT compiled — they stay as shared references that skills point to via relative paths.

```python
# Core logic (pseudocode)
for skill in processed/*.md:
    frontmatter = parse_yaml(skill)
    frontmatter['user-invocable'] = True
    frontmatter['allowed-tools'] = 'Read, Glob, Grep, Edit, Write, Bash'
    body = extract_body(skill)
    output = f"compiled/.claude/skills/{frontmatter['name']}/SKILL.md"
    write(output, serialize_yaml(frontmatter) + body)
```

### Unit Tests

- Run compiler, verify 17 SKILL.md files created in correct subdirectories
- Verify each output has valid YAML frontmatter with all required fields
- Verify body content matches processed/ source exactly

## Phase 2: Agent Workflow Compiler (B3)

### Affected Files

- `scripts/compile-agent.py` — NEW: compile processed/ → compiled/.agent/workflows/{name}.md
- `compiled/.agent/workflows/` — OUTPUT directory (17 workflow files)

### Changes

Create `compile-agent.py` that:

1. Reads each `processed/*.md` file
2. Strips YAML frontmatter (agent workflows don't use YAML)
3. Adds workflow header block with metadata extracted from `<skill>` tag
4. Writes to `compiled/.agent/workflows/{name}.md`

Workflow header format:

```markdown
# Workflow: {name}
# Phase: {phase}
# Persona: {persona}
# Trigger: {trigger}

---

[skill body without YAML frontmatter]
```

```python
# Core logic (pseudocode)
for skill in processed/*.md:
    frontmatter = parse_yaml(skill)
    skill_meta = parse_skill_block(skill)  # extract from <skill> tag
    body = extract_body(skill)
    header = f"# Workflow: {frontmatter['name']}\n# Phase: {skill_meta['phase']}\n..."
    output = f"compiled/.agent/workflows/{frontmatter['name']}.md"
    write(output, header + "\n---\n\n" + body)
```

### Unit Tests

- Run compiler, verify 17 workflow files created
- Verify each output has workflow header with Phase/Persona/Trigger
- Verify no YAML frontmatter in output
- Verify body content preserved

## Phase 3: Combined Runner + Backlog Update

### Affected Files

- `scripts/compile-all.py` — NEW: orchestrator that runs both compilers
- `docs/BACKLOG.md` — Mark B2, B3 complete

### Changes

Create `compile-all.py` that:

1. Runs `process-skills.py` (validate ingest → processed)
2. Runs `compile-claude.py` (processed → compiled/.claude/)
3. Runs `compile-agent.py` (processed → compiled/.agent/)
4. Reports counts and any errors

```bash
python scripts/compile-all.py
# Output:
# Processed: 17 skills, 14 references
# Compiled (Claude Code): 17 SKILL.md files
# Compiled (Agent Workflows): 17 workflow files
```

### Unit Tests

- Run compile-all.py end-to-end
- Verify all three stages complete without error
- Verify final file counts match processed/ count
