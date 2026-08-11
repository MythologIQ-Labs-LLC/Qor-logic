# Plan: unseen-surface gates (Phase 219, GH #309, #311, #312)

**change_class**: feature

**doc_tier**: system

**terms_introduced**: detector scope disclosure

**boundaries**:
- limitations: The identity-term gap is closed at the local gate only. CI cannot
  check identity terms and this phase does not pretend otherwise; it makes the
  asymmetry visible rather than removing it. A repository whose operator never
  runs a local seal remains uncovered for identity terms, by construction.
- non_goals: No tracked denylist. No change to the four structural detectors. No
  change to CI's fail-closed structural step. No `--staged` mode.
- exclusions: #314 and #320 are out of scope.

## Open Questions

None.

## Locked Decisions

**LD-1 — The filed defect is wrong twice, and both corrections change the work.**

`git show HEAD:qor/scripts/publication_boundary_lint.py | grep -n 'ls-files' -> 43:        result = subprocess.run(["git", "-C", str(repo_root), "ls-files"],`

GH #309 says the lint misses files **staged** but not committed, and proposes a
`--staged` mode. Verified by counterfactual against a probe file carrying a real
violation: untracked yields 0 findings at rc 0; **staged yields 1 finding at rc
1**. `git ls-files` reads the index, so staged files are already scanned. A
`--staged` mode would narrow the surface to a subset of what is covered and would
have caught none of the four known misses.

The issue also says the seal ceremony runs the lint before staging. It does not
run it at all:

`git show HEAD:qor/skills/governance/qor-audit/SKILL.md | grep -n 'publication_boundary_lint' -> 169:qor-logic scripts publication_boundary_lint || true`

The only skill invocation is at `/qor-audit` Step 0.6, WARN-only, over a tree
that predates implementation. CI runs fail-closed but structural-only.

**The real gap: no fail-closed, identity-aware run ever sees implementation's new
files before they are committed.** That is why four leaks passed four green runs.

**LD-2 — Untracked coverage, not a narrower mode.**

Scan `git ls-files --others --exclude-standard` alongside the index.
`--exclude-standard` honors `.gitignore`, so the operator's private overlay and
build output stay out. Ignored files are not scanned and must not be: they are
not published.

**LD-3 — `qor-substantiate` needs a disclosure pass before it can carry the step.**

The file is at 39,908 bytes with 28 bytes of slack against the 39,936 lock. Entry
#545 recorded that the next step added to it requires a disclosure pass rather
than a trim; this phase is that next step, and the prediction holds.

The pass relocates rationale to `references/seal-gate-ladder.md` under LD-2 of
Phase 215 -- operative instructions and ABORT clauses stay inline, only
explanatory prose moves. Target: recover enough that the new step fits with
margin, not exactly enough that it fits.

**LD-4 — A green boundary result must carry its own scope.**

CI cannot see identity terms because `.gitignore:37` ignores `.qor/private/`, and
a tracked denylist would publish the strings it suppresses. That is correct and
permanent.

The remedy is disclosure, not coverage: the lint reports which detector set ran
(`structural` or `structural+identity`), and the seal entry records it. A reader
of a green boundary line can then tell whether identity terms were examined. An
unqualified "0 findings" from CI and from a local run mean different things and
currently look identical.

**LD-5 — #311 seeds positionally and one marker at a time.**

`git show HEAD:qor/scripts/seal_artifacts.py | grep -n 'header markers missing' -> 72:            "SYSTEM_STATE header markers missing: need '**Snapshot**: YYYY-MM-DD' "`

Both marker patterns are line-anchored under `re.MULTILINE`, so a marker appended
at end-of-file satisfies the regex while producing a document whose header block
is not its header. Insert under the `# ` title instead.

Seed only the absent marker: a file carrying one and not the other is
half-migrated, not broken, and an existing marker keeps its position.

An existing test asserts `raises(ValueError)` on the missing-marker path. It
encoded the defect as a contract and must be rewritten. The malformed-`snapshot`
`ValueError` validates the caller's argument rather than the document and stays.

**LD-6 — Counterfactual tests, per Phase 218 LD-5.**

Each fix ships a test that fails against `HEAD`: an untracked violating file must
be found, a markerless `SYSTEM_STATE.md` must be seeded. A good-path test would
pass today.

## Phase 1: Untracked coverage

### Unit Tests

- `tests/test_boundary_untracked_coverage.py::test_untracked_violation_is_found` -
  the counterfactual. Writes an untracked file carrying a structural violation
  and asserts a finding. Fails at HEAD, which returns 0.
- `::test_staged_violation_still_found` - regression; the index surface is not
  lost.
- `::test_gitignored_file_is_not_scanned` - ignored files are not published and
  must stay out, including the private overlay.
- `::test_committed_violation_still_found` - the original surface is intact.

### Affected Files

- `qor/scripts/publication_boundary_lint.py` - `_tracked_files` also collects
  `git ls-files --others --exclude-standard`.
- `tests/test_boundary_untracked_coverage.py` - NEW.

## Phase 2: Detector-scope disclosure

### Unit Tests

- `tests/test_boundary_scope_disclosure.py::test_scope_reports_structural_only_without_overlay` -
  asserts the summary line names `structural` when no terms file is present.
- `::test_scope_reports_identity_when_overlay_present` - asserts
  `structural+identity` when it is.
- `::test_scope_is_machine_readable` - the value is exposed as a return, not only
  printed, so the seal can record it without parsing prose.

### Affected Files

- `qor/scripts/publication_boundary_lint.py` - report and return the detector
  scope.
