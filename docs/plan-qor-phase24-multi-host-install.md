# Plan: Phase 24 -- Multi-Host Install (Codex fix + Gemini CLI + repo/global scope)

**change_class**: feature

## Open Questions

- `$QORLOGIC_PROJECT_DIR` as a universal repo-root override: ship in this phase, or defer? Current assumption: Phase 1 honors it if set, else `Path.cwd()`. No per-host env vars introduced.
- Existing `CLAUDE_PROJECT_DIR` semantics: current code uses it as "install into this project's `.claude/`". After Phase 1, scope is explicit via `--scope`; `CLAUDE_PROJECT_DIR` is no longer consulted. This is a behavior change for claude users who relied on the env var. Per project doctrine, no backwards-compat shim.
- Kilo Code Gemini-like layout: should Kilo Code also move to a `commands/` model long-term, or keep `skills/+agents/`? Out of scope; this plan preserves current Kilo Code layout.

## Dependency declaration (new)

Phase 2 introduces YAML frontmatter parsing. Skill frontmatter uses folded block scalars (`description: >-`), nested mappings (`metadata:` with children), and multi-line continuations -- real YAML 1.x features, not a `key: value` subset. Writing a compliant parser vanilla is thousands of lines and is specifically the dependency-audit escape hatch ("<10 lines vanilla? NO").

**Declared addition** to `pyproject.toml` `[project]` `dependencies`:

```
dependencies = ["jsonschema>=4", "PyYAML>=6"]
```

Usage is constrained to `yaml.safe_load` (import `from yaml import safe_load`). `yaml.load` is banned at the codebase level; enforced by lint-style grep test (see Phase 2 Unit Tests).

## Goal

Make `qorlogic install` a uniform, explicit deployer across four hosts (claude, codex, kilo-code, gemini) with repo-default scope. Fix the existing source-variant bug so `--host codex` actually reads `variants/codex/`. Add Gemini CLI as a first-class host with TOML-command output.

## Design summary

- **Scope is explicit and uniform.** `--scope {repo,global}` on install/uninstall/list/init. Default `repo`. Repo = `$QORLOGIC_PROJECT_DIR or Path.cwd()` joined with `.<host>/`. Global = `~/.<host>/`.
- **Each host reads its own variant.** Install source root = `dist_root / "variants" / <host>`. Per-variant manifest at `variants/<host>/manifest.json`.
- **HostTarget exposes an install map**, not two fixed dirs. `install_map: dict[str, Path]` maps source-prefix -> target dir. Lets claude/codex/kilo-code use `{"skills/": ..., "agents/": ...}` while gemini uses `{"commands/": ...}` -- install logic stays identical across hosts.
- **Gemini variant emits TOML commands.** `dist_compile` writes skills -> `commands/<name>.toml`, agents -> `commands/agent-<name>.toml`, each with `description`, `prompt`, and preserved frontmatter (`trigger`, `phase`, `persona`) where present.

## CI validation

After each phase:

```
pytest -q
pytest -q -m integration    # if integration markers added
```

No new lint tooling introduced; existing `pyproject.toml` config governs.

---

## Phase 1: Uniform scope model + source-variant install fix

### Affected files

- `tests/test_hosts_scope.py` (new) -- resolve() repo/global semantics for all existing hosts
- `tests/test_cli_install_source.py` (new) -- `--host codex` installs files from `variants/codex/`, not `variants/claude/`
- `qor/hosts.py` -- add `scope` param to `resolve()`; factories return `(base, install_map)`; drop `CLAUDE_PROJECT_DIR` consultation
- `qor/cli.py` -- add `--scope` to install/uninstall/list/init (default `repo`); `_do_install` uses host-matching variant dir and per-variant manifest
- `qor/scripts/dist_compile.py` -- emit per-variant `manifest.json` at `variants/<host>/manifest.json`; keep top-level `dist/manifest.json` as an index for backwards lookup by `list --available`

### Unit Tests (write FIRST)

- `tests/test_hosts_scope.py`
  - `resolve("claude", scope="repo")` -> `HostTarget` with `base == Path.cwd() / ".claude"`
  - `resolve("claude", scope="global")` -> `base == Path.home() / ".claude"`
  - `resolve("codex", scope="repo")` -> `base == Path.cwd() / ".codex"`
  - `resolve("kilo-code", scope="repo")` -> `base == Path.cwd() / ".kilo-code"`
  - `resolve("claude", scope="repo", target_override=Path("/tmp/x"))` -> `base == Path("/tmp/x")`
  - `$QORLOGIC_PROJECT_DIR=/foo` + `scope="repo"` -> `base == Path("/foo") / ".claude"`
  - Unknown host -> `ValueError`
  - Invalid scope string -> `ValueError`
