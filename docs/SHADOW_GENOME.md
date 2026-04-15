# QoreLogic Shadow Genome

Record of rejected artifacts and failure patterns to prevent repetition.

## Genesis: 2026-04-15

---

### Entry #1: VETO — plan-qor-migration v1

**Timestamp**: 2026-04-15
**Target**: `docs/plan-qor-migration.md`
**Audit Report**: `.agent/staging/AUDIT_REPORT.md`
**Ledger Entry**: #12

**Failure Pattern**: Scaffolding-without-population. Plan declared a rich target structure (`qor/prompts/`, `qor/platform/profiles/*`, `qor/gates/schema/*`, `qor/skills/mlops/`, top-level `build/`) but did not assign creation of those artifacts to any phase. Seven orphan artifacts resulted.

**Failure Pattern**: Dependency ambiguity. Five implementation scripts proposed with no runtime, no package manager, no dependency declaration. Judgment deferred indefinitely.

**Failure Pattern**: Chain-blind migration. Mass file moves specified without addressing how the META_LEDGER SHA256 chain survives. Would corrupt the integrity guarantee the ledger exists to provide.

**Failure Pattern**: Ghost handler proliferation. Four handlers (shadow-issue target repo, `/qor-remediate` trigger, Codex adversarial protocol, `.qor/` state dir) pointed nowhere.

**Lesson**: Every directory and file appearing in a structure diagram must be traceable to a phase that creates it. Every script must declare its runtime and dependencies. Every migration touching the ledger must include a continuation strategy. Every handler must name its target concretely.

**Remediation**: 13 mandatory items issued in audit report §11. Governor must revise and resubmit.

---

---

### Entry #2: VETO — plan-qor-migration v2

**Timestamp**: 2026-04-15 (round 2)
**Target**: `docs/plan-qor-migration-v2.md`
**Audit Report**: `.agent/staging/AUDIT_REPORT.md`
**Ledger Entry**: #13

**Failure Pattern**: Classification-drift. `jsonschema` declared dev-only in dependency section while scripts using it sit in runtime location (`qor/scripts/`). Single source-of-truth for dependency classification must reconcile declaration with usage location.

**Failure Pattern**: Flat-to-hierarchical migration without mapping. 25 files in `ingest/subagents/` slated for move to categorized `qor/agents/`, but no per-file destination declared. Hierarchical moves require explicit mapping, never implicit.

**Failure Pattern**: Implicit test infrastructure. Plan references `tests/` and `tests/fixtures/` across every phase but treats them as pre-existing. Verified absent. Any structural element referenced must be declared and assigned a creating phase.

**Failure Pattern**: Undifferentiated decay. Shadow-genome stale-expiry applied uniformly across severities — highest-severity events (degradation = severity 5) can silently expire without remediation if they fail to combine with other events to hit threshold. Decay policy must be severity-aware.

**Failure Pattern**: Minute-resolution session IDs. Concurrency-naive identifier generation (UTC ISO-min truncation) admits collisions for sub-minute concurrent starts. Identity schemes must be collision-resistant by construction.

**Lesson**: After v1's structural fixes, the failure class shifted to edge cases: classification coherence, implicit references, decay policies, and concurrency assumptions. These are the defects that pass casual review but corrupt state under load.

**Remediation**: 10 mandatory items issued in audit report §12. Governor to produce v3.

---

---

### Entry #3: VETO — plan-qor-migration v3

**Timestamp**: 2026-04-15 (round 3)
**Target**: `docs/plan-qor-migration-v3.md`
**Audit Report**: `.agent/staging/AUDIT_REPORT.md`
**Ledger Entry**: #14

**Failure Pattern**: Named artifact without named author. Manifest files specified as Entry #13/#14 content subjects but no script/phase assigned to write them. Every artifact must have an author; every author must have a phase.

**Failure Pattern**: Plan-of-plans. v3 authored as delta against v2, treating v2 as base. v2's own header declares VETO. An under-remediation base is load-bearing for a remediation plan — structural irony. Remediation plans must either fully supersede (consolidate) or explicitly import/amend with enumerated inheritance; "unchanged unless listed" is too loose.

**Failure Pattern**: Re-emission without idempotence. Self-escalation mechanism (aged_high_severity_unremediated) fires on every sweep for the same source entry because plan lacks "already escalated" predicate. Any process that watches state and emits on threshold must consult its own prior emissions to avoid storms.

**Failure Pattern**: Implicit carrier. Session cache specified as "`$QOR_SESSION` env var" without declaring whether the carrier is subshell env, parent process injection, or file marker. Process boundaries matter; plans must name the carrier.

**Failure Pattern**: CI command that doesn't guard. `grep ... || echo "clean"` exits 0 on both match and non-match, producing no enforcement. Shell exit semantics must be verified for every command claiming to be a CI gate.

