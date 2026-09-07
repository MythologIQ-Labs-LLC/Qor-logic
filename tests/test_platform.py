"""Tests for Phase 6 platform detection + capability catalog."""
from __future__ import annotations

import json
import os
import subprocess

import pytest

from qor.scripts import qor_platform as qplat


# ----- Host detection -----

def _clear_claude_signals(monkeypatch):
    """Remove every claude-code host signal from the environment."""
    monkeypatch.delenv("CLAUDECODE", raising=False)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    for key in [k for k in os.environ if k.startswith("CLAUDE_CODE_")]:
        monkeypatch.delenv(key, raising=False)


def test_detect_host_claude_code_env(monkeypatch):
    _clear_claude_signals(monkeypatch)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/some/path")
    assert qplat.detect_host() == "claude-code"


def test_detect_host_claudecode_env_alone(monkeypatch):
    """Phase 186 (GH #242): CLAUDECODE=1 is the ambient CLI signal."""
    _clear_claude_signals(monkeypatch)
    monkeypatch.setenv("CLAUDECODE", "1")
    assert qplat.detect_host() == "claude-code"


def test_detect_host_claude_code_family_env_alone(monkeypatch):
    """Phase 186 (GH #242): any CLAUDE_CODE_* key identifies the host."""
    _clear_claude_signals(monkeypatch)
    monkeypatch.setenv("CLAUDE_CODE_ENTRYPOINT", "cli")
    assert qplat.detect_host() == "claude-code"


def test_detect_host_unknown_absent_env(monkeypatch):
    _clear_claude_signals(monkeypatch)
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


# ----- Phase 269 (GH #429): absent is not the same as unreadable -----

def _declared(marker):
    return json.loads(marker.read_text(encoding="utf-8"))["declared"]


def test_current_returns_none_on_a_corrupt_marker(tmp_path):
    """A truncated write is the motivating shape in GH #429."""
    marker = tmp_path / "platform.json"
    marker.write_text('{"declared": {"gh_cli": true', encoding="utf-8")
    assert qplat.current(marker=marker) is None


def test_current_returns_none_on_utf16_bytes(tmp_path):
    """PowerShell Out-File writes UTF-16LE; the decode fails before json does."""
    marker = tmp_path / "platform.json"
    marker.write_bytes(json.dumps({"declared": {}}).encode("utf-16"))
    assert qplat.current(marker=marker) is None


def test_current_returns_none_on_non_dict_json(tmp_path):
    """Valid JSON that is not an object reaches no exception handler at all."""
    for body in ("[]", "123", '"text"'):
        marker = tmp_path / "platform.json"
        marker.write_text(body, encoding="utf-8")
        assert qplat.current(marker=marker) is None, body


def test_current_returns_none_on_a_permission_error(tmp_path, monkeypatch):
    """current() is total by contract: every caller sits in a gate-writing or
    capability-gating path where a raise means no artifact can be written.

    The three-way classification is not lost, it is available to callers that
    can act on it via _read_marker; see the test below.

    Monkeypatches the read rather than using chmod: on Windows os.chmod(path, 0)
    does not make a file unreadable to its owner, so a real-permissions fixture
    would exercise nothing on this workspace.
    """
    marker = tmp_path / "platform.json"
    marker.write_text("{}", encoding="utf-8")

    def _denied(self, *a, **kw):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(type(marker), "read_text", _denied)
    assert qplat.current(marker=marker) is None


def test_set_capability_refuses_to_overwrite_an_unreadable_marker(tmp_path):
    """The data-loss defect: `current() or {defaults}` then write.

    detect.md:30 and capabilities.md:85 both state that user declarations are
    never overwritten, so synthesising defaults over an unreadable marker
    contradicts a shipped contract.
    """
    marker = tmp_path / "platform.json"
    qplat.apply_profile("claude-code-solo", marker=marker)
    before = marker.read_bytes()
    marker.write_text('{"declared": {"gh_cli": true, "docker"', encoding="utf-8")

    with pytest.raises(qplat.PlatformMarkerError):
        qplat.set_capability("codex-plugin", True, marker=marker)

    # The corrupt bytes are still there: nothing was written over them.
    assert marker.read_text(encoding="utf-8") == '{"declared": {"gh_cli": true, "docker"'
    assert before  # the fixture really did have prior state