- `qor/gates/schema/substantiate.schema.json` - optional `boundary_scope`.
- `tests/test_boundary_scope_disclosure.py` - NEW.

## Phase 3: Seal-ceremony disclosure pass and wiring

### Unit Tests

- `tests/test_substantiate_boundary_wiring.py::test_seal_step_runs_the_boundary_lint` -
  asserts the skill names `publication_boundary_lint` in an executable step.
- `::test_seal_skill_stays_under_the_headroom_lock` - measured before and after.
- `::test_relocated_prose_is_reachable` - each moved block has a pointer to its
  destination subsection, so the disclosure pass does not orphan rationale.

### Affected Files

- `qor/skills/governance/qor-substantiate/SKILL.md` - disclosure pass, then a new
  step running the lint **after** staging and recording `boundary_scope`.
- `qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md` -
  receives the relocated rationale.
- `tests/test_substantiate_boundary_wiring.py` - NEW.

### Changes

Disclosure pass first, step second. If the step does not fit after the pass, the
pass was insufficient and is extended; the step is not compressed below the point
where it stops being executable.

## Phase 4: Marker seeding (#311)

### Unit Tests

- `tests/test_seal_artifacts_marker_seeding.py::test_write_seeds_missing_markers` -
  the counterfactual. A `SYSTEM_STATE.md` with a title and no markers is seeded.
  Fails at HEAD, which raises.
- `::test_markers_are_inserted_under_the_title_not_appended` - asserts position,
  because a line-anchored match at end-of-file would satisfy the regex while
  producing a malformed header.
- `::test_only_the_missing_marker_is_seeded` - an existing marker keeps its
  position.
- `::test_malformed_snapshot_still_raises` - regression; that check validates the
  caller's argument, not the document.

### Affected Files

- `qor/scripts/seal_artifacts.py` - `render_system_state_header` seeds instead of
  raising.
- `tests/test_seal_artifacts.py` - rewrite the test that encoded the raise as a
  contract.
- `tests/test_seal_artifacts_marker_seeding.py` - NEW.

## Phase 5: Record the pattern (#312)

### Affected Files

- `docs/SHADOW_GENOME.md` - `SG-GrepAbsenceAsIntegrationAbsence-A`, cross-linked
  with `SG-GrepShapedRunclaim-A` so the pair is reachable from either direction.
  `closure_enforcer` cites
  `tests/test_boundary_untracked_coverage.py::test_untracked_violation_is_found`.

### Changes

The entry names the ADR tell: architectural claims are written in the vocabulary
of authorities and consumption, not imports, so testing one by import graph is a
category error from the first step.

## Phase 6: Verification

### Unit Tests

- The four new test modules, run twice.
- The full suite.
- `skill_size_budget_lint` with before/after for `qor-substantiate`.
- `dist_compile` zero-drift.
- `qor-logic scripts publication_boundary_lint --repo-root .` against the live
  tree with untracked files present.

## Definition of Done

### Deliverable: the unseen surface is seen

- **D1**: A violation introduced in a new file is caught before the commit lands,
  by a fail-closed identity-aware run.
- **D2**: `publication_boundary_lint` scans untracked-not-ignored files and
  reports its detector scope; `qor-substantiate` runs it after staging.
- **D3**: Seal entry records `boundary_scope` and states that CI remains
  structural-only by design.
- **D4**: `test_untracked_violation_is_found` fails against `HEAD` and passes
  after.

### Deliverable: the bootstrap loop closes

- **D1**: A repository adopting the toolkit can run `--write` on a
  `SYSTEM_STATE.md` that never carried markers.
- **D2**: `render_system_state_header` seeds positionally, one marker at a time.
- **D3**: Seal entry records that an existing test encoded the defect as a
  contract and was rewritten.
- **D4**: `test_write_seeds_missing_markers` fails against `HEAD`; the
  malformed-`snapshot` raise still passes.

### Deliverable: nothing is weakened

- **D1**: No detector loses a surface it already covered.
- **D2**: Ignored files stay unscanned; `qor-substantiate` stays under the lock.
- **D3**: Seal entry records the disclosure pass sizes before and after.
- **D4**: Full suite green; the only edited existing test is the one LD-5 names.

## Feature Inventory Touches

| Feature | Touch | Source-of-truth | test_descriptor |
|---|---|---|---|
| Untracked boundary coverage | NEW | `qor/scripts/publication_boundary_lint.py` | `test_boundary_untracked_coverage.py::test_untracked_violation_is_found` asserts an untracked violating file yields a finding |
| Detector scope disclosure | NEW | `qor/scripts/publication_boundary_lint.py` | `test_boundary_scope_disclosure.py::test_scope_reports_identity_when_overlay_present` asserts the reported scope names identity coverage |

## CI Commands

- `python -m pytest tests/test_boundary_untracked_coverage.py tests/test_boundary_scope_disclosure.py tests/test_substantiate_boundary_wiring.py tests/test_seal_artifacts_marker_seeding.py -q` — the counterfactual tests.
- `python -m pytest tests/ -q` — full suite; the definition of done for this plan.
- `python -m ruff check qor/ tests/` — the new modules are lint clean.
- `qor-logic scripts skill_size_budget_lint --skills-root qor/skills` — `qor-substantiate` stays under the lock after the disclosure pass.
- `qor-logic scripts dist_compile` — variants rebuilt with zero drift.
- `qor-logic scripts sg_closure_lint` — the new Shadow Genome entry carries an enforcer citation.
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase219-unseen-surface-gates.md` — this plan asserts each path and command identically at every site.
