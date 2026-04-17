# Plan: Phase 25 -- Prompt Resilience + Workspace Seed + Communication Tiers

**change_class**: feature

## Open Questions

- `qorlogic seed --force` (overwrite existing) -- deferred to a follow-up. MVP is idempotent: skip files that already exist, log skipped names.
- Does `seed` also create a `.gitignore` section for `.qor/session/`? Current assumption: yes -- session directory is runtime-only, should not be committed. A `.gitignore` stub is idempotent-safe.
- `qor-bootstrap` overlap: `qor-bootstrap` already exists as a skill for first-time workspace init. `seed` is the non-interactive subset -- it creates the file scaffold; `qor-bootstrap` remains the guided workflow that ALSO authors `CONCEPT.md` and `ARCHITECTURE_PLAN.md` content. Plan treats `seed` as lower-level primitive; `qor-bootstrap` can call it internally in a follow-up phase.

## Goal

Three coupled capabilities:

1. **`qorlogic seed`** -- a new top-level CLI subcommand that scaffolds the governance files skills assume (META_LEDGER, SHADOW_GENOME, ARCHITECTURE_PLAN stub, CONCEPT stub, SYSTEM_STATE stub, plus required directories). Idempotent; does not overwrite existing files.
2. **Skill prompt resilience** -- codify a doctrine banning (a) hidden file-existence assumptions and (b) gratuitous "proceed?" pauses. Apply the pattern to every `/qor-*` skill that currently ABORTs on missing governance artifacts, replacing bare aborts with a single Y/N "correct it or pause?" prompt that, on Y, invokes `qorlogic seed` and continues. Deep-audit family skills run autonomously with auto-heal instead of Y/N.
3. **Communication tiers** -- audience-aware output. Three tiers selected by a `/qor-tone` slash command (session-sticky) and persisted in `.qorlogic/config.json`. Inspired by the MIT-licensed `caveman` project (https://github.com/JuliusBrussee/caveman). Orthogonal to autonomy: a plain-tier autonomous skill still auto-heals silently; only its EMERGENCY surfacing text changes register.

## Design summary

- **`qorlogic seed` is a primitive.** It writes a fixed set of stubs and creates a fixed set of directories. No branching logic, no flags (MVP). Pure scaffold: the shape, not the content.
- **Seed function lives in `qor/seed.py`.** A module, not a script under `qor/scripts/`, because it's callable from both the CLI and (via the resilience pattern) from skills that detect missing scaffold at runtime.
- **Skills declare an autonomy mode in frontmatter.** Two values: `autonomous` and `interactive` (default). The mode dictates the recovery pattern -- this is the hinge of the plan.
  - **Interactive skills** (qor-audit, qor-implement, qor-substantiate, qor-plan, qor-validate, etc.) get ONE inline recovery point per missing prerequisite: a Y/N prompt `"<path> not found. Should I correct it by running 'qorlogic seed' or pause? [Y/n]"`. On Y, run `qorlogic seed` and continue. On N, abort with a one-line error.
  - **Autonomous skills** (entire `qor-deep-audit*` family + any future unattended-run skill) get ZERO user-interaction points except for break-the-glass emergencies. On missing prerequisite: auto-heal silently by invoking `qor.seed.seed()` and continuing. On irrecoverable state (auto-heal failed, data corruption, ambiguous input the skill cannot mechanically resolve): emit a break-the-glass diagnostic prefixed `EMERGENCY:` with the exact path / error / recovery command; this is the ONLY reason an autonomous skill may surface to the user.
- **The doctrine is enforceable.** A new lint test greps `qor/skills/**/*.md`, reads each skill's frontmatter autonomy mode, and enforces the mode-specific rules: autonomous skills get ZERO banned pause phrases AND ZERO Y/N recovery prompts; interactive skills use the Y/N template for every missing-prereq path and justify any residual pause. Test fails CI on any violation and names offending file:line.
- **No backwards-compat for CLAUDE_PROJECT_DIR, `tomli_w`, etc.** Out of scope -- Phase 24 settled those.

## Autonomy classification (canonical)

Skills declare mode in SKILL.md frontmatter:

```yaml
autonomy: autonomous  # or: interactive
```

Missing or unset defaults to `interactive`. The classification is terminal -- no hybrid mode. A skill that needs occasional user input is `interactive` by definition.

**Autonomous skills (Phase 25 inventory)**:
- `qor-deep-audit` (the full deep audit orchestration)
- `qor-deep-audit-recon` (reconnaissance pass)
- `qor-deep-audit-remediate` (remediation pass)

All other `/qor-*` skills are `interactive`.

## Seed contents (canonical)

```
docs/META_LEDGER.md       # chain header + genesis entry
docs/SHADOW_GENOME.md     # header only (no entries)
docs/ARCHITECTURE_PLAN.md # TODO-tagged template
docs/CONCEPT.md           # TODO-tagged template
docs/SYSTEM_STATE.md      # initial snapshot template
.agent/staging/.gitkeep
.qor/gates/.gitkeep
.qor/session/.gitkeep
.gitignore                # append-only section marking .qor/session/ as runtime-only
```

## Resilience doctrine rule (enforced by lint)

**For all skills**: the following phrases are banned unless wrapped in an explicit override marker:

- "wait for user"
- "confirm before"
- "pause here"
- "Ready to proceed?"
- "Continue?"
- bare "Ask the user to proceed"

**Interactive skills** MAY contain exactly one Y/N recovery prompt per missing-prerequisite detection, using the canonical template documented in `doctrine-prompt-resilience.md` (marked `<!-- qor:recovery-prompt -->`).

**Autonomous skills** MUST NOT contain Y/N recovery prompts OR any of the banned phrases. Missing-prerequisite paths MUST use auto-heal (marked `<!-- qor:auto-heal -->`). Break-the-glass errors MUST be prefixed `EMERGENCY:` and MUST carry the marker `<!-- qor:break-the-glass reason="..." -->` explaining why mechanical recovery is impossible.

## Communication tier classification (canonical)

Three tiers:

- **technical** (default) -- full jargon, SG IDs, OWASP tags, `file:line`, hash values, doctrine citations. Audience: engineers, auditors.
- **standard** -- complete sentences, technical terms introduced inline, file paths kept, actionable commands preserved, SG IDs omitted unless load-bearing. Audience: mixed stakeholders.
- **plain** -- no jargon, no SG/OWASP tags, no hashes in body (footnoted if needed), short declarative sentences, explicit next-step commands. Audience: non-technical operators, executive summaries.

Selection mechanism:

- Slash command: `/qor-tone technical|standard|plain` sets the session tier (sticky until changed or session ends).
- Config persistence: `qorlogic init --tone <tier>` writes `tone` into `.qorlogic/config.json` as the workspace default.
- Runtime resolution order: session override (from `/qor-tone`) -> config file -> `technical` default.

**Scope exclusion**: tier selection does NOT apply to hash-chained or evidentiary artifacts (`docs/META_LEDGER.md` entries, `docs/SHADOW_GENOME.md` entries, any content written to `.qor/gates/<session>/*.json`, Merkle seal text). Those stay technical-only for integrity. Every tone-aware skill declares `tone_aware: true|false` in frontmatter; `false` is mandatory for skills that write evidentiary artifacts.

## CI validation

```
pytest -q
pytest -q -m integration   # if integration markers added
```

Plus the new lint test is part of the default `pytest -q` run.

---

## Phase 1: `qorlogic seed` subcommand + scaffold module

### Affected files

- `tests/test_seed_scaffold.py` (new) -- seed creates expected files + dirs; idempotent
- `tests/test_cli_seed.py` (new) -- `qorlogic seed` wires into main dispatch
- `qor/seed.py` (new) -- scaffold primitive, pure function with a fixed target list
- `qor/cli.py` -- register `seed` subcommand + dispatch
- `qor/templates/` (new dir) -- markdown template files read by `qor/seed.py`

### Unit Tests (write FIRST)

- `tests/test_seed_scaffold.py`
  - `seed(base=tmp_path)` creates every file in the canonical seed list
  - Every created markdown file parses as valid UTF-8 and is non-empty
  - Second call to `seed(base=tmp_path)` is a no-op: existing files unchanged (byte-equal), stdout reports "skipped: <path>" for each
  - User-edited `docs/META_LEDGER.md` is NOT overwritten by a second `seed` call (regression guard for idempotence)
  - `.agent/staging/.gitkeep` and `.qor/gates/.gitkeep` are created empty
  - `.gitignore` section for `.qor/session/` is appended once; a second call does not duplicate
  - Missing parent directories are created (`docs/`, `.agent/staging/`, `.qor/gates/`, `.qor/session/`)
- `tests/test_cli_seed.py`
  - `qorlogic seed` runs without args; exit 0
  - `qorlogic seed --target tmp_path` seeds into that path (for test isolation)
  - `qorlogic --help` lists `seed` in subcommands
  - Re-running `qorlogic seed` on already-seeded workspace reports skips, exits 0

### Changes

- `qor/seed.py`:
  - Module-level constant `SEED_TARGETS: tuple[SeedTarget, ...]` where `SeedTarget = namedtuple("SeedTarget", ["rel_path", "template_name", "mode"])` and `mode` is `"file"`, `"gitkeep"`, or `"gitignore_append"`.
  - Pure function `seed(base: Path, *, quiet: bool = False) -> SeedResult` where `SeedResult` is a namedtuple `(created: list[str], skipped: list[str])`.
  - `_write_if_missing(dst: Path, content: str) -> bool` helper returns True if it wrote.
  - `_append_gitignore_section(dst: Path, marker: str, content: str) -> bool` idempotent append bounded by a marker comment.
  - Templates read from `qor/templates/*.md` via `qor.resources`; bundled in package-data.
- `qor/templates/`:
  - `meta_ledger.md` -- header with empty chain + genesis entry formatted to match current ledger style
  - `shadow_genome.md` -- header only
  - `architecture_plan.md` -- minimal scaffold with `## TODO` sections
  - `concept.md` -- minimal scaffold with `## TODO` sections
  - `system_state.md` -- initial snapshot template
- `qor/cli.py`:
  - Register `seed` subcommand: `qorlogic seed [--target PATH]`.
  - Add to `_register_misc` helper (already exists from Phase 24).
  - Dispatch calls `qor.seed.seed(base=args.target or Path.cwd())`.
- `pyproject.toml` `[tool.setuptools.package-data]`:
  - Add `"templates/*.md"` to the `qor` package-data list.

---

## Phase 2: Prompt resilience doctrine + lint test

### Affected files

- `tests/test_prompt_resilience_lint.py` (new) -- grep-based lint enforcing the doctrine
- `tests/test_yaml_safe_load_discipline.py` (edit) -- widen walk to `tests/**/*.py`, excluding `tests/fixtures/`; prove the extended scope catches a planted unsafe call
- `tests/fixtures/` (new dir) -- fixture directory for deliberate unsafe content used in rejection tests; excluded from discipline walk
- `qor/references/doctrine-prompt-resilience.md` (new) -- the codified rule + canonical Y/N recovery template
- `qor/references/skill-recovery-pattern.md` (new) -- one-file reference for the canonical pattern skills embed

### Unit Tests (write FIRST)

- `tests/test_prompt_resilience_lint.py`
  - Walks `qor/skills/**/*.md` and `qor/skills/**/SKILL.md`.
  - **Parser policy**: frontmatter parsing uses `yaml.safe_load` only (`from yaml import safe_load`). `yaml.load`, `yaml.load_all`, `yaml.full_load`, `yaml.unsafe_load` are banned. Enforced codebase-wide by the widened `test_yaml_safe_load_discipline.py` (see below).
  - Parses each file's frontmatter via `safe_load`; extracts `autonomy` (default `interactive`).
  - Banned-phrase grep (all skills, both modes): `"wait for user"`, `"confirm before"`, `"pause here"`, `"Ready to proceed?"`, `"Continue?"`, `"Ask the user to proceed"`. Each hit allowed only with a preceding `<!-- qor:allow-pause reason="..." -->` marker.
  - For every `ABORT` or `INTERDICTION` hit:
    - **Interactive** skill: within 10 lines, either `<!-- qor:recovery-prompt -->` (normal case) or `<!-- qor:fail-fast-only reason="..." -->` (justified pure abort).
    - **Autonomous** skill: within 10 lines, either `<!-- qor:auto-heal -->` (normal case) or `<!-- qor:break-the-glass reason="..." -->` (emergency surfacing).
  - Autonomous-only assertions: no `qor:recovery-prompt` markers (they'd imply user interaction), and no banned phrases at all.
  - Test output names every offending file:line with the autonomy mode so authors can locate and fix.
  - Four positive-control fixtures cover the matrix: `tests/fixtures/skill_interactive_good.md`, `tests/fixtures/skill_interactive_bad.md`, `tests/fixtures/skill_autonomous_good.md`, `tests/fixtures/skill_autonomous_bad.md`. The test asserts the good ones pass and the bad ones fail.

- `tests/test_yaml_safe_load_discipline.py` (edit, not new)
  - Widen the `root` walk from `qor/` alone to ALSO scan `tests/**/*.py`.
  - Exclude `tests/fixtures/` from the walk (that directory deliberately houses unsafe content used in rejection tests, and may contain the banned regex as plain text rather than a call).
  - Add a new assertion: a throwaway Python file `tests/fixtures/bad_unsafe_call.py` containing a raw `yaml.load(...)` call is NOT scanned directly, but the test creates a `tmp_path / "planted_call.py"` with the offending source, copies it into a fresh tests-style walk rooted at `tmp_path`, and asserts the discipline routine flags it. This proves the widened walk catches new violations.
  - Parse `__file__` of the discipline test and assert the `root` walk list is exactly `[qor/, tests/]`, preventing accidental scope regression.

### Changes

- `qor/references/doctrine-prompt-resilience.md`:
  - State the rule: "Skills pause only at genuine decision points. A genuine decision point requires user input that changes the outcome -- not confirmation that the next mechanical step may occur."
  - Name the two failure modes: over-pausing and hidden-prerequisite assumptions.
  - Define the autonomy classification (autonomous vs interactive) and both recovery templates.
  - List banned phrases and all override-marker tokens.
- `qor/references/skill-recovery-pattern.md`:
  - Canonical templates that skills paste into their interdiction blocks: one for interactive (Y/N prompt), one for autonomous (auto-heal).
  - Single source of truth; the lint test reads this file and uses its body as the expected pattern signature.

### Canonical recovery templates

**Interactive skills** (default):

```markdown
<!-- qor:recovery-prompt -->
If `<artifact-path>` does not exist:

Ask the user: `<artifact-path> not found. Should I correct it by running "qorlogic seed" or pause? [Y/n]`

- On Y or empty: run `qorlogic seed` (idempotent), then continue the skill.
- On N: abort with "Run `qorlogic seed` to create the governance scaffold, then re-run this skill."
```

**Autonomous skills** (deep-audit family and unattended-run skills):

```markdown
<!-- qor:auto-heal -->
If `<artifact-path>` does not exist:

Run `qorlogic seed` automatically (idempotent). Do not prompt the user. Continue the skill.

If auto-heal itself fails or leaves the artifact malformed:

<!-- qor:break-the-glass reason="seed scaffold could not be created or is corrupt" -->
Emit: `EMERGENCY: <artifact-path> could not be auto-created. Manual intervention required. Check filesystem permissions and re-run "qorlogic seed".`
Abort.
```

---

## Phase 3: Apply recovery patterns to affected skills

### Affected files

- `tests/test_skill_prerequisite_coverage.py` (new) -- asserts every skill with ABORT has the correct recovery marker for its autonomy mode; asserts the banned-phrase list is clean across all skills
- `qor/skills/meta/qor-deep-audit/SKILL.md` -- add `autonomy: autonomous` frontmatter; convert ABORT to `qor:auto-heal` pattern
- `qor/skills/meta/qor-deep-audit-recon/SKILL.md` -- add `autonomy: autonomous`; apply auto-heal
- `qor/skills/meta/qor-deep-audit-remediate/SKILL.md` -- add `autonomy: autonomous`; apply auto-heal
- `qor/skills/governance/qor-audit/SKILL.md` -- add `autonomy: interactive`; apply Y/N recovery
- `qor/skills/governance/qor-validate/SKILL.md` -- add `autonomy: interactive`; apply Y/N recovery
- `qor/skills/governance/qor-substantiate/SKILL.md` -- add `autonomy: interactive`; apply Y/N recovery
- `qor/skills/sdlc/qor-implement/SKILL.md` -- add `autonomy: interactive`; apply Y/N recovery
- `qor/skills/memory/qor-document/SKILL.md` -- add `autonomy: interactive`; apply Y/N recovery
- `qor/skills/meta/qor-repo-release/SKILL.md` -- add `autonomy: interactive`; remove 2 over-pause phrases + apply Y/N to the ABORT
- `qor/skills/meta/qor-bootstrap/SKILL.md` -- add `autonomy: interactive`; remove 1 over-pause phrase (bootstrap is interactive by nature)
- `qor/skills/memory/qor-organize/SKILL.md` -- add `autonomy: interactive`; remove 1 over-pause phrase

### Unit Tests (write FIRST)

- `tests/test_skill_prerequisite_coverage.py`
  - **Parser policy**: frontmatter parsing uses `yaml.safe_load` only; `yaml.load` banned. Enforced by the widened discipline test.
  - For each skill enumerated above, parse frontmatter via `safe_load` and assert `autonomy` is set to the expected mode.
  - For each autonomous skill, assert the file contains at least one `<!-- qor:auto-heal -->` marker AND zero `<!-- qor:recovery-prompt -->` markers AND zero banned phrases (unmarked or marked).
  - For each interactive skill with ABORT, assert the file contains at least one `<!-- qor:recovery-prompt -->` marker (skills that justify bare ABORT need `<!-- qor:fail-fast-only reason="..." -->`).
  - For all skills in `qor/skills/`, assert the banned-phrase list has zero unmarked hits.
  - Assert `qor/references/skill-recovery-pattern.md` exists and contains both template tokens (`qor:recovery-prompt`, `qor:auto-heal`) AND the string `qorlogic seed`.
  - Assert `qor/references/doctrine-prompt-resilience.md` lists every banned phrase from `test_prompt_resilience_lint.py`'s regex source AND both autonomy modes (single source of truth cross-check).

### Changes

- Every affected skill gets a new frontmatter line: `autonomy: interactive` or `autonomy: autonomous` per the inventory above.
- **Interactive skills** -- each `INTERDICTION` block that currently reads:
  ```
  **INTERDICTION**: If `<path>` does not exist:
  ABORT
  Report: "..."
  ```
  becomes:
  ```
  **INTERDICTION**: If `<path>` does not exist:

  <!-- qor:recovery-prompt -->
  Ask the user: `<path> not found. Should I correct it by running "qorlogic seed" or pause? [Y/n]`
  - On Y or empty: run `qorlogic seed`, then continue.
  - On N: abort with the prior error text naming `<path>` and `qorlogic seed`.
  ```
- **Autonomous skills** (deep-audit family) -- same ABORT blocks become:
  ```
  **INTERDICTION**: If `<path>` does not exist:

  <!-- qor:auto-heal -->
  Run `qorlogic seed` automatically. Do not prompt.

  <!-- qor:break-the-glass reason="seed scaffold could not be created" -->
  If the seed itself fails: emit `EMERGENCY: ...` and abort. This is the only permitted user-facing surfacing in an autonomous skill.
  ```
- Over-pause phrases in the 4 flagged skills are either deleted (if not load-bearing) or wrapped with `<!-- qor:allow-pause reason="..." -->` if they mark genuine decision points (risky action, ambiguous input). Autonomous skills never qualify for `qor:allow-pause` -- any pause in an autonomous skill is a lint failure.
- No skill-behavior changes beyond prompt text + frontmatter -- this is doctrine application, not logic change.

---

## Phase 4: Communication tiers (`/qor-tone` + config + skill frontmatter)

### Affected files

- `tests/test_tone_resolution.py` (new) -- tier resolution order (session override > config > default); also cross-checks doctrine-communication-tiers.md has the canonical "How skills read the tone value" section
- `tests/test_tone_config_persistence.py` (new) -- `qorlogic init --tone <tier>` writes `tone` into config; invalid tier values rejected
- `tests/test_tone_evidentiary_exclusion.py` (new) -- tone-aware skills cannot be used to render evidentiary artifacts (ledger, shadow genome, gate JSON)
- `tests/test_tone_skill_frontmatter.py` (new) -- every `/qor-*` skill has `tone_aware: true|false` set; skills that write evidentiary artifacts have `tone_aware: false`; for `tone_aware: true` skills, asserts canonical `<!-- qor:tone-aware-section -->` markers are present AND contain all three tier names with non-empty instructions
- `tests/test_tone_rendering_example.py` (new) -- picks one canonical tone-aware skill as a fixture and asserts its tone-aware-section contains fragment text for all three tiers (closes the SG-Phase25-B ghost-feature gap)
- `qor/tone.py` (new) -- tier resolution primitive: pure function `resolve_tone(session_override: str | None, config_path: Path | None) -> str`; values validated against `("technical", "standard", "plain")`
- `qor/cli.py` -- add `--tone` to `init` (thread into config JSON)
- `qor/cli_policy.py` -- `do_init` writes `tone` field; defaults to `technical` if unset
- `qor/references/doctrine-communication-tiers.md` (new) -- tier definitions + selection semantics + evidentiary-artifact exclusion list + canonical "How skills read the tone value" section
- `qor/skills/*` -- every SKILL.md and loose skill file gains `tone_aware: true|false` frontmatter key; every `tone_aware: true` skill gains a `<!-- qor:tone-aware-section -->` delimited section with per-tier rendering instructions

### Unit Tests (write FIRST)

- `tests/test_tone_resolution.py`
  - **Parser policy**: any frontmatter parsing uses `yaml.safe_load` only (enforced by widened discipline test).
  - `resolve_tone(None, None)` -> `"technical"` (default)
  - `resolve_tone("plain", None)` -> `"plain"` (session override wins)
  - `resolve_tone(None, config_with_tone("standard"))` -> `"standard"` (config honored)
  - `resolve_tone("technical", config_with_tone("plain"))` -> `"technical"` (session beats config)
  - `resolve_tone("garbage", None)` -> raises `ValueError` naming the invalid tier
  - `resolve_tone(None, config_missing_tone)` -> `"technical"` (fallback)
  - `resolve_tone(None, config_path_nonexistent)` -> `"technical"` (graceful; no crash)
  - **Doctrine presence assertion**: `qor/references/doctrine-communication-tiers.md` exists AND contains the canonical header `## How skills read the tone value`. Fails with a clear message if the section is missing; prevents the doctrine from silently losing its skill-instruction surface.
- `tests/test_tone_config_persistence.py`
  - `qorlogic init --tone plain --target tmp_path` writes `tone == "plain"` into `tmp_path/.qorlogic/config.json`
  - `qorlogic init --tone invalid --target tmp_path` exits non-zero and does NOT create config
  - `qorlogic init --target tmp_path` (no --tone) writes `tone == "technical"` as default
  - Existing Phase 24 init fields (`host`, `scope`, `profile`, `governance_scope`) remain present and correct
- `tests/test_tone_evidentiary_exclusion.py`
  - Walks `qor/skills/**/SKILL.md`.
  - For every skill that mentions `META_LEDGER`, `SHADOW_GENOME`, `.qor/gates/`, or `Merkle` in its prose (heuristic: skill writes evidentiary artifacts), assert `tone_aware: false` in frontmatter.
  - Fixture `tests/fixtures/skill_tone_aware_evidentiary_bad.md` mentions `META_LEDGER` AND declares `tone_aware: true` -- test must flag it.
  - Fixture `tests/fixtures/skill_tone_aware_pure_good.md` mentions no evidentiary artifact AND declares `tone_aware: true` -- test must accept it.
- `tests/test_tone_skill_frontmatter.py`
  - **Parser policy**: frontmatter parsing uses `yaml.safe_load` only (enforced by widened discipline test).
  - Every file under `qor/skills/` that matches `SKILL.md` or `*.md` at the loose-skill level declares `tone_aware` in frontmatter. No skill may omit the key.
  - Cross-reference: the set of `tone_aware: false` skills must be a superset of the evidentiary-writer heuristic set (belt + suspenders).
  - **Ghost-feature closure** (SG-Phase25-B): for every `tone_aware: true` skill, the SKILL.md body MUST contain:
    - An opening marker `<!-- qor:tone-aware-section -->`.
    - A closing marker `<!-- /qor:tone-aware-section -->` somewhere after it.
    - Between the markers: all three tier names (`technical`, `standard`, `plain`) as sub-headers or inline labels.
    - Between the markers: at least one non-empty non-blank content line per tier (rendering instruction). A tier name followed immediately by another tier name or the closing marker fails -- this catches declaration-only sections.
  - Missing any of the above marks the skill as a ghost feature; test output names the skill file:line and the specific missing element.
- `tests/test_tone_rendering_example.py`
  - **Parser policy**: `yaml.safe_load` only.
  - Picks a canonical tone-aware skill (pin to `qor/skills/memory/qor-status/SKILL.md` as the reference example -- chosen because it's low-stakes, output-only).
  - Asserts its tone-aware-section contains fragment text for each of the three tiers. Specifically: within each tier's sub-section, require at least one token that signals the tier's register (e.g., technical tier has SG ID or OWASP tag; standard tier has a complete sentence with no SG ID; plain tier has no technical term AND no hash-looking string).
  - The fragment-matching uses loose regex (tier register heuristics), not exact prose -- authors retain editorial freedom while the shape is enforced.
  - If the canonical skill fails, the test fails loudly with the offending tier and expected register hints. This anchors the doctrine in at least one working example.

### Changes

- `qor/tone.py`:
  - Module-level constant `_VALID_TONES = ("technical", "standard", "plain")`.
  - Pure function `resolve_tone(session_override, config_path)`:
    - Validate `session_override` in `_VALID_TONES` if non-None (else `ValueError`).
    - If `session_override` set, return it.
    - If `config_path` exists, read JSON, return `data.get("tone", "technical")`. Read failures default to `"technical"` silently.
    - Else default to `"technical"`.
  - No side effects, no I/O beyond reading config.
- `qor/cli.py`:
  - `init` subparser gains `--tone` with `choices=_VALID_TONES`, default `None` (explicit `None` so `do_init` can distinguish unset vs default).
  - No other subcommand changes; `/qor-tone` slash command is handled purely by the skill runtime (markdown-level directive), not by the CLI.
- `qor/cli_policy.py`:
  - `do_init` reads `args.tone`, defaulting to `"technical"` if None, writes to config JSON alongside `host`/`scope`/`profile`.
- `qor/references/doctrine-communication-tiers.md`:
  - Tier definitions (canonical paragraph per tier with worked example showing the SAME content rendered at each tier).
  - Selection order (session -> config -> default).
  - Evidentiary-artifact exclusion list (ledger, shadow genome, `.qor/gates/*.json`, Merkle seals).
  - Reference to `caveman` inspiration and attribution (MIT-licensed).
  - **`## How skills read the tone value` section** (required; enforced by `test_tone_resolution.py`): explains the lookup order tone-aware skills use at runtime. Canonical text: session override from any `/qor-tone` directive in the current session window; else config value from `.qorlogic/config.json`; else `"technical"` default. Names the `qor.tone.resolve_tone` helper for Python callers and the markdown preamble pattern that tone-aware skills paste into their body so the agent performs the same lookup when rendering.
- `qor/skills/*` frontmatter edits (bulk):
  - Every SKILL.md and loose skill file gains one line: `tone_aware: true` OR `tone_aware: false`.
  - **Evidentiary skills** (must be `tone_aware: false`): `qor-substantiate`, `qor-audit`, `qor-validate`, `qor-plan`, `qor-implement`, `qor-research`, and any skill that writes to ledger / shadow genome / gate artifacts.
  - **Tone-aware skills** (may be `tone_aware: true`): `qor-status`, `qor-help`, `qor-deep-audit-recon` prose-summary paths, `qor-document`, `qor-organize`, `qor-debug` (debug narrative rendering). The list is declarative -- exact set frozen by `tests/test_tone_skill_frontmatter.py`.
  - **Body edits for every `tone_aware: true` skill** (enforces SG-Phase25-B countermeasure):
    - Insert a `## Output rendering by tone` section delimited by `<!-- qor:tone-aware-section -->` (open) and `<!-- /qor:tone-aware-section -->` (close).
    - Inside the section, three sub-sections (`### technical`, `### standard`, `### plain`), each with at least one non-empty content line giving concrete rendering instructions for this skill's output at that tier.
    - Each tone-aware skill's section opens with a shared preamble paragraph (pasted from `qor/references/doctrine-communication-tiers.md` "How skills read the tone value"): the agent resolves session override -> config -> default, then branches on the resolved value.
    - The three tiers must exemplify their register: technical tier mentions at least one SG ID or OWASP tag or similar; standard tier writes complete sentences but omits SG tags; plain tier uses no jargon and no hash-style tokens.

### Slash-command wiring note

`/qor-tone technical|standard|plain` is a markdown-level directive interpreted by the agent host (Claude Code / Codex / Gemini CLI). It is NOT implemented in the Python CLI. The slash command sets a session-level variable the agent uses when rendering skill output. The tone of that rendering is enforced by the skill prompts themselves, which branch on the current session tone value. The Python CLI's role is limited to: (a) `qorlogic init --tone` config persistence, (b) the `resolve_tone` helper for any Python caller that needs the effective tier. No session-state socket, no daemon.

---

## Delegation

- Plan complete -> `/qor-audit`.
- Phase 3 and Phase 4 are largely mechanical skill-text edits; if the audit flags a skill as semantically changed (not just doctrine-compliant rewording or frontmatter addition), escalate that specific skill to `/qor-refactor`. No module restructuring expected, so `/qor-organize` should not be needed.
