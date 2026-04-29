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

---

### Entry #9: VETO — plan-qor-phase13-governance-enforcement

**Timestamp**: 2026-04-15
**Target**: `docs/plan-qor-phase13-governance-enforcement.md`
**Audit Report**: `.agent/staging/AUDIT_REPORT.md`
**Ledger Entry**: #25

**Failure Pattern**: S-1 recurrence at meta-level. Plan introduces `change_class:` requirement for plan headers but provides no doctrine test enforcing it. This is the same defect class as `gate_writes` declared without execution (Phase 11D S-1). Whenever a phase declares a rule, the same phase must add the test. "Rule without test = optional" — and the plan itself doesn't follow its own rule (V-7).

**Failure Pattern**: Spec-by-implication. Plan wired substantiate to `bump_version(change_class)` but never specified how substantiate KNOWS the change_class. Reading the plan from the implementer's seat, there's no parser spec, no plan-discovery spec, no fallback. The wiring is real; the input is hand-waved.

**Failure Pattern**: Filename scheme drift unaddressed. Plan's parser regex assumes `\d+` after "phase" but verified history shows letter suffixes (11d, 12-v2). Plan needs to either grandfather older naming or extend the parser; silently breaking on existing files is not a choice.

**Failure Pattern**: Operational gaps in branching/tagging. `git checkout -b` doesn't address dirty trees. `git tag -a` doesn't address collisions. Substantiate already has Step 2.5 version-validation interdiction but plan doesn't integrate. Real-world git operations have failure modes; plans must address them or specify "out of scope".

**Failure Pattern**: Self-contradiction. Plan's own header lacks the `change_class:` field that the plan introduces as mandatory. The doctrine-V-1 test would catch this — and would also have caught it during plan authoring if the test had been written first.

**Lesson**: Phase 11D's S-1 ("rule without test") wasn't actually generalized into the doctrine. It was recorded as a one-time finding. Should be elevated to a meta-doctrine: every plan that introduces a new rule MUST add a corresponding test in the SAME phase. Add to `qor/references/doctrine-test-discipline.md` Rule 4 "Rule = Test".

**Remediation**: 10 mandatory items issued in audit report.

### Entry #10: VETO — plan-qor-phase13-v2

**Timestamp**: 2026-04-15
**Target**: `docs/plan-qor-phase13-v2.md`
**Audit Report**: `.agent/staging/AUDIT_REPORT.md`
**Ledger Entry**: #26

**Failure Pattern**: Parallel infrastructure to native machinery. Plan v2 proposed `docs/PHASE_HISTORY.md` to index every phase. Operator pointed out: GitHub already provides this via labeled issues + branches + PR descriptions + tags. Building parallel infrastructure is a YAGNI violation when the platform supplies the machinery for free. Doctrine doc should describe the *practice*, not author the index.

**Failure Pattern**: Format ambiguity. Plan introduced `change_class:` requirement but oscillated between `**change_class**:` (bold) and `change_class:` (plain) across versions. A new format must be canonical from introduction; rule + parser + doctrine test must all agree on one syntax.

**Failure Pattern**: V-9 recurrence (test count mismatch). v1 had this defect; v2 audit caught it in v1; v2 plan introduced it again with a different count. Test counts must be derived (count test functions in the file body) not asserted (header says N). Recurrence shows the count was authored by hand without verification.

**Failure Pattern**: Filesystem-dependent ordering. Plan used mtime as tiebreaker for multi-version plans. Git operations dont preserve mtime; CI checkouts produce arbitrary mtime ordering. Deterministic ordering must be content-addressable (filename suffix, lexicographic order) not metadata-dependent.

**Failure Pattern**: Citation drift. Rule 4 elevation cited 'Phase 11D S-1' but the actual location is `docs/research-brief-full-audit-2026-04-15.md §S-1`. /qor-plan grounding protocol requires verified file paths for every named mechanism.

**Lesson**: Operator hints often surface architecture-altering simplifications. The agents first instinct ('build the doc') competes with the operators bigger view ('the platform already does this'). When operator suggests a hint, audit the v2 plan against the hint as a primary lens, not as an afterthought.

**Remediation**: 7 mandatory items issued in audit report.

### Entry #11: VETO — plan-qor-phase13-v3

**Timestamp**: 2026-04-15
**Target**: `docs/plan-qor-phase13-v3.md`
**Audit Report**: `.agent/staging/AUDIT_REPORT.md`
**Ledger Entry**: #27

**Failure Pattern**: Doctrine/test keyword drift (V-2 pattern recurrence). V-1 remediation introduced both a doctrine clause ("Annotated tag...") and its guarding test (substring match "tag annotation") in the same plan section, in the same authoring pass — and they still disagree on word order. When rule and test are co-authored, sequence must be: write test literal first → paste literal into doctrine → grep to verify. Paraphrase between them is the drift engine.

**Failure Pattern**: Rule-without-test recurrence inside the phase elevating "Rule = Test" to Rule 4. §C.1 spec says `bump_version` raises `InterdictionError` on tag collision or downgrade; §D.2 lists 9 tests, none covers the interdiction. S-1's original surface was `gate_writes` frontmatter without execution test. Pattern is identical — security-relevant interdiction specified in prose without assertion. Doctrine gains keepers only when the test exists.

**Failure Pattern**: Scope-implicit test. `test_plans_declare_change_class` specifies coverage by enumerated exclusion list ("11d/12-v2") rather than numeric forward-boundary (`phase >= 13`). Enumerated exclusions hide the real rule; next author adds a plan file and silently breaks the suite. Forward boundaries must be numeric.

**Failure Pattern**: Undefined local in prescribed code snippet. §B.2 Step 7.5 references `phase_num` never derived. Same class as Entry #26 V-4 (InterdictionError undefined) — symbol used in prose without definition in the same snippet. Plans-as-code must be runnable as written.

**Lesson**: Co-authored rule-test pairs require literal-paste discipline, not paraphrase. Numeric boundaries beat enumerated exceptions. Every interdiction specified in prose requires a test before the plan is gate-passable.

**Remediation**: 4 mandatory items issued in audit report.

---

### Entry #12: VETO — plan-qor-phase14-v2 (shadow attribution remediation)

**Date**: 2026-04-15
**Verdict ID**: Entry #32
**Failure Mode**: DATA_LOSS / BREAKING_CHANGE

#### What Failed
Plan v2 introduced `id_source_map()` for dual-file write-back in `check_shadow_threshold.py` and `create_shadow_issue.py`. The map is built from events on disk; newly-created escalation events (with IDs not yet persisted) fall through both filters and are silently dropped. Separately, `append_event` signature changed to keyword-only but 2 existing test callers pass `log_path` positionally.

#### Why It Failed
Read-modify-write with a post-hoc id-based split cannot handle events created during the modify step. The split assumes all events have a prior on-disk identity — a closed-world assumption violated by the escalation sweep.

#### Pattern to Avoid
**SG-032**: When designing a batch-split-write pattern, verify that the split criterion covers ALL events in the batch, including those created mid-cycle. Newly minted records have no prior identity in any lookup table. Either (a) classify at creation time, or (b) provide a default/fallback bucket for unmatched records.
**SG-033**: When changing a function signature from positional to keyword-only (`*`), grep all call sites including tests. "Existing body unchanged" does not mean "existing callers unchanged."

#### Remediation
4 mandatory items issued in audit report. V-1 prescribes classify-at-creation or `_target_path` metadata. V-2 prescribes updating 2 test call sites to keyword form.

---

### Entry #13: VETO — plan-qor-phase15 (shadow-genome countermeasures doctrine)

**Date**: 2026-04-16
**Verdict ID**: Entry #36
**Failure Mode**: VALIDATION_GAP / COMPLEXITY_VIOLATION

#### What Failed
Plan v1 for the Shadow Genome countermeasures doctrine introduced a static-analysis test for SG-033 (keyword-only signature discipline). The AST walker's positional-arg check used naive length comparison that misclassifies calls containing `ast.Starred` nodes. Doctrine-content tests checked for keywords anywhere in body rather than anchored to the relevant SG section.

#### Why It Failed
SG-034: AST-based code-pattern tests need explicit handling for special node types (`Starred`, `AsyncFunctionDef`, `keyword`); naive `len(args)` comparisons produce false positives on valid Python patterns. SG-035: doctrine-content tests checking for unanchored keywords can pass even when the section they claim to verify is missing entirely; W-1 literal-keyword discipline requires proximity/structure anchoring.

#### Pattern to Avoid
**SG-034**: When writing AST-based tests, enumerate every relevant node type family (`FunctionDef`+`AsyncFunctionDef`; `Starred`+`keyword` in `Call.args`; `Attribute`+`Name` in `Call.func`). A walker that misses a family produces either false positives or false negatives depending on which side of the check the omission falls.
**SG-035**: Doctrine-content tests must anchor keywords to their semantic section (regex proximity, header parsing, or explicit section-scoped reads). `body.contains(keyword)` tests pass on accidental keyword co-occurrence, undermining the rule they claim to enforce.

