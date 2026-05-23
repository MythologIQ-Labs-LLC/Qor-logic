# Plan: Phase 92 — Multi-tier Definition of Done V1 (GH #86)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #86

**boundaries**:
- limitations: V1 ships only the issue's plan-emission + structural-check
  layer. A new `## Definition of Done` section template is added to
  `/qor-plan` plan prose; plans declare D1 (vision/spec), D2 (code), D3
  (governance), and D4 (empirical/runtime verification) acceptance
  criteria per deliverable. `/qor-substantiate` gains Step 4.6.7 that
  invokes `dod_check.py` to verify each D-tier row is either declared
  satisfied or carries an explicit `D4.d` waiver with rationale. V1 is
  WARN-only at substantiate (emits a `## Definition of Done` block in
  the seal report; does NOT fail the seal) — V2 will tighten to
  fail-closed once operator-evidence accumulates on adoption.
  Critically, V1 enforces only the **contract's presence** (D-tier rows
  are declared; waivers carry rationale); it does NOT verify the **truth
  of D4** (that the named tests actually ran and passed against the
  built artifact). Empirical-execution enforcement is the V2 follow-on
  and is the half that closes the issue's full lie-shipping prevention
  case.
- non_goals: D4 empirical-execution check (the test-name → pytest-output
  cross-reference that asserts the D4 named tests actually passed in
  the latest run); ledger SESSION SEAL body extension with the D-tier
  status block (the seal-report block from this phase is operator-
  reviewable WARN output, not part of the cryptographically-sealed body
  yet); `/qor-ideate` integration (V1 wires only `/qor-plan` and
  `/qor-substantiate`; ideation emission is V2). V1 also does NOT
  retrofit Definition of Done sections into prior sealed plans —
  forward-only by construction.
- exclusions: no changes to `/qor-implement` (V1 does not record D4
  test-author intent at implement time; the implement gate artifact
  shape is unchanged); no schema-level validation of the dod.json
  artifact beyond presence of required fields (V1 ships a permissive
  schema so operators can iterate on the row shape without governance
  friction); no new CI workflow; existing `## Step Prerequisites`
  Phase 75 block on `/qor-substantiate` is untouched.

## Open Questions

None.

## Feature Inventory Touches

Empty. This plan touches two new pre-substantiate scripts under
`qor/scripts/`, two governance skill bodies (`/qor-plan`,
`/qor-substantiate`), one new doctrine file, and one new test file; it
introduces no `src/` user-facing feature. `feature_inventory_touches`:
`[]`.

## Design notes

GH #86 documents a credibility class failure: multiple Qor phases can
return PASS while the artifact in question is still a placeholder or a
lie at runtime. The originating COREFORGE evidence (per the issue body)
named ~5 distinct production-credibility blockers (recovery routines
hardcoded to `true`, vendor `handle_sync` placeholders, constraint
checks returning `Ok(())`) that had previously sailed through
`PASS → seal` cycles. The root cause is that the existing gates are
*structural and ceremonial* — they verify artifact-shape and ledger
chain, not behavior. The proposed fix is to make Definition of Done
explicit and **named at four tiers**, with D4 (empirical/runtime
verification) being the missing tier today.

V1 ships the **contract layer**, not the empirical-execution layer.
This is the deliberate scope choice. Per `[[feedback-progressive-
disclosure]]` (the GH #92 corpus-bloat lesson — note: GH #92 is a
separate open issue about skill-corpus growth, distinct from this
Phase 92), V1 lands the structural-check infrastructure so operators
adopt the discipline before the heavier empirical-check machinery is
built on top. The V2 follow-on layers `dod_check.py` test-name
extraction + pytest-output cross-reference; that work has its own
design surface (test-name canonicalization; waiver-protocol shape)
and benefits from V1 operator-evidence first.

**V1 D-tier definitions** (carried verbatim into the new doctrine
file):

- **D1** — Vision / specification. The deliverable's intended behavior
  is named and constrained. Maps to existing `/qor-ideate` + `/qor-plan`
  output. Satisfied by plan-section anchored prose.
