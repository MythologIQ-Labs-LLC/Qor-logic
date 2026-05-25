# AUDIT REPORT — Phase 104 (Release publish-step fix)

**Plan**: `docs/plan-qor-phase104-release-publish-fix.md`
**Auditor**: Judge (qor-audit)
**Date**: 2026-05-25
**Risk Grade**: L3 (declared `high_risk_target: true`)
**Verdict**: **PASS**
**Iteration**: 1

---

## Step 0.3 — Plan-Iteration Lint
All three exit 0 (plan_text_consistency_lint, ci_coverage_lint, dod_check). No ABORT.

## Step 3 — Adversarial Passes

**1 Prompt Injection**: New workflow snippet uses `set -euo pipefail`; `cp` arguments are literal glob patterns; no operator-controlled string reaches a shell-interpolation boundary. **PASS.**

**2 L3 Risk Grade**: high_risk_target declared; impact_assessment names 2 failure modes paired with mitigations (regression of the original bug; future-phase leak). SSDF PS.2.1, PS.3.1, RV.1.1 declared. **PASS.**

**3 OWASP Top-10**: A04 Insecure Design — explicit separation of assembly directory (`dist/`) from delivery directory (`dist-publish/`) is the structural countermeasure that addresses the cluster's design oversight. A08 Software & Data Integrity — the publish payload is now narrowly scoped to wheel+sdist; SHA256SUMS verify still runs in `dist/` before the copy. Other A0X surfaces unchanged. **PASS.**

**4 Ghost-UI / Razor / Self-Application**: No UI. Added step ~5 bash lines; release.yml now ~150 lines (<250). Self-application: the bug was a "structure missing policy" instance (dist directory had no policy on what could enter it); the fix imposes the missing policy via a dedicated delivery directory. Same SG-StructureWithoutPolicy-A pattern documented in the cluster research brief, now applied at the dist-payload surface. **PASS.**

**5 Test Functionality**: Each test verifies a behavioral property: publish step uses a separate `packages-dir` (not `dist/`); prepare step copies only wheel/sdist (not SHA256SUMS, sbom.json, evidence.json); Dependabot config covers both ecosystems with supported schedule intervals. Structure-as-behavior for declarative config, pattern accepted in Phases 101-103. **PASS.**

**6 Filter-Stage**: Affected Files list is exact. **PASS.**

**7 Infrastructure Alignment (grep-verify)**: `pypa/gh-action-pypi-publish@v1.14.0` accepts `with.packages-dir`. `cp` and shell glob expansion are POSIX-standard on `ubuntu-latest`. Dependabot config v2 syntax is documented at docs.github.com. **PASS.**

**8 Runtime Contract Walk (V2, WARN-only)**: No new runtime contracts; the prepare step runs in the build job (already validated). **WARN-only.**

**9 Feature Test Declaration**: D-104.1 → 2 tests on the prepare step + packages-dir; D-104.2 → 3 tests on Dependabot config. **PASS.**

---

## Verdict

**PASS (L3, iter-1).** Implementation may proceed.

## Non-blocking Observations

1. The v0.69.0/v0.70.0/v0.71.0 tags remain as historical artifacts pointing at commits with the broken release.yml. They cannot be re-used (PyPI never claimed those versions, so technically reusable, but operationally messy). Phase 104 ships as v0.72.0; CHANGELOG documents the v0.69-v0.71 publish-step bug.
2. Dependabot config is a cluster carry-forward; folding it into the hotfix avoids a separate trivial PR cycle.
3. The `Prepare publish-only directory` step is a structural minimum; a future hardening phase could replace `cp` with an explicit allowlist + checksum re-verification on the copied files. Not required for the cluster's stated objectives.
