---
name: example-interactive-good
description: Canonical good interactive skill
autonomy: interactive
---

# /example-interactive-good

## Step 1: State check

Read `docs/META_LEDGER.md`.

**INTERDICTION**: If `docs/META_LEDGER.md` does not exist:

<!-- qor:recovery-prompt -->
Ask the user: "docs/META_LEDGER.md not found. Should I correct it by running 'qorlogic seed' or pause? [Y/n]"

- On Y or empty: run `qorlogic seed`, then continue.
- On N: abort with "Run `qorlogic seed` to create the governance scaffold, then re-run this skill."
