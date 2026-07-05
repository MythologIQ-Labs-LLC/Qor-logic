# Plan: Phase 96 — Recon Reachability Probe V1 (GH #108)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #108

**boundaries**:
- limitations: V1 ships a per-finding reachability probe with five checks
  (importability, test collection, caller graph, packaging, interface
  match). The probe walks claim-like inputs (file:symbol pairs and
  module paths) and emits one finding per failing check. WARN-only at
  `/qor-deep-audit-recon` Phase 3 Round 0 (NEW). The probe does NOT
  block any grade in V1 — it surfaces evidence so the operator (and
  the Phase 99 V2 enforcement layer) can decide. V1 also does NOT
  attempt to reach Rust / TypeScript / JS surfaces; the probe is
  Python-only in V1 (multi-language support deferred to V2).
- non_goals: blocking VETO behavior in `/qor-audit` (Phase 99 V2 work);
  multi-language probe (Rust/TS/JS deferred); auto-rewriting of recon
  briefs to apply the downgrade (V1 emits findings; the operator or
  subagent updates `RESEARCH_BRIEF.md` based on them); caching of probe
  results across recon runs (each invocation re-probes).
- exclusions: no changes to `qor-audit` SKILL.md (Phase 99 surface);
  no changes to `qor-deep-audit` SKILL.md (the parent bundle stays
  abstract; recon-half wiring lives in `qor-deep-audit-recon`); no
  changes to existing Step 0.6 audit lints (V1 is a recon-side probe,
  not a pre-audit lint); existing Step 4.6.5/4.6.6/4.6.7/4.6.8/4.6.9
  substantiate gates unchanged in order.

## Open Questions

None. The Entry #6 fragment decision was explicitly deferred to Phase 98
per the cluster meta-memo; not in Phase 96 scope.

## Feature Inventory Touches

Empty. New script + skill prose + new doctrine entry + tests.
`feature_inventory_touches`: `[]`.

## Design notes

GH #108 (filed by a sibling consumer workspace 2026-05-23) documents a governance-level
process finding: `/qor-deep-audit-recon`'s Phase 1-3 vectors accept
**grep-shaped evidence** (file exists, symbol defined, command
registered, claim string present) as sufficient proof to grade a code
surface HIGH severity. The recon never validates the runtime contract:
importability, command-registration → handler reachability, packaging
in the production bundle, test inclusion at collection time, or
caller/callee interface match.

The consequence is **zombie code** — live command registrations +
production-style invocations pointing at a layer whose runtime is
broken — grades the same as production code. Downstream remediation
cycles (`/qor-plan`, `/qor-audit`, `/qor-implement`) inherit the
misgrading; the gap surfaces only at implementation time, after
substantial cycle cost.

a sibling consumer workspace's Phase 371 (persona IPC envelope) is the originating
recurrence: recon graded `DPF-LIE-01` HIGH purely on grep evidence
(`DEFAULT_IPC_ENCRYPTION_SCHEME = "AES-256-GCM"` declared; schema fields
present; zero cipher path), then implementation surfaced runtime
import failures, missing modules, syntax errors in tests, and zero
non-test importers from production code paths. The recon never
imported the module, never traced the Rust→Python call path, never
checked packaging or test collection.

Per the cluster's V1/V2 split pattern: V1 is recon-side, contained to
`/qor-deep-audit-recon` Phase 3, does NOT touch the binding-VETO
surfaces in `/qor-audit`. V2 (Phase 99) touches `/qor-audit` Step 3
Infrastructure Alignment Pass and requires operator evidence from V1
false-positive rate before tightening. The split mirrors Phases
89/90/91/92/93/94/95.

**V1 probe checks** (all five run; any single failure emits a
finding):

| Check | Operative test |
|---|---|
| Importability | `python -c "from <module> import <symbol>"` from a clean process with the project's actual `sys.path` |
| Test collection | `pytest --collect-only <test_path>` succeeds for at least one test exercising the surface |
| Caller graph | At least one production code path (non-test, non-scratch) imports/invokes the cited surface, traced one hop |
| Packaging | The cited path is included in the production build artifact (Tauri bundle / Docker image / dist / wheel) per project-declared manifest |
| Interface match | Names/signatures cited at the call site match what the called module currently exports (parse both sides; confirm agreement) |

**V1 findings**:

