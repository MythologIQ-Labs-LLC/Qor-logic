"""Phase 210 (GH #299): one tolerant reader for `.qorlogic/config.json`.

Two consumers now read this file -- the Phase 207 attribution policy and the
Phase 210 layout resolution. Two independent tolerant parses would degrade
differently under identical malformed input, so there is exactly one reader and
its degradation is pinned here.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qor.scripts.attribution_policy import resolve_policy
from qor.scripts.qorlogic_config import load_section


def _write(root: Path, payload) -> None:
    d = root / ".qorlogic"
    d.mkdir(parents=True, exist_ok=True)
    text = payload if isinstance(payload, str) else json.dumps(payload)
    (d / "config.json").write_text(text, encoding="utf-8")


def test_load_section_returns_declared_mapping(tmp_path: Path):
    _write(tmp_path, {
        "attribution": {"model_coauthor": False},
        "layout": {"skills_root": "skills"},
    })
    assert load_section(tmp_path, "layout") == {"skills_root": "skills"}
    assert load_section(tmp_path, "attribution") == {"model_coauthor": False}
    assert load_section(tmp_path, "absent") == {}


@pytest.mark.parametrize(
    "payload",
    [
        None,                     # no file at all
        "{not valid json",        # unparseable
        '"a bare string"',        # non-object document
        "[1, 2, 3]",              # non-object document
        {"layout": "not-a-dict"},  # non-object section
        {"layout": ["a", "b"]},    # non-object section
    ],
)
def test_load_section_degrades_on_every_malformed_shape(tmp_path: Path, payload):
    if payload is not None:
        _write(tmp_path, payload)
    assert load_section(tmp_path, "layout") == {}


def test_load_section_degrades_when_path_is_a_directory(tmp_path: Path):
    """An unreadable path yields the empty mapping rather than raising."""
    (tmp_path / ".qorlogic" / "config.json").mkdir(parents=True)
    assert load_section(tmp_path, "layout") == {}


def test_attribution_policy_still_resolves_through_the_shared_reader(tmp_path: Path):
    """Phase 207's contract is unchanged by the extraction."""
    assert resolve_policy(tmp_path).model_coauthor is True  # absent file

    _write(tmp_path, {"attribution": {"model_coauthor": False}})
    assert resolve_policy(tmp_path).model_coauthor is False

    for payload in ("{not valid json", '"bare"', {"attribution": "nope"},
                    {"attribution": {"model_coauthor": "false"}}):
        _write(tmp_path, payload)
        assert resolve_policy(tmp_path).model_coauthor is True, payload
