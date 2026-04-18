# Plan: Phase 31 - Operationalization (close the build-vs-deploy gap)

**change_class**: feature

**doc_tier**: system

**boundaries**:
- limitations:
  - Phase 31 does NOT flip Check Surface D to strict mode. Preview shows 352 lenient findings; scope-fence tuning in Phase 2 is expected to reduce this but strict-wiring requires a subsequent clean-triage phase.
  - Documentation Currency Check (new substantiate Step 6.5) uses a heuristic: if the phase touched any SKILL.md / doctrine / schema / script, require at least one system-tier doc to appear in the implement.json files_touched. Semantic completeness (did the doc actually reflect the change?) is not mechanized; that stays operator judgment.
  - PR citation lint inspects PR body text for literal substrings (plan path, `#<entry>`, seal hash). Semantic verification (does the cited seal hash match the current HEAD's seal?) is out of scope.
- non_goals:
  - Auto-regenerate system-tier doc content from code inspection; authoring stays human.
  - Remediate narrative-vs-structured SHADOW_GENOME gap (item 7 of post-Phase-30 inventory); separate phase.
  - Unify `docs/ARCHITECTURE_PLAN.md` vs `docs/architecture.md` (item 9); separate phase.
  - Rewrite `qorlogic seed` to be tier-aware (item 12); separate phase.
- exclusions:
  - Fresh-consumer `/qor-plan` Step 1b dialogue UX testing (item 5 of inventory); separate phase when a consumer repo is available.
  - Session prune CLI (`qorlogic session prune-old`); separate phase.

**Target Version**: next minor bump after v0.21.0 (governed by Step 7.5 of /qor-substantiate).

**Basis**: Post-Phase-30 gap inventory (`what concerns persist, what gaps remain` accounting). Seven items clustered under "operationalization": installed skills stale (#1), audit drift doesn't auto-invoke (#2), Check Surface D/E dormant (#3), session path divergence (#4), PR citation unenforced (#8), E would flag docs if strict (#11), install sync unverified (#13). Plus user-surfaced contract gap: documentation currency at substantiate time.

Pre-plan doctrine check (SG-Phase29-A countermeasure): ran at `doc_tier: system` with empty `terms:` at plan-authoring time. PASS clean. D/E lenient preview against live repo: 352 D findings (too noisy for strict; scope-fence tuning required), 15 E findings (triagable).

## Open Questions

1. **Session path unification direction**: rename `session.py::MARKER_PATH` to `.qor/session/current` (matches existing bash refs in substantiate Step 4.6 + implement Step 5.5) vs update bash refs to `.qor/current_session` (matches existing Python). Plan assumes rename MARKER_PATH (fewer call sites). Confirm before Phase 1.
2. **Documentation Currency Check severity**: at Step 6.5, if the heuristic matches but no system-tier doc was touched, should substantiate WARN (operator decides) or BLOCK (force doc update)? Plan assumes WARN for Phase 31 (shipping the check; discover false-positive rate); BLOCK upgrade deferred to a later phase. Confirm before Phase 1.
3. **Check Surface D scope-fence tuning strategy**: 352 lenient findings today. Options: (a) narrow by excluding doctrine-to-doctrine references (a doctrine mentioning another concept isn't drift); (b) narrow by excluding HOME-file directory peers; (c) add per-entry opt-out via `scope_exclude: []` in glossary frontmatter; (d) accept noise and ship strict-mode anyway with a known-findings allowlist. Plan assumes (a) + (b) combined. Confirm before Phase 2.
4. **PR citation lint CI event trigger**: `pull_request` (open + synchronize + reopen) vs `pull_request_target` (runs with base-branch perms). Plan assumes `pull_request` (safer; no privileged context). Confirm before Phase 3.

## Phase 1: Connective tissue — install sync + session path + audit auto-invoke + doc-currency check

The items that make existing machinery actually work rather than describing what should happen.

### Affected Files

- `tests/test_install_sync_with_source.py` - NEW; asserts every file in `qor/skills/**/SKILL.md` has a byte-identical counterpart in `qor/dist/variants/claude/skills/**/SKILL.md` (and the three other variants). Fails if source + variant diverge -- catches the Phase 28-30 class of dist drift at CI time.
- `tests/test_session_marker_path_unified.py` - NEW; asserts `session.MARKER_PATH.name == 'current'` AND that the substantiate/implement SKILL bash blocks reference the same path. No more `.qor/session/current` vs `.qor/current_session` divergence.
- `tests/test_audit_drift_auto_invoked.py` - NEW; asserts `/qor-audit` SKILL.md Step 4-Documentation-Drift block contains an EXPLICIT `doc_integrity.render_drift_section` call that the skill runtime executes (not just narrative text). Lint test: the skill body must carry the Python block that assigns drift output.
- `tests/test_documentation_currency_check.py` - NEW; tests the new Step 6.5 heuristic function.
- `qor/scripts/session.py` - MODIFY; rename `MARKER_PATH` target from `.qor/current_session` to `.qor/session/current` to match existing bash references. `get_or_create` / `current` / `end_session` / `rotate` all pick up the change automatically via the constant.
- `qor/scripts/doc_integrity_strict.py` - MODIFY; add `check_documentation_currency(implement_payload, repo_root) -> list[str]` function (chosen over `doc_integrity.py` to preserve the core module's 249-line Razor budget; SG-Phase30-A countermeasure applied at plan-authoring time). Returns empty list if no doc-affecting change was made OR at least one system-tier doc is in `files_touched`. Returns a warning list otherwise.
- `qor/skills/governance/qor-substantiate/SKILL.md` - MODIFY; (a) add Step 6.5 (Documentation Currency Check) between Step 6 (Sync System State) and Step 7 (Final Merkle Seal), importing from `doc_integrity_strict`; (b) Step 3 Reality Audit section gains a note pointing at 6.5 for system-tier docs.
- `qor/skills/governance/qor-audit/SKILL.md` - MODIFY; the Documentation Drift section gains an explicit Python block invoking `doc_integrity.render_drift_section` with the drift output appended to AUDIT_REPORT.md under the `<!-- qor:drift-section -->` marker.
- `qor/skills/governance/qor-audit/references/qor-audit-templates.md` - MODIFY; add the `<!-- qor:drift-section -->` marker to the template so every audit report has a canonical insertion point.
- `qor/references/doctrine-documentation-integrity.md` - MODIFY; add §5 Documentation Currency describing the Step 6.5 heuristic and the WARN semantics.

### Changes

**Path unification**. One line change: `MARKER_PATH = _workdir.root() / ".qor" / "session" / "current"` replaces `/ ".qor" / "current_session"`. No other session.py edits; all consumers use the constant. Existing `.qor/current_session` file (if present in a user's workspace) is NOT migrated automatically -- the new marker just starts fresh at next `session.get_or_create()` call. Plan top-matter should note the one-time operator action.

**Documentation Currency Check** (new Step 6.5):

```python
import sys; sys.path.insert(0, 'qor/scripts')
import doc_integrity, gate_chain

implement = gate_chain.read_phase_artifact("implement", session_id=sid)
warnings = doc_integrity.check_documentation_currency(implement, repo_root=".")
if warnings:
    # Emit to operator. Phase 31 behavior: WARN + continue.
    # Future phase may upgrade to BLOCK.
    print("WARNING: Documentation currency check raised:")
    for w in warnings: print(f"  {w}")
```

The heuristic: if `files_touched` contains any file matching `qor/skills/**/SKILL.md`, `qor/references/doctrine-*.md`, `qor/gates/schema/*.json`, or `qor/scripts/*.py`, AND none of `docs/architecture.md`, `docs/lifecycle.md`, `docs/operations.md`, `docs/policies.md` are in `files_touched`, then return a warning listing the triggering files. Else return empty.

**Audit drift auto-invoke**. Replace the current narrative Step 4 Documentation Drift section in `/qor-audit` SKILL.md with an explicit Python block:

```python
import doc_integrity, gate_chain
plan_artifact = gate_chain.read_phase_artifact("plan", session_id=sid)
drift_md = doc_integrity.render_drift_section(plan_artifact, repo_root=".")
# Insert drift_md under the <!-- qor:drift-section --> marker in AUDIT_REPORT.md.
```

Lint test asserts the skill body carries the exact invocation; prevents the prose-without-mechanism gap.

**Install-sync test**. Walk `qor/skills/**/SKILL.md`. For each, compute SHA256 of content. Locate the corresponding file under `qor/dist/variants/claude/skills/**/SKILL.md` (and codex, kilo-code -- gemini has a different structure, excluded). Compare. Any mismatch fails the test with the specific path.

### Unit Tests

- `tests/test_install_sync_with_source.py`:
  - `test_claude_variant_skill_sync` - SHA256 every SKILL.md under `qor/skills/` vs `qor/dist/variants/claude/skills/`. Fail on first mismatch naming the pair.
  - `test_codex_variant_skill_sync` - same for codex variant.
  - `test_kilo_code_variant_skill_sync` - same for kilo-code.
  - `test_gemini_variant_excluded_intentionally` - assert gemini produces TOML commands (different format); test passes trivially but documents the scope fence.
- `tests/test_session_marker_path_unified.py`:
  - `test_marker_path_is_session_current` - `session.MARKER_PATH.name == 'current'` AND parent is `session`.
  - `test_substantiate_bash_refs_match_marker` - grep substantiate SKILL.md for `.qor/session/current`; assert at least one occurrence and no `.qor/current_session`.
  - `test_implement_bash_refs_match_marker` - same for implement SKILL.md.
- `tests/test_audit_drift_auto_invoked.py`:
  - `test_audit_skill_has_drift_invocation_block` - parse `/qor-audit` SKILL.md; assert presence of a Python code fence containing `doc_integrity.render_drift_section`.
  - `test_audit_template_has_drift_marker` - audit-templates.md contains `<!-- qor:drift-section -->` as an insertion point.
- `tests/test_documentation_currency_check.py`:
  - `test_currency_passes_when_no_doc_affecting_change` - files_touched = [random test file]; no warnings.
  - `test_currency_warns_when_skill_touched_but_no_system_doc` - files_touched contains a SKILL.md; no system-tier doc; warnings non-empty.
  - `test_currency_passes_when_skill_and_system_doc_both_touched` - files_touched has both; no warnings.
  - `test_currency_matches_all_trigger_categories` - parameterized over SKILL.md, doctrine, schema, script categories; each triggers independently.

## Phase 2: Check Surface D/E triage + scope-fence tuning

352 D findings + 15 E findings today. Goal: make lenient mode signal-rich so future phases can confidently flip strict=True. Ships a triage CLI + tuned scope fences + glossary `referenced_by:` extensions for legitimate drift cases.

### Affected Files

- `tests/test_doc_integrity_strict_scope_tuning.py` - NEW; parameterized scope-fence tests.
- `tests/test_doc_integrity_drift_report_cli.py` - NEW; smoke-test for the new CLI.
- `qor/scripts/doc_integrity_strict.py` - MODIFY; (a) add doctrine-peer exclusion: if a term's home is a `doctrine-*.md` file, don't flag usage in other `doctrine-*.md` files (cross-doctrine references are normal); (b) add home-directory-peer exclusion: if a term's home is in directory X, don't flag usage in X's other files (siblings discussing shared concepts); (c) add optional `scope_exclude: []` glossary frontmatter field for per-entry opt-out.
- `qor/scripts/doc_integrity_drift_report.py` - NEW; CLI entry point: `python -m qor.scripts.doc_integrity_drift_report` runs both checks in lenient mode, groups findings by term + severity, writes a human-readable Markdown report to stdout. Operators run this ad-hoc for triage.
- `qor/references/glossary.md` - MODIFY; extend `referenced_by:` on entries where the lenient run surfaces legitimate consumers. Specifically for terms with >10 findings after scope-tuning, add the top consumers.
- `qor/references/doctrine-documentation-integrity.md` - MODIFY; §3 Check surface section gains concrete scope-fence rules (doctrine-peer + home-directory-peer exclusions) + documents the `scope_exclude:` opt-out.
- `docs/phase31-drift-triage-report.md` - NEW; human-readable triage artifact produced during Phase 2 execution. Captures: scope-fence tuning decisions made, glossary `referenced_by:` extensions applied, residual lenient findings accepted as known-drift, and the recommendation for a future strict-mode wiring phase. Plan file itself stays immutable post-audit (SG-Phase31-B countermeasure).

### Changes

**Scope-fence tuning** (core of Phase 2). `_iter_scan_files` in `doc_integrity_strict` already skips .py / .json / .toml / .cedar. New exclusions:

```python
# doctrine-peer exclusion: if term.home matches doctrine-*.md, skip other doctrines
if entry.home.startswith("qor/references/doctrine-") and rel.startswith("qor/references/doctrine-"):
    continue

# home-directory-peer exclusion: skip files in same dir as home
home_dir = str(Path(entry.home).parent)
rel_dir = str(Path(rel).parent)
if home_dir == rel_dir and home_dir != ".":
    continue

# per-entry scope_exclude opt-out (glossary frontmatter)
if rel in getattr(entry, 'scope_exclude', []):
    continue
```

Expected impact: 352 D findings -> ~50-80 post-tuning. Still triagable; scope-tunable further per-entry via the opt-out.

**Glossary entry extensions**. After tuning, run lenient D/E, identify terms whose remaining findings are legitimate consumers (e.g., `Governor` appearing in many skills -- those ARE consumers of the concept), extend their `referenced_by:` lists. Triage commentary captured in `docs/phase31-drift-triage-report.md` (new artifact). Plan file stays immutable post-audit (SG-Phase31-B countermeasure).

**Drift report CLI**. `qor/scripts/doc_integrity_drift_report.py` prints:

```
# Documentation Drift Report (lenient)

## Check Surface D (term-drift)
- Term 'Foo' (12 findings)
  - docs/a.md, docs/b.md, ...
- Term 'Bar' (3 findings)
  ...

## Check Surface E (cross-doc conflict)
- Term 'Baz' (2 divergent definitions)
  - docs/x.md: "Baz is ..."
  - docs/y.md: "Baz means ..."
```

Operators run it ad-hoc. Not wired into seal flow.

### Unit Tests

- `tests/test_doc_integrity_strict_scope_tuning.py`:
  - `test_doctrine_peer_excluded` - synthetic glossary with term home in doctrine-a.md; term used in doctrine-b.md; NOT flagged.
  - `test_home_dir_peer_excluded` - term home in docs/foo.md; usage in docs/bar.md; NOT flagged.
  - `test_scope_exclude_opt_out` - glossary entry with `scope_exclude: [docs/special.md]`; usage there NOT flagged.
  - `test_unrelated_directory_still_flagged` - regression; home is qor/references/, usage in docs/, IS flagged.
- `tests/test_doc_integrity_drift_report_cli.py`:
  - `test_cli_runs_against_live_repo` - invokes via subprocess; exit 0; output starts with `# Documentation Drift Report`.
  - `test_cli_groups_findings_by_term` - synthetic repo with 3 findings for Term X; output shows `Term 'X' (3 findings)`.

## Phase 3: PR citation CI lint

The governance-enforcement doctrine §6 requires PR descriptions to cite plan path + ledger entry + Merkle seal. Today this is unenforced. Phase 3 adds a CI lint.

### Affected Files

- `tests/test_pr_citation_lint.py` - NEW; unit tests for the lint function (not the workflow itself).
- `.github/workflows/pr-lint.yml` - NEW; runs on `pull_request` events (opened / reopened / synchronize / edited).
- `qor/scripts/pr_citation_lint.py` - NEW; reads PR body from stdin or file, checks for required citations, emits pass/fail with specific missing elements.
- `qor/references/doctrine-governance-enforcement.md` - MODIFY; §6 gains a note citing the new lint job as the enforcement mechanism.

### Changes

**Lint function** (`pr_citation_lint.py`):

```python
def check_pr_body(body: str) -> list[str]:
    """Return list of missing citations. Empty list means all present.

    Required per doctrine-governance-enforcement §6:
    - plan file path (docs/plan-qor-phase<NN>-<slug>.md)
    - ledger entry (#<n> format)
    - Merkle seal hash (64-char hex)
    """
    missing = []
    if not re.search(r"docs/plan-qor-phase\d+[a-z0-9-]*\.md", body):
        missing.append("plan file path (docs/plan-qor-phase<NN>-<slug>.md)")
    if not re.search(r"(?:entry|ledger)[^#]*#\d+", body, re.IGNORECASE):
        missing.append("ledger entry (#<n>)")
    if not re.search(r"\b[0-9a-f]{64}\b", body):
        missing.append("Merkle seal hash (64 hex chars)")
    return missing
```

**Workflow** (`.github/workflows/pr-lint.yml`):

```yaml
name: PR Citation Lint
on:
  pull_request:
    types: [opened, reopened, synchronize, edited]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e .
      - name: Lint PR description
        run: |
          echo "$PR_BODY" | python qor/scripts/pr_citation_lint.py
        env:
          PR_BODY: ${{ github.event.pull_request.body }}
```

Failing lint produces a clear error naming the missing citation; the PR author amends the description and CI re-runs on `edited`.

### Unit Tests

- `tests/test_pr_citation_lint.py`:
  - `test_all_citations_present` - body with plan path + entry + seal hash; returns empty list.
  - `test_missing_plan_path` - body without plan reference; returns list naming plan-path.
  - `test_missing_ledger_entry` - body without `#<n>`; flagged.
  - `test_missing_merkle_seal` - body without 64-char hex; flagged.
  - `test_all_three_missing` - empty body; list has all three items.
  - `test_seal_matches_hex_but_too_short` - body with 40-char hex; rejected (not a seal).
  - `test_case_insensitive_entry_reference` - body with "Ledger Entry #42" uppercase; accepted.

## Self-Dogfood

Per SG-Phase28-A + SG-Phase29-A + SG-Phase30-B:

- **Pre-plan doctrine check**: ran at `doc_tier: system`, `terms: []`, `plan_slug: phase31-operationalization`. PASS.
- **`doc_tier` declaration satisfied**: `system` at top-matter line 5. Four required docs (architecture/lifecycle/operations/policies) delivered in Phase 30; no new authoring required this phase.
- **`terms_introduced:` deliberately empty**: Phase 31 is mechanism + enforcement, not new concepts. Process labels ("Install Sync", "Drift Triage", "PR Citation Lint") do not rise to canonical-concept status. Omitting per SG-Phase30-B countermeasure (avoid metadata-only declarations).
- **`boundaries:` block populated**: three non-trivial entries each.
- **Every new rule has a test**:
  - Install sync rule -> `test_install_sync_with_source.py` (4 tests).
  - Session path unified rule -> `test_session_marker_path_unified.py` (3 tests).
  - Audit drift auto-invoke rule -> `test_audit_drift_auto_invoked.py` (2 tests).
  - Documentation Currency Check rule -> `test_documentation_currency_check.py` (4 tests).
  - Scope-fence tuning rules -> `test_doc_integrity_strict_scope_tuning.py` (4 tests).
  - Drift report CLI rule -> `test_doc_integrity_drift_report_cli.py` (2 tests).
  - PR citation lint rules -> `test_pr_citation_lint.py` (7 tests).
- **Enumeration cross-check (items)**: post-Phase-30 inventory listed 7 items in the operationalization bundle (1, 2, 3, 4, 8, 11, 13) plus the user-surfaced doc-currency requirement = 8 items total. Phase 1 covers items 1 (install sync), 2 (audit drift auto-invoke), 4 (path unification), 13 (install sync test), and the doc-currency contract. Phase 2 covers items 3 (D/E triage) and 11 (E on new docs subsumed). Phase 3 covers item 8 (PR citation lint). All 8 accounted for.
- **No bare-word YAML/TOML/JSON** requiring a safe-loader citation: Phase 31 touches markdown, tests, and existing helpers. No new parsing surface.
- **Razor anticipation applied at plan-authoring time (SG-Phase30-A countermeasure)**: `doc_integrity.py` sits at 249 lines today. The new `check_documentation_currency` function (~15 lines) would push it over the 250 cap. Self-Dogfood caught this early; Phase 1 Affected Files places the function in `doc_integrity_strict.py` (116 lines, well under cap) from the start. Substantiate SKILL.md imports the function via `from doc_integrity_strict import check_documentation_currency`. No "correction paragraph" pattern -- the upstream source of truth was edited directly (SG-Phase31-A countermeasure).

## CI Commands

- `python -m pytest tests/test_install_sync_with_source.py tests/test_session_marker_path_unified.py tests/test_audit_drift_auto_invoked.py tests/test_documentation_currency_check.py -v` (Phase 1).
- `python -m pytest tests/test_doc_integrity_strict_scope_tuning.py tests/test_doc_integrity_drift_report_cli.py -v` (Phase 2).
- `python -m pytest tests/test_pr_citation_lint.py -v` (Phase 3).
- `python -m pytest tests/ 2>&1 | tail -3` (full suite regression; target `>= 593 passed`).
- `python -m qor.scripts.doc_integrity_drift_report` (ad-hoc; Phase 2 deliverable; not required for seal).
- `python -c "import sys; sys.path.insert(0, 'qor/scripts'); import doc_integrity; plan = {'doc_tier':'system','terms':[],'plan_slug':'phase31-operationalization'}; doc_integrity.run_all_checks_from_plan(plan, repo_root='.')"` (self-check: Phase 31 must pass Step 4.7 at seal).
- New Step 6.5 self-check: `python -c "import sys; sys.path.insert(0,'qor/scripts'); import doc_integrity_strict as dis, gate_chain; sid='<current_sid>'; impl = gate_chain.read_phase_artifact('implement', session_id=sid); print(dis.check_documentation_currency(impl, repo_root='.'))"` -- expected empty or only warnings.

## Delegation

Per `qor/gates/delegation-table.md`:

- Plan complete -> `/qor-audit` (next phase).
- Phase 2 triage reveals scope-fence tuning is insufficient and D/E cannot reach a shippable signal-to-noise ratio -> halt and re-open dialogue; consider narrowing Phase 2 scope to E-only (15 findings are more tractable than 352).
- Phase 1 Step 6.5 heuristic surfaces unexpected complexity (e.g., implement.json schema doesn't carry `files_touched` reliably for all paths) -> extend Phase 1 Affected Files with a `qor/gates/schema/implement.schema.json` tightening; do not silently degrade the heuristic.
