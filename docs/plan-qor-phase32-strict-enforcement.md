# Plan: Phase 32 - Strict Enforcement (install drift + D/E strict-mode)

**change_class**: feature

**doc_tier**: system

**terms_introduced**:
- term: Install Drift            | home: qor/references/doctrine-governance-enforcement.md
- term: Strict Mode              | home: qor/references/doctrine-documentation-integrity.md

**boundaries**:
- limitations:
  - Install drift check compares byte-identical SKILL.md files source vs. install-location. It does NOT verify that `agents/` or other non-SKILL artifacts (patterns, templates, glossary) were installed -- the check scope is the skill catalog, not the full doctrine set.
  - Scope-fence archive exclusion covers the known-problematic paths: `docs/plan-qor-phase*.md`, `docs/META_LEDGER.md`, `docs/SHADOW_GENOME.md`, `docs/phase*-*.md`. Phase 32 does NOT introduce a general-purpose "immutable document" tag; exclusions are path-pattern-driven.
  - Flipping `strict=True` at Step 4.7 makes D/E findings SEAL-BLOCKING. Phase 32 assumes the scope-fence tightening in Phase 2 drops findings to zero or near-zero against the live repo. If it doesn't, Phase 3 blocks indefinitely and requires a follow-up plan (allowlist mechanism, further scope tuning, or rolling back strict).
- non_goals:
  - Automatic `qorlogic install` at seal time (considered 1a in dialogue; rejected as too intrusive to operator environment). Phase 32 ships detection + operator nudge, not auto-modification.
  - CI-side install drift check. The installed-skills live on the operator's machine; CI can't meaningfully check them. Drift check runs locally.
  - Allowlist mechanism for accepted known-drift. Deferred; Phase 32 bets scope-fence is enough.
  - Strict-mode wiring outside `/qor-substantiate` Step 4.7. `/qor-audit` drift advisory stays lenient.
