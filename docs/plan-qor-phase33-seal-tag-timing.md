# Plan: Phase 33 — seal-tag timing fix + release-doc currency + main reconciliation

**change_class**: feature
**target_version**: v0.24.0
**doc_tier**: system
**terms_introduced**:
- release_docs (canonical home: `qor/references/doctrine-documentation-integrity.md`)
- seal_tag_timing (canonical home: `qor/references/doctrine-governance-enforcement.md`)

## Open Questions

None. Scope pre-decided by operator per post-Phase-32 inventory: timing bug + currency gap + main drift.

## Context

Post-Phase-32 forensics uncovered two defects:

1. **Seal-tag timing bug**: `governance_helpers.create_seal_tag` is called at `/qor-substantiate` Step 7.5, but the seal commit is made at Step 9.5. The tag therefore points at the pre-seal HEAD. Confirmed across v0.19.0–v0.22.0: every tag points at a commit whose `pyproject.toml` is one version behind the tag. v0.23.0 accidentally escaped via the manual retag during the Phase 32 PR #4 amend race.

2. **Release-doc currency gap**: Step 6.5 `check_documentation_currency` covers the 4 system-tier docs but not README.md or CHANGELOG.md. Static version references ("What's new in v0.22.0") in README survived Phase 32 seal, producing version drift visible to end users after PyPI install. SG #22 (SG-Phase32-B) records this.

3. **Main reconciliation**: PR #4 auto-merged at pre-amend commit `b671964`; the amended content lives only at `v0.23.0 → d2e87ee`. Addressed by the merge commit already made at the base of this phase branch (`f527727`).

## Phase 1: Seal-tag timing fix

### Unit Tests (TDD — written first)

- `tests/test_seal_tag_timing.py` — NEW file
  - `test_create_seal_tag_targets_explicit_commit` — when `create_seal_tag` is called with `commit=<sha>`, the resulting `git tag -a` argv contains the SHA (monkeypatched `subprocess.run` capture).
  - `test_create_seal_tag_raises_without_commit` — calling `create_seal_tag` without the `commit` argument raises `TypeError` (required-parameter contract; no HEAD-default fallback exists).
  - `test_create_seal_tag_message_unchanged` — message body still contains `Merkle seal:`, `Ledger entry:`, `Phase:`, `Class:` lines verbatim (protect existing ledger-machine-readable format).

- `tests/test_substantiate_tag_timing_wired.py` — NEW file (structural lint, Rule 4)
  - `test_skill_creates_tag_after_seal_commit` — greps `qor/skills/governance/qor-substantiate/SKILL.md`: `create_seal_tag(` must appear in a step numbered ≥ 9.5. Fail if any occurrence remains at Step 7.5.
  - `test_skill_step_7_5_bumps_version_only` — Step 7.5 section contains `bump_version(` but NOT `create_seal_tag(`.
  - `test_skill_step_9_5_5_captures_commit_and_tags` — Step 9.5.5 section contains (a) `git rev-parse HEAD`, (b) `create_seal_tag(` with a `commit=` kwarg. Verifies positive wiring, not just absence elsewhere (SG-Phase32-A).

### Affected Files

- `tests/test_seal_tag_timing.py` — new test module (behavior contract for the fixed helper)
- `tests/test_substantiate_tag_timing_wired.py` — new structural lint test (Rule 4 pairing for the skill-prose change)
- `qor/scripts/governance_helpers.py` — `create_seal_tag` gains required positional `commit: str` parameter; argv is `["git", "tag", "-a", tag, commit, "-m", message]`
- `qor/skills/governance/qor-substantiate/SKILL.md` — Step 7.5 reduced to `bump_version` only; add Step 9.5.5 (post-commit, pre-stage-report) that captures `HEAD` SHA and calls `create_seal_tag(..., commit=sha)`

### Changes

```python
# governance_helpers.py
def create_seal_tag(
    version: str, seal: str, entry: int, phase: int, klass: str, commit: str,
) -> str:
    tag = f"v{version}"
    message = (
        f"v{version}\n\n"
        f"Merkle seal: {seal}\n"
        f"Ledger entry: #{entry}\n"
        f"Phase: {phase}\n"
        f"Class: {klass}\n"
    )
    subprocess.run(
        ["git", "tag", "-a", tag, commit, "-m", message], check=True,
    )
    return tag
```

`commit` is required. No HEAD-default fallback (doctrine: no backwards-compat hacks).

```python
# qor-substantiate SKILL.md Step 9.5.5 (new)
import subprocess
commit_sha = subprocess.run(
    ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
).stdout.strip()
tag = gh.create_seal_tag(
    new_version, merkle_seal, ledger_entry_num, phase_num, change_class,
    commit=commit_sha,
)
```

## Phase 2: Release-doc currency coverage

