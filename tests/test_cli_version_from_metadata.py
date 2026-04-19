"""Regression guard: qor.cli.__version__ must match the installed package
metadata version, not a hardcoded string.

SG-Phase34-A: stale hardcoded versions across six releases (v0.18.0 -
v0.24.0) because the CLI kept a string literal that nothing mechanically
updated on bump. Fix: read via importlib.metadata at module load.
"""
from __future__ import annotations

from importlib import metadata

import qor.cli as cli


def test_cli_version_matches_package_metadata():
    expected = metadata.version("qor-logic")
    assert cli.__version__ == expected, (
        f"qor.cli.__version__ ({cli.__version__!r}) diverged from "
        f"importlib.metadata.version('qor-logic') ({expected!r}). "
        "Do not hardcode the version in cli.py -- read it from package metadata."
    )


def test_cli_version_not_hardcoded_literal():
    """Rule-4 structural guard: cli.py source must not carry a
    SemVer-shaped string literal on the __version__ line."""
    import re
    from pathlib import Path

    src = Path(cli.__file__).read_text(encoding="utf-8")
    for line in src.splitlines():
        stripped = line.strip()
        if stripped.startswith("__version__"):
            assert not re.search(r'"\d+\.\d+\.\d+"', stripped), (
                f"cli.py carries a hardcoded version literal: {stripped!r}. "
                "Use importlib.metadata.version('qor-logic') instead."
            )
