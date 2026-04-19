"""Phase 33: verify the SHADOW_GENOME entry documenting the historical
seal-tag timing bug is present and cites the 4 affected tags.
"""
from __future__ import annotations

from pathlib import Path

SG_PATH = Path(__file__).resolve().parents[1] / "docs" / "SHADOW_GENOME.md"


def test_sg_phase33_a_present():
    text = SG_PATH.read_text(encoding="utf-8")
    assert "SG-Phase33-A" in text
    assert "seal_tag_timing" in text


def test_sg_phase33_a_cites_affected_tags():
    text = SG_PATH.read_text(encoding="utf-8")
    for tag in ("v0.19.0", "v0.20.0", "v0.21.0", "v0.22.0"):
        assert tag in text, f"SG-Phase33-A must name {tag}"
