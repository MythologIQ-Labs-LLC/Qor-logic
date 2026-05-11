# Plan: Phase 58 - Governance capability surface

**change_class**: feature

**doc_tier**: system

**originating_remediation**: operator capability-surface planning request after GH #47-#52 triage

**terms_introduced**:
- term: governance capability surface
  home: qor/capabilities/types.py
- term: governance context packet
  home: qor/capabilities/context.py
- term: risk routing report
  home: qor/capabilities/risk.py
- term: verification request artifact
  home: qor/gates/schema/verification_request.schema.json

**boundaries**:
- limitations:
  - V1 is local-only: Python APIs, CLI output, and gate artifacts.
  - V1 describes QorLogic capabilities; it does not create a network service.
  - V1 uses existing repo artifacts as evidence and does not fetch remote documentation.
- non_goals:
  - Public interoperability claims.
  - Vendor-specific SDK clients.
  - Runtime test execution orchestration beyond existing QorLogic skills.
- exclusions:
  - No public interoperability claims.

## Open Questions

None.

## Phase 1: Capability inventory

### Affected Files

- `qor/capabilities/__init__.py` - NEW.
- `qor/capabilities/types.py` - NEW.
- `qor/capabilities/inventory.py` - NEW.
- `qor/gates/schema/capability_inventory.schema.json` - NEW.
- `tests/test_capability_inventory.py` - NEW.

### Changes

Create frozen dataclasses:

```python
@dataclass(frozen=True)
class Capability:
    id: str
    skill: str
    phase: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    risk_level: str

def build_inventory(repo_root: Path) -> tuple[Capability, ...]: ...
```

Inventory covers audit, implement, substantiate, validate, remediate, policy check, doc integrity, ledger verify, install freshness, feature inventory, filter-stage ordering, SDK alignment, documentation touches, hash integrity, and federated ledger fragments.

### Unit Tests

- `test_inventory_contains_core_lifecycle_capabilities`
- `test_inventory_contains_hash_integrity_capability`
- `test_inventory_contains_sdk_alignment_capability`
- `test_inventory_contains_federated_ledger_capability`
- `test_inventory_schema_accepts_generated_inventory`

## Phase 2: Governance context packet

### Affected Files

- `qor/capabilities/context.py` - NEW.
- `qor/gates/schema/governance_context.schema.json` - NEW.
- `tests/test_governance_context_packet.py` - NEW.

### Changes

Create:

```python
@dataclass(frozen=True)
class GovernanceContextPacket:
    target: str
    doctrines: tuple[str, ...]
    known_failure_patterns: tuple[str, ...]
    feature_inventory_rows: tuple[str, ...]
    recent_ledger_refs: tuple[str, ...]
    recommended_checks: tuple[str, ...]

def build_context_packet(repo_root: Path, target: str) -> GovernanceContextPacket: ...
```

The packet gives an agent or operator the repo-local context needed before planning or auditing: applicable doctrines, Shadow Genome anchors, feature inventory rows, recent related ledger entries, and recommended QorLogic checks.

### Unit Tests

- `test_context_packet_is_frozen`
- `test_context_packet_includes_doctrine_refs_for_governance_target`
- `test_context_packet_includes_shadow_patterns_when_present`
- `test_context_packet_schema_accepts_generated_packet`

## Phase 3: Risk routing report

### Affected Files

- `qor/capabilities/risk.py` - NEW.
- `qor/gates/schema/risk_routing.schema.json` - NEW.
- `tests/test_risk_routing_report.py` - NEW.

### Changes

Create:

```python
@dataclass(frozen=True)
class RiskRoutingReport:
    target: str
    risk_grade: str
    impacted_surfaces: tuple[str, ...]
    required_skills: tuple[str, ...]
    missing_evidence: tuple[str, ...]

def route_risk(repo_root: Path, changed_files: tuple[str, ...]) -> RiskRoutingReport: ...
```

Rules:

- changes to `qor/skills/governance/qor-substantiate` or `qor/scripts/ledger_hash.py` require hash integrity and ledger verification
- changes to `docs/META_LEDGER.md` or ledger scripts require federated ledger checks
- changes to `qor/skills/sdlc/qor-implement` require documentation lifecycle checks
- changes involving dependency declarations or SDK-facing code require SDK alignment
- changes involving filter or selection pipelines require composition-defect review

### Unit Tests

- `test_risk_routes_substantiate_changes_to_hash_integrity`
- `test_risk_routes_ledger_changes_to_federated_ledger_checks`
- `test_risk_routes_implement_skill_changes_to_documentation_lifecycle`
- `test_risk_routes_dependency_changes_to_sdk_alignment`
- `test_risk_routing_schema_accepts_report`

## Phase 4: Verification request artifact

### Affected Files

- `qor/gates/schema/verification_request.schema.json` - NEW.
- `qor/capabilities/verification_request.py` - NEW.
- `qor/cli.py` - add `capabilities` command group.
- `tests/test_verification_request_artifact.py` - NEW.
- `tests/test_cli_capabilities.py` - NEW.

### Changes

Define local artifact:

```json
{
  "target": "string",
  "required_confidence": "targeted | package | workspace | release",
  "requested_checks": ["string"],
  "context_packet": {},
  "risk_routing": {}
}
```

CLI:

```bash
qorlogic capabilities inventory
qorlogic capabilities context --target <path-or-plan>
qorlogic capabilities route-risk --changed-file <path> [--changed-file <path> ...]
qorlogic capabilities verification-request --target <path-or-plan> --confidence targeted
```

The command prints JSON to stdout by default and writes a gate artifact only when `--write-gate` is supplied.

### Unit Tests

- `test_verification_request_schema_requires_target_and_confidence`
- `test_verification_request_embeds_context_and_risk`
- `test_cli_capabilities_inventory_prints_json`
- `test_cli_capabilities_context_prints_json`
- `test_cli_capabilities_route_risk_accepts_multiple_files`
- `test_cli_capabilities_verification_request_write_gate_is_opt_in`

## CI Commands

- `python -m pytest tests/test_capability_inventory.py tests/test_governance_context_packet.py tests/test_risk_routing_report.py -v`
- `python -m pytest tests/test_verification_request_artifact.py tests/test_cli_capabilities.py -v`
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py`
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase58-governance-capability-surface.md`
