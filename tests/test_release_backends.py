"""Behavioral tests for Phase 133 (GH #163): pluggable version-bump + changelog
backends for non-Python release mechanics.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qor.scripts import version_backends as vb
from qor.scripts import changelog_backends as cb
from qor.scripts import governance_helpers as gh


@pytest.fixture(autouse=True)
def _no_tag_coupling(monkeypatch: pytest.MonkeyPatch):
    # Decouple bump tag guards from this repo's live tags.
    monkeypatch.setattr(gh, "_list_tags", lambda: [])
    monkeypatch.setattr(gh, "_highest_tag", lambda tags: None)


def _node(root: Path, version: str) -> Path:
    p = root / "package.json"
    p.write_text(json.dumps({"name": "x", "version": version}), encoding="utf-8")
    return p


def _rust(root: Path, version: str) -> Path:
    p = root / "Cargo.toml"
    p.write_text(f'[package]\nname = "x"\nversion = "{version}"\n', encoding="utf-8")
    return p


def _py(root: Path, version: str) -> Path:
    p = root / "pyproject.toml"
    p.write_text(f'[project]\nname = "x"\nversion = "{version}"\n', encoding="utf-8")
    return p


# --- version backends ---

def test_detect_backend_priority(tmp_path: Path) -> None:
    _node(tmp_path, "1.0.0"); _rust(tmp_path, "1.0.0")
    assert vb.detect_backend(tmp_path).name == "node"  # node before rust
    _py(tmp_path, "1.0.0")
    assert vb.detect_backend(tmp_path).name == "python"  # python wins
    assert vb.detect_backend(tmp_path / "empty") is None


def test_read_version_node(tmp_path: Path) -> None:
    _node(tmp_path, "1.2.3")
    assert vb.read_version(vb.detect_backend(tmp_path), tmp_path) == (1, 2, 3)


def test_read_version_rust(tmp_path: Path) -> None:
    _rust(tmp_path, "0.4.1")
    assert vb.read_version(vb.detect_backend(tmp_path), tmp_path) == (0, 4, 1)


def test_bump_node_writes_new_version(tmp_path: Path) -> None:
    p = _node(tmp_path, "1.2.3")
    new, backend = vb.bump(tmp_path, "feature")
    assert (new, backend) == ("1.3.0", "node")
    assert '"version": "1.3.0"' in p.read_text(encoding="utf-8")


def test_bump_rust_writes_new_version(tmp_path: Path) -> None:
    p = _rust(tmp_path, "0.4.1")
    new, backend = vb.bump(tmp_path, "hotfix")
    assert (new, backend) == ("0.4.2", "rust")
    assert 'version = "0.4.2"' in p.read_text(encoding="utf-8")


def test_bump_python_delegates(tmp_path: Path) -> None:
    p = _py(tmp_path, "0.5.0")
    new, backend = vb.bump(tmp_path, "feature")
    assert backend == "python" and new == "0.6.0"
    assert 'version = "0.6.0"' in p.read_text(encoding="utf-8")


def test_bump_no_backend_raises(tmp_path: Path) -> None:
    with pytest.raises(vb.NoBackendError):
        vb.bump(tmp_path, "feature")


# --- changelog backends ---

def test_detect_keepachangelog() -> None:
    assert cb.detect_changelog_format("# CL\n\n## [Unreleased]\n\n- x\n") == "keepachangelog"


def test_detect_prepend() -> None:
    assert cb.detect_changelog_format("# CL\n\n## v1.0.0\n\n- x\n") == "prepend"


def test_stamp_prepend_inserts_section(tmp_path: Path) -> None:
    p = tmp_path / "CHANGELOG.md"
    p.write_text("# Changelog\n\n## v1.2.3\n\n- old thing\n", encoding="utf-8")
    fmt = cb.stamp(p, "1.3.0", "2026-06-02")
    text = p.read_text(encoding="utf-8")
    assert fmt == "prepend"
    assert "## v1.3.0 - 2026-06-02" in text
    assert "old thing" in text  # prior content preserved
    assert text.index("v1.3.0") < text.index("v1.2.3")  # prepended above prior


def test_stamp_keepachangelog_delegates(tmp_path: Path) -> None:
    p = tmp_path / "CHANGELOG.md"
    p.write_text("# Changelog\n\n## [Unreleased]\n\n- a feature\n", encoding="utf-8")
    fmt = cb.stamp(p, "1.3.0", "2026-06-02")
    assert fmt == "keepachangelog"
    assert "## [1.3.0] - 2026-06-02" in p.read_text(encoding="utf-8")


# --- end-to-end non-Python + wiring ---

def test_end_to_end_non_python_repo(tmp_path: Path) -> None:
    pkg = _node(tmp_path, "2.0.0")
    cl = tmp_path / "CHANGELOG.md"
    cl.write_text("# Changelog\n\n## v2.0.0\n\n- prior\n", encoding="utf-8")
    new, backend = vb.bump(tmp_path, "feature")
    cb.stamp(cl, new, "2026-06-02")
    assert (new, backend) == ("2.1.0", "node")
    assert '"version": "2.1.0"' in pkg.read_text(encoding="utf-8")
    assert "## v2.1.0 - 2026-06-02" in cl.read_text(encoding="utf-8")


def test_substantiate_wires_pluggable_backends() -> None:
    text = Path("qor/skills/governance/qor-substantiate/SKILL.md").read_text(encoding="utf-8")
    assert "version_backends" in text  # prose-lint: ok=prompt-contract
    assert "changelog_backends" in text  # prose-lint: ok=prompt-contract
