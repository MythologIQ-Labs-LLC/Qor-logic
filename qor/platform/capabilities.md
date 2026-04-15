# Qor Platform Capabilities Catalog

**Version**: 1

Catalog of named capabilities that Qor skills can optionally leverage. Populated via a mix of auto-detection and user declaration, stored in `.qor/platform.json`.

## Capabilities

### `host` (auto-detected)

The runtime harness. One of:

- `claude-code` — detected when `CLAUDE_PROJECT_DIR` env var is set
- `kilo-code` — (reserved; currently not auto-detected, fallback `unknown`)
- `codex-standalone` — (reserved; user-declared via profile)
- `unknown` — no recognized host signal

Used by: platform-dependent guidance, debug messaging, profile suggestion.

### `gh-cli` (auto-detected)

Boolean. True only when:

1. `gh` executable exists on PATH (`gh --version` exits 0), AND
2. `gh auth status` exits 0 (user is authenticated)

Consumed by: `qor/scripts/create_shadow_issue.py` (required for issue creation), `qor/skills/meta/qor-repo-release/` (future).

### `codex-plugin` (user-declared)

Boolean. Whether the Codex plugin is installed and available as a sub-agent invocation inside the current session.

No reliable programmatic probe exists from a child Python process, so this is user-declared via `qor_platform.py apply <profile>` or `qor_platform.py set codex-plugin true`.

Consumed by: `qor/skills/governance/qor-audit/` (switches to adversarial mode when available; logs `capability_shortfall` when absent) — wiring is a future task.

### `agent-teams` (user-declared)

Boolean. Whether Claude Code Agent Teams (`TeamCreate` tool) is available in the current session.

Consumed by: `qor/skills/sdlc/qor-plan/` and `qor/skills/sdlc/qor-implement/` (parallel-specialist mode when available) — wiring is a future task.

### `mcp-servers` (user-declared)

List of strings. Names/slugs of connected MCP servers. Free-form; no enum constraint.

Consumed by: future skill-specific capability checks (e.g., "is Linear MCP connected for ticket lookup?").

## Consumption pattern

```python
import sys; sys.path.insert(0, 'qor/scripts')
import qor_platform as qplat

if qplat.is_available("codex-plugin"):
    # run adversarial audit mode
    ...
else:
    # solo mode; log capability_shortfall
    ...
```

## Declaration pattern

```bash
# Apply a named profile (recommended)
python qor/scripts/qor_platform.py apply claude-code-with-codex

# Or toggle individual capabilities
python qor/scripts/qor_platform.py set codex-plugin true
python qor/scripts/qor_platform.py set agent-teams false

# Inspect
python qor/scripts/qor_platform.py get
```

## Re-detection triggers

The platform module re-runs auto-detect (host, gh-cli) when:

- `.qor/platform.json` is absent
- Host env changed since last detection
- Explicit `python qor/scripts/qor_platform.py detect` invocation

User-declared fields (`codex-plugin`, `agent-teams`, `mcp-servers`) are **never** overwritten by auto-detect; they persist until explicitly changed.
