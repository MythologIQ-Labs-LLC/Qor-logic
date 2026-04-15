---
profile: kilo-code
host: kilo-code
capabilities:
  codex-plugin: false
  agent-teams: false
  mcp-servers: []
---

# Profile: kilo-code

Kilocode host. No Codex plugin, no Agent Teams. Skill execution is solo; `qor-audit` runs in single-model mode; `qor-plan`/`qor-implement` execute sequentially.

## When to use

- Kilocode is the active IDE/harness
- Skills consumed from `qor/dist/variants/kilo-code/`

## Host auto-detection

Kilocode does not currently export a standardized env var that Qor's `qor_platform.py detect_host()` recognizes. Users on Kilocode should explicitly apply this profile after install:

```bash
python qor/scripts/qor_platform.py apply kilo-code
```

This sets `host: kilo-code` in `.qor/platform.json` and is never overwritten by auto-detect (declared fields are sticky).
