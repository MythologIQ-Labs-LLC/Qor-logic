"""Behavioral tests for qor.scripts.citation_consumer_trace (Phase 126; GH #157).

Synthetic repos in tmp_path exercise import-following deterministically.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts import citation_consumer_trace as cct


def _mk(root: Path, rel: str, body: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def test_symbol_in_entry_file_reachable(tmp_path: Path) -> None:
    entry = _mk(tmp_path, "pkg/entry.py", "def foo():\n    return 1\n")
    res = cct.trace_reachable(tmp_path, entry, "foo")
    assert res.reachable is True and res.skipped is False


def test_symbol_via_transitive_import_reachable(tmp_path: Path) -> None:
    _mk(tmp_path, "pkg/__init__.py", "")
    entry = _mk(tmp_path, "pkg/entry.py", "from pkg.mid import bridge\n")
    _mk(tmp_path, "pkg/mid.py", "from pkg.leaf import target_sym\nbridge = 1\n")
    _mk(tmp_path, "pkg/leaf.py", "def target_sym():\n    return 2\n")
    res = cct.trace_reachable(tmp_path, entry, "target_sym")
    assert res.reachable is True


def test_symbol_in_unimported_file_unreachable(tmp_path: Path) -> None:
    entry = _mk(tmp_path, "pkg/entry.py", "from pkg.mid import bridge\n")
    _mk(tmp_path, "pkg/mid.py", "bridge = 1\n")
    _mk(tmp_path, "pkg/orphan.py", "def target_sym():\n    return 3\n")
    res = cct.trace_reachable(tmp_path, entry, "target_sym")
    assert res.reachable is False and res.skipped is False


def test_missing_entry_file_skips(tmp_path: Path) -> None:
    res = cct.trace_reachable(tmp_path, tmp_path / "nope.py", "whatever")
    assert res.skipped is True and res.reachable is False


def test_resolve_imports_drops_stdlib_and_external(tmp_path: Path) -> None:
    _mk(tmp_path, "qor/scripts/x.py", "y = 1\n")
    base = _mk(tmp_path, "pkg/a.py",
              "import os\nimport json\nfrom qor.scripts.x import y\n")
    resolved = cct.resolve_imports(base.read_text(), base, tmp_path)
    rels = {p.relative_to(tmp_path).as_posix() for p in resolved}
    assert "qor/scripts/x.py" in rels
    assert not any("os" in r or "json" in r for r in rels)


def test_cycle_does_not_hang(tmp_path: Path) -> None:
    a = _mk(tmp_path, "pkg/a.py", "from pkg.b import bb\naa = 1\n")
    _mk(tmp_path, "pkg/b.py", "from pkg.a import aa\nbb = 1\n")
    res = cct.trace_reachable(tmp_path, a, "target_sym")
    assert res.reachable is False  # terminates, no hang


def test_main_exit_1_on_unreachable(tmp_path: Path) -> None:
    entry = _mk(tmp_path, "pkg/entry.py", "x = 1\n")
    _mk(tmp_path, "pkg/orphan.py", "def target_sym(): return 1\n")
    rc = cct.main(["--repo-root", str(tmp_path), "--entry", str(entry),
                   "--symbol", "target_sym"])
    assert rc == 1


def test_main_exit_0_when_reachable(tmp_path: Path) -> None:
    entry = _mk(tmp_path, "pkg/entry.py", "def target_sym(): return 1\n")
    rc = cct.main(["--repo-root", str(tmp_path), "--entry", str(entry),
                   "--symbol", "target_sym"])
    assert rc == 0


def test_main_exit_0_skip_on_missing_entry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = cct.main(["--repo-root", str(tmp_path), "--entry",
                   str(tmp_path / "nope.py"), "--symbol", "x"])
    out = capsys.readouterr().out
    assert rc == 0 and "SKIP" in out.upper()
