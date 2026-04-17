"""Phase 25 Phase 4: qorlogic init --tone persists tier to config."""
from __future__ import annotations

import json
from pathlib import Path


def test_init_tone_plain_writes_config(tmp_path):
    from qor.cli import main
    rc = main(["init", "--tone", "plain", "--target", str(tmp_path)])
    assert rc == 0
    data = json.loads((tmp_path / ".qorlogic" / "config.json").read_text(encoding="utf-8"))
    assert data["tone"] == "plain"


def test_init_invalid_tone_rejected(tmp_path):
    """argparse choices= rejects invalid tiers at the parser level (exit 2)."""
    from qor.cli import main
    import pytest
    with pytest.raises(SystemExit) as exc_info:
        main(["init", "--tone", "invalid", "--target", str(tmp_path)])
    assert exc_info.value.code == 2
    assert not (tmp_path / ".qorlogic" / "config.json").exists()


def test_init_no_tone_defaults_to_technical(tmp_path):
    from qor.cli import main
    rc = main(["init", "--target", str(tmp_path)])
    assert rc == 0
    data = json.loads((tmp_path / ".qorlogic" / "config.json").read_text(encoding="utf-8"))
    assert data["tone"] == "technical"


def test_init_preserves_phase24_fields(tmp_path):
    from qor.cli import main
    rc = main(["init", "--host", "gemini", "--scope", "repo", "--tone", "standard", "--target", str(tmp_path)])
    assert rc == 0
    data = json.loads((tmp_path / ".qorlogic" / "config.json").read_text(encoding="utf-8"))
    assert data["host"] == "gemini"
    assert data["scope"] == "repo"
    assert data["profile"] == "sdlc"
    assert data["tone"] == "standard"
    assert "governance_scope" in data
