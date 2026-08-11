# Qor-logic Lifecycle

The governance lifecycle is a phased sequence of skills, each gated by the prior phase's artifact. This document captures the canonical sequence, per-phase contracts, and the session model.

## Phase sequence

```
research -> plan -> audit -> implement -> substantiate -> validate -> remediate
```

Defined in [qor/gates/chain.md](../qor/gates/chain.md). Each phase has:

- A **skill** that executes it (`/qor-<phase>` or a bundle).
- A **persona** that embodies the skill's role (Governor, Judge, Specialist, Fixer, Orchestrator).
- A **gate artifact** written to `.qor/gates/<session_id>/<phase>-iter<N>.json` (immutable, one per emission; Phase 173) with a byte-identical latest copy at `.qor/gates/<session_id>/<phase>.json`, validated against `qor/gates/schema/<phase>.schema.json`.
- A **prior-phase check** at Step 0 that reads the prior phase's artifact and aborts on absence (operator may override but override is logged as a severity-1 `gate_override` shadow event).

## Per-phase contracts

| Phase | Skill | Persona | Gate reads | Gate writes | Output artifact |
|---|---|---|---|---|---|
| research | `/qor-research` | Governor | (none) | research | optional `RESEARCH_BRIEF.md` |
| plan | `/qor-plan` | Governor | research | plan | `docs/plan-qor-phase<NN>-<slug>.md` + gate artifact |
| audit | `/qor-audit` | Judge | plan | audit | `.agent/staging/AUDIT_REPORT.md` + gate artifact + META_LEDGER entry |
| implement | `/qor-implement` | Specialist | audit | implement | source/test edits + META_LEDGER entry |
| substantiate | `/qor-substantiate` | Judge | implement | substantiate | Merkle seal + version bump + tag + CHANGELOG stamp + META_LEDGER entry |
| validate | `/qor-validate` | Judge | substantiate | validate | validation report |
| remediate | `/qor-remediate` | Governor | (cross-cutting) | remediate | process-change proposal |

See [delegation-table](../qor/gates/delegation-table.md) for the full handoff matrix and [qor/skills/](../qor/skills/) for skill directory layout.

## Substantiate steps (Phase 31 expansion)

The seal sequence under `/qor-substantiate` is:

| Step | Purpose |
|---|---|
| 0 | Gate check -- implement.json present and valid |
| 0.2 | (`/qor-plan` only, Phase 32 wiring) Install drift check: `install_drift_check.py` WARNs if local SKILL.md install lags repo source |
| 1 | Identity activation (Judge mode) |
| 2-2.5 | State verification + version validation (target > current tag) |
| 3 | Reality audit (Reality = Promise on file tree) |
| 3.5 | Backlog blocker scan |
| 4 | Functional verification (tests) |
| 4.5 | Skill file integrity (structural lint on modified SKILL.md files) |
| 4.6 | Reliability sweep via `python -m qor.reliability.{intent_lock,skill_admission,gate_skill_matrix}` (Phase 35 wiring: was path-invocation of hyphen-named files, CWD-dependent) |
| 4.7 | Documentation integrity check (topology + glossary hygiene + orphan scan; Phase 28 wiring + **Phase 32 strict-mode**: Check Surface D/E now raise at seal time; `legacy` tier bypasses) |
| 5 | Section 4 Razor final check |
| 6 | Sync `docs/SYSTEM_STATE.md` |
| **6.5** | **Documentation Currency Check (Phase 31 + Phase 33 wiring): WARNs when doc-affecting files touched without a corresponding system-tier doc update. Phase 33 addition: when `plan_payload.change_class ∈ {feature, breaking}`, README.md and CHANGELOG.md are also required in `files_touched` (release-doc coverage). Hotfix exempt.** |
| 7 | Compute Merkle seal |
| 7.5 | `bump_version(change_class)` — writes `pyproject.toml` only. Tag creation moved to Step 9.5.5 (Phase 33 wiring; prevents pre-seal-HEAD tagging) |
| 7.6 | Stamp `CHANGELOG.md` |
| **7.7** | **Post-seal verification (Phase 47 wiring): `python -m qor.reliability.seal_entry_check --ledger docs/META_LEDGER.md --plan "$PLAN_PATH"`. Verifies the latest META_LEDGER entry is a SESSION SEAL for the current phase with internally-consistent chain hash. Closes SG-AdjacentState-A's bookkeeping-gap subclass (Phase 46's first substantiate sealed without writing ledger entries). ABORT on non-zero exit.** |
| 8 | Cleanup `<legacy-staging>/` staging |
| 8.5 | Dist recompile (`python -m qor.scripts.dist_compile`; Phase 30 wiring) |
| 9 | Final report |
| 9.5 | Auto-stage for commit |
| **9.5.5** | **Annotated seal-tag creation (Phase 33 wiring): capture post-commit SHA via `git rev-parse HEAD`, pass as required `commit` arg to `create_seal_tag`. Ensures tag targets the sealed content, not the pre-seal HEAD.** |
| 9.6 | Operator push/merge decision (4-option menu) |
| Z | Write `substantiate.json`; call `session.rotate()` so next phase starts clean |