- `tests/test_cli_install_source.py`
  - Fixture: staged `variants/claude/skills/A/SKILL.md` + `variants/codex/skills/A/SKILL.md` with differing content + matching per-variant manifests
  - `_do_install("codex", ...)` copies the codex-flavored `SKILL.md`, not the claude one (assert file content bytes)
  - `_do_install` fails clean when the per-variant manifest is missing (error message names the host)
  - `--dry-run` prints source path under `variants/<host>/`, not `variants/claude/`

### Changes

- `HostTarget` dataclass: fields become `name: str`, `base: Path`, `install_map: dict[str, Path]`. Drop `skills_dir` and `agents_dir` (callers that need them read `install_map["skills/"]` / `install_map["agents/"]`).
- Factories `_claude_target(scope)`, `_codex_target(scope)`, `_kilo_target(scope)` compute `base` from `scope` and `$QORLOGIC_PROJECT_DIR`, return `install_map = {"skills/": base/"skills", "agents/": base/"agents"}`.
- `resolve(host_name, scope="repo", target_override=None)`:
  - validates scope in `{"repo","global"}` (ValueError otherwise)
  - if `target_override`: `base = target_override`, install_map rebuilt on it
  - else delegates to factory with scope
- `_do_install(host, scope, target_override, dist_root, dry_run)`:
  - `source_root = dist_root / "variants" / host`
  - reads `source_root / "manifest.json"` (per-variant)
  - for each manifest entry, finds the matching `install_map` prefix and copies to `install_map[prefix] / rel[len(prefix):]`
  - record file path is `base / ".qorlogic-installed.json"`
- `_do_uninstall`, `_do_list` updated to take `scope`.
- `dist_compile`: after compiling a variant directory, writes `variants/<host>/manifest.json`. Top-level `dist/manifest.json` continues to exist as the cross-variant index used by `list --available` (union of ids).

---

## Phase 2: Gemini CLI host (variant + install dispatch)

### Affected files

- `tests/test_hosts_gemini.py` (new) -- gemini host registration + scope resolution + install_map
- `tests/test_dist_compile_gemini.py` (new) -- compile emits `variants/gemini/commands/*.toml` with required fields
- `tests/test_cli_install_gemini.py` (new) -- end-to-end install of gemini variant with scope flag
- `qor/hosts.py` -- add `_gemini_target(scope)` with `install_map = {"commands/": base/"commands"}`; register under `"gemini"`
- `qor/scripts/dist_compile.py` -- add gemini-variant writer: parse skill/agent frontmatter via `yaml.safe_load` (banning `yaml.load`), render TOML files under `variants/gemini/commands/` via a vanilla renderer (no new deps), emit per-variant manifest
- `qor/cli.py` -- add `"gemini"` to `_hosts` choices; no other code change needed (dispatch already generic after Phase 1)

### Unit Tests (write FIRST)

- `tests/test_hosts_gemini.py`
  - `resolve("gemini", scope="repo")` -> `base == Path.cwd() / ".gemini"`, `install_map == {"commands/": base/"commands"}`
  - `resolve("gemini", scope="global")` -> `base == Path.home() / ".gemini"`
  - Gemini has NO `skills/` or `agents/` prefix in install_map (asserts absence)
- `tests/test_dist_compile_gemini.py`
  - Given source skill `qor/skills/sdlc/qor-plan/SKILL.md` with frontmatter `trigger: /qor-plan`, `phase: PLAN`, `persona: Governor`, compile produces `variants/gemini/commands/qor-plan.toml`
  - Parsed TOML contains `description` (non-empty str), `prompt` (non-empty str containing the SKILL.md body), `trigger == "/qor-plan"`, `phase == "PLAN"`, `persona == "Governor"`
  - Loose skill `log-decision.md` produces `commands/log-decision.toml`
  - Agent `agent-architect.md` produces `commands/agent-agent-architect.toml` (agent- prefix) and sets `description` from first non-heading line
  - Skills missing optional frontmatter keys produce TOML without those keys (not empty strings)
  - `variants/gemini/manifest.json` lists every emitted TOML with correct `install_rel_path` starting with `commands/` and correct `sha256`
  - TOML passes `tomllib.loads` without error for every emitted file
  - **Safe-loader rejection test**: frontmatter containing `!!python/object/apply:os.system` fails compilation with a clear error (proves `yaml.safe_load`, not `yaml.load`, is wired). A second fixture with `!!python/name:builtins.print` also fails.
  - **TOML round-trip test**: a skill body containing `"""`, backslashes, and literal `\n` characters is rendered by `render_gemini_command` and re-parsed via `tomllib.loads`; the recovered `prompt` equals the original byte-for-byte.
  - **Dependency shape test**: `pyproject.toml` runtime `dependencies` list equals exactly `["jsonschema>=4", "PyYAML>=6"]` after Phase 2 -- asserts no stray deps (`tomli_w`, `python-frontmatter`, etc.) sneak in.
  - **Unsafe YAML API ban test**: grep across `qor/` (excluding `qor/vendor/`) for the regex `yaml\.(load|load_all|full_load|unsafe_load)\s*\(` returns zero matches. Test lives at `tests/test_yaml_safe_load_discipline.py` and fails with a message that names every banned call site.
