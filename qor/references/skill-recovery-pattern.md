# Skill Recovery Pattern Reference

Canonical recovery templates skills paste into their interdiction blocks.
Single source of truth; the lint test reads this file and uses its marker
tokens as the expected pattern signature.

See `qor/references/doctrine-prompt-resilience.md` for the autonomy
classification and banned-phrase list.

## Interactive skills (default)

Every `autonomy: interactive` skill with a prerequisite check uses this
pattern:

```markdown
**INTERDICTION**: If `<artifact-path>` does not exist:

<!-- qor:recovery-prompt -->
Ask the user: "<artifact-path> not found. Should I correct it by running 'qorlogic seed' or pause? [Y/n]"

- On Y or empty: run `qorlogic seed` (idempotent), then continue.
- On N: abort with "Run `qorlogic seed` to create the governance scaffold, then re-run this skill."
```

If the skill is deliberately fail-fast (no self-heal offered), use the
justified override:

```markdown
**INTERDICTION**: If `<artifact-path>` does not exist:

<!-- qor:fail-fast-only reason="skill operates on content that must be author-supplied" -->
Abort with "Author <artifact-path> before re-running."
```

## Autonomous skills (deep-audit family, unattended-run)

Every `autonomy: autonomous` skill with a prerequisite check uses this
pattern:

```markdown
**INTERDICTION**: If `<artifact-path>` does not exist:

<!-- qor:auto-heal -->
Run `qorlogic seed` automatically (idempotent). Do not prompt the user. Continue the skill.

<!-- qor:break-the-glass reason="seed scaffold could not be created or is corrupt" -->
If auto-heal itself fails or leaves the artifact malformed: emit "EMERGENCY: <artifact-path> could not be auto-created. Manual intervention required. Check filesystem permissions and re-run 'qorlogic seed'." Abort.
```

## Marker reference

| Marker | Used in | Purpose |
|--------|---------|---------|
| `<!-- qor:recovery-prompt -->` | interactive | Y/N recovery prompt precedes the prerequisite-missing branch |
| `<!-- qor:fail-fast-only reason="..." -->` | interactive | justified pure abort (rare) |
| `<!-- qor:auto-heal -->` | autonomous | silent `qorlogic seed` on missing prereq |
| `<!-- qor:break-the-glass reason="..." -->` | autonomous | emergency surface when auto-heal fails |
| `<!-- qor:allow-pause reason="..." -->` | interactive | justifies a banned phrase appearing legitimately (e.g., user-facing risky action confirmation) |

## Enforcement

`tests/test_prompt_resilience_lint.py` requires:

- Zero banned phrases without `qor:allow-pause` justification.
- Every `ABORT`/`INTERDICTION` in an interactive skill has `qor:recovery-prompt`
  OR `qor:fail-fast-only` within 10 lines.
- Every `ABORT`/`INTERDICTION` in an autonomous skill has `qor:auto-heal` OR
  `qor:break-the-glass` within 10 lines.
- No autonomous skill contains `qor:recovery-prompt`.
