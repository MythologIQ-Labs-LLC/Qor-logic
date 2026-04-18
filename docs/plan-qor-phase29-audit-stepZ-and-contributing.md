# Plan: Phase 29 - /qor-audit Step Z + CONTRIBUTING.md

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations:
  - Scope is strictly the missing `/qor-audit` Step Z wiring and a minimal root CONTRIBUTING.md. Does not rewrite any audit pass, does not add new audit rubric, does not expand CONTRIBUTING beyond a pointer + quickstart.
  - Does not retroactively rewrite previously-written `audit.json` artifacts; those were hand-written during Phase 28 and remain as-is.
- non_goals:
  - PR template under `.github/PULL_REQUEST_TEMPLATE.md` (scope creep; only pays off with external contributors).
  - Automation bots, issue templates, contributor CLAs.
  - External contributor outreach.
- exclusions:
  - Other governance-related skills that may lack Step Z artifacts (none known); if one surfaces, a separate plan opens.
  - The retroactive audit.json written by hand for session `2026-04-17T2335-f284b9` is not rewritten to match the new Step Z format; it stays as evidence of the gap that this plan closes.

**Target Version**: next minor bump after v0.19.0 (governed by Step 7.5 of /qor-substantiate).

**Basis**: Phase 28 inventory surfaced that `/qor-audit` lacks a Step Z gate artifact write, forcing downstream phases to either fail the gate check or hand-write `audit.json`. The second approach was used once during Phase 28 session sealing; it is technical debt that this plan repays. GAP-REPO-07 (no CONTRIBUTING.md) is closed as a paired concern since both touch the "contributor onboarding" surface.

## Open Questions

1. Audit Step Z payload fields: minimum is `verdict`, `target`, `report_path`, `risk_grade`. Optional additions: `pass_number` (current is 1 for a fresh audit, >1 for re-audits after amendment), `violations` (structured list of VETO grounds). Plan assumes minimum payload for this phase; extensions deferred to when a concrete consumer needs them. Confirm before Phase 1.
2. CONTRIBUTING.md location: repo root is canonical for GitHub discovery. Plan assumes root.
3. CHANGELOG entry grouping: combine both changes under a single release section, or split into Added (CONTRIBUTING) + Changed (audit skill)? Plan assumes combined under v0.20.0 with two distinct bullets.

## Phase 1: `/qor-audit` Step Z wiring

Add the missing gate artifact write to `/qor-audit` so `audit.json` lands at `.qor/gates/<session>/audit.json` for downstream phases. Uses the existing `gate_chain.write_gate_artifact` helper; no new code paths, no schema change.

### Affected Files

- `tests/test_audit_gate_artifact.py` - NEW; asserts Step Z writes a schema-valid audit.json for both PASS and VETO verdicts.
- `qor/skills/governance/qor-audit/SKILL.md` - MODIFY; add Step Z block after Step 7 (Final Report).
- `qor/skills/governance/qor-audit/references/qor-audit-templates.md` - MODIFY; add a short subsection documenting the Step Z payload shape.

### Changes

**`/qor-audit` SKILL.md Step Z**. Insert after Step 7 (Final Report), before Constraints:

```markdown
### Step Z: Write Gate Artifact (Phase 29 wiring)

Persist the structured gate artifact at `.qor/gates/<session_id>/audit.json` so `/qor-implement` (and any other downstream phase) can read it via `gate_chain.check_prior_artifact`.

\`\`\`python
import sys; sys.path.insert(0, 'qor/scripts')
import gate_chain, shadow_process

payload = {
    "ts": shadow_process.now_iso(),
    "target": plan_path,          # the plan audited (from Step 2)
    "verdict": verdict,           # "PASS" or "VETO"
    "report_path": ".agent/staging/AUDIT_REPORT.md",
    "risk_grade": risk_grade,     # "L1" | "L2" | "L3" from Step 3
}
gate_chain.write_gate_artifact(phase="audit", payload=payload, session_id=sid)
\`\`\`

Schema lives at `qor/gates/schema/audit.schema.json`; the helper validates before write. No silent fallback; a write failure surfaces a `ValueError` the operator must resolve before proceeding.
```

**`qor-audit-templates.md` addition**. Single-paragraph subsection "Step Z payload shape" referencing the SKILL.md block, listing required fields (`phase`, `ts`, `session_id`, `target`, `verdict`) and optional fields (`violations`, `risk_grade`, `report_path`) per the existing schema. No new fields introduced.

**No schema change**. The existing `qor/gates/schema/audit.schema.json` already accepts these fields; Phase 29 is a prompt-layer fix, not a schema extension.

### Unit Tests

