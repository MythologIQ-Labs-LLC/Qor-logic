# Plan: Corpus-growth counterweight — progressive-disclosure lint + periodic consolidation sweep

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: Ships #162's two deferred V2 directions for SG-SkillCorpusGrowth-A. **AC1**: `qor.scripts.progressive_disclosure_lint` walks `qor/skills/**/SKILL.md`, splits each into heading sections, measures inline prose (fenced code excluded), and flags any section whose prose exceeds a budget while NOT pointing to a `references/` file — an `inline-prose-extractable` candidate for progressive-disclosure extraction. **AC2**: `qor.scripts.corpus_consolidation_report` aggregates current-state corpus signals (total SKILL.md bytes, per-skill size findings, progressive-disclosure candidates) into a ranked consolidation-candidate report, wired into `/qor-process-review-cycle` as a periodic corpus-weight sweep. Both are visibility/advisory surfaces (they suggest, never auto-refactor).
- non_goals: Auto-refactoring skills or moving prose (operator-driven); git-history growth-rate analysis (deferred — avoids the live-git flake class; the report is current-state); making either a fail-closed gate (advisory; the size-budget lint at substantiate 4.6.9 remains the only corpus gate); context-fan-out measurement (separate reserved item).
- exclusions: Sections already pointing to `references/`, and sections carrying the `<!-- qor:inline-prose-ok -->` escape, are exempt from the progressive-disclosure lint.

## Open Questions

None. Thresholds + the references/ exemption bound false positives (the documented over-flag failure mode). Report is current-state only (deterministic, no live-git). The periodic mechanism is the report wired into `qor-process-review-cycle` (the existing periodic review skill), per the doctrine's own V2 proposal.

## Feature Inventory Touches

(`docs/FEATURE_INDEX.md` absent; declared for traceability. Touches `qor/scripts` + skill + tests.)

- entry_id: `n/a` · operation: `NEW` · test_path: `tests/test_progressive_disclosure_lint.py` · test_descriptor: `progressive_disclosure_lint flags an oversized inline SKILL.md section and clears one that points to references/ or carries the escape; corpus_consolidation_report ranks oversized skills + extractable sections from synthetic skills`

## Phase 1: Progressive-disclosure lint (#162 AC1) — `qor/scripts/progressive_disclosure_lint.py`

### Affected Files

- `tests/test_progressive_disclosure_lint.py` - NEW. Behavioral tests over synthetic SKILL.md text (see Unit Tests). Written first; red before the module.
- `qor/scripts/progressive_disclosure_lint.py` - NEW. Section splitter + inline-prose measure + lint + `main(argv)`.

### Changes

```python
SECTION_PROSE_BUDGET = 2200  # chars of non-code prose per heading section
_HEADING_RE = re.compile(r"^#{2,6}\s+.*$", re.MULTILINE)
_FENCED_RE = re.compile(r"```.*?```", re.DOTALL)
_REFERENCES_RE = re.compile(r"references/[\w./-]+\.md")
_ESCAPE = "qor:inline-prose-ok"

@dataclass(frozen=True)
class DisclosureFinding:
    skill: str
    section: str
    prose_chars: int

def _sections(text): ...   # (heading, body) per heading section
def _inline_prose_chars(body): ...  # len(body) with fenced blocks stripped
def scan_text(skill, text) -> list[DisclosureFinding]:
    """Flag a section whose inline prose >= SECTION_PROSE_BUDGET and which has no
    references/ pointer and no escape comment."""
def scan_skills(skills_root) -> list[DisclosureFinding]: ...
def main(argv): ...  # --skills-root qor/skills; print findings; exit 1 if any (WARN-only at callsite)
```

De-complecting: `_sections` + `_inline_prose_chars` (pure) feed `scan_text` (policy) feed `scan_skills`/`main`.

### Unit Tests

