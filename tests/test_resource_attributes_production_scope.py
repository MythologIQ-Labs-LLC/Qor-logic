"""Phase 56: tests for compute_production_attributes helper."""
from __future__ import annotations

from qor.policy.resource_attributes import compute_production_attributes


def test_compute_production_attributes_returns_expected_shape():
    attrs = compute_production_attributes("src/x.py", "x = 1\n")
    assert set(attrs.keys()) == {"has_hardcoded_secrets"}
    assert isinstance(attrs["has_hardcoded_secrets"], bool)


def test_helper_handles_non_python_paths_via_content_only():
    # Path is metadata only — secret detected purely from content.
    attrs = compute_production_attributes(
        "docs/README.md", '-----BEGIN OPENSSH PRIVATE KEY-----\nfoo\n')  # noqa: secret-scan
    assert attrs["has_hardcoded_secrets"] is True