**Lesson**: Round-over-round defect class is compressing: v1 was structural, v2 was edge-case spec, v3 is precision-of-specification. Residual gaps are in cross-cutting mechanisms (generators, carriers, idempotence rules, shell semantics) — small surfaces that fail if not examined with specific questions.

**Remediation**: 6 mandatory items issued in audit report §12.

---

---

### Entry #4: VETO — plan-qor-migration-final v1

**Timestamp**: 2026-04-15 (round 4)
**Target**: `docs/plan-qor-migration-final.md`
**Audit Report**: `.agent/staging/AUDIT_REPORT.md`
**Ledger Entry**: #15

**Failure Pattern**: Scope telescoping. Three rounds of audits focused on skill/agent structure; the `ingest/` directory's broader content (9 subdirectories beyond `skills/` and `subagents/`) remained unaddressed across all plan revisions. Consolidating the plan surfaced the blind spot. Migration scope must enumerate the entire source surface, not the subset actively being planned.

**Failure Pattern**: Classifier without table. Phase 1 directive "third-party only" names a classifier for 90 `ingest/skills/` items without providing the mapping it implies. Classifiers are declarative intent; implementation requires enumeration, or explicit category rules with an exceptions list. Either format is acceptable; the classifier alone is not.

**Failure Pattern**: Unverified path reference. Phase 7 targeted `ingest/ql-*.md` for deletion. Verified location is `ingest/skills/ql-*.md`. Path referenced in plan prose must be grep-validated at authoring time. One-shot verification catches the typo before VETO.

**Failure Pattern**: Grep anchor misuse. CI guard command used `^processed/` and `^compiled/` while the surrounding tokens (`kilo-code/qor-`, `deployable state`) were unanchored. Inconsistent anchoring produced a guard that enforces some patterns and ignores others. Shell command semantics must be verified mechanism-by-mechanism, not assumed from resemblance.

**Failure Pattern**: Platform-blind primitive. Atomic-write spec ("tempfile + rename") correct on POSIX, broken on Windows. User environment is Windows. Portability of primitives must be verified against target platform, particularly where the plan specifies canonical invocation.

**Lesson**: Round 4 defect class is scope-coverage + platform-specifics + one-shot verification of named mechanisms. Structural design is solid; remaining issues are the kind that surface only under exhaustive enumeration.

**Remediation**: 5 items issued in audit report §12.

---

---

### Entry #5: VETO — plan-qor-migration-final (round 5)

**Timestamp**: 2026-04-15 (round 5)
**Target**: `docs/plan-qor-migration-final.md` (amended)
**Audit Report**: `.agent/staging/AUDIT_REPORT.md`
**Ledger Entry**: #16

**Failure Pattern**: Amendment-drift. Round 4 amendments introduced §2.B with new destination paths (`qor/experimental/`, `qor/templates/`, `qor/scripts/utilities/`) that were never back-propagated into §2's main structure tree. Structure and mapping amendments must be synchronized; adding a destination in a mapping table without reflecting it in the canonical structure is a structural defect.

**Failure Pattern**: Collision-blind routing. Two sources (`ingest/skills/<x>` and `ingest/scripts/<x>`) verified to have 21 name-identical entries, both routed to the same `qor/vendor/skills/<x>/`. Mapping rules must specify collision resolution at plan time — "silent overwrite" is a failure mode, not a policy.

**Failure Pattern**: Deferred-to-runtime classification. Rules R-5, R-6 stated "inspection at Phase 1 execution" rather than resolving classification at plan time. An audit cannot verify what the plan does not specify; deferred decisions pass audit vacuously and surface at execution.

**Failure Pattern**: CI guard pollutes historical record. Post-migration path-rot grep applied uniformly across `docs/` catches legitimate historical audit references in immutable append-only artifacts (META_LEDGER, SHADOW_GENOME). Guards must be scoped to the surface they police (forward-looking docs), not collapsed against it.

**Lesson**: Round 5 defects emerge from amendment cross-impact. Every amendment touches multiple sections; failing to check for synchronization (structure vs mapping), collision (two sources → one dest), and scope (guard breadth vs immutable records) produces a different class of regression than round-over-round compression would suggest.

**Remediation**: 5 items in audit §10.

---

---

### Entry #6: VETO — research-brief-full-audit

**Timestamp**: 2026-04-15
**Target**: `docs/research-brief-full-audit-2026-04-15.md`
**Audit Report**: `.agent/staging/AUDIT_REPORT.md`
**Ledger Entry**: #21

**Failure Pattern**: Count inflation. Brief reported "9 affected skills" for S-1; verified count is 8. The grep filter caught a non-applicable item (qor-shadow-process declares a free-form log path, not a gate artifact). Counts in research briefs must be re-verified after the filter step, not reported from the raw filter.