- **D2** — Code. The deliverable's source matches the spec; types,
  signatures, files declared in the plan exist at HEAD. Maps to
  existing `/qor-implement` + `/qor-audit` Step 3. Satisfied by
  Affected Files table + audit Infrastructure Alignment Pass.
- **D3** — Governance. Documentation, doctrine, ledger entries, seal-
  chain, badge-currency are consistent. Maps to existing
  `/qor-substantiate` Steps 4.5 / 4.7 / 6.5 / 7. Satisfied by existing
  integrity gates.
- **D4** — Empirical / runtime verification. The implementation has
  been executed and observed to behave as the spec promises. At
  minimum: tests written for the spec-named behavior have passed
  against the implementation, on a build that compiles. V1 enforces
  the *declaration* of D4 acceptance criteria (the test name and the
  observed behavior); V2 will verify the *truth* (the test ran and
  passed in this seal cycle).
- **D4.d** — Waiver. D4 may carry an explicit waiver when empirical
  verification is impossible in the current cycle (e.g., compile gate
  offline; external dependency unreachable). Each waiver names a
  rationale string and a follow-up phase that closes it.

**Plan-section format** (canonical V1; future phases may extend):

```markdown
## Definition of Done

Per-deliverable acceptance criteria. Each deliverable listed below
declares D1-D4 acceptance; any D4 row may instead be `D4.d` with a
rationale and follow-up phase.

### Deliverable: <name>

- **D1**: <vision/spec statement>
- **D2**: <code-level acceptance: signature, types, file location>
- **D3**: <governance acceptance: ledger entry shape, doc surfaces>
- **D4**: <test name + observed behavior assertion>
  OR
- **D4.d**: <waiver rationale; follow-up phase>
```

`dod_record.parse_plan(plan_path) -> list[DodRecord]` walks the
`## Definition of Done` section, splits on `### Deliverable:`
sub-headers, and returns a list of frozen dataclasses each carrying
`{deliverable_name, d1, d2, d3, d4 | d4_waiver_rationale,
d4_waiver_followup}`. Returns `[]` when the section is absent — V1 is
permissive (substantiate WARNs but does not abort on absent block).

`dod_check.check_plan(plan_path) -> list[CheckFinding]` invokes
`parse_plan` and emits findings for missing rows / malformed waivers.
V1 finding categories:

- `missing-dod-section` — plan has no `## Definition of Done` block.
- `deliverable-missing-tier` — deliverable lists D1 but omits one or
  more of D2/D3/D4.
- `waiver-without-rationale` — `D4.d` row is empty or contains only
  placeholder text.
- `waiver-without-followup` — `D4.d` row lacks a follow-up phase
  reference.

Each finding carries `severity = "warn"` in V1; V2 may promote
specific categories to `severity = "block"` once adoption matures.

`/qor-substantiate` Step 4.6.7 (NEW; between procedural-fidelity 4.6.6
and doc-integrity 4.7): invokes `dod_check.check_plan` against the
current phase's plan; emits a `## Definition of Done` block in the
seal report with per-deliverable D-tier status; appends each finding
to the seal report; does NOT fail the seal in V1.

New `qor/references/doctrine-definition-of-done.md` carries the V1 D-
tier definitions, the waiver protocol, and cross-references to
`doctrine-test-functionality.md`, `doctrine-procedural-fidelity.md`,
and `doctrine-governance-enforcement.md`. The doctrine file is the
operator-readable home for the contract; the new SG entry catalogs
the originating pattern.

`SG-DoDImplicit-A` doctrine entry catalogs the lie-shipping pattern,
the COREFORGE originating recurrence (the ~5 production-credibility
blockers from the issue body), and Phase 92's V1 countermeasure. V2
empirical execution is explicitly named as the unfinished half.

**Self-application of the Phase 92 plan itself**: the plan carries its
own `## Definition of Done` block declaring D1-D4 for each of the V1
deliverables (the two new scripts, the two skill insertions, the new
doctrine file). The `dod_check.check_plan` test asserts the lint
reports zero findings against this very plan — the dogfooding anchor
that mirrors Phase 89's `test_lint_self_applies_to_phase_89_plan` and
Phase 91's canonical-ledger forward-only guards.

## Phase 1: dod_record + dod_check + skill wiring + doctrine + tests

