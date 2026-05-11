# Doctrine: Host-repo posture

A "host-repo posture" is the set of assumptions a Qor-logic lifecycle skill makes about the consuming repository — Python toolkit modules, `pyproject.toml`, Keep-a-Changelog format, version source. These assumptions are calibrated for Qor-logic's own release shape and silently break when invoked against a non-Python repo (TypeScript / Rust / Go / hybrid).

Source incident: GH #38 (operator ran `/qor-substantiate` against a React 18 + bun + Supabase repo; ~8 of ~15 ceremony steps silently no-opped or failed loudly mid-flight, producing a META_LEDGER seal entry that claimed completeness it didn't have).

## V1 contract (Phase 47)

Two mechanisms close the posture gap without a full pluggable-backend refactor:

1. **Per-step prerequisite declarations** (#38 option 1). Each `/qor-substantiate` step that depends on a Python toolkit module or a Python-shape artifact declares its prerequisites; missing prerequisites emit `prerequisite_absent` (severity-2 shadow event) and SKIP the step. The seal entry surfaces a `Prerequisites: N steps SKIPPED` line so the operator sees gate-state coverage at a glance.

2. **Install-freshness check** (B23). Each lifecycle skill (`/qor-plan`, `/qor-audit`, `/qor-implement`, `/qor-substantiate`) runs `host_capability.check_qor_logic_freshness(repo_root)` at session start. The check compares the host repo's `pyproject.toml` `qor-logic` version against `latest_known` (passed by caller or read from `.qor/freshness/latest_known`). Drift emits `qor_logic_stale_install` (severity-1, advisory WARN). Operator decides whether to run `qorlogic install --host <h> --scope <s>` before proceeding.

## Prerequisite skip behavior

When a step's prereq check fails (`check_step_prerequisites(...).can_proceed == False`):

1. Emit `prerequisite_absent` to `.qor/session/shadow.jsonl` (severity-2; details include step name and missing prereq list).
2. Skip the step body.
3. Surface in seal entry under `Prerequisites: N steps SKIPPED (step_4.6.5, step_7.4, ...)`.
4. Do NOT fail the substantiate cycle on prereq skips — the seal entry's transparency is the deterrent against silent no-ops.

The operator can see exactly which gates ran and which were prereq-deferred. This is the smallest possible posture-gap mitigation: no new pluggable backends, no two-track skill split, no contract changes for repos that DO have the Python toolkit.

## Install-freshness check behavior

`check_qor_logic_freshness(repo_root, latest_known)`:

- Reads `pyproject.toml` `version = "..."` line. Absent file → `installed_version=None`, `drift=False` (cannot determine).
- Compares against `latest_known`. Absent reference → `drift=False` (no comparison possible).
- Match → `drift=False`. Mismatch → `drift=True`; caller emits `qor_logic_stale_install` event.

Lifecycle skills invoke the check at session start and treat drift as advisory WARN. Non-blocking; operator decides whether to install fresh or proceed.

## V2 deferrals

- **Pluggable backends** per #38 option 2: `version_bump: python | node | rust | go | none`; `changelog_stamp: keepachangelog | release-please | conventional-commits | none`; `release_artifact_compile: qor-dist-compile | none`. Selected by `.qor/workspace.json` archetype detection.
- **Two-track substantiate split** per #38 option 3: `qor-substantiate-core` (language-agnostic) + `qor-substantiate-release` (Python-toolkit ceremony).
- **Machine-readable `requires:` declarations**: SKILL.md sections declare prereqs in structured form rather than prose tables.
- **Manifest-hash freshness comparison**: per-skill-artifact integrity check instead of pyproject-version-only.

## How this composes with Phase 45 and Phase 46

- **Phase 45** Self-Targeting Remediation Pass applied to this plan confirms `host_capability` is a governance module (internal helper, not user-touchable feature). Empty `feature_inventory_touches` correct.
- **Phase 46** feature-inventory discipline does not apply to internal helpers; lifecycle-skill freshness hooks are governance, not user-touchable surface.
- **Phase 47** prereq-skip events appear in the Process Shadow Genome alongside Phase 45/46 events, and the existing `aged_high_severity_unremediated` escalator (Phase 37) covers them per the unified severity ladder.