- `tests/test_progressive_disclosure_lint.py::test_oversized_inline_section_flagged` - a section with >2200 chars of prose, no references/ pointer; `scan_text` returns an `inline-prose-extractable` finding naming the section.
- `::test_section_with_references_pointer_cleared` - same oversized section but containing `see qor/references/foo.md`; no finding.
- `::test_escape_comment_clears` - oversized section with `<!-- qor:inline-prose-ok -->`; no finding.
- `::test_small_section_not_flagged` - a short section; no finding.
- `::test_fenced_code_excluded_from_prose` - a section whose bulk is a fenced code block (prose under budget once code is stripped); no finding.
- `::test_scan_skills_over_tmp_root` - a tmp `skills/<name>/SKILL.md` with one oversized section; `scan_skills` returns one finding.
- `::test_main_exit_codes` - exit 1 with a finding, 0 clean.

## Phase 2: Consolidation report + periodic wiring (#162 AC2) — `qor/scripts/corpus_consolidation_report.py`

### Affected Files

- `tests/test_progressive_disclosure_lint.py` - add the report + wiring tests.
- `qor/scripts/corpus_consolidation_report.py` - NEW. Aggregates `skill_size_budget_lint.check_skills` + `progressive_disclosure_lint.scan_skills` + total corpus bytes into a ranked `ConsolidationReport`; `main(argv)` prints it.
- `qor/skills/governance/qor-process-review-cycle/SKILL.md` - add a "Phase 4 — Corpus-weight sweep" invoking `qor-logic scripts corpus_consolidation_report --skills-root qor/skills` so the periodic review surfaces consolidation candidates.

### Changes

```python
@dataclass(frozen=True)
class ConsolidationReport:
    total_bytes: int
    oversized_skills: tuple  # from skill_size_budget_lint
    extractable_sections: tuple  # from progressive_disclosure_lint
    candidates: tuple[str, ...]  # ranked: EXCEEDED skills first, then WARN, then extractable sections

def build_report(skills_root: Path) -> ConsolidationReport: ...
def main(argv): ...  # print report; exit 0 (advisory periodic tool)
```

`candidates` ranks oversized skills (EXCEEDED before WARN) ahead of section-level extraction candidates so the periodic review has an ordered worklist. The `qor-process-review-cycle` Phase 4 runs it as the corpus counterweight to additive growth — the doctrine's "periodic consolidation cadence" proposal.

### Unit Tests

- `::test_report_ranks_oversized_skills_first` - synthetic skills root with one EXCEEDED skill + one with an extractable section; `build_report().candidates[0]` names the EXCEEDED skill.
- `::test_report_total_bytes_sums_corpus` - total_bytes equals the sum of the synthetic SKILL.md sizes.
- `::test_report_empty_when_lean` - small skills only; `candidates == ()`.
- `::test_process_review_cycle_wires_consolidation_report` - read `qor-process-review-cycle/SKILL.md`; assert it names `corpus_consolidation_report`.

## Phase 3: Doctrine

### Affected Files

- `qor/references/doctrine-shadow-genome-countermeasures.md` - SG-SkillCorpusGrowth-A: move the progressive-disclosure auto-suggest + periodic-consolidation-cadence items from "V2 reserved" to shipped (Phase 132; GH #162); note git-history growth-rate + context-fan-out remain reserved.

## Definition of Done

### Deliverable: corpus-growth counterweight

- **D1**: oversized inline SKILL.md sections are mechanically flagged as extraction candidates; a periodic consolidation sweep ranks corpus-weight worklist items in `/qor-process-review-cycle`.
- **D2**: `qor/scripts/progressive_disclosure_lint.py` + `qor/scripts/corpus_consolidation_report.py`; process-review-cycle Phase 4 wiring.
- **D3**: doctrine SG-SkillCorpusGrowth-A V2 items marked shipped; META_LEDGER seal entry; version bump; variants recompiled.
- **D4**: `tests/test_progressive_disclosure_lint.py::test_oversized_inline_section_flagged` + `::test_section_with_references_pointer_cleared` + `::test_report_ranks_oversized_skills_first` + `::test_process_review_cycle_wires_consolidation_report`.

## CI Commands

- `python -m pytest tests/test_progressive_disclosure_lint.py tests/test_skill_size_budget_lint.py -q` — new lint + report + existing size lint (no regression).
- `python -m qor.cli scripts corpus_consolidation_report --skills-root qor/skills` — produces the current corpus consolidation worklist (advisory, exit 0).
- `python -m pytest -q` — full suite green before substantiate.
