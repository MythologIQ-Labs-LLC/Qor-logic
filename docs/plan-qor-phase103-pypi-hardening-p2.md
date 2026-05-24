# Plan: Phase 103 — PyPI Publication Hardening P2 (GH #118 close)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #118 P2 controls per `docs/research-brief-gh118-pypi-hardening-2026-05-24.md`

**high_risk_target**: true

**impact_assessment**: This phase closes the final two remaining acceptance items from GH #118: post-publish PyPI pull-back verification and a cooling-period dependency-admission doctrine. Failure modes touched: (1) a successful PyPI publish that did not actually deliver the intended artifact (cache poisoning, mirror divergence, accidental overwrite) -- mitigated by post-publish `pip download` of the just-published version and SHA-256 comparison against the locally-produced `dist/SHA256SUMS`; (2) a malicious package published very recently entering the release dependency tree via an unguarded transitive update -- mitigated by the new dependency-admission doctrine declaring a minimum age threshold for new transitive dependencies plus an emergency-override procedure. SSDF: PS.2.1 (verify software release integrity), PS.3.1 (archive and protect each software release), PW.4.4 (review and analyze human-readable source code), RV.1.1 (identify and confirm vulnerabilities on an ongoing basis). EU AI Act / NIST AI RMF: out of scope.

**boundaries**:
- limitations: P2 scope only. Adds a post-publish verification step to the publish job of `.github/workflows/release.yml` that runs `pip download --no-deps qor-logic==<VERSION>`, computes SHA-256 of the downloaded wheel + sdist, and `sha256sum -c`-compares against the build-job-produced `dist/SHA256SUMS` records. Adds new doctrine `qor/references/doctrine-dependency-admission.md` declaring the cooling-period policy + emergency-override procedure + check mechanics. Adds 2 structural tests on the workflow YAML + 3 doctrine-content tests (presence, required sections, term-glossary inclusion if applicable).
- non_goals: automated cooling-period enforcement tooling (P2 ships doctrine; automated check deferred to a future hygiene phase); admin-bypass disable (still not API-exposed); Action major-version bumps; broaden CODEOWNERS reviewers; cyclonedx-bom hash-pinning (carry-forward non_goal from Phase 102); Dependabot config for `github-actions` ecosystem (separate hygiene phase).
- exclusions: no changes to the build/publish job split topology, the SHA pins, the lockfile content, the CODEOWNERS rules, or the dependency-review workflow established in Phases 101/102.

## Open Questions

None. Research brief + Phase 101/102 ledger entries mapped P2.

## Feature Inventory Touches

Empty. Workflow step addition + new doctrine doc + tests.
`feature_inventory_touches`: `[]`.

## Design notes

### Post-publish pull-back verification (F-4b)

After `pypa/gh-action-pypi-publish` succeeds and before `gh release create` runs, the publish job:

1. Extracts the version from `$GITHUB_REF_NAME` (strip leading `v`).
2. Polls PyPI's simple index with bounded retries (max 6 attempts at 10s intervals = 60s) until the version is observable. The PyPI Simple API at `https://pypi.org/simple/qor-logic/` reflects new releases within seconds typically.
3. Runs `pip download --no-deps --dest=/tmp/pypi-verify --no-cache-dir qor-logic==<VERSION>` to fetch the wheel and sdist from PyPI.
4. For each downloaded file, computes `sha256sum` and looks up the expected SHA from the build-produced `dist/SHA256SUMS`. Fails the step if any hash mismatches.

If a mismatch is detected, the workflow exits non-zero -- the GitHub release is NOT created, the audit chain is preserved, and the operator investigates. The mismatch case is rare but high-signal: it indicates either a PyPI-side error, a mid-publish replacement attack, or a workflow bug.

The polling loop is bounded; on timeout the step fails with a clear diagnostic. The retry interval is short enough that 60s total is comfortably within the 6-hour GitHub Actions job timeout.

### Cooling-period dependency-admission doctrine (F-3c)

New `qor/references/doctrine-dependency-admission.md` declares:

- **Minimum age threshold**: a transitive dependency newly entering the release dependency tree must have a release age of at least **14 days** at the time of the merge.
- **Check mechanic**: when regenerating `requirements-release.txt` via `pip-compile`, the operator (or future tooling) checks each newly-added or version-bumped entry against the upload time on PyPI (`pip index versions <pkg> --json` or `https://pypi.org/pypi/<pkg>/json`). Bumps within the 14-day window require justification or an override.
- **Emergency override procedure**: a documented exception path with three components — (1) a META_LEDGER entry stamped `DEPENDENCY_ADMISSION_OVERRIDE` with rationale (CVE patch, blocking incident, etc.); (2) opt-in PR label `dep-admit-override` that the reviewer applies; (3) a follow-up scheduled re-evaluation within 30 days.
- **Rationale**: prevents supply-chain attacks that exploit the freshness window when a compromised maintainer or hostile typosquat publishes a malicious update. The 14-day window is a defensible compromise between security (longer is safer) and developer velocity (shorter is faster).
- **Coordination with dependency-review-action**: the Phase 102 `pr-dependency-review.yml` workflow catches severity-graded vulnerabilities; this doctrine catches the freshness vector orthogonally.

