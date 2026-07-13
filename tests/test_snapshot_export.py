"""Phase 191 (GH #270): read-only repository governance snapshot contract."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import jsonschema
import pytest

from qor.scripts.snapshot_export import build_snapshot

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "qor" / "gates" / "schema" / "repository_snapshot.schema.json"

SECTIONS = ("meta", "session", "lifecycle", "gates", "ledger",
            "latest_seal", "health", "shadow", "drift", "findings")


def _strip_ts(snapshot: dict) -> dict:
    clone = json.loads(json.dumps(snapshot))
    clone["meta"].pop("generated_ts", None)
    return clone


# ----- healthy path (this repository) ---------------------------------------

def test_healthy_repo_snapshot():
    snap = build_snapshot(REPO_ROOT)
    for section in SECTIONS:
        assert section in snap, f"missing section {section}"
        assert "state" in snap[section], f"section {section} missing state"

    assert snap["meta"]["schemaVersion"] == "1"
    with (REPO_ROOT / "pyproject.toml").open("rb") as fh:
        version = tomllib.load(fh)["project"]["version"]
    assert snap["meta"]["qor_logic_version"] == version

    assert snap["session"]["state"] == "ok"
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{4}-[0-9a-f]{6}$", snap["session"]["session_id"])

    assert snap["lifecycle"]["state"] == "ok"
    assert snap["lifecycle"]["disposition"] == "SEALED"

    assert snap["ledger"]["state"] == "ok"
    assert re.match(r"^[0-9a-f]{64}$", snap["ledger"]["head_chain_hash"])
    assert snap["ledger"]["seal_entries"] > 0

    assert snap["latest_seal"]["state"] == "ok"
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    head_version = re.search(r"^## \[(\d+\.\d+\.\d+)\]", changelog, re.MULTILINE).group(1)
    assert snap["latest_seal"]["version"] == head_version

    assert snap["shadow"]["state"] == "ok"
    assert snap["shadow"]["total"] > 0
    assert all(isinstance(v, int) for v in snap["shadow"]["by_severity"].values())


def test_schema_conformance():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    snap = build_snapshot(REPO_ROOT)
    jsonschema.validate(snap, schema)


# ----- degraded fixtures ------------------------------------------------------

def _bare_repo(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "META_LEDGER.md").write_text(
        "# Meta Ledger\n\n*Chain integrity: VALID*\n", encoding="utf-8")
    return tmp_path


def test_no_session_repo(tmp_path):
    snap = build_snapshot(_bare_repo(tmp_path))
    assert snap["session"]["state"] == "unknown"
    assert snap["meta"]["schemaVersion"] == "1"  # export still succeeds


def test_malformed_ledger_repo(tmp_path):
    repo = _bare_repo(tmp_path)
    (repo / "docs" / "META_LEDGER.md").write_text("garbage \x00 bytes", encoding="utf-8")
    snap = build_snapshot(repo)
    assert snap["ledger"]["state"] in ("error", "unknown")
    assert snap["ledger"]["state"] != "ok"


def test_tampered_chain_repo(tmp_path):
    repo = _bare_repo(tmp_path)
    (repo / "docs" / "META_LEDGER.md").write_text(
        "# Meta Ledger\n\n"
        "### Entry #1: TEST\n\n"
        "**Content Hash**: `" + "a" * 64 + "`\n"
        "**Previous Hash**: `" + "c" * 64 + "`\n"
        "**Chain Hash (Merkle seal)**: `" + "b" * 64 + "`\n\n---\n",
        encoding="utf-8")
    snap = build_snapshot(repo)
    assert snap["ledger"]["state"] == "error"


def test_missing_artifacts_repo(tmp_path):
    repo = _bare_repo(tmp_path)
    (repo / ".qor" / "session").mkdir(parents=True)
    (repo / ".qor" / "session" / "current").write_text(
        "2026-07-13T0000-abcdef", encoding="utf-8")
    (repo / ".qor" / "gates").mkdir()
    snap = build_snapshot(repo)
    assert snap["session"]["state"] == "ok"
    assert snap["gates"]["state"] == "unknown"


# ----- contract properties ----------------------------------------------------

def test_determinism_modulo_ts(tmp_path):
    repo = _bare_repo(tmp_path)
    first = _strip_ts(build_snapshot(repo))
    second = _strip_ts(build_snapshot(repo))
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_export_is_read_only(tmp_path):
    repo = _bare_repo(tmp_path)

    def tree_hash() -> str:
        h = hashlib.sha256()
        for p in sorted(repo.rglob("*")):
            if p.is_file():
                h.update(p.relative_to(repo).as_posix().encode())
                h.update(p.read_bytes())
        return h.hexdigest()

    before = tree_hash()
    build_snapshot(repo)
    assert tree_hash() == before


def test_cli_writes_out_file(tmp_path):
    repo = _bare_repo(tmp_path)
    out = tmp_path / "snapshot.json"
    proc = subprocess.run(
        [sys.executable, "-m", "qor.scripts.snapshot_export",
         "--repo-root", str(repo), "--out", str(out)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["meta"]["schemaVersion"] == "1"
