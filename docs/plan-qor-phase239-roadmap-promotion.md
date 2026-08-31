# Plan: Phase 239 — Governed Promotion of `/qor-roadmap` P1

**change_class**: feature

**doc_tier**: standard

**originating_issue**: GH #373

**design_authorities**:
- `docs/ADR_QOR_ROADMAP.md`
- `docs/adversarial-review-qor-roadmap-2026-08-27.md`
- `docs/roadmap-qor-roadmap-build-2026-08-27.md`

**prototype_evidence**:
- Phase 238 candidate commit: `31243902b02b778f6421c2d8e06f458a97526e27`
- CI run: `33125353801`
- All six Python/OS matrix lanes passed: Ubuntu and Windows on Python 3.11, 3.12, and 3.13.
- Gate-chain completeness, install smoke, provenance-attest, Ruff, publication-boundary lint, variant drift, ledger verification, committed-seal verification, and ledger base-currency passed on the prototype candidate.
- Phase 238 is evidence only. Its missing pre-implementation formal audit is not inherited or repaired retroactively.

**boundaries**:
- limitations:
  - P1 remains operator-invoked and single-writer.
  - canonical state is one append-only `.qor/roadmaps/<id>/events.jsonl` history reduced in memory.
  - frontier exposes the complete actionable set and graph-derived explanation; it does not auto-rank or auto-select work.
- non_goals:
  - no decision supersession in P1;
  - no leases, heartbeats, or concurrent canonical writers;
  - no persisted `state.json` cache;
  - no tracker projection, automatic invocation/routing, enterprise integration, model-tier routing, or implementation-task nodes.
- exclusions:
  - no production implementation path from `/qor-roadmap`;
  - no broad prompt-corpus refactor;
  - no attempt to substantiate or seal Phase 238.

## Open Questions

None. Promotion is intentionally constrained to the already-evaluated P1 contract.

## Phase 1: Pin the prototype contract before import

### Affected Files

- `docs/plan-qor-phase239-roadmap-promotion.md`
- `.qor/gates/2026-08-27T2317-239a1c/plan.json`
- `.agent/staging/AUDIT_REPORT.md`
- `.qor/gates/2026-08-27T2317-239a1c/audit.json`

### Changes

Record the exact P1 contract admitted for promotion and the exact prototype evidence commit.

The audit target is this plan, not the Phase 238 implementation branch. The audit must reject any widening beyond the file/content set enumerated below.

### Verification

- plan declares no unresolved operator questions;
- P1 exclusions match the adversarial review;
- Phase 238 is cited as evidence, not as a prior legal gate.

## Phase 2: Import the exact proven P1 implementation

### Affected Files

Promote the Phase 238 P1 content for exactly these repository surfaces.

`README.md` is the single content exception discovered by Adversarial Preflight Iteration 1: preserve the Phase 239 base file and change only the Skills badge/count from 30 to 31. Do not import the prototype's unrelated `/qor-tone` wording or EOF-format drift.

