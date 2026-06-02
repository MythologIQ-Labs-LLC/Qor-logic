# Plan: Pluggable version-bump + changelog backends (non-Python release mechanics)

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: Ships #38's deferred Option 2. **Version**: `qor.scripts.version_backends` detects the repo archetype (`pyproject.toml` -> python, `package.json` -> node, `Cargo.toml` -> rust, in that priority) and bumps the version in the detected file. The python path **delegates to the unchanged `governance_helpers.bump_version`** (identical behavior for this repo's own seals); node/rust reuse the same semver compute (`_compute_new`) + tag-collision/downgrade guards (`_list_tags`/`_highest_tag`) with a format-specific read/write. **Changelog**: `qor.scripts.changelog_backends` detects keepachangelog (`## [Unreleased]` present -> delegate to the existing `changelog_stamp.apply_stamp`) vs a generic "prepend" format (no Unreleased -> prepend a `## vX.Y.Z - date` section at the top). Substantiate Step 7.5/7.6 are rewired to the pluggable entry points so non-Python repos actually bump + stamp instead of SKIP.
- non_goals: A version backend for every ecosystem (ships python+node+rust; the registry is extensible for later additions); semantic changelog reflow / entry synthesis (the prepend backend inserts a dated section header, it does not author entries); changing the python repo's seal behavior (delegation preserves it exactly).
- exclusions: Repos with none of the three manifest files still record the Phase 75 disclosed-skip (no backend detected -> skip, unchanged).

## Open Questions

None. Backend priority is pyproject > package.json > Cargo.toml (Python-first matches this repo + the existing prerequisite). Python bump delegates to the proven `bump_version` so this repo's own seals are byte-for-byte unaffected. Tag guards are shared across backends (consistent release discipline). Tests monkeypatch the tag list for the bump integration so they do not couple to this repo's live tags.

## Feature Inventory Touches

(`docs/FEATURE_INDEX.md` absent; declared for traceability. Touches `qor/scripts` + skills + tests.)

- entry_id: `n/a` · operation: `NEW` · test_path: `tests/test_release_backends.py` · test_descriptor: `version_backends.bump bumps package.json + Cargo.toml versions (delegating pyproject to governance_helpers) and changelog_backends.stamp prepends a dated section to a non-keepachangelog CHANGELOG while delegating keepachangelog to apply_stamp`

## Phase 1: Version backends (`qor/scripts/version_backends.py`)

### Affected Files

- `tests/test_release_backends.py` - NEW. Behavioral tests over node/rust/python fixtures (see Unit Tests). Written first; red before the module.
- `qor/scripts/version_backends.py` - NEW. Backend registry + detect + read + bump.

### Changes

```python
@dataclass(frozen=True)
class VersionBackend:
    name: str          # python | node | rust
    filename: str      # pyproject.toml | package.json | Cargo.toml
    pattern: re.Pattern
    template: str      # e.g. 'version = "{v}"' / '"version": "{v}"'

_TOML_RE = re.compile(r'^version\s*=\s*"(\d+)\.(\d+)\.(\d+)"', re.MULTILINE)  # pyproject + Cargo
_JSON_RE = re.compile(r'"version"\s*:\s*"(\d+)\.(\d+)\.(\d+)"')
BACKENDS = [python(pyproject), node(package.json), rust(Cargo.toml)]

def detect_backend(repo_root: Path) -> VersionBackend | None:
    """First backend whose filename exists under repo_root (priority order)."""

def read_version(backend, repo_root) -> tuple[int, int, int]: ...

def bump(repo_root: Path, change_class: str) -> tuple[str, str]:
    """Return (new_version, backend_name). Python -> governance_helpers.bump_version
    (unchanged). node/rust -> _compute_new + shared tag guards + format-specific
    atomic write. None detected -> raise NoBackendError (caller maps to skip)."""
```

De-complecting: detection, read, and write are per-backend data; the semver + tag-guard policy is shared (imported from `governance_helpers`), so all archetypes get one release discipline.

### Unit Tests

