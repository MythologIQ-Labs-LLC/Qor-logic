# Plan: Phase 95 — Skill-corpus size-budget lint V1 (GH #92)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #92

**boundaries**:
- limitations: V1 ships a per-skill SKILL.md size-budget lint with two
  thresholds (25 KB WARN, 40 KB EXCEEDED). Walks `qor/skills/**/SKILL.md`
  and emits one finding per skill exceeding each threshold. WARN-only
  at `/qor-substantiate` Step 4.6.9 (new). The lint does NOT measure
  historical growth, does NOT track context-load weight per phase, and
  does NOT enforce a consolidation cadence — all V2 candidates. V1 also
  does NOT account for content moved to reference files (a skill whose
  prose was offloaded to `references/` is counted at its current SKILL.md
  size only).
- non_goals: a periodic consolidation cadence (the issue proposes
  extending `qor-process-review-cycle` to sweep skill weight; deferred);
  context-load measurement per phase (per-skill reference fan-out is
  not measured in V1); auto-suggest of progressive-disclosure refactor
  candidates; growth-rate analysis from git history.
- exclusions: no changes to any existing SKILL.md (V1 is purely an
  observation surface; it does NOT auto-refactor skills); no new CI
  workflow; existing Step 4.6.5/4.6.6/4.6.7/4.6.8 substantiate gates
  unchanged in order.

## Open Questions

None.

## Feature Inventory Touches

Empty. New script + skill prose + new doctrine entry + tests.
`feature_inventory_touches`: `[]`.

## Design notes

GH #92 documents a process finding: the canonical SKILL.md corpus
grew from 91 KB / 3024 lines (Phase 0) to 282 KB / 6766 lines (Phase
81) in ~6 weeks — monotonic, never contracted. The open-issue
backlog is overwhelmingly additive; nothing budgets skill size.
Phase 92's `dod_check` discipline, Phase 89/93/94's pre-audit
lints, and this session's 6-phase governance burst all add to the
corpus without paying any of it down.

V1 ships the simplest visibility surface: a per-skill size-budget
lint. Operators see a WARN when a single SKILL.md exceeds 25 KB and
an EXCEEDED finding when it exceeds 40 KB. V1 fires on the canonical
corpus immediately — `qor-audit` is at 44 KB (EXCEEDED) and
`qor-substantiate` is at 39.8 KB (WARN). That's the deliberate
dogfooding signal: the lint catches Qor-logic's own bloat the first
time it runs.

Per the cluster's V1/V2 split pattern: V2 layers historical-growth
tracking (per-phase corpus diff via git history) and the periodic
consolidation cadence (extending `qor-process-review-cycle`); V1
ships the per-skill threshold check first so operators have evidence
on adoption before the heavier infrastructure is built.

**V1 thresholds** (tunable constants in the module):

- `WARN_BYTES = 25 * 1024` (25 KB). Above this, the skill is large
  enough that operators should consider progressive-disclosure
  refactor.
- `EXCEEDED_BYTES = 40 * 1024` (40 KB). Above this, the skill is
  large enough that context-load weight begins to dominate
  invocation cost.

**V1 findings**:

- `skill-over-warn-threshold` — SKILL.md size between `WARN_BYTES`
  and `EXCEEDED_BYTES`. Operator-actionable: consider moving
  sub-pass / step prose to reference files per the GH #92
  progressive-disclosure pattern.
- `skill-over-exceeded-threshold` — SKILL.md size > `EXCEEDED_BYTES`.
  Operator-actionable: progressive-disclosure refactor is overdue.

CLI exits 0 on zero findings; exits 1 when any EXCEEDED finding is
present so V2 can convert to a hard ABORT by removing the `|| true`
at the substantiate-site.

`/qor-substantiate` Step 4.6.9 (NEW; between merge-velocity 4.6.8
and doc-integrity 4.7) invokes the lint WARN-only:

```bash
python -m qor.scripts.skill_size_budget_lint --skills-root qor/skills || true
```

New `SG-SkillCorpusGrowth-A` doctrine entry catalogs the pattern
(monotonic corpus growth; no consolidation counterweight), the
originating GH #92 measurement table, and the V1 detector.

