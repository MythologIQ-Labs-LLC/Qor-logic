# Plan: Phase 99 — /qor-audit Runtime Contract Walk V2 (GH #108 full close)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #108

**boundaries**:
- limitations: V2 ships an audit-side `runtime_contract_walk` that
  walks the import graph one hop in each direction for any Python
  module path cited in a plan's Affected Files or body text. Forward
  walk: the cited module's own `import` statements all parse without
  error. Backward walk: at least one production caller of the cited
  module parses without error. Wired into `/qor-audit` Step 3
  Infrastructure Alignment Pass as a NEW sub-check; starts WARN-only
  because no Phase 96 V1 operator-evidence has been gathered yet in
  this same-session cluster. A separate future phase converts the
  WARN to a hard VETO once V1 false-positive evidence is in.
- non_goals: multi-language walk (Rust/TS/JS — V1+V2 both Python-only);
  hard VETO at first rollout (deferred to a V2-of-V2 phase with
  operator-evidence requirement); replacing the existing Infrastructure
  Alignment grep-verify checks (the walk complements them, doesn't
  supplant); auto-rewriting plans on walk failure (the walk emits
  findings; operator amends the plan).
- exclusions: no changes to Phase 96's recon-side `reachability_probe`
  (separate mechanism for a separate phase of the lifecycle); no
  changes to existing Step 0.6 pre-audit lints (the walk runs INSIDE
  Step 3, not at Step 0.6); no changes to Step 4.6.* substantiate
  gates; no changes to skill Environment blocks (the walk runs only
  when qor.scripts.runtime_contract_walk is importable, otherwise
  Phase 75 SKIP applies).

## Open Questions

None. The operator-evidence question on V1 false-positive rate is
explicitly deferred to a future V2-of-V2 phase per the cluster
discipline; Phase 99 ships V2 with the WARN ramp matching that
discipline.

## Feature Inventory Touches

Empty. New script + skill prose extension + reference file +
doctrine extension + tests.
`feature_inventory_touches`: `[]`.

## Design notes

GH #108's V2 proposal: `/qor-audit` Step 3 Infrastructure Alignment
Pass gains a new "Runtime Contract Walk" sub-pass. When auditing a
plan that cites a Python module path, the Judge walks the import
graph one hop in each direction:

- **Forward walk** (callees): the cited module's own `import` and
  `from X import Y` statements all resolve and parse without error
  in the project's actual environment.
- **Backward walk** (callers): at least one production code path
  (non-test, non-scratch, non-doc) imports the cited surface and that
  caller parses without error.

Half-failures route back to `/qor-plan` per the cluster's V2 enforcement
pattern. The walk catches plan claims about runtime surfaces that
will fail at implementation time but pass grep-based Infrastructure
Alignment.

**V2 enforcement ramp**: Per Phase 96 plan's V1/V2 split rationale,
V2 enforcement requires operator-evidence on V1 false-positive rate
before tightening. Same-session cluster means no Phase 96 evidence
has accumulated yet. Phase 99 ships V2 with the binding sub-pass
WIRED but invoked WARN-only (the `|| true` wrap). A future V2-of-V2
phase (post-evidence) removes the wrap and converts to hard VETO.

This is the same pattern Phases 93/94/95 used: WARN-only V1 first,
hard ABORT once false-positive rate is characterized in production
adoption.

**Walk vs probe distinction**:
- Phase 96 V1 `reachability_probe`: five-check probe per recon
  claim; operator-action; recon Phase 3 Round 0; WARN-only.
- Phase 99 V2 `runtime_contract_walk`: two-direction import graph
  walk per plan-cited module; audit-side; Step 3 Infrastructure
  Alignment; WARN-only ramp to VETO.

Different mechanisms for different lifecycle phases. Both close GH
#108 — V1 catches drift at recon time (before plan); V2 catches drift
at audit time (after plan, before implement).

**Progressive disclosure**: per `SG-SkillCorpusGrowth-A` doctrine,
the detailed walk protocol lives in
`qor/references/audit-runtime-contract-walk.md` (NEW); the SKILL.md
gains only a short pointer + one-paragraph summary. qor-audit/SKILL.md
is currently at 43.5 KB (EXCEEDED per Phase 95 lint); adding the full
protocol inline would worsen the standing finding. The reference-file
approach is the standard countermeasure.

