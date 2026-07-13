"""Phase 96: reachability probe behavior tests (GH #108 V1).

Each test exercises one of the five checks (importability, test collection,
caller graph, packaging, interface match) in pass and fail directions, plus
CLI exit-code behavior. The dogfooding anchor builds a synthetic broken
repo and asserts the probe emits findings across all five categories.
"""
from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from qor.scripts.reachability_probe import (
    Claim,
    ReachabilityFinding,
    check_caller_graph,
    check_claim,
    check_importability,
    check_interface_match,
    check_packaging,
    check_test_collection,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


# --- importability ---------------------------------------------------------

def test_check_importability_passes_for_real_qor_symbol():
    claim = Claim(
        module="qor.scripts.skill_size_budget_lint",
        symbol="check_skills",
        file_path="qor/scripts/skill_size_budget_lint.py",
    )
    finding = check_importability(claim, REPO_ROOT)
    assert finding is None, f"expected no finding; got {finding}"


def test_check_importability_fails_for_unreachable_symbol(tmp_path):
    pkg = tmp_path / "broken_pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("def )(syntax error here", encoding="utf-8")
    claim = Claim(
        module="broken_pkg",
        symbol=None,
        file_path="broken_pkg/__init__.py",
    )
    finding = check_importability(claim, tmp_path)
    assert finding is not None
    assert finding.category == "reachability-importability-failed"


# --- test collection -------------------------------------------------------

def test_check_test_collection_passes_when_test_exists(tmp_path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_dummy.py").write_text(
        textwrap.dedent(
            """
            def test_smoke():
                assert True
            # references mymod for the heuristic match
            """
        ).strip(),
        encoding="utf-8",
    )
    claim = Claim(module="mymod", symbol=None, file_path="mymod.py")
    finding = check_test_collection(claim, tmp_path)
    assert finding is None, f"expected no finding; got {finding}"


def test_check_test_collection_fails_when_no_test_exercises_surface(tmp_path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_other.py").write_text("def test_other(): pass", encoding="utf-8")
    claim = Claim(
        module="unreferenced_module_xyz",
        symbol="never_used_symbol_xyz",
        file_path="unreferenced_module_xyz.py",
    )
    finding = check_test_collection(claim, tmp_path)
    assert finding is not None
    assert finding.category == "reachability-test-collection-failed"


# --- caller graph ----------------------------------------------------------

def test_check_caller_graph_finds_production_importer(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "consumer.py").write_text(
        "from mylib import compute\nx = compute(1)\n", encoding="utf-8"
    )
    (tmp_path / "mylib.py").write_text("def compute(x): return x\n", encoding="utf-8")
    claim = Claim(module="mylib", symbol="compute", file_path="mylib.py")
    finding = check_caller_graph(claim, tmp_path)
    assert finding is None, f"expected production caller match; got {finding}"


def test_check_caller_graph_flags_test_only_caller(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_uses_it.py").write_text(
        "from mylib import compute\n", encoding="utf-8"
    )
    (tmp_path / "mylib.py").write_text("def compute(x): return x\n", encoding="utf-8")
    claim = Claim(module="mylib", symbol="compute", file_path="mylib.py")
    finding = check_caller_graph(claim, tmp_path)
    assert finding is not None
    assert finding.category == "reachability-no-production-caller"


# --- packaging -------------------------------------------------------------

def test_check_packaging_passes_when_path_in_manifest(tmp_path):
    manifest = tmp_path / "pyproject.toml"
    manifest.write_text(
        '[tool.setuptools.packages.find]\ninclude = ["mylib*"]\n', encoding="utf-8"
    )
    claim = Claim(module="mylib", symbol=None, file_path="mylib/__init__.py")
    finding = check_packaging(claim, tmp_path)
    assert finding is None, f"expected manifest match; got {finding}"


def test_check_packaging_flags_missing_manifest_entry(tmp_path):
    manifest = tmp_path / "pyproject.toml"
    manifest.write_text("[project]\nname = 'other'\n", encoding="utf-8")
    claim = Claim(module="mylib", symbol=None, file_path="mylib/__init__.py")
    finding = check_packaging(claim, tmp_path)
    assert finding is not None
    assert finding.category == "reachability-packaging-missing"


# --- interface match -------------------------------------------------------

def test_check_interface_match_passes_when_signature_agrees(tmp_path):
    (tmp_path / "mylib.py").write_text("def foo(a, b): return a + b\n", encoding="utf-8")
    (tmp_path / "caller.py").write_text("result = foo(1, 2)\n", encoding="utf-8")
    claim = Claim(
        module="mylib",
        symbol="foo",
        file_path="mylib.py",
        call_site="caller.py:1",
    )
    finding = check_interface_match(claim, tmp_path)
    assert finding is None, f"expected signature agreement; got {finding}"


def test_check_interface_match_flags_signature_drift(tmp_path):
    (tmp_path / "mylib.py").write_text("def foo(a, b): return a + b\n", encoding="utf-8")
    (tmp_path / "caller.py").write_text("result = foo(1, 2, 3)\n", encoding="utf-8")
    claim = Claim(
        module="mylib",
        symbol="foo",
        file_path="mylib.py",
        call_site="caller.py:1",
    )
    finding = check_interface_match(claim, tmp_path)
    assert finding is not None
    assert finding.category == "reachability-interface-mismatch"


# --- CLI exit codes --------------------------------------------------------

def _write_claims(path: Path, claims: list[dict]) -> None:
    path.write_text(json.dumps(claims), encoding="utf-8")


def _clean_synthetic_repo(repo: Path) -> Path:
    """Repo where the claim is fully reachable across all five checks."""
    (repo / "src").mkdir()
    (repo / "mylib.py").write_text("def foo(a, b): return a + b\n", encoding="utf-8")
    (repo / "src" / "consumer.py").write_text(
        "from mylib import foo\nx = foo(1, 2)\n", encoding="utf-8"
    )
    (repo / "tests").mkdir()
    (repo / "tests" / "test_mylib.py").write_text(
        "from mylib import foo\ndef test_foo(): assert foo(1, 2) == 3\n",
        encoding="utf-8",
    )
    (repo / "pyproject.toml").write_text(
        '[tool.setuptools.packages.find]\ninclude = ["mylib*"]\n',
        encoding="utf-8",
    )
    return repo


def test_main_cli_exits_zero_on_no_findings(tmp_path):
    repo = _clean_synthetic_repo(tmp_path)
    claims_path = repo / "claims.json"
    _write_claims(
        claims_path,
        [
            {
                "module": "mylib",
                "symbol": "foo",
                "file_path": "mylib.py",
                "call_site": "src/consumer.py:2",
            }
        ],
    )
    result = subprocess.run(
        [
            sys.executable, "-m", "qor.scripts.reachability_probe",
            "--claims", str(claims_path),
            "--repo-root", str(repo),
        ],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, f"stdout={result.stdout} stderr={result.stderr}"


def test_main_cli_exits_zero_with_findings_by_default(tmp_path):
    claims_path = tmp_path / "claims.json"
    _write_claims(
        claims_path,
        [{"module": "totally_unreachable_module_xyz", "file_path": "noop.py"}],
    )
    result = subprocess.run(
        [
            sys.executable, "-m", "qor.scripts.reachability_probe",
            "--claims", str(claims_path),
            "--repo-root", str(tmp_path),
        ],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, f"V1 is WARN-only by default; stdout={result.stdout}"
    assert "finding" in result.stdout.lower()


def test_main_cli_exits_one_with_findings_when_exit_on_any_set(tmp_path):
    claims_path = tmp_path / "claims.json"
    _write_claims(
        claims_path,
        [{"module": "totally_unreachable_module_xyz", "file_path": "noop.py"}],
    )
    result = subprocess.run(
        [
            sys.executable, "-m", "qor.scripts.reachability_probe",
            "--claims", str(claims_path),
            "--repo-root", str(tmp_path),
            "--exit-on-any",
        ],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 1
    assert "finding" in result.stdout.lower()


# --- dogfooding self-application anchor ------------------------------------

def test_probe_self_application_on_broken_fixture_emits_all_five(tmp_path):
    """The V1 probe MUST catch a zombie-code claim across all five checks.

    The dogfooding shipping-correctness anchor for Phase 96. Constructs a
    synthetic claim that fails every one of the five reachability checks
    and asserts the probe emits a finding in each category.
    """
    # 1. importability fails: module has syntax error
    pkg = tmp_path / "broken_pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("def )(syntax error", encoding="utf-8")
    # 2. test collection fails: no test references it
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_unrelated.py").write_text(
        "def test_other(): pass", encoding="utf-8"
    )
    # 3. caller graph fails: no production caller
    # (nothing imports broken_pkg)
    # 4. packaging fails: no manifest
    # (no pyproject.toml created)
    # 5. interface match fails: claim cites a symbol that won't be parseable
    claim = Claim(
        module="broken_pkg",
        symbol="missing_symbol",
        file_path="broken_pkg/__init__.py",
        call_site="caller_does_not_exist.py:1",
    )
    findings = check_claim(claim, tmp_path)
    categories = {f.category for f in findings}
    expected = {
        "reachability-importability-failed",
        "reachability-test-collection-failed",
        "reachability-no-production-caller",
        "reachability-packaging-missing",
        "reachability-interface-mismatch",
    }
    missing = expected - categories
    assert not missing, (
        f"V1 dogfooding shipping-correctness anchor failed: "
        f"expected all five categories; missing {missing}. "
        f"Got categories: {categories}"
    )


# ----- Phase 184 (GH #264): load-tolerant collection timeout -----

def test_collection_subprocess_uses_module_timeout(tmp_path, monkeypatch):
    """The collect-only subprocess must use the module constant (default 120s,
    reporter-validated under full-suite load) -- not a hardcoded 30."""
    import subprocess as _subprocess
    from qor.scripts import reachability_probe as rp

    recorded = {}

    def recorder(*args, **kwargs):
        recorded.update(kwargs)
        class R:  # minimal CompletedProcess stand-in
            returncode = 0
        return R()

    monkeypatch.setattr(_subprocess, "run", recorder)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text(
        "import qor.scripts.reachability_probe\n", encoding="utf-8")
    claim = rp.Claim(module="qor.scripts.reachability_probe", symbol=None,
                     file_path="qor/scripts/reachability_probe.py")
    rp.check_test_collection(claim, tmp_path)
    assert recorded.get("timeout") == rp.COLLECTION_TIMEOUT
    assert rp.COLLECTION_TIMEOUT == 120


def test_collection_timeout_env_override(monkeypatch):
    import importlib
    from qor.scripts import reachability_probe as rp

    monkeypatch.setenv("QOR_REACHABILITY_COLLECTION_TIMEOUT", "45")
    try:
        importlib.reload(rp)
        assert rp.COLLECTION_TIMEOUT == 45
    finally:
        monkeypatch.delenv("QOR_REACHABILITY_COLLECTION_TIMEOUT", raising=False)
        importlib.reload(rp)
        assert rp.COLLECTION_TIMEOUT == 120
