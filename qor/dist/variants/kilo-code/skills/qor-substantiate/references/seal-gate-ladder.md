# Seal-gate ladder — per-gate rationale

Extended rationale for the `/qor-substantiate` Step 4.6.x / 4.7.x reliability and
integrity gate ladder. Held here (not inline in `SKILL.md`) per GH #92
progressive disclosure: the Judge loads this file only when investigating why a
particular gate exists or what recurrence it closes. SKILL.md carries each gate's
runnable command + ABORT/WARN posture + Phase 75 prerequisite line + a one-line
pointer to this file. New gates extend the ladder forward; existing gates are not
reordered.

---

## Step 4.6.5 — Secret-scanning gate (Phase 56 wiring)

Pre-seal scan over staged content. Closes OWASP LLM Top 10 LLM06 (Sensitive
Information Disclosure) and NIST AI 600-1 §2.10. Drives the previously dormant
`has_hardcoded_secrets` Cedar attribute (rule on books since Phase 23). ABORT
semantics on non-zero exit: the operator must remediate detected secrets (remove
from staging, redact, or add to allowlist when literal-match false-positive)
before re-running substantiation. Findings JSON written to
`dist/secrets.findings.json` in gitleaks v8 schema for downstream tool
compatibility.

## Step 4.6.6 — Procedural-fidelity check (Phase 58 wiring)

Static-analysis pass over the implement-gate `files_touched` set. WARN-only:
deviations append severity-2 events to the Process Shadow Genome but do NOT abort
substantiate. Catches the doc-surface coverage gap (skill / script / doctrine /
schema changes without at least one update to `docs/SYSTEM_STATE.md`,
`docs/operations.md`, `docs/architecture.md`, or `docs/lifecycle.md`). Operator
reviews `dist/procedural-fidelity.findings.json` after seal; remediation lands in
the next seal cycle. See `qor/references/doctrine-procedural-fidelity.md` for the
four-class deviation catalog and remediation workflow.

## Step 4.6.7 — Definition of Done check (Phase 92 wiring; GH #86)

WARN-only structural check that the plan's `## Definition of Done` section is
well-formed. Per `qor/references/doctrine-definition-of-done.md`, every
deliverable declares D1 (vision/spec), D2 (code), D3 (governance), and D4
(empirical verification) acceptance criteria; D4 may instead carry a `D4.d`
waiver with rationale and a follow-up phase reference. V1 enforces only the
contract's presence; V2 (deferred) will verify the truth of D4 via test-name
extraction + pytest-output cross-reference. `PLAN_PATH` is consumed only as an
argv argument (SG-Phase47-A; no `python -c "...${VAR}..."` interpolation).
Findings (`missing-dod-section`, `deliverable-missing-tier`,
`waiver-without-rationale`, `waiver-without-followup`) are surfaced but do NOT
abort. Per `qor/references/doctrine-shadow-genome-countermeasures.md`
`SG-DoDImplicit-A`.

## Step 4.6.8 — Merge-velocity throttle check (Phase 93 wiring; GH #89; fail-closed since Phase 129, GH #153)

