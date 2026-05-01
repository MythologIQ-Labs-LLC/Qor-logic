"""Phase 56: secret-scanning gate — pattern catalog + scan API tests."""
from __future__ import annotations

import subprocess
import sys
from dataclasses import is_dataclass
from pathlib import Path

import pytest

from qor.scripts import secret_scanner


# --- detection (positive paths) -------------------------------------------------

def test_scan_detects_aws_access_key(tmp_path: Path):
    f = tmp_path / "leak.py"
    f.write_text('AWS_KEY = "AKIAIOSFODNN7VARIANT"\n', encoding="utf-8")  # noqa: secret-scan
    findings = secret_scanner.scan(f)
    names = {x.pattern_name for x in findings}
    assert "aws-access-key" in names


def test_scan_detects_github_pat_classic_format(tmp_path: Path):
    body = "ghp_" + "a" * 36
    f = tmp_path / "leak.py"
    f.write_text(f'TOKEN = "{body}"\n', encoding="utf-8")
    findings = secret_scanner.scan(f)
    assert any(x.pattern_name == "github-pat-classic" for x in findings)


def test_scan_detects_github_pat_finegrained_format(tmp_path: Path):
    body = "github_pat_" + "a" * 82
    f = tmp_path / "leak.py"
    f.write_text(f'TOKEN = "{body}"\n', encoding="utf-8")
    findings = secret_scanner.scan(f)
    assert any(x.pattern_name == "github-pat-finegrained" for x in findings)


def test_scan_detects_private_ssh_key_header(tmp_path: Path):
    f = tmp_path / "key.pem"
    f.write_text("-----BEGIN OPENSSH PRIVATE KEY-----\n", encoding="utf-8")  # noqa: secret-scan
    findings = secret_scanner.scan(f)
    assert any(x.pattern_name == "private-key-header" for x in findings)


def test_scan_detects_anthropic_key(tmp_path: Path):
    body = "sk-ant-" + "a" * 95
    f = tmp_path / "leak.py"
    f.write_text(f'KEY = "{body}"\n', encoding="utf-8")
    findings = secret_scanner.scan(f)
    assert any(x.pattern_name == "anthropic-key" for x in findings)


def test_scan_detects_generic_high_entropy_assignment(tmp_path: Path):
    f = tmp_path / "leak.py"
    f.write_text('secret_key = "abcDEF123ghiJKL456mnoPQR789"\n', encoding="utf-8")  # noqa: secret-scan
    findings = secret_scanner.scan(f)
    assert any(x.pattern_name == "generic-high-entropy-assignment" for x in findings)


# --- allowlist (negative paths) -------------------------------------------------

def test_scan_skips_aws_access_key_in_allowlist(tmp_path: Path):
    f = tmp_path / "doc.py"
    f.write_text('EXAMPLE = "AKIAIOSFODNN7EXAMPLE"\n', encoding="utf-8")
    assert secret_scanner.scan(f) == []


def test_scan_skips_known_attribute_name_pattern(tmp_path: Path):
    # Cedar/schema attribute names that resemble assignment regex but are not secrets.
    f = tmp_path / "config.py"
    f.write_text('permitted_tools = "Read, Grep, Bash, Edit, Write, Agent"\n', encoding="utf-8")
    assert secret_scanner.scan(f) == []


# --- finding shape --------------------------------------------------------------

def test_scan_returns_finding_with_redacted_match(tmp_path: Path):
    f = tmp_path / "leak.py"
    f.write_text('AWS_KEY = "AKIAIOSFODNN7VARIANT"\n', encoding="utf-8")  # noqa: secret-scan
    findings = secret_scanner.scan(f)
    assert findings, "expected at least one finding"
    redacted = findings[0].matched_text_redacted
    assert "..." in redacted
    # first 4 + ... + last 2 form
    head, tail = redacted.split("...", 1)
    assert len(head) == 4
    assert len(tail) == 2


