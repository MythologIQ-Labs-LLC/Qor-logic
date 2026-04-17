"""Phase 24: install gemini variant lands TOML files in commands/."""
from __future__ import annotations

import json
from pathlib import Path


def _stage_gemini_variant(dist_root: Path) -> None:
    variant = dist_root / "variants" / "gemini"
    commands = variant / "commands"
    commands.mkdir(parents=True)
    body_a = 'description = "A"\nprompt = """\nA body\n"""\n'
    body_b = 'description = "B"\nprompt = """\nB body\n"""\n'
    (commands / "a.toml").write_text(body_a, encoding="utf-8")
    (commands / "b.toml").write_text(body_b, encoding="utf-8")

    import hashlib
    files = []
    for name, body in [("a.toml", body_a), ("b.toml", body_b)]:
        rel = f"commands/{name}"
        sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
        files.append({
            "id": name,
            "source_path": rel,
            "install_rel_path": rel,
            "sha256": sha,
        })
    (variant / "manifest.json").write_text(
        json.dumps({
            "schema_version": "1",
            "generated_ts": "2026-04-17T00:00:00Z",
            "files": files,
        }, indent=2) + "\n",
        encoding="utf-8",
    )


def test_gemini_install_repo_scope_with_override(tmp_path):
    from qor.install import _do_install
    _stage_gemini_variant(tmp_path)
    target = tmp_path / "project"
    rc = _do_install("gemini", scope="repo", target_override=target, dist_root=tmp_path)
    assert rc == 0
    assert (target / "commands" / "a.toml").exists()
    assert (target / "commands" / "b.toml").exists()
    assert (target / ".qorlogic-installed.json").exists()


def test_gemini_install_repo_scope_cwd(tmp_path, monkeypatch):
    from qor.install import _do_install
    _stage_gemini_variant(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("QORLOGIC_PROJECT_DIR", raising=False)
    rc = _do_install("gemini", scope="repo", dist_root=tmp_path)
    assert rc == 0
    assert (tmp_path / ".gemini" / "commands" / "a.toml").exists()


def test_gemini_uninstall_cleans_commands_dir(tmp_path):
    from qor.install import _do_install, _do_uninstall
    _stage_gemini_variant(tmp_path)
    target = tmp_path / "project"
    _do_install("gemini", scope="repo", target_override=target, dist_root=tmp_path)
    assert (target / "commands" / "a.toml").exists()

    _do_uninstall(host="gemini", target_override=target)
    assert not (target / "commands" / "a.toml").exists()
    assert not (target / ".qorlogic-installed.json").exists()


def test_cli_main_accepts_gemini_host(tmp_path, monkeypatch):
    _stage_gemini_variant(tmp_path)
    target = tmp_path / "project"
    monkeypatch.setattr("qor.cli._default_dist_root", lambda: tmp_path)
    from qor.cli import main
    rc = main(["install", "--host", "gemini", "--target", str(target)])
    assert rc == 0
    assert (target / "commands" / "a.toml").exists()