**Self-application paradox / acknowledgement**: this very plan
adds ~120 lines of doctrine prose + ~150 LOC of script + skill
prose to the corpus. It explicitly increases the very bloat it
measures. That tension is acknowledged in the SG entry's
"Reflective note" — the V1 detector is itself part of what V2
work will eventually consolidate. V1 lands the visibility; V2 may
need to retire some of V1's prose once growth-tracking shows
which doctrine sub-sections are operative vs. archival.

## Phase 1: skill_size_budget_lint + Step 4.6.9 wiring + tests

### Affected Files

- `qor/scripts/skill_size_budget_lint.py` — NEW. The lint module.
- `qor/skills/governance/qor-substantiate/SKILL.md` — add
  `### Step 4.6.9: Skill-corpus size-budget lint (Phase 95 wiring; GH #92)`
  between Step 4.6.8 (merge-velocity) and Step 4.7 (doc-integrity).
- `qor/references/doctrine-shadow-genome-countermeasures.md` —
  `SG-SkillCorpusGrowth-A` entry.
- `tests/test_skill_size_budget_lint.py` — NEW. Behavior tests +
  canonical-corpus dogfooding anchor.
- `tests/test_skill_size_budget_substantiate_wiring.py` — NEW.
  Step 4.6.9 wiring tests.
- `docs/plan-qor-phase95-skill-corpus-budget.md` — NEW. This plan.

### Unit Tests

