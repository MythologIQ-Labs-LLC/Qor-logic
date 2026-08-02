"""Phase 207 (GH-less; audit entries #506/#507): declarable co-author policy.

The `Authored via [Qor-logic SDLC]` line is the attribution the doctrine exists
for and stays mandatory at every setting. The model `Co-Authored-By:` line
serves GitHub contributor-stats reporting, which is a convenience rather than a
governance guarantee, so whether it is REQUIRED is declarable per repository.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from qor.scripts.attribution import commit_trailer, message_has_full_trailer
from qor.scripts.attribution_policy import AttributionPolicy, resolve_policy

_MODEL = "Claude Opus 5 (1M context)"


def _write_config(root: Path, payload: dict) -> None:
    config_dir = root / ".qorlogic"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


# -------- the pure helper --------

def test_commit_trailer_omits_coauthor_when_policy_disables_it():
    relaxed = commit_trailer(_MODEL, model_coauthor=False)
    assert "Authored via" in relaxed and "Qor-logic" in relaxed
    assert "Co-Authored-By:" not in relaxed

    strict = commit_trailer(_MODEL)
    assert "Authored via" in strict and "Qor-logic" in strict
    assert f"Co-Authored-By: {_MODEL}" in strict


def test_message_has_full_trailer_accepts_framework_line_only_when_not_required():
    message = (
        "seal: phase 207 - attribution co-author policy\n\n"
        "\U0001F916 Authored via [Qor-logic SDLC](https://example.invalid) "
        "on [Claude Code](https://example.invalid)\n"
    )
    assert message_has_full_trailer(message, require_coauthor=False) is True
    assert message_has_full_trailer(message) is False


def test_message_has_full_trailer_still_rejects_missing_framework_line():
    """Relaxing the co-author requirement must never relax the framework one."""
    message = (
        "seal: phase 207 - attribution co-author policy\n\n"
        f"Co-Authored-By: {_MODEL} <noreply@anthropic.com>\n"
    )
    assert message_has_full_trailer(message, require_coauthor=False) is False
    assert message_has_full_trailer(message) is False


def test_seal_subject_without_phase_number_is_flagged_not_skipped():
    """An unparseable seal subject is in scope, not an accidental exemption."""
    from tests.test_attribution_tiered_usage import _seal_phase_in_scope

    assert _seal_phase_in_scope(None) is True
    assert _seal_phase_in_scope(48) is False
    assert _seal_phase_in_scope(207) is True


# -------- the policy resolver --------

def test_policy_defaults_to_requiring_coauthor_when_config_absent(tmp_path: Path):
    assert resolve_policy(tmp_path) == AttributionPolicy(model_coauthor=True)


def test_policy_reads_declared_false_from_config(tmp_path: Path):
    _write_config(tmp_path, {"attribution": {"model_coauthor": False}})
    assert resolve_policy(tmp_path).model_coauthor is False


def test_policy_tolerates_malformed_config(tmp_path: Path):
    """A corrupt config fails closed toward REQUIRING attribution."""
    config_dir = tmp_path / ".qorlogic"
    config_dir.mkdir(parents=True)
    (config_dir / "config.json").write_text("{not valid json", encoding="utf-8")
    assert resolve_policy(tmp_path).model_coauthor is True

    _write_config(tmp_path, {"attribution": "not-an-object"})
    assert resolve_policy(tmp_path).model_coauthor is True

    _write_config(tmp_path, {"attribution": {"model_coauthor": "false"}})
    assert resolve_policy(tmp_path).model_coauthor is True


# -------- the CLI gate --------

def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args], cwd=str(repo), check=True,
        capture_output=True, text=True,
    )


def _repo_with_framework_only_seal(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")
    (repo / "f.txt").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "f.txt")
    _git(
        repo, "commit", "-m",
        "seal: phase 207 - attribution co-author policy\n\n"
        "\U0001F916 Authored via [Qor-logic SDLC](https://example.invalid) "
        "on [Claude Code](https://example.invalid)",
    )
    return repo


def _run_check(repo: Path) -> int:
    return subprocess.run(
        [sys.executable, "-m", "qor.scripts.seal_trailer_check",
         "--commit", "HEAD", "--repo-root", str(repo)],
        capture_output=True, text=True,
    ).returncode


def test_seal_trailer_check_honors_declared_policy(tmp_path: Path):
    repo = _repo_with_framework_only_seal(tmp_path)

    assert _run_check(repo) == 1, "no config: co-author line is required"

    _write_config(repo, {"attribution": {"model_coauthor": False}})
    assert _run_check(repo) == 0, "declared policy: framework line suffices"


def test_seal_trailer_check_still_rejects_missing_framework_line(tmp_path: Path):
    repo = tmp_path / "repo2"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")
    (repo / "f.txt").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "f.txt")
    _git(repo, "commit", "-m", "seal: phase 207 - no framework line\n\nnothing here")
    _write_config(repo, {"attribution": {"model_coauthor": False}})

    assert _run_check(repo) == 1


@pytest.mark.parametrize("declared", [True, False])
def test_live_repo_policy_resolves_without_raising(declared: bool, tmp_path: Path):
    """The resolver never raises on a well-formed declaration of either value."""
    _write_config(tmp_path, {"attribution": {"model_coauthor": declared}})
    assert resolve_policy(tmp_path).model_coauthor is declared