Base-motion amendment (promotion executed on post-v0.160.0 main): the numbers the prototype captured have moved with the base and are imported at their current values rather than the stale ones -- the Skills badge/count moves 31 to 32 (Phase 244 added /qor-harden after this plan was authored), and the FEATURE_INDEX entry renumbers from FX026 to FX027 (FX026 was allocated to Phase 242's procedure-evidence evaluator). No other semantic deviation from the admitted P1 contract is introduced; the promotion runs in this session's own gate directory rather than the pre-rebase 2026-08-27T2317-239a1c session.

- `README.md`
- `docs/FEATURE_INDEX.md`
- `docs/SKILL_REGISTRY.md`
- `qor/gates/SCHEMA_REGISTRY.json`
- `qor/gates/delegation-table.md`
- `qor/gates/schema/roadmap_event.schema.json`
- `qor/scripts/roadmap_cli.py`
- `qor/scripts/roadmap_model.py`
- `qor/scripts/roadmap_state.py`
- `qor/scripts/roadmap_store.py`
- `qor/scripts/roadmap_view.py`
- `qor/skills/meta/qor-help/SKILL.md`
- `qor/skills/meta/qor-roadmap/SKILL.md`
- `tests/test_roadmap_cli.py`
- `tests/test_roadmap_skill_contract.py`
- `tests/test_roadmap_state.py`
- `tests/test_roadmap_store.py`

Do not import `docs/plan-qor-phase238-roadmap-pilot.md` or any Phase 238 governance artifact.

### Changes

Import the P1 implementation represented by prototype commit `31243902b02b778f6421c2d8e06f458a97526e27`, except for the explicit README badge-only correction above, preserving the post-trim contract:

- event kinds exclude decision supersession;
- node kinds are only `fact`, `decision`, and `prerequisite`;
- state reduction rejects unsupported versions, malformed history, unknown references, duplicate identities, sequence gaps, cycles, and illegal authority use;
- fact resolution requires evidence;
- decision resolution requires exact declared authority;
- store path is confined under `.qor/roadmaps/<id>/events.jsonl`;
- interrupted atomic replacement preserves prior valid history;
- frontier remains a set with blockers/resolver/authority and graph-derived counts;
- named planning scope fails closed until all declared blockers are resolved;
- handoff requires a repository-local `ideation` or `research` predecessor and stops at `/qor-plan`;
- skill routing remains delegation-first and contains no production implementation procedure.

No new behavior is designed in this phase.

## Phase 3: Re-prove the candidate on the governed branch

### Required Tests

- `python -m pytest tests/test_roadmap_state.py tests/test_roadmap_store.py tests/test_roadmap_cli.py tests/test_roadmap_skill_contract.py -q`
- `python -m pytest -q`
- `python -m ruff check qor tests`
- `python qor/scripts/check_variant_drift.py`
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md`

Repository CI must additionally pass:

- Ubuntu Python 3.11 / 3.12 / 3.13;
- Windows Python 3.11 / 3.12 / 3.13;
- gate-chain completeness;
- install smoke;
- provenance attestation;
- publication-boundary lint.

### Fail-closed promotion rule

Any semantic difference from the admitted prototype contract, new runtime surface, new event kind, new node kind, or new dependency beyond what the audited plan declares returns to `/qor-plan` and `/qor-audit`. It is not folded into this promotion opportunistically.

## Phase 4: Substantiate the governed implementation

After Phase 239 CI is green:

1. emit the implementation gate artifact for this session;
2. run `/qor-substantiate`;
3. record the real test/CI evidence;
4. produce ledger/seal/provenance artifacts using repository-native tooling and signing material;
5. update the PR citation only after the real substantiation chain exists.

If repository-native signing material or a required provenance capability is unavailable in the active execution environment, stop before seal creation and report the missing capability. Do not fabricate HMAC, ledger, Merkle, or provenance evidence.

## CI Commands

- `python -m pytest tests/test_roadmap_state.py tests/test_roadmap_store.py tests/test_roadmap_cli.py tests/test_roadmap_skill_contract.py -q`
- `python -m pytest -q`
- `python -m ruff check qor tests`
- `python qor/scripts/check_variant_drift.py`
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md`

**ci_commands**:
- `python -m pytest tests/test_roadmap_state.py tests/test_roadmap_store.py tests/test_roadmap_cli.py tests/test_roadmap_skill_contract.py -q`
- `python -m pytest -q`
- `python -m ruff check qor tests`
- `python qor/scripts/check_variant_drift.py`
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md`

## Feature Inventory Touches

| FEATURE_INDEX entry | Operation | Test descriptor |
|---|---|---|
| FX027 `qor-logic scripts roadmap_cli` (renumbered from FX026 by base motion) | NEW | `tests/test_roadmap_cli.py::test_vertical_pilot_across_fresh_loads` proves persisted topology, frontier progression, fresh-load resume, and legal `/qor-plan` handoff. |

## Definition of Done

- **D1**: Phase 239 has a formal pre-implementation audit PASS on this promotion plan.
- **D2**: Only the admitted P1 runtime/integration surfaces are imported.
- **D3**: The imported P1 contract is behaviorally identical to the green Phase 238 prototype candidate, except for Phase 239 governance artifacts and the deliberate removal of unrelated README `/qor-tone`/EOF drift identified by Adversarial Preflight Iteration 1.
- **D4**: Full repository CI passes on the Phase 239 branch.
- **D5**: No Phase 238 seal or audit is backfilled.
- **D6**: Phase 239 substantiation is created only from real repository-native evidence.

## Implementation stop condition

Stop after the governed P1 promotion is green and substantiated. Evaluation of Roadmap against the current Qor baseline remains GH #373's next evidence task; supersession, ranking, concurrency, tracker projection, automatic routing, and enterprise consumption require separate admission.
