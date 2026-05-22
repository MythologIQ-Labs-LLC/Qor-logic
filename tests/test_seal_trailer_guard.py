"""Phase 85: tests for the seal-commit trailer guard (GH #96 FIX A)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from qor.scripts.attribution import commit_trailer, message_has_full_trailer

REPO_ROOT = Path(__file__).resolve().parent.parent

_FULL = commit_trailer("Claude Opus 4.7")
_COMPACT_ONLY = "Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
_AUTHORED_VIA_ONLY = (
    "\U0001F916 Authored via [Qor-logic SDLC](https://example/qor) "
    "on [Claude Code](https://example/cc)"
)


def test_message_has_full_trailer_accepts_full_trailer():
    assert message_has_full_trailer(f"seal: phase 85\n\n{_FULL}") is True


def test_message_has_full_trailer_rejects_compact_only():
    # The phase 82/83 defect shape: only the Co-Authored-By line.
    assert message_has_full_trailer(f"seal: phase 82\n\n{_COMPACT_ONLY}") is False


def test_message_has_full_trailer_rejects_missing_coauthor():
    assert message_has_full_trailer(f"seal: phase 85\n\n{_AUTHORED_VIA_ONLY}") is False


def test_message_has_full_trailer_accepts_lowercase_coauthor():
    msg = f"seal: phase 85\n\n{_AUTHORED_VIA_ONLY}\n\nCo-authored-by: X <e@e>"
    assert message_has_full_trailer(msg) is True


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=str(cwd), check=True,
                   capture_output=True, text=True,
                   encoding="utf-8", errors="replace")


def _tmp_repo_with_commit(tmp_path: Path, message: str) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init"], repo)
    _git(["config", "user.email", "t@example.com"], repo)
    _git(["config", "user.name", "Tester"], repo)
    _git(["commit", "--allow-empty", "-m", message], repo)
    return repo


def _run_cli(repo: Path, commit: str = "HEAD") -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "qor.scripts.seal_trailer_check",
         "--commit", commit, "--repo-root", str(repo)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(REPO_ROOT),
    )


def test_cli_exits_zero_on_compliant_seal_commit(tmp_path):
    repo = _tmp_repo_with_commit(tmp_path, f"seal: phase 85 - x\n\n{_FULL}")
    proc = _run_cli(repo)
    assert proc.returncode == 0


def test_cli_exits_nonzero_and_names_missing_part(tmp_path):
    repo = _tmp_repo_with_commit(tmp_path, f"seal: phase 82 - x\n\n{_COMPACT_ONLY}")
    proc = _run_cli(repo)
    assert proc.returncode == 1
    assert "Authored via" in proc.stderr
    assert "re-run /qor-substantiate" in proc.stderr


def test_cli_rejects_dash_prefixed_commit(tmp_path):
    # `--commit=-x` lets argparse accept the dash-leading value, so it reaches
    # the script's own leading-dash guard (the bare `--commit -x` form is
    # rejected earlier by argparse). Either way a dash value never hits git.
    repo = _tmp_repo_with_commit(tmp_path, f"seal: phase 85 - x\n\n{_FULL}")
    proc = subprocess.run(
        [sys.executable, "-m", "qor.scripts.seal_trailer_check",
         "--commit=-x", "--repo-root", str(repo)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 1
    assert "must not start with '-'" in proc.stderr
