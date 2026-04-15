# Plan: Phase 6 — Platform Detection & Capability Catalog

**Status**: Active (scope-limited, infra-only)
**Author**: QorLogic Governor
**Date**: 2026-04-15
**Scope**: Ship the platform module + capability catalog + 5 profile docs. Skills unchanged (wiring is future work).
**Base spec**: `docs/plan-qor-migration-final.md` §Phase 6

## Open Questions

None. Decisions settled pre-draft:
- Host: auto-detect via env vars (`CLAUDE_PROJECT_DIR`). `gh` CLI: auto-detect via subprocess.
- Codex plugin, Agent Teams, MCP servers: user-declared (no reliable programmatic probe from a child Python process).
- Carrier: file marker `.qor/platform.json`.
- Tolerance rule: re-detect if marker missing OR host env changed OR declared profile name absent from `qor/platform/profiles/`.
- Scope: infrastructure only; skills are not modified this phase.

## Capability catalog (v1)

- `host`: `claude-code` | `kilo-code` | `codex-standalone` | `unknown` (auto-detected)
- `gh-cli`: bool, auto-detected via `gh --version` + `gh auth status`
- `codex-plugin`: bool, user-declared
- `agent-teams`: bool, user-declared
- `mcp-servers`: list of strings, user-declared (free-form)

## Profiles (v1)

Stored under `qor/platform/profiles/`. Each file is a markdown doc with a declarative YAML front matter that `qor_platform.py apply` reads.

| Profile | host | codex-plugin | agent-teams |
|---|---|---|---|
| `claude-code-solo` | claude-code | false | false |
| `claude-code-with-codex` | claude-code | true | false |
| `claude-code-teams` | claude-code | false | true |
| `kilo-code` | kilo-code | false | false |
| `codex-standalone` | codex-standalone | true | false |

## Deliverables

### 1. `qor/platform/capabilities.md`

Declarative catalog:
- Each capability name
- Auto-detect OR user-declare
- Meaning in-context (what enables it)
- How skills consume (`is_available("codex-plugin")`)

### 2. `qor/platform/profiles/*.md` (5 files)

Each has YAML front matter + descriptive body:

```yaml
---
profile: claude-code-with-codex
host: claude-code
capabilities:
  codex-plugin: true
  agent-teams: false
  mcp-servers: []
---
```

### 3. `qor/platform/detect.md`

Skill spec (markdown, no YAML frontmatter changes to existing skills this phase):
- When detection fires (session start, explicit command)
- Auto-detected fields vs user-declared
- How to apply a profile: `python qor/scripts/qor_platform.py apply claude-code-solo`
- How skills query: `import qor_platform as qplat; qplat.is_available("codex-plugin")`

### 4. `qor/scripts/qor_platform.py`

Python 3.11 stdlib + jsonschema (already runtime).

Library:
- `detect_host() -> str` — reads env, returns `claude-code` / `kilo-code` / `codex-standalone` / `unknown`
- `detect_gh_cli() -> bool` — subprocess `gh --version`, then `gh auth status`; True only if authenticated
- `apply_profile(name: str) -> dict` — reads `qor/platform/profiles/<name>.md` YAML front matter, writes merged state to `.qor/platform.json`
- `current() -> dict | None` — reads `.qor/platform.json`
- `is_available(capability: str) -> bool` — looks up capability in current state
- `set_capability(name: str, value) -> dict` — merges into current state

CLI:
- `detect` — run auto-detect, print JSON summary
- `get` — print `.qor/platform.json`
- `apply <profile>` — load + save profile
- `set <cap> <value>` — single-capability override
- `check <cap>` — exit 0 if truthy, non-zero otherwise
- `clear` — remove marker

File marker `.qor/platform.json` shape:
```json
{
  "version": "1",
  "detected": {"host": "claude-code", "gh_cli": true},
  "declared": {"codex-plugin": false, "agent-teams": false, "mcp-servers": []},
  "profile_applied": "claude-code-solo",
  "ts": "ISO-8601"
}
```

Atomic writes via `os.replace()`.

### 5. `tests/test_platform.py`

- `test_detect_host_claude_code_env` — `CLAUDE_PROJECT_DIR` set → `claude-code`
- `test_detect_host_unknown_absent_env` — no recognized env → `unknown`
- `test_detect_gh_cli_true_when_auth_ok` — mocked subprocess returns 0 → True
- `test_detect_gh_cli_false_when_not_installed` — `FileNotFoundError` → False
- `test_detect_gh_cli_false_when_unauthenticated` — `gh auth status` returns non-zero → False
- `test_apply_profile_claude_code_solo` — file written; contents match catalog
- `test_apply_profile_unknown_raises` — invalid profile name raises
- `test_is_available_true_after_profile` — apply profile → `is_available("codex-plugin")` reflects declared
- `test_is_available_false_when_no_marker` — no file → False
- `test_set_capability_merges` — set overrides profile default
- `test_current_roundtrip` — apply, current() returns same data
- `test_clear_removes_marker`

## Constraints

- **Python 3.11+ stdlib** + optional `jsonschema` (already runtime dep).
- **No YAML parser dep** — front matter is a small fixed shape; hand-parse the `---`-delimited block.
- **Atomic writes** via `os.replace()`.
- **Skills unchanged** this phase — no edits to any `qor/skills/*/SKILL.md`.

## Success Criteria

- [ ] `python qor/scripts/qor_platform.py detect` runs without error, emits JSON
- [ ] `python qor/scripts/qor_platform.py apply claude-code-solo` writes `.qor/platform.json`
- [ ] `python qor/scripts/qor_platform.py check codex-plugin` exit non-zero after `claude-code-solo`; exit 0 after `claude-code-with-codex`
- [ ] All 12 platform tests pass
- [ ] Full suite 66/66 (11 compile + 18 shadow + 25 gates + 12 platform) all pass
- [ ] Drift clean; ledger chain intact
- [ ] Committed + pushed

## CI Commands

```bash
python -m pytest tests/test_platform.py -v
python qor/scripts/qor_platform.py detect
```