- `reachability-importability-failed` — the symbol cannot be imported from a clean Python process.
- `reachability-test-collection-failed` — no test exercising the surface collects without error.
- `reachability-no-production-caller` — no non-test, non-scratch caller imports/invokes the cited surface.
- `reachability-packaging-missing` — the cited path is not present in the production build artifact (or the manifest is absent and cannot be probed).
- `reachability-interface-mismatch` — call-site name/signature does not match the called module's current export.

Each finding is informational in V1. The `--exit-on-any` flag is
available for operators who want CI-style enforcement during their
own recon runs; default behavior is exit 0 with findings on stdout.

`/qor-deep-audit-recon` Phase 3 gains a new **Round 0 — Reachability
Probe** (NEW; between checkpoint after-synthesis and existing Round 1
gap verification). The Round 0 prose adds:

> Before grading any finding HIGH or production-critical, run the
> reachability probe against the cited surface. Any single probe
> failure downgrades the finding to `reachability-gap` classification
> until end-to-end runtime evidence is added. The probe is
> WARN-only in V1; Phase 99 V2 layers blocking enforcement in
> `/qor-audit`.

The detailed five-check protocol lives in
`qor/references/recon-reachability-probe.md` (NEW; per the
progressive-disclosure doctrine; SKILL.md gains only the round
heading + one-paragraph summary + reference pointer).

New `SG-GrepShapedRunclaim-A` doctrine entry catalogs the pattern,
the sibling consumer workspace's Phase 371 originating recurrence, the V1 detector,
and a V2-reserved enforcement clause (Phase 99 will fill).

**Self-application anchor** (per cluster standard): the dogfooding
test invokes the probe against a synthetic claim that points at a
Qor-logic symbol known to be unreachable (a deliberately-broken
fixture under `tests/fixtures/reachability/`), and asserts the probe
emits all five finding categories. The forward-only structural sweep
asserts that the `/qor-deep-audit-recon` SKILL.md contains the
Round 0 heading + the reference pointer.

## Phase 1: reachability_probe + Phase 3 Round 0 wiring + tests

### Affected Files

- `qor/scripts/reachability_probe.py` — NEW. The probe module
  (~250 LOC).
- `qor/skills/meta/qor-deep-audit-recon/SKILL.md` — add
  `### Phase 3 Round 0: Reachability Probe (Phase 96 wiring; GH #108)`
  between the after-synthesis checkpoint and the existing Phase 3
  Verification prose. One-paragraph summary + reference pointer
  (no inline five-check detail per progressive-disclosure doctrine).
- `qor/references/recon-reachability-probe.md` — NEW. Detailed
  five-check protocol, examples, downgrade rule, a sibling consumer workspace's Phase 371
  originating case study.
- `qor/references/doctrine-shadow-genome-countermeasures.md` —
  `SG-GrepShapedRunclaim-A` entry after Phase 95's
  `SG-SkillCorpusGrowth-A`.
- `tests/test_reachability_probe.py` — NEW. Behavior tests + canonical
  dogfooding anchor.
- `tests/test_reachability_probe_recon_wiring.py` — NEW. Phase 3
  Round 0 wiring tests.
- `tests/fixtures/reachability/` — NEW. Deliberately-broken fixture
  symbols used by the dogfooding anchor.
- `docs/plan-qor-phase96-recon-reachability-probe.md` — NEW. This
  plan.

### Unit Tests

