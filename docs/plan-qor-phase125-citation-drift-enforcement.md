# Plan: Citation-drift enforcement — grep-evidence lint for sealed citations

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: Extends `qor.scripts.plan_grep_lint` with a citation-evidence check: within a plan's Locked-Decision / Citation-Inventory region, a sealed-infrastructure citation (a `git show <ref>:<path>` reference, a migration filename, or a `path.ext:line` file:line citation) must be paired with a grep-evidence statement (`... grep ... -> <observed text>`) somewhere in the same LD block. Scoped to LD/citation-inventory regions so plans that do not use the discipline (no `Locked Decision` / `Citation Inventory` heading) get zero findings. WARN-only at the Step 0.6 pre-audit layer (the binding VETO is the audit Infrastructure Alignment full re-walk, P2); this is the early catch (P1 enforcement).
- non_goals: Re-implementing the audit-side iter-N>1 re-walk (P2 already shipped as prose); a general "every file:line anywhere needs evidence" rule (over-flag risk per SG over-flag lesson); verifying the grep-evidence is *correct* (that the observed text actually matches the ref) — only that a paired evidence statement is present.
- exclusions: Plans with no Locked-Decision / Citation-Inventory region (the check is a no-op); the `## Affected Files` block (those are NEW/declared paths, not sealed citations).

## Open Questions

None. Trigger is LD-region-scoped to keep false positives near zero (the over-flag failure mode SG-PlanTextDrift-A / prose-lint warns against). The grep-evidence signal is the canonical `grep ... -> ...` completion from `/qor-plan` Step 2 + `doctrine-shadow-genome-countermeasures.md` SG-CitationDrift-A P1.

## Feature Inventory Touches

(`docs/FEATURE_INDEX.md` absent; declared for traceability. Touches `qor/scripts` + tests.)

- entry_id: `n/a` · operation: `MODIFIED` · test_path: `tests/test_plan_grep_lint_citation_evidence.py` · test_descriptor: `plan_grep_lint flags a sealed citation inside a Locked-Decision block that lacks a paired grep-evidence line, and emits nothing for the same citation when grep-evidence is present or when no LD region exists`

## Context

GH #152 (umbrella #147; follow-on to #56). PR #67 (v0.48.0) shipped the prose half of SG-CitationDrift-A: the `/qor-plan` Citation Inventory section, the `/qor-audit` iter-N>1 re-walk text, and the doctrine entry. AC4 (extend `plan_grep_lint` to flag sealed citations lacking grep-evidence) and AC5/AC6 (behavioral tests + the attribution-12g cross-iteration regression) never shipped — `plan_grep_lint` was last touched in Phase 55. This phase ships the enforcement lint + behavioral tests.

## Phase 1: Citation-evidence check in `qor/scripts/plan_grep_lint.py`

### Affected Files

- `tests/test_plan_grep_lint_citation_evidence.py` - NEW. Behavioral tests over synthetic plan text (see Unit Tests). Written first; red before the function exists.
- `qor/scripts/plan_grep_lint.py` - add `check_citation_evidence(text) -> list[LintWarning]`; call it from `check_plan` and merge into the returned warnings (so the existing Step 0.6 invocation surfaces it).

### Changes

```python
# A grep-evidence statement: a `grep` invocation with the `-> observed` completion.
_EVIDENCE_RE = re.compile(r"grep\b.*->", re.IGNORECASE)
# Sealed-infrastructure citation kinds (high-confidence, low false-positive):
_GIT_SHOW_RE = re.compile(r"git show\s+\S+:\S+")
_MIGRATION_RE = re.compile(r"\b\d{8,}[_-][\w-]+\.sql\b")
_FILE_LINE_RE = re.compile(r"\b[\w./-]+\.(?:py|ts|tsx|sql|rs|go|js):\d+\b")
# LD-region heading trigger (case-insensitive): the check only runs inside these.
_LD_HEADING_RE = re.compile(r"^#+.*(locked decision|citation inventory)", re.IGNORECASE | re.MULTILINE)

def _ld_blocks(text: str) -> list[tuple[int, str]]:
    """Return (start_line, block_text) for each Locked-Decision / Citation-Inventory
    region (heading -> next same-or-higher heading)."""

def check_citation_evidence(text: str) -> list[LintWarning]:
    """For each LD block, flag every sealed citation (git-show / migration /
    file:line) when the block contains NO grep-evidence statement. Empty when
    the plan has no LD region (the discipline isn't in use)."""
```

