"""Behavior contract for Phase 33 create_seal_tag timing fix.

After Phase 33, create_seal_tag takes a required `commit` parameter so the
tag is placed on the seal commit (made at /qor-substantiate Step 9.5),
not the pre-seal HEAD at Step 7.5.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "qor" / "scripts"))
import governance_helpers as gh


def _capture_argv(monkeypatch):
    captured: dict = {}

    def _fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs

        class R:
            returncode = 0

        return R()

    monkeypatch.setattr(gh.subprocess, "run", _fake_run)
    return captured


def test_create_seal_tag_targets_explicit_commit(monkeypatch):
    captured = _capture_argv(monkeypatch)
    sha = "1234567890abcdef1234567890abcdef12345678"
    gh.create_seal_tag(
        "0.24.0", "deadbeef", 109, 33, "feature", commit=sha,
    )
    argv = captured["argv"]
    assert argv[:3] == ["git", "tag", "-a"]
    assert argv[3] == "v0.24.0"
    assert argv[4] == sha, f"expected SHA as positional arg after tag, got {argv}"
    assert "-m" in argv


def test_create_seal_tag_raises_without_commit():
    with pytest.raises(TypeError):
        gh.create_seal_tag("0.24.0", "seal", 1, 33, "feature")  # type: ignore[call-arg]


def test_create_seal_tag_message_unchanged(monkeypatch):
    captured = _capture_argv(monkeypatch)
    gh.create_seal_tag(
        "0.24.0", "abc123", 109, 33, "feature", commit="deadbeefcafef00d",
    )
    argv = captured["argv"]
    m_idx = argv.index("-m")
    message = argv[m_idx + 1]
    assert "Merkle seal: abc123" in message
    assert "Ledger entry: #109" in message
    assert "Phase: 33" in message
    assert "Class: feature" in message