- `tests/test_reachability_probe.py`
  - `test_check_importability_passes_for_real_qor_symbol` —
    `qor.scripts.skill_size_budget_lint:check_skills` is importable;
    assert probe returns no `reachability-importability-failed`.
  - `test_check_importability_fails_for_unreachable_symbol` —
    fixture `tests.fixtures.reachability.broken_import` has a syntax
    error; assert probe emits `reachability-importability-failed`.
  - `test_check_test_collection_passes_when_test_exists` — fixture
    test that collects cleanly; assert no `reachability-test-collection-failed`.
  - `test_check_test_collection_fails_when_no_test_exercises_surface`
    — claim points at a symbol with zero tests; assert finding.
  - `test_check_caller_graph_finds_production_importer` — fixture
    module imported by a non-test caller; assert no
    `reachability-no-production-caller`.
  - `test_check_caller_graph_flags_test_only_caller` — fixture
    imported only by tests; assert `reachability-no-production-caller`.
  - `test_check_packaging_passes_when_path_in_manifest` — fixture
    declares the path in a manifest stub; assert no finding.
  - `test_check_packaging_flags_missing_manifest_entry` — fixture
    omits the path; assert `reachability-packaging-missing`.
  - `test_check_interface_match_passes_when_signature_agrees` — call
    site imports `foo(a, b)`; module exports `def foo(a, b)`;
    assert no `reachability-interface-mismatch`.
  - `test_check_interface_match_flags_signature_drift` — call site
    imports `foo(a, b, c)`; module exports `def foo(a, b)`; assert
    `reachability-interface-mismatch`.
  - `test_main_cli_exits_zero_on_no_findings` — subprocess on a clean
    fixture; assert exit 0.
  - `test_main_cli_exits_zero_with_findings_by_default` — subprocess
    on a fixture with findings; assert exit 0 (V1 is WARN-only).
  - `test_main_cli_exits_one_with_findings_when_exit_on_any_set` —
    subprocess with `--exit-on-any`; assert exit 1.
  - `test_probe_self_application_on_broken_fixture_emits_all_five`
    — self-application: invoke probe against the
    `tests/fixtures/reachability/zombie_claim.json` fixture; assert
    findings span all five categories. This is the dogfooding
    shipping-correctness anchor (the V1 probe must catch a
    zombie-code claim the first time it runs).

- `tests/test_reachability_probe_recon_wiring.py`
  - `test_phase_3_round_0_heading_present` — anchored positive on
    `### Phase 3 Round 0: Reachability Probe (Phase 96 wiring; GH #108)`.
  - `test_phase_3_round_0_section_removed_breaks_assertion` —
    strip-and-fail.
  - `test_phase_3_round_0_positioned_before_existing_round_1` —
    positional guard.
  - `test_recon_skill_references_progressive_disclosure_reference_file`
    — sweep asserting `qor/references/recon-reachability-probe.md`
    is cited from the SKILL.md (the round summary references the
    detailed protocol per the doctrine).

### Changes

`qor/scripts/reachability_probe.py`:

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Claim:
    """One recon-style claim: file path + symbol + optional call-site."""
    module: str
    symbol: str | None
    file_path: str
    call_site: str | None  # 'file:line' where the surface is invoked

@dataclass(frozen=True)
class ReachabilityFinding:
    claim: Claim
    category: str  # one of the five reachability-* categories
    detail: str
    severity: str  # 'warn' in V1

def check_claim(claim: Claim, repo_root: Path,
                production_paths: list[str] | None = None,
                manifest_path: Path | None = None) -> list[ReachabilityFinding]:
    """Run all five checks; return findings for failing ones."""
    ...

def main(argv: list[str] | None = None) -> int:
    """CLI: reads claims from a JSON file or stdin; exits 0 (V1 WARN-only)
    unless --exit-on-any is set, in which case exits 1 when any
    finding is present."""
    ...
```

`/qor-deep-audit-recon` Phase 3 Round 0 inserted between the
after-synthesis checkpoint and Phase 3 VERIFICATION (existing Round
1-3). The inline prose is a one-paragraph summary + reference
pointer; the five-check detail lives in
`qor/references/recon-reachability-probe.md`.

`SG-GrepShapedRunclaim-A` doctrine entry catalogs the pattern, the
a sibling consumer workspace's Phase 371 originating recurrence, the V1 detector, and a
V2-reserved enforcement clause that Phase 99 will fill.

## Definition of Done

### Deliverable: reachability_probe module

- **D1**: A pure-Python probe exists that takes claim-shaped input
  (`Claim(module, symbol, file_path, call_site)`) and returns
  `list[ReachabilityFinding]` for any of five failing checks.
- **D2**: `qor/scripts/reachability_probe.py:check_claim(claim, repo_root, production_paths, manifest_path) -> list[ReachabilityFinding]`
  with frozen `Claim` and `ReachabilityFinding` dataclasses. `main()`
  CLI exits 0 by default (V1 WARN-only); exits 1 when findings are
  present AND `--exit-on-any` is set.
- **D3**: Plan + ledger + SYSTEM_STATE Phase 96 entry seal the
  module; new `SG-GrepShapedRunclaim-A` doctrine entry catalogs the
  pattern.
- **D4**: `tests/test_reachability_probe.py` carries 14 assertions
  covering each of the five checks (pass + fail), the three CLI exit
  modes (clean, WARN-only with findings, --exit-on-any with
  findings), and ONE self-application anchor — the zombie-claim
  fixture must yield findings across all five categories. The
  canonical anchor is the dogfooding shipping-correctness test: the
  V1 probe must catch a zombie-code claim the first time it runs.

### Deliverable: qor-deep-audit-recon Phase 3 Round 0 wiring

- **D1**: `/qor-deep-audit-recon` SKILL.md gains a Round 0 heading
  between the after-synthesis checkpoint and the existing Phase 3
  VERIFICATION prose. The Round 0 inline prose is a one-paragraph
  summary + reference pointer to the detailed protocol (per
  progressive-disclosure doctrine).
- **D2**: `qor/skills/meta/qor-deep-audit-recon/SKILL.md` gains
  `### Phase 3 Round 0: Reachability Probe (Phase 96 wiring; GH #108)`
  with the summary paragraph and the explicit pointer to
  `qor/references/recon-reachability-probe.md`.
