"""Phase 105: tests for the dependency-admission cooling-period lint."""
from __future__ import annotations

import io
import json
import textwrap
from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest

from qor.scripts import dependency_admission_lint as lint


def _make_pypi_response(upload_time_iso: str) -> dict:
    return {"urls": [{"upload_time_iso_8601": upload_time_iso}]}


def _mock_urlopen(mapping: dict[str, dict]):
    """Returns a urlopen replacement that maps URL -> JSON response, with optional failures.

    Mapping value can be either a dict (returned as JSON) or an Exception subclass instance
    (raised when urlopen is called).
    """
    def opener(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else req
        if url not in mapping:
            raise lint.urllib.error.URLError(f"unmapped URL: {url}")
        value = mapping[url]
        if isinstance(value, BaseException):
            raise value
        ctx = mock.MagicMock()
        ctx.__enter__.return_value = io.BytesIO(json.dumps(value).encode("utf-8"))
        ctx.__exit__.return_value = False
        return ctx
    return opener


@pytest.fixture
def fixed_now(monkeypatch):
    """Pin the lint's notion of 'now' so age calculations are deterministic."""
    fixed = datetime(2026, 5, 25, 0, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(lint, "_now_utc", lambda: fixed)
    return fixed


def test_lint_emits_no_violation_when_all_bumps_outside_window(monkeypatch, fixed_now, capsys):
    """Bumps with age >= 14 days -> exit 0, no violation stderr."""
    base_lockfile = "build==1.4.0 \\\n    --hash=sha256:" + "a" * 64 + "\n"
    current_lockfile = "build==1.5.0 \\\n    --hash=sha256:" + "b" * 64 + "\n"
    upload_time = (fixed_now - timedelta(days=30)).isoformat().replace("+00:00", "Z")

    monkeypatch.setattr(
        lint.urllib.request, "urlopen",
        _mock_urlopen({
            "https://pypi.org/pypi/build/1.5.0/json": _make_pypi_response(upload_time),
        }),
    )

    result = lint.run_lint(
        current_lockfile_text=current_lockfile,
        base_lockfile_text=base_lockfile,
        ledger_text="",
    )

    assert result.exit_code == 0
    assert result.violations == []
    assert any(b.status == "clean" for b in result.bumps)


def test_lint_emits_violation_when_within_window_and_no_override(monkeypatch, fixed_now):
    """Bump with age < 14 days and no matching override -> exit 1, violation reported."""
    base_lockfile = ""
    current_lockfile = "fresh-pkg==9.9.9 \\\n    --hash=sha256:" + "c" * 64 + "\n"
    upload_time = (fixed_now - timedelta(days=5)).isoformat().replace("+00:00", "Z")

    monkeypatch.setattr(
        lint.urllib.request, "urlopen",
        _mock_urlopen({
            "https://pypi.org/pypi/fresh-pkg/9.9.9/json": _make_pypi_response(upload_time),
        }),
    )

    result = lint.run_lint(
        current_lockfile_text=current_lockfile,
        base_lockfile_text=base_lockfile,
        ledger_text="",
    )

    assert result.exit_code == 1
    assert len(result.violations) == 1
    assert result.violations[0].name == "fresh-pkg"
    assert result.violations[0].new_version == "9.9.9"


def test_lint_clears_violation_when_override_entry_present(monkeypatch, fixed_now):
    """Within-window bump WITH matching override ledger entry -> exit 0, bump marked override."""
    base_lockfile = ""
    current_lockfile = "fresh-pkg==9.9.9 \\\n    --hash=sha256:" + "c" * 64 + "\n"
    upload_time = (fixed_now - timedelta(days=5)).isoformat().replace("+00:00", "Z")
    ledger = textwrap.dedent(f"""\
        ### Entry #999: IMPLEMENTATION

        **Timestamp**: 2026-05-24T00:00:00Z

        **Dependency admission override**: fresh-pkg@9.9.9; upload_age_days=5; justification=CVE-2026-9999 emergency patch.

        ---
        """)

    monkeypatch.setattr(
        lint.urllib.request, "urlopen",
        _mock_urlopen({
            "https://pypi.org/pypi/fresh-pkg/9.9.9/json": _make_pypi_response(upload_time),
        }),
    )

    result = lint.run_lint(
        current_lockfile_text=current_lockfile,
        base_lockfile_text=base_lockfile,
        ledger_text=ledger,
    )

    assert result.exit_code == 0
    assert result.violations == []
    assert any(b.name == "fresh-pkg" and b.status == "override" for b in result.bumps)


def test_lint_handles_pypi_network_failure_with_exit_2(monkeypatch, fixed_now):
    """Three consecutive PyPI failures -> exit 2, distinct from violation exit 1."""
    base_lockfile = ""
    current_lockfile = "ghost-pkg==1.0.0 \\\n    --hash=sha256:" + "d" * 64 + "\n"

    monkeypatch.setattr(
        lint.urllib.request, "urlopen",
        _mock_urlopen({
            "https://pypi.org/pypi/ghost-pkg/1.0.0/json": lint.urllib.error.URLError("simulated network failure"),
        }),
    )
    monkeypatch.setattr(lint.time, "sleep", lambda _s: None)  # don't actually sleep in tests

    result = lint.run_lint(
        current_lockfile_text=current_lockfile,
        base_lockfile_text=base_lockfile,
        ledger_text="",
    )

    assert result.exit_code == 2
    assert any("ghost-pkg" in err for err in result.network_errors)


def test_lint_handles_pre_phase102_base_with_no_lockfile(monkeypatch, fixed_now):
    """When base lockfile doesn't exist (pre-Phase-102 base ref), treat base as empty."""
    current_lockfile = "build==1.5.0 \\\n    --hash=sha256:" + "e" * 64 + "\n"
    upload_time = (fixed_now - timedelta(days=30)).isoformat().replace("+00:00", "Z")

    monkeypatch.setattr(
        lint.urllib.request, "urlopen",
        _mock_urlopen({
            "https://pypi.org/pypi/build/1.5.0/json": _make_pypi_response(upload_time),
        }),
    )

    # base_lockfile_text=None signals "lockfile didn't exist at base"
    result = lint.run_lint(
        current_lockfile_text=current_lockfile,
        base_lockfile_text=None,
        ledger_text="",
    )

    # All current entries count as new (old_version=None); but age is outside window so exit 0
    assert result.exit_code == 0
    assert len(result.bumps) == 1
    assert result.bumps[0].name == "build"
    assert result.bumps[0].old_version is None


# --- Phase 106: PR-label override + pyproject coverage -----------------------


def test_lint_pr_label_override_clears_within_window(monkeypatch, fixed_now):
    """`dep-admit-override` label on the PR clears a within-window admission."""
    base_lockfile = ""
    current_lockfile = "fresh-pkg==9.9.9 \\\n    --hash=sha256:" + "c" * 64 + "\n"
    upload_time = (fixed_now - timedelta(days=5)).isoformat().replace("+00:00", "Z")

    monkeypatch.setattr(
        lint.urllib.request, "urlopen",
        _mock_urlopen({
            "https://pypi.org/pypi/fresh-pkg/9.9.9/json": _make_pypi_response(upload_time),
        }),
    )

    # Simulate CI context with the override label present.
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REPOSITORY", "MythologIQ-Labs-LLC/Qor-logic")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/123/merge")

    class _MockGhResult:
        returncode = 0
        stdout = '{"labels": [{"name": "dep-admit-override"}]}'
        stderr = ""

    def _mock_subprocess_run(argv, **kwargs):
        assert argv[0] == "gh"
        assert "pr" in argv and "view" in argv
        return _MockGhResult()

    monkeypatch.setattr(lint.subprocess, "run", _mock_subprocess_run)

    result = lint.run_lint(
        current_lockfile_text=current_lockfile,
        base_lockfile_text=base_lockfile,
        ledger_text="",
    )

    assert result.exit_code == 0
    assert result.violations == []
    assert any(b.name == "fresh-pkg" and b.status == "override" for b in result.bumps)


def test_lint_pr_label_query_fails_open_to_ledger_only(monkeypatch, fixed_now, capsys):
    """gh CLI failure -> stderr fallback note + lint continues with ledger-only check."""
    base_lockfile = ""
    current_lockfile = "fresh-pkg==9.9.9 \\\n    --hash=sha256:" + "c" * 64 + "\n"
    upload_time = (fixed_now - timedelta(days=5)).isoformat().replace("+00:00", "Z")

    monkeypatch.setattr(
        lint.urllib.request, "urlopen",
        _mock_urlopen({
            "https://pypi.org/pypi/fresh-pkg/9.9.9/json": _make_pypi_response(upload_time),
        }),
    )

    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REPOSITORY", "MythologIQ-Labs-LLC/Qor-logic")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/123/merge")

    def _mock_subprocess_failure(argv, **kwargs):
        raise lint.subprocess.CalledProcessError(returncode=1, cmd=argv, stderr="network glitch")

    monkeypatch.setattr(lint.subprocess, "run", _mock_subprocess_failure)

    result = lint.run_lint(
        current_lockfile_text=current_lockfile,
        base_lockfile_text=base_lockfile,
        ledger_text="",  # no ledger override
    )

    # Lint continues with META_LEDGER-only check; no override -> violation
    assert result.exit_code == 1
    assert len(result.violations) == 1

    captured = capsys.readouterr()
    assert "PR label query failed" in captured.err
    assert "META_LEDGER" in captured.err


