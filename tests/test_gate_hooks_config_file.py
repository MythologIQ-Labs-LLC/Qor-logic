"""Config-file dispatch: .qor/hooks.yaml maps event -> [{module|command}].

Python dotted-path entries are imported and called. Shell entries are
run via subprocess with artifact path appended to argv. Both write
an entry to .qor/hooks/hooks.log on success (failure covered by
test_gate_hooks_swallow.py).
"""
from __future__ import annotations

import importlib.metadata
import json
import sys
from pathlib import Path

from qor.scripts import gate_hooks


def _make_event(tmp_path: Path) -> gate_hooks.GateWrittenEvent:
    artifact = tmp_path / ".qor" / "gates" / "s1" / "plan.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("{}", encoding="utf-8")
    return gate_hooks.GateWrittenEvent(
        phase="plan",
        session_id="s1",
        artifact_path=artifact,
        payload_sha256="beefdead",
        ts="2026-04-20T00:00:00Z",
    )


_config_hook_calls: list[gate_hooks.GateWrittenEvent] = []


def _config_hook(event):
    """Dotted-path target loaded via the config-file hook."""
    _config_hook_calls.append(event)


def test_dotted_path_hook_invoked(monkeypatch, tmp_path):
    _config_hook_calls.clear()
    monkeypatch.setattr(
        importlib.metadata, "entry_points", lambda group=None: [],
    )
    gate_hooks.reload_entry_points()
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))
    dotted = f"{__name__}:_config_hook"
    hooks_yaml = tmp_path / ".qor" / "hooks.yaml"
    hooks_yaml.parent.mkdir(parents=True, exist_ok=True)
    hooks_yaml.write_text(
        f"gate_written:\n  - module: {dotted}\n",
        encoding="utf-8",
    )

    event = _make_event(tmp_path)
    gate_hooks.dispatch_gate_written(event)

    assert len(_config_hook_calls) == 1
    log_path = tmp_path / ".qor" / "hooks" / "hooks.log"
    assert log_path.exists()
    entries = [json.loads(line) for line in log_path.read_text().splitlines() if line]
    assert entries[-1]["status"] == "ok"
    assert entries[-1]["event"]["phase"] == "plan"


def test_shell_command_hook_invoked(monkeypatch, tmp_path):
    monkeypatch.setattr(
        importlib.metadata, "entry_points", lambda group=None: [],
    )
    gate_hooks.reload_entry_points()
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))

    marker = tmp_path / "shell_hook_ran.txt"
    script = tmp_path / "hook.py"
    script.write_text(
        "import sys, pathlib\n"
        f"pathlib.Path({str(marker)!r}).write_text(sys.argv[1])\n",
        encoding="utf-8",
    )
    hooks_yaml = tmp_path / ".qor" / "hooks.yaml"
    hooks_yaml.parent.mkdir(parents=True, exist_ok=True)
    hooks_yaml.write_text(
        "gate_written:\n"
        f"  - command: [{sys.executable!r}, {str(script)!r}]\n",
        encoding="utf-8",
    )

    event = _make_event(tmp_path)
    gate_hooks.dispatch_gate_written(event)

    assert marker.exists()
    assert str(event.artifact_path) in marker.read_text()
