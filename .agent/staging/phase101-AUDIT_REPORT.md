# AUDIT REPORT — Phase 101 (PyPI Hardening P0)

**Plan**: `docs/plan-qor-phase101-pypi-hardening-p0.md`
**Auditor**: Judge (qor-audit, invoked from /qor-auto-dev-1)
**Date**: 2026-05-24
**Risk Grade**: L3 (declared `high_risk_target: true`)
**Verdict**: **PASS**
**Iteration**: 1

---

## Step 0.3 — Plan-Iteration Lint

- `plan_text_consistency_lint` — exit 0
- `ci_coverage_lint` — exit 0
- `dod_check` — exit 0

No ABORT.

## Step 3 — Adversarial Passes

### Pass 1: Prompt Injection

Scan of the plan and proposed script content for adversarial-instruction patterns (system-prompt overrides, jailbreak fragments, role-reversal attempts, fenced "ignore previous" tokens). The new YAML and Python content contain no such patterns. The `configure_pypi_environment.py` script accepts only typed argparse inputs (`--repo`, `--reviewer-id int`, `--reviewer-type` choice-bounded, `--dry-run` flag) and passes a structured JSON body via stdin to `gh api`, so no user-controlled string reaches a shell-interpolation boundary. **PASS.**

### Pass 2: L3 Risk Grade

L3 conditions tripped (security-critical path — release publication, OIDC mint). Required contracts on plan:
- `high_risk_target: true` — declared.
- `impact_assessment:` block — present; identifies 3 named failure modes with paired mitigations and maps to SSDF practices PO.4.1, PO.5.1, PS.2.1, PS.3.1.
- Fundamental-rights / safety / financial / employment / education / essential-services scope — explicitly N/A in the impact assessment, supply-chain only.

**PASS.**

### Pass 3: OWASP Top-10

- **A01 Broken Access Control**: `id-token: write` reduced from workflow-level to publish-job-only; `pypi` environment gains reviewer + tag-only deployment policy. Improvement, no new exposure.
- **A02 Cryptographic Failures**: SHA-256 used for both action pinning (commit identity) and artifact integrity (SHA256SUMS). Appropriate.
- **A03 Injection**: New script uses `subprocess.run([...], input=json.dumps(body))` with list-form argv and stdin JSON; no shell, no string interpolation of operator input into argv. List-form argv plus typed argparse covers the SG-ArgInjectionBlindSpot-A shape from prior Shadow Genome.
- **A04 Insecure Design**: Two-job split with artifact handoff verified by in-band SHA256SUMS is defense-in-depth. Tag-ancestry guard runs in both jobs (load-bearing-gate preservation, per qor-substantiate Constraints). Pattern explicitly addresses the SG-StructureWithoutPolicy-A finding from research brief.
- **A05 Security Misconfiguration**: Cache disabled on privileged publish job; setup-python removed from publish job entirely; minimal `contents: read` on build job.
- **A06 Vulnerable Components**: SHA-pinning is the direct mitigation — replaces mutable tag refs (worst case: `@release/v1` branch ref) with frozen commit SHAs.
- **A07 ID & Auth Failures**: Required-reviewer rule on `pypi` environment plus deployment-branch restriction to `v*.*.*` tag refs.
- **A08 Software & Data Integrity**: SHA256SUMS handoff between build and publish jobs; `sha256sum -c` runs in publish before `pypa/gh-action-pypi-publish` invocation; tag-ancestry guard preserved.
- **A09 Security Logging Failures**: `configure_pypi_environment.py` prints the PUT body before invocation; substantiate seal entry records the gh-api invocation outcome. Adequate for P0; richer release-evidence bundle is P1 scope.
- **A10 SSRF**: N/A — no fetch of arbitrary URLs introduced.

**PASS.**

### Pass 4: Ghost-UI / Razor / Self-Application

- **Ghost-UI**: no UI introduced.
- **Razor — function length**: all new functions < 40 lines (`build_put_body` ~10 lines, `main` ~30 lines, `build_branch_policy_body` 2 lines).
- **Razor — file length**: rewritten `release.yml` ~70 lines (was ~40); `configure_pypi_environment.py` ~80 lines; test files projected ~120 lines each. All < 250.
- **Razor — nesting**: max depth 3 in `main()` (try... not used; only sequential subprocess calls). YAML nesting matches existing project workflows.
- **Self-application**: the plan's own structural rules are enforced by the new tests. The discipline being added (SHA pins, split jobs, env protection) is also what the tests assert. The plan applies its own discipline.

