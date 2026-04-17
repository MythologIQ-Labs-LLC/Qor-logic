---
name: example-autonomous-good
description: Canonical good autonomous skill
autonomy: autonomous
---

# /example-autonomous-good

## Step 1: State check

Read `docs/META_LEDGER.md`.

**INTERDICTION**: If `docs/META_LEDGER.md` does not exist:

<!-- qor:auto-heal -->
Run `qorlogic seed` automatically. Do not prompt.

<!-- qor:break-the-glass reason="seed scaffold could not be created or is corrupt" -->
If the seed itself fails: emit `EMERGENCY: docs/META_LEDGER.md could not be auto-created. Manual intervention required.` and abort.