- exclusions:
  - Fresh-consumer `/qor-plan` Step 1b UX testing (item #5 of inventory).
  - `/qor-remediate` narrative-ingestion (item #7).
  - `qorlogic seed` tier awareness (item #12).
  - Session prune CLI (item #14).

**Target Version**: next minor bump after v0.22.0.

**Basis**: Post-Phase-31 gap inventory. Two items remained unclosed: #1 (user-scope install staleness; Phase 31 shipped source-vs-dist parity but not user-install-vs-source) and #3 (Check Surface D/E dormant in strict mode). User guidance confirms consumer-readiness priority (planning to use Qor-logic on another project soon) -- item #1 becomes urgent for consumer hygiene; item #3 closes the doctrine-drift machinery.

Pre-plan doctrine check (SG-Phase29-A countermeasure): `doc_tier: system`, empty `terms:` at authoring time -> PASS. Current lenient D/E findings against live repo per `docs/phase31-drift-triage-report.md`: ~92 Gate findings, ~63 Shadow Genome, ~50 Doctrine, et al. Phase 2 scope-fence archive exclusion is expected to drop these below 20 total; if not, Phase 3 blocks.

## Open Questions

1. **Install drift check scope**: SKILL.md catalog only (plan default) vs also verify `agents/` + reference docs + glossary? Plan assumes SKILL.md-only. Confirm before Phase 1.
2. **Install drift check invocation point**: CLI-only (`python -m qor.scripts.install_drift_check`) vs also wired into `/qor-plan` Step 0 as a pre-phase nudge? Plan assumes both. Confirm before Phase 1.
3. **Phase 3 rollback policy**: if strict-mode wiring produces legitimate seal-blocks on the first phase seal after Phase 32, do we (a) expand Phase 2 scope-fence tightening and re-flip, (b) add an emergency kill-switch env var to revert to lenient, or (c) accept the block and address case-by-case? Plan assumes (a); (b) requires deferring to Phase 33.
4. **Archive exclusion path list**: the four patterns named in Boundaries are based on current repo state. If future plan files land at non-matching paths (e.g., `docs/plans/phase-X/plan.md`), the exclusion misses them. Plan assumes we hardcode the current pattern set; generalization deferred.

## Phase 1: Install drift check (item #1 closure)

Detect when the operator's local skill install lags the repo source. Non-blocking; surface via CLI and pre-phase nudge.

### Affected Files

- `tests/test_install_drift_check.py` - NEW; covers source-present-but-install-missing, install-present-but-stale (SHA256 mismatch), install-matches (no drift). **Functional** tests for `check()` behavior.
- `tests/test_install_drift_wiring.py` - NEW; **structural** tests asserting the Phase 1 SKILL/doctrine/glossary edits landed (pattern mirrors Phase 30's `test_session_rotation_glossary_entry_exists.py`).
- `qor/scripts/install_drift_check.py` - NEW; public API `check(host: str, scope: str) -> list[str]` returning drift descriptions (empty if clean). CLI entry point via `__main__`.
- `qor/skills/sdlc/qor-plan/SKILL.md` - MODIFY; Step 0.2 added (between gate check and phase-branch creation): invoke install drift check; WARN if drift detected. Non-blocking.
- `qor/references/doctrine-governance-enforcement.md` - MODIFY; add §8 Install Currency describing the drift-check contract + invocation sites.
- `qor/references/glossary.md` - MODIFY; add `Install Drift` entry with `home: doctrine-governance-enforcement.md` and `referenced_by: [qor/scripts/install_drift_check.py, qor/skills/sdlc/qor-plan/SKILL.md]`.

### Changes

**`qor/scripts/install_drift_check.py`**:

```python
def check(host: str = "claude", scope: str = "repo") -> list[str]:
    """Compare installed SKILL.md files against qor/skills/**/SKILL.md source.

    Uses qor.hosts.resolve(host, scope) to locate the install's skills_dir.
    For each source SKILL.md, check if installed counterpart exists and
    SHA256 matches. Returns list of drift descriptions (missing file OR
    content mismatch). Empty list = clean.
    """
```

Public API is narrow (one function + CLI); no state; easy to unit test with tmp_path + mocked hosts.resolve.

**`/qor-plan` SKILL.md Step 0.2**:

```bash
python -m qor.scripts.install_drift_check --host claude --scope repo || \
  echo "WARNING: Local skill install differs from repo source. Consider: qorlogic install --host claude --scope repo"
```

Explicitly non-blocking (`|| echo ...`). If the operator has never installed skills locally, the check reports that and prompts; if they have and are current, it stays silent.

**Doctrine §8 Install Currency** (addition to `doctrine-governance-enforcement.md`):

Describes: the drift-check contract; when to run (pre-phase + ad-hoc); what to do on drift (run `qorlogic install`); why (prevent governance drift between user's running skills and the planned authority). Links to `install_drift_check.py` and the `/qor-plan` Step 0.2 invocation.

### Unit Tests

- `tests/test_install_drift_check.py`:
  - `test_clean_install_returns_empty` - source and install byte-identical -> `check()` returns `[]`.
  - `test_missing_install_file_flagged` - source has SKILL.md, install doesn't -> drift entry names the missing path.
  - `test_stale_install_file_flagged` - source and install differ by one byte -> drift entry names the path + "SHA mismatch".
  - `test_host_not_supported_raises` - unsupported host name -> `ValueError`.
  - `test_scope_repo_looks_at_project_dir` - scope=repo -> check examines `.claude/skills/` (resolved by `hosts.resolve`).
  - `test_scope_global_looks_at_home_dir` - scope=global -> check examines `~/.claude/skills/`.
- `tests/test_install_drift_wiring.py` (Rule 4 / structural):
  - `test_plan_skill_has_install_drift_step_0_2` - parse `/qor-plan` SKILL.md; assert Step 0.2 section present and body contains `install_drift_check` invocation.
  - `test_governance_enforcement_doctrine_has_install_currency_section` - parse `doctrine-governance-enforcement.md`; assert `## 8.` or `## Install Currency` header present and body > 80 chars (non-trivial content).
  - `test_install_drift_glossary_entry_exists` - parse glossary via `doc_integrity.parse_glossary`; assert `Install Drift` entry with `home: qor/references/doctrine-governance-enforcement.md` and non-empty `referenced_by:` listing both `qor/scripts/install_drift_check.py` and `qor/skills/sdlc/qor-plan/SKILL.md`.

## Phase 2: Scope-fence archive exclusion (item #3 preamble)

Extend `doc_integrity_strict._excluded_by_scope_fence` with archive-path exclusions so lenient D/E findings drop to a viable level for strict-mode flip.

### Affected Files

- `tests/test_archive_path_exclusion.py` - NEW; parameterized over the four archive-path patterns.
- `qor/scripts/doc_integrity_strict.py` - MODIFY; extend `_excluded_by_scope_fence` with archive-pattern exclusions.
- `qor/references/doctrine-documentation-integrity.md` - MODIFY; §6 Check-surface extensions gains an archive-path exclusion rule.
- `docs/phase32-drift-triage-followup.md` - NEW; post-tuning lenient run captured as artifact; decision on strict-readiness documented.

### Changes

**`_excluded_by_scope_fence` addition**:

```python
# Archive-path exclusion (Phase 32 wiring): historical plans, ledger,
# narrative shadow genome, and phase-era snapshot docs are immutable
# and legitimately reference core terms without being adoptable consumers.
import re
_ARCHIVE_PATTERNS = (
    re.compile(r"^docs/plan-qor-phase\d+"),
    re.compile(r"^docs/META_LEDGER\.md$"),
    re.compile(r"^docs/SHADOW_GENOME\.md$"),
    re.compile(r"^docs/phase\d+[a-z0-9-]*\.md$"),  # docs/phase10-findings.md etc
)
if any(p.match(rel) for p in _ARCHIVE_PATTERNS):
    return True
```

Applied after existing exclusions.

**Doctrine §6 update**: list the archive patterns explicitly; note that excluding these is safe because they are frozen historical records, not candidates for `referenced_by:` adoption.

**`docs/phase32-drift-triage-followup.md`**: produced during Phase 2 execution. Re-runs `python -m qor.scripts.doc_integrity_drift_report` against the live repo post-archive-exclusion. Captures: the new finding counts by term, decision on whether strict-mode is viable (Phase 3 go/no-go), and the residual list (if any). Not the plan file itself modifying; this is a separate artifact declared up-front per SG-Phase31-B countermeasure.

### Unit Tests

- `tests/test_archive_path_exclusion.py`:
  - `test_plan_file_excluded` - term used in `docs/plan-qor-phase28-documentation-integrity.md` -> NOT flagged.
  - `test_meta_ledger_excluded` - term used in `docs/META_LEDGER.md` -> NOT flagged.
  - `test_shadow_genome_excluded` - term used in `docs/SHADOW_GENOME.md` -> NOT flagged.
  - `test_phase_snapshot_excluded` - term used in `docs/phase10-findings.md` -> NOT flagged.
  - `test_non_archive_doc_still_flagged` - term used in `docs/architecture.md` NOT in referenced_by AND not a home-dir-peer -> still flagged.
  - `test_archive_pattern_doesnt_overreach` - `docs/plan-qor-phase-notes.md` (mis-named hypothetical) flagged if it doesn't strictly match `plan-qor-phase\d+` pattern. Guards against overly-greedy exclusion.

## Phase 3: Flip `strict=True` in `/qor-substantiate` Step 4.7 (item #3 completion)

Enable strict-mode D/E at seal time. Any residual D/E finding now ABORTs substantiation.

### Affected Files

- `tests/test_substantiate_strict_mode_wired.py` - NEW; asserts Step 4.7 invokes `run_all_checks_from_plan(..., strict=True)` AND asserts the composite function actually routes to strict-mode checks when called that way.
- `tests/test_strict_mode_wiring.py` - NEW; **structural** tests asserting the Phase 3 glossary/doctrine edits landed (pattern mirrors Phase 30's wiring tests).
- `qor/skills/governance/qor-substantiate/SKILL.md` - MODIFY; Step 4.7 Python block gains `strict=True` kwarg on the `run_all_checks_from_plan` call.
- `qor/references/doctrine-documentation-integrity.md` - MODIFY; §3 Check surface gains "Strict mode is live at `/qor-substantiate` Step 4.7 as of Phase 32" + §6 strict-mode section revises the deferred-wiring language to match the live state.

### Changes

**`/qor-substantiate` Step 4.7 Python block**:

Change:

```python
doc_integrity.run_all_checks_from_plan(plan_artifact, repo_root=".")
```

To:

```python
# Phase 32 wiring: strict=True enables Check Surface D + E hard-block.
# Requires clean lenient findings per Phase 2 scope-fence tightening.
doc_integrity.run_all_checks_from_plan(plan_artifact, repo_root=".", strict=True)
```

**Doctrine updates**: documentation-integrity §3 promotes D and E from "optional strict mode" to "live at substantiate Step 4.7." §6 updates the "Strict-mode wiring into /qor-substantiate Step 4.7 is deferred..." sentence to describe the live state.

**Add `Strict Mode` glossary entry**: per `terms_introduced:` at plan top-matter. home = doctrine-documentation-integrity.md; referenced_by = doctrine-documentation-integrity.md, qor/scripts/doc_integrity.py, qor/scripts/doc_integrity_strict.py, qor/skills/governance/qor-substantiate/SKILL.md.

### Unit Tests

- `tests/test_substantiate_strict_mode_wired.py`:
  - `test_step_4_7_passes_strict_true` - parse `/qor-substantiate` SKILL.md Step 4.7 block; assert `strict=True` kwarg present on `run_all_checks_from_plan` call.
  - `test_composite_routes_strict_to_strict_module` - unit test for `run_all_checks_from_plan(..., strict=True)`: mock a repo where Check Surface D would flag; assert `ValueError` raised (NOT a lenient return).
  - `test_composite_lenient_still_default` - without `strict=True`, the composite does NOT invoke strict checks (regression guard for existing callers).
- `tests/test_strict_mode_wiring.py` (Rule 4 / structural):
  - `test_strict_mode_glossary_entry_exists` - parse glossary; assert `Strict Mode` entry with `home: qor/references/doctrine-documentation-integrity.md` and non-empty `referenced_by:` listing `qor/scripts/doc_integrity.py`, `qor/scripts/doc_integrity_strict.py`, and `qor/skills/governance/qor-substantiate/SKILL.md`.
  - `test_doc_integrity_doctrine_declares_strict_live` - parse `doctrine-documentation-integrity.md`; assert either §3 or §6 body contains the literal phrase "Strict mode is live at `/qor-substantiate` Step 4.7" (or equivalent; allow flexible match).

## Self-Dogfood

Per SG-Phase28-A + SG-Phase29-A + SG-Phase30-B + SG-Phase31-A + SG-Phase31-B:

- **Pre-plan doctrine check**: ran at `doc_tier: system`, `terms: []`, `plan_slug: phase32-strict-enforcement` -> PASS clean.
- **`doc_tier` declaration**: `system` at top-matter. Phase 30 delivered the four required docs; no new authoring in Phase 32.
- **`terms_introduced:` populated**: 2 terms, each assigned to a concrete phase (Install Drift in Phase 1, Strict Mode in Phase 3). No metadata-only declarations (SG-Phase30-B countermeasure).
- **`boundaries:` block populated**: non-trivial entries in limitations / non_goals / exclusions.
- **Every new rule has a test** (functional + structural per Rule 4):
  - "install drift check detects source-vs-install mismatch" -> `test_install_drift_check.py` (6 functional tests).
  - "/qor-plan Step 0.2 wires install_drift_check + doctrine §8 Install Currency exists + Install Drift glossary entry with correct home/referenced_by" -> `test_install_drift_wiring.py` (3 structural tests; applies audit pass-1 Ground 1 remediation).
  - "archive paths excluded from D/E scope" -> `test_archive_path_exclusion.py` (6 tests).
  - "Step 4.7 passes strict=True and composite routes through" -> `test_substantiate_strict_mode_wired.py` (3 tests).
  - "Strict Mode glossary entry exists + doctrine declares strict live" -> `test_strict_mode_wiring.py` (2 structural tests; applies audit pass-1 Ground 1 remediation).
- **Enumeration cross-check (items)**: plan closes 2 items from post-Phase-31 inventory (#1 user-scope install, #3 D/E strict-mode). Phase 1 covers #1; Phase 2 + 3 together cover #3 (Phase 2 is preamble enabling Phase 3). Both accounted for.
- **Enumeration cross-check (terms_introduced)**: every term in top-matter resolves to one phase's Affected Files:
  - `Install Drift` -> Phase 1 (glossary + doctrine §8).
  - `Strict Mode` -> Phase 3 (glossary + doctrine §3/§6 updates).
- **Razor anticipation (SG-Phase30-A countermeasure)**: `install_drift_check.py` NEW (~80 lines, fresh module, under cap). `doc_integrity_strict.py` currently 148 lines; Phase 2 addition of archive-pattern block ~8-10 lines -> ~160 lines, well under cap.
- **No bare YAML/TOML/JSON** requiring safe-loader citation; Phase 32 touches markdown + existing Python helpers only.
- **No plan self-modification**: Phase 2 triage output lands in `docs/phase32-drift-triage-followup.md` (new artifact), NOT this plan file (SG-Phase31-B countermeasure).
- **No in-plan corrections** that contradict Affected Files upstream (SG-Phase31-A countermeasure): Affected Files is the source of truth; this Self-Dogfood section is a checklist, not a patch mechanism.
- **Documentation Currency** (Phase 31 user-surfaced contract): Phase 32 touches skills/doctrine/scripts, so Step 6.5 will fire at substantiate time. Plan schedules doc updates: doctrine §8 + glossary edits in Phase 1; doctrine §3 + §6 + glossary edits in Phase 3; no direct system-tier doc edits anticipated (nothing changes in architecture/lifecycle/operations/policies at the narrative level). Step 6.5 WARN at seal will prompt amendment if overlooked.

## CI Commands

- `python -m pytest tests/test_install_drift_check.py -v` (Phase 1).
- `python -m pytest tests/test_archive_path_exclusion.py -v` (Phase 2).
- `python -m pytest tests/test_substantiate_strict_mode_wired.py -v` (Phase 3).
- `python -m pytest tests/ 2>&1 | tail -3` (full suite regression; target `>= 622 passed` -- 15 functional + 5 structural new tests).
- `python -m qor.scripts.install_drift_check --host claude --scope repo` (Phase 1 deliverable; ad-hoc verify).
- `python -m qor.scripts.doc_integrity_drift_report > docs/phase32-drift-triage-followup.md` (Phase 2 deliverable; verifies exclusion efficacy).
- `python -c "import sys; sys.path.insert(0, 'qor/scripts'); import doc_integrity; plan = {'doc_tier':'system','terms':[...],'plan_slug':'phase32-strict-enforcement'}; doc_integrity.run_all_checks_from_plan(plan, repo_root='.', strict=True)"` (Phase 3 self-check: plan must pass strict at seal time; zero residual findings).

Each phase's tests must pass on two consecutive runs.

## Delegation

Per `qor/gates/delegation-table.md`:

- Plan complete -> `/qor-audit` (next phase).
- Phase 2 lenient re-run surfaces >5 residual findings after archive exclusion -> halt and re-open dialogue; choose between (a) further scope-fence narrowing, (b) allowlist mechanism for accepted drift, or (c) defer Phase 3 to a later plan. Do not silently ship strict-mode against a noisy baseline.
- Phase 3 Step 4.7 live-strict produces legitimate seal-blocks on Phase 32's own seal -> PAUSE and either (i) update glossary `referenced_by:` on flagged terms, (ii) expand archive exclusion, or (iii) file a Phase 33 allowlist plan and revert to lenient for this seal.
- Phase 1 install drift check reveals `qor/hosts.resolve()` doesn't cleanly return a stable install path (e.g., per-variant logic is more convoluted than expected) -> halt and invoke `/qor-research` for a host-layer survey; do not inline the research.
