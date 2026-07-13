"""Phase 174 (GH #274): gate-writing tests must not touch the live gate tree.

Inventory guard: snapshot the live `.qor/gates/` tree, run the historically
offending test files in a real pytest subprocess, and assert the tree is
byte-identical afterwards. Catches the resolver-only-patch regression class
(patching `gate_chain.GATES_DIR` while the writer joins
`validate_gate_artifact.GATES_DIR`) and the doppelganger-import class
(`sys.path.insert` + top-level module imports whose monkeypatches never reach
the canonical modules).

The snapshot excludes first-level dirs matching the conftest session-end
sweep patterns (`test*`, `cli-*`, `t<N>`): the subprocess runs its own
session-end sweep, which may legitimately delete such dirs created earlier
by the outer suite.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GATES_ROOT = REPO_ROOT / ".qor" / "gates"

GATE_WRITING_TEST_FILES = [
    "tests/test_gate_chain_provenance.py",
    "tests/test_qor_ideate_writes_gate_artifact.py",
    "tests/test_skill_active_env.py",
]


def _swept(name: str) -> bool:
    """Mirror tests/conftest.py _cleanup_test_session_pollution patterns."""
    return (
        name.startswith("test")
        or name.startswith("cli-")
        or (len(name) <= 3 and name[0] == "t" and name[1:].isdigit())
    )


def _snapshot(gates_root: Path) -> dict[str, str]:
    """Map every live gate-tree file (outside swept dirs) to its SHA-256."""
    out: dict[str, str] = {}
    if not gates_root.is_dir():
        return out
    for entry in gates_root.iterdir():
        if not entry.is_dir() or _swept(entry.name):
            continue
        for path in sorted(entry.rglob("*")):
            if path.is_file():
                rel = path.relative_to(gates_root).as_posix()
                out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def test_gate_writing_tests_leave_live_tree_untouched():
    before = _snapshot(GATES_ROOT)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *GATE_WRITING_TEST_FILES],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, (
        f"inner pytest run failed:\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}"
    )
    after = _snapshot(GATES_ROOT)
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    modified = sorted(k for k in set(before) & set(after) if before[k] != after[k])
    assert not (added or removed or modified), (
        f"live .qor/gates tree mutated by gate-writing tests: "
        f"added={added} removed={removed} modified={modified}"
    )