- `tests/test_audit_gate_artifact.py`:
  - `test_audit_step_z_writes_pass_verdict` - write payload with verdict=PASS; reads back; asserts round-trip matches schema.
  - `test_audit_step_z_writes_veto_verdict_with_risk_grade` - same for VETO + L2.
  - `test_audit_step_z_rejects_missing_required_fields` - write payload without `target` -> raises (schema enforcement).
  - `test_audit_step_z_rejects_bogus_verdict` - verdict="MAYBE" -> raises (enum enforcement).
  - `test_downstream_phases_can_read_audit_json` - after Step Z write, `gate_chain.check_prior_artifact("implement")` returns found=True, valid=True (proves the missing-link gap is closed).

## Phase 2: CONTRIBUTING.md (pointer + quickstart)

Author a root CONTRIBUTING.md following option B from the dialogue: pointer-heavy, with a 5-line quickstart recipe pointing into the /qor-* governance flow. No PR template, no examples, no machine-enforced templates.

### Affected Files

- `tests/test_contributing_quickstart.py` - NEW; asserts CONTRIBUTING.md exists at root and names the canonical skill chain.
- `CONTRIBUTING.md` - NEW (repo root); ~60 lines.
- `qor/references/glossary.md` - MODIFY; extend `referenced_by:` lists across **seven** entries to adopt Phase-28-introduced orphans (audit pass-1 Ground 1). See the adoption table below.
- `README.md` - MODIFY (one line); add a CONTRIBUTING.md link in the appropriate section.

#### Glossary orphan adoption table (closes audit pass-1 Ground 1)

Phase 28 introduced six glossary entries whose `referenced_by:` was empty; their grace-period plan tag (`phase28-documentation-integrity`) no longer matches Phase 29's slug, so `check_orphans` would ABORT substantiation unless adopted. Each entry gains at least one legitimate consumer:

| Term                          | Add to `referenced_by:`                                                                 |
|-------------------------------|-----------------------------------------------------------------------------------------|
| `Doctrine`                    | `CONTRIBUTING.md` (already planned; carried forward)                                    |
| `Doc Tier`                    | `qor/skills/sdlc/qor-plan/SKILL.md`, `qor/gates/schema/plan.schema.json`                |
| `Glossary Entry`              | `qor/scripts/doc_integrity.py`                                                          |
| `Concept Home`                | `qor/references/glossary.md` (self-reference is legitimate: the file IS the registry)   |
| `Orphan Concept`              | `qor/scripts/doc_integrity.py`                                                          |
| `Doc Integrity Check Surface` | `qor/references/doctrine-documentation-integrity.md`                                    |
| `Complecting`                 | `qor/skills/sdlc/qor-plan/SKILL.md`                                                     |

Consumers cited are all pre-existing files that factually reference the concept; no synthetic "citation" is invented.

### Changes

**`CONTRIBUTING.md` structure**:

1. Header (1 paragraph): "Qor-logic is a prompt system. Contributions are proposed, audited, implemented, and sealed through the `/qor-*` skill chain. This document points to the authorities; read them in order."
2. Reading order (bulleted list, ~6 items): `CLAUDE.md` (token efficiency + test discipline + governance flow) -> `qor/gates/chain.md` (phase sequence) -> `qor/gates/delegation-table.md` (handoff matrix) -> `qor/gates/workflow-bundles.md` (multi-phase orchestration) -> `qor/references/doctrine-*` (deep dives) -> `qor/references/glossary.md` (terminology).
3. Quickstart (5 lines, fenced): the canonical `/qor-research` -> `/qor-plan` -> `/qor-audit` -> `/qor-implement` -> `/qor-substantiate` chain, with a note that `/qor-substantiate` Step 9.6 offers four push/merge options and that PR descriptions must cite plan file + ledger entry + Merkle seal per `doctrine-governance-enforcement.md` §6.
4. "What NOT to do" (~5 bullets): no direct-to-main pushes, no governance-artifact edits outside the flow, no skipping `/qor-audit`, no silent overrides of gate checks, no inventing new terminology without a glossary entry.
5. Where to ask questions: point to `docs/BACKLOG.md` + existing issues.

**`README.md`**: single-line addition in an appropriate section (likely under "Getting Started" or equivalent) linking to `CONTRIBUTING.md`.

**`qor/references/glossary.md`**: extend `referenced_by:` on all seven entries per the adoption table above. This is the concrete Ground 1 remediation and also the first live demonstration that Qor-logic's plans actively consume the Phase 28 doctrine rather than pay it lip service.

### Unit Tests

