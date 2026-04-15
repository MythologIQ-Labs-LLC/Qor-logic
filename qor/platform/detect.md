# Platform Detection

## Purpose

Qor skills optionally leverage platform capabilities (Codex plugin, Agent Teams, connected MCP servers). Capabilities that cannot be reliably probed from a child Python process are user-declared; the rest (host, `gh` CLI) are auto-detected. State persists in `.qor/platform.json`.

## Detection flow

### Auto-detected (cheap, re-run on demand)

- **Host**: `detect_host()` reads `CLAUDE_PROJECT_DIR` env var. Present → `claude-code`. Absent → `unknown`. Kilocode and Codex-standalone are reserved values; users declare those via `apply <profile>` because no standard env signal exists yet.
- **gh CLI**: `detect_gh_cli()` runs `gh --version` then `gh auth status` via `subprocess`. Returns True only if both succeed.

### User-declared (sticky, persists across detect runs)

- `codex-plugin` — Codex plugin installed and invokable
- `agent-teams` — `TeamCreate` tool available
- `mcp-servers` — list of connected MCP server slugs

Declare via:

```bash
# Apply a named profile (preferred)
python qor/scripts/qor_platform.py apply claude-code-with-codex

# Or toggle a single capability
python qor/scripts/qor_platform.py set codex-plugin true
```

User declarations are **never overwritten** by auto-detect; the detected + declared fields are stored side-by-side.

## Re-detection triggers

Auto-detect re-runs when:

- `.qor/platform.json` is absent (first-run initialization)
- User invokes `python qor/scripts/qor_platform.py detect` explicitly
- User invokes `python qor/scripts/qor_platform.py apply <profile>` (re-detects at apply time so detected fields stay current)

**User-declared fields are not re-evaluated** on re-detection. To reset them, apply a profile or `clear`:

```bash
python qor/scripts/qor_platform.py clear
```

## Consumption

Skills (and other Qor scripts) query the state via the library interface:

```python
import sys
sys.path.insert(0, 'qor/scripts')
import qor_platform as qplat

if qplat.is_available("codex-plugin"):
    # Adversarial audit path
    ...
else:
    # Solo audit; optionally log capability_shortfall shadow event
    ...
```

`is_available(capability)` returns:

- `True` if the capability is in `detected` and truthy
- `True` if the capability is in `declared` and truthy (non-empty list counts as truthy)
- `False` if the capability is not present in either, or if `.qor/platform.json` is absent

## Profiles

5 canonical profiles ship in `qor/platform/profiles/`:

| Profile | host | codex-plugin | agent-teams |
|---|---|---|---|
| `claude-code-solo` | claude-code | false | false |
| `claude-code-with-codex` | claude-code | true | false |
| `claude-code-teams` | claude-code | false | true |
| `kilo-code` | kilo-code | false | false |
| `codex-standalone` | codex-standalone | true | false |

Each profile is a markdown doc with YAML front matter; `apply_profile(name)` parses the front matter (no YAML dep — a small hand-rolled parser handles the fixed shape).

## Current phase scope

This phase ships infrastructure only:

- `qor/scripts/qor_platform.py`
- `qor/platform/capabilities.md`
- `qor/platform/detect.md` (this file)
- `qor/platform/profiles/*.md` × 5

**Skills are not modified this phase.** Wiring `qor-audit` to switch modes based on `is_available("codex-plugin")`, or `qor-plan` to fan out via `agent-teams`, is deliberately deferred — the lesson from the earlier audit loop is that per-skill wiring is a cross-cutting change best handled in a dedicated small-scope plan, not bundled into infra.
