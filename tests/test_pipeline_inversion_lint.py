"""Phase 49 pipeline_inversion_lint behavior tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts.pipeline_inversion_lint import (
    scan,
    scan_source,
    scan_repo,
    main,
    PipelineFinding,
)


def _write(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


def test_scan_returns_empty_for_simple_file_with_no_pipelines(tmp_path):
    src = "def foo(x):\n    return x + 1\n"
    p = _write(tmp_path, "x.py", src)
    assert scan(p) == []


def test_scan_returns_empty_when_no_validator_in_module(tmp_path):
    src = (
        "def pipeline(items):\n"
        "    a = (i for i in items if i.tier == 'A')\n"
        "    b = (i for i in a if i.classification == 'X')\n"
        "    return list(b)\n"
    )
    p = _write(tmp_path, "x.py", src)
    assert scan(p) == []


def test_scan_detects_filter_chain_referencing_validator_field(tmp_path):
    src = (
        "def validate_manifest(m):\n"
        "    if not m.tier:\n"
        "        return False\n"
        "    return True\n"
        "\n"
        "def decide(items):\n"
        "    a = filter(lambda i: i.tier == 'A', items)\n"
        "    b = filter(lambda i: i.cost < 100, a)\n"
        "    c = filter(lambda i: i.vendor == 'V', b)\n"
        "    return min(c, key=lambda i: i.cost)\n"
    )
    p = _write(tmp_path, "x.py", src)
    findings = scan(p)
    assert len(findings) == 1
    assert findings[0].function == "decide"
    assert "tier" in findings[0].shared_fields
    assert findings[0].validator_function == "validate_manifest"


def test_scan_detects_sequential_if_continue_pipeline(tmp_path):
    src = (
        "def check_skill(s):\n"
        "    return s.tier in ('A', 'B')\n"
        "\n"
        "def decide(items):\n"
        "    for item in items:\n"
        "        if item.tier == 'C':\n"
        "            continue\n"
        "        if item.classification != 'core':\n"
        "            continue\n"
        "        return item\n"
        "    return None\n"
    )
    p = _write(tmp_path, "x.py", src)
    findings = scan(p)
    assert len(findings) == 1
    assert findings[0].function == "decide"


def test_scan_no_finding_when_validator_runs_first(tmp_path):
    src = (
        "def validate_manifest(m):\n"
        "    return bool(m.tier)\n"
        "\n"
        "def decide(items):\n"
        "    items = [i for i in items if validate_manifest(i)]\n"
        "    a = filter(lambda i: i.tier == 'A', items)\n"
        "    b = filter(lambda i: i.cost < 100, a)\n"
        "    return min(b, key=lambda i: i.cost)\n"
    )
    p = _write(tmp_path, "x.py", src)
    findings = scan(p)
    assert findings == [], "validator call as first body stmt should suppress finding"


def test_scan_no_finding_when_no_shared_fields(tmp_path):
    src = (
        "def validate_meta(m):\n"
        "    return bool(m.owner)\n"
        "\n"
        "def decide(items):\n"
        "    a = filter(lambda i: i.tier == 'A', items)\n"
        "    b = filter(lambda i: i.cost < 100, a)\n"
        "    return min(b, key=lambda i: i.cost)\n"
    )
    p = _write(tmp_path, "x.py", src)
    findings = scan(p)
    assert findings == [], "no shared field between pipeline predicates and validator"


def test_scan_reports_function_name_and_line(tmp_path):
    src = (
        "\n\n"
        "def validate_manifest(m):\n"
        "    return bool(m.tier)\n"
        "\n"
        "\n"
        "def decide(items):\n"
        "    a = filter(lambda i: i.tier == 'A', items)\n"
        "    b = filter(lambda i: i.tier == 'B', a)\n"
        "    return list(b)\n"
    )
    p = _write(tmp_path, "x.py", src)
    findings = scan(p)
    assert len(findings) == 1
    assert findings[0].function == "decide"
    assert findings[0].line == 7


def test_cli_check_exit_code_zero_on_clean_file(tmp_path):
    src = "def foo():\n    return 1\n"
    p = _write(tmp_path, "x.py", src)
    assert main(["--check", str(p)]) == 0


def test_cli_check_exit_code_one_on_finding(tmp_path):
    src = (
        "def validate(m):\n"
        "    return bool(m.tier)\n"
        "def decide(items):\n"
        "    a = filter(lambda i: i.tier == 'A', items)\n"
        "    b = filter(lambda i: i.tier == 'B', a)\n"
        "    return b\n"
    )
    p = _write(tmp_path, "x.py", src)
    assert main(["--check", str(p)]) == 1


def test_cli_repo_root_skips_tests_by_default(tmp_path):
    (tmp_path / "tests").mkdir()
    _write(tmp_path / "tests", "t.py", (
        "def validate(x):\n"
        "    return x.tier\n"
        "def decide(items):\n"
        "    a = filter(lambda i: i.tier, items)\n"
        "    b = filter(lambda i: i.tier == 'A', a)\n"
        "    return b\n"
    ))
    assert main(["--repo-root", str(tmp_path)]) == 0


def test_cli_repo_root_include_tests_picks_up_tests(tmp_path):
    (tmp_path / "tests").mkdir()
    _write(tmp_path / "tests", "t.py", (
        "def validate(x):\n"
        "    return x.tier\n"
        "def decide(items):\n"
        "    a = filter(lambda i: i.tier, items)\n"
        "    b = filter(lambda i: i.tier == 'A', a)\n"
        "    return b\n"
    ))
    assert main(["--repo-root", str(tmp_path), "--include-tests"]) == 1


def test_cli_missing_file_exit_2(tmp_path):
    assert main(["--check", str(tmp_path / "nope.py")]) == 2