**Self-application anchor** (per cluster standard): the dogfooding
test invokes the walk against a synthetic plan citing a deliberately-
broken module fixture and asserts the walk emits both forward and
backward findings. The plan also runs the walk against its OWN plan
file to confirm zero findings (the canonical positive case).

## Phase 1: runtime_contract_walk + Step 3 wiring + tests

### Affected Files

- `qor/scripts/runtime_contract_walk.py` — NEW. The walk module
  (~150 LOC).
- `qor/skills/governance/qor-audit/SKILL.md` — Step 3 Infrastructure
  Alignment Pass gains a brief Runtime Contract Walk sub-block with
  one-paragraph summary + reference pointer (progressive disclosure).
- `qor/references/audit-runtime-contract-walk.md` — NEW. Detailed
  two-direction walk protocol + WARN ramp rationale + canonical
  example.
- `qor/references/doctrine-shadow-genome-countermeasures.md` —
  extends `SG-GrepShapedRunclaim-A` entry with the V2 enforcement
  clause and operator-evidence-ramp paragraph.
- `tests/test_runtime_contract_walk.py` — NEW. Behavior tests +
  dogfooding anchor (synthetic broken plan + canonical positive).
- `tests/test_runtime_contract_walk_audit_wiring.py` — NEW. Step 3
  wiring tests.
- `docs/plan-qor-phase99-audit-runtime-contract-walk.md` — NEW. This
  plan.

### Unit Tests