- `tests/test_cli_install_gemini.py`
  - Staged gemini variant with two commands + manifest
  - `_do_install("gemini", scope="repo", target_override=tmp_path)` lands files at `tmp_path / "commands" / "<name>.toml"`
  - `_do_install("gemini", scope="global")` (mocked home) lands files at `~/.gemini/commands/`
  - `.qorlogic-installed.json` record written at `base` and covers all copied paths
  - Uninstall removes every file, then the empty `commands/` dir, then the record

### Changes

- `qor/hosts.py`:
  - Add `_gemini_target(scope)` producing `HostTarget(name="gemini", base=..., install_map={"commands/": base/"commands"})`.
  - Register under key `"gemini"` in `_HOSTS`.
- `qor/scripts/dist_compile.py`:
  - New function `_emit_gemini_variant(source_root, out_root)` that iterates compiled skills/agents, parses YAML frontmatter via `yaml.safe_load` (import path: `from yaml import safe_load`), renders TOML via a pure function `render_gemini_command(name, description, prompt_body, extras: dict) -> str`.
  - **Parser policy**: `yaml.load` is banned. `yaml.safe_load` only. The module adds no other YAML entry points. Rejection of `!!python/*` tags is covered by a unit test (see Unit Tests).
  - Extras allowed: `trigger`, `phase`, `persona`. Unknown frontmatter keys are NOT forwarded (explicit allow-list; prevents schema drift).
  - `description` derivation: prefer frontmatter `description`; else first non-empty line of body after the H1; truncated to 200 chars.
  - **TOML renderer (vanilla, no new deps)**: `render_gemini_command` is a pure function that emits the canonical schema below using f-string templating. Scalars (`description`, `trigger`, `phase`, `persona`) are written as TOML basic strings -- a helper `_toml_basic(value: str) -> str` quotes with `"..."` and escapes `\\` -> `\\\\`, `"` -> `\\"`, `\n` -> `\\n`, `\r` -> `\\r`, `\t` -> `\\t`, and control chars via `\\uXXXX`. The `prompt` field is written as a TOML multi-line basic string delimited by `"""`; if the body contains the literal sequence `"""`, it is escaped to `\\"\\"\\"`; trailing backslashes in the body are escaped to `\\\\`. Output is validated by the round-trip test (see Unit Tests).
  - After emitting files, writes `variants/gemini/manifest.json` with `install_rel_path` values starting with `commands/`.
- `qor/cli.py`:
  - `_hosts` list becomes `["claude", "kilo-code", "codex", "gemini"]`.
  - No changes to `_do_install` or install map routing -- Phase 1 made it host-agnostic.

### TOML schema (canonical)

```toml
description = "Create implementation plans following Simple Made Easy principles."
trigger = "/qor-plan"
phase = "PLAN"
persona = "Governor"
prompt = """
# /qor-plan - Simple Made Easy Planning
...
"""
```

Fields: `description` (required), `prompt` (required), `trigger` `phase` `persona` (optional, forwarded only when present in source frontmatter).

---

## Phase 3: `init` and documentation alignment

### Affected files

- `tests/test_cli_init_scope.py` (new) -- `init` writes `.qorlogic/config.json` respecting scope
- `qor/cli.py` -- thread `--scope` through `init` handler
- `qor/cli_policy.py` -- `do_init` accepts and uses `scope`
- `README.md` -- replace install examples to show `--scope` flag; add Gemini to supported hosts table

### Unit Tests (write FIRST)

- `tests/test_cli_init_scope.py`
  - `init --host gemini --scope repo --target tmp` writes `tmp/.qorlogic/config.json` (or wherever config belongs per existing shape)
  - `init --host codex --scope global` writes to the global base returned by `resolve("codex", scope="global")`
  - Config JSON records `host` and `scope` for later commands to read

### Changes

- `do_init(args)` reads `args.scope` (default `"repo"`), resolves host target, writes config. No new config fields beyond `host` and `scope`.
- README updates are mechanical: add gemini row, show `--scope repo` (default) and `--scope global` forms.

---

## Delegation

- After this plan lands and passes dialogue review, run `/qor-audit` (L1 risk: new feature, no security surface beyond filesystem writes to predictable user-scoped paths).
- No restructuring of project topology required (no `/qor-organize` handoff).
- No new research required (`/qor-research` not needed).
