"""Phase 57: swallow-log error semantics + except Exception (not BaseException)."""
from __future__ import annotations

import inspect
import json
from pathlib import Path
from types import SimpleNamespace

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
    yield
    gate_hooks.reload_entry_points()


def test_callable_hook_raising_exception_is_swallowed_and_logged(tmp_path, monkeypatch):
    def bad_hook(event):
        raise ValueError("boom")

    fake_ep = SimpleNamespace(name="bad-hook", load=lambda: bad_hook)
    monkeypatch.setattr(gate_hooks.importlib.metadata, "entry_points",
                        lambda group=None: [fake_ep])

    # No exception should escape
    gate_hooks.dispatch_gate_written(_event(tmp_path))

    log = tmp_path / ".qor" / "hooks" / "hooks.log"
    assert log.exists()
    record = json.loads(log.read_text().strip())
    assert record["status"] == "error"
    assert "ValueError" in record["exception"]
    assert "boom" in record["exception"]


def test_subprocess_hook_with_nonzero_exit_is_logged_with_status_ok(tmp_path, monkeypatch):
    """Subprocess BLOCK is the consumer's responsibility; non-zero exits don't error the dispatch."""
    monkeypatch.setattr(gate_hooks.importlib.metadata, "entry_points",
                        lambda group=None: [])
    yaml_text = 'gate_written:\n  - command: ["python", "-c", "import sys; sys.exit(1)"]\n'
    (tmp_path / ".qor").mkdir()
    (tmp_path / ".qor" / "hooks.yaml").write_text(yaml_text, encoding="utf-8")

    gate_hooks.dispatch_gate_written(_event(tmp_path))

    log = tmp_path / ".qor" / "hooks" / "hooks.log"
    assert log.exists()
    record = json.loads(log.read_text().strip())
    # subprocess.run with check=False does not raise on non-zero; logged as ok
    assert record["status"] == "ok"


def test_swallow_uses_except_exception_not_baseexception():
    """Phase 57 VETO-remediation regression: source must use except Exception in _invoke_hook_safely.

    Anchored to actual Python except clauses (parsing AST), not docstring substring matches.
    """
    import ast
    src = inspect.getsource(gate_hooks._invoke_hook_safely)
    tree = ast.parse(src)
    handlers: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                handlers.append("bare")
            else:
                handlers.append(ast.unparse(node.type))
    assert "Exception" in handlers, f"must catch Exception; got handlers={handlers}"
    assert "BaseException" not in handlers, (
        f"BaseException catch swallows SIGINT/SystemExit; "
        f"Phase 57 VETO ground per Entry #186 audit. Got handlers={handlers}"
    )