## Session model

A **session** is the unit of a single phase invocation. Format: `<YYYY-MM-DDTHHMM>-<6hex>` (e.g., `2026-04-18T1200-a3f9c2`), stored in `.qor/session/current`.

- Session IDs are created or refreshed by `qor/scripts/session.py::get_or_create()`.
- After 24h of inactivity, the marker is considered stale and a new ID is issued on next read.
- Every gate artifact carries the session_id. Gate-chain checks use it to locate the prior phase's artifact.
- **Session rotation** (Phase 30 wiring): `/qor-substantiate` Step Z calls `session.rotate()` after writing the substantiate artifact, so the next `/qor-plan` starts with a clean `.qor/gates/<new_sid>/` directory. Prior session directories are preserved for archaeology (not pruned). See [governance-enforcement §7](../qor/references/doctrine-governance-enforcement.md).

## Branch model

Per [governance-enforcement §2](../qor/references/doctrine-governance-enforcement.md):

- One branch per phase: `phase/<NN>-<slug>`, cut from `main`.
- `/qor-plan` Step 0.5 enforces a clean working tree before checkout; operator picks stash / commit / abandon.
- `/qor-substantiate` Step 9.6 offers four push/merge options after seal: push-only, push+PR, merge-local (dry-run first), hold-local.

## Version model

Per [governance-enforcement §3](../qor/references/doctrine-governance-enforcement.md):

- Plan header declares `**change_class**: hotfix | feature | breaking`.
- `/qor-substantiate` Step 7.5 calls `governance_helpers.bump_version(change_class)` -> updates `pyproject.toml`.
  - `hotfix` -> patch (0.2.0 -> 0.2.1)
  - `feature` -> minor (0.2.0 -> 0.3.0)
  - `breaking` -> major (0.2.0 -> 1.0.0)
- `governance_helpers.create_seal_tag` writes an annotated git tag with the Merkle seal, ledger entry, phase number, and change class. **Order matters**: bump before tag, per Phase 30 constraint (SG-Phase30 wiring). Inverted order interdicts on "tag already exists" and forces manual pyproject editing.
- `/qor-substantiate` Step 7.6 stamps `CHANGELOG.md` via `changelog_stamp.apply_stamp`: renames `## [Unreleased]` to `## [X.Y.Z] - YYYY-MM-DD` and inserts a fresh Unreleased header above.

## Gate artifact chain

Each phase's artifact is validated (`jsonschema` draft-2020-12) before write. Downstream phases read via `gate_chain.check_prior_artifact` which returns `GateResult(found, valid, path, errors)`.

The chain itself is the SHA256-linked META_LEDGER (see [architecture.md](architecture.md) and [operations.md](operations.md)). Gate artifacts are ephemeral per-session; META_LEDGER entries are immutable history.

## Ledger chain

Every AUDIT / IMPLEMENTATION / SEAL lands as a numbered entry in [docs/META_LEDGER.md](META_LEDGER.md). Each entry carries:

- **Content Hash**: SHA256 of the content being entered (plan + audit report for audit entries; source files for implement entries; etc.).
- **Previous Hash**: the prior entry's Chain Hash.
- **Chain Hash**: `SHA256(content_hash + "|" + previous_hash)` (Phase 23 format; legacy entries use `SHA256(content_hash + previous_hash)` without separator).