def test_lint_pyproject_exact_pin_within_window_triggers_violation(monkeypatch, fixed_now):
    """Synthetic pyproject diff with a within-window `==`-pinned entry -> exit 1."""
    upload_time = (fixed_now - timedelta(days=3)).isoformat().replace("+00:00", "Z")
    monkeypatch.setattr(
        lint.urllib.request, "urlopen",
        _mock_urlopen({
            "https://pypi.org/pypi/freshlib/2.0.0/json": _make_pypi_response(upload_time),
        }),
    )

    current_pyproject = textwrap.dedent("""\
        [project]
        name = "demo"
        version = "1.0"
        dependencies = ["freshlib==2.0.0"]
        """)
    base_pyproject = textwrap.dedent("""\
        [project]
        name = "demo"
        version = "1.0"
        dependencies = []
        """)

    result = lint.run_lint(
        current_lockfile_text="",
        base_lockfile_text="",
        ledger_text="",
        current_pyproject_text=current_pyproject,
        base_pyproject_text=base_pyproject,
    )

    assert result.exit_code == 1
    assert len(result.violations) == 1
    assert result.violations[0].name == "freshlib"
    assert result.violations[0].new_version == "2.0.0"


# --- Phase 107 D-107.3: range-pin lower-bound coverage in run_lint ----------


def test_lint_pyproject_range_pin_within_window_triggers_violation(monkeypatch, fixed_now):
    """`>=X.Y.Z` lower bound within 14 days -> violation."""
    upload_time = (fixed_now - timedelta(days=3)).isoformat().replace("+00:00", "Z")
    monkeypatch.setattr(
        lint.urllib.request, "urlopen",
        _mock_urlopen({
            "https://pypi.org/pypi/freshrange/3.0.0/json": _make_pypi_response(upload_time),
        }),
    )

    current_pyproject = textwrap.dedent("""\
        [project]
        name = "demo"
        version = "1.0"
        dependencies = ["freshrange>=3.0.0"]
        """)
    base_pyproject = textwrap.dedent("""\
        [project]
        name = "demo"
        version = "1.0"
        dependencies = []
        """)

    result = lint.run_lint(
        current_lockfile_text="",
        base_lockfile_text="",
        ledger_text="",
        current_pyproject_text=current_pyproject,
        base_pyproject_text=base_pyproject,
    )

    assert result.exit_code == 1
    assert len(result.violations) == 1
    assert result.violations[0].name == "freshrange"
    assert result.violations[0].new_version == "3.0.0"
