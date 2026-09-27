# Plan: Phase 298 - Close Dependency Review SBOM path coverage gap

**change_class**: hotfix

**doc_tier**: minimal

**iteration**: 2 (on branch `phase/298-dependency-review-sbom-path-coverage-current`; responds to VETO META_LEDGER #815)

**Issue**: GH #511

**Current base**: `43ee76b7ed561a308eaeab0844044c7642e02efd` (`main` after Phase 297 merged; project version `0.175.1`, sealed at META_LEDGER #814)

**Target version**: `0.175.2` (hotfix bump from `0.175.1`)

**Provenance**: this plan recomposes Phase 298 on the new `main`. Its substance is the iteration-3 plan authored on the prior branch `phase/298-dependency-review-sbom-path-coverage` (PR #522, plan commit `cddc903`), which received audit PASS in META_LEDGER entry #811 of that branch after VETOs at entries #809 and #810 of that branch. Those entry numbers belong to that branch's ledger only; on `main` the same numbers are Phase 297 entries, and this branch's ledger continues from #814. That branch's audit, implementation (`357baf3`) and seal of `0.175.1` (`af0ae68c`, entries #809-#813 of that branch) are bound to base `15729311f9f4d55d5dad2db004b972415c39432c`. They are revision-bound ancestry only and are not audit, implementation or seal authority for this branch. This plan requires a fresh `/qor-audit` on this revision.

**Citation currency**: every `git show` evidence statement below cites the current base `43ee76b7ed561a308eaeab0844044c7642e02efd` and was re-executed against it for iteration 2 (51 statements: the 49 carried from iteration 1, all reproduced, plus 2 added in iteration 2; 0 mismatches), together with the no-match, prints-nothing, line-count, empty-diff, line-24134 and `merge-base --is-ancestor` claims. The evidence statements cite 18 files. Byte identity between `15729311f9f4d55d5dad2db004b972415c39432c` and the current base was computed per file with `git diff --name-only 15729311f9f4d55d5dad2db004b972415c39432c 43ee76b7ed561a308eaeab0844044c7642e02efd -- <path>` (empty output means byte-identical):

- byte-identical (10): `.github/workflows/pr-dependency-review.yml`, `.github/workflows/release.yml`, `qor/references/doctrine-dependency-admission.md`, `qor/references/glossary.md` (first cited in iteration 2), `qor/scripts/_dep_admit_common.py`, `qor/scripts/dependency_admission_lint.py`, `qor/scripts/governance_helpers.py`, `tests/support/git_fixture.py`, `tests/test_dependency_admission_lint.py`, `tests/test_pr_dependency_review_workflow.py`;
- changed by Phase 297 (5): `pyproject.toml`, `CHANGELOG.md`, `docs/META_LEDGER.md`, `qor/references/doctrine-changelog.md`, `tests/test_changelog_tag_coverage.py`;
- absent at `15729311f9f4d55d5dad2db004b972415c39432c`, created by Phase 297 (3): `qor/scripts/release_state.py`, `docs/release-state.json`, `tests/test_release_state.py`.

The 8 changed or new files carry LD-10 and LD-11. Their citations have no counterpart at the prior base and rest only on the re-execution at the current base. Iteration 1 of this plan cited the other 17 files, and it and its commit message `e055cd34` claimed every cited file was byte-identical to the prior base. That claim was false for these 8 files (VETO #815, V1). It is withdrawn here; the commit message is history and is not amended.

## Open Questions

None.

## Problem

The repository's `PR Dependency Review` workflow is intended to block unsafe dependency changes, but its `pull_request.paths` filter watches only `pyproject.toml`, `requirements-release.txt`, and workflow files.

The governed root dependency surface is broader:

- `requirements-release.in`
- `requirements-release.txt`
- `requirements-sbom.in`
- `requirements-sbom.txt`

PR #496 changes only `requirements-sbom.txt`. Because that path is absent from the filter, the workflow never starts, so neither `actions/dependency-review-action` nor the hard-fail dependency-admission cooling-period step runs. The existing regression test preserves the same blind spot.

Widening the filter alone is not sufficient. The cooling-period step invokes `dependency_admission_lint` with `--base` only, and the lint examines exactly one lockfile, `requirements-release.txt` by default. After a filter-only fix, a `requirements-sbom.txt`-only PR would run the step and pass it with zero entries examined. That vacuous pass is the residual iteration 1 left open. This plan closes it by running the admission step once per governed root lockfile.

PR #512 demonstrated the bounded workflow/test correction, but its non-phase branch and plan filename could not enter Qor's canonical audit resolver. Phase 298 recomposes the correction in canonical governance shape and starts plan-first so the normal audit -> implement -> substantiate sequence remains intact.

Phase 297 landed on `main` first and took `0.175.1`. Phase 298 therefore seals as `0.175.2`, and its seal must leave release-state coverage truthful for the `0.175.1` it supersedes as project version (LD-10, LD-11).

## Locked Decisions

### LD-1: both dependency inputs and generated locks are gate-bearing

A dependency can enter through an `.in` declaration or through a generated `.txt` lock update. Both are supply-chain-relevant and both must trigger Dependency Review.

The current base proves the trigger surface is incomplete. The filter holds exactly these two dependency-bearing entries:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:.github/workflows/pr-dependency-review.yml | grep -nE '"pyproject.toml"'` -> `9:      - "pyproject.toml"`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:.github/workflows/pr-dependency-review.yml | grep -nE '"requirements-release.txt"'` -> `10:      - "requirements-release.txt"`

The pattern `requirements-(release\.in|sbom)` has no match in that file at the base.

`requirements-sbom.txt` is a real release-build input:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:.github/workflows/release.yml | grep -nE 'requirements-sbom.txt'` -> `59:          pip install --require-hashes -r requirements-sbom.txt`

### LD-2: the governed path set is derived, not enumerated

The governed root dependency surface is defined mechanically as: every repository-root file matching `requirements-*.in` or `requirements-*.txt`, plus `pyproject.toml`. At the base this yields exactly five files:

- `pyproject.toml`
- `requirements-release.in`
- `requirements-release.txt`
- `requirements-sbom.in`
- `requirements-sbom.txt`

The regression derives the set from the repository root at test time, so a future `requirements-<name>.in/.txt` pair that is not added to the workflow fails the test. It also asserts the five known files are members of the derived set, so the derivation cannot silently shrink. The workflow keeps an explicit path list (no glob), and self-coverage through `.github/workflows/**` remains required.

The current regression is the enumerated-subset shape GH #511 names:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:tests/test_pr_dependency_review_workflow.py | grep -nE 'required_paths = '` -> `54:    required_paths = {"pyproject.toml", "requirements-release.txt"}`

### LD-3: policy semantics do not change

This slice does not change dependency versions, `fail-on-severity`, the 14-day cooling-period threshold, override semantics (META_LEDGER entry or `dep-admit-override` label), the hard-fail posture, or the dependency-review action pin. It changes no code under `qor/`. It repairs trigger coverage and makes the existing admission step examine every governed root lockfile through the lint's existing `--lockfile` argument.

### LD-4: #496 re-evaluation criterion

The absence of a Dependency Review run on #496 is evidence that the gate did not execute, not evidence that the dependency change passed. Re-evaluate #496 only after this correction is accepted on `main` and a `PR Dependency Review` run exists on #496's current head.

Admission evidence for #496 requires both: the `actions/dependency-review-action` step ran, and the `requirements-sbom.txt` admission step's output lists a `cyclonedx-bom` row. A green `requirements-sbom.txt` step whose output is `_No lockfile bumps detected._` is not admission evidence for #496 and must not be read as such. A `violation` row fails the step; admission then follows the doctrine's override procedure or waits out the window. This plan does not decide #496.

### LD-5: canonical governance shape is part of the fix

The work lives on `phase/298-dependency-review-sbom-path-coverage-current` and this file is the canonical `docs/plan-qor-phase298-*.md` plan consumed by Qor's phase resolver. The branch remains plan-only until `/qor-audit` returns PASS. Only then may `/qor-implement` apply the bounded changes under TDD-Light.

The resolver contract on the current base:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/governance_helpers.py | grep -nE '_BRANCH_PHASE_RE ='` -> `23:_BRANCH_PHASE_RE = re.compile(r"^phase/(\d+)-")`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/governance_helpers.py | grep -nE 'def current_phase_plan_path'` -> `57:def current_phase_plan_path(docs_dir: Path | None = None) -> Path:`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/governance_helpers.py | grep -nE 'Not on a phase branch'` -> `62:        raise InterdictionError(f"Not on a phase branch: {branch!r}")`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/governance_helpers.py | grep -nE 'plan-qor-phase\{nn\}'` -> `64:    candidates = sorted(docs_dir.glob(f"plan-qor-phase{nn}*.md"))`

No ledger, gate, intent-lock, HMAC, or Merkle evidence is hand-authored through GitHub. Admission must pass the repository's real `/qor-audit` and `/qor-substantiate` path on a writable checkout.

The prior implementation commit `357baf3` on PR #522 is reference only. `/qor-implement` re-does the work test-first on this base: the Phase 1 tests are written and observed RED (or, for the CLI tests, proven discriminating) before the workflow, doctrine and release-state edits. No file is copied or cherry-picked from `357baf3` as evidence of completion.

### LD-6: one admission step per governed root lockfile

The lint's CLI entry point reads one lockfile, named by `--lockfile`, defaulting to `requirements-release.txt`, and diffs it against the same path at `--base`:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/dependency_admission_lint.py | grep -nE 'add_argument\("--lockfile"'` -> `241:    p.add_argument("--lockfile", default="requirements-release.txt")`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/dependency_admission_lint.py | grep -nE 'current_path = repo_root'` -> `248:    current_path = repo_root / args.lockfile`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/dependency_admission_lint.py | grep -nE 'base_text = _git_show'` -> `254:    base_text = _git_show(base_ref, args.lockfile, repo_root)`

The workflow step passes `--base` only, so it examines `requirements-release.txt` alone:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:.github/workflows/pr-dependency-review.yml | grep -nE 'python -m qor.scripts.dependency_admission_lint'` -> `39:          python -m qor.scripts.dependency_admission_lint \`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:.github/workflows/pr-dependency-review.yml | grep -nE 'base.sha'` -> `40:            --base "${{ github.event.pull_request.base.sha }}"`

Mechanism: replace the single admission step with one step per governed root lockfile (every root `requirements-*.txt`; today `requirements-release.txt` and `requirements-sbom.txt`), each passing `--base "${{ github.event.pull_request.base.sha }}"` and an explicit `--lockfile <name>`, none wrapped in `|| true`. The lint is not changed; it already parses a pip-compile hash lockfile regardless of its name. Separate steps are chosen over a lint that accepts several lockfiles because they reuse the existing interface and change no code. A violation in the first step fails the job before the second step runs; the job still fails, so the hard-fail posture holds.

Observed evidence that the lint parses `requirements-sbom.txt` (run 2026-09-25 against the prior base `15729311f9f4d55d5dad2db004b972415c39432c`, lint and `_dep_admit_common` byte-identical between that base and #496's head `ac568fdf2a547332b50aeef41efe25bb70027429`; detached scratch worktree of #496's head, since removed). Both files are also byte-identical between that prior base and the current base (`git diff --stat 15729311f9f4d55d5dad2db004b972415c39432c 43ee76b7ed561a308eaeab0844044c7642e02efd -- qor/scripts/dependency_admission_lint.py qor/scripts/_dep_admit_common.py` prints nothing), so the observation carries over:

- `python -m qor.scripts.dependency_admission_lint --base 15729311f9f4d55d5dad2db004b972415c39432c --lockfile requirements-sbom.txt` printed `WARN: cyclonedx-bom@7.4.0 uploaded 10 days ago (within 14d window); override absent`, the table row `| cyclonedx-bom | 7.4.0 | 10 | violation |`, and exited 1.
- The same command without `--lockfile` (the current workflow's form) printed only `| build | 1.6.0 | 29 | clean |` and exited 0. That row reflects #496's head predating `main`'s `build` bump; the sbom change was not examined.

The age value is time-dependent and is recorded as an observation, not as a test expectation. The routing it illustrates is proven deterministically by LD-9.

Accepted step behavior: the steps run in declared order, release lockfile first. A violation in an earlier step stops the job before later steps report; the job still fails, and the later lockfile is reported on the next run after the first is resolved. This fail-fast ordering is accepted. A PR that deletes a governed lockfile makes its step exit 2 (fail-closed), because the lint refuses a missing lockfile:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/dependency_admission_lint.py | grep -nE 'ERROR: lockfile not found'` -> `250:        print(f"ERROR: lockfile not found at {current_path}", file=sys.stderr)`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/dependency_admission_lint.py | grep -nE 'return 2$'` -> `251:        return 2`

Removing a governed lockfile therefore also requires removing its admission step, which is itself a governed workflow change. This exit-2 behavior is accepted as fail-closed.

### LD-7: residual - pyproject pins are not examined by the CLI entry point

`run_lint` accepts pyproject text, but `main` never passes it. The call spans lines 258-263 and carries these four keywords only:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/dependency_admission_lint.py | grep -nE 'result = run_lint\('` -> `258:    result = run_lint(`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/dependency_admission_lint.py | grep -nE 'current_lockfile_text=current_text'` -> `259:        current_lockfile_text=current_text,`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/dependency_admission_lint.py | grep -nE 'base_lockfile_text=base_text'` -> `260:        base_lockfile_text=base_text,`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/dependency_admission_lint.py | grep -nE 'ledger_text=ledger_text,'` -> `261:        ledger_text=ledger_text,`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/dependency_admission_lint.py | grep -nE 'threshold_days=args.threshold_days,'` -> `262:        threshold_days=args.threshold_days,`

So a `pyproject.toml` or `.in` change triggers the workflow (dependency-review-action runs), but the cooling-period step examines only the governed lockfiles. Wiring pyproject pins through `main` is a lint code change and is out of scope for this hotfix. The residual is declared here and in the doctrine; D1 does not claim it.

### LD-8: assumption - dependency graph recognition of `requirements-sbom.txt`

Whether the GitHub dependency graph used by `actions/dependency-review-action` recognizes a manifest named `requirements-sbom.txt` could not be verified from this host and is not cited. This plan makes no claim that the action evaluates that file. The control this plan proves for the sbom lockfile is the in-repo cooling-period step (LD-6). The action runs on every governed-path PR either way.

### LD-9: the CLI routing of `--lockfile` is proven by a deterministic test

D1's "examined" claim rests on `main` using `--lockfile` for both the current read (line 248, LD-6) and the base `git show` read (line 254, LD-6). A new test file invokes `main` directly with argv against a temporary git repository, so a regression in either read fails a declared test.

`main` takes argv and a repository root:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/dependency_admission_lint.py | grep -nE 'def main\(argv'` -> `238:def main(argv: list[str] | None = None) -> int:`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/dependency_admission_lint.py | grep -nE 'p.add_argument\("--repo-root"'` -> `243:    p.add_argument("--repo-root", default=".")`

The clock and the PyPI lookup are module-level functions that the test monkeypatches; no network and no wall clock are used:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/dependency_admission_lint.py | grep -nE 'def _now_utc'` -> `59:def _now_utc() -> datetime:`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/dependency_admission_lint.py | grep -nE 'now = _now_utc\(\)'` -> `158:    now = _now_utc()`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/dependency_admission_lint.py | grep -nE 'upload_time = _fetch_pypi_upload_time\('` -> `165:            upload_time = _fetch_pypi_upload_time(bump.name, bump.new_version)`

`main` does not pass `skip_pr_labels`, and the label query reads the CI environment, so the test also monkeypatches `_query_pr_labels` to return `None` (no `gh` subprocess, no dependence on `GITHUB_EVENT_NAME` in the CI job that runs pytest):

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/dependency_admission_lint.py | grep -nE 'event = os.environ.get\("GITHUB_EVENT_NAME"'` -> `92:    event = os.environ.get("GITHUB_EVENT_NAME", "")`

`run_lint` calls the label query with a keyword argument, so the replacement must accept `skip`:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/dependency_admission_lint.py | grep -nE 'pr_labels = _query_pr_labels\('` -> `155:    pr_labels = _query_pr_labels(skip=skip_pr_labels)`

The scratch repository must be hermetic per the Phase 209 fixture contract. Fixture git commands use the shared helper, which excludes ambient global and system config and supplies its own identity:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:tests/support/git_fixture.py | grep -nE 'def scratch_env'` -> `38:def scratch_env(**overrides: str) -> dict[str, str]:`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:tests/support/git_fixture.py | grep -nE 'def run_git'` -> `53:def run_git(`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:tests/support/git_fixture.py | grep -nE 'env\["GIT_CONFIG_GLOBAL"\] = _NO_CONFIG'` -> `45:    env["GIT_CONFIG_GLOBAL"] = _NO_CONFIG`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:tests/support/git_fixture.py | grep -nE 'env\["GIT_CONFIG_NOSYSTEM"\]'` -> `47:    env["GIT_CONFIG_NOSYSTEM"] = "1"`

The lint's own base read runs `git show` in a subprocess that inherits the test process environment:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/dependency_admission_lint.py | grep -nE '\["git", "show"'` -> `215:            ["git", "show", f"{ref}:{path}"],`

So the test also sets `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM` and `GIT_CONFIG_NOSYSTEM` through `monkeypatch.setenv`, taking the values from `scratch_env()`, which keeps the lint's `git show` hermetic too.

The lint validates each hash digest, so fixture hashes must be `sha256:` followed by exactly 64 lowercase hex characters:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/_dep_admit_common.py | grep -nE 'must be 64 hex chars'` -> `104:        raise LockfileParseError(f"hash digest {digest!r} must be 64 hex chars")`

The clock seam already has an established test pattern:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:tests/test_dependency_admission_lint.py | grep -nE 'monkeypatch.setattr\(lint, "_now_utc"'` -> `43:    monkeypatch.setattr(lint, "_now_utc", lambda: fixed)`

No existing test calls `main`: `git show 43ee76b7ed561a308eaeab0844044c7642e02efd:tests/test_dependency_admission_lint.py | grep -nE 'lint.main|--lockfile'` prints nothing. No lint code change is needed; LD-3 holds.

The new tests go in a new file rather than `tests/test_dependency_admission_lint.py`, which is already 333 lines at the base.

### LD-10: version target is 0.175.2

Phase 297 sealed `0.175.1` on `main`, so the base project version is `0.175.1`:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:pyproject.toml | grep -nE '^version = '` -> `7:version = "0.175.1"`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:CHANGELOG.md | grep -nE '^## \[0\.175\.1\]'` -> `13:## [0.175.1] - 2026-09-27`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:docs/META_LEDGER.md | grep -nE '^### Entry #814'` -> `24112:### Entry #814: SESSION SEAL -- Phase 297 sealed-unpublished release state (v0.175.1)`

`change_class: hotfix` bumps `0.175.1` to `0.175.2` at `/qor-substantiate`. The superseded PR #522 candidate that sealed `0.175.1` (`af0ae68c`) is not an ancestor of the current base (`git merge-base --is-ancestor af0ae68c 43ee76b7ed561a308eaeab0844044c7642e02efd` exits 1). It never reached `main`, so it needs no release-state entry. It stays on PR #522 as revision-bound ancestry. This plan does not reuse, re-tag or re-number any of its evidence.

### LD-11: release-state continuity for the superseded 0.175.1

Once the seal bumps the project version to `0.175.2`, `0.175.1` stops being the single implicit candidate. The coverage rule then treats it as an orphan unless a reachable tag or a disposition covers it:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/release_state.py | grep -nE 'v for v in versions - tags - set\(exceptions\) - \{project_version\}'` -> `118:        v for v in versions - tags - set(exceptions) - {project_version}`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/release_state.py | grep -nE 'if _semver\(v\) <= ceiling'` -> `119:        if _semver(v) <= ceiling`

`0.175.1` has no release tag on the remote. Phase 297's seal states this: at `43ee76b7ed561a308eaeab0844044c7642e02efd`, line 24134 of `docs/META_LEDGER.md` is the Entry #814 `**Version**:` line, and it ends with the sentence "No remote tag is created; the seal tag stays local." (a `grep -n` for that sentence at that revision prints line 24134; the line carries inline code spans, so it is quoted in part here rather than as a full-line evidence statement). While authoring iterations 1 and 2, `git ls-remote --tags origin` listed no `v0.173+` tag; the highest remote tag was `v0.172.2` (observation, 2026-09-27; not a test expectation).

The record at the base covers `0.175.0` and no later version:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:docs/release-state.json | grep -nE '"version": "0\.175\.(0|1)"'` -> `65:      "version": "0.175.0",`

This phase appends exactly one entry to `docs/release-state.json`, after the `0.175.0` entry:

- `version`: `0.175.1`
- `state`: `sealed_unpublished`
- `reason`: `Sealed by /qor-substantiate (META_LEDGER #814); no release tag was pushed to the remote, so the version is sealed but not published.`

The reason is true at authoring time and stays true after the `0.175.2` seal. The record validator requires a dated CHANGELOG section for every entry, and `0.175.1` has one (see LD-10):

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/scripts/release_state.py | grep -nE 'has no dated CHANGELOG section'` -> `84:        raise ReleaseStateError(f"{path}: {version} has no dated CHANGELOG section")`

A local seal tag `v0.175.1` created by Phase 297's seal is reachable from `HEAD` in a local checkout. It is not on the remote, so CI does not see it. It does not void the disposition:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/references/doctrine-changelog.md | grep -nE 'stays authoritative even if a local seal tag exists'` -> `83:  stays authoritative even if a local seal tag exists. Publishing the version`

Because that local tag covers `0.175.1` locally, the plain local run of the tag-coverage suite cannot tell whether the entry is present. The proof therefore uses a CI view, in which every tag absent from the remote is ignored. It runs twice (Phase 4):

- At `/qor-implement`, an in-memory simulation models the post-seal state (project version `0.175.2`) against the working tree. It does not depend on seal ordering.
- After the seal, a post-seal verification runs the real suite in a scratch clone of the seal commit. `git clone` copies committed history only. `/qor-substantiate` bumps at Step 7.5 and stamps at Step 7.6, but commits at Step 9.5 and tags at Step 9.5.5. So the clone proof runs after Step 9.5.5 and before Step 9.6 (push/merge). A guard makes it fail unless the clone's `[project].version` is `0.175.2` and its CHANGELOG carries a dated `## [0.175.2] - ` section. Run any earlier, the clone holds the implement commit (`0.175.1`) and the guard fails, so the proof cannot pass vacuously. It also fails if pytest reports a skip.

The suite consumes the live record:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:tests/test_changelog_tag_coverage.py | grep -nE 'exceptions = release_state.load_release_state\(RELEASE_STATE, versions\)'` -> `54:    exceptions = release_state.load_release_state(RELEASE_STATE, versions)`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:tests/test_changelog_tag_coverage.py | grep -nE 'def test_every_changelog_section_has_tag'` -> `68:def test_every_changelog_section_has_tag():`

No `release_state` code changes. The coverage rule already has unit tests for a single disposition and for a `sealed_unpublished` version with a local tag:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:tests/test_release_state.py | grep -nE 'def test_disposition_exempts_only_the_named_version'` -> `109:def test_disposition_exempts_only_the_named_version():`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:tests/test_release_state.py | grep -nE 'def test_sealed_unpublished_version_with_local_tag_is_clean'` -> `115:def test_sealed_unpublished_version_with_local_tag_is_clean():`

The entry is recorded by `/qor-implement` (Phase 4), not written by hand at seal time. No entry is recorded for `0.175.2`: after the seal it is the implicit candidate.

## Feature Inventory Touches

Empty. This is workflow/test/doctrine maintenance and introduces no `src/` or user-touchable product feature surface.

`feature_inventory_touches`: `[]`.

## Phase 1: Regression tests

### Affected Files

- `tests/test_dependency_admission_lint_cli.py` (NEW) - prove `dependency_admission_lint.main` routes `--lockfile` to both the current read and the base `git show` read (LD-9).
- `tests/test_pr_dependency_review_workflow.py` - derive the governed dependency set from the repository root; require workflow trigger coverage and per-lockfile admission coverage for it.

### Changes

`tests/test_dependency_admission_lint_cli.py` (NEW, about 90 lines):

- fixture `fixed_now` pins `lint._now_utc` to `datetime(2026, 5, 25, tzinfo=timezone.utc)` (the existing pattern);
- fixture `fake_pypi` monkeypatches `lint._fetch_pypi_upload_time` with a recorder that appends `(name, version)` to a list and returns `fixed_now - timedelta(days=5)`, and monkeypatches `lint._query_pr_labels` with `lambda skip=False: None`;
- fixture `hermetic_git` sets `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM` and `GIT_CONFIG_NOSYSTEM` via `monkeypatch.setenv` to their `scratch_env()` values, so the lint's internal `git show` reads no ambient config (LD-9);
- helper `_fixture_repo(tmp_path) -> str` uses `run_git` from `tests.support.git_fixture` (default `scratch_env()`) for every git command: `git init -b main`, then two commits with `git commit -q`. The base commit holds `requirements-release.txt` (`build==1.6.0`) and `requirements-sbom.txt` (`cyclonedx-bom==7.3.0` and `sbom-anchor==1.0.0`), in pip-compile form: each `name==version \` line is followed by an indented `--hash=sha256:<64 lowercase hex>` line. The head commit changes only `requirements-sbom.txt`, bumping `cyclonedx-bom` to `7.4.0`. The helper returns the base commit SHA from `git rev-parse HEAD`, taken before the head commit. No ledger file exists in the fixture, so the ledger text is empty.

Tests (argv only, `capsys` for output):

- `test_main_lockfile_arg_examines_named_lockfile`: `lint.main(["--base", base, "--lockfile", "requirements-sbom.txt", "--repo-root", str(tmp_path)])` returns `1`. The recorder equals exactly `[("cyclonedx-bom", "7.4.0")]`, stdout contains `| cyclonedx-bom | 7.4.0 | 5 | violation |`, and stderr contains `WARN: cyclonedx-bom@7.4.0`.
- `test_main_default_lockfile_does_not_examine_sbom_bump`: `lint.main(["--base", base, "--repo-root", str(tmp_path)])` on the same fixture returns `0`. The recorder is empty and stdout contains `_No lockfile bumps detected._`.

Discrimination: if the current read ignored `--lockfile`, the release lockfile would be diffed against the sbom base and `build` would be fetched. If the base read ignored `--lockfile`, `sbom-anchor` would appear as a new entry and be fetched. If the argument were dropped, no bump would be found and the exit would be `0`. Each case breaks the exact-recorder or exit-code assertion.

`tests/test_pr_dependency_review_workflow.py`: add `_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]` and resolve `_WORKFLOW` from it, so the tests do not depend on the working directory. `_WORKFLOW` is cwd-relative at the base:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:tests/test_pr_dependency_review_workflow.py | grep -nE '_WORKFLOW = '` -> `9:_WORKFLOW = pathlib.Path(".github/workflows/pr-dependency-review.yml")`

Add a module-level helper `_governed_dependency_paths() -> set[str]` returning the names of files directly under `_REPO_ROOT` matching `requirements-*.in` or `requirements-*.txt`, plus `pyproject.toml`. Add `_KNOWN_GOVERNED = {"pyproject.toml", "requirements-release.in", "requirements-release.txt", "requirements-sbom.in", "requirements-sbom.txt"}`.

Rewrite `test_workflow_triggers_on_dependency_paths`:

- assert `_KNOWN_GOVERNED` is a subset of `_governed_dependency_paths()`;
- assert `_governed_dependency_paths()` is a subset of the parsed `on.pull_request.paths`;
- keep the existing `.github/workflows/**` self-coverage assertion.

Add `test_admission_lint_runs_for_every_governed_lockfile`:

- walk every job under `jobs`, and collect each job's parsed steps whose `run` invokes `dependency_admission_lint`, keeping the owning job with each step;
- extract each step's `--lockfile` argument;
- assert every governed lockfile (members of `_governed_dependency_paths()` ending in `.txt`) is named by exactly one such step;
- assert each such step's `run` contains `--base`, and contains neither `|| true` nor `set +e`;
- assert each such step has no `if:` key and no truthy `continue-on-error`;
- assert each owning job has no `if:` key and no truthy `continue-on-error` (a job-level guard would neutralize its steps as surely as a step-level one).

### Unit Tests

- `tests/test_dependency_admission_lint_cli.py::test_main_lockfile_arg_examines_named_lockfile` - invokes `main` with `--lockfile requirements-sbom.txt` against the fixture repository and asserts the sbom bump is the only entry examined, is reported as a violation, and yields exit 1.
- `tests/test_dependency_admission_lint_cli.py::test_main_default_lockfile_does_not_examine_sbom_bump` - invokes `main` without `--lockfile` on the same fixture and asserts no entry is examined, `_No lockfile bumps detected._` is printed, and exit is 0.
- TDD classification for the two CLI tests: regression coverage backfill. `main` already honours `--lockfile` at the base (LD-6 lines 248 and 254), so they are GREEN on first run. The implementer proves they discriminate by a local, uncommitted mutation: replace `args.lockfile` with `"requirements-release.txt"` at line 254, then separately at line 248, run the file with `python -B -m pytest` (both mutations change the file by the same byte count, so a stale bytecode cache could mask the second), and observe `test_main_lockfile_arg_examines_named_lockfile` FAIL each time. The implementer then reverts, confirms `git diff --exit-code qor/scripts/dependency_admission_lint.py`, and runs the file twice GREEN.
- `tests/test_pr_dependency_review_workflow.py::test_workflow_triggers_on_dependency_paths` - parses the real workflow YAML and fails when any derived governed path, including a newly added root `requirements-*.in/.txt` file, is absent from `on.pull_request.paths`. RED against the pre-fix workflow (the three missing paths).
- `tests/test_pr_dependency_review_workflow.py::test_admission_lint_runs_for_every_governed_lockfile` - parses the real workflow YAML and fails when any governed root lockfile has no hard-fail admission step naming it, or when a naming step, or the job that owns it, is neutralized by `|| true`, `set +e`, `continue-on-error: true` or an `if:` guard. RED against the pre-fix workflow (no step passes `--lockfile`).

## Phase 2: Workflow coverage

### Affected Files

- `.github/workflows/pr-dependency-review.yml` - add the three missing dependency-bearing root paths; run the admission step once per governed root lockfile.

### Changes

Add exactly these entries under `on.pull_request.paths`:

- `requirements-release.in`
- `requirements-sbom.in`
- `requirements-sbom.txt`

Replace the single admission step with two steps, each running `python -m qor.scripts.dependency_admission_lint --base "${{ github.event.pull_request.base.sha }}" --lockfile <name>`: one for `requirements-release.txt`, one for `requirements-sbom.txt`. Neither is wrapped in `|| true` or `set +e`, and neither carries `continue-on-error` or an `if:` guard. The owning `dependency-review` job stays unguarded. The pattern `continue-on-error|if:` has no match in the workflow at the base, whose only job is `dependency-review`:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:.github/workflows/pr-dependency-review.yml | grep -nE '^  [a-z-]+:$'` -> `22:  dependency-review:`

Preserve every existing trigger path, the action pin, `fail-on-severity: high`, and the checkout/setup/install steps unchanged.

### Unit Tests

- Re-run both Phase 1 tests after the workflow edit and observe GREEN.
- Run the full `tests/test_pr_dependency_review_workflow.py` file to prove the action remains SHA-pinned, `fail-on-severity: high` remains intact, workflow self-coverage remains intact, and the admission steps stay hard-fail.

## Phase 3: Doctrine scope note

### Affected Files

- `qor/references/doctrine-dependency-admission.md` - name `requirements-sbom.txt` as a governed lockfile, record the lockfile-only scope of the CI step, and correct stale "manual"/"deferred" enforcement wording.
- `qor/references/glossary.md` - correct the stale `dependency-admission-lint` definition (single lockfile, WARN-only).

### Changes

In `## Purpose`, add `requirements-sbom.txt` (the hash-pinned SBOM toolchain lockfile installed by the release build) to the parenthetical naming the release dependency tree. After the Phase 107 paragraph, add one `**Phase 298 lockfile coverage**:` paragraph stating: the CI admission step runs once per governed root lockfile via `--lockfile`; the threshold and override procedure are unchanged; the CLI entry point does not pass `pyproject.toml` to the pyproject pin walk, so pyproject pins are not examined in CI (declared residual).

Correct two stale statements that contradict the Phase 107 hard-fail enforcement:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/references/doctrine-dependency-admission.md | grep -nE 'The check is currently manual'` -> `43:The check is currently manual. Automated enforcement is a non_goal`

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/references/doctrine-dependency-admission.md | grep -nE 'threshold is deferred to a future hygiene phase'` -> `114:threshold is deferred to a future hygiene phase.`

Rewrite the paragraph at line 43 in past tense: at Phase 103 the check was manual; Phase 105 added `qor/scripts/dependency_admission_lint.py`, and Phase 107 made it hard-fail in `pr-dependency-review.yml`. Rewrite the Authority clause ending at line 114 to state that automated enforcement of the 14-day threshold is operative in `pr-dependency-review.yml`, for the governed root lockfiles only. No threshold, override or policy wording changes.

The glossary entry for `dependency-admission-lint` still describes the Phase 105 wiring. It says the lint walks one lockfile and is WARN-only:

`git show 43ee76b7ed561a308eaeab0844044c7642e02efd:qor/references/glossary.md | grep -nE '^term: dependency-admission-lint$'` -> `922:term: dependency-admission-lint`

Line 923 is that entry's `definition:`. It contains the phrases `walks the requirements-release.txt lockfile diff` and `Wired WARN-only in .github/workflows/pr-dependency-review.yml`; the line is long and is quoted in part here. Edit only that `definition:` value. Say the lint walks the lockfile named by `--lockfile` (default `requirements-release.txt`), and that `pr-dependency-review.yml` runs it hard-fail (Phase 107), once per governed root lockfile (Phase 298). Keep `term`, `home`, `referenced_by` and `introduced_in_plan` unchanged. The lint module docstring carries the same stale wording, but it is code and stays out of scope (non-goal).

### Unit Tests

- None added. Documentation-only change; `tests/test_doctrine_dependency_admission.py` must stay green (threshold, override, workflow reference, SSDF assertions unchanged), and `tests/test_dogfood_glossary_coverage.py`, which parses the real glossary, must stay green.

## Phase 4: Release-state continuity

### Affected Files

- `docs/release-state.json` - append the `0.175.1` `sealed_unpublished` entry (LD-11).

### Changes

Append the LD-11 entry as the last element of `exceptions`, with the same key order and indentation as the existing entries. No other entry changes. No CHANGELOG section, ledger entry or tag is written by this phase; `/qor-substantiate` stamps `[0.175.2]` and records the seal.

### Unit Tests

- None added. The record is data consumed by the existing suite. TDD classification: regression coverage backfill is not needed, because `tests/test_release_state.py::test_disposition_exempts_only_the_named_version` and `tests/test_release_state.py::test_sealed_unpublished_version_with_local_tag_is_clean` already prove the rule the entry relies on (LD-11).
- At `/qor-implement`, `python -m pytest tests/test_release_state.py tests/test_changelog_tag_coverage.py -q` stays GREEN, which proves the record still validates with the new entry.
- At `/qor-implement`, the CI-view simulation in `## CI Commands` models the post-seal state (project version `0.175.2`, remote tags only). On the current base, before the entry exists, it prints `{'0.175.1'} {'0.175.1'}` (observed while authoring iterations 1 and 2): the gap is RED. After the entry is appended it reports no orphans with the entry. With `0.175.1` removed from the loaded exceptions in memory, it reports exactly `{'0.175.1'}`. That shows the entry is what keeps coverage green.
- Post-seal verification: the substantiating operator runs the guarded CI-view clone proof in `## CI Commands` after `/qor-substantiate` Step 9.5.5 (seal commit and local `v0.175.2` tag exist) and before Step 9.6 (push/merge). It must exit 0, which requires the guard to pass, pytest to pass, and no test to be skipped. It clones the seal commit, so it proves the committed bump, stamp and entry together. The operator records the observed output in the substantiation hand-off report. A non-zero exit blocks Step 9.6; the legal next action is `/qor-remediate`, and the seal is not pushed. Running it before the seal commit is not a substitute: the guard fails there by design.
- Proof that the post-seal verification discriminates (observed while authoring iteration 2, in a scratch clone of this branch outside the repository, with `origin` set to the real remote; the seal commits were simulated there and never entered this repository):
  - implement-state commit (this branch's head, `version = "0.175.1"`), no entry: exit 1, and the guard prints `CI-view guard FAIL: clone is not a sealed 0.175.2 (project version 0.175.1)`. The unguarded iteration-1 command reports `4 passed` on the same commit, which is the vacuous pass VETO #815 V2 found;
  - a commit that bumps `version` to `0.175.2` without the `[0.175.2]` CHANGELOG stamp: exit 1, `CI-view guard FAIL: clone is not a sealed 0.175.2 (project version 0.175.2)`;
  - simulated seal commit (`version = "0.175.2"`, `## [0.175.2] - ` section, local `v0.175.2` tag), no `0.175.1` entry: exit 1, `1 failed, 3 passed`, and `test_every_changelog_section_has_tag` reports orphan `0.175.1`;
  - the same seal commit with the LD-11 entry added: exit 0, `4 passed`, and the same result on a second run.

## Definition of Done

### Deliverable: complete Dependency Review root-path and lockfile coverage

- **D1**: every change to a governed root dependency file (derived per LD-2) triggers `PR Dependency Review`, and every governed root lockfile is examined by a hard-fail cooling-period admission step. "Examined" means the step names the lockfile via `--lockfile` and `main` diffs that lockfile against the same path at `--base` (LD-9). Pyproject pin examination in CI is a declared residual (LD-7).
- **D2**: `.github/workflows/pr-dependency-review.yml` names `pyproject.toml`, `requirements-release.in`, `requirements-release.txt`, `requirements-sbom.in`, and `requirements-sbom.txt` under `pull_request.paths`, preserves `.github/workflows/**`, and carries one admission step per governed root lockfile passing `--base` and `--lockfile`, with no `if:` or `continue-on-error` on those steps or their job; the action pin, `fail-on-severity: high`, and hard-fail posture are unchanged.
- **D3**: Phase 298 follows canonical phase branch/plan resolution and receives truthful current-revision audit/substantiation evidence before promotion; no governance evidence is synthesized through the GitHub API. The doctrine records the sbom lockfile coverage and the pyproject residual, and no longer describes enforcement as manual or deferred. The `dependency-admission-lint` glossary definition no longer describes the lint as WARN-only or limited to `requirements-release.txt`.
- **D4**: `tests/test_pr_dependency_review_workflow.py::test_workflow_triggers_on_dependency_paths` and `tests/test_pr_dependency_review_workflow.py::test_admission_lint_runs_for_every_governed_lockfile` are RED before the workflow edit and GREEN afterward. `tests/test_dependency_admission_lint_cli.py::test_main_lockfile_arg_examines_named_lockfile` and `tests/test_dependency_admission_lint_cli.py::test_main_default_lockfile_does_not_examine_sbom_bump` are GREEN (regression coverage backfill), and each discriminating mutation in Phase 1 turns the first one RED. The full workflow test file passes on the implemented revision.

### Deliverable: release-state continuity for 0.175.1

- **D1**: after the Phase 298 seal bumps the project version to `0.175.2`, the superseded `0.175.1` (sealed on `main` at META_LEDGER #814, with no remote tag) stays covered by a truthful `sealed_unpublished` disposition. PR #522's superseded candidate never reached `main` and gets no entry (LD-10).
- **D2**: `docs/release-state.json` gains exactly one entry, `0.175.1` / `sealed_unpublished` with the LD-11 reason. No other entry and no code under `qor/` changes.
- **D3**: the entry is recorded by `/qor-implement`, and the seal changes the version from `0.175.1` to `0.175.2` (hotfix). No tag is pushed and nothing is published.
- **D4**: at `/qor-implement`, the CI-view simulation reports no orphans with the entry and `{'0.175.1'}` without it, and `tests/test_release_state.py` stays GREEN. After the seal commit and before push, the guarded post-seal clone proof passes on the seal commit: its guard confirms `[project].version` is `0.175.2` with a dated `[0.175.2]` CHANGELOG section, and `tests/test_changelog_tag_coverage.py::test_every_changelog_section_has_tag` passes in the CI view (remote tags only), with no skip.

## CI Commands

- `python -m pytest tests/test_pr_dependency_review_workflow.py -q` - verifies derived trigger coverage, per-lockfile admission coverage, and unchanged dependency-review enforcement semantics.
- `python -m pytest tests/test_dependency_admission_lint_cli.py -q` - verifies `main` routes `--lockfile` to the current and base reads, with no network and a pinned clock.
- `python -m pytest tests/test_doctrine_dependency_admission.py -q` - verifies the doctrine edit keeps its contracted content.
- `for f in requirements-*.txt; do python -m qor.scripts.dependency_admission_lint --base origin/main --lockfile "$f" || exit 1; done` - runs each governed-lockfile admission step's command locally, over the same root `requirements-*.txt` set LD-2 derives. On a branch whose lockfiles equal `origin/main` the expected output is `_No lockfile bumps detected._` per lockfile; that local result is not admission evidence for #496 (LD-4).
- `python -m pytest tests/test_release_state.py tests/test_changelog_tag_coverage.py -q` - verifies the release-state record validates with the new entry and local tag coverage holds.
- `python -c "import subprocess; from pathlib import Path; from qor.scripts import release_state as rs; import tests.test_changelog_tag_coverage as t; remote = {l.rsplit('/', 1)[1] for l in subprocess.run(['git', 'ls-remote', '--tags', 'origin'], capture_output=True, text=True, check=True).stdout.split() if l.startswith('refs/tags/v') and not l.endswith('^{}')}; tags = {v for v in rs.merged_semver_tags(t.REPO) if 'v' + v in remote}; versions = t._changelog_versions() | {'0.175.2'}; ex = rs.load_release_state(t.RELEASE_STATE, versions); print(rs.coverage_violations(versions, tags, '0.175.2', ex).orphans, rs.coverage_violations(versions, tags, '0.175.2', {k: v for k, v in ex.items() if k != '0.175.1'}).orphans)"` - CI-view simulation of the post-seal state at `/qor-implement` (network: reads remote tag names only); expected output `set() {'0.175.1'}`.
- `(T=$(mktemp -d) && R=$(git ls-remote --tags origin | awk '{print $2}') && git clone -q --no-local . "$T/c" && git -C "$T/c" tag -l 'v*' | while read tg; do printf '%s\n' "$R" | grep -qx "refs/tags/$tg" || git -C "$T/c" tag -d "$tg" >/dev/null; done && cd "$T/c" && python -c "import sys, tomllib; v = tomllib.load(open('pyproject.toml', 'rb'))['project']['version']; c = open('CHANGELOG.md', encoding='utf-8').read(); sys.exit(0 if v == '0.175.2' and '## [0.175.2] - ' in c else 'CI-view guard FAIL: clone is not a sealed 0.175.2 (project version ' + v + ')')" && PYTHONPATH=. python -m pytest tests/test_changelog_tag_coverage.py -q -rs -p no:cacheprovider > "$T/out" 2>&1; rc=$?; cat "$T/out" 2>/dev/null; [ "$rc" -eq 0 ] && ! grep -q skipped "$T/out")` - post-seal verification: after `/qor-substantiate` Step 9.5.5 and before Step 9.6, runs the real tag-coverage suite in the CI view (remote tags only) on a clone of the seal commit. It fails unless the clone is a sealed `0.175.2`, and it fails on any skip.
- `python -m pytest tests/ -q` - verifies repository regression safety.
- `python qor/scripts/check_variant_drift.py` - verifies installed/generated variant consistency.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` - verifies the ledger chain.
- `python -m ruff check qor/ tests/` - lints the changed test file.
- `python -m qor.scripts.publication_boundary_lint --repo-root .` - verifies the publication-boundary surface remains clean.

## CI Coverage Exemptions

- `python -m qor.reliability.seal_entry_check` - seal-time check; runs at `/qor-substantiate`, not affected by a workflow/test/doctrine edit.
- `python -m qor.reliability.ledger_base_currency` - WARN-only ledger freshness; not affected by this plan.
- `python -m qor.reliability.gate_chain_completeness` - sealed-phase gate-chain check; runs at seal.
- `python -m qor.reliability.intent_lock_committed` - sealed-phase intent-lock check; runs at seal.
- `python -m qor.scripts.seal_artifacts` - seal-artifact currency; runs at seal.
- `python -m qor.scripts.gate_provenance` - sealed-phase provenance verify/attest; runs at seal and in CI with a secret.
- `python -m qor.scripts.status_json --self-test` - nightly health self-test; not affected by this plan.
- `tests/test_packaging_install.py` - packaging integration smoke; no packaging surface changes.

## Non-goals

- dependency version changes;
- dependency-policy redesign (threshold, override, severity);
- changes to `dependency_admission_lint` code, including wiring pyproject pins through its CLI entry point;
- weakening or bypassing Dependency Review;
- merging #496 through the pre-fix enforcement gap;
- release-state dispositions for any version other than `0.175.1`, changes to `qor/scripts/release_state.py`, remote tag pushes, or publication;
- reusing PR #522's audit, implementation or seal evidence as authority on this branch;
- hand-issuing governance evidence;
- unrelated repository cleanup.
