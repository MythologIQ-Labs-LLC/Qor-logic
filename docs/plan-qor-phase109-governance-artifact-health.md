# Plan: Phase 109 - Governance artifact health gate

**change_class**: feature

**doc_tier**: system

**terms_introduced**:
- term: Governance Artifact Health
  home: qor/references/doctrine-prompt-resilience.md
- term: Ungoverned Path Forward
  home: qor/references/doctrine-prompt-resilience.md
- term: Governance Repair Mode
  home: qor/references/skill-recovery-pattern.md

**boundaries**:
- limitations: This phase makes missing, damaged, and incomplete governance artifacts mechanically visible before skill execution proceeds. It does not attempt to repair damaged historical ledger content automatically.
- non_goals: No automatic bootstrap over an existing `docs/META_LEDGER.md`; no silent creation of authoritative content beyond idempotent scaffold files; no replacement for `/qor-remediate` when governance state is corrupt.
- exclusions: No migration of archived historical prompt files under `docs/archive/`; no changes to non-Qor third-party skills.

**high_risk_target**: true

**impact_assessment**:
- **purpose**: Prevent any `/qor-*` prompt from inventing an ungoverned continuation path when required governance artifacts are missing, damaged, or incomplete.
- **affected_stakeholders**: Qor-logic operators, downstream Qor-governed projects, reviewers relying on `META_LEDGER` and gate artifacts, and future agents consuming the skill corpus.
- **identified_risks**: (R1) A prompt may continue after a missing file by substituting assumptions. (R2) A damaged ledger or malformed governance file may be treated as absent and overwritten. (R3) A seeded placeholder may be accepted as meaningful project governance. (R4) Generated variant skills may drift from source skill recovery rules.
- **mitigations**: (M1) Add one reusable governance-health checker with explicit statuses. (M2) Permit `qor-logic seed` only for missing scaffold in uninitialized or recoverable scaffold cases; damaged existing artifacts block and route to repair. (M3) Add prompt lint coverage so governance reads require a health preflight or a justified fail-fast marker. (M4) Run variant drift and prompt-resilience tests in CI.
- **residual_risks**: Heuristic completeness checks may not catch every stale value inside a syntactically valid artifact. The plan mitigates this by making the health registry extensible and by treating `GOVERNANCE_INDEX.md` as the future freshness surface.

## Open Questions

None. Operator direction is explicit: missing, damaged, or incomplete governance artifacts must never be ignored, and inventing an ungoverned path forward is invalid.

## Locked Decisions

- **LD1 (Governance Index scope)**: `docs/GOVERNANCE_INDEX.md` and `qor/templates/GOVERNANCE_INDEX.md` are NOT created in Phase 109. The checker's required-artifact registry is the freshness surface and remains extensible so a future Governance Index phase appends the row without changing call sites. Evidence: no `GOVERNANCE_INDEX` reference exists anywhere in the tree (`grep -rl GOVERNANCE_INDEX qor/ docs/` empty); the plan's `residual_risks` frames it as "the future freshness surface."
- **LD2 (CLI surface)**: `qor-logic governance-health` is implemented as a user-facing command delegating to `qor.scripts.governance_health`, with exit codes 0 (all OK), 1 (MISSING/INCOMPLETE), 2 (DAMAGED). Evidence: Definition of Done D-109.3 D4 and the CI Commands list both require `tests/test_cli_governance_health.py` to pass.
- **LD3 (scaffold-owned set)**: scaffold-owned (seed-repairable) artifacts equal `qor.seed.SEED_TARGETS` paths (`META_LEDGER`, `SHADOW_GENOME`, `ARCHITECTURE_PLAN`, `CONCEPT`, `SYSTEM_STATE`). `BACKLOG.md` and `FEATURE_INDEX.md` are required but NOT scaffold-owned: when MISSING they route to `/qor-remediate`, not seed. A test pins the checker's scaffold-owned set to `SEED_TARGETS` so the two lists cannot drift.

## Context

Phase 25 introduced `qor-logic seed` and prompt-resilience markers. The implemented behavior is useful but too narrow for the stronger invariant now required:

