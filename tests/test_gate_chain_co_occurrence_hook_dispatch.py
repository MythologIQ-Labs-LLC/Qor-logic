"""Phase 57 + Phase 50 co-occurrence behavior invariant: write_gate_artifact MUST call _fire_gate_written_hook.

AST-based check (not substring grep) that verifies call ordering inside the function.
"""
from __future__ import annotations

import ast
import inspect

from qor.scripts import gate_chain


def test_write_gate_artifact_function_body_calls_fire_hook():
    """Conditional rule: every successful path through `write_gate_artifact`
    MUST call `_fire_gate_written_hook` AFTER `vga.write_artifact(...)` AND
    BEFORE the function returns.
    """
    src = inspect.getsource(gate_chain.write_gate_artifact)
    tree = ast.parse(src)
    func_def = tree.body[0]
    assert isinstance(func_def, ast.FunctionDef)

    # Walk the body, tracking the order of relevant calls
    order: list[str] = []
    for node in ast.walk(func_def):
        if isinstance(node, ast.Call):
            target = ast.unparse(node.func)
            if "write_artifact" in target and "vga" in target:
                order.append("write_artifact")
            elif target == "_fire_gate_written_hook":
                order.append("fire_hook")

    assert "write_artifact" in order, "write_gate_artifact must call vga.write_artifact"
    assert "fire_hook" in order, (
        "write_gate_artifact MUST call _fire_gate_written_hook (Phase 57 invariant)"
    )
    # write_artifact must come before fire_hook (write before fire)
    assert order.index("write_artifact") < order.index("fire_hook"), (
        "_fire_gate_written_hook must be called AFTER vga.write_artifact"
    )