### Affected Files

- `qor/scripts/dod_record.py` — NEW. `parse_plan(plan_path)` returns a
  list of `DodRecord` dataclasses; permissive (empty list on missing
  section).
- `qor/scripts/dod_check.py` — NEW. `check_plan(plan_path)` returns a
  list of `CheckFinding` dataclasses (one per defect, V1 severity all
  `warn`). CLI prints findings; exit 0 always (WARN-only).
- `qor/skills/sdlc/qor-plan/SKILL.md` — add `## Definition of Done`
  section template to the plan-structure prose; new step in the plan
  authoring sequence that emits the section before `## CI Commands`.
- `qor/skills/governance/qor-substantiate/SKILL.md` — add new
  `### Step 4.6.7: Definition of Done check (Phase 92 wiring; GH #86)`
  between Step 4.6.6 (procedural-fidelity) and Step 4.7 (documentation
  integrity). Invokes `qor.scripts.dod_check`; WARN-only.
- `qor/references/doctrine-definition-of-done.md` — NEW. V1 D-tier
  definitions, waiver protocol, cross-references.
- `qor/references/doctrine-shadow-genome-countermeasures.md` —
  `SG-DoDImplicit-A` entry catalogs the lie-shipping pattern.
- `tests/test_dod_record.py` — NEW. Behavior tests for `parse_plan`.
- `tests/test_dod_check.py` — NEW. Behavior tests for `check_plan` +
  CLI propagation + Phase 92 self-application anchor.
- `tests/test_dod_substantiate_wiring.py` — NEW. Anchored +
  strip-and-fail wiring test for Step 4.6.7.
- `docs/plan-qor-phase92-definition-of-done.md` — NEW. This plan
  file.

### Unit Tests

- `tests/test_dod_record.py`
  - `test_parse_plan_returns_empty_when_section_absent` — fixture plan
    has no `## Definition of Done` block; `parse_plan` returns `[]`.
  - `test_parse_plan_extracts_single_deliverable_d1_d2_d3_d4` — fixture
    plan declares one `### Deliverable: foo` with D1-D4 bullets;
    assert returned record's fields populated, no waiver.
  - `test_parse_plan_extracts_multiple_deliverables` — fixture plan
    declares two deliverables; assert two records returned in document
    order.
  - `test_parse_plan_recognizes_d4_d_waiver_with_rationale_and_followup`
    — fixture has `D4.d` row with rationale and follow-up phase;
    assert record's `d4` field is None and `d4_waiver_rationale` +
    `d4_waiver_followup` populated.

- `tests/test_dod_check.py`
  - `test_check_plan_emits_missing_dod_section_finding_when_absent`
    — fixture has no DoD section; assert one finding with category
    `missing-dod-section`.
  - `test_check_plan_emits_deliverable_missing_tier_finding_for_partial_row`
    — fixture has deliverable with D1, D2, D3 but no D4 or D4.d;
    assert one finding with category `deliverable-missing-tier`
    naming the deliverable + missing tier.
  - `test_check_plan_emits_waiver_without_rationale_finding_for_empty_d4_d`
    — fixture `D4.d:` row carries only whitespace; assert one finding
    with category `waiver-without-rationale`.
  - `test_check_plan_emits_waiver_without_followup_finding_when_phase_absent`
    — fixture `D4.d` row has rationale prose but no `phase` reference;
    assert one finding with category `waiver-without-followup`.
  - `test_check_plan_emits_no_findings_for_complete_dod_block`
    — fixture declares two deliverables, both complete D1-D4; assert
    findings list is empty.
  - `test_main_cli_returns_zero_even_with_findings` — subprocess-invoke
    `python -m qor.scripts.dod_check --plan <fixture-with-gaps>`;
    assert exit code 0; assert stdout contains the finding category
    string.
  - `test_check_plan_self_applies_to_phase_92_plan` — invoke
    `check_plan` against `docs/plan-qor-phase92-definition-of-done.md`;
    assert findings list is empty. This is the deterministic
    shipping-correctness anchor (Phase 89/91 pattern).

