"""Phase 56: gitleaks-v8-compatible findings JSON shape tests."""
from __future__ import annotations

from qor.scripts import secret_scanner


def _finding(**overrides):
    base = dict(  # noqa: secret-scan
        file="src/leak.py",
        line=42,
        pattern_name="aws-access-key",
        severity=3,
        matched_text_redacted="AKIA..NT",
    )
    base.update(overrides)
    return secret_scanner.Finding(**base)


def test_to_gitleaks_json_emits_required_v8_fields():
    out = secret_scanner.to_gitleaks_json([_finding()])
    assert len(out) == 1
    keys = set(out[0].keys())
    assert {"Description", "RuleID", "File", "Line", "Match", "Secret", "Tags"} <= keys


def test_to_gitleaks_json_secret_field_is_redacted():
    f = _finding(matched_text_redacted="abcd...ef")
    out = secret_scanner.to_gitleaks_json([f])
    assert out[0]["Secret"] == "abcd...ef"
    assert "AKIAIOSFODNN7VARIANT" not in out[0]["Secret"]  # noqa: secret-scan


def test_to_gitleaks_json_handles_empty_finding_list():
    assert secret_scanner.to_gitleaks_json([]) == []


def test_to_gitleaks_json_tags_field_includes_severity():
    out = secret_scanner.to_gitleaks_json([_finding(severity=3)])
    assert any(t == "severity:3" for t in out[0]["Tags"])
