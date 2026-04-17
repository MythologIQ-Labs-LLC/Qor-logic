# Doctrine: Prompt Resilience

> Skills pause only at genuine decision points. A genuine decision point
> requires user input that changes the outcome -- not confirmation that the
> next mechanical step may occur.

## Failure modes

1. **Over-pausing**: skills stop mid-workflow and wait for "ok" / "proceed" /
   "continue?" acknowledgements that add no decision value. This trains the
   operator to say "proceed" reflexively and blurs real decision points into
   noise.
2. **Hidden prerequisite assumptions**: skills ABORT on missing governance
   artifacts (`docs/META_LEDGER.md`, `.agent/staging/`, `.qor/gates/`) with
   opaque errors instead of offering self-heal or emitting a clear, actionable
   prerequisite message naming the missing path and the exact recovery command.

## Autonomy classification

Every `/qor-*` skill declares `autonomy: autonomous | interactive` in its
SKILL.md frontmatter. Missing or unset defaults to `interactive`.

- **interactive** -- may pause at genuine decision points; uses the Y/N
  recovery prompt when a prerequisite is missing.
- **autonomous** -- runs start-to-finish without user interaction except for
  break-the-glass emergencies. Missing prerequisites auto-heal via
  `qorlogic seed`. Zero Y/N prompts.

The classification is terminal. A skill that needs occasional user input is
`interactive` by definition.

### Inventory

**Autonomous** (as of Phase 25): `qor-deep-audit`, `qor-deep-audit-recon`,
`qor-deep-audit-remediate`. Any future unattended-run skill.

**Interactive**: every other `/qor-*` skill.

## Banned phrases

The following are banned in skill bodies unless each occurrence is justified
by a preceding `<!-- qor:allow-pause reason="..." -->` marker. Autonomous
skills MAY NOT use the allow-pause marker at all -- any pause in an
autonomous skill is a lint failure.

- `wait for user`
- `confirm before`
- `pause here`
- `Ready to proceed?`
- `Continue?`
- `Ask the user to proceed`

Enforced codebase-wide by `tests/test_prompt_resilience_lint.py`.

## Canonical recovery markers

The lint recognizes four markers. Their canonical templates live in
`qor/references/skill-recovery-pattern.md`.

- `<!-- qor:recovery-prompt -->` -- interactive skill, missing prerequisite,
  Y/N recovery prompt.
- `<!-- qor:fail-fast-only reason="..." -->` -- interactive skill, missing
  prerequisite, justified pure abort (rare).
- `<!-- qor:auto-heal -->` -- autonomous skill, missing prerequisite, silent
  `qorlogic seed` invocation.
- `<!-- qor:break-the-glass reason="..." -->` -- autonomous skill, emergency
  surface when auto-heal itself fails; emits `EMERGENCY:` message and aborts.

## Enforcement

- `tests/test_prompt_resilience_lint.py` walks `qor/skills/**/*.md`, reads
  the autonomy mode, and enforces mode-specific rules.
- `tests/test_skill_prerequisite_coverage.py` locks the autonomy inventory
  and asserts every ABORT/INTERDICTION site has the correct marker.

See `qor/references/skill-recovery-pattern.md` for the canonical templates
authors paste into skill bodies.