`check_plan` appends `check_citation_evidence(text)` to its warnings. De-complecting: the existing path-existence logic is untouched; the new check is a separate pure function over text. The block-level "no evidence in block" rule (not per-citation pairing) keeps it simple and matches the doctrine ("the grep-evidence statement is part of the LD body").

### Unit Tests

- `tests/test_plan_grep_lint_citation_evidence.py::test_flags_sealed_citation_without_evidence` - LD block citing `supabase/migrations/20240101_init.sql` and `git show abc123:src/x.py` with no `grep ... ->` line; `check_citation_evidence` returns a finding naming the block/citation.
- `::test_no_finding_when_evidence_present` - same LD block plus `git show abc123:src/x.py | grep -nE 'def foo' -> def foo(a, b):`; returns `[]`.
- `::test_no_finding_without_ld_region` - a normal plan body citing `qor/scripts/x.py:42` outside any Locked-Decision heading; returns `[]` (no over-flag).
- `::test_file_line_citation_in_ld_flagged` - LD block citing `qor/scripts/foo.py:120` with no evidence; flagged.
- `::test_check_plan_merges_citation_findings` - write a plan file with an evidence-less LD block; `check_plan(path, repo_root)` includes the citation finding alongside any path findings.
- `::test_attribution_12g_cross_iteration_regression` - the SG-CitationDrift-A scenario: a plan whose LD cites a sealed migration with no grep-evidence (the citation that historically survived across iterations); assert the lint flags it deterministically on the plan text (stateless — fires regardless of "iteration", which is the cross-iteration drift the audit diff-walk missed).
- `::test_main_exit_1_on_citation_finding` - `main(["--plan", p, "--repo-root", r])` returns non-zero when an evidence-less LD citation is present (WARN surface still uses exit code for the Step 0.6 `|| true`).

## Phase 2: Behavioral wiring (replace text-presence assertions)

### Affected Files

- `tests/test_plan_grep_lint_citation_evidence.py` - the behavioral tests above ARE the AC5 replacement (exit-code / finding-output assertions, not SKILL.md substring checks).
- `qor/references/doctrine-shadow-genome-countermeasures.md` - update the SG-CitationDrift-A entry: P1 now has an executable lint (`plan_grep_lint.check_citation_evidence`) at the Step 0.6 pre-audit layer, not prose-only.

### Changes

The doctrine entry's P1 line gains: "Enforced by `qor.scripts.plan_grep_lint.check_citation_evidence` (Phase 125) at `/qor-audit` Step 0.6 (WARN); the binding VETO remains the P2 iter-N>1 re-walk." No skill-text behavioral test is added (the lint tests are the behavioral coverage); the existing Step 0.6 invocation already runs `plan_grep_lint`.

## Definition of Done

### Deliverable: citation-drift enforcement lint

- **D1**: a plan's evidence-less sealed citation in an LD block is flagged at the pre-audit layer; plans not using the discipline are unaffected.
- **D2**: `check_citation_evidence` in `qor/scripts/plan_grep_lint.py`, merged into `check_plan`; sealed-citation + evidence regexes; LD-region scoping.
- **D3**: doctrine SG-CitationDrift-A P1 marked enforced (executable); META_LEDGER seal entry; version bump.
- **D4**: `tests/test_plan_grep_lint_citation_evidence.py::test_flags_sealed_citation_without_evidence` + `::test_no_finding_when_evidence_present` + `::test_no_finding_without_ld_region` + `::test_attribution_12g_cross_iteration_regression`.

## CI Commands

- `python -m pytest tests/test_plan_grep_lint_citation_evidence.py tests/test_plan_grep_lint.py -q` — new check + existing lint (no regression).
- `python -m qor.cli scripts plan_grep_lint --plan docs/plan-qor-phase125-citation-drift-enforcement.md --repo-root .` — self-applies clean (this plan has no evidence-less LD citations).
- `python -m pytest -q` — full suite green before substantiate.
