# Skill Audit Checklist (B7)

Quality gate for evaluating S.H.I.E.L.D. governance skills.
Use during `/ql-audit` or manual review. Every skill must pass Section 1.
Sections 2-5 apply based on skill type.

---

## 1. Structural Compliance

Automated by `process-skills.py`. All items are hard requirements.

- [ ] Has `<skill>` trigger block with `phase` and `persona` attributes
- [ ] Has `## Execution Protocol` with numbered steps
- [ ] Has `## Constraints` with NEVER/ALWAYS rules
- [ ] Has `## Success Criteria` with checkboxes (`- [ ]`)
- [ ] Has `## Integration` section
- [ ] File is under 250 lines
- [ ] Has YAML frontmatter with `name` and `description` fields

**Fail condition:** Any unchecked item blocks promotion to canonical.

---

## 2. Content Quality

Manual review. Evaluates clarity and reusability.

- [ ] **Purpose** states what the skill does in 1-2 sentences (no filler)
- [ ] Each execution step has a **concrete action** (verb + object), not vague guidance
- [ ] Constraints use **bold NEVER/ALWAYS** format consistently
- [ ] Success criteria are **verifiable** (measurable or binary, not subjective)
- [ ] Integration section explains how this skill **connects to other skills**
- [ ] No project-specific references — skill is generic/canonical
- [ ] No duplicate content with other registered skills

### Red Flags

| Issue | Example |
|---|---|
| Vague step | "Consider the architecture" |
| Subjective criterion | "Code is clean" |
| Project leak | "Update the FailSafe ledger" |
| Missing verb | "Error handling" (step without action) |

---

## 3. Lifecycle Coherence

Validates correct placement in the S.H.I.E.L.D. lifecycle.

- [ ] Successor skills referenced in Integration exist in the skill registry
- [ ] **Phase** assignment matches the S.H.I.E.L.D. lifecycle stage
  - `plan` / `audit` / `implement` / `harden` / `deploy`
- [ ] **Persona** assignment matches ARCHITECTURE_PLAN persona table
- [ ] No circular handoff chains (A -> B -> C -> A)
- [ ] Interdictions reference **correct prerequisite artifacts**
  - e.g., "requires approved architecture doc" before implementation

### Handoff Validation

Trace the routing path from the skill under review:

```
this-skill -> successor-1 -> successor-2 -> terminal
```

Confirm: path terminates, no loops, each successor exists.

---

## 4. Section 4 Razor + Code Quality Doctrine

Applies only to skills that **generate or template code**.
Reference: `ingest/internal/references/doctrine-code-quality.md`

- [ ] Template/example functions are under **40 lines** each
- [ ] Reference file patterns are under **250 lines**
- [ ] No nested ternaries in examples
- [ ] No `unwrap()` in Rust examples (use `?` or explicit error handling)
- [ ] Max nesting depth of **3** in any code block
- [ ] Functions classifiable as **semantic** (pure, no side effects) or **pragmatic** (orchestrator, documented)
- [ ] Models use **enums over optional fields** where states are mutually exclusive
- [ ] Domain primitives use **brand types** (not bare String/Uuid)
- [ ] No generic names (`process`, `handle`, `manage`) without domain qualifier

**Skip condition:** Mark N/A if the skill does not produce code artifacts.

---

## 5. Collaborative Design

Applies only to **planning-phase skills** (phase: `plan`).

- [ ] Uses **one-question-at-a-time** dialogue pattern
- [ ] Proposes **2-3 approaches** with explicit trade-offs per decision point
- [ ] **YAGNI enforcement** present — skill actively discourages speculative features
- [ ] Questions use multiple-choice format where applicable
- [ ] Incremental validation — each answer feeds the next question

**Skip condition:** Mark N/A if the skill phase is not `plan`.

---

## Audit Verdict

| Result | Meaning |
|---|---|
| **PASS** | All applicable sections clear |
| **CONDITIONAL** | Section 1 passes, minor issues in Sections 2-5 with fix plan |
| **FAIL** | Section 1 incomplete or critical issues in any section |

Record verdict and findings in the meta-ledger entry for the skill.