Doctrine is reference material (not a step in any skill), advisory until tooling is built. Phase 103 ships the doctrine; future tooling is a non_goal.

### Test surface

5 new tests across two files.

1. `tests/test_release_workflow_immutability.py` (AMENDED)
   - `test_release_workflow_publish_job_verifies_via_pypi_pullback` -- publish job contains a step that runs `pip download` from PyPI and `sha256sum -c` against `dist/SHA256SUMS`, after `pypa/gh-action-pypi-publish` and before `gh release create`
   - `test_pypi_pullback_step_has_bounded_retry` -- the pull-back step uses bounded retries (no infinite loop); script asserts presence of a retry-bound mechanism (`for i in 1 2 3 4 5 6` or similar) and a sleep delay
2. `tests/test_doctrine_dependency_admission.py` (NEW)
   - `test_doctrine_file_exists` -- `qor/references/doctrine-dependency-admission.md` present
   - `test_doctrine_declares_minimum_age_threshold` -- doctrine prose names "14 days" minimum age explicitly
   - `test_doctrine_declares_override_procedure` -- doctrine prose names the override mechanism (ledger entry, PR label, follow-up window)

## Phase 1: pull-back verification + dependency-admission doctrine + tests

### Affected Files

- `.github/workflows/release.yml` -- AMENDED. Publish job: add post-publish pull-back verification step between `pypa/gh-action-pypi-publish` and `gh release create`.
- `qor/references/doctrine-dependency-admission.md` -- NEW. ~70 lines doctrine + override procedure.
- `tests/test_release_workflow_immutability.py` -- AMENDED. 2 new tests.
- `tests/test_doctrine_dependency_admission.py` -- NEW. 3 tests.
- `docs/plan-qor-phase103-pypi-hardening-p2.md` -- NEW. This plan.

### Unit Tests

See "Test surface" above. 5 new test functions across 1 new file + 1 amendment.

### Changes

#### `.github/workflows/release.yml` (AMEND publish job)

Insert between the `pypa/gh-action-pypi-publish` step and the `Attach evidence bundle to GitHub release` step:

```yaml
      - name: Verify published artifact via PyPI pull-back
        run: |
          set -euo pipefail
          VERSION="${GITHUB_REF_NAME#v}"
          echo "Verifying qor-logic==${VERSION} via PyPI pull-back"
          mkdir -p /tmp/pypi-verify
          for i in 1 2 3 4 5 6; do
            if pip download --no-deps --dest=/tmp/pypi-verify --no-cache-dir \
                "qor-logic==${VERSION}" 2>&1; then
              echo "PyPI pull-back succeeded on attempt ${i}"
              break
            fi
            if [ "$i" = "6" ]; then
              echo "::error::PyPI pull-back failed after 6 attempts (60s); aborting"
              exit 1
            fi
            sleep 10
          done
          cd /tmp/pypi-verify
          sha256sum *.whl *.tar.gz > /tmp/pypi-pullback-sums
          # Compare against the build-produced sums (filtering to artifact lines only)
          grep -E '\.whl$|\.tar\.gz$' "${GITHUB_WORKSPACE}/dist/SHA256SUMS" \
              > /tmp/expected-sums
          if ! diff -u <(sort /tmp/expected-sums) <(sort /tmp/pypi-pullback-sums); then
            echo "::error::PyPI pull-back SHA mismatch -- published artifact differs from locally-built artifact"
            exit 1
          fi
          echo "Pull-back verification PASS"
```

#### `qor/references/doctrine-dependency-admission.md` (NEW)