def test_scan_returns_finding_with_correct_line_number(tmp_path: Path):
    f = tmp_path / "leak.py"
    f.write_text("\n\n\n\n" + 'AWS_KEY = "AKIAIOSFODNN7VARIANT"\n', encoding="utf-8")  # noqa: secret-scan
    findings = secret_scanner.scan(f)
    assert findings
    assert findings[0].line == 5


# --- scan_paths -----------------------------------------------------------------

def test_scan_paths_aggregates_findings_across_multiple_files(tmp_path: Path):
    a = tmp_path / "a.py"
    b = tmp_path / "b.py"
    a.write_text('K = "AKIAIOSFODNN7VARIANT"\n', encoding="utf-8")  # noqa: secret-scan
    b.write_text("ghp_" + "b" * 36 + "\n", encoding="utf-8")
    findings = secret_scanner.scan_paths([a, b])
    assert len(findings) == 2


def test_scan_paths_skips_binary_files(tmp_path: Path):
    binary = tmp_path / "blob.bin"
    binary.write_bytes(b"\x00\x01\x02" + b'AKIAIOSFODNN7VARIANT' + b"\x00")  # noqa: secret-scan
    findings = secret_scanner.scan_paths([binary])
    assert findings == []


# --- scan_staged ----------------------------------------------------------------

def test_scan_staged_invokes_git_diff_cached_argv_form(monkeypatch, tmp_path: Path):
    seen: dict[str, list[str]] = {}

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(argv, **kwargs):
        seen["argv"] = list(argv)
        return Result()

    monkeypatch.setattr(secret_scanner.subprocess, "run", fake_run)
    secret_scanner.scan_staged(tmp_path)
    assert seen["argv"] == [
        "git", "diff", "--cached", "--name-only", "--diff-filter=AM"
    ]


def test_scan_staged_returns_empty_when_nothing_staged(monkeypatch, tmp_path: Path):
    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(secret_scanner.subprocess, "run", lambda *a, **k: Result())
    assert secret_scanner.scan_staged(tmp_path) == []


# --- catalog frozen invariants --------------------------------------------------

def test_patterns_catalog_is_frozen():
    assert isinstance(secret_scanner.PATTERNS, tuple)
    for p in secret_scanner.PATTERNS:
        assert is_dataclass(p)
        # frozen=True dataclasses raise on __setattr__
        with pytest.raises(Exception):
            p.name = "mutated"  # type: ignore[misc]


def test_allowlist_is_frozen_and_contains_known_seeds():
    assert isinstance(secret_scanner._ALLOWLIST, frozenset)
    seeds = {
        "REDACTED", "EXAMPLE_SECRET", "AKIAIOSFODNN7EXAMPLE",
        "permitted_tools", "permitted_subagents",
    }
    assert seeds <= secret_scanner._ALLOWLIST


# --- CLI ------------------------------------------------------------------------

def test_cli_exit_1_on_finding_via_subprocess(tmp_path: Path):
    f = tmp_path / "leak.py"
    f.write_text('AWS_KEY = "AKIAIOSFODNN7VARIANT"\n', encoding="utf-8")  # noqa: secret-scan
    out = tmp_path / "findings.json"
    proc = subprocess.run(
        [sys.executable, "-m", "qor.scripts.secret_scanner",
         "--files", str(f), "--out", str(out)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 1, proc.stderr
    assert "BLOCK" in (proc.stderr + proc.stdout)


def test_cli_exit_0_on_clean_via_subprocess(tmp_path: Path):
    f = tmp_path / "ok.py"
    f.write_text('PI = 3.14159\n', encoding="utf-8")
    out = tmp_path / "findings.json"
    proc = subprocess.run(
        [sys.executable, "-m", "qor.scripts.secret_scanner",
         "--files", str(f), "--out", str(out)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr


def test_cli_exit_2_on_invalid_input(tmp_path: Path):
    proc = subprocess.run(
        [sys.executable, "-m", "qor.scripts.secret_scanner",
         "--files", str(tmp_path / "nonexistent.py")],
        capture_output=True, text=True,
    )
    assert proc.returncode == 2
