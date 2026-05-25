"""Phase 104: Dependabot configuration assertions.

Carry-forward from the Phase 101-103 supply-chain hardening cluster.
"""
from __future__ import annotations

import pathlib

import yaml

_CONFIG = pathlib.Path(".github/dependabot.yml")


def _load() -> dict:
    return yaml.safe_load(_CONFIG.read_text(encoding="utf-8"))


def test_dependabot_config_file_exists():
    assert _CONFIG.is_file(), ".github/dependabot.yml must be committed"


def test_dependabot_config_covers_actions_and_pip_ecosystems():
    config = _load()
    assert config.get("version") == 2, "dependabot config must declare version: 2"
    updates = config.get("updates") or []
    ecosystems = {u.get("package-ecosystem") for u in updates}
    assert "github-actions" in ecosystems, (
        f"dependabot must manage github-actions; got {ecosystems!r}"
    )
    assert "pip" in ecosystems, (
        f"dependabot must manage pip; got {ecosystems!r}"
    )


def test_dependabot_config_uses_supported_schedule_intervals():
    config = _load()
    valid_intervals = {"daily", "weekly", "monthly"}
    for entry in config.get("updates") or []:
        schedule = entry.get("schedule") or {}
        interval = schedule.get("interval")
        ecosystem = entry.get("package-ecosystem")
        assert interval in valid_intervals, (
            f"ecosystem {ecosystem!r} declares unsupported interval {interval!r}; "
            f"must be one of {valid_intervals}"
        )