```markdown
# Doctrine: Dependency Admission

## Purpose

Govern when a newly-published or version-bumped transitive dependency
may enter the release dependency tree (`requirements-release.txt`,
`requirements-sbom.txt` if added later, or direct deps in
`pyproject.toml`).

## Policy

### Minimum age threshold

A transitive dependency entering the release tree -- either as a new
addition or as a version bump -- must have a release age of at least
**14 days** at the time of the merge to `main`.

The 14-day window is a defensible compromise between security
(longer is safer; longer windows give the broader ecosystem time to
detect compromise) and developer velocity (shorter is faster).
The window is calibrated to be wider than the median PyPI
yanking-after-publish window (a few days) and narrower than the
"too slow to react to security patches" range (months).

### Check mechanic

When regenerating `requirements-release.txt` via
`pip-compile --generate-hashes`, the operator (or future tooling)
checks each newly-added or version-bumped entry against the upload
time on PyPI:

- Query `https://pypi.org/pypi/<pkg>/<version>/json`
- Read the top-level `upload_time` or `releases[<version>][0].upload_time`
- If `(now - upload_time).days < 14`, the dependency is in the
  cooling-period window

The check is currently manual. Automated enforcement is a non_goal
of Phase 103; a future hygiene phase may add a lint that walks
`requirements-release.txt` and the diff against the previous merge
to detect within-window admissions.

### Emergency override procedure

A documented exception path exists for cases where a bump within
the 14-day window is justified (CVE patch, blocking-incident fix,
upstream maintainer-coordinated security release):

1. **META_LEDGER entry**: a phase IMPLEMENTATION or HOTFIX entry must
   carry a `**Dependency admission override**:` line naming the
   package, the within-window version, the upload age in days, and
   the justification (CVE id, incident reference, etc.).
2. **PR label**: the operator applies the `dep-admit-override` label
   to the PR. The reviewer's CODEOWNERS approval ratifies the
   override.
3. **Follow-up re-evaluation**: a scheduled re-check at 30 days
   post-merge confirms the override target has not been yanked or
   superseded. If yanked, the next hotfix removes or replaces the
   override target.

### Coordination with dependency-review-action

The `pr-dependency-review.yml` workflow (Phase 102) catches
severity-graded vulnerabilities. This doctrine catches the
freshness vector orthogonally. A dependency may pass severity review
but fail cooling-period admission if it is newer than 14 days;
both gates fire independently.

## Rationale

Supply-chain attacks exploit the freshness window when a compromised
maintainer or hostile typosquat publishes a malicious update. The
window between "package published" and "ecosystem detects compromise"
is the danger interval; admitting within-window updates expands the
blast radius. The 14-day delay does not eliminate the attack class
but it shifts the economics: an attacker must either evade detection
for two full weeks or accept reduced reach.

## SSDF mapping

- **PS.2.1** -- Verify software release integrity.
- **PW.4.4** -- Review and analyze human-readable source code.
- **RV.1.1** -- Identify and confirm vulnerabilities on an ongoing basis.

## Authority

This doctrine is reference material. Override procedure is operative;
automated enforcement deferred.
```

## Definition of Done

### Deliverable D-103.1: Post-publish PyPI pull-back verification

- **D1**: `release.yml` publish job carries a `Verify published artifact via PyPI pull-back` step between `pypa/gh-action-pypi-publish` and `Attach evidence bundle to GitHub release`.
- **D2**: The step runs `pip download` with bounded retries (6 attempts at 10s intervals) and `sha256sum`-compares against build-produced SHA256SUMS.
- **D3**: `test_release_workflow_publish_job_verifies_via_pypi_pullback` and `test_pypi_pullback_step_has_bounded_retry` pass.

### Deliverable D-103.2: Dependency-admission doctrine

- **D1**: `qor/references/doctrine-dependency-admission.md` exists with Policy, Override procedure, and Rationale sections.
- **D2**: `test_doctrine_file_exists`, `test_doctrine_declares_minimum_age_threshold`, `test_doctrine_declares_override_procedure` all pass.

## CI Coverage Exemptions

None.

## CI Commands

- `python -m pytest tests/test_release_workflow_immutability.py -q` -- amended Phase 101 + 102 + 103 tests.
- `python -m pytest tests/test_doctrine_dependency_admission.py -q` -- Phase 103 doctrine tests.
- `python -m pytest tests/ -v` -- full regression.
- `python qor/scripts/check_variant_drift.py` -- ci.yml.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` -- ci.yml.
- `python -m pytest tests/test_packaging_install.py -v -m integration` -- install-smoke.
- `python -m qor.reliability.gate_chain_completeness --phase-min 52` -- gate-chain.
- `python qor/scripts/pr_citation_lint.py` -- pr-lint.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase103-pypi-hardening-p2.md` -- plan-internal.
- `python -m qor.scripts.ci_coverage_lint --plan docs/plan-qor-phase103-pypi-hardening-p2.md --workflows-dir .github/workflows` -- Phase 89 ci-coverage.
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase103-pypi-hardening-p2.md` -- Phase 92 DoD check.
- `python -m qor.scripts.skill_size_budget_lint --skills-root qor/skills` -- Phase 95 skill-corpus-budget lint (WARN-only).
