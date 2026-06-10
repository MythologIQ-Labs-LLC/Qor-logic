# Plan: Phase 161 — deterministic naming in test_merge_velocity_check (CI flake fix)

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

None.

## Problem

`tests/test_merge_velocity_check.py::_make_merge_commit` derives the feature
branch name and the touched filename from `abs(hash(subject)) % 100000`:

> `sed -n '57,58p'` ->
> `files = files or {f"feature_{safe}_{abs(hash(subject)) % 100000}.txt": subject}`
> `branch = f"feat-{abs(hash(subject)) % 100000}"`

Python's builtin `hash()` of a `str` is randomized per process by `PYTHONHASHSEED`,
and the `% 100000` truncation collides distinct subjects. Within one test repo
the subjects are distinct (`feature {i}`, `fix: {i}`, ...), but on a seed where
two of them collide mod 100000 the second `git checkout -b feat-<n>` hits an
existing branch and exits 128 -- a nondeterministic CI failure that flaked
`test_recommended_action_maps_from_grade` + `test_main_cli_exits_one_on_exceeded`
on the ubuntu-3.13 matrix cell during the Phase 158 PR while the other five cells
passed. This violates the test-discipline doctrine (no hidden random coupling).

## Phase 1: deterministic, collision-resistant feat suffix

### Affected Files

- `tests/test_merge_velocity_check.py` - EDIT. Add a pure `_feat_suffix(subject)`
  helper returning a deterministic hex digest, use it for both the branch and
  filename in `_make_merge_commit`, and add behavioral tests pinning its
  determinism + collision-freedom.

### Changes

- Add `_feat_suffix(subject: str) -> str` returning
  `hashlib.sha1(subject.encode("utf-8")).hexdigest()[:8]` (stdlib `hashlib` is
  already importable; add the import if absent). It is a pure function of its
  input -- deterministic across processes (no `PYTHONHASHSEED` dependence) and
  collision-resistant for distinct subjects (no mod-100000 truncation).
- Replace both `abs(hash(subject)) % 100000` sites in `_make_merge_commit` with
  `_feat_suffix(subject)`: `branch = f"feat-{_feat_suffix(subject)}"` and the
  default filename `f"feature_{safe}_{_feat_suffix(subject)}.txt"`.

### Unit Tests

- `tests/test_merge_velocity_check.py`:
  - `test_feat_suffix_is_deterministic_and_seed_independent` — asserts
    `_feat_suffix("feature 3")` equals `hashlib.sha1(b"feature 3").hexdigest()[:8]`
    (pins the algorithm, proving it does not use the seed-randomized builtin
    `hash()`), and that a repeat call returns the identical value.
  - `test_feat_suffix_unique_across_the_exercised_subject_range` — builds the
    subject set the suite actually uses (`feature {i}`, `fix: {i}`, `recent {i}`,
    `old {i}` for i in 0..300) and asserts every `_feat_suffix` value is distinct,
    so no within-repo `git checkout -b` collision can occur (the exit-128 class).

## Definition of Done

### Deliverable: deterministic test naming

- **D1**: `_make_merge_commit` produces branch/file names that are a deterministic
  function of the subject, eliminating the `PYTHONHASHSEED` mod-collision flake.
- **D2**: `_feat_suffix` in `tests/test_merge_velocity_check.py`; both
  `abs(hash(...)) % 100000` sites replaced.
- **D3**: Ledger SESSION SEAL records the CI-flake hotfix; CHANGELOG `### Fixed`.
- **D4**: `tests/test_merge_velocity_check.py::test_feat_suffix_is_deterministic_and_seed_independent`
  and `::test_feat_suffix_unique_across_the_exercised_subject_range` pass; the
  existing velocity tests stay green.

## CI Commands

- `python -m pytest tests/test_merge_velocity_check.py -v` — flake-prone tests now deterministic.
- `python -m pytest tests/ -q` — full suite stays green.
