"""Phase 25 Phase 1: qor.seed scaffold primitive."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


EXPECTED_FILES = [
    "docs/META_LEDGER.md",
    "docs/SHADOW_GENOME.md",
    "docs/ARCHITECTURE_PLAN.md",
    "docs/CONCEPT.md",
    "docs/SYSTEM_STATE.md",
    ".agent/staging/.gitkeep",
    ".qor/gates/.gitkeep",
    ".qor/session/.gitkeep",
    ".gitignore",
]


def test_seed_creates_every_expected_file(tmp_path):
    from qor.seed import seed
    result = seed(base=tmp_path, quiet=True)
    for rel in EXPECTED_FILES:
        assert (tmp_path / rel).exists(), f"Missing: {rel}"
    assert sorted(result.created) == sorted(EXPECTED_FILES)
    assert result.skipped == []


def test_seed_markdown_files_non_empty_valid_utf8(tmp_path):
    from qor.seed import seed
    seed(base=tmp_path, quiet=True)
    for rel in EXPECTED_FILES:
        if rel.endswith(".md"):
            content = (tmp_path / rel).read_text(encoding="utf-8")
            assert content.strip(), f"Empty: {rel}"


def test_seed_is_idempotent(tmp_path):
    from qor.seed import seed
    seed(base=tmp_path, quiet=True)
    original_ledger = (tmp_path / "docs/META_LEDGER.md").read_bytes()
    result = seed(base=tmp_path, quiet=True)
    assert result.created == []
    assert sorted(result.skipped) == sorted(EXPECTED_FILES)
    assert (tmp_path / "docs/META_LEDGER.md").read_bytes() == original_ledger


def test_seed_preserves_user_edits(tmp_path):
    """Second seed call does NOT overwrite a user-edited ledger."""
    from qor.seed import seed
    seed(base=tmp_path, quiet=True)
    ledger = tmp_path / "docs/META_LEDGER.md"
    ledger.write_text("# MY CUSTOM LEDGER\n", encoding="utf-8")
    seed(base=tmp_path, quiet=True)
    assert ledger.read_text(encoding="utf-8") == "# MY CUSTOM LEDGER\n"


def test_seed_gitkeep_files_are_empty(tmp_path):
    from qor.seed import seed
    seed(base=tmp_path, quiet=True)
    for rel in [".agent/staging/.gitkeep", ".qor/gates/.gitkeep", ".qor/session/.gitkeep"]:
        assert (tmp_path / rel).read_text(encoding="utf-8") == ""


def test_seed_gitignore_appends_session_section_once(tmp_path):
    from qor.seed import seed
    seed(base=tmp_path, quiet=True)
    gitignore = tmp_path / ".gitignore"
    first = gitignore.read_text(encoding="utf-8")
    assert "qor:seed" in first
    assert ".qor/session/" in first

    seed(base=tmp_path, quiet=True)
    second = gitignore.read_text(encoding="utf-8")
    assert first == second  # no duplicate section appended


def test_seed_creates_parent_directories(tmp_path):
    """Missing docs/, .agent/staging/, .qor/gates/ etc. are created."""
    from qor.seed import seed
    # tmp_path is empty -- no parents exist yet
    assert not (tmp_path / "docs").exists()
    assert not (tmp_path / ".agent").exists()
    assert not (tmp_path / ".qor").exists()
    seed(base=tmp_path, quiet=True)
    assert (tmp_path / "docs").is_dir()
    assert (tmp_path / ".agent/staging").is_dir()
    assert (tmp_path / ".qor/gates").is_dir()
    assert (tmp_path / ".qor/session").is_dir()


def test_seed_result_namedtuple_shape():
    from qor.seed import SeedResult
    r = SeedResult(created=["a"], skipped=["b"])
    assert r.created == ["a"]
    assert r.skipped == ["b"]
