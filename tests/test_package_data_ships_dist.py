"""Phase 305: the package-data globs select every file under qor/dist that
`list --available` and `install` read.

The tests stage only the qor/dist files the declared package-data globs
select (Python's recursive glob, files only, relative to qor/), then run the
real `list --available` and `install` handlers against that staged dist. They
prove the glob selection, not what a build ships: no wheel is built here. A
guard also fails if any dist manifest lists a path with a segment the build is
known to drop (a dot-prefixed name, or RCS, CVS or _darcs); that list of
segments is not claimed complete.
"""
from __future__ import annotations

import argparse
import glob
import json
import shutil
import tomllib
from pathlib import Path

import pytest

import qor.cli
from qor.install import _do_install, _do_list

REPO = Path(__file__).resolve().parents[1]
QOR = REPO / "qor"
HOSTS = sorted(p.name for p in (QOR / "dist" / "variants").iterdir() if p.is_dir())
BUILD_DROPPED_SEGMENTS = {"RCS", "CVS", "_darcs"}


def _package_data_globs() -> list[str]:
    data = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    return data["tool"]["setuptools"]["package-data"]["qor"]


def _stage_shipped_dist(dest: Path) -> Path:
    for pattern in _package_data_globs():
        for rel in glob.glob(pattern, root_dir=QOR, recursive=True):
            rel_posix = Path(rel).as_posix()
            if not rel_posix.startswith("dist/") or not (QOR / rel).is_file():
                continue
            target = dest / rel_posix
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(QOR / rel, target)
    return dest / "dist"


def _manifest(rel: str) -> dict:
    return json.loads((QOR / "dist" / rel).read_text(encoding="utf-8"))


def _listed_paths() -> list[str]:
    paths = [e["install_rel_path"] for e in _manifest("manifest.json")["files"]]
    for host in HOSTS:
        files = _manifest(f"variants/{host}/manifest.json")["files"]
        paths.extend(f"variants/{host}/{e['install_rel_path']}" for e in files)
    return paths


def test_list_available_reads_the_shipped_root_manifest(tmp_path, monkeypatch, capsys):
    dist = _stage_shipped_dist(tmp_path / "staged")
    monkeypatch.setattr(qor.cli, "_default_dist_root", lambda: dist)

    rc = _do_list(argparse.Namespace(available=True))

    expected = list(dict.fromkeys(e["id"] for e in _manifest("manifest.json")["files"]))
    assert rc == 0
    assert capsys.readouterr().out.splitlines() == expected


@pytest.mark.parametrize("host", HOSTS)
def test_install_from_the_shipped_dist_installs_every_manifest_file(tmp_path, host):
    dist = _stage_shipped_dist(tmp_path / "staged")
    target = tmp_path / "target"

    rc = _do_install(host, target_override=target, dist_root=dist)

    assert rc == 0
    records = list(target.rglob(".qorlogic-installed.json"))
    assert len(records) == 1
    installed = len(json.loads(records[0].read_text(encoding="utf-8"))["files"])
    listed = len(_manifest(f"variants/{host}/manifest.json")["files"])
    assert installed == listed


def test_no_manifest_path_has_a_segment_the_build_drops():
    offending = [
        path for path in _listed_paths()
        if any(s.startswith(".") or s in BUILD_DROPPED_SEGMENTS for s in path.split("/"))
    ]
    assert offending == []
