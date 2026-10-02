"""Phase 302 (GH #440): install records only sha256 values it has checked
against the installed bytes, and dist manifests are drift-checked.

The fixtures compile a two-file fake source tree into ``tmp_path`` with the
compile clock pinned, so no result depends on the wall clock, the network or
the repository's live dist. The LF-pin test reads the checkout's own
``.gitattributes`` through git.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from qor.install import _do_install
from qor.scripts import check_variant_drift as drift_mod
from qor.scripts import dist_compile as compile_mod

REPO_ROOT = Path(__file__).resolve().parent.parent
CI_YML = REPO_ROOT / ".github" / "workflows" / "ci.yml"
SKILL_REL = "skills/test-skill/SKILL.md"
ZERO = "0" * 64
RECEIPT = ".qorlogic-installed.json"


class _FixedClock(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.fixture
def dist(tmp_path, monkeypatch):
    skills = tmp_path / "skills"
    agents = tmp_path / "agents"
    (skills / "governance" / "test-skill").mkdir(parents=True)
    (skills / "governance" / "test-skill" / "SKILL.md").write_bytes(b"# test-skill\n")
    (agents / "governance").mkdir(parents=True)
    (agents / "governance" / "test-agent.md").write_bytes(b"# agent\n")
    monkeypatch.setattr(compile_mod, "SKILLS_SRC", skills)
    monkeypatch.setattr(compile_mod, "AGENTS_SRC", agents)
    monkeypatch.setattr(compile_mod, "datetime", _FixedClock)
    out = tmp_path / "dist"
    compile_mod.compile_all(out)
    return out


def _drift(out: Path, monkeypatch, capsys) -> tuple[int, str]:
    capsys.readouterr()
    monkeypatch.setattr(sys, "argv", ["check_variant_drift", "--committed", str(out)])
    rc = drift_mod.main()
    return rc, capsys.readouterr().out


def _edit_manifest(path: Path, edit) -> None:
    doc = json.loads(path.read_text(encoding="utf-8"))
    edit(doc)
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def _stale_hash(doc: dict) -> None:
    for entry in doc["files"]:
        if entry["install_rel_path"] == SKILL_REL:
            entry["sha256"] = ZERO


def _drop_entry(doc: dict) -> None:
    doc["files"] = [e for e in doc["files"] if e["install_rel_path"] != SKILL_REL]


def _ghost_entry(doc: dict) -> None:
    doc["files"].append({
        "id": "ghost.md",
        "source_path": "agents/ghost.md",
        "install_rel_path": "agents/ghost.md",
        "sha256": ZERO,
    })


def _claude(dist: Path) -> Path:
    return dist / "variants" / "claude"


def _stale_manifest_hash(dist: Path) -> None:
    _edit_manifest(_claude(dist) / "manifest.json", _stale_hash)


def _append_to_shipped_file(dist: Path) -> None:
    shipped = _claude(dist) / SKILL_REL
    shipped.write_bytes(shipped.read_bytes() + b"TAMPER\n")


@pytest.mark.parametrize("manifest_rel,edit", [
    ("variants/claude/manifest.json", _stale_hash),
    ("variants/claude/manifest.json", _drop_entry),
    ("variants/claude/manifest.json", _ghost_entry),
    ("manifest.json", _stale_hash),
], ids=["stale-hash", "unlisted-file", "unshipped-entry", "top-level-index"])
def test_drift_flags_a_manifest_that_does_not_describe_the_shipped_bytes(
    dist, monkeypatch, capsys, manifest_rel, edit,
):
    rc, out = _drift(dist, monkeypatch, capsys)
    assert rc == 0, out
    _edit_manifest(dist / manifest_rel, edit)
    rc, out = _drift(dist, monkeypatch, capsys)
    assert rc == 1, out
    assert f"~ {manifest_rel} (content differs)" in out


def test_drift_flags_an_unparseable_manifest(dist, monkeypatch, capsys):
    (_claude(dist) / "manifest.json").write_bytes(b"{")
    rc, out = _drift(dist, monkeypatch, capsys)
    assert rc == 1, out
    assert "~ variants/claude/manifest.json (content differs)" in out


def test_drift_ignores_only_the_generated_timestamp(dist, monkeypatch, capsys):
    manifests = sorted(dist.rglob("manifest.json"))
    assert len(manifests) == 7
    for path in manifests:
        _edit_manifest(path, lambda doc: doc.update(generated_ts="2000-01-01T00:00:00Z"))
    rc, out = _drift(dist, monkeypatch, capsys)
    assert rc == 0, out
    assert out.startswith("OK: ")


@pytest.mark.parametrize("dry_run", [False, True], ids=["install", "dry-run"])
@pytest.mark.parametrize("damage", [_stale_manifest_hash, _append_to_shipped_file],
                         ids=["stale-manifest-hash", "edited-shipped-bytes"])
def test_install_refuses_bytes_that_do_not_match_the_manifest(
    dist, tmp_path, capsys, damage, dry_run,
):
    damage(dist)
    target = tmp_path / "target"
    capsys.readouterr()
    rc = _do_install("claude", target_override=target, dist_root=dist, dry_run=dry_run)
    captured = capsys.readouterr()
    assert rc == 1, captured.out
    assert f"sha256 mismatch: {SKILL_REL}" in captured.err
    written = [p for p in target.rglob("*") if p.is_file()] if target.exists() else []
    assert written == []
    assert "Installed" not in captured.out


def _receipt_rows(target: Path) -> list[dict]:
    return json.loads((target / RECEIPT).read_text(encoding="utf-8"))["files"]


def test_install_receipt_hashes_equal_the_installed_bytes(dist, tmp_path):
    target = tmp_path / "target"
    assert _do_install("claude", target_override=target, dist_root=dist) == 0
    rows = _receipt_rows(target)
    installed = {p for p in target.rglob("*") if p.is_file() and p.name != RECEIPT}
    assert {Path(r["path"]) for r in rows} == installed
    for row in rows:
        actual = hashlib.sha256(Path(row["path"]).read_bytes()).hexdigest()
        assert row["sha256"] == actual, row["path"]


def test_install_does_not_verify_an_entry_it_does_not_install(dist, tmp_path):
    extra = _claude(dist) / "extra" / "x.md"
    extra.parent.mkdir(parents=True)
    extra.write_bytes(b"extra\n")
    _edit_manifest(_claude(dist) / "manifest.json", lambda doc: doc["files"].append({
        "id": "x.md", "source_path": "extra/x.md",
        "install_rel_path": "extra/x.md", "sha256": ZERO,
    }))
    target = tmp_path / "target"
    assert _do_install("claude", target_override=target, dist_root=dist) == 0
    rows = _receipt_rows(target)
    assert not [r for r in rows if "extra" in r["path"]]
    assert len(rows) == 2


def _drift_precedes_recompile(steps: list) -> bool:
    for step in steps:
        run = step.get("run", "") if isinstance(step, dict) else ""
        if any(word in run for word in ("pytest", "dist_compile", "qor-logic compile")):
            return False
        if "check_variant_drift" in run:
            return True
    return False


def test_a_ci_job_checks_variant_drift_on_the_committed_dist():
    data = yaml.safe_load(CI_YML.read_text(encoding="utf-8"))
    jobs = data["jobs"]
    assert any(_drift_precedes_recompile(job.get("steps", [])) for job in jobs.values()), (
        "no CI job runs check_variant_drift before a step that runs pytest or recompiles"
    )


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    return result.stdout


def test_every_committed_dist_file_checks_out_with_lf_line_endings():
    paths = [p for p in _git("ls-files", "-z", "qor/dist").split("\0") if p]
    assert paths
    fields = _git("check-attr", "-z", "eol", "--", *paths).split("\0")
    eol = {fields[i]: fields[i + 2] for i in range(0, len(fields) - 2, 3)}
    not_lf = sorted(p for p in paths if eol.get(p) != "lf")
    assert not_lf == [], f"{len(not_lf)} dist file(s) without eol=lf: {not_lf[:10]}"
