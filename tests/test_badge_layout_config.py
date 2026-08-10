"""Phase 210 (GH #299): the declared layout is reachable from the governed flow.

Phase 206 made the badge layout declarable and fail-loud, but flags were the
only channel and no governed invocation passes one. A repository whose skills
are not under `qor/` therefore failed every release-class seal, and the abort
message told the operator to declare a layout the governed path could not carry.

Two properties are pinned here that inheritance would not prove:

* an unset flag must LOSE to config, which is impossible while flag defaults
  equal the real layout values; and
* containment must hold for config-supplied roots, asserted by driving the
  CONFIG channel rather than reusing the flag-channel negatives.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qor.scripts import badge_currency, seal_artifacts
from qor.scripts.badge_layout import (
    DEFAULT_LAYOUT,
    BadgeLayoutError,
    add_layout_args,
    layout_from_args,
)


def _write_config(root: Path, payload) -> None:
    d = root / ".qorlogic"
    d.mkdir(parents=True, exist_ok=True)
    text = payload if isinstance(payload, str) else json.dumps(payload)
    (d / "config.json").write_text(text, encoding="utf-8")


def _resolve(root: Path, argv: list[str] | None = None):
    """Resolve a layout exactly as a CLI would, for `argv` (default: none)."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    add_layout_args(parser)
    args = parser.parse_args(["--repo-root", str(root), *(argv or [])])
    return layout_from_args(args)


def _non_qor_repo(tmp_path: Path) -> Path:
    (tmp_path / "skills" / "demo").mkdir(parents=True)
    (tmp_path / "skills" / "demo" / "SKILL.md").write_text("# demo\n", encoding="utf-8")
    (tmp_path / "skills" / "bic" / "agents").mkdir(parents=True)
    (tmp_path / "skills" / "bic" / "agents" / "r.md").write_text("# r\n", encoding="utf-8")
    (tmp_path / "governance").mkdir()
    (tmp_path / "governance" / "doctrine-demo.md").write_text("# d\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "META_LEDGER.md").write_text(
        "### Entry #1: SESSION SEAL -- Phase 1 test\n", encoding="utf-8")
    (tmp_path / "docs" / "SYSTEM_STATE.md").write_text(
        "# State\n\n**Snapshot**: 2026-07-30\n**Phase**: Phase 1\n", encoding="utf-8")
    (tmp_path / "README.md").write_text(
        '<img src="https://img.shields.io/badge/Tests-1%20passing-green" alt="Tests: 1 passing">\n'
        '<img src="https://img.shields.io/badge/Ledger-1%20entries%20sealed-green" alt="Ledger: 1 entries sealed">\n'
        '<img src="https://img.shields.io/badge/Skills-1-blue" alt="Skills: 1">\n'
        '<img src="https://img.shields.io/badge/Agents-1-blue" alt="Agents: 1">\n'
        '<img src="https://img.shields.io/badge/Doctrines-1-blue" alt="Doctrines: 1">\n',
        encoding="utf-8")
    return tmp_path


_NON_QOR_LAYOUT = {
    "skills_root": "skills", "skills_pattern": "**/SKILL.md",
    "agents_root": "skills", "agents_pattern": "**/agents/*.md",
    "doctrines_root": "governance", "doctrines_pattern": "doctrine-*.md",
}


# -------- resolution --------

def test_config_declared_layout_resolves_without_flags(tmp_path: Path):
    _write_config(tmp_path, {"layout": {"skills_root": "skills"}})
    assert _resolve(tmp_path).skills_root == Path("skills")


def test_flag_beats_config_and_config_beats_default(tmp_path: Path):
    assert _resolve(tmp_path).skills_root == DEFAULT_LAYOUT.skills_root

    _write_config(tmp_path, {"layout": {"skills_root": "from-config"}})
    assert _resolve(tmp_path).skills_root == Path("from-config")

    flagged = _resolve(tmp_path, ["--skills-root", "from-flag"])
    assert flagged.skills_root == Path("from-flag")


def test_resolution_is_per_key_not_all_or_nothing(tmp_path: Path):
    _write_config(tmp_path, {"layout": {"skills_root": "skills"}})
    resolved = _resolve(tmp_path)
    assert resolved.skills_root == Path("skills")
    assert resolved.skills_pattern == DEFAULT_LAYOUT.skills_pattern
    assert resolved.agents_root == DEFAULT_LAYOUT.agents_root
    assert resolved.agents_pattern == DEFAULT_LAYOUT.agents_pattern
    assert resolved.doctrines_root == DEFAULT_LAYOUT.doctrines_root
    assert resolved.doctrines_pattern == DEFAULT_LAYOUT.doctrines_pattern


