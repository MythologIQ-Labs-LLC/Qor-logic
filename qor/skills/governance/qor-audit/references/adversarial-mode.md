# qor-audit — Adversarial Mode (Codex Plugin)

**Status**: Subprocess bridge implemented (Phase 123; GH #160). `qor.scripts.external_reviewer` dispatches this input/output contract to an operator-configured external reviewer. The command is resolved from `.qorlogic/config.json` -> `external_reviewer.command` (an argv list, **operator-trusted**); it is executed list-form (no shell), the reviewer-input JSON is passed on stdin, and the returned JSON is contract-validated before use. Any failure (no command configured, nonzero exit, timeout, invalid output) degrades to a graceful `fallback` outcome and the audit proceeds in-harness (solo) with a logged `capability_shortfall`. The Codex-plugin path (`should_run_adversarial_mode`) remains the harness-native trigger; the bridge is the general external-process mechanism.

## Trigger

`qor_audit_runtime.should_run_adversarial_mode()` returns `True` only when:
1. `qor_platform.current()["detected"]["host"] == "claude-code"`, AND
2. `qor_platform.is_available("codex-plugin")` returns `True`.

When False on a `claude-code` host, audit logs a `capability_shortfall` shadow event (severity 2) and falls back to solo mode.

## Input contract (audit → Codex)

The Judge passes the audit subject + verified context to Codex:

```json
{
  "plan_path": "docs/plan-<feature>.md",
  "plan_content_hash": "<sha256>",
  "codebase_snapshot_refs": [
    {"path": "src/<file>", "lines": "1-200"},
    ...
  ],
  "session_id": "<UTC-ISO-MIN>-<6hex>",
  "audit_passes_completed": ["security", "razor", "macro", "orphan", "dependency"],
  "judge_findings_so_far": [
    {"id": "V-1", "category": "razor", "severity": "L2", "claim": "..."},
    ...
  ]
}
```

The plan's content hash must be computed via `qor/scripts/ledger_hash.py hash <plan_path>` so Codex can verify it matches the on-disk plan.

## Output contract (Codex → audit)

Codex returns a structured critique:

```json
{
  "critiques": [
    {
      "severity": "L1|L2|L3",
      "claim_challenged": "Razor estimate undercounts function lines",
      "counter_evidence": "src/foo.ts:45 — function spans 67 lines, exceeds 40 limit",
      "recommended_gap": "V-NEW: file-level Razor breach, mandate /qor-refactor"
    },
    ...
  ],
  "confidence": 0.0,
  "model": "<codex-model-id>",
  "ts": "<ISO-8601>"
}
```

## Synthesis (Judge integrates Codex critique)

After Codex returns:

1. Each critique with `severity >= L2` becomes a new `V-<n>` row in the audit report
2. Critiques that contradict the Judge's existing findings are merged: the Judge re-examines and either accepts (re-classifies severity) or refutes (cites why)
3. The synthesized audit verdict is recorded with mode marker: `**Mode**: adversarial (Codex critique synthesized)` in the report frontmatter
4. The Codex critique payload is preserved at `.qor/gates/<session_id>/audit-codex-critique.json` for traceability (not committed; runtime-only)

## Failure modes

| Mode | Behavior |
|---|---|
| Codex unavailable mid-call | Emit `capability_shortfall` (sev 2); continue solo; flag in verdict that adversarial was attempted-but-aborted |
| Codex returns malformed JSON | Treat as unavailable; emit shortfall; continue solo |
| Codex critique contradicts Judge with no evidence | Judge dismisses critique; logs reason in verdict |
| Codex critique severity > Judge's | Adopt the higher severity; re-classify findings accordingly |

## Wiring

The actual `subprocess` / tool-call invocation that delivers the input contract to Codex and parses the output contract is **not implemented in this repository**. It is documented as a profile binding in `qor/platform/profiles/claude-code-with-codex.md`. When the Codex-plugin invocation surface is finalized in Claude Code, that profile gains a one-line bridge to call this contract.

Until then, `should_run_adversarial_mode()` returns `False` in all observable test environments, and audit runs in solo mode with the shortfall logged.

## External-reviewer subprocess bridge (Phase 123 wiring; GH #160)

When an external reviewer is configured (`.qorlogic/config.json` ->
`external_reviewer.command`), `/qor-audit` Step 1 dispatches the reviewer-input
contract to it via `external_reviewer.run_external_review` and ingests its
verdict. The bridge runs the operator-configured command list-form (no shell),
passes the reviewer-input JSON on stdin, validates the returned JSON against the
output contract, and degrades to a `fallback` outcome on any failure — so a
missing/broken reviewer never blocks the audit; it proceeds solo with the logged
capability shortfall. The Phase 87 author-momentum auto-dispatch mandate is
unchanged.

## Option B — independent reviewer codification (Phase 68 wiring; GH #50)

The SKILL.md code block runs Option A: Codex-plugin-driven Claude+Codex
adversarial pairing when the harness exposes it. **Option B** is the fallback
(and explicit choice) when Option A is unavailable OR when the auditor was also
the plan's author. Per SG-007 (self-audit verification scope bias) and the
recurring "author-audit momentum" pattern: when the same LLM agent authors a
plan and then audits it, the audit inherits the author's search-path momentum —
the locations the author did not check during planning are the same locations
the author will not check during audit. Independent reviewers with no
plan-authorship context naturally check different sources.

Operator dispatch protocol for Option B (any of the following clears
author-context):

- **Fresh-context audit**: re-run `/qor-audit` in a new session (different
  `.qor/session/current`) so the LLM running the audit has no carryover from
  plan authorship.
- **Architect-reviewer subagent**: invoke an `architect-reviewer` (or
  `code-reviewer`) subagent for the audit pass; the subagent receives only the
  plan content, not the plan-authoring conversation.
- **Second operator**: dispatch the audit to a second human (or human+LLM)
  operator who did not participate in plan authorship.

Operator selects Option A by default when the harness supports Codex plugin;
Option B otherwise. Selecting Option B mid-cycle is also valid when the operator
notices that prior audit iterations missed defects the author would not have
searched for (cross-reference: SG-007 empirical results — sub-plan 01 audit
chain found 4 self-audit defects + 3 additional independent-reviewer defects;
sub-plan 02a found 10/9/12 with independent review from iter 1 including critical
`pg_notify` durability hallucination).

## Author-momentum risk auto-dispatch (Phase 87 wiring; GH #82)

Before the adversarial passes, `/qor-audit` Step 1 scores the plan under audit
for SG-007 author-momentum risk via `qor-logic scripts audit_risk_score --plan
<plan>`. When `audit_risk_score` reports `option_b_required: true`, Option B is
**mandatory** for this audit — the auditing agent MUST run an independent
reviewer (architect-reviewer subagent or fresh-context audit), not a solo audit,
regardless of the Option A/B operator default above. This makes Option B
proactive: dispatched on the iteration where the author-momentum risk first
appears, not reactively after a VETO. The operator may override the mandate only
with explicit written justification recorded in the audit report. Per
`qor/references/doctrine-shadow-genome-countermeasures.md`
SG-AuthorAuditMomentum-A.

## Self-Application Sub-Pass pattern origin (Phase 68 wiring; GH #44)

The Step 3 Self-Application Sub-Pass (run when the plan's `originating_remediation`
field is set) traces to **SG-007 (self-audit verification scope bias)** and the
recurring "author-audit momentum" anti-pattern — when the same agent that
authored a plan also audits it, the audit inherits the author's search-path
momentum and misses precisely the locations the author would also not check. The
concrete recurrence is documented in the COREFORGE 3-VETO meta-cycle: META_LEDGER
#200/#201/#203 (consumer ledger) where the plan authoring
`plan_text_consistency_lint` itself exhibited the very text-drift pattern the
lint targets. The originating Failure Entry #26 ratified self-application as the
framework countermeasure.

## See also

- `qor/scripts/qor_audit_runtime.py` — `should_run_adversarial_mode`, `emit_capability_shortfall`
- `qor/gates/schema/audit.schema.json` — audit gate artifact schema (input data lineage)
- `qor/platform/profiles/claude-code-with-codex.md` — profile that wires the actual invocation (when authored)
- `qor/references/doctrine-token-efficiency.md` — Codex critique should be summarized at synthesis time, not pasted in full