- `tests/test_contributing_quickstart.py`:
  - `test_contributing_md_exists` - file is at repo root.
  - `test_contributing_names_canonical_skill_chain` - body contains `/qor-research`, `/qor-plan`, `/qor-audit`, `/qor-implement`, `/qor-substantiate` in that order (regex or sequential-index check).
  - `test_contributing_references_governance_enforcement_for_pr_template` - body cites `doctrine-governance-enforcement.md` for PR description contract (single source of truth rule: if governance-enforcement changes, CONTRIBUTING should delegate, not duplicate).
  - `test_contributing_under_line_limit` - file is <= 80 lines (prevents scope creep; option B boundary).
  - `test_glossary_doctrine_entry_names_contributing` - the glossary's `Doctrine` entry's `referenced_by` includes `CONTRIBUTING.md` (dogfood: Phase 28's glossary-hygiene rule is actively enforced, not just declared).
  - `test_no_phase28_orphan_terms_remain` - every glossary entry whose `introduced_in_plan` is `phase28-documentation-integrity` has a non-empty `referenced_by:` list. Guards against Phase 29's own Step 4.7 ABORT; also serves as a forward-looking regression check for future phases (any later plan that accidentally strips a consumer re-orphans the entry and this test fails).

## CI Commands

Validate both phases via:

- `python -m pytest tests/test_audit_gate_artifact.py -v` (Phase 1).
- `python -m pytest tests/test_contributing_quickstart.py -v` (Phase 2).
- `python -m pytest tests/ 2>&1 | tail -3` (full suite regression).
- `python qor/reliability/skill-admission.py qor-audit` (confirm audit SKILL.md still admits after Step Z addition).
- `python qor/reliability/gate-skill-matrix.py` (no broken handoffs after doctrine cross-link).
- `python -c "import sys; sys.path.insert(0, 'qor/scripts'); import doc_integrity; plan = {'doc_tier':'standard','terms':[],'plan_slug':'phase29-audit-stepZ-and-contributing'}; doc_integrity.run_all_checks_from_plan(plan, repo_root='.')"` (Phase 28 doctrine self-check: Phase 29 must pass Step 4.7 at seal; CONTRIBUTING.md counts as an additional standard-tier consumer for the Doctrine glossary entry).

Each phase's tests must pass on two consecutive runs before the phase is marked complete (CLAUDE.md test-discipline).

## Self-Dogfood

Per SG-Phase28-A (doctrine-introduction plans must self-apply the rules they introduce; extended here to future plans for consistency):

- **`doc_tier` declaration satisfied**: plan top-matter declares `**doc_tier**: standard`. Evidence: line 5.
- **`terms_introduced`** omitted intentionally: this plan closes existing gaps and does not introduce new domain concepts. No terms to register.
- **`boundaries` block populated**: non-trivial entries for limitations / non_goals / exclusions; overengineering fence is explicit.
- **Every new rule has a test**:
  - Rule "audit SKILL writes schema-valid audit.json at Step Z" -> `test_audit_step_z_writes_pass_verdict` + `test_audit_step_z_writes_veto_verdict_with_risk_grade`.
  - Rule "downstream phases can now check audit.json" -> `test_downstream_phases_can_read_audit_json`.
  - Rule "CONTRIBUTING.md exists and names the chain" -> `test_contributing_names_canonical_skill_chain`.
  - Rule "CONTRIBUTING.md stays under 80 lines (option-B fence)" -> `test_contributing_under_line_limit`.
  - Rule "glossary stays in sync with new consumers" -> `test_glossary_doctrine_entry_names_contributing`.
  - Rule "no Phase-28-introduced glossary entry remains orphan once its grace period expires" -> `test_no_phase28_orphan_terms_remain` (added in audit pass-1 remediation; Ground 1).
- **Enumeration cross-check**: the six reading-order items in CONTRIBUTING.md (CLAUDE.md, chain.md, delegation-table.md, workflow-bundles.md, doctrine-*, glossary.md) match the Phase 2 Changes section description ("~6 items"). No drift.
- **No bare-word YAML/TOML/JSON** appears in this plan requiring a safe-loader citation; Phase 29 touches markdown docs and a pre-existing helper only.
- **No schema change**: this plan stays in the prompt-layer per user's "standalone prompt system" guidance. `qor/gates/schema/audit.schema.json` is unchanged.

## Delegation

Per `qor/gates/delegation-table.md`:

- Plan complete -> `/qor-audit` (next phase).
- Phase 1 reveals that `gate_chain.write_gate_artifact` needs new fields to serve the audit payload (e.g., structured `violations` array) -> halt and open a separate schema-extension plan; do not balloon this one.
- Phase 2 reveals that CONTRIBUTING.md needs examples or templates beyond the quickstart -> halt and re-open dialogue via `/qor-plan`; do not silently widen scope past option B.
