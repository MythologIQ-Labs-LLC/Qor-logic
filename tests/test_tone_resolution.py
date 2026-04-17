"""Phase 25 Phase 4: tier resolution primitive."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _write_config(path: Path, tone: str | None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {} if tone is None else {"tone": tone}
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_resolve_default_is_technical():
    from qor.tone import resolve_tone
    assert resolve_tone(None, None) == "technical"


def test_session_override_wins(tmp_path):
    from qor.tone import resolve_tone
    cfg = _write_config(tmp_path / "config.json", "plain")
    assert resolve_tone("technical", cfg) == "technical"


def test_config_honored(tmp_path):
    from qor.tone import resolve_tone
    cfg = _write_config(tmp_path / "config.json", "standard")
    assert resolve_tone(None, cfg) == "standard"


def test_session_override_alone():
    from qor.tone import resolve_tone
    assert resolve_tone("plain", None) == "plain"


def test_invalid_session_override_raises():
    from qor.tone import resolve_tone
    with pytest.raises(ValueError, match="garbage|invalid"):
        resolve_tone("garbage", None)


def test_config_missing_tone_falls_back(tmp_path):
    from qor.tone import resolve_tone
    cfg = _write_config(tmp_path / "config.json", None)
    assert resolve_tone(None, cfg) == "technical"


def test_config_path_nonexistent_falls_back(tmp_path):
    from qor.tone import resolve_tone
    assert resolve_tone(None, tmp_path / "does-not-exist.json") == "technical"


def test_doctrine_has_how_skills_read_section():
    doctrine = Path(__file__).resolve().parent.parent / "qor" / "references" / "doctrine-communication-tiers.md"
    assert doctrine.exists(), f"doctrine file missing: {doctrine}"
    text = doctrine.read_text(encoding="utf-8")
    assert "## How skills read the tone value" in text
