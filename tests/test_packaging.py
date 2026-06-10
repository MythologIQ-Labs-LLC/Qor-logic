"""Phase 19: PyPI packaging configuration tests.

Asserts pyproject.toml declares the fields required for `pip install qor-logic`
to produce a valid wheel with all resources included.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"


def _load() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def test_pyproject_declares_packages_find():
    config = _load()
    find = config.get("tool", {}).get("setuptools", {}).get("packages", {}).get("find", {})
    assert "include" in find, "[tool.setuptools.packages.find] must declare include"
    assert "exclude" in find, "[tool.setuptools.packages.find] must declare exclude"
    assert "qor*" in find["include"], "include must cover qor* namespace"


def test_pyproject_declares_package_data():
    config = _load()
    package_data = config.get("tool", {}).get("setuptools", {}).get("package-data", {})
    assert "qor" in package_data, "[tool.setuptools.package-data] must declare qor"
    globs = package_data["qor"]
    required_fragments = [
        "skills/",
        "references/",
        "agents/",
        "gates/schema/",
        "compliance/",
        "py.typed",
        "platform/",
        "templates/",
        "dist/variants/",
    ]
    globs_joined = "\n".join(globs)
    for fragment in required_fragments:
        assert fragment in globs_joined, f"package-data must include {fragment} glob"


def test_pyproject_declares_entry_point():
    config = _load()
    scripts = config.get("project", {}).get("scripts", {})
    assert scripts.get("qorlogic") == "qor.cli:main", (
        "[project.scripts] must declare qorlogic = 'qor.cli:main'"
    )


def test_pyproject_declares_readme():
    config = _load()
    assert config.get("project", {}).get("readme") == "README.md", (
        "[project] must declare readme = 'README.md'"
    )


def test_pyproject_declares_classifiers():
    config = _load()
    classifiers = config.get("project", {}).get("classifiers", [])
    joined = "\n".join(classifiers)
    for version in ("3.11", "3.12", "3.13"):
        assert f"Python :: {version}" in joined, (
            f"classifiers must include Python :: {version}"
        )