- `qor-logic seed` creates a scaffold, but not every prompt is forced to run a governance-health check.
- Interactive skills such as `/qor-audit` and `/qor-validate` have recovery prompts, but other skills read governance files directly.
- `/qor-status` reports `UNINITIALIZED` when `docs/META_LEDGER.md` is missing, but it does not distinguish missing, damaged, and incomplete governance state.
- Bootstrap is correctly forbidden over an existing ledger, but the source prompts do not yet encode the broader rule: existing damaged governance blocks forward motion until repaired.

The target invariant for this phase:

> A skill may proceed only after required governance artifacts are classified as healthy, or after it has taken an explicitly governed recovery branch. Missing scaffold may be seeded. Damaged or incomplete governance must be surfaced and routed to repair. No prompt may synthesize a plan, audit, implementation, or seal from assumptions.

## Feature Inventory Touches

Empty. Governance prompt and tooling enforcement only; no user-touchable product feature surface.
`feature_inventory_touches`: `[]`.

## Phase 1: Governance health checker

### Affected Files

- `qor/scripts/governance_health.py` - NEW. Reusable checker for required governance artifacts.
- `tests/test_governance_health.py` - NEW. Behavioral tests for missing, damaged, incomplete, and healthy states.
- `qor/seed.py` - AMENDED. Expose the health-checker scaffold-owned registry so the seed list and the checker's required-artifact list cannot drift. Phase 109 does NOT absorb the Governance Index scaffold (see Locked Decisions).
- `qor/references/doctrine-prompt-resilience.md` - AMENDED. Define `Governance Artifact Health`, `Ungoverned Path Forward`, and the missing/damaged/incomplete decision contract.
- `qor/references/skill-recovery-pattern.md` - AMENDED. Add canonical preflight snippets for interactive and autonomous skills.

### Changes

Add `qor.scripts.governance_health` with a pure API:

```python
class ArtifactStatus(str, Enum):
    OK = "ok"
    UNINITIALIZED = "uninitialized"
    MISSING = "missing"
    DAMAGED = "damaged"
    INCOMPLETE = "incomplete"

@dataclass(frozen=True)
class ArtifactFinding:
    path: str
    status: ArtifactStatus
    reason: str
    legal_next: str

def check_governance_health(base: Path, *, required: Iterable[str] | None = None) -> list[ArtifactFinding]:
    ...
```

Initial required artifacts:

- `docs/META_LEDGER.md`
- `docs/CONCEPT.md`
- `docs/ARCHITECTURE_PLAN.md`
- `docs/SYSTEM_STATE.md`
- `docs/SHADOW_GENOME.md`
- `docs/BACKLOG.md`
- `docs/FEATURE_INDEX.md`

`docs/GOVERNANCE_INDEX.md` is explicitly OUT of scope for this phase (see Locked Decisions); the checker registry is extensible so a future Governance Index phase appends it without touching call sites.

Status semantics:

- `UNINITIALIZED`: no ledger and no project DNA. Legal next: `/qor-bootstrap` or `qor-logic seed` depending on skill mode.
- `MISSING`: workspace is initialized but a required artifact is absent. Legal next: `qor-logic seed` only for scaffold-owned files; otherwise route to `/qor-remediate`.
- `DAMAGED`: artifact exists but fails structural validation, hash verification, JSON/Markdown parse, or ledger-chain verification. Legal next: `/qor-remediate`; no seed or bootstrap overwrite.
- `INCOMPLETE`: artifact exists but is a placeholder, has unresolved TODO markers in required sections, lacks required headings, or omits required index rows. Legal next: complete governance content before continuing.
- `OK`: artifact passes the checks required for the invoking skill.

### Unit Tests

- `tests/test_governance_health.py::test_uninitialized_workspace_returns_bootstrap_next` - empty temp repo returns `UNINITIALIZED` with `/qor-bootstrap` as legal next.
- `tests/test_governance_health.py::test_missing_required_artifact_in_initialized_workspace_blocks` - ledger present plus missing `ARCHITECTURE_PLAN.md` returns `MISSING`, not `UNINITIALIZED`.
- `tests/test_governance_health.py::test_damaged_ledger_blocks_seed_repair` - malformed or hash-invalid ledger returns `DAMAGED` and legal next `/qor-remediate`.
- `tests/test_governance_health.py::test_placeholder_artifact_is_incomplete` - TODO-only seeded `CONCEPT.md` or `ARCHITECTURE_PLAN.md` returns `INCOMPLETE`.
- `tests/test_governance_health.py::test_healthy_seeded_and_completed_workspace_returns_ok` - completed synthetic governance set returns all `OK`.