`qor/scripts/ledger_hash.py verify` walks the ledger and confirms chain integrity; `tests/test_ledger_hash.py` runs this on every suite execution.

## Shadow genome

Two parallel records of governance-relevant observations:

- **`docs/SHADOW_GENOME.md`**: narrative entries for rejected artifacts and failure patterns (SG-016 through SG-Phase30-B today). Prose format; not parsed structurally.
- **`docs/PROCESS_SHADOW_GENOME.md`** + UPSTREAM sibling: structured JSONL events (`gate_override`, `capability_shortfall`, `degradation`, `repeated_veto_pattern`, etc.), validated against `qor/gates/schema/shadow_event.schema.json`. Parsed by `/qor-remediate`.

See [shadow-genome-countermeasures](../qor/references/doctrine-shadow-genome-countermeasures.md) for the full pattern catalog and [shadow-attribution](../qor/references/doctrine-shadow-attribution.md) for attribution rules.

## Delegation rules

Skills never invent handoffs. Every cross-skill directive names its target per [delegation-table](../qor/gates/delegation-table.md). When `/qor-audit` VETO grounds trigger remediation, the audit report's `**Required next action:**` line names the exact skill per [audit-report-language](../qor/references/doctrine-audit-report-language.md):

- Section 4 Razor violation -> `/qor-refactor`
- Orphan / Macro-arch breach -> `/qor-organize`
- Plan-text ground -> Governor amends plan, re-runs `/qor-audit`
- Process-level pattern -> `/qor-remediate`
- Code-logic defect -> `/qor-debug`

## Related docs

- [architecture.md](architecture.md) -- system layers
- [operations.md](operations.md) -- operator runbook
- [policies.md](policies.md) -- policy layer
- [../qor/gates/chain.md](../qor/gates/chain.md) -- canonical phase definitions
- [../qor/gates/delegation-table.md](../qor/gates/delegation-table.md) -- handoff matrix

## Execution continuity (Phase 216; GH #285)

Qor-logic classifies and routes execution-continuity evidence; it does not
define the checkpoint, reconstruction, or receipt schemas, which belong to the
upstream contract and are referenced by version.

| Module | Responsibility |
|---|---|
| `qor/scripts/continuity_contract.py` | Qor-owned key set, outcome vocabulary, config-backed contract pin |
| `qor/scripts/continuity_gate.py` | `classify(Evidence) -> Decision`; pure, no I/O, exact-revision comparison |
| `qor/scripts/plan_continuity_lint.py` | Plan-declaration lint, one finding code per defect class |

Data flow: a plan declares `execution_continuity` (validated by
`plan_continuity_lint`); `/qor-audit` runs the Execution-Continuity Pass;
`/qor-substantiate` requires an exact-revision receipt; `/qor-validate` and
`/qor-remediate` route on `continuity_outcome`.

Rule order is the specification and fail-closed conditions precede acceptance,
so a valid checkpoint never outranks a live-writer conflict or an authority
request. Revision comparison is string equality, never git ancestry --
`intent_lock` keeps its Phase 43 ancestry tolerance and the two are not folded
together. Contract: `qor/references/doctrine-execution-continuity.md`.

## Installed skill-corpus drift (Phase 217; GH #314)

`qor-logic install` writes a copy of each `SKILL.md` into the host's skills
directory; that copy, not the repo source, is what actually executes.

| Module | Responsibility |
|---|---|
| `qor/scripts/install_drift_check.py` | `installed_scopes()` discovery; `check(scope="auto")` compares source against every scope that has an install |
| `qor/scripts/skill_corpus.py` | `digest(host, scope)` over the sorted `(skill name, sha256)` pairs of the installed set |

An absent scope reports once as not-installed rather than once per source skill.
Reporting per-skill produced 30 guaranteed-irrelevant findings on every run,
which collapsed under `|| echo` into one warning and hid 27 real mismatches.

`/qor-substantiate` Step 4.6.13 records the digest, scope, and drift count in
the seal entry. Disclosure, not ABORT: the skill running the check is part of
the corpus under test, so the drift most worth catching is the drift that
removes the catcher. Enforcement is tracked at GH #320.

Note that `qor-logic install` ships from `qor/dist/variants/` while the drift
check compares against `qor/skills/` source, so a stale `dist` makes the two
disagree. Run `dist_compile` before `install`.