- `tests/test_runtime_contract_walk.py`
  - `test_walk_extracts_python_module_paths_from_plan_affected_files`
  - `test_walk_forward_passes_when_callees_parse_cleanly` (tmp synthetic)
  - `test_walk_forward_flags_when_callee_has_syntax_error`
  - `test_walk_backward_passes_when_caller_exists` (tmp synthetic)
  - `test_walk_backward_flags_when_no_production_caller` (tmp synthetic)
  - `test_walk_skips_when_module_path_does_not_resolve` (gracefully)
  - `test_main_cli_exits_zero_on_no_findings` (subprocess)
  - `test_main_cli_exits_one_when_exit_on_any_set` (subprocess)
  - `test_walk_self_application_on_phase_99_plan_emits_zero_findings`
    (positive dogfooding anchor — walk against Phase 99's own plan)

- `tests/test_runtime_contract_walk_audit_wiring.py`
  - `test_step_3_infrastructure_alignment_cites_runtime_contract_walk`
    (anchored positive on SKILL.md addition)
  - `test_step_3_runtime_contract_walk_warns_only_in_v2_ramp`
    (asserts the `|| true` WARN wrapper is present, not a hard VETO)
  - `test_audit_skill_references_progressive_disclosure_reference_file`
    (sweep)

### Changes

`qor/scripts/runtime_contract_walk.py`:

```python
from dataclasses import dataclass
from pathlib import Path
import ast, re, subprocess, sys

@dataclass(frozen=True)
class WalkFinding:
    module_path: str
    direction: str  # 'forward' (callees) or 'backward' (callers)
    detail: str
    severity: str = "warn"

def extract_python_modules_from_plan(plan_path: Path) -> list[str]: ...
def walk_forward(module_path: str, repo_root: Path) -> list[WalkFinding]: ...
def walk_backward(module_path: str, repo_root: Path) -> list[WalkFinding]: ...
def walk_plan(plan_path: Path, repo_root: Path) -> list[WalkFinding]: ...
def main(argv: list[str] | None = None) -> int: ...
```

`/qor-audit` Step 3 Infrastructure Alignment Pass extension (added
after the existing infrastructure alignment block at line ~418):

```markdown
**Phase 99 wiring (GH #108 V2)**: After the grep-verify checks above,
run the Runtime Contract Walk against the plan to catch runtime
contract drift that grep cannot see — module imports that don't
resolve at runtime, callers whose own imports fail to parse, etc.
The walk runs one hop forward (callees) and one hop backward
(callers) for each Python module path cited in the plan. WARN-only
in V2; a future V2-of-V2 phase converts to hard VETO once operator
evidence on V1 false-positive rate is in. See
`qor/references/audit-runtime-contract-walk.md` for the detailed
two-direction protocol and `SG-GrepShapedRunclaim-A` for the binding
doctrine.

```bash
python -m qor.scripts.runtime_contract_walk --plan <plan-path> || true
```
```

`SG-GrepShapedRunclaim-A` doctrine entry extension (replaces the
existing "V2 reserved" sub-paragraph with the now-shipped V2
implementation paragraph + V2-of-V2 reservation).

## Definition of Done

### Deliverable: runtime_contract_walk module

- **D1**: A pure-Python walk exists that parses a plan path, extracts
  Python module paths cited in it, and runs forward+backward import-
  graph walks one hop each.
- **D2**: `qor/scripts/runtime_contract_walk.py:walk_plan(plan_path, repo_root) -> list[WalkFinding]`
  with frozen dataclass; `main()` CLI WARN-only by default; `--exit-on-any`
  opts into CI-style failure.
- **D3**: Plan + ledger + SYSTEM_STATE Phase 99 entry seal.
- **D4**: `tests/test_runtime_contract_walk.py` carries 9 assertions
  including forward+backward pass/fail, CLI exit modes, graceful
  skip-on-unresolvable, dogfooding (Phase 99 plan walks clean).

### Deliverable: qor-audit Step 3 Runtime Contract Walk wiring

- **D1**: `/qor-audit` Step 3 Infrastructure Alignment Pass invokes
  the walk as a sub-check; WARN-only ramp; pointer to reference file.
- **D2**: `qor/skills/governance/qor-audit/SKILL.md` gains the
  Phase 99 wiring paragraph after the existing infrastructure
  alignment block; `|| true` WARN wrapper present.
- **D3**: Plan + ledger entries cover the SKILL.md change; doctrine
  cross-references SG-GrepShapedRunclaim-A V2 extension.
- **D4**: `tests/test_runtime_contract_walk_audit_wiring.py` carries
  three assertions: anchored positive (Phase 99 wiring paragraph
  present); WARN-only assertion (`|| true` present, not hard VETO);
  progressive-disclosure sweep (SKILL.md cites the reference file).

### Deliverable: audit-runtime-contract-walk reference file

- **D1**: A reference file exists carrying the detailed two-direction
  walk protocol + WARN ramp rationale + canonical example.
- **D2**: `qor/references/audit-runtime-contract-walk.md` exists with
  sections for forward walk + backward walk + WARN-to-VETO ramp +
  examples + cross-references.
- **D3**: Plan + ledger seal.
- **D4.d**: Waiver. Reference files are operator-readable prose; the walk behavior is exercised by the module tests above. **Follow-up phase**: a V2-of-V2 phase (post-evidence) will reference this file again when removing the `|| true` wrap and converting to hard VETO.

### Deliverable: SG-GrepShapedRunclaim-A doctrine V2 extension

- **D1**: The doctrine entry's "V2 reserved" paragraph is replaced
  with the shipped V2 implementation paragraph + operator-evidence
  ramp clause.
- **D2**: `qor/references/doctrine-shadow-genome-countermeasures.md`
  `SG-GrepShapedRunclaim-A` section updated: "V2 reserved" line
  replaced; the new V2 paragraph describes the walk mechanism, the
  WARN-only ramp, and the V2-of-V2 evidence requirement.
- **D3**: Plan + ledger seal.
- **D4.d**: Waiver. Doctrine prose is operator-readable; the V2 behavior is exercised by the walk tests. **Follow-up phase**: V2-of-V2 will further extend this entry when the WARN -> VETO flip lands.

## CI Coverage Exemptions

None.

## CI Commands

- `python -m pytest tests/test_runtime_contract_walk.py -q` — behavior tests.
- `python -m pytest tests/test_runtime_contract_walk_audit_wiring.py -q` — Step 3 wiring tests.
- `python -m pytest tests/ -v` — full regression.
- `python qor/scripts/check_variant_drift.py` — ci.yml.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` — ci.yml.
- `python -m pytest tests/test_packaging_install.py -v -m integration` — install-smoke.
- `python -m qor.reliability.gate_chain_completeness --phase-min 52` — gate-chain.
- `python qor/scripts/pr_citation_lint.py` — pr-lint.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase99-audit-runtime-contract-walk.md` — plan-internal.
- `python -m qor.scripts.ci_coverage_lint --plan docs/plan-qor-phase99-audit-runtime-contract-walk.md --workflows-dir .github/workflows` — Phase 89 ci-coverage.
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase99-audit-runtime-contract-walk.md` — Phase 92 DoD check.
- `python -m qor.scripts.skill_size_budget_lint --skills-root qor/skills` — Phase 95 size-budget (WARN-only).
- `python -m qor.scripts.runtime_contract_walk --plan docs/plan-qor-phase99-audit-runtime-contract-walk.md` — Phase 99 self-application.
