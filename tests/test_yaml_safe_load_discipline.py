"""Phase 24: codebase-wide ban on unsafe YAML loaders."""
from __future__ import annotations

import re
from pathlib import Path


_UNSAFE_API = re.compile(r"yaml\.(load|load_all|full_load|unsafe_load)\s*\(")


def test_no_unsafe_yaml_apis_in_qor():
    root = Path(__file__).resolve().parent.parent / "qor"
    violations: list[str] = []
    for py_path in root.rglob("*.py"):
        # Skip vendored third-party skill scripts
        if "vendor" in py_path.parts:
            continue
        text = py_path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _UNSAFE_API.search(line):
                violations.append(f"{py_path}:{lineno}: {line.strip()}")
    assert not violations, (
        "Unsafe YAML API usage detected (use yaml.safe_load only):\n  "
        + "\n  ".join(violations)
    )