- `tests/test_release_backends.py::test_detect_backend_priority` - a repo with both `package.json` and `Cargo.toml` (no pyproject) detects `node`; pyproject present -> `python`; none -> `None`.
- `::test_read_version_node` / `::test_read_version_rust` - `read_version` parses `1.2.3` from a `package.json` / a `Cargo.toml [package]`.
- `::test_bump_node_writes_new_version` - `package.json` at `1.2.3`, `bump(repo, "feature")` (tag guards monkeypatched to empty) returns `("1.3.0", "node")` and the file now contains `"version": "1.3.0"`.
- `::test_bump_rust_writes_new_version` - `Cargo.toml` at `0.4.1`, `bump(repo, "hotfix")` -> `("0.4.2", "rust")`, file updated.
- `::test_bump_python_delegates` - a repo with only `pyproject.toml`; `bump` returns backend `python` and the version is bumped (delegated path).
- `::test_bump_no_backend_raises` - empty repo; `bump` raises `NoBackendError`.

## Phase 2: Changelog backends (`qor/scripts/changelog_backends.py`)

### Affected Files

- `tests/test_release_backends.py` - add the changelog-backend tests.
- `qor/scripts/changelog_backends.py` - NEW. Format detection + stamp dispatch.

### Changes

```python
def detect_changelog_format(text: str) -> str:
    """'keepachangelog' if '## [Unreleased]' present, else 'prepend'."""

def stamp(path: Path, version: str, date: str) -> str:
    """keepachangelog -> changelog_stamp.apply_stamp (existing). prepend ->
    insert '## v{version} - {date}\n\n' after the first heading line (or at top),
    write atomically. Returns the format used."""
```

### Unit Tests

- `::test_detect_keepachangelog` / `::test_detect_prepend` - format detection from text with/without `## [Unreleased]`.
- `::test_stamp_prepend_inserts_section` - a CHANGELOG with no Unreleased; `stamp` prepends `## v1.3.0 - <date>` near the top and the prior content is preserved below.
- `::test_stamp_keepachangelog_delegates` - a CHANGELOG with `## [Unreleased]` + a bullet; `stamp` produces the `## [1.3.0] - <date>` section (delegated to apply_stamp).

## Phase 3: Substantiate wiring + non-Python fixture

### Affected Files

- `tests/test_release_backends.py` - add the end-to-end non-Python fixture test.
- `qor/skills/governance/qor-substantiate/SKILL.md` - Step 7.5: invoke the pluggable `version_backends.bump` (detected backend) rather than assuming pyproject; the Phase 75 skip now applies only when NO backend is detected. Step 7.6: invoke `changelog_backends.stamp` (format-detected) rather than assuming keepachangelog. Update the Step Prerequisites note (`file:pyproject.toml` -> "a supported manifest: pyproject.toml / package.json / Cargo.toml").
- `qor/dist/variants/**` - regenerated.

### Changes

The skill prose calls the pluggable entry points; the python path is unchanged (delegates to `bump_version` + `apply_stamp`). Non-Python repos now perform real release mechanics.

### Unit Tests

- `::test_end_to_end_non_python_repo` - a fixture repo with `package.json` (`2.0.0`) + a non-keepachangelog `CHANGELOG.md`; `version_backends.bump` (guards monkeypatched) + `changelog_backends.stamp` bump the package.json to `2.1.0` and prepend the `## v2.1.0` section — proving off-Python release mechanics actually run.
- `::test_substantiate_wires_pluggable_backends` - read `qor-substantiate/SKILL.md`; assert it names `version_backends` and `changelog_backends`.

## Definition of Done

### Deliverable: pluggable release backends

- **D1**: a non-Python repo (package.json / Cargo.toml) bumps its version + stamps its changelog at seal instead of SKIPing; the python repo's seal behavior is unchanged.
- **D2**: `qor/scripts/version_backends.py` (`detect_backend`/`read_version`/`bump`) + `qor/scripts/changelog_backends.py` (`detect_changelog_format`/`stamp`); substantiate Step 7.5/7.6 rewired.
- **D3**: Step Prerequisites manifest note updated; META_LEDGER seal entry; version bump; variants recompiled.
- **D4**: `tests/test_release_backends.py::test_bump_node_writes_new_version` + `::test_bump_rust_writes_new_version` + `::test_stamp_prepend_inserts_section` + `::test_end_to_end_non_python_repo`.

## CI Commands

- `python -m pytest tests/test_release_backends.py -q` — backends + wiring.
- `python -m pytest tests/test_governance_helpers.py tests/test_changelog_stamp.py -q` — no regression in the delegated python path (if present).
- `python -m pytest -q` — full suite green before substantiate.