- `tests/test_dod_substantiate_wiring.py`
  - `test_step_4_6_7_invokes_dod_check` — read
    `qor/skills/governance/qor-substantiate/SKILL.md`; isolate the
    `### Step 4.6.7` section; assert it cites
    `qor.scripts.dod_check` and `|| true` (V1 WARN-only contract,
    matching Step 0.6 convention).
  - `test_step_4_6_7_section_removed_breaks_assertion` — strip-and-
    fail negative; assert `qor.scripts.dod_check` is no longer
    present in the isolated section after removal.
  - `test_step_4_6_7_positioned_between_4_6_6_and_4_7` — assert the
    Step 4.6.7 heading appears AFTER `### Step 4.6.6` and BEFORE
    `### Step 4.7` in document order. Guards against future drift
    where a renumber breaks the substantiate sequence.

### Changes

`qor/scripts/dod_record.py` — new module structured like the existing
`qor/scripts/*_lint.py` scripts:

```python
@dataclass(frozen=True)
class DodRecord:
    deliverable: str
    d1: str | None
    d2: str | None
    d3: str | None
    d4: str | None
    d4_waiver_rationale: str | None
    d4_waiver_followup: str | None

def parse_plan(plan_path: Path) -> list[DodRecord]:
    """Walk plan's `## Definition of Done` section; split on
    `### Deliverable:` sub-headers; return one record per deliverable.
    Returns [] when the section is absent (permissive V1 contract --
    substantiate Step 4.6.7 surfaces the absence as a finding).
    """
```

`qor/scripts/dod_check.py` — new module:

```python
@dataclass(frozen=True)
class CheckFinding:
    plan: str
    category: str  # 'missing-dod-section' | 'deliverable-missing-tier' |
                   # 'waiver-without-rationale' | 'waiver-without-followup'
    deliverable: str | None
    detail: str
    severity: str  # 'warn' in V1

def check_plan(plan_path: Path) -> list[CheckFinding]: ...
def main(argv: list[str] | None = None) -> int:  # exit 0 always
    ...
```

`qor/skills/sdlc/qor-plan/SKILL.md` — add `## Definition of Done` to
the canonical plan-structure outline (current outline lists `## Phase
N`, `## CI Commands`; insert `## Definition of Done` between them).
The new section instructs the Governor to declare per-deliverable
D1-D4 rows or `D4.d` waivers per the format in design notes above.

`qor/skills/governance/qor-substantiate/SKILL.md` — insert
`### Step 4.6.7: Definition of Done check (Phase 92 wiring; GH #86)`
between Step 4.6.6 (procedural-fidelity) and Step 4.7 (documentation
integrity). Step body:

```bash
PLAN_PATH=$(python -c "from qor.scripts.governance_helpers import current_phase_plan_path; print(current_phase_plan_path())")
python -m qor.scripts.dod_check --plan "$PLAN_PATH" || true
```

`PLAN_PATH` is consumed only as an argv argument; SG-Phase47-A
countermeasure honored by construction. WARN-only contract (V1); the
findings are surfaced in the seal report's `## Definition of Done`
block but do not fail the seal. V2 will tighten specific categories
to fail-closed once adoption matures. Cross-reference:
`qor/references/doctrine-definition-of-done.md` and
`qor/references/doctrine-shadow-genome-countermeasures.md`
`SG-DoDImplicit-A`.

`qor/references/doctrine-definition-of-done.md` — NEW. Sections:

1. Purpose: name the lie-shipping failure mode and the four-tier
   contract.
2. D-tier definitions (D1 / D2 / D3 / D4) with mappings to existing
   skills/passes.
3. Waiver protocol (`D4.d` row shape; rationale + follow-up phase
   requirements).
4. V1 enforcement (presence-only; WARN at substantiate Step 4.6.7).
5. V2 reserved scope (empirical-execution check; ledger SESSION SEAL
   body extension; `/qor-ideate` integration).
6. Cross-references to `doctrine-test-functionality.md`,
   `doctrine-procedural-fidelity.md`,
   `doctrine-governance-enforcement.md` §6.

`qor/references/doctrine-shadow-genome-countermeasures.md` — append
`SG-DoDImplicit-A` paragraph:

- **Pattern**: multiple Qor phases return PASS while the artifact is
  a placeholder or lie at runtime. Existing gates verify artifact-
  shape and ledger chain; none require empirical observation of
  runtime behavior. Seal entries land with quietly-incomplete D4
  coverage; trust in "all gates ran" erodes.
- **Originating recurrence**: COREFORGE consumer session (per GH #86
  body) — ~5 production-credibility blockers (recovery routines
  hardcoded to `true`, vendor `handle_sync` placeholders, constraint
  checks returning `Ok(())`) sailed through `PASS → seal` cycles;
  detected only by separate full-repo gap audit after the fact.
- **Countermeasure** (Phase 92 wiring; GH #86): explicit multi-tier
  Definition of Done as a first-class contract. V1 ships plan-section
  emission + structural substantiate check (Step 4.6.7); WARN-only;
  enforces declaration presence + waiver rationale, NOT empirical
  truth. V2 (deferred) layers empirical-execution check that
  cross-references D4-declared test names against pytest output and
  fails seal on mismatch.
- **Cross-reference**: GH #86; doctrinally adjacent to
  `SG-HalfSealedClaim-A` (Phase 75 — structural gaps below the
  ceremonial-verification surface) and `SG-DocSurfaceUncovered-A`
  (Phase 58 — procedural-fidelity check that finds skipped doc-
  surface updates). Same root family: ceremonial gates pass while
  substantive verification is absent.

## Definition of Done

Per-deliverable acceptance criteria for the Phase 92 V1 ship.

### Deliverable: qor.scripts.dod_record module

- **D1**: A pure-Python parser exists that reads a plan file's
  `## Definition of Done` section and returns one structured record
  per `### Deliverable:` sub-header, including D1/D2/D3/D4 acceptance
  bullets or D4.d waiver fields. Returns the empty list on absent
  section.
- **D2**: `qor/scripts/dod_record.py:parse_plan(plan_path) -> list[DodRecord]`
  with a frozen `DodRecord` dataclass carrying `deliverable, d1, d2,
  d3, d4, d4_waiver_rationale, d4_waiver_followup` fields.
- **D3**: Plan Phase 92 entry under `## Phase 1: ...` lists the new
  module; SYSTEM_STATE.md gains a Phase 92 entry; META_LEDGER #245-247
  (or as numbered at substantiate time) seal the implementation.
- **D4**: `tests/test_dod_record.py` carries four assertions —
  empty-section returns []; single-deliverable record populated;
  multi-deliverable order preserved; D4.d waiver fields recognized
  with rationale + follow-up. Each test invokes `parse_plan` against
  a tmp-path fixture and asserts the returned shape.

### Deliverable: qor.scripts.dod_check module

- **D1**: A pre-substantiate check exists that emits a finding per
  missing-tier / malformed-waiver / absent-section / missing-followup
  defect against a plan's `## Definition of Done` block. V1 severity
  all `warn`; exit 0 always.
- **D2**: `qor/scripts/dod_check.py:check_plan(plan_path) -> list[CheckFinding]`
  with a frozen `CheckFinding` dataclass carrying `plan, category,
  deliverable, detail, severity` fields. `main(argv)` CLI prints
  findings and returns 0.
- **D3**: Plan Phase 92 entry under `## Phase 1: ...` lists the new
  module; SYSTEM_STATE.md Phase 92 entry covers the check; META_LEDGER
  seals.
- **D4**: `tests/test_dod_check.py` carries six assertions covering
  each finding category (missing-dod-section, deliverable-missing-tier,
  waiver-without-rationale, waiver-without-followup, no-findings on
  complete block, CLI exit 0 with findings); plus the
  `test_check_plan_self_applies_to_phase_92_plan` deterministic
  shipping-correctness anchor (this plan reports zero findings against
  its own `## Definition of Done` block).

### Deliverable: qor-substantiate Step 4.6.7 wiring

- **D1**: `/qor-substantiate` invokes `dod_check.check_plan` between
  the procedural-fidelity check (Step 4.6.6) and the documentation-
  integrity check (Step 4.7), surfacing findings as a `## Definition
  of Done` block in the seal report. WARN-only in V1.
- **D2**: `qor/skills/governance/qor-substantiate/SKILL.md` gains a
  `### Step 4.6.7: Definition of Done check (Phase 92 wiring; GH #86)`
  section with a `python -m qor.scripts.dod_check --plan "$PLAN_PATH"
  || true` invocation and a Phase 92 wiring paragraph.
- **D3**: Plan + ledger entries cover the SKILL.md change; doctrine
  cross-references `SG-DoDImplicit-A`.
- **D4**: `tests/test_dod_substantiate_wiring.py` carries three
  assertions: anchored positive (Step 4.6.7 cites `qor.scripts.dod_check`
  and `|| true`); strip-and-fail negative; positional guard (Step
  4.6.7 appears between Step 4.6.6 and Step 4.7 in document order).

### Deliverable: qor-plan Definition of Done template prose

- **D1**: `/qor-plan` plan-structure outline names `## Definition of
  Done` as a required section between `## Phase N` and `## CI Commands`,
  with a deliverable-row template documenting D1-D4 + D4.d shape.
- **D2**: `qor/skills/sdlc/qor-plan/SKILL.md` gains the new section
  template in the plan-structure prose; existing sections unchanged.
- **D3**: Plan + ledger entries cover the SKILL.md change.
- **D4.d**: Waiver. `/qor-plan` SKILL.md edits are prose-only;
  behavior verification is via the self-application anchor on
  `tests/test_dod_check.py::test_check_plan_self_applies_to_phase_92_plan`
  (this plan covers its own DoD block per the new template). A
  separate behavior test that asserts the SKILL.md template renders
  correctly is structurally identical to the strip-and-fail wiring
  test for Step 4.6.7 and is therefore covered transitively; a
  dedicated `tests/test_qor_plan_dod_template.py` is deferred to a
  later phase if drift evidence surfaces. **Follow-up phase**:
  reserved for a future Definition-of-Done v2 cycle.

### Deliverable: doctrine-definition-of-done.md

- **D1**: A new doctrine file at `qor/references/doctrine-definition-
  of-done.md` documents the four-tier contract, the waiver protocol,
  the V1 / V2 split, and cross-references to existing doctrines.
- **D2**: File created with sections (Purpose; D-tier definitions;
  Waiver protocol; V1 enforcement; V2 reserved; Cross-references).
- **D3**: Plan + ledger seal the new doctrine file; existing
  doctrine-shadow-genome-countermeasures.md gains the
  `SG-DoDImplicit-A` entry that cross-references it.
- **D4.d**: Waiver. Doctrine files are operator-readable prose; their
  "behavior" is the discipline they describe, which is exercised by
  the dod_check tests above. A direct behavior test that asserts the
  doctrine file's structure is over-engineered for V1 (would test
  markdown shape, not doctrine substance). **Follow-up phase**:
  reserved for a future doctrine-integrity sweep phase if drift
  surfaces.

## CI Coverage Exemptions

None for this phase. Phase 92's `## CI Commands` block declares the
full Qor-logic CI surface so `ci_coverage_lint` reports zero WARNs.

## CI Commands

- `python -m pytest tests/test_dod_record.py -q` — behavior tests for the parser module.
- `python -m pytest tests/test_dod_check.py -q` — behavior tests for the check module + CLI exit-0 contract + self-application anchor.
- `python -m pytest tests/test_dod_substantiate_wiring.py -q` — anchored + strip-and-fail + positional wiring tests for Step 4.6.7.
- `python -m pytest tests/ -v` — full regression suite (matches the ci.yml `test` job's `-v` form).
- `python qor/scripts/check_variant_drift.py` — ci.yml `test` job step.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` — ci.yml `test` job step.
- `python -m pytest tests/test_packaging_install.py -v -m integration` — ci.yml `install-smoke` job step.
- `python -m qor.reliability.gate_chain_completeness --phase-min 52` — ci.yml `gate-chain-completeness` job step.
- `python qor/scripts/pr_citation_lint.py` — pr-lint.yml `lint` job step.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase92-definition-of-done.md` — plan-internal text-consistency.
- `python -m qor.scripts.ci_coverage_lint --plan docs/plan-qor-phase92-definition-of-done.md --workflows-dir .github/workflows` — Phase 89 ci-coverage lint (third cross-phase application; dogfooding pattern continued).
