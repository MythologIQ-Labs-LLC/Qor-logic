"""Phase 24: install reads from per-host variant dir, not hardcoded claude."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _stage_variant(dist_root: Path, host: str, skill_body: str) -> None:
    variant = dist_root / "variants" / host
    skill_dir = variant / "skills" / "A"
    skill_dir.mkdir(parents=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(skill_body, encoding="utf-8")
    import hashlib
    sha = hashlib.sha256(skill_path.read_bytes()).hexdigest()
    manifest = {
        "schema_version": "1",
        "generated_ts": "2026-04-17T00:00:00Z",
        "files": [{
            "id": "A",
            "source_path": "skills/A/SKILL.md",
            "install_rel_path": "skills/A/SKILL.md",
            "sha256": sha,
        }],
    }
    (variant / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8",
    )


def test_codex_install_reads_codex_variant(tmp_path):
    """--host codex must install codex-flavored bytes, not claude."""
    from qor.install import _do_install
    _stage_variant(tmp_path, "claude", "CLAUDE_BODY\n")
    _stage_variant(tmp_path, "codex", "CODEX_BODY\n")

    target = tmp_path / "target"
    rc = _do_install("codex", target_override=target, dist_root=tmp_path)
    assert rc == 0

    installed = (target / "skills" / "A" / "SKILL.md").read_text(encoding="utf-8")
    assert installed == "CODEX_BODY\n"


def test_claude_install_reads_claude_variant(tmp_path):
    from qor.install import _do_install
    _stage_variant(tmp_path, "claude", "CLAUDE_BODY\n")
    _stage_variant(tmp_path, "codex", "CODEX_BODY\n")

    target = tmp_path / "target"
    rc = _do_install("claude", target_override=target, dist_root=tmp_path)
    assert rc == 0

    installed = (target / "skills" / "A" / "SKILL.md").read_text(encoding="utf-8")
    assert installed == "CLAUDE_BODY\n"


def test_missing_per_variant_manifest_errors(tmp_path, capsys):
    from qor.install import _do_install
    # Stage claude but not codex
    _stage_variant(tmp_path, "claude", "CLAUDE_BODY\n")

    target = tmp_path / "target"
    rc = _do_install("codex", target_override=target, dist_root=tmp_path)
    assert rc == 1
    err = capsys.readouterr().err
    assert "codex" in err.lower() or "manifest" in err.lower()


def test_dry_run_shows_variant_specific_source(tmp_path, capsys):
    from qor.install import _do_install
    _stage_variant(tmp_path, "codex", "CODEX_BODY\n")

    target = tmp_path / "target"
    rc = _do_install("codex", target_override=target, dist_root=tmp_path, dry_run=True)
    assert rc == 0
    captured = capsys.readouterr().out
    assert "variants" in captured.replace("\\", "/")
    assert "codex" in captured
    assert "claude" not in captured or "variants/claude" not in captured.replace("\\", "/")
    # Nothing actually copied
    assert not (target / "skills" / "A" / "SKILL.md").exists()
