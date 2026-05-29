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
  `qor-logic seed`. Zero Y/N prompts.

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
  `qor-logic seed` invocation.
- `<!-- qor:break-the-glass reason="..." -->` -- autonomous skill, emergency
  surface when auto-heal itself fails; emits `EMERGENCY:` message and aborts.

## Governance Artifact Health (Phase 109)

**Governance Artifact Health** is the classification of every required
governance artifact into exactly one status before a skill reads or routes from
it. The checker `qor.scripts.governance_health` returns, per artifact, a status
and the single legal next action:

| Status | Meaning | Legal next | Blocking? |
|--------|---------|-----------|-----------|
| `OK` | passes the checks the invoking skill requires | continue lifecycle | no |
| `UNINITIALIZED` | no ledger and no project DNA | `/qor-bootstrap` (or `qor-logic seed` in autonomous mode) | yes, until seeded |
| `MISSING` | initialized workspace, required artifact absent | `qor-logic seed` for scaffold-owned files; otherwise `/qor-remediate` | yes, until repaired |
| `DAMAGED` | exists but fails parse, structure, or ledger-chain verification | `/qor-remediate` | **yes, always** |
| `INCOMPLETE` | exists but is an unfilled placeholder / has unresolved markers / lacks required sections | complete the named sections | **yes, always** |

An **Ungoverned Path Forward** is any continuation a prompt invents when a
required artifact is not `OK` -- synthesizing a plan, audit, implementation, or
seal from assumptions instead of surfacing the checker's `legal_next`. It is
always invalid. A preflight failure can never be converted into governed work by
assumption.

Decision contract:

- `UNINITIALIZED` and scaffold-owned `MISSING` are the **only** states a skill may
  resolve with `qor-logic seed` (interactive: offer Y/N; autonomous: seed
  silently). Non-scaffold `MISSING` routes to `/qor-remediate`.
- `DAMAGED` and `INCOMPLETE` are **blocking** and never seed/bootstrap-repairable.
  They block forward progress for every skill except one whose sole purpose is
  repair (`/qor-remediate`). Seeding or bootstrapping over a `DAMAGED` artifact
  risks overwriting authoritative content (R2) and is forbidden.

## Skill-active env management (Phase 111; #138)

Scripts must self-manage the `QOR_SKILL_ACTIVE` provenance env var via
`gate_chain.skill_active(<phase>)` (or the `skill=<phase>` parameter on
`gate_chain.write_gate_artifact`) rather than relying on a leak-prone inline
shell prefix (`QOR_SKILL_ACTIVE=plan python ...`). The context manager sets the
var for the wrapped scope and restores the prior value on exit, so a status
surface that reads `$QOR_SKILL_ACTIVE` cannot observe a stale phase between
subprocess calls. Status surfaces should read the authoritative active-phase
reporter `python -m qor.scripts.active_phase` (newest gate-artifact `phase`),
not the ambient env var.

## Enforcement

- `tests/test_prompt_resilience_lint.py` walks `qor/skills/**/*.md`, reads
  the autonomy mode, and enforces mode-specific rules. It also asserts the
  doctrine and recovery-pattern files define both `DAMAGED` and `INCOMPLETE`
  as blocking (no ungoverned path forward).
- `tests/test_skill_prerequisite_coverage.py` locks the autonomy inventory
  and asserts every ABORT/INTERDICTION site has the correct marker.
- `tests/test_governance_prompt_health_coverage.py` maps every source skill's
  governance-artifact reads to a `qor:governance-health-preflight` marker or a
  justified `qor:governance-health-exempt` exemption.

See `qor/references/skill-recovery-pattern.md` for the canonical templates
authors paste into skill bodies, including the governance-health preflight.