- **D3**: Plan + ledger entries cover the SKILL.md change; doctrine
  cross-references `SG-GrepShapedRunclaim-A`.
- **D4**: `tests/test_reachability_probe_recon_wiring.py` carries
  four assertions: anchored positive (Round 0 heading + reference
  pointer present); strip-and-fail negative; positional guard (Round
  0 ordered before existing Round 1); progressive-disclosure sweep
  (the SKILL.md cites the reference file).

### Deliverable: recon-reachability-probe reference file

- **D1**: A reference file exists carrying the detailed five-check
  protocol, examples, downgrade rule, and a sibling consumer workspace's Phase 371
  originating case study, so the SKILL.md can stay short per the
  progressive-disclosure doctrine.
- **D2**: `qor/references/recon-reachability-probe.md` exists with
  sections for each of the five checks + downgrade rule + case study
  + cross-references.
- **D3**: Plan + ledger seal; SYSTEM_STATE Phase 96 entry
  references.
- **D4.d**: Waiver. Reference files are operator-readable prose; the
  five-check behavior they describe is exercised by
  `tests/test_reachability_probe.py`. The wiring test
  `test_recon_skill_references_progressive_disclosure_reference_file`
  asserts the file is cited from SKILL.md, which is the structural
  guard against the file going stranded. **Follow-up phase**: Phase
  99 V2 will reference this file from `/qor-audit` Step 3 as well.

### Deliverable: SG-GrepShapedRunclaim-A doctrine entry

- **D1**: The countermeasures doctrine gains an entry naming the
  grep-shaped-runclaim pattern, the sibling consumer workspace's Phase 371 originating
  recurrence, the V1 detector, and a V2-reserved enforcement clause.
- **D2**: `qor/references/doctrine-shadow-genome-countermeasures.md`
  gains a `## SG-GrepShapedRunclaim-A` section after Phase 95's
  `SG-SkillCorpusGrowth-A`, with Pattern / Originating recurrence /
  V1 countermeasure / V2 reserved / Cross-reference sub-sections.
- **D3**: Plan + ledger seal; SYSTEM_STATE Phase 96 entry
  references.
- **D4.d**: Waiver. Doctrine entries are operator-readable prose;
  their behavior is the discipline they describe, which is exercised
  by the `reachability_probe` tests above. **Follow-up phase**:
  Phase 99 V2 will extend this entry with the audit-side enforcement
  clause.

## CI Coverage Exemptions

None.

## CI Commands

- `python -m pytest tests/test_reachability_probe.py -q` — behavior tests for the probe module.
- `python -m pytest tests/test_reachability_probe_recon_wiring.py -q` — Phase 3 Round 0 wiring tests.
- `python -m pytest tests/ -v` — full regression.
- `python qor/scripts/check_variant_drift.py` — ci.yml.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` — ci.yml.
- `python -m pytest tests/test_packaging_install.py -v -m integration` — install-smoke.
- `python -m qor.reliability.gate_chain_completeness --phase-min 52` — gate-chain.
- `python qor/scripts/pr_citation_lint.py` — pr-lint.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase96-recon-reachability-probe.md` — plan-internal.
- `python -m qor.scripts.ci_coverage_lint --plan docs/plan-qor-phase96-recon-reachability-probe.md --workflows-dir .github/workflows` — Phase 89 ci-coverage.
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase96-recon-reachability-probe.md` — Phase 92 DoD check.
- `python -m qor.scripts.skill_size_budget_lint --skills-root qor/skills` — Phase 95 skill-corpus-budget lint (WARN-only).
