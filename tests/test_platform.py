"""Tests for Phase 6 platform detection + capability catalog."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import qor_platform as qplat


# ----- Host detection -----

def test_detect_host_claude_code_env(monkeypatch):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/some/path")
    assert qplat.detect_host() == "claude-code"


def test_detect_host_unknown_absent_env(monkeypatch):
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    assert qplat.detect_host() == "unknown"


# ----- gh CLI detection -----

def test_detect_gh_cli_true_when_auth_ok(monkeypatch):
    def fake_run(cmd, *args, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, "", "")
    monkeypatch.setattr(subprocess, "run", fake_run)
    assert qplat.detect_gh_cli() is True


def test_detect_gh_cli_false_when_not_installed(monkeypatch):
    def fake_run(cmd, *args, **kwargs):
        raise FileNotFoundError("gh: command not found")
    monkeypatch.setattr(subprocess, "run", fake_run)
    assert qplat.detect_gh_cli() is False


def test_detect_gh_cli_false_when_unauthenticated(monkeypatch):
    def fake_run(cmd, *args, **kwargs):
        if cmd[:2] == ["gh", "--version"]:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if cmd[:3] == ["gh", "auth", "status"]:
            return subprocess.CompletedProcess(cmd, 1, "", "not authenticated")
        raise AssertionError(f"Unexpected: {cmd}")
    monkeypatch.setattr(subprocess, "run", fake_run)
    assert qplat.detect_gh_cli() is False


def test_detect_gh_cli_false_on_timeout(monkeypatch):
    def fake_run(cmd, *args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=5)
    monkeypatch.setattr(subprocess, "run", fake_run)
    assert qplat.detect_gh_cli() is False


# ----- Profile I/O -----

def test_list_profiles_returns_five():
    profiles = qplat.list_profiles()
    expected = {"claude-code-solo", "claude-code-with-codex", "claude-code-teams",
                "kilo-code", "codex-standalone"}
    assert set(profiles) == expected


def test_load_profile_claude_code_solo():
    p = qplat.load_profile("claude-code-solo")
    assert p["profile"] == "claude-code-solo"
    assert p["host"] == "claude-code"
    assert p["capabilities"]["codex-plugin"] is False
    assert p["capabilities"]["agent-teams"] is False


def test_load_profile_with_codex_sets_capability_true():
    p = qplat.load_profile("claude-code-with-codex")
    assert p["capabilities"]["codex-plugin"] is True


def test_load_profile_unknown_raises():
    with pytest.raises(ValueError, match="Unknown profile"):
        qplat.load_profile("definitely-not-a-profile")


# ----- Marker state -----

def test_apply_profile_writes_marker(tmp_path, monkeypatch):
    marker = tmp_path / "platform.json"
    state = qplat.apply_profile("claude-code-solo", marker=marker)
    assert marker.exists()
    on_disk = json.loads(marker.read_text(encoding="utf-8"))
    assert on_disk == state
    assert state["profile_applied"] == "claude-code-solo"
    assert state["declared"]["codex-plugin"] is False


def test_current_roundtrip(tmp_path):
    marker = tmp_path / "platform.json"
    applied = qplat.apply_profile("claude-code-with-codex", marker=marker)
    loaded = qplat.current(marker=marker)
    assert loaded == applied


def test_current_returns_none_when_absent(tmp_path):
    marker = tmp_path / "no-file.json"
    assert qplat.current(marker=marker) is None


def test_set_capability_merges(tmp_path):
    marker = tmp_path / "platform.json"
    qplat.apply_profile("claude-code-solo", marker=marker)
    qplat.set_capability("codex-plugin", True, marker=marker)
    state = qplat.current(marker=marker)
    assert state["declared"]["codex-plugin"] is True
    # Other declared fields preserved
    assert state["declared"]["agent-teams"] is False


def test_set_capability_without_prior_marker(tmp_path):
    marker = tmp_path / "platform.json"
    qplat.set_capability("codex-plugin", True, marker=marker)
    state = qplat.current(marker=marker)
    assert state["declared"]["codex-plugin"] is True
    assert state["profile_applied"] is None


def test_clear_removes_marker(tmp_path):
    marker = tmp_path / "platform.json"
    qplat.apply_profile("claude-code-solo", marker=marker)
    qplat.clear(marker=marker)
    assert not marker.exists()


def test_clear_no_op_when_absent(tmp_path):
    marker = tmp_path / "nonexistent.json"
    qplat.clear(marker=marker)  # should not raise


# ----- is_available -----

def test_is_available_true_after_profile_sets_true(tmp_path):
    marker = tmp_path / "platform.json"
    qplat.apply_profile("claude-code-with-codex", marker=marker)
    assert qplat.is_available("codex-plugin", marker=marker) is True


def test_is_available_false_after_profile_sets_false(tmp_path):
    marker = tmp_path / "platform.json"
    qplat.apply_profile("claude-code-solo", marker=marker)
    assert qplat.is_available("codex-plugin", marker=marker) is False


def test_is_available_false_when_no_marker(tmp_path):
    marker = tmp_path / "nope.json"
    assert qplat.is_available("codex-plugin", marker=marker) is False


def test_is_available_false_for_unknown_capability(tmp_path):
    marker = tmp_path / "platform.json"
    qplat.apply_profile("claude-code-solo", marker=marker)
    assert qplat.is_available("mystery-capability", marker=marker) is False


def test_is_available_detected_host_wins(tmp_path):
    marker = tmp_path / "platform.json"
    qplat.apply_profile("claude-code-solo", marker=marker)
    # host is in detected; is_available returns truthy for non-empty string
    assert qplat.is_available("host", marker=marker) is True


def test_is_available_mcp_servers_list_nonempty(tmp_path):
    marker = tmp_path / "platform.json"
    qplat.apply_profile("claude-code-solo", marker=marker)
    qplat.set_capability("mcp-servers", ["linear", "github"], marker=marker)
    assert qplat.is_available("mcp-servers", marker=marker) is True


def test_is_available_mcp_servers_list_empty(tmp_path):
    marker = tmp_path / "platform.json"
    qplat.apply_profile("claude-code-solo", marker=marker)
    # mcp-servers defaults to []
    assert qplat.is_available("mcp-servers", marker=marker) is False