**Failure Pattern**: Doctrine conflation. S-8 ("16 missing from delegation-table") and S-12 ("agents lack /qor-* refs") treat doctrine choices as gaps. A finding requires (a) a doctrine that says "X must hold" and (b) evidence "X does not hold". Without (a), it's a doctrine proposal, not a gap.

**Failure Pattern**: Citation drift. Research protocol mandates file:line for every finding. Brief cites for ~25%; the rest say "many skills" or "X skills". Without citations, future readers can't verify or act precisely.

**Failure Pattern**: Self-blind to test coverage. Brief surfaces 24 systemic gaps but doesn't ask "why didn't tests catch any of these?". User asked the question independently. The omission is itself a gap — the meta-finding (S-14: SKILL.md compliance not test-covered) is more consequential than several specific findings the brief did surface.

**Lesson**: Audits-of-research-briefs need a "verification round" before publication: re-run grep filters with the per-finding edge cases checked; make every finding cite at least one file:line; ask "why didn't the existing test/audit infra catch this?" — that meta-question usually surfaces an additional systemic gap.

**Remediation**: 6 mandatory items issued in audit report. Brief revises to v2 OR Phase 11D plan absorbs the corrections directly (skipping a brief revision since the headline findings are correct).

---

---

### Entry #7: VETO — plan-qor-phase12-budget-ledger-tests

**Timestamp**: 2026-04-15
**Target**: `docs/plan-qor-phase12-budget-ledger-tests.md` + premature `tests/test_ledger_hash.py`
**Audit Report**: `.agent/staging/AUDIT_REPORT.md`
**Ledger Entry**: #22

**Failure Pattern**: Plan-without-ratification. Governor drafted plan + began coding without surfacing design questions for user validation. /qor-plan skill mandates dialogue first; this iteration skipped it. User had to invoke /qor-plan to interrupt mid-execution.

**Failure Pattern**: Deferred-decision-as-prose. Plan said "If pyyaml is already a transitive dep ... use it." Decision determined by runtime check rather than committed in plan. A plan with conditional decisions is not a plan; it's a wish.

**Failure Pattern**: Misnamed test. `test_write_manifest_atomic_write` docstring claimed "no torn state on partial write" but body only verified os.replace was called. Test name describes intent; assertion describes mechanism. When they disagree, the assertion wins (and the name lies).

**Failure Pattern**: TDD-claimed but regression-coverage-actual. Plan invoked TDD enforcement language but tests verified existing code. The skill's TDD discipline was not honored; the work is regression coverage backfill — which is fine, but should be classified honestly.

**Failure Pattern**: Hardcoded coupling to live state. Test recomputed Entry #20's chain hash by hardcoding its values. If Entry #20 is ever superseded the test breaks. Tests should derive expected values from the algorithm, not from frozen examples of the algorithm's output (use synthetic inputs with computed expected outputs).

**Lesson**: The /qor-plan skill exists for a reason. When the Governor jumps to coding, it bypasses the dialogue checkpoint that catches design questions BEFORE they become test artifacts that need rewriting. Pre-implementation audits catch some of this; ratifying dialogue catches more, earlier, cheaper.

**Remediation**: 11 mandatory items issued in audit report.

---

---

### Entry #8: VETO — plan-qor-phase12-v2

**Timestamp**: 2026-04-15
**Target**: `docs/plan-qor-phase12-v2.md`
**Audit Report**: `.agent/staging/AUDIT_REPORT.md`
**Ledger Entry**: #23

**Failure Pattern**: Ironic complect. Plan v2's V-10 remediation introduced a single test name (`test_verify_handles_malformed_entry_header`) covering THREE distinct conditions — exactly the V-4 complect defect v2 was meant to fix. Remediation plans authored quickly can reproduce the defects they're remediating; second-pass discipline matters as much as first-pass.

**Failure Pattern**: Stale arithmetic. Plan said "163 prior + ... = 184" while `pytest tests/` actually returns 178 (uncommitted test_ledger_hash.py is being discovered). Test counts in plans must be re-verified against the running suite, not inferred from "last known state".

**Failure Pattern**: Adjacent-sentence-disagreement in doctrine. Rule 4 first sentence asserted universal scope ("workflows installing Python deps"); the next sentence narrowed the scope. Doctrine rules and their exceptions belong in the same sentence, not as adjacent paragraphs that contradict each other.

**Failure Pattern**: Incomplete ratification. Plan header cited Q1/Q2/Q3 from the first dialogue round but omitted Q-A/Q-B/Q-C from the second round. Ratification headers are not "best of" lists; they enumerate ALL decisions.

**Lesson**: Multi-round audit loops produce v2/v3/v4 plans where each round addresses prior defects but seeds new ones. The "amendment-drift" pattern from the original Phase 1 plan-migration loop applies to remediation plans too. Either (a) accept rougher plans and iterate faster, or (b) bake more ruthless self-review into v2 authoring before re-audit.

**Remediation**: 7 mandatory items issued in audit report.

---

*Shadow integrity: ACTIVE*
