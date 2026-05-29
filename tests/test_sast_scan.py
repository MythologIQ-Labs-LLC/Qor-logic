"""Behavioral tests for the tool-agnostic SAST sub-check (Phase 115, #167).

Unit tests drive canned bandit JSON and a fake backend so they pass with or
without bandit installed; the integration test runs the real backend only when
bandit is available.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from qor.scripts import sast_scan


def test_to_pillar_pass_on_no_findings():
    p = sast_scan.to_pillar([])
    assert p["status"] == "pass"
    assert p["metric"] == 0


def test_to_pillar_fail_on_high_severity():
    p = sast_scan.to_pillar([{"severity": "HIGH", "text": "x", "location": "f.py:1"}])
    assert p["status"] == "fail"


def test_to_pillar_metric_counts_findings():
    p = sast_scan.to_pillar([{"severity": "LOW"}, {"severity": "MEDIUM"}])
    assert p["metric"] == 2
    assert p["status"] == "pass"  # no HIGH


def test_bandit_normalize_parses_json():
    raw = {"results": [
        {"issue_severity": "HIGH", "issue_text": "use of eval",
         "filename": "f.py", "line_number": 3},
    ]}
    findings = sast_scan.normalize_bandit(raw)
    assert len(findings) == 1
    assert findings[0]["severity"] == "HIGH"
    assert findings[0]["location"] == "f.py:3"


def test_unknown_backend_raises():
    with pytest.raises(ValueError):
        sast_scan.scan(["."], backend="nope")


def test_scan_skips_when_backend_unavailable(monkeypatch):
    def _unavailable(paths):
        raise sast_scan.BackendUnavailable("fake not installed")
    monkeypatch.setitem(sast_scan.BACKENDS, "fake", _unavailable)
    p = sast_scan.scan(["."], backend="fake")
    assert p["status"] == "skip"
    assert "fake" in p["note"]


def test_scan_fail_via_fake_backend(monkeypatch):
    monkeypatch.setitem(sast_scan.BACKENDS, "fake",
                        lambda paths: [{"severity": "HIGH", "location": "x.py:1"}])
    p = sast_scan.scan(["."], backend="fake")
    assert p["status"] == "fail"
    assert p["metric"] == 1


@pytest.mark.skipif(importlib.util.find_spec("bandit") is None,
                    reason="bandit not installed; SAST backend inactive in this env")
def test_bandit_backend_integration(tmp_path):
    f = tmp_path / "vuln.py"
    f.write_text("import hashlib\nh = hashlib.md5(b'x')\n", encoding="utf-8")
    findings = sast_scan.bandit_backend([str(tmp_path)])
    assert isinstance(findings, list)
    assert all("severity" in fd for fd in findings)
