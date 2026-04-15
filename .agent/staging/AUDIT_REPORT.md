# AUDIT REPORT — plan-qor-migration-final.md (round 5)

**Timestamp**: 2026-04-15 (round 5)
**Judge**: QoreLogic Judge (adversarial, solo)
**Target**: docs/plan-qor-migration-final.md (amended)
**Verdict**: **VETO**
**Risk Grade**: L1

---

## 1. Security Pass
PASS.

## 2. Ghost Handler Pass
All handlers resolved. PASS.

## 3. Section 4 Razor Pass
PASS.

## 4. Dependency Audit
PASS.

## 5. Macro-Level Architecture Pass

**V-1**: **§2.B introduces destinations not declared in §2 main structure tree.** The amendment adds these paths without any corresponding declaration in §2:

- `qor/experimental/` (target for `ingest/experimental/`)
- `qor/templates/` (target for `ingest/templates/`)
- `qor/skills/custom/` / `qor/vendor/skills/custom/` (target for `ingest/skills/custom/`, R-6)
- `qor/scripts/utilities/` (target for `ingest/internal/utilities/`)

§2's structural tree is the authoritative declaration. Destinations invented mid-plan create orphan-by-construction.

## 6. Orphan Detection

All declared artifacts have creating phases. But V-1 above implies four undeclared paths.

## 7. Scope/Mapping Pass

**V-2**: **Duplicate-item collision unresolved.** Verified (`comm -12` on `ingest/skills/` vs `ingest/scripts/`): **21 subdirectories exist in both locations** with identical names — `composition-patterns`, `custom`, `frontend-bridge-integration`, `marketplace-plugin-ops`, `playwright-e2e-mocks`, `react-best-practices`, `react-native-skills`, `rust-skills`, `security-permission-audit`, `skill-lifecycle-ops`, `tauri2-async-commands`, `tauri2-cicd-distribution`, `tauri2-error-handling`, `tauri2-performance-optimization`, `tauri2-plugin-integration`, `tauri2-security-permissions`, `tauri2-state-management`, `tauri2-testing-validation`, `tauri-ipc-wiring`, `technical-writing-narrative`, `web-design-guidelines`.

- §3.B R-7 routes `ingest/skills/<name>` → `qor/vendor/skills/<name>/`
- §2.B routes `ingest/scripts/<name>` → `qor/vendor/skills/<name>/`
- Both target the same destination path for the same-named item. No merge/dedup/precedence rule specified.

Implementation will either (a) have the second write overwrite the first silently, losing content, or (b) fail on collision. Neither is a specified behavior.

**V-3**: **Merge-order ambiguity for `ingest/internal/scripts/` → `qor/scripts/`.** Phase 2 authors new scripts (`compile.py`, `check_variant_drift.py`, `session.py`, `validate_gate_artifact.py`, `create_shadow_issue.py`). §2.B routes `ingest/internal/scripts/` into the same `qor/scripts/`. No policy for: (a) phase ordering (does §2.B migration run before or after Phase 2 authorship?), (b) naming collisions if `ingest/internal/scripts/` contains overlapping filenames.

**V-4**: **Deferred decisions in R-5 and R-6.** §3.B R-5 ("inspect each: qor-scoped vs vendor") and R-6 (same pattern) defer classification to Phase 1 execution time rather than plan time. Plan is the gate artifact for audit; deferring decisions to runtime violates gate semantics (the audit cannot verify what the plan does not specify).

## 8. CI Guard Correctness Pass

**V-5**: **Phase 7 post-migration grep is too aggressive — blocks legitimate historical references.**

Amended form:
```
! grep -r "kilo-code/qor-\|deployable state\|processed/\|compiled/\|ingest/" docs/ --exclude-dir=archive
```

Verified: `docs/META_LEDGER.md` contains **11 references** to `ingest/` (across audit tribunal entries #12, #13, #14, #15); `docs/SHADOW_GENOME.md` contains **4 references** (across shadow genome entries #1, #2, #3, #4). These are historical audit records — immutable by design, not doc rot.

The grep will match these and return exit code 0 → `!` inverts → CI exits 1 → fails. The guard cannot distinguish "forward-looking doc still uses old path" (should fail) from "historical audit cites old path" (should pass).

Additionally: `kilo-code/qor-` and `deployable state` tokens have the same problem — both are cited in audit prose inside the ledger.

## 9. Verdict

**VETO** — Risk Grade L1

| Category | Violations |
|---|---|
| Security/Ghost/Razor/Dep/Orphans | 0 |
| Macro-level (§2/§2.B split) | 1 (V-1) |
| Scope (duplicate collision) | 1 (V-2) |
| Scope (merge order) | 1 (V-3) |
| Scope (deferred decisions) | 1 (V-4) |
| CI guard (over-aggressive) | 1 (V-5) |

**Total: 5 violations.** Same count as round 4; different class. Previous round 4 violations are resolved but amendment introduced new scope/merge issues and a CI over-reach.

## 10. Mandatory Remediation

1. **V-1**: Add to §2 structure tree:
   ```
   qor/experimental/           (non-canonical research retention, Phase 1 §2.B)
   qor/templates/              (doc templates, Phase 1 §2.B)
   qor/scripts/utilities/      (internal utility scripts, Phase 1 §2.B)
   qor/skills/custom/          (only if R-6 resolves qor-scoped — see V-4)
   ```
2. **V-2**: Add §2.B collision rule. Recommend: "For items appearing in both `ingest/skills/<name>` and `ingest/scripts/<name>` (verified: 21 duplicates), `ingest/skills/` wins; `ingest/scripts/` duplicate is discarded. Discarded items are logged to `.qor/migration-discards.log` for post-migration review."
3. **V-3**: Explicit ordering rule. Recommend: "Phase 2 authorship runs BEFORE §2.B migration of `ingest/internal/scripts/` → `qor/scripts/`. If any migrated script has a name collision with a Phase 2 authored script, the Phase 2 version wins; `ingest/internal/scripts/` version is routed to `qor/scripts/vendored/` instead."
4. **V-4**: Resolve R-5 and R-6 at plan time. Either (a) run inspection now and encode actual mapping in §3.B, or (b) declare upfront rule: "All content under `ingest/skills/custom/` and `ingest/skills/agents/` is qor-scoped; promote to `qor/skills/custom/` and merge-into-existing `qor/agents/` respectively. Collision within `qor/agents/` rule: already-migrated source wins; ingest duplicate goes to `.qor/migration-discards.log`."
5. **V-5**: Narrow Phase 7 grep. Two mutually-exclusive fixes:
   - (a) Exclude historical artifacts: `! grep -r "kilo-code/qor-\|deployable state\|processed/\|compiled/\|ingest/" docs/ --exclude-dir=archive --exclude=META_LEDGER.md --exclude=SHADOW_GENOME.md`
   - (b) Scope to forward-looking docs only: `! grep "kilo-code/qor-\|deployable state\|ingest/" docs/SYSTEM_STATE.md docs/SKILL_REGISTRY.md README.md`

   Option (b) is simpler and intent-aligned; recommend it.

---

**Content Hash**: (computed at ledger entry)
**Previous Chain Hash**: 741ecc9d93ae49d1b59fd46deb428e438ffb2252622607f84b035fa55e619397 (Entry #15)

**Next action**: Governor amends in place. 5 items; all mechanical or rule-additions.