- `tests/test_skill_size_budget_lint.py`
  - `test_check_finds_no_findings_below_warn_threshold` — fixture
    skill at 20 KB; assert empty findings list.
  - `test_check_emits_warn_finding_for_skill_between_warn_and_exceeded`
    — fixture skill at 30 KB; assert one finding with category
    `skill-over-warn-threshold`.
  - `test_check_emits_exceeded_finding_for_skill_over_40kb` — fixture
    skill at 45 KB; assert one finding with category
    `skill-over-exceeded-threshold`.
  - `test_check_skips_non_skill_files` — fixture directory with
    `qor/skills/foo/notes.md`; assert it is not counted.
  - `test_main_cli_exits_zero_on_no_findings` — subprocess on a
    clean fixture; assert exit 0.
  - `test_main_cli_exits_one_when_any_exceeded` — subprocess on a
    fixture with at least one EXCEEDED skill; assert exit 1.
  - `test_check_canonical_corpus_includes_qor_audit_finding` —
    self-application: invoke `check_skills(qor/skills)` against the
    actual Qor-logic corpus; assert `qor-audit/SKILL.md` is in the
    findings (it is currently 44 KB → EXCEEDED). This is the
    dogfooding shipping-correctness anchor (the V1 lint must catch
    Qor-logic's own bloat the first time it runs).
  - `test_check_canonical_corpus_qor_substantiate_in_warn_range` —
    self-application: assert `qor-substantiate/SKILL.md` is in the
    findings with the WARN (not EXCEEDED) category at the time of
    Phase 95 substantiate (39.8 KB).

- `tests/test_skill_size_budget_substantiate_wiring.py`
  - `test_step_4_6_9_invokes_skill_size_budget_lint` — anchored
    positive.
  - `test_step_4_6_9_section_removed_breaks_assertion` — strip-and-
    fail.
  - `test_step_4_6_9_positioned_between_4_6_8_and_4_7` — positional
    guard.

### Changes

`qor/scripts/skill_size_budget_lint.py`:

```python
WARN_BYTES = 25 * 1024
EXCEEDED_BYTES = 40 * 1024

@dataclass(frozen=True)
class SizeFinding:
    skill_path: str
    size_bytes: int
    category: str  # 'skill-over-warn-threshold' | 'skill-over-exceeded-threshold'
    severity: str  # 'warn' in V1

def check_skills(skills_root: Path) -> list[SizeFinding]: ...

def main(argv: list[str] | None = None) -> int:
    """CLI: exits 0 on no findings or WARN-only; exits 1 when any
    EXCEEDED finding is present (V2 can remove the `|| true` wrap to
    convert to a hard ABORT)."""
```

`/qor-substantiate` Step 4.6.9 inserted between Step 4.6.8
(merge-velocity) and Step 4.7 (doc-integrity).

`SG-SkillCorpusGrowth-A` doctrine entry catalogs the pattern, the GH
#92 measurement table (91 KB → 282 KB in 6 weeks), the V1 detector,
and the reflective acknowledgement that the lint itself contributes
to the corpus it measures (V2 work will consolidate once growth-
tracking shows which sub-sections are operative).

## Definition of Done

### Deliverable: skill_size_budget_lint module

- **D1**: A pure-Python lint exists that walks `qor/skills/**/SKILL.md`
  and emits findings for skills exceeding the 25 KB WARN and 40 KB
  EXCEEDED thresholds.
- **D2**: `qor/scripts/skill_size_budget_lint.py:check_skills(skills_root) -> list[SizeFinding]`
  with a frozen `SizeFinding` dataclass. `main()` CLI exits 0 on no
  findings or WARN-only; exits 1 when any EXCEEDED finding is present.
- **D3**: Plan + ledger + SYSTEM_STATE Phase 95 entry seal the module;
  new `SG-SkillCorpusGrowth-A` doctrine entry catalogs the pattern.
- **D4**: `tests/test_skill_size_budget_lint.py` carries 8 assertions
  covering each threshold transition, non-SKILL.md exclusion, CLI exit
  codes, and TWO self-application anchors — `qor-audit` is in EXCEEDED;
  `qor-substantiate` is in WARN range. The two canonical-corpus
  assertions are the dogfooding shipping-correctness anchors: the V1
  lint must catch Qor-logic's own bloat the first time it runs.

### Deliverable: qor-substantiate Step 4.6.9 wiring

- **D1**: `/qor-substantiate` invokes the size-budget lint between
  merge-velocity check (Step 4.6.8) and doc-integrity (Step 4.7).
  WARN-only V1.
- **D2**: `qor/skills/governance/qor-substantiate/SKILL.md` gains
  `### Step 4.6.9: Skill-corpus size-budget lint (Phase 95 wiring; GH #92)`
  with the `|| true`-wrapped invocation + Phase 95 wiring paragraph.
- **D3**: Plan + ledger entries cover the SKILL.md change; doctrine
  cross-references `SG-SkillCorpusGrowth-A`.
- **D4**: `tests/test_skill_size_budget_substantiate_wiring.py`
  carries three assertions: anchored positive (Step 4.6.9 cites
  `skill_size_budget_lint` + `|| true`); strip-and-fail negative;
  positional guard (Step 4.6.9 ordered between 4.6.8 and 4.7).

### Deliverable: SG-SkillCorpusGrowth-A doctrine entry

- **D1**: The countermeasures doctrine gains an entry naming the
  corpus-growth pattern, the GH #92 measurement table, the V1
  detector, and a reflective acknowledgement that the lint itself
  contributes to corpus growth.
- **D2**: `qor/references/doctrine-shadow-genome-countermeasures.md`
  gains a `## SG-SkillCorpusGrowth-A` section with Pattern /
  Originating measurement / Countermeasure / V2 reserved /
  Reflective note / Cross-reference sub-sections.
- **D3**: Plan + ledger seal; SYSTEM_STATE Phase 95 entry
  references.
- **D4.d**: Waiver. Doctrine entries are operator-readable prose; their behavior is the discipline they describe, which is exercised by the `skill_size_budget_lint` tests above. **Follow-up phase**: reserved for a future doctrine-integrity sweep phase that addresses the corpus-bloat tension this very lint identifies.

## CI Coverage Exemptions

None.

## CI Commands

- `python -m pytest tests/test_skill_size_budget_lint.py -q` — behavior tests for the lint module.
- `python -m pytest tests/test_skill_size_budget_substantiate_wiring.py -q` — Step 4.6.9 wiring tests.
- `python -m pytest tests/ -v` — full regression.
- `python qor/scripts/check_variant_drift.py` — ci.yml.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` — ci.yml.
- `python -m pytest tests/test_packaging_install.py -v -m integration` — install-smoke.
- `python -m qor.reliability.gate_chain_completeness --phase-min 52` — gate-chain.
- `python qor/scripts/pr_citation_lint.py` — pr-lint.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase95-skill-corpus-budget.md` — plan-internal.
- `python -m qor.scripts.ci_coverage_lint --plan docs/plan-qor-phase95-skill-corpus-budget.md --workflows-dir .github/workflows` — Phase 89 ci-coverage.
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase95-skill-corpus-budget.md` — Phase 92 DoD check.
