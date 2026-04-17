---
name: example-autonomous-bad
description: Bad autonomous skill (has Y/N prompt which autonomous skills must not carry)
autonomy: autonomous
---

# /example-autonomous-bad

## Step 1: State check

**INTERDICTION**: If `docs/META_LEDGER.md` does not exist:

<!-- qor:recovery-prompt -->
Ask the user: "Missing ledger. Should I correct it or pause? [Y/n]"

Continue?