Fail-closed throttle on stabilization-capacity strain from `origin/main`'s recent
merge history. The sibling-workspace originating recurrence (27 PRs / 14,758 additions /
repair cluster #346-#353 / failing e2e on tail PR #354 in a single window) showed
that throughput, branch integration, and shared-surface expansion can exceed the
rate at which the project can reliably absorb changes. The CLI exits 0 on
`healthy`/`strained` and exits 1 on `exceeded`, which now ABORTs the seal (Phase
129 removed the `|| true`). To seal anyway during a deliberate high-velocity
window, re-run with `--override`: it emits a logged `gate_override` shadow event
(`details.gate = merge_velocity_check`) and passes — the explicit
operator-authorized escape the #153 AC requires. Operators may add
`--shared-core-path` patterns so shared-surface touches count toward the
threshold. Per `qor/references/doctrine-shadow-genome-countermeasures.md`
`SG-MergePaceThrottle-A`.

## Step 4.6.9 — Skill-corpus size-budget lint (Phase 95 wiring; GH #92)

WARN-only per-skill size-budget lint that walks `qor/skills/**/SKILL.md` and
surfaces a finding for each SKILL.md exceeding the size thresholds (WARN at 25
KB, EXCEEDED at 40 KB). Per `SG-SkillCorpusGrowth-A`, the canonical SKILL.md
corpus grew from 91 KB / 3024 lines (Phase 0) to 282 KB / 6766 lines (Phase 81)
in 6 weeks — monotonic, never contracted, with no consolidation counterweight.
CLI exits 1 when any EXCEEDED finding (>= 40 KB) is present, which is what let
V2 convert the gate to a hard ABORT. **V2 (Phase 234; GH #320)**: the ladder row
dropped the true-wrap -- the superseded V1 command was
`qor-logic scripts skill_size_budget_lint || true` --
and the row's policy reads ABORT. WARN-band findings remain advisory; only an
EXCEEDED finding (the CLI's sole exit-1 condition) now aborts the seal. No
override path: a size breach is self-inflicted by the sealing phase's own edits,
is preceded by two earlier signals (the 25 KB WARN and the headroom tests), and
resolves mechanically via the progressive-disclosure refactor recommended since
Phase 95. Operator-actionable: skills exceeding
the WARN threshold are candidates for progressive-disclosure refactor (move
sub-pass / step prose to `references/` files); skills exceeding EXCEEDED are
overdue. (Phase 135 brought `qor-audit` + `qor-substantiate` back under EXCEEDED
via exactly this refactor.)

## Step 4.6.10 — Data-API access-control lint (Phase 121 wiring; GH #177)

Static scan over the target repo's SQL migrations. Fail-closed on blocking
findings (`missing-grant` — an API-schema `CREATE TABLE` with no `GRANT` to
authenticated/anon and no service-role-only marker; `definer-view` — a view
without `security_invoker = true`). `security-definer-fn` is advisory. Closes the
privileged-principal false-PASS surface from GH #177 (a feature broken for its
authenticated caller sealing green because tests ran under `service_role`).
Escapes: `-- qor:service-role-only` (intentional service-role-only table) and
`-- qor:definer-view-intended reason: ...` (intentional definer view). On
hosts/repos with no SQL migrations the lint prints a `SKIP:` line and exits 0
(disclosed-skip). Full contract:
`qor/references/doctrine-runtime-principal-fidelity.md`.

## Step 4.7.5 — Governance Index enforcement (Phase 120 wiring; GH #149)

Makes the Hierarchical Governance Index self-policing (closes #140's deferred
enforcement half). The gate auto-advances `Last Reviewed` to the seal date
(clearing `stale-tier1` by construction) and then fail-closes on residual drift:
`unregistered` (a governance doc named in no tier — operator registers it) and
`tier3-unarchived` (a Tier 3 "Active Initiative" row naming a `phase <N>` already
SESSION-SEALed — archive it to Tier 6). On non-zero exit the operator registers
the new doc to a tier or archives the sealed Tier 3 row, then re-runs. The
advanced `docs/GOVERNANCE_INDEX.md` is staged with the seal commit. Per
`qor/references/doctrine-governance-index.md` "V2 (Phase 120; GH #149) -- shipped
enforcement".

## FEATURE_INDEX surface-tag lint (Phase 138 wiring; GH #196 V1)

Step 7 of the FEATURE_INDEX verification pass (after the Step 6 regression
ABORT). WARN-only: `qor-logic scripts feature_index_verify --surface-lint
--session "$SESSION_ID" --repo-root .` always exits 0. When the repo's
`FEATURE_INDEX.md` header declares a `Surface` column, every non-`n/a` row
missing a surface value appends a severity-2 `degradation` event
(`details.gate = feature_index_surface_lint`, `details.untagged = [...]`) and
the seal proceeds. A header without a `Surface` column is a Phase 75
disclosed-skip (`gate_skipped_prerequisite_absent`); a missing `FEATURE_INDEX.md`
is a silent skip. The motivating data is the sibling governance repository's (an external repository's issue); the gate
lives in qor-logic. V2 fail-closed promotion (remove the WARN escape) mirrors the Phase
114->122 `feature_index_verify` ladder and must wait until the consuming repo
reports full surface coverage. Per `qor/references/doctrine-feature-inventory.md`
"Surface column".

## Step 6.8 seal-hash helpers — CRLF-invariance (Phase 157 wiring; GAP-GOV-03 follow-on)

The Step 6.8 Preparation cites `hash_guard.hash_file`, `ledger_hash.content_hash`,
and `ledger_hash.chain_hash` as the helpers an operator uses to compute the
four real seal digests. Both file-digest helpers are CRLF-sensitive sources:
git autocrlf rewrites a committed TEXT artifact to CRLF, so a digest computed
at LF seal time over the working copy would disagree with a recompute over the
committed/checked-out file. `ledger_hash.content_hash` LF-normalizes
unconditionally (Phase 156, the GOV-01 binding). `hash_guard.hash_file` stays
byte-exact by default (it is also a general-purpose / binary hasher) and exposes
`normalize_newlines=True` for the text-seal path: pass it when the digest is
recorded against a text artifact that round-trips through git, and leave the
default for binary or intra-checkout evidence. `byte_count` always reports the
bytes actually hashed under either mode. `intent_lock._hash_file` is excluded:
it captures and re-checks the plan/audit gate artifacts within one working copy
(no git round-trip), so byte-exact comparison is correct there.

## Step 7.7.5 seal-artifact generation (Phase 164 wiring; relocated Phase 224)

**Why the pair sits at 7.7.5 (Phase 224; GH #334).** The ledger badge counts
ledger entries, so it can only be generated from truth once the entry this seal
adds is in `docs/META_LEDGER.md`. The pre-Phase-224 order regenerated at Step 6
and graded at Step 6.5, both before Step 7 appended that entry, so the gate
compared the artifact against the state that produced it: it read current, and
the badge shipped one behind on every seal. CI was the first observer, after the
branch was already pushed.

Step numbering is not execution order in this region. Steps 7.4 and 7.5 produce
content the seal entry carries -- the SSDF practice tags and the version the
entry title records -- so they run before the append despite their numbers. Step
7.7 is the first step that asserts the appended entry exists, which makes it the
earliest correct anchor.

**Nothing between 7.7.5 and the Step 9.5 staging mutates a counted input.**
Counted inputs are the `### Entry #` count, the skills / agents / doctrines
roots, the pytest collect, and for the header the max sealed phase. Step Z writes
a gate artifact; Step 7.8 reads; Step 7.9 writes under `qor/specs/` and amends
the existing seal entry rather than adding one; Step 8.5 writes under `qor/dist`.
None is a counted root.


Research entry #378 rec 2: the pre-164 seal ceremony hand-edited README count
badges and the SYSTEM_STATE header, and 13 always-on tests asserted that live
repo state matched truth -- a class that broke on nearly every seal (phases
121/122/123/140). Phase 164 inverts the contract: `qor.scripts.seal_artifacts
--write --phase <N> --snapshot <date>` deterministically regenerates the
mechanical fields (Snapshot date, Phase number, the five README literal-count
badges) from current truth via the `badge_currency` counters, with atomic
tmp+os.replace writes. Step 7.7.5 `--check` (release classes; hotfix exempt) and
the CI `seal-artifacts currency` step enforce currency where repo state is
stable. The generators are behaviorally tested against synthetic fixtures in
`tests/test_seal_artifacts.py`; the `**Phase**:` narrative and `**Chain
Status**:` prose remain authored content.

---

# Prose relocated from SKILL.md (Phase 178; GH #266)

## Step Prerequisites operator flow (moved from SKILL.md, Phase 178)

Operators run `qor-logic substantiate-capability` before invoking
`/qor-substantiate` to confirm which gates will run on their host. Output is a
paste-able markdown table for the seal entry body.

## Step 6.5 documentation-currency operator judgment (moved from SKILL.md, Phase 178)

Phase 31 semantics are WARN + continue. Operator judgment: continue on
spurious warnings; PAUSE + amend on legitimate ones (new doctrine without a
lifecycle.md update, feature shipped without release-doc authoring). The Phase 49/164 release-class badge check moved to Step 7.7.5 in Phase 224 and is locked by
`tests/test_substantiate_seal_artifacts_wiring.py` per
`qor/references/doctrine-governance-enforcement.md` "Badge currency".

## Step 6.8 digest-preparation discipline (moved from SKILL.md, Phase 178)

When preparing the four seal-critical digests, do not pattern-fill hex strings
or interpolate placeholders; the Step 6.8 validation block catches any digest
the canonical helpers did not actually produce.

## Step 7.7 post-seal verification detail (moved from SKILL.md, Phase 178)

Step 7.7 closes SG-AdjacentState-A: substantiate sealing without writing the
ledger entry, which the pre-seal Step 4.6 gates cannot catch. The Phase 76
previous_hash-uniqueness pass runs
`check_previous_hash_uniqueness(ledger_path, min_entry_num=207)`; a duplicate
`previous_hash` signals a concurrent federation race (reconcile per
`SG-ConcurrentLedgerRace-A`; pre-Phase-76 entries grandfathered).

## Step 4.7.5 fail-closed drift classes (moved from SKILL.md, Phase 178)

The Governance Index gate makes the Hierarchical Governance Index
self-policing (closing the deferred enforcement half of GH #140): advancing
`Last Reviewed` to the seal date clears `stale-tier1` by construction;
`unregistered` means a governance doc named in no tier; `tier3-unarchived`
means a Tier 3 row naming an already-SESSION-SEALed `phase <N>`. Per
`qor/references/doctrine-governance-index.md` "V2 (Phase 120; GH #149) --
shipped enforcement".

## Step 7.9: Spec fold (Phase 192; GH #277)

After the reliability gates and before the seal commit:

```python
from qor.scripts.spec_fold import fold_session_deltas
hashes = fold_session_deltas(Path("."), SESSION_ID)  # {} when no deltas declared
```

- A `SpecMergeError` (conflicting delta) or `FoldError` (fold would produce a
  grammar-violating spec) ABORTS the seal with the tree untouched; the
  operator re-plans the delta.
- On success, each capability's LF-normalized spec sha256 lands in the seal
  entry as `**Spec Corpus Hash**: <capability>=<hash>` and in
  substantiate.json's `spec_corpus_hash`; the consumed delta file is deleted
  (git history is the archive).
- The coverage pillar: `qor.scripts.spec_requirement_verify.verify_deltas`
  produces the qa_evidence coverage payload (structure + declared-surface
  existence; scenario semantics stay a Judge duty at audit).

## Step 2.5 version-applicability: why it rarely fires here

The check at seal is the SAME shared check the audit ran before issuing PASS
(`version_applicability.validate`). A release-class plan whose target version
could not exceed the current tag never reaches this step -- the audit would have
stopped it. Its presence at seal covers the narrow window where the tag advanced
between PASS and seal.

## Step 7.4 SSDF tagger: scope and grandfather boundary

Computes NIST SSDF practice tags for the SESSION SEAL entry body before Step 7
computes `content_hash`, so the tags are inside the hashed content rather than
appended after it.

Emission is forward-only: phase 52 and later entries carry tags; phase 51 and
earlier are grandfathered, because retrofitting tags into sealed entries would
change their content hashes and break the chain. Closes G-1 from
`docs/compliance-re-evaluation-2026-04-29.md`.

## Step 7.8 gate-chain completeness: form and ordering

Argv-form throughout, with no shell-variable interpolation (SG-Phase47-A).

It runs after Step 7.7 has confirmed ledger integrity, so that the check for
this phase's four gate artifacts happens against a ledger already known good --
a missing artifact is then unambiguously a missing artifact, not a symptom of
ledger corruption upstream.

## Step 9.6 acceptance-criteria close guard: what it inspects

The guard parses the AC checklist of each `Closes #N` target named in the
planned PR body and WARNs when an unmet criterion has no linked follow-on, or
when the `qa.json` verdict for the session is not PASS.

V1 is WARN-first and exits 0; `--enforce` is reserved for V2. Contract and the
QA evidence artifact:
`qor/references/doctrine-verification-closure-integrity.md`.

## Step 6.5 documentation currency: where the heuristic lives

The system-tier currency check is implemented by
`doc_integrity_strict.check_documentation_currency`, which returns a warning
list rather than raising -- currency is advisory at this tier, unlike the
badge-currency check in the same step, which ABORTs.

## Step 4.6.13 skill-corpus disclosure: why it discloses rather than aborts

A seal establishes what the plan promised and what the tests proved, but until
Phase 217 it recorded nothing about which skill corpus executed the ceremony.
Two seals with identical entries could come from materially different skills and
the ledger could not distinguish them, so install drift was invisible
retroactively as well as prospectively.

The step records a digest over the installed `SKILL.md` set, the scope it was
taken at, and the drift count against repo source.

It does not ABORT, and the reason is architectural rather than cautious. The
skill running the check is part of the corpus under test: a drifted
`qor-substantiate` could carry a weakened or absent check, so the drift most
worth catching is exactly the drift that removes the catcher. CI cannot cover
the gap either, having no operator install to compare against. A fail-closed
gate on that architecture would assert a guarantee the architecture does not
support -- the GH #314 shape repeated one phase after it was diagnosed.

Disclosure is therefore not a half-measure but the strongest honest claim the
structure permits. Enforcement is tracked at GH #320, with entry criteria
requiring observed drift counts from V1 first, following the
`merge_velocity_check` WARN-then-enforce path (Phase 93 -> 129).

Scope is `auto` rather than a fixed value because the original control was wired
at `--scope repo` while the operator installed globally, producing 30
guaranteed-irrelevant findings per run and hiding 27 real ones.

## Step 4.6.12 execution-continuity: separation of acceptances

Implementation verification, merge authorization, release authorization, and
deployment acceptance are four decisions, not one. A `verified` continuity
outcome speaks only to the first, and collapsing them is how a passing test
becomes a deployment warrant.

The pinned contract version is recorded at seal, and what is recorded is that
Qor-logic ASSERTS conformance rather than verifying it -- checking conformance
would require holding the upstream schema the ownership boundary forbids
copying. Stating that ceiling is the countermeasure to GH #314's shape, where a
declaration read as a guarantee.

Checkpoint and receipt artifacts are referenced by path and digest. Duplicating
their bodies into ledger prose would create a second copy that drifts from the
artifact it describes, and the ledger would then carry two answers to one
question.

## Step 4.6.14 publication boundary: why the seal runs it after staging

`/qor-audit` Step 0.6 runs the boundary lint WARN-only, over a tree that
predates implementation. CI runs it fail-closed but structural-only, because the
identity-terms overlay is gitignored by design -- a tracked denylist of private
identifiers in a public repository publishes the strings it exists to suppress.

Before Phase 219 nothing in between: no fail-closed, identity-aware run ever saw
implementation's new files before they were committed. Four leaks passed four
green runs that way, each time with the operator running the lint and it
reporting clean. It was clean, of the surface it could see.

The seal step closes that window. It runs AFTER staging so the phase's artifacts
are present, and it is fail-closed because a WARN here would reproduce the
audit-time invocation it exists to supplement.

The recorded `boundary_scope` distinguishes `structural` from
`structural+identity`. An unqualified "0 findings" from CI and from a local run
mean different things; a seal that does not say which one it got is not evidence
about identity terms.


---

## Per-step detail displaced by the Phase 222 table migration (GH #327)

Phase 222 collapsed the ten Step 4.6.x prose blocks into one machine-readable
table. The Notes column carries only what changes execution; everything the
prose blocks explained lives here. Nothing was deleted, only relocated -- a
property `tests/test_seal_ladder_tokens_survived.py` proves against the pinned
pre-rewrite revision rather than against a hand-written list.

**4.6 reliability sweep.** Three interdictions run sequentially; non-zero exit
aborts substantiation. `qor-logic reliability intent_lock verify` re-verifies the
lock captured at `/qor-implement` Step 5.5 and fails on plan, audit, or HEAD
drift. `qor-logic reliability skill_admission qor-substantiate` confirms the
current skill is registered with well-formed frontmatter.
`qor-logic reliability gate_skill_matrix` confirms every `/qor-*` handoff
reference resolves to a real skill. `qor-logic scripts session_id_lint || true`
is the Phase 106 WARN-only convention lint that catches fall-through to
`default`. Any ABORT leaves the session unsealed; the operator resolves the
drift -- re-audit, re-admit, or fix the broken handoff -- and re-runs.

**4.6.5 secret_scanner.** Pre-seal scan over staged content, ABORTing on any
detected secret. Closes OWASP LLM06 and NIST AI 600-1 section 2.10. The Cedar
`has_hardcoded_secrets` attribute and the gitleaks-v8 findings schema are
described above in this file.

**4.6.6 procedural_fidelity.** Static-analysis pass over the implement-gate
`files_touched` set. WARN-only: deviations append severity-2 events and do not
abort. Catches the doc-surface coverage gap. Four-class deviation catalog and
remediation: `qor/references/doctrine-procedural-fidelity.md`.

**4.6.7 dod_check.** WARN-only structural check that the plan's
`## Definition of Done` section is well-formed. V1 enforces presence only.
`PLAN_PATH` is argv-only per SG-Phase47-A. Tier contract and finding classes are
described above (`SG-DoDImplicit-A`).

**4.6.8 merge_velocity_check.** Fail-closed throttle on stabilization-capacity
strain from `origin/main`'s recent merge history. Exits 0 on `healthy` and
`strained`, 1 on `exceeded`; Phase 129 removed the `|| true`. To seal during a
deliberate high-velocity window, re-run with `--override`, which logs a
`gate_override` shadow event carrying
`details.gate = merge_velocity_check`. `--shared-core-path` patterns add
shared-surface signals. Originating recurrence and `SG-MergePaceThrottle-A` are
described above.

**4.6.9 skill_size_budget_lint.** Per-skill size-budget lint over
`qor/skills/**/SKILL.md`, WARN at 25 KB and EXCEEDED at 40 KB. Since V2 (Phase
234; GH #320) an EXCEEDED finding -- the CLI's sole exit-1 condition -- aborts
the seal; WARN-band findings remain advisory. Corpus-growth history and
`SG-SkillCorpusGrowth-A` are described above. This is one of the two controls
that made composition unworkable as a size remedy: it measures the file that
ships, so a composed artifact would measure the same.

**4.6.10 data_api_acl_lint.** Fail-closed on blocking findings `missing-grant`
and `definer-view`; `security-definer-fn` is advisory. Escapes are
`-- qor:service-role-only` and `-- qor:definer-view-intended reason: ...`.
No-SQL-migration repos print `SKIP:` and exit 0, a disclosed-skip that records
SKIP and emits `gate_skipped_prerequisite_absent`. Full contract:
`qor/references/doctrine-runtime-principal-fidelity.md`.

**4.6.12 execution-continuity receipt gate.** Applies when the plan declares
`execution_continuity`. Requires a verification receipt bound to the EXACT
implementation revision; a stale-revision receipt ABORTs. Provider prose and
status badges are not receipts. `verified`, `rejected`, and `inconclusive` stay
distinct outcomes, and `inconclusive` is not `skip`. Reference artifacts by path
and digest, and record the pinned contract version. Separation of acceptances,
and why conformance is asserted rather than verified, are described above.

**4.6.13 install_drift_check.** Records `skill_corpus` -- digest, scope, drift
count -- in the gate artifact and the seal entry. Disclosure, not ABORT: the
skill running the check is part of the corpus under test, so an ABORT wired
inside it would be unreliable by construction. Enforcement is tracked at GH #320.
This is the second control that made composition unworkable: it compares
`qor/skills/**/SKILL.md` byte-for-byte against the operator's installed copy, so
whatever a build step emits must land there as a single file.

**4.6.14 publication_boundary_lint.** Runs AFTER Step 9.5 staging so this phase's
new files are visible; the audit-time run predates them. Untracked files are
scanned. Records `boundary_scope` as `structural` or `structural+identity`,
because CI cannot load the identity overlay and an unqualified zero means less
there.

**4.6.11 is absent by decision.** Phase 221 (ledger #563) found that GH #314 had
been filed against text that existed only in an operator's installed copy. The
gap in the numbering is the record of that, and closing it would erase the
evidence that a gate was once declared and never existed.