def test_unset_flag_is_distinguishable_from_flag_set_to_default(tmp_path: Path):
    """The property that makes a config channel possible at all.

    While flag defaults equalled the real layout values, an unset flag was
    indistinguishable from one set to the default and would win every
    comparison, so any config source would have been inert.
    """
    _write_config(tmp_path, {"layout": {"skills_root": "skills"}})

    assert _resolve(tmp_path).skills_root == Path("skills"), "unset flag must lose to config"
    explicit = _resolve(tmp_path, ["--skills-root", str(DEFAULT_LAYOUT.skills_root)])
    assert explicit.skills_root == DEFAULT_LAYOUT.skills_root, "explicit flag must win"


@pytest.mark.parametrize("payload", [
    {"layout": "not-a-dict"},
    {"layout": ["skills"]},
    {"layout": {"skills_root": 17}},
    {"layout": {"skills_root": ""}},
    {"layout": {"skills_root": "   "}},
    {"layout": {"skills_pattern": None}},
    "{not valid json",
])
def test_malformed_and_wrong_typed_layout_values_degrade_to_defaults(tmp_path: Path, payload):
    _write_config(tmp_path, payload)
    resolved = _resolve(tmp_path)
    assert resolved == DEFAULT_LAYOUT, payload


# -------- containment, driven through the CONFIG channel --------

def test_config_declared_root_escaping_the_repository_is_rejected(tmp_path: Path):
    """Containment is re-proven through the new channel, not inherited.

    Every Phase 206 negative drives flags. A later change resolving config
    roots eagerly would move resolution outside the guard with nothing to
    notice, so these enter with no flags set.
    """
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "SKILL.md").write_text("# external\n", encoding="utf-8")

    _write_config(repo, {"layout": {"skills_root": "../outside"}})
    with pytest.raises(BadgeLayoutError, match="within repo root|not found"):
        badge_currency.count_skills(
            repo, _resolve(repo).skills_root, _resolve(repo).skills_pattern
        )

    _write_config(repo, {"layout": {"skills_root": str(outside)}})
    with pytest.raises(BadgeLayoutError, match="within repo root"):
        badge_currency.count_skills(
            repo, _resolve(repo).skills_root, _resolve(repo).skills_pattern
        )

    _write_config(repo, {"layout": {"skills_pattern": "../**/SKILL.md"}})
    layout = _resolve(repo)
    (repo / "qor" / "skills").mkdir(parents=True)
    with pytest.raises(BadgeLayoutError, match="must not traverse"):
        badge_currency.count_skills(repo, layout.skills_root, layout.skills_pattern)


def test_config_declared_root_through_a_symlink_is_rejected(tmp_path: Path):
    repo = tmp_path / "repo"
    skills = repo / "skills"
    skills.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "SKILL.md").write_text("# external\n", encoding="utf-8")
    try:
        (skills / "linked").symlink_to(outside, target_is_directory=True)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"host cannot create symlinks: {exc}")

    _write_config(repo, {"layout": {"skills_root": "skills/linked"}})
    layout = _resolve(repo)
    with pytest.raises(BadgeLayoutError, match="within repo root"):
        badge_currency.count_skills(repo, layout.skills_root, layout.skills_pattern)


# -------- the two entry points agree --------

def test_both_entry_points_resolve_identical_layouts(tmp_path: Path):
    """The check path and the write path cannot drift into divergent layouts."""
    _write_config(tmp_path, {"layout": _NON_QOR_LAYOUT})
    argv = ["--check", "--repo-root", str(tmp_path), "--skip-tests"]

    seal_args = seal_artifacts._build_parser().parse_args(argv)
    currency_args = badge_currency._build_parser().parse_args(
        ["--repo-root", str(tmp_path)]
    )
    assert layout_from_args(seal_args) == layout_from_args(currency_args)


# -------- the governed invocations, verbatim --------

def test_governed_check_invocation_honors_config(tmp_path: Path):
    """GH #299 acceptance criterion 1, executed.

    This is the exact argv `/qor-substantiate` Step 6.5 and the CI step use.
    """
    root = _non_qor_repo(tmp_path)
    governed = ["--check", "--repo-root", str(root), "--skip-tests"]

    assert seal_artifacts.main(governed) == 1, "no config: unresolvable, must abort"

    _write_config(root, {"layout": _NON_QOR_LAYOUT})
    assert seal_artifacts.main(governed) == 0, "declared layout must be honored"


def test_governed_write_invocation_honors_config(tmp_path: Path):
    root = _non_qor_repo(tmp_path)
    readme = root / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8")
        .replace("Skills-1-blue", "Skills-99-blue")
        .replace('alt="Skills: 1"', 'alt="Skills: 99"'),
        encoding="utf-8",
    )
    _write_config(root, {"layout": _NON_QOR_LAYOUT})

    rc = seal_artifacts.main(
        ["--write", "--phase", "1", "--snapshot", "2026-07-30",
         "--repo-root", str(root), "--skip-tests"]
    )

    assert rc == 0
    written = readme.read_text(encoding="utf-8")
    assert "Skills-1-blue" in written and "Skills-99" not in written