**PASS.**

### Pass 5: Test Functionality (Phase 79)

For each new test, what behavior does it verify?
- `test_release_workflow_actions_sha_pinned` — verifies the **policy property** that every `uses:` line uses a 40-hex commit SHA (the property being enforced). Behavior = workflow uses immutable refs. Functional, not presence-only.
- `test_release_workflow_split_jobs` — verifies the **topology property** that build and publish are separate jobs with `needs:` dependency. Behavior = artifact-producing job and OIDC-minting job cannot share execution context.
- `test_release_workflow_id_token_scoped_to_publish_job` — verifies the **permission-scope property** that the OIDC permission appears nowhere outside the publish job. Behavior = no other job can mint a PyPI publish token.
- `test_release_workflow_publish_job_disables_cache` — verifies the **cache-isolation property** that the privileged job consumes no restorable cache state. Behavior = cache poisoning cannot affect publish.
- `test_release_workflow_artifact_handoff_with_sha_verify` — verifies the **integrity-handoff property** that publish downloads + verifies SHA256SUMS before publishing. Behavior = artifact tampering between jobs is detected.
- `test_configure_pypi_environment_*` — verifies the PUT-body factory produces the correct gh-api shape (reviewer requirement, tag-only branch policy, idempotency). Behavior = the script will configure GitHub correctly when invoked.

Borderline observation: workflow structural tests verify policy properties, not runtime workflow execution. The "behavior" of a CI workflow IS its structure, so this is the closest the unit-test layer can approach without spinning up `act` or a workflow-runner. Plan correctly notes that integration-tier behavior is covered by the existing `tests/test_packaging_install.py -m integration` smoke. Acceptable.

**PASS.**

### Pass 6: Filter-Stage

Plan's Affected Files list enumerates exactly the files that will be written/modified. The implementation will stage only those files. No broad-glob staging proposed. `tests/test_release_workflow_guard.py` amendment is declared in Affected Files; no other existing file will be silently mutated. **PASS.**

### Pass 7: Infrastructure Alignment (grep-verify)

Confirmed real-infrastructure references:
- `actions/checkout`, `actions/setup-python`, `actions/upload-artifact`, `actions/download-artifact`, `pypa/gh-action-pypi-publish` — all real, all SHAs queried live via `gh api repos/<owner>/<repo>/git/ref/tags/<tag>` and resolved.
- `repos/{owner}/{repo}/environments/{env}` PUT endpoint — real GitHub REST API.
- `repos/{owner}/{repo}/environments/{env}/deployment-branch-policies` POST endpoint — real GitHub REST API.
- `qor.scripts.plan_text_consistency_lint`, `qor.scripts.ci_coverage_lint`, `qor.scripts.dod_check` — verified to run (exit 0) above.
- All file paths exist (existing files: `.github/workflows/*.yml`, `tests/test_release_workflow_guard.py`) or are declared NEW.

**PASS.**

### Pass 8: Runtime Contract Walk (V2, WARN-only per Phase 99)

WARN-only ramp. The plan's commands in the CI Commands section grep-resolve to actual modules and real workflow files. The shell snippets in the new `release.yml` (`git merge-base`, `sha256sum`, `sha256sum -c`) are POSIX-standard and present on `ubuntu-latest`. No runtime-contract drift detected. **WARN-only, no VETO contribution.**

### Pass 9: Feature Test Declaration

Each deliverable in `## Definition of Done` declares its test(s):
- D-101.1 → `test_release_workflow_actions_sha_pinned`, `test_ci_workflow_actions_sha_pinned`, `test_pr_lint_workflow_actions_sha_pinned`
- D-101.2 → five split-jobs tests + amended ancestry test
- D-101.3 → four PUT-body tests + post-state verify via `gh api ... | jq` in substantiate

**PASS.**

---

## Verdict

**PASS (L3, iter-1).** Implementation may proceed.

## Non-blocking Observations (decision log)

1. **Workflow-level integration test** would strengthen Pass 5 from "structural" to "behavioral" but requires `act` or a runner harness — out of scope for P0. Consider in a future phase if a workflow regression slips past structural tests.
2. **Admin-bypass disable** is not yet API-exposed for environment-level PUT body in the current GitHub REST API; documented in plan as a manual UI step + P1 follow-up. Operator should disable admin bypass in the UI as a one-time action after the script runs.
3. **Single reviewer** is the initial protection level; broaden as team grows. Not a P0 blocker.