## Phase 2: Prompt enforcement

### Affected Files

- `qor/skills/**/*.md` - AMENDED. Add governance-health preflight language to every source skill that reads, writes, or routes based on governance artifacts.
- `qor/dist/variants/{claude,codex,kilo-code}/skills/**/*.md` - REGENERATED. Generated variants match source skill behavior.
- `tests/test_prompt_resilience_lint.py` - AMENDED. Enforce governance-health preflight coverage.
- `tests/test_skill_prerequisite_coverage.py` - AMENDED. Inventory expands from ABORT/INTERDICTION marker checks to governance-read preflight checks.
- `tests/test_governance_prompt_health_coverage.py` - NEW. Maps every skill's governance artifact reads to a preflight marker or explicit exemption.

### Changes

Introduce two canonical prompt markers:

```markdown
<!-- qor:governance-health-preflight -->
Run `python -m qor.scripts.governance_health --required <profile>` before reading governance artifacts. If any finding is `DAMAGED` or `INCOMPLETE`, do not continue; report the finding and legal next action.
```

```markdown
<!-- qor:governance-health-exempt reason="..." -->
```

Prompt rule:

- Any source skill mentioning `docs/META_LEDGER.md`, `docs/CONCEPT.md`, `docs/ARCHITECTURE_PLAN.md`, `docs/SYSTEM_STATE.md`, `docs/BACKLOG.md`, `docs/FEATURE_INDEX.md`, `docs/GOVERNANCE_INDEX.md`, `.qor/gates/`, or `.agent/staging/` must include `qor:governance-health-preflight` unless it has a narrow exemption.
- Exemptions are allowed only for documentation-only references, examples, or the bootstrap skill's inverse guard.
- A preflight failure cannot be converted into a plan, audit, implementation, or seal by assumption. The prompt must surface the checker's `legal_next`.
- Interactive skills may ask whether to run `qor-logic seed` only for `UNINITIALIZED` or scaffold-owned `MISSING` states.
- Autonomous skills may run `qor-logic seed` automatically only for `UNINITIALIZED` or scaffold-owned `MISSING` states.
- `DAMAGED` and `INCOMPLETE` always block forward progress except for skills whose sole purpose is repair.

### Unit Tests

- `tests/test_governance_prompt_health_coverage.py::test_governance_reading_skills_have_preflight_marker` - every source skill with governance artifact reads has preflight or exemption.
- `tests/test_governance_prompt_health_coverage.py::test_exemptions_require_reason` - every exemption includes a reason string.
- `tests/test_governance_prompt_health_coverage.py::test_no_prompt_treats_damaged_as_seedable` - no source skill text says damaged governance can be fixed by seed/bootstrap.
- `tests/test_prompt_resilience_lint.py::test_damaged_and_incomplete_are_blocking_terms` - a checker that scans the doctrine and recovery-pattern files returns no violation when both `DAMAGED` and `INCOMPLETE` are defined as blocking, and returns a violation against a fixture doctrine that omits the blocking clause (invokes the checker and asserts on its returned violations, not bare substring presence).
- `tests/test_skill_prerequisite_coverage.py::test_interactive_recovery_only_mentions_seed_for_missing_scaffold` - Y/N recovery prompts do not offer seed for damaged or incomplete artifacts.

## Phase 3: Status, CI, and variant drift

### Affected Files

- `qor/skills/memory/qor-status/SKILL.md` - AMENDED. Use governance-health status instead of existence-only `UNINITIALIZED` routing.
- `qor/cli.py` - AMENDED. Expose `qor-logic governance-health` as a user-facing command delegating to `qor.scripts.governance_health` (required: DoD D-109.3 and the CI Commands list both exercise `tests/test_cli_governance_health.py`).
- `.github/workflows/ci.yml` - AMENDED if the new lint/test commands are not already covered by default pytest.
- `qor/references/doctrine-governance-enforcement.md` - AMENDED. Add the "no ungoverned path forward" enforcement note.
- `qor/references/glossary.md` - AMENDED. Add the three new terms and references.
- `docs/SYSTEM_STATE.md` - AMENDED. Record the new governance-health surface.