#### Remediation
4 mandatory items in audit report. V-1: handle `ast.Starred` in call args. V-2: anchor doctrine tests to their section. V-3: resolve `qor-plan/SKILL.md` Razor state (trim or explicit exemption). V-4: include `AsyncFunctionDef` in walker.

---

### Entry #14: VETO — plan-qor-phase16-governance-polish (dogfood failure)

**Date**: 2026-04-16
**Verdict ID**: Entry #40
**Failure Mode**: DOCUMENTATION_DRIFT / VALIDATION_GAP

#### What Failed
Phase 16 plan — authored immediately after Phase 15 codified the Grounding Protocol into `doctrine-shadow-genome-countermeasures.md` — violated SG-016 in its Track B by deferring file-size verification instead of resolving it inline.

#### Why It Failed
Cognitive pattern: the plan author (operating as Governor) treated the countermeasures doctrine as a reference for future phases rather than an active constraint on the phase being written. The verify was acknowledged ("needs verification before implementing") but not executed, creating the exact "I know this already" failure mode the doctrine warned against.

#### Pattern to Avoid
**SG-036**: A doctrine codified in phase N does not become automatically load-bearing in phase N+1 unless the author treats it as active. "I'll verify during implementation" is a deferral, not compliance. The Grounding Protocol requires inline citation at plan-authoring time, not at implementation time. This is especially important for phases immediately following doctrine adoption — no grace period.

#### Remediation
3 mandatory items in audit report. V-1: cite verified line counts inline. V-2: strengthen "verbatim extraction" test to check content movement, not just substring presence. V-3: omit invalid anchors, match Phase 15 pointer style.

---

### Entry #15: VETO — plan-qor-phase17a-doctrine-completion (prose-code mismatch)

**Date**: 2026-04-16
**Verdict ID**: Entry #44
**Failure Mode**: DOCUMENTATION_DRIFT / VALIDATION_GAP

#### What Failed
Plan promised to expand `test_doctrine_lists_all_sg_ids` to cover 11 SG IDs (prose + Success Criteria), but the proposed code block listed only 9 — missing SG-034 and SG-035. Implementer following the code would produce a test whose name suggests full coverage but actual coverage is partial.

#### Why It Failed
Cognitive pattern: when editing a plan mid-draft, the author updated the prose narrative but forgot to update the code snippet in sync. The prose and code are separate surfaces that both encode the same spec; drift between them is silent.

#### Pattern to Avoid
**SG-038**: In a plan document, prose descriptions and code blocks are two encodings of the same spec. They drift independently. An implementer reading the code literally may ship what the code says, not what the prose promises. Countermeasure: when a plan updates a list/enumeration, grep the plan for every occurrence of the list and update all copies in lockstep. Optional future enforcement: lint plans for prose+code consistency on named enumerations.

#### Remediation
2 mandatory items in audit report. V-1: fix code block to list all 11 IDs (015-021, 032-037). V-2: fix arithmetic (+2, not +3; baseline 231 → 233).

---

### Entry #16: VETO — plan-qor-phase19-packaging-foundation (third SG-038 recurrence)

