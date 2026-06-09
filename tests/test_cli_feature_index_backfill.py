"""Phase 146: behavioral coverage for the `list` and `info` CLI handlers.

Regression-coverage backfill (the handlers already ship): these tests lock in
current behavior so the FEATURE_INDEX rows FX003 (`list`) and FX005 (`info`)
can flip from `unverified` to `verified`. Each invokes the handler and asserts
return code + captured output; none is presence-only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _stage_manifest(dist_root: Path, ids: list[str]) -> None:
    files = [
        {"id": sid, "source_path": f"{sid}.md", "install_rel_path": f"{sid}.md", "sha256": "0" * 64}
        for sid in ids
    ]
    (dist_root / "manifest.json").write_text(
        json.dumps({"schema_version": "1", "generated_ts": "2026-06-09T00:00:00Z", "files": files}),
        encoding="utf-8",
    )


def _stage_skill(dist_root: Path, name: str, body: str) -> None:
    skill_dir = dist_root / "variants" / "claude" / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")


def test_do_list_available_enumerates_skills(tmp_path, monkeypatch, capsys):
    import qor.cli
    from qor.install import _do_list

    _stage_manifest(tmp_path, ["qor-plan", "qor-audit", "qor-plan"])
    monkeypatch.setattr(qor.cli, "_default_dist_root", lambda: tmp_path)

    rc = _do_list(argparse.Namespace(available=True))

    out = capsys.readouterr().out
    assert rc == 0
    assert "qor-plan" in out
    assert "qor-audit" in out
    # de-duplicated: the repeated id appears once
    assert out.count("qor-plan") == 1


def test_do_list_no_flag_errors(capsys):
    from qor.install import _do_list

    rc = _do_list(argparse.Namespace())

    err = capsys.readouterr().err
    assert rc == 1
    assert "--available" in err and "--installed" in err


def test_do_info_prints_known_skill(tmp_path, monkeypatch, capsys):
    import qor.cli
    from qor.cli import _do_info

    marker = "# qor-plan -- Simple Made Easy Planning"
    _stage_skill(tmp_path, "qor-plan", marker + "\nbody\n")
    monkeypatch.setattr(qor.cli, "_default_dist_root", lambda: tmp_path)

    rc = _do_info(argparse.Namespace(skill="qor-plan"))

    out = capsys.readouterr().out
    assert rc == 0
    assert marker in out


def test_do_info_missing_skill_returns_1(tmp_path, monkeypatch, capsys):
    import qor.cli
    from qor.cli import _do_info

    monkeypatch.setattr(qor.cli, "_default_dist_root", lambda: tmp_path)

    rc = _do_info(argparse.Namespace(skill="no-such-skill"))

    err = capsys.readouterr().err
    assert rc == 1
    assert "not found" in err
