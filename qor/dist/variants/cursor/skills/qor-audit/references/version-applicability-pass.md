# Version-Applicability Pass (GH #282)

Progressive-disclosure detail for the `/qor-audit` Version-Applicability Pass. Run this before
emitting PASS so a release-class plan whose target could not exceed the current tag is caught at
audit rather than after implementation at `/qor-substantiate`.

```bash
PLAN_PATH=$(python -c "from qor.scripts.governance_helpers import current_phase_plan_path; print(current_phase_plan_path())")
python -c "import sys; from qor.scripts import version_applicability as va; v=va.validate('${PLAN_PATH}','.'); print(v.reason); sys.exit(0 if v.ok else 1)" || VETO
```

`version_applicability.validate(plan_path, repo_root)` returns a `VersionVerdict`:

- `classification == "release"` (`change_class` in `{hotfix, feature, breaking}`): `ok` iff the
  computed target version exceeds the current highest `v*` tag. This mirrors the substantiate
  bump-time downgrade guard exactly, moved earlier.
- `classification == "version-not-applicable"` (`change_class: governance`): always `ok`; the
  non-release governance cycle bumps nothing and tags nothing. Plan, audit, and substantiate
  interpret this identically.

A plan missing the canonical `**change_class**:` header makes `validate` raise before PASS.

**A release-class plan whose target is <= the current highest tag -> VETO with `specification-drift`
category** (the plan would inevitably fail substantiate version validation). Required next action:
Governor declares the correct release target, or reclassifies the cycle as `governance` for a
non-release cycle, then re-runs `/qor-audit`.
