# Doctrine: Dependency Admission

## Purpose

Govern when a newly-published or version-bumped transitive dependency
may enter the release dependency tree (`requirements-release.txt` or
direct deps in `pyproject.toml`).

This doctrine catches a class of supply-chain attacks orthogonal to
severity-graded vulnerability review: the **freshness vector**, where
a compromised maintainer account or hostile typosquat publishes a
malicious update and a downstream project ingests it before the
broader ecosystem detects the compromise.

## Policy

### Minimum age threshold

A transitive dependency entering the release tree -- either as a new
addition or as a version bump -- must have a release age of at least
**14 days** at the time of the merge to `main`.

The 14-day window is a defensible compromise between security
(longer is safer; longer windows give the broader ecosystem time to
detect compromise) and developer velocity (shorter is faster).
It is calibrated to be wider than the median PyPI yanking-after-publish
window (a few days) and narrower than the "too slow to react to
security patches" range (months).

### Check mechanic

When regenerating `requirements-release.txt` via
`pip-compile --generate-hashes`, the operator (or future tooling)
checks each newly-added or version-bumped entry against the upload
time on PyPI:

- Query `https://pypi.org/pypi/<pkg>/<version>/json`
- Read the top-level `urls[0].upload_time_iso_8601` (the wheel/sdist
  upload time) or `releases[<version>][0].upload_time_iso_8601`
- If `(now - upload_time).days < 14`, the dependency is in the
  cooling-period window and admission requires an override

The check is currently manual. Automated enforcement is a non_goal
of Phase 103; a future hygiene phase may add a lint
(`qor/scripts/dependency_admission_lint.py`) that walks
`requirements-release.txt` and the diff against the previous
`merge-base origin/main HEAD` to detect within-window admissions.

**Phase 105 tooling (V1, WARN-only)**: `python -m qor.scripts.dependency_admission_lint --base <ref>` runs the cooling-period check against the lockfile diff (queries `https://pypi.org/pypi/<pkg>/<version>/json` for `urls[0].upload_time_iso_8601`, bounded retry of 3 × 5s); `python -m qor.scripts.dep_admit_override_tracker` lists `**Dependency admission override**:` ledger entries due for 30-day re-evaluation. The lint runs WARN-only in `.github/workflows/pr-dependency-review.yml` on PRs touching `requirements-release.txt` (the step exits non-zero on violations but is wrapped with `|| true` so the workflow stays green). V2 will flip the WARN to hard fail once operator-evidence on false-positive rate accumulates.

**Phase 106 V1.1 extensions**: the lint now also accepts a `dep-admit-override` GitHub PR label as an override signal when running in CI context. CI is detected via the standard GitHub Actions env vars (`GITHUB_EVENT_NAME == "pull_request"`, `GITHUB_REPOSITORY`, `GITHUB_REF` parsed for the PR number); the lint shells out to `gh pr view <n> --repo <owner>/<name> --json labels` and treats the presence of `dep-admit-override` as an override (in addition to the existing META_LEDGER override check). **Fails open**: any gh non-zero exit emits a stderr fallback note and falls back to META_LEDGER-only — a failed network query must not introduce a spurious within-window violation when the operator has done the right thing via ledger entry. Operators bypass the gh query in local testing via `--skip-pr-labels`. Additionally, the cooling-period check now walks `[project] dependencies` and `[project.optional-dependencies]` in `pyproject.toml`, applying the 14-day threshold to entries pinned in PEP 440 exact form (`package==X.Y.Z`); range and unbounded specifiers are skipped because the resolved version is not knowable until install time. Both extensions are additive on top of the V1 lockfile + ledger surface.

**Phase 107 closure of all V2 carry-forward items**: V1.1 cooling-period lint **flipped to hard fail** in `pr-dependency-review.yml` (the `|| true` wrap was removed); the lint step's non-zero exit on real violations now blocks PR merge. The operator override path (META_LEDGER `**Dependency admission override**:` entry OR `dep-admit-override` PR label) remains operative as the safety valve. Range-pin **lower-bound coverage** was added: `parse_pyproject_range_pins(text)` extracts the lower bound from `>=X.Y.Z` and `~=X.Y.Z` specifiers in `[project] dependencies` and `[project.optional-dependencies]`; the lint applies the 14-day threshold to those lower-bound versions because pip's installer COULD resolve to that version on a fresh install. `<`, `!=`, and unbounded specifiers continue to be skipped. The override tracker gained `--emit-issue` (Phase 105 V2 calendar/GH-issue carry-forward closure): when run with the flag and the `--filter due` state has entries, the tracker invokes `gh issue create` with a rollup body listing all due entries under the `dep-admit-override-review` label; single rollup per invocation prevents spam. The Phase 102 `cyclonedx-bom` hash-pin carry-forward was closed via a new `requirements-sbom.in` + `requirements-sbom.txt` (the latter exempted from the Razor 250-line file budget per the Phase 107 plan's explicit exemption block — autogenerated lockfile, size tracks dependency graph not authoring complexity); the release workflow's build job uses `pip install --require-hashes -r requirements-sbom.txt` in place of the prior unpinned install. With Phase 107 sealed, all five Phase 105 V2 carry-forward items have shipped or been documented as deliberate operational decisions; the dep-admit V2 carry-forward list is empty.

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
   override target. The re-evaluation lands as a brief
   `**Dependency admission follow-up**:` line in the next phase's
   IMPLEMENTATION ledger entry.

### Coordination with dependency-review-action

The `.github/workflows/pr-dependency-review.yml` workflow (Phase 102)
catches severity-graded vulnerabilities via
`actions/dependency-review-action` failing on `high` severity.
This doctrine catches the freshness vector orthogonally. A dependency
may pass severity review but fail cooling-period admission if it is
newer than 14 days; both gates fire independently.

## Rationale

Supply-chain attacks exploit the freshness window between
"package published" and "ecosystem detects compromise." Admitting
within-window updates expands the blast radius. The 14-day delay
does not eliminate the attack class but shifts the economics: an
attacker must either evade detection for two full weeks or accept
reduced reach.

Recent industry examples illustrating this attack pattern: PyPI
typosquatting waves (where malicious packages live for days before
detection); npm crypto-wallet stealer campaigns (where compromised
maintainer accounts publish weaponized minor versions); the broader
class catalogued by the PSF and ENISA as "fresh-publish supply-chain
attacks." Cooling-period admission is one of several layered
defenses (alongside vulnerability scanning, hash-pinned lockfiles,
SBOM attestation) recommended in NIST SP 800-218A.

## SSDF mapping

- **PS.2.1** -- Verify software release integrity.
- **PW.4.4** -- Review and analyze human-readable source code.
- **RV.1.1** -- Identify and confirm vulnerabilities on an ongoing
  basis.

## Authority

This doctrine is reference material. Override procedure is operative
(operators MUST carry the `**Dependency admission override**:` line
on within-window admissions); automated enforcement of the 14-day
threshold is deferred to a future hygiene phase.
