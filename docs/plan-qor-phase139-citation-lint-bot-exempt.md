# Plan: Exempt bot authors from the PR citation lint (unblock dependabot)

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

None. dependabot (and any `*[bot]` author) raises machine-generated PRs with no plan/ledger/Merkle-seal to cite, so `qor/scripts/pr_citation_lint.py` fails them whenever they touch non-doc files (e.g. `.github/workflows/*.yml` action bumps). The fix moves the exemption into the Python lint (testable) and has the workflow pass the PR author. Mirrors the existing doc-only skip in `pr-lint.yml`.

## Feature Inventory Touches

(`docs/FEATURE_INDEX.md` absent; declared for traceability. Touches `qor/scripts` + tests.)

- entry_id: `n/a` · operation: `MODIFIED` · test_path: `tests/test_pr_citation_lint.py` · test_descriptor: `is_exempt_actor returns True for any login ending in [bot] (dependabot[bot], renovate[bot]) and False for human logins; main(["--actor","dependabot[bot]"]) exits 0 even when stdin has no citations, while main(["--actor","alice"]) with an empty body exits 1`

## Phase 1: Bot-actor exemption in `qor/scripts/pr_citation_lint.py`

### Affected Files

- `tests/test_pr_citation_lint.py` - add behavioral tests for `is_exempt_actor` + the `--actor` exemption path in `main`.
- `qor/scripts/pr_citation_lint.py` - add `is_exempt_actor(actor)`, give `main` an `--actor` argument that short-circuits to exit 0 (skip) for bot authors before reading the body.
- `.github/workflows/pr-lint.yml` - pass `--actor "${{ github.event.pull_request.user.login }}"` to the lint invocation.

### Changes

```python
def is_exempt_actor(actor: str) -> bool:
    """True for machine authors (login ending in '[bot]', e.g. dependabot[bot]).
    Their PRs are dependency/automation bumps with no ledger entry to cite."""
    return actor.strip().lower().endswith("[bot]")
```

`main` gains `argparse` with `--actor` (default `""`). When `is_exempt_actor(args.actor)`, print a `SKIP:` line and return 0 WITHOUT reading stdin or checking citations. Otherwise the existing body read + `check_pr_body` flow is unchanged.

`pr-lint.yml` "Lint PR description" step becomes:
`printf '%s' "$PR_BODY" | python qor/scripts/pr_citation_lint.py --actor "${{ github.event.pull_request.user.login }}"`

### Unit Tests

- `tests/test_pr_citation_lint.py`:
  - `test_is_exempt_actor_true_for_dependabot` - `is_exempt_actor("dependabot[bot]") is True`. Confirms the bot predicate's output.
  - `test_is_exempt_actor_true_for_other_bot` - `is_exempt_actor("renovate[bot]") is True` (any `*[bot]`).
  - `test_is_exempt_actor_false_for_human` - `is_exempt_actor("Knapp-Kevin") is False`.
  - `test_main_skips_bot_actor_despite_missing_citations` - monkeypatch `sys.stdin` to a body with NO citations; `main(["--actor", "dependabot[bot]"]) == 0`. Confirms the exemption skips the check (not just that the body happened to pass).
  - `test_main_enforces_for_human_missing_citations` - monkeypatch `sys.stdin` to an empty body; `main(["--actor", "alice"]) == 1`. Confirms non-bot authors are still gated.
  - `test_main_passes_human_with_full_citations` - monkeypatch `sys.stdin` to a fully-cited body; `main(["--actor", "alice"]) == 0`. Confirms the actor arg does not break the normal pass path.

## Definition of Done

### Deliverable: bot-actor citation-lint exemption

- **D1**: dependabot / `*[bot]` PRs that touch non-doc files no longer fail the PR Citation Lint, while human PRs remain gated by doctrine §6.
- **D2**: `is_exempt_actor(actor) -> bool` and a `--actor` argument on `main` in `qor/scripts/pr_citation_lint.py`; `.github/workflows/pr-lint.yml` passes the PR author.
- **D3**: hotfix seal entry in META_LEDGER; no new doc surfaces (doc_tier minimal).
- **D4**: `test_main_skips_bot_actor_despite_missing_citations` asserts `main(["--actor","dependabot[bot]"]) == 0` over an uncited body; `test_main_enforces_for_human_missing_citations` asserts `== 1` for a human.

## CI Commands

- `python -m pytest tests/test_pr_citation_lint.py -q` — new behavior, run twice for determinism.
- `python -m pytest -q` — full suite green before substantiate.
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase139-citation-lint-bot-exempt.md` — plan self-consistency.