**Date**: 2026-04-16
**Verdict ID**: Entry #56
**Failure Mode**: DOCUMENTATION_DRIFT (SG-038 recurrence #3)

#### What Failed
Plan's header claimed "5 of 18 gaps closed" but Track A and Track D extended scope to 7 gaps (added PKG-04 readme + PKG-05 metadata). Header, Track A Changes footer, Track D test list, and the Constraints section's "SG-038 lockstep" line all disagreed on the gap count.

#### Why It Failed
Third occurrence of SG-038 pattern (prose-code drift) in Phase 17a v1 (Entry #44), Phase 15 v1 (the original SG-035 discovery), and now Phase 19. The plan author expanded Track A's content mid-draft (added readme/classifiers/keywords/urls/authors after initial scoping) but didn't update the header's gap count. This was the first plan explicitly authored under SG-036 "no grace period" discipline after SG-038 was codified — yet the very discipline SG-038 prescribed was violated.

#### Pattern to Avoid (reinforcement)
**SG-038 is empirically sticky.** Codifying it in the doctrine did not prevent its recurrence one plan later. Future mitigation options: (a) author plans in a template that grep-asserts prose-code consistency; (b) add a plan-linter test that validates "Closes gaps" header enumerates exactly the same IDs as each Track's Changes footer; (c) require the final Draft→Resolve pass to explicitly grep the plan for every enumerated list and cross-check.

#### Remediation
3 mandatory items in audit report. V-1: pick scope (keep 7 or shrink to 5) and reconcile header / tracks / tests / constraints / CI Commands. V-2: update Out-of-scope section to match. V-3: fix off-by-one grounding claim.

---

### Entry #17: VETO — plan-qor-phase20-import-migration (fourth SG-038 recurrence)

**Date**: 2026-04-16
**Verdict ID**: Entry #60
**Failure Mode**: DOCUMENTATION_DRIFT (SG-038 recurrence #4)

#### What Failed
Phase 20 plan has 3 arithmetic inconsistencies in its Affected-Files and gap-count summaries. "Scripts (12)" over a list of 15. "Modified (14)" over a section that sums to 20. "11 open after this phase" when actual post-phase remaining is 7.

#### Why It Failed
SG-038 was codified in Phase 17a v2, yet has recurred in every planning phase since: Phase 15 v1, Phase 17a v1, Phase 19 v1, Phase 20 v1. Narrative awareness of the pattern does not prevent it. The author writes the header count first, then expands the content, and doesn't go back to reconcile.

#### Pattern Confirmed
**SG-038 is empirically sticky despite doctrine.** Four consecutive VETOes at Phase 20 say doctrine-only mitigation fails. The prescribed countermeasure in the doctrine ("grep the plan for every occurrence of that element and update all copies in lockstep") is correct but the human-in-the-loop discipline is fragile. Mechanical enforcement is needed.

#### Proposed Mechanical Mitigation (to ship as part of Phase 20 remediation)
A plan-linter test `tests/test_plan_self_consistency.py` that parses any `docs/plan-qor-phase*.md` file and asserts:
- Every `Scripts (N):` / `Modified (N)` / `New (N)` / etc. header where `N` is a digit matches the number of enumerated items that follow.
- Every "X of 18" or similar gap-count claim is internally arithmetic-consistent with enumerated GAP-* IDs in the same plan.

This is small (~50 lines), catches the pattern mechanically, and can run in CI.

#### Remediation
3 mandatory items in audit report. V-1: 12 → 15 scripts. V-2: 14 → 20 total. V-3: 11 → 7 remaining after Phase 20.

---

*Shadow integrity: ACTIVE*


## Entry SG-Phase24-A: Razor Creep via Cumulative Plan Additions

**Date**: 2026-04-17
**Phase Target**: 24 (multi-host install)
**Judge Verdict**: VETO

### Pattern
`qor/cli.py` crossed the 250-line razor during Phase 22's CLI expansion (init, policy, compliance). Subsequent plans have continued to grow it without mandating a split. Phase 24 would have pushed it to ~320 lines. `_do_install` is likewise already 54 lines (54 > 40) and every install-related plan extends it without decomposition.

### Why It Matters
Razor violations are binary per `/qor-audit`. "Already over the limit" is not an exception -- each new plan that adds to the file is a fresh violation. Without a refactor gate, growth compounds until readability collapses.

### Countermeasure
Any plan that touches `qor/cli.py` or `_do_install` must either:
1. Keep net line-delta <= 0 (substitution, not addition), or
2. Include a Phase 0 refactor that extracts logic to restore compliance, or
3. Delegate explicitly to `/qor-refactor` before implementation.

### Pattern ID
SG-Phase24-A (cumulative razor creep in CLI harness)

---

## Entry SG-Phase24-B: YAML Parser Introduction Without Safe-Load Commitment

**Date**: 2026-04-17
**Phase Target**: 24 (multi-host install)
**Judge Verdict**: VETO (contributing ground)

### Pattern
Phase 24 Plan line 118: "parse skill/agent frontmatter". The codebase currently has zero YAML usage in `qor/scripts/`. Plans that introduce a new parser class (YAML, pickle, shelve, plistlib) without naming the specific safe API invite A08 deserialization vulnerabilities. Implementers reach for the import autocomplete (`yaml.load`, `pickle.loads`) rather than the safe sibling.

### Countermeasure
When a plan introduces a deserializer for a new format, it must name the exact safe API: `yaml.safe_load`, `json.loads` (no custom hooks), `pickle` is BANNED, `tomllib.loads`, `plistlib.loads(fmt=FMT_XML)`. Audit VETOes plans that say "parse X" without naming the safe entry point.

### Pattern ID
SG-Phase24-B (unsafe deserializer defaults)

---

## Entry SG-Phase24-C: Third-Party Dependency Preferred Over Trivial Vanilla

**Date**: 2026-04-17
**Phase Target**: 24 (multi-host install)
**Judge Verdict**: VETO (contributing ground)

### Pattern
Plan line 121 proposed `tomli_w` for TOML writing when the output schema is five scalar keys + one triple-quoted prompt. A vanilla writer fits in <15 lines. The dependency was proposed reflexively ("there's a library for this") rather than by necessity. Pre-existing project discipline (`pyproject.toml` has exactly one runtime dep, `jsonschema>=4`) should resist this drift.

### Countermeasure
Dependency audit asks "<10 lines vanilla?" -- the answer governs. For narrow output formats (fixed schema, bounded key set), the vanilla answer is almost always yes. Plans adding a dependency for serialization must justify by pointing to either schema breadth or edge-case correctness that vanilla cannot address.

### Pattern ID
SG-Phase24-C (reflexive dependency introduction for trivial serializers)

---

*Shadow integrity: ACTIVE*


## Entry SG-Phase24-D: Remediation Target Mismatch

**Date**: 2026-04-17
**Phase Target**: 24 (multi-host install)
**Judge Verdict**: VETO (Pass 2)

### Pattern
After Entry #70 VETO listed three grounds (A08 safe_load, Razor, tomli_w dependency), the Governor ran `/qor-refactor` -- which is the correct skill for Razor but cannot by design address the other two grounds, which live in plan text (Phase 2 Changes block). The subsequent audit (Entry #72) found Grounds 1 and 3 unchanged and re-VETOed.

### Why It Matters
`/qor-refactor` mutates code. Plan-text violations (unsafe-parser commitments, unjustified dependencies) can only be cleared by editing the plan. Running the code-shape skill and then re-auditing without touching the plan is a loop: the code-shape ground clears, but the plan-text grounds persist forever.

### Countermeasure
When an audit VETO lists multiple grounds, the Governor must classify each ground:
- **Code-shape ground** (Razor, Ghost UI in implementation, Orphan) -> `/qor-refactor` or `/qor-organize`
- **Plan-text ground** (Dependency choice, A08 safe-parser commitment, missing tests for violations) -> edit `docs/plan-qor-phase*.md` directly, no skill required

Then re-audit only after BOTH classes of remediation have been applied.

### Pattern ID
SG-Phase24-D (remediation target mismatch: running code skill when plan-text edits are required)

---

*Shadow integrity: ACTIVE*


## Entry SG-Phase25-A: A08 Discipline Scope Gap (test code)

**Date**: 2026-04-17
**Phase Target**: 25 (prompt resilience + workspace seed)
**Judge Verdict**: VETO

### Pattern
Phase 24 introduced `tests/test_yaml_safe_load_discipline.py` as a codebase-wide ban on unsafe YAML APIs. The test's `rglob("*.py")` walk is rooted at `qor/` only. Test code is not scanned. Phase 25 plan adds YAML frontmatter parsing in new test files (`test_prompt_resilience_lint.py`, `test_skill_prerequisite_coverage.py`) without committing to `yaml.safe_load`, leaving a silent drift path: an implementer can use `yaml.load(...)` in a test and CI stays green.

### Why It Matters
Discipline tests are only as strong as their scope. Any path not walked is a future vulnerability the lint can't see. When a plan extends YAML parsing into an uncovered directory, it must either (a) commit to safe_load explicitly in plan text, or (b) widen the discipline test's scope, or ideally both.

### Countermeasure
Any plan that adds deserializer calls in a directory not currently covered by the relevant discipline test must, as part of that plan:
1. Name the safe API explicitly in the plan's Changes/Unit Tests blocks.
2. Widen the discipline test's walk to cover the new directory, OR justify in plan text why the new directory is exempt.
3. Add a planted-call negative test proving the widened scope catches violations.

### Pattern ID
SG-Phase25-A (discipline-test scope does not track new usage sites)

---

*Shadow integrity: ACTIVE*


## Entry SG-Phase25-B: Ghost Feature via Metadata-Only Declaration

**Date**: 2026-04-17
**Phase Target**: 25 (Phase 4 -- communication tiers)
**Judge Verdict**: VETO (Pass 2)

### Pattern
Phase 4 added `tone_aware: true|false` to every skill's frontmatter and added a lint test verifying the flag's *presence*. It did NOT require the skill's body to contain per-tier rendering instructions, and it did NOT instruct any skill to read the persisted config `tone` value. The metadata declared an intent ("this skill can render differently per tier") without any mechanism that delivers on it. Adversarial outcome: operator runs `qorlogic init --tone plain`, observes no change in output, has no way to diagnose why -- all tests pass.

### Why It Matters
A governance framework whose features are metadata-only is worse than one that doesn't claim the feature at all: the audit trail suggests behavior that isn't there. This is the same family as Ghost UI (frontend buttons without backend handlers) but at the documentation/skill layer.

### Countermeasure
Any plan that introduces a behavioral flag in frontmatter must ALSO:
1. Require a canonical section in the skill body that implements the flag's claimed behavior (delimited by a `<!-- qor:<feature>-section -->` marker pair so lint can find it deterministically).
2. Require at least one consumer of any persisted config value the flag depends on (instruction in the skill body, or a helper function the skill calls).
3. Include a lint assertion that ties the metadata claim to the body content: `if flag == true, body must contain <marker> AND <content-assertion>`.

Without all three, the flag is a ghost.

### Pattern ID
SG-Phase25-B (metadata-only feature declaration without enforced behavior)

---

### Entry #18: VETO -- plan-qor-phase28-documentation-integrity pass 1

**Timestamp**: 2026-04-17
**Target**: `docs/plan-qor-phase28-documentation-integrity.md`
**Audit Report**: `.agent/staging/AUDIT_REPORT.md`
**Ledger Entry**: #89
**Session**: `2026-04-17T2335-f284b9`

### Pattern

Four plan-text violations on first audit pass of a doctrine-introduction plan. No implementation risk; all corrections are editorial. The spread of grounds reveals a recurring authoring risk when a plan both (a) creates a new rule and (b) must satisfy that rule itself.

1. **SG-Phase24-B recurrence** -- YAML parsing proposed for glossary frontmatter without naming `yaml.safe_load`. The mitigation test (`tests/test_yaml_safe_load_discipline.py`) already exists; the recurrence is authorial, not systemic. Still, the failure to cite the safe loader at plan-authoring time is exactly what SG-Phase24-B documents.

2. **SG-038 recurrence** -- prose-code mismatch between the schema prose (declaring a `concepts` alias of `terms`) and the adjacent JSON code block (which omits `concepts`). The alias was a leftover from the pre-dialogue draft; the Q3 decision (fold concept-map into glossary) removed the need for it. Prose updated, code did not.

3. **SG-036 new manifestation: doctrine self-application failure.** The plan codifies the rule "every plan declares `doc_tier`, `terms_introduced`, `boundaries`" but does not apply those fields to itself. SG-036 names this as "newly codified doctrine does not become automatically load-bearing in phase N+1 unless the author treats it as active" -- this plan compressed the grace-period into a single-plan failure by creating the doctrine and immediately failing to dogfood it.

4. **Rule 4 gap (Rule = Test).** Plan declared "legacy tier must include rationale" but wired only an event-emission test, not a rationale-presence enforcement test. Operator can declare `doc_tier: legacy` with no rationale; event fires; rule is unenforced.

### Why It Matters

Doctrine-introduction plans carry elevated authoring risk: the plan both introduces a standard and is the first artifact audited against it. Plans like these need a self-dogfood checklist before submission:

- Do I satisfy every rule this plan creates?
- Is every rule paired with an enforcement test?
- Are prose and code blocks cross-checked for enumeration drift?
- Am I citing safe-loaders / hardening defaults by name?

When the author skips this checklist, all four SG categories can light up at once -- as they did here.

### Countermeasure

For plans that introduce new doctrines (not just features), add a `Self-Dogfood` section at the plan's end (above `Delegation`) that explicitly asserts:

- The plan satisfies every rule it introduces (one bullet per rule, pointing at the plan text that applies it).
- Every new rule has a corresponding test in the Unit Tests list (one bullet per rule-test pair).
- No bare-word "YAML / TOML / JSON" appears without naming the safe loader.
- Every enumeration referenced in prose also appears in any adjacent code block (one cross-check bullet per enumeration).

A doctrine-introduction plan that lacks this section should be VETOed on sight.

### Pattern ID

SG-Phase28-A (doctrine-introduction plan without self-dogfood checklist)

---

### Entry #19: VETO -- plan-qor-phase29-audit-stepZ-and-contributing pass 1

**Timestamp**: 2026-04-18
**Target**: `docs/plan-qor-phase29-audit-stepZ-and-contributing.md`
**Audit Report**: `.agent/staging/AUDIT_REPORT.md`
**Ledger Entry**: #93
**Session**: `2026-04-17T2335-f284b9`

### Pattern

Two VETO grounds. The first is the important one: **a newly enforced doctrine catches its first real post-authoring violation one phase later.** Phase 28 introduced the `check_orphans` rule (every glossary entry must have a `referenced_by:` consumer OR be newly introduced in the current plan). Phase 28's own seal passed because all its entries' `introduced_in_plan:` matched the then-current plan slug. Phase 29's plan had no terms to register and no expectation that it would inherit enforcement against prior-phase entries -- but when `check_orphans` runs at Phase 29's seal, the grace-period clause no longer applies, and six Phase-28-introduced entries become expired orphans requiring adoption.

This is the doctrine working as designed, but the post-authoring effect was not anticipated by the Phase 29 plan. The plan addressed one glossary entry (`Doctrine` gains `CONTRIBUTING.md` as a consumer) without noticing that five siblings had the same exposure.

The second ground is a SG-038 recurrence in the very section Phase 28 introduced to prevent SG-038 (Self-Dogfood). Count-enumeration drift: "five" declared, six enumerated.

### Why It Matters

Newly codified enforcement doctrines create a pattern: **the first few plans authored after the doctrine lands are the ones most likely to trip it in unexpected ways.** Authors have not yet internalized the forward-propagating implications. Phase 28's authors (the same session as the doctrine's creation) satisfied every rule by intentional construction; Phase 29's authors saw the doctrine as "done" and did not scan the repo for still-exposed prior-phase artifacts.

The second ground compounds the first: even the self-dogfood checklist (itself a Phase 28 invention) carried forward a prose-enumeration inconsistency that the checklist was meant to detect.

### Countermeasure

For any plan authored in the first three phases after a new enforcement doctrine lands, add an explicit step:

1. Run the new doctrine's check helper(s) against the repo state once, BEFORE writing the plan.
2. Record the helper's output in the plan's "Basis" section.
3. If the helper reports violations, resolve them IN THE CURRENT PLAN -- do not defer.

This closes the "newly-enforced-doctrine grace gap" surfaced by Phase 29's VETO.

Concretely for Phase 29: amend Phase 2 to extend `referenced_by:` on the six orphan entries, add a test that forbids empty `referenced_by:` on any entry older than the current plan's session.

### Pattern ID

SG-Phase29-A (newly-enforced-doctrine grace gap: plans authored soon after a new enforcement doctrine fail to scan for pre-existing exposures)

---

### Entry #20: VETO -- plan-qor-phase30-system-tier-hardening pass 1

**Timestamp**: 2026-04-18
**Target**: `docs/plan-qor-phase30-system-tier-hardening.md`
**Audit Report**: `.agent/staging/AUDIT_REPORT.md`
**Ledger Entry**: #97
**Session**: `2026-04-17T2335-f284b9`

### Pattern

Two VETO grounds. The interesting one is Ground 1: **projected Razor violation from additive edits to an already-near-cap module.** `qor/scripts/doc_integrity.py` sat at 244 lines post-Phase-28 trim. Phase 30's plan proposed adding 2 functions + scope fences (~50-70 lines) to the same module, projecting ~294-314 lines -- clearly over the 250 limit.

Phase 28 tripped this exact limit once already (originally 258 lines; trimmed to 244 under seal-time pressure by stripping section-divider comments). The Phase 30 plan did not acknowledge that recurrence risk, nor propose a split or companion module.

Ground 2 is a classic assignment gap: a term declared in plan top-matter (`Session Rotation`) with `home: doctrine-governance-enforcement.md` but no phase actually modifies either the doctrine body or the glossary file to author the entry. The declaration was a metadata-only claim -- the SG-Phase25-B pattern at doctrine scope rather than skill-frontmatter scope.

### Why It Matters

**Cumulative razor creep at module scope** (adjacent to SG-Phase24-A at CLI-harness scope): monotonically additive edits to a single file across phases eventually trip the 250-line cap. The cap is a *speed bump*, not a floor -- once a module is within ~10-15 lines of it, any future additive phase must budget for a split in its own plan. The alternative (trim-under-pressure each seal) sacrifices readability incrementally and obscures the structural signal that the module needs to bifurcate.

**Metadata-only declarations at doctrine scope**: a plan's top-matter `terms_introduced:` block is a promise. If no phase's Affected Files section fulfills the promise (authoring the glossary entry + editing the declared home), the promise becomes exactly the kind of ghost feature SG-Phase25-B warned about at skill-frontmatter scope, just one layer up.

### Countermeasure

For Governor authoring:

1. **When a plan adds lines to any existing module, include the module's current line count in the plan (or the Basis section) and sum the projected delta.** If the projected total is within 20 lines of the Razor limit, propose the split or trim *in the same plan* -- do not defer.
2. **Every term in `terms_introduced:` must appear in exactly one phase's Affected Files section, covering both the glossary entry and the declared home.** Add a dogfood bullet explicitly cross-checking this: "Enumeration cross-check: every `terms_introduced:` entry resolves to one or more edits in Phase N's Affected Files."

For Judge auditing:

1. When a plan proposes additive edits to a file, `wc -l` the file and add the plan's projected delta. Flag projections within 10 lines of the 250 cap as Razor-anticipation VETO grounds. Refactor is the *mechanism*; the fix must live in the *plan* before implementation, not be deferred.
2. Walk the `terms_introduced:` list against each phase's Affected Files; flag any term not assigned to a phase as a metadata-only claim.

### Pattern ID

SG-Phase30-A (projected Razor violation from additive edits to near-cap module) + SG-Phase30-B (metadata-only term declaration at doctrine scope: term in `terms_introduced:` with no phase authoring the glossary entry + home)

---

### Entry #21: VETO -- plan-qor-phase31-operationalization pass 1

**Timestamp**: 2026-04-18
**Target**: `docs/plan-qor-phase31-operationalization.md`
**Audit Report**: `.agent/staging/AUDIT_REPORT.md`
**Ledger Entry**: #101
**Session**: `2026-04-18T1007-301fa2`

### Pattern

Two VETO grounds. The first is a new manifestation: **an in-plan "correction" that contradicts the plan's primary source of truth instead of fixing it upstream.** Phase 31's Self-Dogfood section caught a Razor risk (adding `check_documentation_currency` to `doc_integrity.py` would cross the 250 cap) and wrote a correction paragraph saying "the function goes in `doc_integrity_strict.py` instead." But the primary Affected Files section was left unchanged -- still saying the function goes in `doc_integrity.py`. The correction is right; the corrective action (editing Affected Files) was not performed.

The second ground is plan self-modification at implementation time. Phase 31 declared it would modify itself during Phase 2 execution to append triage commentary. Plans modifying themselves post-audit breaks the audit -> seal contract: content-hash at seal differs from content-hash at audit.

### Why It Matters

**SG-Phase31-A (in-plan correction instead of upstream fix)**: the Self-Dogfood pattern codified in SG-Phase28-A was meant to catch the plan applying its own doctrine. Phase 31 honored that spirit -- the Self-Dogfood section DID catch the Razor risk early. But the execution failed: instead of editing the Affected Files section (upstream fix), the plan added a parallel "correction" section (downstream patch). An implementer reading the plan top-to-bottom sees the wrong instruction first, then a correction -- race condition on who wins. Worse, automated tools (IDEs, PR reviewers) typically parse the Affected Files section as the source of truth and miss free-prose corrections elsewhere.

**SG-Phase31-B (plan self-modification risk)**: plans are the audit target. If implementation modifies the plan, the audit's content-hash no longer describes what gets sealed. The ledger chain remains cryptographically valid (each hash links), but the semantic claim "Judge approved this plan" becomes false for any text added after audit.

### Countermeasure

For plan authoring:

1. **When Self-Dogfood catches a design change, FIX IT UPSTREAM in the same edit session.** Don't write a "correction" paragraph; rewrite the Affected Files / Changes section that caused the flag. The Self-Dogfood section is a CHECKLIST, not a PATCH MECHANISM -- if it catches something, go back and fix the source of truth before saving the plan.
2. **Plans do not modify themselves at implementation time.** If a phase produces information that belongs in a plan (triage commentary, benchmark results, incident notes), extract to a separate artifact with a dated filename. The plan stays frozen post-audit.

For Judge auditing:

1. When a plan contains a "correction" paragraph that contradicts an earlier section, flag both: the contradiction AND the failure to apply the correction upstream. The correction's presence is evidence the author caught the issue; its non-application is the VETO-grade failure.
2. Walk every phase's Affected Files for self-references (the plan file listing itself as modified). Flag any self-reference as presumptive VETO unless the plan-in-question is the Phase 1 scaffold of a wholly new doctrine that legitimately iterates.

### Pattern ID

SG-Phase31-A (in-plan correction parallel to primary source of truth instead of upstream fix) + SG-Phase31-B (plan self-modification post-audit breaks audit -> seal content-hash immutability)

---

### Entry #22: post-seal failure -- README version-specific content went stale across Phase 32

**Timestamp**: 2026-04-18
**Target**: `README.md` (not a plan artifact; narrative doc)
**Context**: surfaced after Phase 32 seal when operator attempted `pip install qor-logic` and observed version mismatch across badge / "What's new" header / `qorlogic --version` / PyPI latest.

### Pattern

During Phase 31's /qor-document run I wrote a `## What's new in v0.22.0` section with v0.22.0-specific bullets into README.md. Phase 32 sealed at v0.23.0 but the /qor-document skill was not re-invoked. README still says "What's new in v0.22.0" with Phase 28-31 content and a stale nav anchor `#whats-new-in-v0220`. The Phase 31 Documentation Currency Check (/qor-substantiate Step 6.5) EXPLICITLY EXCLUDES README.md and CHANGELOG.md as "narrative entry points" -- so nothing fired.

### Why It Matters

Version-specific content in README drifts every release. My Phase 31 design call was wrong: I excluded README from Step 6.5 to prevent noise, but README is not pure narrative -- it carries version-specific claims (badges, "What's new", nav anchors, counts) that must be kept current OR made version-agnostic.

The Documentation Currency heuristic as designed catches skill/doctrine/script changes vs system-tier docs; it does NOT catch README drift even though README IS a system-tier consumer of every release.

### Countermeasure

Two-layer fix applied in this session:

1. **README rewritten to be version-agnostic**: replaced the static `## What's new in v0.22.0` section with a `## Latest release` section that points to CHANGELOG.md as the single source of truth. No version-specific content in README body; the PyPI badge auto-reflects latest published. This removes the drift surface -- there's nothing version-specific left in README to go stale.
2. **Future Phase 33 candidate**: extend Step 6.5 heuristic to include README.md and CHANGELOG.md when the triggering file class is `qor/scripts/changelog_stamp.py` or any version-bump path -- catches the narrow case where release metadata drifts.

The deeper pattern: **narrative docs that carry version-specific claims need either currency checking OR version-agnostic content.** Choose one, never neither.

### Pattern ID

SG-Phase32-B (narrative-doc version drift: README / CHANGELOG excluded from currency check but carries version-specific content that goes stale)

---

## Entry #23: seal-tag timing off-by-one — historical release tags point at pre-seal HEAD

**Timestamp**: 2026-04-18
**Target**: `governance_helpers.create_seal_tag` (Phase 13 wiring in `/qor-substantiate` SKILL.md)
**Context**: surfaced during post-Phase-32 forensics after the PR #4 amend race exposed tag/pyproject inconsistency. Traced backwards across the 4 prior release tags.

### Pattern

`governance_helpers.create_seal_tag` was called at `/qor-substantiate` Step 7.5 with no explicit commit argument, so `git tag -a` attached the tag to whatever HEAD pointed at when Step 7.5 ran. But the seal commit is not produced until Step 9.5 (several steps later). The tag therefore always pointed at the pre-seal HEAD — one commit behind the sealed content.

Confirmed for every release tag prior to Phase 33:

- v0.19.0 → 83418ff21c73f14b6c610e1b160066358875fa1d: pyproject `version = "0.18.0"`
- v0.20.0 → c26709eabd6fc87ac15e1437cb62ed494dea1020: pyproject `version = "0.19.0"`
- v0.21.0 → 8a29fd03f4937e34e60d751bfe946df088b933b1: pyproject `version = "0.20.0"`
- v0.22.0 → 4b275f0acb711a37ec4256a4c9c449d6f58533d0: pyproject `version = "0.21.0"`

v0.23.0 accidentally escaped the bug via the Phase 32 amend+retag during the PR #4 race.

### Why It Matters

Any release-automation workflow (PyPI publish on tag, GitHub release notes extraction, `pip install git+...@v{X}`) that reads the tag commit sees pyproject one version behind the tag name. The drift is invisible until someone runs `git show v{X}:pyproject.toml` or installs from the tag. Because PyPI publishing wasn't yet wired in this project, no user-visible breakage occurred — but the integrity guarantee the annotated tag exists to provide (this tag points at the sealed content) was never actually true.

### Countermeasure (Phase 33)

1. **Split the wiring**: Step 7.5 bumps `pyproject.toml` only (writes the version, no tag). Step 9.5.5 (new, post-seal-commit) captures `git rev-parse HEAD` and passes the SHA as a required `commit` positional argument to `create_seal_tag`. The tag is placed directly on the seal commit.

2. **Required parameter, no default**: `create_seal_tag(version, seal, entry, phase, klass, commit)` — `commit` has no default. Omitting it raises `TypeError`. Prevents future regression where a careless edit restores the HEAD-default behavior (doctrine: no backwards-compat hacks that preserve footguns).

3. **Rule-4 structural lint**: `tests/test_substantiate_tag_timing_wired.py` asserts (a) Step 7.5 contains `bump_version(` but NOT `create_seal_tag(`, (b) Step 9.5.5 exists and contains `git rev-parse HEAD` + `create_seal_tag(` with `commit=` kwarg. The structural test makes the skill-prose change mechanically enforceable.

4. **Historical tags left in place**: v0.19.0–v0.22.0 are not retagged. Retagging a published remote rewrites history for any downstream consumer; not worth the fix given no PyPI workflow depends on them yet. Forensic recovery: `git show v{X}:pyproject.toml` shows the pre-seal state; the seal commit itself is reachable one step forward via `git log v{X}..` on the originating phase branch.

### Pattern ID

SG-Phase33-A (seal_tag_timing: tagging before the seal commit targets the pre-seal HEAD, producing off-by-one release tags across v0.19.0–v0.22.0)

---

## Entry #24: hardcoded CLI __version__ drift across six releases

**Timestamp**: 2026-04-19
**Target**: `qor/cli.py` `__version__ = "0.18.0"`
**Context**: surfaced during Phase 33 post-seal smoke test. `qorlogic --version` reported `0.18.0` after installing v0.24.0 from PyPI.

### Pattern

`qor/cli.py:13` held a hardcoded string `__version__ = "0.18.0"`. Between v0.18.0 and v0.24.0, the version bump happened six times in `pyproject.toml` (authored by `governance_helpers.bump_version` at `/qor-substantiate` Step 7.5) but the CLI constant was never touched because nothing mechanically linked the two. `pip show qor-logic` reported the correct version (reads pyproject metadata); `qorlogic --version` reported the stale string.

### Why It Matters

Third recurrence of the same root pattern:
- SG-Phase32-B: README's `## What's new in v0.22.0` heading survived into v0.23.0.
- SG-Phase33-A: annotated tag placed on pre-seal HEAD targeted stale `pyproject.toml`.
- SG-Phase34-A (this): CLI `__version__` string literal drifted from pyproject for six releases.

Common mechanism: **state duplicated away from its single source of truth drifts silently because nothing mechanically updates the duplicate at version-bump time.** Whenever governance owns the canonical version (pyproject.toml), any other place that names a version must either be mechanically regenerated from that canonical OR read it at runtime.

### Countermeasure

Two-layer fix:

1. **Immediate (this hotfix)**: replace the hardcoded literal with runtime lookup:
   ```python
   from importlib import metadata
   try:
       __version__ = metadata.version("qor-logic")
   except metadata.PackageNotFoundError:
       __version__ = "0+unknown"
   ```
   Once-and-done; future bumps never need a cli.py edit.

2. **Regression guard (this hotfix)**: `tests/test_cli_version_from_metadata.py` carries two tests:
   - `test_cli_version_matches_package_metadata`: asserts module-level `__version__` agrees with `importlib.metadata.version("qor-logic")`.
   - `test_cli_version_not_hardcoded_literal`: Rule-4 structural lint — `cli.py` source must not carry a SemVer-shaped string literal on any `__version__ = ...` line. Prevents regression to hardcoding.

3. **Future Phase 35 candidate**: extend the Rule-4 structural lint to ALL source files — grep for SemVer-shaped string literals outside `pyproject.toml`, `CHANGELOG.md`, `META_LEDGER.md`, and `SHADOW_GENOME.md` (the legitimate holders of historical version strings). Any match in `qor/**/*.py` that's not fetching from metadata becomes a seal-time failure. Catches any future hardcoded-version creep across the codebase in one sweep.

### Pattern ID

SG-Phase34-A (hardcoded version drift: module-level constant duplicating pyproject version drifted across six releases because nothing mechanically coupled the two)

---

## Entry #25: installed-mode breakage across seven releases

**Timestamp**: 2026-04-19
**Target**: `qor/skills/**/SKILL.md` Python blocks + `qor/reliability/*.py` subprocess invocations + 2 bare intra-`qor/scripts` imports
**Context**: surfaced when user reported `pip install qor-logic` produces a package whose skills cannot actually execute because every governance-helper import fails with `ModuleNotFoundError`.

### Pattern

Skill prose (SKILL.md Python blocks) embedded the CWD-dependent hack `import sys; sys.path.insert(0, 'qor/scripts'); import gate_chain`. Works if CWD happens to be the Qor-logic repo root; fails on every `pip install` user because the operator's CWD is their own project root, not the Qor-logic repo, and `qor/scripts/` does not exist there. 49 occurrences across 12 skill files shipped this broken pattern from v0.18.0 onward.

Compound breakage: `qor/reliability/` shipped hyphen-named files (`intent-lock.py`, `skill-admission.py`, `gate-skill-matrix.py`) — invalid Python module names. Skill prose invoked them as `python qor/reliability/intent-lock.py ARGS`, CWD-dependent and non-importable. Intra-`qor/scripts` bare imports (`doc_integrity.py: import shadow_process`; `doc_integrity_strict.py: from doc_integrity import parse_glossary`) piggybacked on the hack — only worked when some earlier skill code had prepended `qor/scripts/` to `sys.path`.

### Why It Matters

Fourth recurrence of the broader "**installed artifact diverges from dev-environment artifact**" family, after SG-Phase32-B (README version), SG-Phase33-A (seal-tag timing), SG-Phase34-A (CLI `__version__`). The three earlier drifts were cosmetic/metadata. This one is operational: the package's headline feature (runnable governance skills) was non-functional for every user who ran `pip install qor-logic` from outside the repo clone. The Release workflow published a broken package to PyPI for six sequential releases (v0.18.0–v0.24.1) without any regression guard catching it, because the repo's own tests always ran from repo root where the CWD assumption happens to hold.

### Countermeasure

Phase 35 ships:

1. **Runtime fix**: all 49 skill-prose occurrences rewritten to `from qor.scripts import X`. Reliability scripts renamed to snake_case; skill invocations rewritten to `python -m qor.reliability.<name>`. Two bare imports qualified.

2. **Regression guards** (`tests/test_installed_import_paths.py`): four tests locking structural (no hack patterns) + runtime (imports resolve) contracts.

3. **Doctrine**: `doctrine-governance-enforcement.md` §9 "Installed-Mode Invariants" codifies the three rules so future skill authoring cannot re-introduce the pattern.

4. **Phase 36 candidate**: extend the structural lint to any Python source file embedding repo-layout assumptions (`sys.path.insert.*qor/`, bare in-tree imports, `Path("qor/...")` literals). Sweep for where else the same family might hide.

### Pattern ID

SG-Phase35-A (installed-mode breakage: skill Python blocks + subprocess invocations + bare intra-package imports assumed repo-root CWD; package was non-functional for pip-installed users across v0.18.0–v0.24.1)

---

## Entry #26: plan/audit/replan loop without execution handoff

**Timestamp**: 2026-04-19
**Target**: `/qor-plan` ↔ `/qor-audit` ↔ `/qor-remediate` orchestration boundary
**Context**: External postmortem from an operator running Qor-logic skills on another codebase. Reported verbatim by the operator for pattern capture. The loop consumed multiple planning/audit cycles without converting remediation plans into code changes; observed blockers remained on-disk unchanged across cycles.

### Pattern

Operator enters `/qor-plan` → `/qor-audit` returns VETO on structural findings. Operator narrows the remediation plan and re-enters `/qor-audit`. Audit re-inspects repo state (not plan intent), finds the same unresolved structural issues, returns VETO again. Operator re-narrows the plan. Repeat.

Observed concrete blockers that persisted unchanged across multiple plan/audit cycles (external system):

- `docs/CONCEPT.md` still missing
- `src/matchmaker/loop.ts` still depended on `src/router.ts`
- Router still owned `lastPairAt`
- Files marked for relocation still located under `src/`
- Razor overages still present
- Test suite not green

**What iterated**: remediation design. **What did not iterate**: remediation execution. The loop was planning/audit → planning/audit, bypassing `/qor-implement` entirely because VETO was treated as binding (correct gate behavior in isolation) without a mechanical surface for "plan is already correct; execute it."

### Root-cause classification (per operator)

- **Not primarily `/qor-audit`**: audit checked actual repo state and correctly returned VETO each cycle. Audit behaving as designed.
- **Partly `/qor-plan`**: planning flow kept regenerating plans instead of forcing handoff to `/qor-implement` once the remediation was already obvious. No cycle-count threshold exists for "stop replanning."
- **Primarily orchestration**: operator allowed the loop to continue instead of either (a) running the already-obvious implementation pass, or (b) explicitly bypassing Qor gating to patch directly. Neither was done cleanly.

### Why existing countermeasures did not catch this

Verified against `qor/skills/sdlc/qor-remediate/SKILL.md`:

1. **HIGH — Step 4 closes events before downstream review** (lines 93-104 vs constraint at line 122). `mark_addressed` writes `addressed: true` immediately; the gate artifact for downstream audit is not emitted until Step 5. Per line 122 constraint, remediation is advisory until reviewed — but Step 4 already flipped the flag. Unresolved process failures can appear "addressed" in the shadow log before any review gate accepts them. This masks recurrence.

2. **MED — `gate-loop` detector too narrow** (line 72). Defines gate-loop as ≥2 `gate_override` events in the same group. The observed loop produced zero overrides — plans failed audit cleanly and restarted planning. The classifier would not have fired. A second, complementary pattern is needed: `plan-replay` or `replan-without-implement`, triggered by N consecutive `/qor-plan` invocations targeting stable findings-signature with no intervening `/qor-implement` in the session timeline.

3. **MED — no automatic escalation** from `/qor-plan` or `/qor-audit` to `/qor-remediate` on repeat-failure. Current delegation (per `qor/gates/delegation-table.md`): audit VETO → `/qor-refactor` or `/qor-organize`; plan complete → `/qor-audit`. Cycle-count escalation is absent. After K audit VETOs citing the same findings class, the legal next move should be `/qor-remediate` (process-level concern), not another `/qor-plan` round.

4. **LOW — CI-command field in plan has no template slot.** `qor/skills/sdlc/qor-plan/SKILL.md` §Constraints mandates CI commands in every plan; the plan-body template and `plan.schema.json` do not declare where they live. Inconsistent plan shape predictably results.

### Why It Matters

The loop is not a gate failure — it is a *gate success* that stalls. Each individual skill behaves correctly; the composition produces stall. This is exactly the class of process failure that `/qor-remediate` was designed to catch, and the current classifier does not catch it. Without a countermeasure, the loop is repeatable by design: any remediation plan whose audit still finds remaining blockers triggers replan-without-implement by default, and nothing in the current framework surfaces the stall to the operator.

Operator's own summary: *"We iterated on remediation design, not remediation execution."*

### Countermeasure (proposed; not yet implemented)

Handoffs required, in priority order:

**C1 (HIGH) — Fix Step 4/Step 5 ordering in `/qor-remediate`.** `addressed: true` must not be written until the gate artifact has been consumed by a downstream review (at minimum, a subsequent `/qor-audit` cycle that PASSes on the remediation proposal). Two-stage flip: `addressed_pending: true` at Step 4; `addressed: true` only after review-pass. Requires schema update + `mark_addressed` refactor + regression test asserting no event carries `addressed: true` without a paired review-pass event.

**C2 (MED) — Add `plan-replay` classifier** to `/qor-remediate` Step 2. Pattern definition: ≥K consecutive `plan_complete` events in a session timeline with no intervening `implement_complete` or `debug_complete`, optionally filtered by findings-signature stability across the plan cycles. K=2 is aggressive; K=3 is safer. Tuning is a live question.

**C3 (MED) — Automatic `/qor-remediate` escalation** from `/qor-plan` and `/qor-audit` on cycle-count threshold. Planner / auditor consult session history; on Nth consecutive failure against stable findings signature, the "next action" emission switches from `/qor-audit` / `/qor-refactor` to `/qor-remediate` with `escalation_reason: "cycle-count"`. Operator may override but the override is recorded as a severity-2 `orchestration_override` shadow event — which then feeds back into the gate-loop classifier.

**C4 (LOW) — Plan template must carry a `ci_commands` field** with a schema-enforced location. Removes the inconsistency by making the field non-optional in shape, not just in constraint prose.

None of C1-C4 remove the operator's responsibility to close the loop. What they add is a mechanical surface for the stall pattern: classifier, escalation trigger, event-state integrity. The operator-judgment layer (the "plan is already correct; execute it" call) remains in the operator.

### What this entry is NOT

This entry does not propose or execute fixes. Per `/qor-remediate` doctrine, remediation is advisory until reviewed. The fixes above are the review input; the review is the next `/qor-plan` cycle that consumes this SG entry as source material.

Not closing this SG entry as addressed. `addressed: false` until the countermeasures ship and pass their own audit.

### Pattern ID

SG-PlanAuditLoop-A (plan/audit/replan loop without execution handoff: the framework continued to accept new plan submissions against stable findings-signature failures, producing no code change across multiple cycles; no mechanical stall surface existed — see C1-C4 countermeasures)

---

## Entry #27: VETO — plan-qor-phase36-planaudit-loop-countermeasures v1

**Timestamp**: 2026-04-19
**Target**: `docs/plan-qor-phase36-planaudit-loop-countermeasures.md`
**Audit Report**: `.agent/staging/AUDIT_REPORT.md`
**Ledger Entry**: #118
**Pass**: 1

### Failure Patterns

**Schema-migration blindness.** Phase 1 adds a required field (`addressed_pending`) to the shadow_event schema with zero migration strategy for existing events. Every event currently in `PROCESS_SHADOW_GENOME.md` and `...UPSTREAM.md` would fail validation on first post-seal read. Same class as hardcoded-version drift (SG Phase 34): the schema is a source of truth, and any change to its required set is a migration event.

**Cross-phase source artifact inconsistency.** Phase 2's `findings_signature` computes from an audit-report markdown file; Phase 3's `cycle_count_escalator` computes from audit gate artifacts. These are different artifact classes — one narrative, one schema-validated JSON. The audit gate schema does not currently carry findings categories. The plan requires a schema extension that it does not declare. State-duplicated-from-source-of-truth in planning form: the same concept ("findings signature") lives in two places without a canonical source.

**Open-enum invitation.** Plan's `findings_signature` hashes categories described as "e.g., razor-overage, import-coupling, ...". "E.g." instead of a closed enum opens the same drift the plan is trying to prevent (Phase 32-35 family). Category stability depends on audit emission discipline, not a mechanical constraint. One string-casing drift and signatures stop matching semantic equivalents — stall classifier goes blind.

**Event-type/classifier mismatch.** Plan adds `orchestration_override` as a new event_type and asserts via test that the gate-loop classifier fires on two of them. Gate-loop classifier keys on `gate_override`, not `orchestration_override`. Plan mechanism does not match plan test — internal inconsistency at the specification level.

**Razor pre-audit impossibility.** Five new or refactored scripts; zero LOC estimates. Judge cannot pre-check Section 4 compliance. Not a Razor violation (code isn't written yet), but a blocker to pre-implementation audit.

### Lesson

The plan to catch plan/audit/replan stalls is itself a stall-prone plan-specification artifact. Meta-lesson: specification precision requirements apply recursively. A plan that declares multi-phase state changes, cross-phase data flows, and schema-enum additions must close those contracts in the plan, not in the implementation-discovery phase.

Intent was correct. Specification was under-closed. Exactly the failure mode the Judge exists to catch pre-implementation — and exactly the recurrence class the plan aims to add machinery for. The machinery must be specified to the precision it is designed to enforce.

### Remediation

5 mandatory V-items + 8 F-items in audit report §Mandated amendments / §Secondary findings. Governor amends and resubmits. Not a `/qor-organize` handoff (no topology issue); not a `/qor-refactor` handoff (no code yet). Return to `/qor-plan`.

### Pattern ID

SG-Phase36-A (pending): specification drift in a plan whose explicit purpose was to add anti-drift machinery. Not sealed as a canonical pattern until the amendment outcome shows whether this is a one-time planning miss or a recurring authoring pattern that needs its own countermeasure in `/qor-plan`.

---

## Entry #28: VETO — plan-qor-phase36-planaudit-loop-countermeasures v2

**Timestamp**: 2026-04-19
**Target**: `docs/plan-qor-phase36-planaudit-loop-countermeasures.md` (Pass 2)
**Audit Report**: `.agent/staging/AUDIT_REPORT.md`
**Ledger Entry**: #119
**Pass**: 2

### Pass 1 → Pass 2 progression

Pass 1 issued 5 VETO findings (V1-V5) + 8 secondary (F1-F8). Pass 2 amendment resolved V1-V5, F1-F4, F6-F8 substantively; F5 disclosed in limitations. Signature shifted: Pass 1 emitted 4 categories (`schema-migration-missing`, `macro-architecture`, `specification-drift`, `razor-overage`); Pass 2 emits 2 (`specification-drift`, `macro-architecture`). Different signatures — `plan-replay` classifier would not fire. This is iterative refinement, not stall.

### Failure Patterns (Pass 2)

**Schema narrative vs schema JSON drift (V6).** Plan text states `findings_categories` is required on VETO artifacts; the JSON schema snippet in the plan does not encode this. The plan's own grounding-protocol claim (specification must close contracts in the plan itself) is violated by the plan. Second-order occurrence of the state-duplicated-from-source-of-truth family (SG Phase 32-35) — the CLAIM and the SCHEMA are two copies of one contract, and they disagree.

**Legacy-artifact false-positive stall (V7).** `findings_signature` treats absent `findings_categories` as empty-list → stable hash. Any session containing ≥3 pre-Phase-36 VETO audit artifacts (such as the Pass 1 audit from earlier this session) would produce three identical "empty" signatures, firing cycle-count escalation on what is actually legacy data. The mechanism must distinguish "field absent" from "categories empty."

### Lesson

Second-order drift: amendments resolve named findings but can introduce fresh ones from the same family. The Judge caught one instance of specification-drift (V6) as part of resolving three others (V2, V3, V4). Progress is real; completeness is not. This is exactly the expected behavior when the defect family is recursive — each round surfaces instances previously hidden behind coarser drift.

Not a stall signal. Pass 1→Pass 2 signature changed; Pass 2→Pass 3 amendment will be narrower (no HIGH findings to resolve, only two MED + three LOW).

### Remediation

5 items (V6, V7, F9, F10, F11) in audit report §Mandated amendments. Governor amends and resubmits. No delegation triggers (topology, code-shape, remediate all unaffected). Return to `/qor-plan`.

### Pattern ID

SG-Phase36-A (still pending): one more instance of specification drift, surfaced by the Judge in adversarial mode. Pattern is provisionally a recurring authoring concern rather than a one-time miss. If Pass 3 introduces a fresh drift instance, escalate to a proper Pattern ID with countermeasure proposal for `/qor-plan` grounding protocol.

---

## Entry #29: VETO — plan-qor-phase36-planaudit-loop-countermeasures v3

**Timestamp**: 2026-04-20
**Target**: `docs/plan-qor-phase36-planaudit-loop-countermeasures.md` (Pass 3)
**Audit Report**: `.agent/staging/AUDIT_REPORT.md`
**Ledger Entry**: #120
**Pass**: 3

### Pass 2 → Pass 3 progression

Pass 2 findings V6, V7, F9, F10, F11 all resolved (verified). One new drift (V8) was introduced by Pass 3's F9 decomposition — the function-split specification omitted the timestamp field the orchestrator needs. One pre-existing drift (V9) surfaced for the first time — `plan-replay` classifier consumes event types that are never emitted. Judge acknowledges V9 as prior-pass miss; not Governor fault.

### Failure Patterns (Pass 3)

**Decomposition omitted data carrier (V8).** Pass 3 split `cycle_count_escalator.check` into four functions with explicit return types. The orchestrator body references a value (`first_match_ts`) that is not in any helper's return signature. Inline handwaving via `<ts of earliest matching audit in the run>` — pseudocode placeholder where a declared data flow was required. Third-order drift: resolving F9 (decomposition clarity) introduced V8 (interface incompleteness).

**Classifier input plumbing never declared (V9).** Phase 2's `plan-replay` classifier triggers on `plan_complete`/`implement_complete`/`debug_complete` events. These events exist nowhere in the event_type enum and no skill emits them. The classifier has output plumbing (enum addition for `plan-replay`) but no input plumbing. Functional wiring reversed: pattern-output is declared; pattern-input data source is implicit and unsatisfied.

### Lesson

Third consecutive pass with specification-drift findings in the same defect family. Pattern is crystallizing: amendments against tight scope still leak drift instances — because the defect class (SG Phase 32-35 family) is recursive. Each pass resolves named instances while the authoring surface keeps exposing new ones.

Signature-stability observation: Pass 2 and Pass 3 emit identical findings categories `[specification-drift, macro-architecture]`. If Pass 4 also VETOs on this signature, the classifier under design would fire at K=3 — the plan-for-stall-detection iterating against a stable findings signature is itself a textbook stall. The irony is not lost on the Judge.

### Remediation

2 V-items (V8, V9) in audit report §Mandated amendments. Narrow. No LOW findings. Governor amends and resubmits. No delegation triggers — structural issues remain in specification, not topology / code / process.

### Pattern ID

SG-Phase36-A (confirmed recurring): three consecutive passes with specification-drift findings confirms this is a recurring authoring pattern, not a one-time miss. Deserves its own countermeasure in `/qor-plan` grounding protocol. Current candidate countermeasure: when plan declares multi-function decomposition, lint that every value referenced in one function's body originates from a declared return or parameter (catches V8 class). When plan declares a classifier, lint that every event type in the classifier trigger exists in the event-type enum (catches V9 class). Deferrable to a follow-up phase; not required to land Phase 36.

---

## Entry #30: VETO — plan-qor-phase36-remediate-two-stage-flip v1 (rescoped)

**Timestamp**: 2026-04-20
**Target**: `docs/plan-qor-phase36-remediate-two-stage-flip.md` (Pass 1 of rescoped plan)
**Audit Report**: `.agent/staging/AUDIT_REPORT.md`
**Ledger Entry**: #123
**Pass**: 1 (of rescoped plan)

### Scope context

Rescope accepted 2026-04-20 after 4 passes on prior Phase 36 plan surfaced V1-V10. Rescoped plan targets B19 only — zero infrastructure dependency. Smaller scope = smaller finding surface.

### Failure Pattern

**Review-pass detection coarseness.** Plan's `/qor-audit` Step 4 integration detects "this audit reviews a remediation" via `remediate.json` file presence in the session. File presence is too weak a signal — any session that invoked `/qor-remediate` carries `remediate.json` indefinitely. PASS audits on unrelated plans later in the same session would fire the flip. Second-level disambiguation via `reviews_remediate_gate` field verification exists in the plan but its set-path is undefined.

Not a specification drift or infrastructure mismatch in the SG-Phase36-A family — this is a domain-logic wiring gap. Distinct class from prior passes.

### Lesson

Even with tight scope and infrastructure-alignment discipline, domain-logic wiring requires explicit intent signals. "Detect by file presence" is a common attractor because it requires no ceremony, but it conflates "remediate was invoked" with "this audit reviews that invocation." Intent must be carried explicitly.

### Remediation

V1 resolution: pick (a) operator flag, (b) proposal-plan linkage, or (c) manual closure. Narrow amendment.

### Pattern ID

No new SG pattern ID. V1 is a standard wiring-clarity finding, not a member of any recurring family documented in the shadow log.

---

## Entry #31: VETO — plan-qor-phase42-changelog-tag-coverage-fix v1

**Timestamp**: 2026-04-24T20:55:00Z
**Target**: `docs/plan-qor-phase42-changelog-tag-coverage-fix.md` (Pass 1)
**Audit Report**: `.agent/staging/AUDIT_REPORT.md`
**Ledger Entry**: #134
**Pass**: 1

### Failure Mode

COVERAGE_GAP (plan-text ground)

### What Failed

Plan addresses only one of two symmetric tests in `tests/test_changelog_tag_coverage.py`. The unaddressed test (`test_every_tag_has_changelog_section`) is already latently broken on main and will surface at Phase 42's own CI run after its v0.28.2 tag pushes to origin without a matching CHANGELOG section.

### Why It Failed

Author anchored on the PR-CI symptom (PRs #10/#11 failing on the orphan-section direction) and scoped the plan to that symptom. The reverse-direction test was already failing in a dormant state because main CI last ran before v0.28.1 tag was pushed — the failure was invisible until the next CI trigger. Scoping to "the visible failure the PRs hit" missed "the latent failure the fix itself will trigger."

### Pattern to Avoid

When fixing a CI test that's part of a symmetric pair, run BOTH tests locally against the current main state before scoping the plan. If the complementary test is already failing (or will fail under the fix's own state change), fold the adjacent fix into the same phase rather than shipping a partial resolution that lands broken main state.

General heuristic: "tests come in pairs" is itself a flag. When the test file defines two tests that enforce bidirectional equality, any fix that relaxes one direction should be accompanied by a current-state check on the other.

### Remediation Attempted

Pending Governor amendment. Audit directs: add CHANGELOG.md edit to Phase 1's Affected Files — backfill `## [0.28.1]` (Phase 40 retrospective summary) and add `## [0.28.2]` (this hotfix summary). No new tests needed; existing tests will enforce correctness once sections are present.

### Pattern ID

No new SG family ID. This is a coverage-gap finding similar in structure to Phase 41 Pass 1's V1 (both missed adjacent-test state that the fix itself would affect). Two occurrences is suggestive but not yet a sealed pattern; watch for third occurrence.

---

## Phase 47 Pass 1 — VETO

**Date**: 2026-04-28
**Verdict**: VETO (L2)
**Categories**: `infrastructure-mismatch`, `prose-code-mismatch`, `injection-risk`

### Findings

V-1: New gate `seal_entry_check` wired into `/qor-substantiate` Step 4.6 (Reliability Sweep). Step 4.6 runs at [SKILL.md:192](qor/skills/governance/qor-substantiate/SKILL.md), *before* Step 7 (Final Merkle Seal, [SKILL.md:266](qor/skills/governance/qor-substantiate/SKILL.md)) writes the SESSION SEAL ledger entry the check is supposed to verify. Check would always fail because its precondition (latest entry is SESSION SEAL for current phase) is structurally false at Step 4.6 time.

V-2: `$MERKLE_SEAL` referenced in wiring but never defined. Computed at Step 7; undefined at Step 4.6.

V-3: `python -c "...derive_phase_metadata('$PLAN_PATH')[0]"` — shell-injection vector. Single-quoted Python literal with unescaped shell-variable interpolation (OWASP A03).

### Root Cause Analysis

Plan's prose acknowledges the dependency ("runs LAST because it requires the seal entry to be written by Step 7") but the implementation block places it in Step 4.6 anyway. SG-038 direct hit (prose-code mismatch in plans). The plan author inferred placement from the existing pattern (other reliability gates live in Step 4.6) without verifying the new gate's precondition is satisfied at that step. Pattern: borrowing the location of structurally-similar gates without re-validating the structural constraint that justified each one's location.

### Pattern to Avoid

When adding a new reliability gate to an existing skill's step-numbered protocol, the plan must trace each precondition the gate depends on back to the skill step that establishes it. "Place it next to the other gates" is location-by-association, not location-by-precondition. Each gate's location is determined by its dependency graph, not by its taxonomic siblings.

### Remediation Attempted

Pending Governor amendment. Audit directs: restructure Phase 2 to place `seal_entry_check` in a new step *after* Step 7 (Final Merkle Seal), define how `$MERKLE_SEAL` is acquired (Step 7 export, or helper reads ledger directly), and replace shell-interpolation `python -c "...('$VAR')..."` with argv-form invocation.

### Pattern ID

Reinforces SG-AdjacentState-A family (seventh instance — first to surface during `/qor-audit` on its own remediation phase, ironically). The countermeasure Phase 47 itself proposes (post-seal verification) would, if generalized to "verify substantiate-step preconditions at audit time", catch this exact wiring defect. Recursive scope worth tracking for a later phase: an audit pass that simulates the plan's wiring against the substantiate skill's actual step ordering and aborts on precondition mismatch.

---

## Phase 47 Pass 2 — VETO

**Date**: 2026-04-28
**Verdict**: VETO (L1)
**Categories**: `infrastructure-mismatch`, `prose-code-mismatch`

### Findings

V-1 (Pass 2): Bash plan-path derivation `PLAN_PATH=$(cat .qor/session/current 2>/dev/null | xargs -I{} ls docs/plan-qor-phase{}*.md 2>/dev/null | head -1)` is structurally broken. The session file format is `2026-04-28T0247-92f578` (date-time-hex); plan filenames match `plan-qor-phaseNN-slug.md` where NN is the phase number derived from the git branch via `governance_helpers.current_phase_plan_path()`. The `xargs -I{}` glob substitutes the session ID into a pattern that matches nothing; `$PLAN_PATH` expands empty, the helper receives `--plan ""`, substantiate aborts with a confusing error.

### Root Cause Analysis

Pass 1 directive specified "argv-form CLI invocation" as remediation for V-3 (shell injection). Pass 2 followed the directive — CLI uses argparse, no shell interpolation into Python literals. **But the directive did not specify how the bash should populate the argv.** Pass 2 author improvised a session-id-based glob, did not verify it against the actual plan-filename convention, and labeled the alternative path "Or equivalent: derive PLAN_PATH from the phase branch name. Whatever the operator's preferred resolution, the helper reads it via argv." The hand-waving leaves the implementer to pick a derivation at implement time — exactly the SG-AdjacentState-A pattern Phase 47 was designed to prevent.

### Pattern to Avoid

Audit directives that specify "use X" without specifying "how to obtain X" leave a wiring slip surface. When a Pass-N audit redirects a plan toward a different wiring shape, the Pass-(N+1) plan must demonstrate the new shape with verified-working code, not an example-and-equivalent stub. The grounded mechanism (`current_phase_plan_path()`) was already in the codebase; the plan should have called it directly.

### Remediation Attempted

Pending Governor amendment. Audit directs two acceptable single-line fixes (Option A: replace bash with `PLAN_PATH=$(python -c "from qor.scripts.governance_helpers import current_phase_plan_path; print(current_phase_plan_path())")` — no shell-variable interpolation, calls grounded helper. Option B: drop `--plan` from CLI; helper calls `current_phase_plan_path()` internally; smallest API).

### Pattern ID

SG-AdjacentState-A eighth instance. Two consecutive VETOs on the same plan, both citing wiring defects in `/qor-substantiate` step integration. Phase 47 plan literally proposes a runtime check for "skill prose vs runtime mismatch" — and its second pass exhibits the very pattern in its own bash. Worth flagging for a future SG family promotion: every reliability-gate plan needs explicit bash-tested derivation paths, not hand-waved equivalents. Recursive: the structural countermeasure Phase 47 proposes would, if generalized to audit-time enforcement, catch this exact slip on Pass 1 (and the Pass 1 slip too).

---

*Shadow integrity: ACTIVE*
