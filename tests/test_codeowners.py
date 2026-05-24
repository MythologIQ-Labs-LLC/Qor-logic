"""Phase 102 (GH #118 P1): CODEOWNERS structural assertions."""
from __future__ import annotations

import pathlib

_CODEOWNERS = pathlib.Path(".github/CODEOWNERS")


def _read() -> list[str]:
    return _CODEOWNERS.read_text(encoding="utf-8").splitlines()


def _rules() -> list[tuple[str, list[str]]]:
    out: list[tuple[str, list[str]]] = []
    for line in _read():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) >= 2:
            pattern, owners = parts[0], parts[1:]
            out.append((pattern, owners))
    return out


def test_codeowners_file_exists():
    assert _CODEOWNERS.is_file(), ".github/CODEOWNERS must be committed"


def test_codeowners_covers_workflow_dir():
    patterns = [p for p, _ in _rules()]
    assert any(p == "/.github/workflows/" or p == "/.github/workflows/*" for p in patterns), (
        f"CODEOWNERS must carry a rule for /.github/workflows/; patterns: {patterns!r}"
    )


def test_codeowners_covers_pyproject_and_lockfile():
    patterns = [p for p, _ in _rules()]
    assert "/pyproject.toml" in patterns, "CODEOWNERS must cover /pyproject.toml"
    assert "/requirements-release.txt" in patterns, (
        "CODEOWNERS must cover /requirements-release.txt"
    )
    assert "/requirements-release.in" in patterns, (
        "CODEOWNERS must cover /requirements-release.in"
    )


def test_codeowners_covers_intent_lock_and_env_config():
    patterns = [p for p, _ in _rules()]
    assert "/qor/reliability/intent_lock.py" in patterns, (
        "CODEOWNERS must cover /qor/reliability/intent_lock.py"
    )
    assert "/qor/scripts/configure_pypi_environment.py" in patterns, (
        "CODEOWNERS must cover /qor/scripts/configure_pypi_environment.py"
    )


def test_codeowners_every_rule_has_owner():
    for pattern, owners in _rules():
        assert owners, f"CODEOWNERS rule {pattern!r} has no owners"
        for owner in owners:
            assert owner.startswith("@"), (
                f"CODEOWNERS owner {owner!r} on {pattern!r} must start with @"
            )
