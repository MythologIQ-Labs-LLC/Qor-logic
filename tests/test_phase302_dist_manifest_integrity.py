"""Phase 302 / GH #440: dist manifest claims are verified end to end."""
from __future__ import annotations

import hashlib
import json


def test_variant_drift_hashes_manifest_semantics_ignoring_only_timestamp(tmp_path):
    from qor.scripts.check_variant_drift import hash_tree

    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    root_a.mkdir()
    root_b.mkdir()
    base = {
        "schema_version": "1",
        "files": [{"install_rel_path": "skills/x/SKILL.md", "sha256": "abc"}],
    }
    (root_a / "manifest.json").write_text(
        json.dumps({**base, "generated_ts": "2026-01-01T00:00:00Z"}), encoding="utf-8"
    )
    (root_b / "manifest.json").write_text(
        json.dumps({**base, "generated_ts": "2026-09-28T00:00:00Z"}), encoding="utf-8"
    )
    assert hash_tree(root_a) == hash_tree(root_b)

    changed = {**base, "files": [{"install_rel_path": "skills/x/SKILL.md", "sha256": "def"}]}
    (root_b / "manifest.json").write_text(
        json.dumps({**changed, "generated_ts": "2026-09-28T00:00:00Z"}), encoding="utf-8"
    )
    assert hash_tree(root_a) != hash_tree(root_b)


def test_install_aborts_before_copy_when_manifest_hash_is_false(tmp_path, monkeypatch):
    from qor.install import _do_install
    from qor.scripts import dist_compile as compile_mod

    skills = tmp_path / "skills"
    agents = tmp_path / "agents"
    (skills / "governance" / "test-skill").mkdir(parents=True)
    (skills / "governance" / "test-skill" / "SKILL.md").write_text("# test\n", encoding="utf-8")
    agents.mkdir()
    monkeypatch.setattr(compile_mod, "SKILLS_SRC", skills)
    monkeypatch.setattr(compile_mod, "AGENTS_SRC", agents)

    dist = tmp_path / "dist"
    compile_mod.compile_all(dist)
    manifest_path = dist / "variants" / "claude" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][0]["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    target = tmp_path / "target"
    assert _do_install("claude", target_override=target, dist_root=dist) == 1
    assert not (target / ".qorlogic-installed.json").exists()
    assert not (target / "skills").exists()


def test_install_receipt_hashes_bytes_actually_copied(tmp_path, monkeypatch):
    from qor.install import _do_install
    from qor.scripts import dist_compile as compile_mod

    skills = tmp_path / "skills"
    agents = tmp_path / "agents"
    (skills / "governance" / "test-skill").mkdir(parents=True)
    (skills / "governance" / "test-skill" / "SKILL.md").write_text("# test\n", encoding="utf-8")
    agents.mkdir()
    monkeypatch.setattr(compile_mod, "SKILLS_SRC", skills)
    monkeypatch.setattr(compile_mod, "AGENTS_SRC", agents)

    dist = tmp_path / "dist"
    compile_mod.compile_all(dist)
    target = tmp_path / "target"
    assert _do_install("claude", target_override=target, dist_root=dist) == 0

    record = json.loads((target / ".qorlogic-installed.json").read_text(encoding="utf-8"))
    assert record["files"]
    for entry in record["files"]:
        installed = __import__("pathlib").Path(entry["path"])
        assert entry["sha256"] == hashlib.sha256(installed.read_bytes()).hexdigest()
