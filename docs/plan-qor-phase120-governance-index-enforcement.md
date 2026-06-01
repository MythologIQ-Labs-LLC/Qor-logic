# Plan: Governance Index enforcement — wire GOVERNANCE_INDEX into /qor-substantiate + /qor-validate

**change_class**: feature

**doc_tier**: standard

**terms_introduced**:
- term: governance index enforcement
  home: qor/references/doctrine-governance-index.md

**boundaries**:
- limitations: Enforcement operates on the existing six-tier `docs/GOVERNANCE_INDEX.md` shape (tiers as glob/row tables + a single `**Last Reviewed**` marker). The Tier3->6 / Tier4->6 archival check is a forward guard: it flags a Tier 3 "Active Initiative" row that names a phase already sealed in the ledger; it does not auto-move rows or rewrite tier tables. Substantiate auto-advances `Last Reviewed` to the seal date (the only index mutation) and fail-closes on remaining drift.
- non_goals: The deferred `/qor-implement` hard-block on stale Tier 1 (#140 third V2 item — left for a follow-on); auto-archival mutation of Tier 3/4 rows; restructuring the index to per-artifact rows.
- exclusions: Non-Python / unseeded workspaces (the gate records an explicit disclosed-skip via the Phase 75 prerequisite-absent path when `docs/GOVERNANCE_INDEX.md` or the module is absent).

## Open Questions

None. Enforcement model resolved from the AC + measured blast radius (current repo has only `stale-tier1` drift, zero `unregistered`): substantiate **auto-advances** `Last Reviewed` to the seal date, then runs a **fail-closed** index check (ABORT on `unregistered` or `tier3-unarchived`), with a Phase 75 **disclosed-skip** when the artifact/module is absent. /qor-validate runs a read-only **ledger cross-check** (Last-Reviewed currency + Tier3-sealed-but-not-archived). No row auto-mutation; archival is a forward guard.

## Context

GH #149 (umbrella #147; follow-on to #140). #140 shipped the Hierarchical Governance Index as a WARN-only checker (`qor.scripts.governance_index.check_index_drift`: `stale-tier1`/`unregistered`/`missing-index`), CLI (`qor-logic governance-index`), doctrine, bootstrap scaffold, and a /qor-status indicator (PR #145, v0.79.0). The **enforcement** half was deferred to an unfiled V2: there are no governance-index references in `qor-substantiate` or `qor-validate` SKILL.md, and no Tier3->6/Tier4->6 or ledger-cross-check logic. The index is descriptive, not self-policing. This phase ships the enforcement.

## Feature Inventory Touches

(`docs/FEATURE_INDEX.md` absent; declared for traceability.)

- entry_id: `n/a` · operation: `NEW` · test_path: `tests/test_governance_index_enforcement.py` · test_descriptor: `governance_index.enforce_at_seal advances Last Reviewed to the seal date and returns ABORT-worthy findings (unregistered / tier3-unarchived) else empty`
- entry_id: `n/a` · operation: `NEW` · test_path: `tests/test_governance_index_enforcement.py` · test_descriptor: `cross_check_index_against_ledger flags a Tier3 row naming a phase already SESSION-SEALed in META_LEDGER (tier3-unarchived) and a Last-Reviewed older than the latest seal`

## Phase 1: Enforcement logic + CLI (`qor/scripts/governance_index.py`, `qor/cli.py`)

### Affected Files

- `tests/test_governance_index_enforcement.py` - NEW. Behavioral tests for advance/enforce/cross-check + disclosed-skip (see Unit Tests).
- `qor/scripts/governance_index.py` - add `advance_last_reviewed`, `enforce_at_seal`, `cross_check_index_against_ledger`, and a new `tier3-unarchived` finding kind.
- `qor/cli.py` - extend the `governance-index` subparser with `--advance-last-reviewed DATE`, `--enforce`, `--cross-check-ledger` flags routed through `_do_governance_index`.

### Changes

```python
def advance_last_reviewed(base: Path, date_str: str) -> bool:
    """Rewrite every `**Last Reviewed**: <date>` line in GOVERNANCE_INDEX.md to
    date_str. Returns True if the file changed. The only index mutation."""

def enforce_at_seal(base: Path, seal_date: str) -> list[IndexFinding]:
    """Advance Last Reviewed to seal_date, then return the residual drift that
    must fail-close the seal: `unregistered` (new doc in no tier) + the
    forward-guard `tier3-unarchived`. `stale-tier1` is cleared by the advance."""

def cross_check_index_against_ledger(base: Path) -> list[IndexFinding]:
    """Read-only validate (for /qor-validate): `stale-tier1` (Last Reviewed <
    latest sealed entry date) + `tier3-unarchived` (a Tier 3 'Active Initiative'
    row names a `phase <N>` that already has a `SESSION SEAL -- Phase <N>` entry
    in the ledger)."""
```

`tier3-unarchived` parsing: scan the Tier 3 table region for `phase\s*(\d+)` tokens; flag when the ledger contains a matching `SESSION SEAL -- Phase <N>` entry (reusing the `_latest_seal_date` parse path / ledger text). No row mutation. CLI: `_do_governance_index` branches on the new flags — `--advance-last-reviewed` calls `advance_last_reviewed`; `--enforce` runs `enforce_at_seal` (requires `--advance-last-reviewed` to supply the date; exit 1 on any residual finding = fail-closed); `--cross-check-ledger` runs the cross-check (exit 1 on findings). Absent index/module returns a disclosed-skip exit (distinct sentinel, exit 0 with a `SKIP` line) so skills can record the Phase 75 event.

De-complecting: mutation (`advance_last_reviewed`) is separated from detection (`enforce_at_seal` / `cross_check_index_against_ledger`); the existing WARN-only `check_index_drift` is untouched (the /qor-status + Phase 112 surface keeps working).

### Unit Tests

- `tests/test_governance_index_enforcement.py::test_advance_last_reviewed_rewrites_date` - build a synthetic index with `**Last Reviewed**: 2026-01-01`; call `advance_last_reviewed(base, "2026-05-30")`; assert the file now contains `2026-05-30` and not the old date, and the function returned True; calling again with the same date returns False.
- `::test_enforce_at_seal_passes_when_clean` - synthetic index whose tiers register all docs; `enforce_at_seal(base, seal_date)` returns `[]` and the index Last-Reviewed equals seal_date afterward.
- `::test_enforce_at_seal_fails_on_unregistered` - add a doc on disk that matches no tier row; `enforce_at_seal` returns a finding with kind `unregistered` naming that doc.
- `::test_enforce_at_seal_flags_tier3_unarchived` - Tier 3 row names `phase 119`; ledger has `### Entry #N: SESSION SEAL -- Phase 119 ...`; `enforce_at_seal` returns a `tier3-unarchived` finding.
- `::test_cross_check_flags_stale_last_reviewed` - Last Reviewed predates the latest sealed entry date; `cross_check_index_against_ledger` returns a `stale-tier1` finding.
- `::test_cross_check_clean_when_current_and_archived` - Last Reviewed >= latest seal, Tier 3 empty; returns `[]`.
- `::test_disclosed_skip_when_index_absent` - no GOVERNANCE_INDEX.md; `enforce_at_seal` / `cross_check_index_against_ledger` return a `missing-index` finding (callers map to disclosed-skip) rather than raising.

## Phase 2: Skill wiring + variant recompile

### Affected Files

- `tests/test_governance_index_substantiate_wiring.py` - NEW. Asserts the substantiate skill invokes the enforce gate at fail-closed semantics (see Unit Tests).
- `tests/test_governance_index_validate_wiring.py` - NEW. Asserts the validate skill invokes the ledger cross-check.
- `qor/skills/governance/qor-substantiate/SKILL.md` - add Step 4.7.5 "Governance Index enforcement" (after Step 4.7 doc-integrity), with a `## Step Prerequisites` row `module:qor.scripts.governance_index`; invocation `qor-logic governance-index --advance-last-reviewed <seal_date> --enforce --repo-root . || ABORT`, plus the Phase 75 disclosed-skip note for absent artifact.
- `qor/skills/governance/qor-validate/SKILL.md` - add a step (after Step 4 chain verify) invoking `qor-logic governance-index --cross-check-ledger --repo-root .` and folding the result into the validation report.
- `qor/dist/variants/**` - regenerated via `dist_compile`.

### Changes

The substantiate gate uses the established `|| ABORT` idiom (fail-closed, matching Step 4.6.5 secret-scanner / Step 7.7 seal-entry). The disclosed-skip path mirrors the Phase 75 prerequisite-absent contract (record SKIP + emit `gate_skipped_prerequisite_absent`) when the index is absent. The validate cross-check is read-only and contributes to the validate verdict.

### Unit Tests

- `tests/test_governance_index_substantiate_wiring.py::test_substantiate_invokes_governance_index_enforce` - read `qor-substantiate/SKILL.md`; assert it contains `governance-index` with both `--advance-last-reviewed` and `--enforce`, and that the invocation is followed by `|| ABORT` within a short window (fail-closed, not WARN). Prompt-contract test (reads SKILL.md).
- `tests/test_governance_index_substantiate_wiring.py::test_substantiate_governance_index_has_prerequisite_row` - assert the `## Step Prerequisites` table has a `module:qor.scripts.governance_index` row (the Phase 75 disclosed-skip contract is declared).
- `tests/test_governance_index_validate_wiring.py::test_validate_invokes_cross_check` - read `qor-validate/SKILL.md`; assert it contains `governance-index --cross-check-ledger`.

## Phase 3: Doctrine

### Affected Files

- `qor/references/doctrine-governance-index.md` - flip the "V2 (deferred)" block: the Tier3->6/Tier4->6 archival forward-guard + the /qor-validate ledger-cross-check are shipped (Phase 120; GH #149); note the remaining deferral (the /qor-implement hard-block on stale Tier 1).

### Changes

Replace "V2 (deferred): automated Tier 3->6 / Tier 4->6 archival at /qor-substantiate, the /qor-validate ledger-cross-check ..." with a "V2 (Phase 120; GH #149)" subsection describing the shipped enforcement (substantiate auto-advances Last Reviewed + fail-closes on unregistered/tier3-unarchived; validate runs the read-only ledger cross-check) and explicitly carrying forward only the /qor-implement stale-Tier-1 hard-block as still-deferred.

### Unit Tests

- `tests/test_governance_index_enforcement.py::test_doctrine_marks_enforcement_shipped` - assert `doctrine-governance-index.md` references `/qor-substantiate` enforcement and `/qor-validate` cross-check as shipped (contains "Phase 120" and "cross-check") while still naming the carried-forward `/qor-implement` deferral. (Functional doc-contract: reads the file, checks the co-occurrence the wiring depends on.)

## Definition of Done

### Deliverable: governance index enforcement logic

- **D1**: substantiate makes the index self-policing (advance Last Reviewed, fail-close on unregistered/tier3-unarchived); validate cross-checks the index against the ledger.
- **D2**: `advance_last_reviewed`, `enforce_at_seal`, `cross_check_index_against_ledger`, `tier3-unarchived` finding in `qor/scripts/governance_index.py`; `--advance-last-reviewed`/`--enforce`/`--cross-check-ledger` flags in `qor/cli.py`.
- **D3**: doctrine-governance-index.md flips the V2-deferred enforcement to shipped; META_LEDGER seal entry; version bump (substantiate Step 7.5).
- **D4**: `tests/test_governance_index_enforcement.py::test_enforce_at_seal_fails_on_unregistered` + `::test_enforce_at_seal_flags_tier3_unarchived` + `::test_cross_check_flags_stale_last_reviewed`.

### Deliverable: skill wiring

- **D1**: /qor-substantiate fail-closes on index drift; /qor-validate reports the cross-check.
- **D2**: Step 4.7.5 + prerequisite row in qor-substantiate SKILL.md; cross-check step in qor-validate SKILL.md; variants recompiled.
- **D3**: Phase 75 disclosed-skip declared for absent index.
- **D4**: `tests/test_governance_index_substantiate_wiring.py::test_substantiate_invokes_governance_index_enforce` + `tests/test_governance_index_validate_wiring.py::test_validate_invokes_cross_check`.

## CI Commands

- `python -m pytest tests/test_governance_index_enforcement.py tests/test_governance_index_substantiate_wiring.py tests/test_governance_index_validate_wiring.py -q` — new enforcement + wiring.
- `python -m pytest tests/test_governance_index.py tests/test_governance_index_doctrine.py tests/test_governance_index_seed.py -q` — no regression in the Phase 112 WARN-only surface.
- `python -m qor.cli governance-index --cross-check-ledger --repo-root .` — the canonical index cross-checks clean (after Last-Reviewed advance).
- `python -m pytest -q` — full suite green before substantiate.
