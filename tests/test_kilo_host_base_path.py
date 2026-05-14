"""Phase 65 (#53): kilo-code host filesystem base = .kilo (not .kilo-code).

The Kilo tool reads its config from `.kilo/`; pre-Phase-65 qor-logic
installed skills/agents under `.kilo-code/`, which Kilo never reads.
This test locks the corrected behavior:
- Filesystem base resolves to `.kilo` (repo + global scopes).
- Logical host identifier stays `kilo-code` (no breaking API change).
- Skills and agents directories resolve under `.kilo`, not `.kilo-code`.

Acceptance question: "If the unit's behavior were silently broken but the
artifact still existed, would this test fail?" - yes. Reverting
`_kilo_target()` to `.kilo-code` fails every test below.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.hosts import resolve


def test_kilo_repo_scope_base_is_dot_kilo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("QORLOGIC_PROJECT_DIR", raising=False)
    target = resolve("kilo-code", scope="repo")
    assert target.base == tmp_path / ".kilo", (
        f"kilo-code repo-scope base must be .kilo; got {target.base}"
    )


def test_kilo_global_scope_base_is_dot_kilo():
    target = resolve("kilo-code", scope="global")
    assert target.base == Path.home() / ".kilo", (
        f"kilo-code global-scope base must be ~/.kilo; got {target.base}"
    )


def test_kilo_host_name_is_unchanged(tmp_path, monkeypatch):
    """Per Issue #53 + remediation handoff: preserve logical host id.

    Only the filesystem path changes; the public host identifier
    `kilo-code` stays so existing scripts, CI invocations, and
    `qor-logic install --host kilo-code` keep working.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("QORLOGIC_PROJECT_DIR", raising=False)
    target = resolve("kilo-code", scope="repo")
    assert target.name == "kilo-code", (
        f"host identifier must remain 'kilo-code'; got {target.name!r}"
    )


@pytest.mark.parametrize("scope", ["repo", "global"])
def test_kilo_skills_agents_dirs_resolve_under_dot_kilo(scope, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("QORLOGIC_PROJECT_DIR", raising=False)
    target = resolve("kilo-code", scope=scope)
    expected_root = (tmp_path if scope == "repo" else Path.home()) / ".kilo"
    assert target.install_map["skills/"] == expected_root / "skills", (
        f"skills dir must be {expected_root / 'skills'}; got "
        f"{target.install_map['skills/']}"
    )
    assert target.install_map["agents/"] == expected_root / "agents", (
        f"agents dir must be {expected_root / 'agents'}; got "
        f"{target.install_map['agents/']}"
    )
