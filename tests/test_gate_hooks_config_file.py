"""Phase 57: .qor/hooks.yaml parse + dotted-path + subprocess-argv resolution."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qor.scripts import gate_hooks


def _event(tmp_path: Path) -> gate_hooks.GateWrittenEvent:
    artifact = tmp_path / "art.json"
    artifact.write_text("{}", encoding="utf-8")
    return gate_hooks.GateWrittenEvent(
        phase="plan", session_id="test-sid",
        artifact_path=artifact, payload_sha256="a" * 64,
        ts="2026-05-01T20:00:00Z",
    )


@pytest.fixture(autouse=True)
def _reset_cache(monkeypatch, tmp_path):
    gate_hooks.reload_entry_points()
    monkeypatch.setattr(gate_hooks._workdir, "root", lambda: tmp_path)
    monkeypatch.setattr(gate_hooks.importlib.metadata, "entry_points",
                        lambda group=None: [])
    yield
    gate_hooks.reload_entry_points()


def test_loads_dotted_path_hook_from_yaml(tmp_path, monkeypatch):
    invocations: list = []

    def my_hook(event):
        invocations.append(event)

    monkeypatch.setattr(gate_hooks, "_import_dotted", lambda d: my_hook)

    yaml_text = "gate_written:\n  - module: my_pkg.hooks:on_event\n"
    (tmp_path / ".qor").mkdir()
    (tmp_path / ".qor" / "hooks.yaml").write_text(yaml_text, encoding="utf-8")

    gate_hooks.dispatch_gate_written(_event(tmp_path))
    assert len(invocations) == 1


def test_loads_command_hook_from_yaml_with_list_argv(tmp_path, monkeypatch):
    seen_argv: list = []

    class FakeResult:
        returncode = 0

    def fake_run(argv, **kwargs):
        seen_argv.append(list(argv))
        return FakeResult()

    monkeypatch.setattr(gate_hooks.subprocess, "run", fake_run)

    yaml_text = 'gate_written:\n  - command: ["echo", "hello"]\n'
    (tmp_path / ".qor").mkdir()
    (tmp_path / ".qor" / "hooks.yaml").write_text(yaml_text, encoding="utf-8")

    event = _event(tmp_path)
    gate_hooks.dispatch_gate_written(event)
    assert len(seen_argv) == 1
    assert seen_argv[0] == ["echo", "hello", str(event.artifact_path)]


def test_rejects_command_with_string_argv(tmp_path):
    """A03 Injection: string-form command must be silently dropped (no shell=True attack surface)."""
    yaml_text = 'gate_written:\n  - command: "echo hello"\n'
    (tmp_path / ".qor").mkdir()
    (tmp_path / ".qor" / "hooks.yaml").write_text(yaml_text, encoding="utf-8")

    targets = gate_hooks._load_config_file_hooks(tmp_path)
    assert targets == []


def test_rejects_unknown_entry_shape(tmp_path):
    yaml_text = 'gate_written:\n  - not_a_known_key: "x"\n'
    (tmp_path / ".qor").mkdir()
    (tmp_path / ".qor" / "hooks.yaml").write_text(yaml_text, encoding="utf-8")

    targets = gate_hooks._load_config_file_hooks(tmp_path)
    assert targets == []


def test_subprocess_hook_argv_only_appends_artifact_path(tmp_path, monkeypatch):
    """Open Question 3 default: payload_sha256 and phase are NOT appended."""
    seen_argv: list = []

    class FakeResult:
        returncode = 0

    def fake_run(argv, **kwargs):
        seen_argv.append(list(argv))
        return FakeResult()

    monkeypatch.setattr(gate_hooks.subprocess, "run", fake_run)

    yaml_text = 'gate_written:\n  - command: ["my-hook"]\n'
    (tmp_path / ".qor").mkdir()
    (tmp_path / ".qor" / "hooks.yaml").write_text(yaml_text, encoding="utf-8")

    event = _event(tmp_path)
    gate_hooks.dispatch_gate_written(event)
    # Only artifact_path appended; phase/sha256 are NOT in argv
    assert seen_argv[0] == ["my-hook", str(event.artifact_path)]
    assert event.phase not in seen_argv[0][1:]
    assert event.payload_sha256 not in seen_argv[0]


def test_yaml_parse_error_returns_empty_list(tmp_path):
    yaml_text = "gate_written:\n  - command: [unbalanced\n"
    (tmp_path / ".qor").mkdir()
    (tmp_path / ".qor" / "hooks.yaml").write_text(yaml_text, encoding="utf-8")

    targets = gate_hooks._load_config_file_hooks(tmp_path)
    assert targets == []
