# Doctrine: Communication Tiers

> Output register should match the reader. Hash-chained evidentiary artifacts
> stay technical; operator-facing prose adapts to the audience.

Inspired by the MIT-licensed `caveman` project
(https://github.com/JuliusBrussee/caveman). The compression angle there maps
to a register angle here: same substance, different density of jargon.

## Tiers

### technical

Full jargon. SG IDs, OWASP tags, `file:line` citations, hash values,
Merkle seals, doctrine citations inline. Audience: engineers, auditors,
governance reviewers. Default tier.

**Example**: `A08 / SG-Phase25-B: tone_aware flag declared without backing
section; lint fails at qor/skills/memory/qor-status/SKILL.md:42. Run
/qor-refactor to close.`

### standard

Complete sentences. Technical terms introduced inline on first use. File
paths and commands preserved. SG IDs omitted unless load-bearing. Audience:
mixed stakeholders who need enough context to act but not the full
doctrine apparatus.

**Example**: `The audit found a data-integrity issue (category A08): a flag
was declared in the skill's metadata without any corresponding behavior in
the skill body. The file qor/skills/memory/qor-status/SKILL.md needs a
rendering section added. Run /qor-refactor.`

### plain

No jargon. No SG/OWASP tags. No hash-style tokens in the body (footnote if
needed). Short declarative sentences. Explicit next-step commands. Audience:
non-technical operators, executive summaries.

**Example**: `The plan has a problem: it claims the skill can do something
but the skill file is missing the part that actually does it. Edit the skill
to add the missing section, then re-check.`

## Selection order

1. **Session override** -- a `/qor-tone <tier>` directive in the current
   agent-session window sets the tier for the remainder of the session.
2. **Workspace config** -- `.qorlogic/config.json`'s `tone` field. Written
   by `qorlogic init --tone <tier>`.
3. **Default** -- `"technical"`.

## How skills read the tone value

Tone-aware skills (those with `tone_aware: true` in frontmatter) resolve
the tier at rendering time using this order. Python callers use the helper
`qor.tone.resolve_tone(session_override, config_path)`. Agent-rendered
skills branch on the resolved value when producing output text.

Every `tone_aware: true` skill MUST include a `## Output rendering by tone`
section delimited by `<!-- qor:tone-aware-section -->` / `<!-- /qor:tone-aware-section -->`
markers with three sub-sections (one per tier) giving concrete rendering
instructions.

## Evidentiary-artifact exclusion

Tier selection does NOT apply to hash-chained or evidentiary content:

- `docs/META_LEDGER.md` entries
- `docs/SHADOW_GENOME.md` entries
- Any content written to `.qor/gates/<session>/*.json`
- Merkle seal text, chain hashes, content hashes

These stay technical-only for integrity. Any skill that writes to these
artifacts MUST declare `tone_aware: false` in frontmatter. Enforced by
`tests/test_tone_skill_frontmatter.py`.

## Enforcement

- `tests/test_tone_resolution.py` -- resolution order + doctrine presence
  check.
- `tests/test_tone_config_persistence.py` -- `qorlogic init --tone` writes
  the config field.
- `tests/test_tone_skill_frontmatter.py` -- every skill declares
  `tone_aware`; tone-aware skills have rendering sections; evidentiary
  skills do NOT have `tone_aware: true`.
- `tests/test_tone_rendering_example.py` -- canonical example
  (`qor/skills/memory/qor-status/SKILL.md`) passes tier-register heuristics.
