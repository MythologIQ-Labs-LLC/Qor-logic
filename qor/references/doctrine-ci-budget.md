# Doctrine: CI Budget

**Goal**: GitHub Actions minutes are bounded; cost-blind workflows blow the budget. This doctrine codifies rules every workflow MUST follow before being added to `.github/workflows/`.

**Source**: pre-emptive — no workflows exist today. Doctrine + audit test ship before the first workflow does.

## Rules

### Rule 1 — No scheduled workflows without justification

Workflows declaring a `schedule:` trigger MUST include a comment block at the top of the file containing the literal string `cost justification:` followed by an estimate of monthly minute consumption and the business reason.

Example:

```yaml
# cost justification: ~30 min/month (cron daily, ~1min run).
# Reason: nightly dependency vulnerability scan; legal/security requirement.
on:
  schedule:
    - cron: '0 5 * * *'
```

Without this comment block, the workflow audit test fails.

### Rule 2 — Path filters mandatory

Every workflow MUST declare `paths-ignore:` (or `paths:` for inclusion) on its `on:` triggers. Default exclusions for any code/build workflow:

```yaml
on:
  push:
    paths-ignore: ['docs/**', '*.md', '.gitignore']
```

Doc-only changes burning CI minutes is the most common waste pattern.

### Rule 3 — No matrix without justification

Workflows with `matrix:` MUST include a `# matrix justification: <reason>` comment explaining why test logic genuinely differs per matrix axis.

A 5-OS × 4-Python matrix is 20× the cost of a single-Linux/single-Python run. Justify the multiplier or remove it.

### Rule 4 — Caching for setup-python

Workflows that explicitly use the `actions/setup-python@` action MUST also declare the `cache:` parameter (or invoke `actions/cache` separately for pip cache). Workflows using uv/poetry/pdm/Docker images choose their own caching mechanism; the rule applies only to direct setup-python usage.

Example:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.11'
    cache: 'pip'
```

### Rule 5 — Pre-commit hook ownership

Fast checks run pre-commit, not in CI:

- Drift detection (`qor/scripts/check_variant_drift.py`)
- Doctrine tests (`tests/test_skill_doctrine.py`)
- Lint
- Single-file unit tests with no external state

CI runs only what cannot be done locally:

- gh-CLI integration tests
- Multi-platform sanity (when justified per Rule 3)
- Full test suite on PR/main only (not every push)

### Rule 6 — Concurrency control

Every workflow MUST declare:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

Without this, every PR push triggers a fresh run while prior runs continue, doubling/tripling cost.

## Verification

`tests/test_workflow_budget.py` enforces these rules. The test passes vacuously when `.github/workflows/` is empty (preventive infrastructure). When the first workflow lands, all 7 tests run and any rule violation fails CI.

## Parsing strategy

Tests use **regex only** — no `pyyaml` or other YAML parser dependency. Workflows are small, line-based; regex covers the rules. YAML-aware refactor deferred to Phase 13 if rules outgrow regex.

## Update protocol

When new GitHub Actions cost patterns emerge (e.g., new actions with hidden multipliers), add the rule here AND extend `tests/test_workflow_budget.py`. Doctrine and test ship together; never one without the other.