def test_platform_marker_error_is_not_an_oserror_or_valueerror():
    """Base class is load-bearing.

    An OSError subclass would collide with the reader's "any other OSError
    propagates" contract; a ValueError subclass becomes catchable by the
    _parse_bool guard in the CLI `set` handler on any reorder.
    """
    assert issubclass(qplat.PlatformMarkerError, Exception)
    assert not issubclass(qplat.PlatformMarkerError, OSError)
    assert not issubclass(qplat.PlatformMarkerError, ValueError)


def test_set_capability_still_creates_a_marker_when_absent(tmp_path):
    """Refusing on unreadable must not break first run."""
    marker = tmp_path / "platform.json"
    qplat.set_capability("codex-plugin", True, marker=marker)
    assert _declared(marker)["codex-plugin"] is True


def test_is_available_is_false_on_a_corrupt_marker(tmp_path):
    marker = tmp_path / "platform.json"
    marker.write_text("[]", encoding="utf-8")
    assert qplat.is_available("codex-plugin", marker=marker) is False


def test_cli_get_distinguishes_absent_from_unreadable(tmp_path, monkeypatch, capsys):
    """'(no platform marker)' is actively false for a file sitting on disk."""
    marker = tmp_path / "platform.json"
    monkeypatch.setattr(qplat, "MARKER_PATH", marker)

    monkeypatch.setattr("sys.argv", ["qor_platform.py", "get"])
    assert qplat.main() == 1
    assert "no platform marker" in capsys.readouterr().out

    marker.write_text("{oops", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["qor_platform.py", "get"])
    rc = qplat.main()
    out = capsys.readouterr()
    assert rc != 0
    assert "no platform marker" not in (out.out + out.err)
    assert "cannot be read" in (out.out + out.err)


def test_cli_check_distinguishes_unavailable_from_unreadable(tmp_path, monkeypatch, capsys):
    """A script branching on the exit code must be able to tell them apart."""
    marker = tmp_path / "platform.json"
    monkeypatch.setattr(qplat, "MARKER_PATH", marker)

    qplat.apply_profile("claude-code-solo", marker=marker)
    monkeypatch.setattr("sys.argv", ["qor_platform.py", "check", "codex-plugin"])
    assert qplat.main() == 1  # genuinely not available

    marker.write_text("{oops", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["qor_platform.py", "check", "codex-plugin"])
    assert qplat.main() == 2  # cannot tell
    assert "cannot be read" in "".join(capsys.readouterr())


def test_cli_set_reports_an_unreadable_marker_without_a_traceback(tmp_path, monkeypatch, capsys):
    """set_capability sits outside the _parse_bool try, so the error escapes main()."""
    marker = tmp_path / "platform.json"
    monkeypatch.setattr(qplat, "MARKER_PATH", marker)
    marker.write_text("{oops", encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["qor_platform.py", "set", "codex-plugin", "true"])
    rc = qplat.main()  # must not raise
    assert rc == 2
    assert "cannot be read" in capsys.readouterr().err


def test_current_returns_none_on_pathologically_nested_json(tmp_path):
    """Fourth instance of the enumerated-handler class, found by applying the
    enumerate-the-exits method to the third reader in this change.

    json.loads is recursive, so depth alone raises RecursionError, which
    `except json.JSONDecodeError` does not catch. Content that cannot be parsed
    is 'the bytes are not our state' whatever the reason, so it degrades.
    """
    marker = tmp_path / "platform.json"
    marker.write_bytes(b'{"a":' * 5000 + b"1" + b"}" * 5000)
    assert qplat.current(marker=marker) is None


def test_read_marker_still_propagates_permission_errors(tmp_path, monkeypatch):
    """Widening the PARSE handler must not swallow the READ classification.

    Asserted at _read_marker, where the three-way split lives. current() is
    deliberately total and must NOT surface this; the surfaces that can act on
    it -- set_capability, CLI get, CLI check -- call _read_marker directly.
    """
    marker = tmp_path / "platform.json"
    marker.write_text("{}", encoding="utf-8")

    def _denied(self, *a, **kw):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(type(marker), "read_text", _denied)
    with pytest.raises(PermissionError):
        qplat._read_marker(marker)


def test_diagnosis_surfaces_still_see_a_permission_error(tmp_path, monkeypatch):
    """Loudness stays where an operator can act on it."""
    marker = tmp_path / "platform.json"
    marker.write_text("{}", encoding="utf-8")

    def _denied(self, *a, **kw):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(type(marker), "read_text", _denied)
    with pytest.raises(PermissionError):
        qplat.set_capability("codex-plugin", True, marker=marker)