### Changes

`/qor-status` replaces existence-only state with the checker result:

- `UNINITIALIZED`: next `/qor-bootstrap`.
- `MISSING`: list missing artifacts and legal recovery.
- `DAMAGED`: block; next `/qor-remediate`.
- `INCOMPLETE`: block; complete named artifact sections.
- `OK`: continue existing lifecycle routing.

Add CLI support if selected:

```bash
python -m qor.scripts.governance_health --repo-root . --profile skill-entry
```

or:

```bash
qor-logic governance-health --profile skill-entry
```

The command prints one finding per line and exits:

- `0` when all required artifacts are `OK`.
- `1` for `MISSING` or `INCOMPLETE`.
- `2` for `DAMAGED`.

### Unit Tests

- `tests/test_qor_status_governance_health.py::test_status_reports_damaged_before_lifecycle_next` - damaged ledger produces repair next action, not `/qor-plan` or `/qor-implement`.
- `tests/test_qor_status_governance_health.py::test_status_reports_incomplete_seeded_artifact` - placeholder architecture plan is incomplete, not ready.
- `tests/test_cli_governance_health.py::test_cli_exit_zero_for_healthy_workspace` - healthy fixture exits 0.
- `tests/test_cli_governance_health.py::test_cli_exit_two_for_damaged_workspace` - damaged ledger exits 2.
- `tests/test_variant_drift_governance_health.py::test_generated_variants_contain_preflight_markers` - generated variants retain the source preflight markers after build.

## CI Coverage Exemptions

Pre-existing repo-wide CI jobs not relevant to this governance-prompt/tooling phase:

- `test_packaging_install` - packaging integration smoke; orthogonal to governance health.
- `gate_chain_completeness` - sealed-phase chain audit; runs on every PR regardless of phase.
- `dependency_admission_lint` - Phase 107 dependency cooling-period check; no dependency changes here.

## Definition of Done

### Deliverable D-109.1: Governance health checker

- **D1**: A single checker classifies required governance artifacts as `OK`, `UNINITIALIZED`, `MISSING`, `DAMAGED`, or `INCOMPLETE`.
- **D2**: `DAMAGED` and `INCOMPLETE` never return seed/bootstrap as legal repair.
- **D3**: Doctrine defines the statuses and the "no ungoverned path forward" invariant.
- **D4**: `tests/test_governance_health.py` passes with behavioral fixture coverage for every status.

### Deliverable D-109.2: Prompt preflight enforcement

- **D1**: Every source skill that reads or routes from governance artifacts has a governance-health preflight marker or a justified exemption.
- **D2**: Interactive and autonomous recovery text only permits seed for uninitialized or missing scaffold states.
- **D3**: Prompt resilience doctrine and recovery patterns are updated.
- **D4**: `tests/test_governance_prompt_health_coverage.py`, `tests/test_prompt_resilience_lint.py`, and `tests/test_skill_prerequisite_coverage.py` pass.

### Deliverable D-109.3: Status and generated variants

- **D1**: `/qor-status` reports health findings before lifecycle routing.
- **D2**: Generated variants match source skill preflight behavior.
- **D3**: `docs/SYSTEM_STATE.md`, glossary, and governance-enforcement doctrine document the new surface.
- **D4**: `tests/test_qor_status_governance_health.py`, `tests/test_cli_governance_health.py`, and `tests/test_variant_drift_governance_health.py` pass.

## CI Commands

- `python -m pytest tests/test_governance_health.py -q` - governance artifact classifier.
- `python -m pytest tests/test_governance_prompt_health_coverage.py -q` - prompt preflight coverage.
- `python -m pytest tests/test_prompt_resilience_lint.py tests/test_skill_prerequisite_coverage.py -q` - prompt resilience regression.
- `python -m pytest tests/test_qor_status_governance_health.py tests/test_cli_governance_health.py -q` - status and CLI behavior.
- `python -m pytest tests/test_variant_drift_governance_health.py -q` - generated variant marker preservation.
- `python -m pytest tests/ -v` - full regression.
- `python qor/scripts/check_variant_drift.py` - generated variant drift.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase109-governance-artifact-health.md` - plan-internal consistency.
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase109-governance-artifact-health.md` - Definition of Done declaration check.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` - ledger chain integrity.
