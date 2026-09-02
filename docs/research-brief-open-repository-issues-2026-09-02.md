# Research Brief

**Date**: 2026-09-02
**Analyst**: The Qor-logic Analyst
**Target**: The 9 open issues on the Qor-logic repository (#394, #404-#411)
**Scope**: Verify every cited file:line claim against current `main`; separate live defects from claims already remediated since the reporting version; establish ownership boundaries and the cross-cutting theme for planning

---

## Executive Summary

Nine issues are open. One (#394) is already fixed on an open PR awaiting the governed seal ceremony. Of the eight remaining, every one is a real defect, but four carry sub-claims that are **stale** -- fixed by GH #282 and GH #365 after the reporting version -- so a plan written from the issue text alone would rebuild work that already shipped.

The dominant finding is that five of the eight are one defect family, not five: **Qor-logic's own repository layout and release history are compiled into gate constants**, so gates resolve truth from paths and numbers that exist only in this repository. #406 names this explicitly; #404's `MARKUP_COMPAT_BOUNDARY`, #405's seed template, and #407's plan-name allowlist are the same defect reached through different gates. One consumer-portability phase addresses all of them; eight point fixes would not.

---

## Findings

### #394 -- superseded, not open work

PR #403 (`phase/248-plan-terms-key-canonicalization`, MERGEABLE) closes it: schema-level `not: {required: [terms_introduced]}`, skill/doctrine rename, variant recompile, red-proved negative probe. Ten of twelve CI checks pass; `lint` and `gate-chain-completeness` are RED, and the PR body discloses why -- the branch carries a plan file but no ledger entry or Merkle seal citation.

Residual in-repo: `qor/skills/sdlc/qor-plan/SKILL.md:172` still reads `terms_introduced` in the Step 1b prose on `main`. The PR fixes it; this is only a note that `main` is not yet clean.

**Disposition**: not a research target. It needs the ceremony run against the existing diff, or an explicit promotion decision. No new investigation.

### #404 -- ledger markup: one live half, two stale halves, one amplifier the report missed

**LIVE.** `qor/skills/meta/qor-bootstrap/references/qor-bootstrap-templates.md:127-131` writes `**Previous Hash**: GENESIS (no predecessor)` and, for subsequent entries, a bare inline hex. `qor/scripts/ledger_dialect.py:35-40` recognizes exactly three value forms -- inline backtick, `= <hex>`, and a bare hex **alone on its own line**. An inline unbackticked hex on the `**Previous Hash**:` line matches none of them, so `PREV_HASH_RE` misses and the entry resolves as non-verifiable. The reporter's observed `content True / prev False / chain True` is reproduced by the current dialect.

**STALE.** Two of the three root causes are already closed:

- "`seal_entry_check._HASH_FIELD_RE` is stricter than `ledger_hash._HASH_VALUE`" -- both now import from `qor/scripts/ledger_dialect.py` (`seal_entry_check.py:27-28`, `ledger_hash.py:158-160`). One contract governs. Suggested fix 2 is done.
- "`_ENTRY_HEADER_RE` requires a literal `Phase <N>`" -- `qor/reliability/seal_entry_check.py:31-40` no longer does; the comment cites GH #282 and the phase is read from the header *or* a `**Phase**:` line.

**Amplifier not in the report.** `ledger_dialect.py:26` sets `MARKUP_COMPAT_BOUNDARY = 123`, and `ledger_hash.verify` (`ledger_hash.py:527-556`) fails an unparseable entry only when `num >= markup_required_cutoff`; below it the entry is counted in `skipped` and nothing else. 123 is a Qor-logic-absolute entry number. **A fresh consumer ledger has no entry at or above it**, so every unparseable entry in a new workspace degrades to a silent skip and exit 0 -- which is precisely the reported "7 of 8 skipped, exit 0". The markup gap is the cause; the absolute cutoff is why it presents as clean rather than as FAIL. This belongs in the same portability family as #406.

### #405 -- alias already shipped; column vocabulary still diverges

**STALE.** Suggested fix 3 is done. `qor/scripts/feature_index_verify.py:73-77` falls back to `row.get("status", "")` when `verification status` is absent, with the GH #365 citation in the docstring. Bootstrap-seeded rows are no longer dropped for the status column.

**LIVE, and materially narrower than reported.** The two vocabularies still diverge:

- bootstrap seed (`qor-bootstrap-templates.md:184`): `| ID | Feature | Doc | Code | Test | Status | Notes |`
- canonical (`qor/templates/FEATURE_INDEX.example.md:6`): `| ID | Name | Source-of-truth file:line | Doc citation | Test path | Surface | Verification status |`

Consequence today is column misalignment, not row loss: rows parse, but `name`, `source-of-truth`, `doc citation`, `test path`, and `surface` all resolve to absent keys, so `surface_lint` sees no `Surface` column and the doc/test citations the doctrine depends on are never read. The coverage tally is right and everything it is supposed to substantiate is empty.

**LIVE.** Suggested fix 2 is untouched: a table whose header declares no recognized status column still returns `[]` from `parse_index_rows`, so "no rows" and "rows I could not read" remain the same result.

### #406 -- confirmed live, and the mechanism it asks for is already built

Every cited constant is present on `main`:

- `qor/scripts/doc_integrity.py:26,30,176,212` -- `qor/references/glossary.md` hardcoded in four places, two of them as literal `Path` joins.
- `qor/scripts/doc_integrity_strict.py:77,199` -- same literal as the non-absolute fallback.
- `qor/scripts/skill_size_budget_lint.py:3` -- walks `qor/skills/**/SKILL.md`.

The reporter's central point holds and is stronger than stated. `qor/scripts/qorlogic_config.py` is a general tolerant reader (`load_section(repo_root, name)`) explicitly built as "the one tolerant reader" for exactly this, already consumed by `badge_layout` and `attribution_policy`. The workspace's own `.qorlogic/config.json` carries only an `attribution` section. Extending it to `layout` requires no new mechanism.

The typed-skip half of the proposal is new governance surface: today `feature_index_verify.py:207-209` and `governance_index.py:219` emit `gate_skipped_prerequisite_absent` with free-text reasons, so skips are ungroupable in the shadow genome. The proposed contract -- declared-absent key yields a typed skip, no config entry at all is a hard failure -- is a doctrine change, not a refactor, and needs its own audit.

### #407 -- resolver already generalized; the residual is registration, not the regex

**STALE as written.** The literal `_PLAN_PATH_RE` the issue quotes no longer governs. `qor/scripts/prompt_injection_canaries.py:10-14` delegates to `qor/scripts/governance_paths.resolve_governance_plan_path`, which admits any index-registered plan alongside the historical families.

**LIVE, relocated.** `governance_paths.py:26-32` keeps `_ALWAYS_ALLOWED_RE` anchored on `docs/plan-qor-phase\d+...`, and registration is the only other route. But `/qor-bootstrap` seeds no `docs/GOVERNANCE_INDEX.md` and `/qor-plan` writes no registration row for the plan it authors -- neither skill mentions `GOVERNANCE_INDEX` at all. So a freshly bootstrapped workspace has no registration path, and a plan named for its work is still rejected. The defect is real; the fix is seeding and registration wiring, not widening a pattern.

### #408 -- confirmed live; precedent exists, codification does not

The `AMENDMENT` entry type is in active use -- `docs/META_LEDGER.md` entries #645 and #669 -- but `grep AMENDMENT qor/references/*.md` returns nothing. The convention this repository already practices is written down nowhere, so a consumer has no way to know it exists.

The enforcement half is entirely unbuilt. `/qor-substantiate` Step 3 (`qor/skills/governance/qor-substantiate/SKILL.md:158-172`) compares planned files against the blueprint tree for MISSING/UNPLANNED/EXISTS; it does not recompute content hashes. `gate_provenance.verify_committed` recomputes gate-artifact digests, which is a different surface -- no gate recomputes the content hashes that earlier *ledger entries* committed for artifacts touched during the session. The reporter's assessment is right: half 2 is what closes it, and half 1 alone is a bookkeeping step that gets skipped under audit pressure.

### #409 -- split ownership; the actionable half is here

`qor/skills/sdlc/qor-plan/references/step-extensions.md:14-21` raises `InterdictionError` on any non-empty `git status --porcelain` and then unconditionally `git checkout -b phase/<NN>-<slug>`. There is no "already isolated" escape. That half is Qor-logic-owned and the proposed fix -- accept HEAD-is-not-default as satisfying the step -- lands cleanly here.

`/qor-enterprise-auto-dev` is **not in this repository**. `qor/skills/` holds `governance`, `memory`, `meta`, `sdlc`; no `qor-enterprise-*` skill exists. The Delegation-Boundary half of the fix belongs to the private line.

### #410 -- split; the mechanism changes are all local

Local and actionable: `qor/scripts/check_shadow_threshold.py:86` sums severity over `not e["addressed"]`, and `mark_addressed_pending` sets only `addressed_pending`, so a pending remediation never lowers the sum. `/qor-audit` Step 4.2 flips the whole `addressed_event_ids` list under one `closure_enforcer`. Both the `deferred-upstream` closure state (the event schema already carries `issue_url`) and per-change flips are changes to files in this repository.

Inherent: the cross-workspace framing itself. A remediation owned by another repository is exactly what this repository's own boundary rules produce, so the vocabulary gap is structural, not incidental. Suggested fix 3 is the one that must be decided rather than built -- either the threshold excludes `addressed_pending`, or the routing rule gains an escape; leaving both as-is is what deadlocks.

### #411 -- split; the vocabulary belongs here, the emitter does not

`/qor-enterprise-environment-adapter` is not in this repository (see #409). But the status vocabulary it would use is local: `qor/scripts/qor_platform.py:190-204` `is_available` returns a bare `bool` with no third state, and `qor/platform/profiles/claude-code-solo.md:22` mandates the severity-2 `capability_shortfall` whenever `enhances_with` lists an unavailable capability. `qor/platform/detect.md:92` and `qor/platform/capabilities.md:35` both record that per-skill wiring was deliberately deferred -- so the reported event is an adapter honoring a Qor-logic-side contract that cannot express "covered by a supported substitute".

Adding `satisfied-by-fallback` to `qor/platform/` is the load-bearing change and it is local. The adapter change that consumes it is not.

---

## Blueprint Alignment

| Blueprint claim | Actual finding | Status |
|---|---|---|
| Phase 241 defined a portable governance engine boundary (PR #383, merged) | Four gate families still resolve truth from Qor-logic-absolute constants: `glossary.md` path (`doc_integrity.py:26,30,176,212`), skills root (`skill_size_budget_lint.py:3`), ledger entry number 123 (`ledger_dialect.py:26`), plan-name family (`governance_paths.py:26-32`) | **DRIFT** |
| `qorlogic_config.load_section` is "the one tolerant reader" for operator layout declarations | True, and correctly used by `badge_layout` + `attribution_policy`; the three layout-bound gates bypass it entirely | **DRIFT** |
| GH #282 unified ledger-dialect handling across `ledger_hash`, `seal_entry_check`, `governance_health` | Confirmed -- shared `ledger_dialect` module, one contract. #404's "two verifiers disagree" claim is stale | **MATCH** |
| GH #365 closed the FEATURE_INDEX zero-row silent pass | Confirmed for the status column via the `status` alias; the remaining six columns still diverge from the seed template | **PARTIAL** |
| `/qor-bootstrap` seeds a governed workspace ready for the gate chain | The seed emits ledger markup the dialect rejects, a FEATURE_INDEX header the canonical parser misreads, and no `GOVERNANCE_INDEX.md` at all | **DRIFT** |
| The `AMENDMENT` ledger entry type is a governed convention | Practiced (entries #645, #669) but absent from every doctrine under `qor/references/` | **DRIFT** |

---

## Recommendations

1. **P0 -- Close #394 through the ceremony, not through new work.** PR #403's diff is complete and green on all substantive checks. Run `/qor-audit` -> `/qor-implement` -> `/qor-substantiate` against the existing branch to produce the ledger entry and seal citation the `lint` gate wants. Do not re-plan it.

2. **P1 -- One consumer-portability phase covering #406, #404, #405, #407.** These are one defect: Qor-logic constants where consumer configuration belongs. Scope it as: extend `.qorlogic/config.json` with a `layout` section read through `qorlogic_config.load_section` (glossary path, skills root, seal-artifact roots); make `MARKUP_COMPAT_BOUNDARY` a resolved value rather than an absolute; correct both bootstrap templates to the canonical vocabularies; seed `GOVERNANCE_INDEX.md` at bootstrap and register the plan at `/qor-plan`. Splitting these across four phases would produce four partial fixes of the same defect.

3. **P1 -- Separate the typed-skip contract (#406 half two) into its own governed phase.** "Declared-absent yields a typed skip; no config entry is a hard failure" changes the seal ladder's failure semantics. It is doctrine work with an audit of its own, and bundling it into the portability refactor would put a behavior change behind a path change.

4. **P2 -- #408 amendment enforcement.** Codify the `AMENDMENT` entry in a doctrine under `qor/references/` (the practice is already two entries deep), then extend `/qor-substantiate` Step 3 to recompute ledger-committed content hashes for session-touched artifacts and fail the seal on undisclosed mismatch. The doctrine alone is not a closure -- ship both halves or neither.

5. **P2 -- #409 and #411 local halves, filed as such.** `/qor-plan` Step 0.5 gains an already-isolated precondition; `qor/platform/` gains `satisfied-by-fallback`. Both are small and both unblock their counterparts elsewhere. The enterprise-skill halves are out of this repository's execution authority and should be raised with the operator for routing, not planned here.

6. **P3 -- #410 requires a decision before it can be planned.** The `deferred-upstream` closure state and per-change flips are buildable now, but suggested fix 3 (whether `addressed_pending` counts toward the threshold) is an authority call about whether remediation may self-clear. That question should reach the operator before a plan is written against it.

7. **Correct the issues with what was verified.** #404, #405, and #407 each contain a root-cause claim that no longer holds. Leaving them uncorrected means the next reader re-derives it -- and #405's real severity (column misalignment) is quieter and easier to miss than the reported one (total row loss).

---

## Updated Knowledge

Two entries for the process record:

- **Consumer-reported defects age against a moving repository.** Three of eight issues filed from one consumer cycle contained root causes already closed by GH #282 and GH #365. The reporting version, not the filing date, determines what is stale -- and the issue text does not carry that version forward into anyone's planning. Verification against current `main` must precede planning for any externally-reported defect, and this brief is the instance that proves it.
- **A layout constant and a history constant are the same defect.** `MARKUP_COMPAT_BOUNDARY = 123` reads as a compatibility affordance and behaves as a portability defect: it silently converts a hard failure into a clean exit for every workspace younger than this one. Absolute references to this repository's own release history belong on the same remediation list as absolute references to its directory tree.

---

---

## Addendum (same session): the toolkit-boundary question

Raised by the operator after the findings above: a consumer workspace's agent had to hand-write a boundary statement into its own governance docs -- that Qor-logic is a development-time governance toolkit, not a runtime/build/test dependency; that it ships no code into the consumer's package; that nothing in the consumer's source tree imports it; and that `qor/...` paths appearing in governance prose refer to the toolkit's repository rather than the consumer's tree. The question is whether Qor-logic can assert and enforce that boundary itself.

### Correction to the #407 finding above

`qor/seed.py:25-39` `SEED_TARGETS` **does** seed `docs/GOVERNANCE_INDEX.md`, and `scaffold_file_targets()` pins it as scaffold-owned for governance-health. The finding above stated it was not seeded; that was checked against the `/qor-bootstrap` skill text (which indeed never mentions the index) and not against the `seed()` primitive the CLI invokes. The residual for #407 is narrower than written: the index exists in a seeded workspace, but `/qor-plan` writes no registration row for the plan it authors, so a plan named for its work is still unregistered and still unresolvable by `governance_paths.resolve_governance_plan_path`. The load-bearing half of the fix is registration wiring, not seeding.

### The boundary is already being violated mechanically

`qor/scripts/host_capability.py:78-83` reads the consuming repository's `pyproject.toml` and extracts a version with `_PYPROJECT_VERSION` (`host_capability.py:21`), which matches the **first** `version = "X.Y.Z"` line in the file. In any consumer repository that is the consumer's own product version. `check_qor_logic_freshness` then compares it against `latest_known` -- a Qor-logic version -- and reports drift, and per `qor/references/doctrine-host-repo-posture.md` the caller emits `qor_logic_stale_install` (severity 1, advisory).

Two consequences. The check is correct only in Qor-logic's own repository, where the first `version =` line happens to be Qor-logic's; everywhere else it compares two unrelated version lines and drifts permanently. And it is a severity-1 event that fires every session on that comparison, so it joins #411 as a standing contributor to the shadow threshold that carries no information.

This is the same layout-bound-gate family as #406 and the `MARKUP_COMPAT_BOUNDARY` finding, in its sharpest form: the toolkit reads the consumer's product identity as if it were its own. The operator's question is not hypothetical -- the boundary the consumer's agent asserted in prose is one the toolkit currently crosses in code.

### Why the hand-written statement was necessary, and why it is not sufficient

The four claims split cleanly. Three are mechanically provable against the consuming repository:

| Claim | Provable by |
|---|---|
| Not a runtime/build/test dependency | `qor-logic` absent from runtime/build/test dependency manifests |
| Ships no code into the package | no toolkit path inside the consumer's packaged/distributed paths |
| Not imported by the consumer's source | no `import qor` / `from qor` under the consumer's source roots |

The fourth -- that `qor/...` in governance prose means the toolkit's tree -- is not a claim to prove but an ambiguity to remove, and it is the same ambiguity that produces #406, #404, #405 and #407. Once glossary path, skills root and seal-artifact roots resolve through the `.qorlogic/config.json` `layout` section (Recommendation 2), a `qor/...` literal in prose is either config-resolved (the consumer's own) or explicitly toolkit-relative. The disambiguation is a byproduct of the portability phase, not separate work.

The three provable claims are where the toolkit currently offers nothing. A consumer can only write them down. This repository's own `doctrine-verification-closure-integrity.md` and `_validate_closure_enforcer` exist precisely to reject closure on prose -- and a seeded paragraph is prose. The consumer's agent produced exactly the artifact this project's doctrine calls insufficient, because the toolkit gave them no other way to say it.

### Shape of the fix: the inbound twin of the publication boundary

`doctrine-publication-boundary.md` governs the outbound direction -- what Qor-logic must not say about repositories outside itself. What is missing is the inbound direction: what Qor-logic must not become inside a repository that installs it. Same shape, opposite sense, and `qor/scripts/publication_boundary_lint.py` is the pattern to mirror -- structural tracked patterns, a per-line allow marker with a required reason, exit 1 on findings, no denylist that would itself breach the boundary.

Two halves, and the second is what closes it:

1. **Declaration.** Seed the boundary statement so no consumer has to author it. `docs/GOVERNANCE_INDEX.md` is already seeded (`seed.py:25-39`), already scaffold-owned, and already describes itself as the authoritative map of governance artifacts in the project -- the natural home for a statement of what Qor-logic is and is not within that project.
2. **Enforcer.** A `toolkit_boundary_lint` run as a `/qor-substantiate` gate that proves the three provable claims against the consuming repository, rather than trusting the seeded text. Fail-closed on a violation; typed skip where a manifest kind is absent, per the typed-skip contract in Recommendation 3.

The freshness-check defect above must be fixed in the same phase. Shipping a gate that asserts the toolkit is not a dependency while `host_capability` reads the consumer's product version as the toolkit's own would be a control contradicting its own codebase.

### Recommendation

Add as **Recommendation 8 (P1)**: one governed phase for the inbound toolkit boundary -- doctrine, seeded declaration, `toolkit_boundary_lint` enforcer, and the `host_capability` freshness-check correction. It is a sibling of the consumer-portability phase (Recommendation 2) and should follow it, since the path-disambiguation half depends on the `layout` config section landing first. It should not be folded into it: portability is a path refactor, this is a new control with new failure semantics, and the audit surfaces differ.


_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
