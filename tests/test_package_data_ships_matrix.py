"""Phase 142: the compliance control matrix must ship in the package so a pip
consumer receives it. Parses pyproject and asserts a package-data glob covers
the matrix path -- without this the downstream SDK has no manifest.
"""
from __future__ import annotations

import fnmatch
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - py<3.11
    import tomli as tomllib  # type: ignore

REPO = Path(__file__).resolve().parents[1]
_MATRIX_REL = "compliance/control_matrix.json"  # relative to the qor package


def _package_data_globs() -> list[str]:
    data = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    return data["tool"]["setuptools"]["package-data"]["qor"]


def test_matrix_covered_by_package_data():
    globs = _package_data_globs()
    assert any(fnmatch.fnmatch(_MATRIX_REL, g) for g in globs), (
        f"no package-data glob in {globs} matches {_MATRIX_REL}; "
        "the control matrix would not ship to pip consumers"
    )


def test_matrix_file_actually_exists_at_packaged_path():
    assert (REPO / "qor" / _MATRIX_REL).is_file()
