"""Phase 213 (GH #304): ruff is adopted narrowly, and the narrowing cannot drift.

The adoption rests on rot and orthogonality, not on defects found: the full
default rule set produced 254 findings and zero real defects. Pyflakes is
selected because it is the only class that could catch a live `NameError`, and
because nothing else in this repository reads Python for correctness.

It landed at zero with no baseline file. An uncleaned baseline becomes a
permanently-red control, which this project has already repaired twice.
"""
from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"


def _config() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def test_ruff_is_a_declared_dev_dependency():
    """A CI step may not depend on a tool the project does not install."""
    dev = _config()["project"]["optional-dependencies"]["dev"]
    assert any(spec.startswith("ruff") for spec in dev), (
        f"ruff must be declared in the dev extra; got {dev}"
    )


def test_ruff_config_selects_pyflakes_only():
    """Broadening the rule set must be a deliberate edit, not a drift."""
    ruff = _config()["tool"]["ruff"]
    assert ruff["lint"]["select"] == ["F"], (
        "select must remain exactly ['F']; the E style rules produced 24 of the "
        "254 original findings and zero defects, so they were excluded by "
        f"decision. Got {ruff['lint']['select']}"
    )
    assert "tests/fixtures/ab_corpus" in ruff["exclude"], (
        "the seeded-defect corpus is excluded by path; it holds deliberately "
        "broken code used as detector fixtures"
    )
    assert "secret-scan" in ruff["lint"]["external"], (
        "`# noqa: secret-scan` belongs to this project's own secret_scanner. "
        "Declaring it external stops ruff treating it as a malformed directive "
        "of its own; those suppressions must never be edited away."
    )


def test_no_baseline_file_exists():
    """Landing at zero is the contract; a baseline would reintroduce the
    permanently-red-control failure mode."""
    for candidate in (".ruff_baseline", "ruff-baseline.json", ".ruff.toml"):
        assert not (REPO_ROOT / candidate).exists(), (
            f"{candidate} would baseline findings instead of clearing them"
        )


def test_live_tree_is_ruff_clean():
    """The regression lock: the adoption stays at zero."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "qor/", "tests/"],
        cwd=str(REPO_ROOT), capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    assert result.returncode == 0, (
        "ruff must report zero findings; fix them rather than baselining:\n"
        + result.stdout[:4000]
    )
