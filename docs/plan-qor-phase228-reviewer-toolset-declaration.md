# Plan: The reviewer declares what it can verify

**iteration**: 1

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: The contract is prose-enforced at dispatch time; there is no machine-readable dispatch-prompt artifact to lint, so enforcement is the wiring tests plus the Judge's report discipline (V1 disclosure posture, like other prose contracts).
- non_goals: No change to the external-reviewer subprocess bridge, the Option A/B selection rules, or the author-momentum mandate. No `cycle_count_escalator` per-category enhancements (remain with GH #342 as enhancement, not debt). No reopening of the three Phase 223 closures (the shipped state resolves GH #342's decision checkbox toward documented acceptance, recorded at cycle end).
- exclusions: GH #332, GH #337, GH #320, GH #286, GH #341.

## Open Questions

None. The contract text is the Phase 223 remediation's own specification, sharpened into three numbered rules; its home and anchor follow the existing Step 1 delegation pattern.

## Locked Decisions

**LD-1: The anchor lands in the step the repointed citation names; the step heading is the anchor's host.**

```
git show v0.148.1:qor/skills/governance/qor-audit/SKILL.md | grep -nE '^### Step 1: Identity Activation' -> 180:### Step 1: Identity Activation + Mode Selection
```

**LD-2: The contract body joins the Option B dispatch protocol in the reference file, beside the dispatch options it governs.**

```
git show v0.148.1:qor/skills/governance/qor-audit/references/adversarial-mode.md | grep -nE '^Operator dispatch protocol for Option B' -> 105:Operator dispatch protocol for Option B (any of the following clears
```

**LD-3: The contract has three rules, verbatim intent from the Phase 223 remediation proposal**: the dispatched reviewer opens its report by declaring its available toolset (shell, git, repository file access, network); the Judge maps every mandating finding's verification to the declared set and may not pin as reviewer-verified a verification outside it (the orchestrating agent re-executes, or the finding carries PLAUSIBLE until re-executed); the audit report's Mode line records the declared toolset.

**LD-4: The `7b2ed33a` repointment to `/qor-audit Step 1` executes only after Phases 1-2 are green, under a reviews-remediate PASS attestation with repo-relative artifact paths**, per ledger #597's hold condition and the #344 publication-boundary lesson. `addressed` and `addressed_ts` untouched (corrective-path contract, `tests/test_remediate_enforcer_edges.py`).

## Phase 1: Bind the contract's tokens (tests first)

### Affected Files

- `tests/test_reviewer_toolset_wiring.py` - NEW; two wiring tests, both red at v0.148.1.

### Unit Tests

- `test_the_reference_carries_the_toolset_contract` - `references/adversarial-mode.md` contains the section heading `## Reviewer toolset declaration` and its two binding token phrases: `declares its available toolset` and `may not pin`.
- `test_step_1_anchors_the_toolset_contract` - the SKILL.md Step 1 region (from the Step 1 heading to the next `### Step` heading) names the reference section token `Reviewer toolset declaration`, so the gate-step citation `/qor-audit Step 1` resolves to a step that carries the contract.

## Phase 2: Author the contract

### Affected Files

- `qor/skills/governance/qor-audit/references/adversarial-mode.md` - NEW section `## Reviewer toolset declaration (Phase 228; GH #342)` with the three LD-3 rules and the SG-context (the Phase 223 recurrence: a no-shell reviewer had a content-hash freeze attestation pinned across four iterations).
- `qor/skills/governance/qor-audit/SKILL.md` - ONE anchor sentence appended to the Step 1 adversarial-mode delegation paragraph (the file is in the 25 KB WARN band; prose stays in the reference).

### Changes

Phase 1's two tests go green; the five existing qor-audit wiring tests stay green (additive tokens only).

### Unit Tests

- Phase 1's two tests observed red-then-green.
- `tests/test_external_reviewer_wiring.py`, `tests/test_runtime_principal_wiring.py`, `tests/test_session_total_escalator_skill_wiring.py`, `tests/test_spec_delta_wiring.py`, `tests/test_plan_text_consistency_lint_audit_wiring.py` - caller sweep, green unmodified.

## Phase 3: Repoint the held closure citation

### Affected Files

- `docs/PROCESS_SHADOW_GENOME.md` - event `7b2ed33a...` closure_enforcer repointed from `qor.scripts.cycle_count_escalator` to `/qor-audit Step 1` via `correct_closure_enforcers` under a reviews-remediate PASS attestation (artifacts in this session's gate directory, repo-relative paths).

### Unit Tests

- `tests/test_remediate_enforcer_edges.py::test_corrective_repair_leaves_addressed_true` - existing, unmodified; the shipped contract this step relies on.

## Feature Inventory Touches

None. Skill corpus, reference prose, wiring tests, and a shadow-log provenance correction.

## Definition of Done

### Deliverable 1: The toolset contract exists where the citation points

- **D1**: A dispatched reviewer's verification authority is bounded by what it declares it can execute.
- **D2**: The reference section with the three rules; the one-line Step 1 anchor.
- **D3**: Implement-phase ledger entry cites this plan; seal binds this plan file.
- **D4**: both wiring tests observed red at v0.148.1 and green after Phase 2.

### Deliverable 2: Truthful repointment (GH #342 held item two)

- **D1**: The closure citation for `7b2ed33a` names a step that carries the contract on the day it is recorded.
- **D2**: `correct_closure_enforcers` execution under PASS attestation, this session, repo-relative paths.
- **D4**: post-flip event state observed: `closure_enforcer == "/qor-audit Step 1"`, `addressed` true, `addressed_ts` unchanged.

## CI Commands

- `python -m pytest tests/ -q` -- full suite; the new wiring tests and every existing qor-audit wiring test green.
- `qor-logic-plus scripts plan_text_consistency_lint --check docs/plan-qor-phase228-reviewer-toolset-declaration.md` -- plan-internal consistency.
- `python -m qor.scripts.plan_grep_lint --plan docs/plan-qor-phase228-reviewer-toolset-declaration.md --repo-root .` -- citation truth check over this plan's Locked Decisions.
