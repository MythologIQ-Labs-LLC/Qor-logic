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
Ask the user: "<artifact-path> not found. Should I correct it by running 'qor-logic seed' or pause? [Y/n]"

- On Y or empty: run `qor-logic seed` (idempotent), then continue.
- On N: abort with "Run `qor-logic seed` to create the governance scaffold, then re-run this skill."
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
Run `qor-logic seed` automatically (idempotent). Do not prompt the user. Continue the skill.

<!-- qor:break-the-glass reason="seed scaffold could not be created or is corrupt" -->
If auto-heal itself fails or leaves the artifact malformed: emit "EMERGENCY: <artifact-path> could not be auto-created. Manual intervention required. Check filesystem permissions and re-run 'qor-logic seed'." Abort.
```

## Governance-health preflight (Phase 109)

Every source skill that reads, writes, or routes based on governance artifacts
(`docs/META_LEDGER.md`, `docs/CONCEPT.md`, `docs/ARCHITECTURE_PLAN.md`,
`docs/SYSTEM_STATE.md`, `docs/BACKLOG.md`, `docs/FEATURE_INDEX.md`,
`docs/GOVERNANCE_INDEX.md`, `.qor/gates/`, `.agent/staging/`) MUST carry the
preflight marker unless it has a justified exemption. The preflight runs the
health checker BEFORE the governance read and refuses to invent an
ungoverned path forward on `DAMAGED` / `INCOMPLETE`.

Interactive and autonomous skills share one preflight marker:

```markdown
<!-- qor:governance-health-preflight -->
Run `qor-logic governance-health --profile skill-entry` before reading governance artifacts. If any finding is `DAMAGED` or `INCOMPLETE`, do not continue: report the finding's `path`, `reason`, and `legal_next`. Only `UNINITIALIZED` or scaffold-owned `MISSING` may be resolved by `qor-logic seed` (interactive: offer Y/N; autonomous: seed silently). `DAMAGED` and `INCOMPLETE` always route to `/qor-remediate` or section completion -- never to seed or bootstrap.
```

Skills that mention a governance path only in documentation, examples, or as the
bootstrap skill's inverse guard declare an exemption instead:

```markdown
<!-- qor:governance-health-exempt reason="documentation-only reference; no live governance read" -->
```

The `reason` string is mandatory; an exemption without one is a lint failure.

**Governance Repair Mode**: when the preflight reports a `DAMAGED` or
`INCOMPLETE` finding, the skill enters Governance Repair Mode -- forward
lifecycle motion is blocked and the only legal next action is `/qor-remediate`
(damaged) or completing the named artifact sections (incomplete). Seeding or
bootstrapping over the unhealthy artifact is forbidden. Only `/qor-remediate`
itself is exempt, since its sole purpose is to operate on the unhealthy state.

## Marker reference

| Marker | Used in | Purpose |
|--------|---------|---------|
| `<!-- qor:recovery-prompt -->` | interactive | Y/N recovery prompt precedes the prerequisite-missing branch |
| `<!-- qor:fail-fast-only reason="..." -->` | interactive | justified pure abort (rare) |
| `<!-- qor:auto-heal -->` | autonomous | silent `qor-logic seed` on missing prereq |
| `<!-- qor:break-the-glass reason="..." -->` | autonomous | emergency surface when auto-heal fails |
| `<!-- qor:allow-pause reason="..." -->` | interactive | justifies a banned phrase appearing legitimately (e.g., user-facing risky action confirmation) |
| `<!-- qor:governance-health-preflight -->` | both | runs the health checker before a governance read; blocks on DAMAGED/INCOMPLETE |
| `<!-- qor:governance-health-exempt reason="..." -->` | both | justifies a governance-path mention that is not a live read |

## Enforcement

`tests/test_prompt_resilience_lint.py` requires:

- Zero banned phrases without `qor:allow-pause` justification.
- Every `ABORT`/`INTERDICTION` in an interactive skill has `qor:recovery-prompt`
  OR `qor:fail-fast-only` within 10 lines.
- Every `ABORT`/`INTERDICTION` in an autonomous skill has `qor:auto-heal` OR
  `qor:break-the-glass` within 10 lines.
- No autonomous skill contains `qor:recovery-prompt`.
