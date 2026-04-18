# Contributing to Qor-logic

Qor-logic is a prompt system. Contributions are proposed, audited, implemented, and sealed through the `/qor-*` skill chain. This document points to the authorities; read them in order.

## Reading order

Read these documents before proposing a change:

1. [`CLAUDE.md`](CLAUDE.md) - token-efficiency defaults, test discipline, governance flow.
2. [`qor/gates/chain.md`](qor/gates/chain.md) - the canonical phase sequence (research -> plan -> audit -> implement -> substantiate -> validate -> remediate).
3. [`qor/gates/delegation-table.md`](qor/gates/delegation-table.md) - cross-skill handoff matrix; single source of truth for which skill takes over when.
4. [`qor/gates/workflow-bundles.md`](qor/gates/workflow-bundles.md) - bundle protocol for multi-phase workflows.
5. [`qor/references/`](qor/references/) - deep-dive doctrines (test discipline, documentation integrity, audit-report language, shadow-genome countermeasures, etc.).
6. [`qor/references/glossary.md`](qor/references/glossary.md) - canonical terminology; every term Qor-logic uses has exactly one home here.

## Quickstart: first contribution

```
/qor-research   -> gather context; write a brief if the scope warrants.
/qor-plan       -> collaborative dialogue, then a plan file with doc_tier + terms + boundaries.
/qor-audit      -> adversarial review (Judge persona); binary PASS or VETO.
/qor-implement  -> tests first; then code; then run the suite twice.
/qor-substantiate -> Reality = Promise check; Merkle seal; version bump; CHANGELOG stamp.
```

At substantiation's Step 9.6 you choose one of four push/merge options. PR descriptions MUST cite the plan file path, the Meta Ledger entry number, and the Merkle seal hash, per [`qor/references/doctrine-governance-enforcement.md`](qor/references/doctrine-governance-enforcement.md) Section 6. Do not duplicate that contract here; if the doctrine changes, this document inherits automatically.

## What not to do

- No direct-to-main pushes. Every change goes through `/qor-plan` -> audit -> implement -> substantiate on its own `phase/<NN>-<slug>` branch.
- No governance-artifact edits outside the flow. `docs/META_LEDGER.md`, `docs/SHADOW_GENOME.md`, `.qor/gates/`, `CHANGELOG.md`, and version tags are produced mechanically by the skills. Hand-editing them breaks chain integrity.
- No skipping `/qor-audit`. Implementation requires a PASS verdict recorded in `audit.json`.
- No silent gate overrides. Overrides are permitted (advisory gates) but are logged as severity-1 shadow events for later review.
- No inventing new terminology without a glossary entry. If your change introduces a new domain concept, declare it in the plan's `terms_introduced:` block and add the entry to `qor/references/glossary.md` in the same phase. The substantiate-time orphan check will flag additions that never get adopted by a consumer.

## Asking questions

- Scope, prioritization, and blockers live in [`docs/BACKLOG.md`](docs/BACKLOG.md).
- Existing patterns and prior decisions are searchable via `docs/META_LEDGER.md` (sealed phases) and `docs/SHADOW_GENOME.md` (failure patterns + countermeasures).
- If a proposed change doesn't fit cleanly into the flow, open an issue before starting -- the earliest audit happens in `/qor-plan` dialogue, and unresolved design questions are cheaper there than at VETO time.
