# Research Brief

**Date**: 2026-09-04
**Analyst**: The Qor-logic Analyst
**Target**: (1) an executable ADR status-drift detector; (2) an opt-in `--full` tier for `/qor-status`
**Scope**: `docs/ADR_*.md` front matter, `docs/GOVERNANCE_INDEX.md` tier contracts, `qor/scripts/` lint and gh-introspection conventions, actor classification, skill size headroom

---

## Executive Summary

Both capabilities are buildable, and neither needs new infrastructure. The ledger walker, the lint CLI convention, the gh fail-safe pattern, the check-ladder registry, and an actor classifier all already exist and were verified by execution against live data. The blocking finding is upstream of the detector: the three ADRs share **no common machine-readable field** binding them to an implementing phase, and the one carrying the stalest status (`ADR_QOR_ROADMAP.md`) names neither a phase nor an issue. A detector written against today's front matter would bind two of three ADRs and silently pass the worst offender. The first deliverable is therefore an ADR front-matter contract, not a detector.

Two secondary findings: the ADRs are registered in a governance-index tier whose drift contract has no freshness marker to check, and actor classification exists twice with divergent predicates behind a docstring that falsely claims parity.

## Findings

### 1. ADR front matter: three dialects, no common binding field (DRIFT)

| ADR | Status line | Phase named | Issue named | Field separation |
|---|---|---|---|---|
| `docs/ADR_EXECUTION_CONTEXT_ADAPTIVE_GOVERNANCE.md:3` | `**Status:** Accepted for Phase 240 implementation` | yes (240) | yes (`:5` GH #379) | blank-line |
| `docs/ADR_PORTABLE_GOVERNANCE_ENGINE_BOUNDARY.md:3` | `**Status:** Proposed for Phase 241, revised after governed-procedure evidence review` | yes (241) | yes (`:5` GH #381) | blank-line |
| `docs/ADR_QOR_ROADMAP.md:3` | `**Status:** Proposed, amended after pre-implementation adversarial review; formal /qor-audit still required` | **no** | **no** | contiguous |

`ADR_QOR_ROADMAP.md:3-6` also carries two fields the others lack (`**Scope:**`, `**Adversarial review:**`) and omits the `**Issue:**` field both others carry. The intersection of machine-readable fields across all three files is the literal `**Status:**` label and nothing else.

Consequence: a phase-binding detector keyed on `Phase (\d+)` in the status line resolves ADRs 1 and 2 and returns *no finding* for ADR 3, which is the most stale of the three, still claiming `/qor-audit` is required for work that was audited and sealed at entries #653-#656. **The detector would report clean on the single artifact that motivated it.**

### 2. Phase-to-ledger binding works, verified by execution

`qor/scripts/meta_ledger_walker.py:73` `walk()` executed against `docs/META_LEDGER.md`:

- 722 records returned; `grep -cE '^### Entry #'` also returns 722. The walker is a **complete** enumeration, not a lossy one.
- Ids run 1..724 with 510 and 532 absent. `grep -nE '^### Entry #(510|532)\b'` exits 1, so these are genuine numbering gaps in the ledger itself, not parser drops. Pre-existing and out of scope here; noted so a future reader does not mistake it for a walker defect.
- `LedgerRecord.phase_label` (`meta_ledger_walker.py:29-35`) carries `"<KIND> -- Phase <NNN> <slug> (<version>)"`.
- 582 of 722 records name a phase.

Binding executed against the three ADR target phases:

| Phase | Entries | `SESSION SEAL` entry |
|---|---|---|
| 239 | 653, 654, 655, 656 | **656** |
| 240 | 643, 644, 645 | **644** |
| 241 | 646, 647, 648, 649 | **649** |

`SESSION SEAL -- Phase <N>` is a reliable "this phase shipped" predicate. The detector needs no new ledger parsing.

### 3. The ADRs are already registered, in a tier with no freshness marker (DRIFT)

All three are Tier 2 rows: `docs/GOVERNANCE_INDEX.md:45`, `:46`, `:48`.

Tier 2's contract (`docs/GOVERNANCE_INDEX.md:26-28`) reads: *"Stable; changes are explicit doctrine events. Drift signal: rules contradict each other or operator memory."* Its table is `| Artifact | Path |` with **no freshness-marker column**. Tier 1's table (`:14-24`) has one (`| Artifact | Path | Freshness marker |`).

An ADR whose status says `Proposed` after its implementing phase sealed is precisely a freshness defect, and Tier 2 as specified has nothing to check it against. Either the ADR rows are mis-tiered, or Tier 2 needs a marker column for them. This is a doctrine decision for `/qor-plan`, not a detector detail.

### 4. Lint conventions the detector must match

- `qor/scripts/governance_index.py:184-224`: `main(argv) -> int`; flags `--repo-root`, `--enforce`, `--cross-check-ledger`, `--dry-run`; findings as a frozen `IndexFinding(kind, path, reason)`; `_emit(findings, fail_closed)` at `:216-224` returns `1 if findings else 0`; error path returns `2` (`:205`).
- `qor/cli.py:262-281`: generic `scripts` / `reliability` family dispatch. A new `qor/scripts/<name>.py` is reachable as `qor-logic scripts <name> [args]` **with no registration step**.
- `qor/scripts/status_json.py:30-105`: `Check` dataclass registry, `run_check` (never raises; an exception records exit 3, `:63-77`), `run_all` (`:78`), `default_registry(repo_root)` (`:88-105`), `--self-test` (`:108`). This is the ladder the nightly job runs, and the natural wiring point for an ADR check.

### 5. Actor classification exists twice, divergently (DRIFT)

| Site | Predicate |
|---|---|
| `qor/scripts/github_surface.py:45-53` `is_machine_author(login)` | `endswith("[bot]") or startswith("app/")` |
| `qor/scripts/pr_citation_lint.py:89-95` `is_exempt_actor(actor)` | `endswith("[bot]")` only |

`github_surface.py:48` documents itself as *"Same reasoning as `pr_citation_lint.is_exempt_actor`"* while implementing a strictly wider predicate, and `:49-50` explains exactly why the wider form is needed: `gh pr list --json author` returns the `app/dependabot` form, not the `dependabot[bot]` trailer form.

**Graded honestly: latent, not live.** `pr_citation_lint`'s only caller is `.github/workflows/pr-lint.yml:71`, which passes `github.event.pull_request.user.login`. That emits `dependabot[bot]`, matched by the narrow predicate. The trap fires only when a future caller feeds it a `gh --json author` value. The defect today is the false parity claim in the docstring; a third classifier added by the `--full` tier would compound it.

Measured baseline for the tier's actor split (`origin/main`, 722 commits):

| Class | Identity | Commits | Share |
|---|---|---|---|
| developer | 3 name aliases on one email | 621 | 86.0% |
| agent | QoreLogic Governor | 76 | 10.5% |
| agent | Claude | 12 | 1.7% |
| **bot** | dependabot[bot] | **9** | **1.2%** |
| bot | qor-governance-bot, github-actions[bot] | 4 | 0.6% |

Dependabot pull requests all-time: 15 (10 merged, 5 closed, **0 open**); zero dependabot branches outstanding. The bot rows are a rounding error against the developer and agent rows, which is the finding that justifies splitting them out rather than the reverse: an operator reading a single undifferentiated count cannot tell a 1.2% automation row from real outstanding work.

### 6. gh fail-safe: reuse `github_surface`, not `merge_readiness`

Ten scripts shell out to `gh`: `ac_close_guard`, `collect_shadow_genomes`, `configure_pypi_environment`, `create_shadow_issue`, `dep_admit_override_tracker`, `dependency_admission_lint`, `github_surface`, `merge_readiness`, `qor_platform`, `release_ci_gate`.

Two incompatible strategies:

- `github_surface.py:74-84` `_gh_json` raises `RuntimeError` on non-zero exit; `main(argv, fetcher=fetch_surface)` at `:111` takes a **dependency-injected fetcher** so tests never invoke `gh`, and catches `(RuntimeError, OSError, ValueError)` at `:122-124` to print one `ERROR` line and return `2`. `OSError` covers `gh` absent from PATH. This is the reusable pattern.
- `merge_readiness.py:93-104` `fetch_checks` shells out with no injection and *deliberately tolerates* a non-zero exit (`:99`) because `gh pr checks` exits non-zero whenever a check is failing or pending. Its testability lives in the pure `classify` (`:74`) instead.

No `shutil.which("gh")` probe exists anywhere in the corpus. The `--full` tier should follow the injection pattern and degrade to a named `gh unavailable` row rather than failing the status read. CI and forks have no token, and a status command that errors on a missing optional tool is worse than one that says so.

### 7. Skill size headroom: measured, not a constraint

`qor/skills/memory/qor-status/SKILL.md` is **7,369 bytes**. `qor/scripts/skill_size_budget_lint.py:23-24` sets `WARN_BYTES = 25 KB` and `EXCEEDED_BYTES = 40 KB`. Headroom to WARN: **18,231 bytes**.

Current WARN findings are `qor-audit` (38.3 KB), `qor-substantiate` (36.4 KB), and `qor-plan` (25.6 KB). `qor-status` is not among them. Documenting a `--full` flag costs a few hundred bytes against roughly 18 KB of headroom. The progressive-disclosure pressure that constrained Phase 257's seal-skill wiring **does not apply here**, and the phase should not be planned as though it does.

The `<5KB context impact` target in the skill body is a *runtime read budget*, not a file-size budget. It stays intact by construction if the default path is unchanged and `--full` is a separate module the skill invokes only on the explicit flag.

## Blueprint Alignment

| Claim | Actual finding | Status |
|---|---|---|
| ADR status lines name their implementing phase | 2 of 3 do; `ADR_QOR_ROADMAP.md:3` names no phase and no issue | **DRIFT** |
| ADRs are tracked governance artifacts | Registered at `GOVERNANCE_INDEX.md:45,46,48` | MATCH |
| The tracking tier can express staleness | Tier 2 (`:26-28`) has no freshness-marker column | **DRIFT** |
| Ledger binding needs new parsing | `meta_ledger_walker.walk()` is complete and carries `phase_label` | MATCH (reuse) |
| A new script needs CLI registration | `qor/cli.py:262-281` dispatches `qor/scripts/*` generically | MATCH (reuse) |
| Actor classification must be written | Exists at `github_surface.py:45`, duplicated divergently at `pr_citation_lint.py:89` | **DRIFT** |
| gh introspection must be written | `github_surface.py:74-124` supplies fetch, injection, and fail-safe | MATCH (reuse) |
| `/qor-status` is near its size budget | 7,369 B against a 25 KB WARN threshold | **DRIFT** (the assumption was wrong) |

## Recommendations

1. **P0. Define the ADR front-matter contract before writing any detector.** One required, machine-readable binding field on every ADR (`**Phase:** NNN`, or `**Status:** <verb> for Phase NNN`), plus a closed status vocabulary. Without it the detector's coverage is 2 of 3 and its blind spot is the motivating case. Backfill `ADR_QOR_ROADMAP.md`.
2. **P0. Decide the tier question.** Either move ADR rows to a tier with a freshness marker, or add a marker column to Tier 2. The detector needs a contract to enforce; today Tier 2 gives it none.
3. **P1. Build the detector as `qor/scripts/adr_status_lint.py`.** Match `governance_index.py`'s CLI and finding shape; bind via `meta_ledger_walker.walk()` plus `SESSION SEAL -- Phase <N>`; register as a `Check` in `status_json.default_registry` so the nightly ladder carries it. Advisory (exit 1, WARN) in V1. Fail-closed at seal is a V2 decision after the false-positive rate is observed, consistent with how `skill_size_budget_lint` and `procedural_fidelity` were staged.
4. **P1. Consolidate actor classification first, then reuse it.** Promote one predicate (the wider `github_surface` form) to a shared home, repoint `pr_citation_lint.is_exempt_actor` at it, and correct the false parity docstring at `github_surface.py:48`. The `--full` tier consumes that one function. Do not add a third.
5. **P2. Build `--full` as `qor/scripts/status_full.py`,** invoked by the skill only on the explicit flag. Follow `github_surface`'s injected-fetcher pattern; every gh-dependent row degrades to a named `unavailable` row rather than an error. Report bot rows in a separate, labeled block from developer and agent rows.
6. **P2. Prune the branch backlog separately.** 30 unmerged remote branches and roughly 40 local branches tracking `gone` remotes are the largest single source of noise the `--full` tier would report on day one. Cleaning them first makes the tier's first output legible; leaving them makes it look broken.

## Updated Knowledge

For `qor/references/` on implementation:

- The corpus has **no ADR contract**. `grep -rlni "ADR" qor/references/ qor/gates/` hits only `doctrine-negative-constraints.md`, `downstream-enforcement-boundary.md`, `patterns-architecture.md`, `patterns-project-planning.md`, and `delegation-table.md`, all incidental mentions. `doc_integrity.py`, `governance_index.py`, and `governance_health.py` contain zero ADR-aware logic. ADRs are registered but ungoverned.
- Two divergent machine-author predicates exist, one of which documents parity it does not have (`github_surface.py:48` against `pr_citation_lint.py:89-95`). Recorded so the next consumer reuses rather than adds a third.
- `meta_ledger_walker.walk()` is a complete enumeration of `^### Entry #` headings (722 of 722, verified 2026-09-04). Ledger ids 510 and 532 are genuine numbering gaps in the file, not parser loss.

---

_Research complete. Findings are advisory; implementation decisions remain with the Governor._
