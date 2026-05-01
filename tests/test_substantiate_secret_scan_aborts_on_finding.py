"""Phase 56: substantiate-time scanner behavioral test (subprocess + fixture worktree)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from qor.policy.resource_attributes import compute_production_attributes


def test_substantiate_secret_scan_blocks_seal_when_finding_present(tmp_path: Path):
    f = tmp_path / "leak.py"
    f.write_text('AWS_KEY = "AKIAIOSFODNN7VARIANT"\n', encoding="utf-8")  # noqa: secret-scan
    out = tmp_path / "secrets.findings.json"
    proc = subprocess.run(
        [sys.executable, "-m", "qor.scripts.secret_scanner",
         "--files", str(f), "--out", str(out)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 1
    assert out.exists()
    assert "BLOCK" in (proc.stderr + proc.stdout)


def test_substantiate_secret_scan_passes_seal_on_clean_staging(tmp_path: Path):
    f = tmp_path / "ok.py"
    f.write_text("x = 1\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "qor.scripts.secret_scanner",
         "--files", str(f)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0


def test_compute_production_attributes_returns_has_hardcoded_secrets():
    dirty = compute_production_attributes(
        "src/leak.py", 'AWS_KEY = "AKIAIOSFODNN7VARIANT"\n')  # noqa: secret-scan
    assert dirty["has_hardcoded_secrets"] is True

    clean = compute_production_attributes("src/ok.py", "x = 1\n")
    assert clean["has_hardcoded_secrets"] is False


def test_compute_production_attributes_respects_allowlist():
    # Cedar/schema attribute names that resemble secret patterns but are seeded.
    content = 'permitted_tools = "Read, Grep, Bash, Edit, Write, Agent"\n'
    attrs = compute_production_attributes("qor/skills/foo/SKILL.md", content)
    assert attrs["has_hardcoded_secrets"] is False