### Unit Tests (TDD)

- `tests/test_release_doc_currency.py` — NEW file
  - `test_change_class_feature_requires_readme` — plan_payload with `change_class=feature` and implement_payload missing README.md triggers a warning naming README.md.
  - `test_change_class_feature_requires_changelog` — same for CHANGELOG.md.
  - `test_change_class_breaking_requires_release_docs` — `change_class=breaking` behaves like feature.
  - `test_change_class_hotfix_exempt` — `change_class=hotfix` does NOT trigger release-doc warnings (hotfixes can skip release-notes authoring; caught separately).
  - `test_change_class_feature_with_both_covers` — feature class with README.md + CHANGELOG.md in files_touched returns no release-doc warnings.
  - `test_no_plan_payload_no_release_docs_warning` — when `plan_payload=None` (legacy call site), release-doc branch is skipped; existing system-tier trigger behavior preserved.

### Affected Files

- `tests/test_release_doc_currency.py` — new test module
- `qor/scripts/doc_integrity_strict.py` — add `_RELEASE_DOCS = frozenset({"README.md", "CHANGELOG.md"})` and `_RELEASE_CLASSES = frozenset({"feature", "breaking"})`; extend `check_documentation_currency` signature with `plan_payload=None`; add release-path branch gated on `plan_payload.change_class`
- `qor/skills/governance/qor-substantiate/SKILL.md` — Step 6.5 wiring passes `plan_payload` to `check_documentation_currency`
- `qor/references/doctrine-documentation-integrity.md` — §Currency Check: add subsection documenting release-doc coverage rule, the `release_docs` term, and the change_class-based trigger
- `qor/references/glossary.md` — add `release_docs` entry

### Changes

```python
# doc_integrity_strict.py
_RELEASE_DOCS = frozenset({"README.md", "CHANGELOG.md"})
_RELEASE_CLASSES = frozenset({"feature", "breaking"})

def check_documentation_currency(
    implement_payload: dict,
    repo_root: str,
    plan_payload: dict | None = None,
) -> list[str]:
    files_touched = implement_payload.get("files_touched", [])
    normalized = [f.replace("\\", "/") for f in files_touched]
    warnings: list[str] = []

    trigger_files = [
        f for f in normalized
        if any(p in f for p in _CURRENCY_TRIGGER_PATTERNS)
    ]
    if trigger_files and not any(d in normalized for d in _SYSTEM_TIER_DOCS):
        warnings.extend(
            f"Doc-affecting change to {f} without updating any system-tier doc "
            f"({', '.join(_SYSTEM_TIER_DOCS)})"
            for f in trigger_files
        )

    if plan_payload and plan_payload.get("change_class") in _RELEASE_CLASSES:
        missing = [d for d in _RELEASE_DOCS if d not in normalized]
        warnings.extend(
            f"Release-path change (change_class={plan_payload['change_class']}) "
            f"without updating {d}"
            for d in missing
        )
    return warnings
```

```python
# qor-substantiate SKILL.md Step 6.5 wiring (updated)
warnings = check_documentation_currency(implement, repo_root=".", plan_payload=plan_artifact)
```

## Phase 3: Doctrine + Shadow Genome backfill

### Unit Tests (TDD)

- `tests/test_sg_phase33_entries.py` — NEW file
  - `test_sg_phase33_a_present` — `docs/SHADOW_GENOME.md` contains an entry with ID `SG-Phase33-A` and keyword `seal_tag_timing`.
  - `test_sg_phase33_a_cites_affected_tags` — entry body names v0.19.0, v0.20.0, v0.21.0, v0.22.0.

### Affected Files

- `tests/test_sg_phase33_entries.py` — new test module
- `docs/SHADOW_GENOME.md` — Entry #23 SG-Phase33-A (seal-tag timing bug, 4 historical tags off-by-one)
- `docs/META_LEDGER.md` — BACKFILL entry documenting the 4 affected tags (non-advancing; no chain-hash consumption; purely annotational)

### Changes

SG entry body names the mechanism (`create_seal_tag` at Step 7.5 pre-commit), the affected tags (v0.19.0–v0.22.0), the detection path (post-Phase-32 forensics via `git show <tag>:pyproject.toml`), and the countermeasure (Phase 33 Phase 1 timing fix above).

BACKFILL ledger entry cites tag → commit → pyproject-version for each of v0.19.0–v0.22.0 so future operators can inspect historical release content without repeating the forensic.

## CI Validation

```bash
python -m pytest tests/test_seal_tag_timing.py tests/test_substantiate_tag_timing_wired.py tests/test_release_doc_currency.py tests/test_sg_phase33_entries.py -q
python -m pytest -q  # full suite must stay green
python qor/scripts/doc_integrity_strict.py  # structural lint (no new violations)
```
