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
CLI exits 1 when any EXCEEDED finding (>= 40 KB) is present so V2 can convert to a
hard ABORT by removing the `|| true` wrap. Operator-actionable: skills exceeding
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

## Step 6 seal-artifact generation (Phase 164 wiring; generate, don't assert)

Research entry #378 rec 2: the pre-164 seal ceremony hand-edited README count
badges and the SYSTEM_STATE header, and 13 always-on tests asserted that live
repo state matched truth -- a class that broke on nearly every seal (phases
121/122/123/140). Phase 164 inverts the contract: `qor.scripts.seal_artifacts
--write --phase <N> --snapshot <date>` deterministically regenerates the
mechanical fields (Snapshot date, Phase number, the five README literal-count
badges) from current truth via the `badge_currency` counters, with atomic
tmp+os.replace writes. Step 6.5 `--check` (release classes; hotfix exempt) and
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
lifecycle.md update, feature shipped without release-doc authoring). The Phase
49/164 release-class badge check is locked by
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
