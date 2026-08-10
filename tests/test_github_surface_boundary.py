"""Phase 211: the publication boundary covers the GitHub surface.

The tracked-surface control scans `git ls-files`. Issue and pull-request
titles, bodies, and comments are not files, so they were never examined -- the
surface was cleaned by hand twice, and one issue title survived a body-only
anonymization performed the same day.

No test here performs network I/O: `scan_surface` is pure over already-fetched
items, and the CLI takes an injectable fetcher.
"""
from __future__ import annotations

import pytest

from qor.scripts.github_surface import SurfaceItem, main, scan_surface

_TERMS = ["SomeProduct"]


def _item(kind="issue", number=7, field="body", text=""):
    return SurfaceItem(kind=kind, number=number, field=field, text=text)


# -------- scanning --------

def test_scans_title_and_body_and_comments():
    leak = "see https://github.com/OtherOwner/other-repo for context\n"  # boundary-lint: ok=detector-own-fixture
    for field in ("title", "body", "comment"):
        findings = scan_surface([_item(field=field, text=leak)], terms=[])
        assert len(findings) == 1, (field, findings)
        assert "issue" in findings[0] and "#7" in findings[0], findings[0]
        assert field in findings[0], f"reference must name the field; got {findings[0]!r}"


def test_reports_clean_for_a_surface_with_no_findings():
    items = [
        _item(text="a neutral sentence citing qor/scripts/x.py\n"),
        _item(field="title", text="Fix the resolver\n"),
        _item(text="see https://github.com/MythologIQ-Labs-LLC/Qor-logic/issues/1\n"),
    ]
    assert scan_surface(items, terms=[]) == []


def test_honors_the_exemption_marker_per_line():
    text = (
        "https://github.com/OtherOwner/other-repo  <!-- boundary-lint: ok=documented -->\n"
        "https://github.com/OtherOwner/other-repo unmarked\n"  # boundary-lint: ok=detector-own-fixture
    )
    findings = scan_surface([_item(text=text)], terms=[])
    assert len(findings) == 1, findings
    assert ":2:" in findings[0], f"must name the unmarked line; got {findings[0]!r}"


def test_applies_identity_terms_when_supplied():
    text = "SomeProduct and https://github.com/OtherOwner/other-repo\n"  # boundary-lint: ok=detector-own-fixture

    structural_only = scan_surface([_item(text=text)], terms=[])
    assert len(structural_only) == 1
    assert "identity term" not in structural_only[0]

    with_terms = scan_surface([_item(text=text)], terms=_TERMS)
    assert len(with_terms) == 2
    assert any("identity term: SomeProduct" in f for f in with_terms)


# -------- the CLI, with an injected fetcher --------

def _fetcher(items):
    def fetch(repo):  # noqa: ARG001 - signature parity with the real fetcher
        return items
    return fetch


def test_cli_reports_findings_from_an_injected_fetcher(capsys):
    items = [_item(text="https://github.com/OtherOwner/other-repo\n")]  # boundary-lint: ok=detector-own-fixture
    rc = main(["--repo", "owner/name"], fetcher=_fetcher(items))
    out = capsys.readouterr().out
    assert rc == 1
    assert "OtherOwner/other-repo" in out


def test_cli_exit_zero_when_surface_is_clean(capsys):
    items = [_item(text="neutral prose\n")]
    rc = main(["--repo", "owner/name"], fetcher=_fetcher(items))
    assert rc == 0
    assert "0 finding" in capsys.readouterr().out


def test_cli_reports_which_detector_classes_ran(tmp_path, capsys):
    """A clean report must not overstate what it actually checked."""
    items = [_item(text="neutral prose\n")]

    main(["--repo", "owner/name"], fetcher=_fetcher(items))
    assert "structural only" in capsys.readouterr().out

    terms_file = tmp_path / "terms.txt"
    terms_file.write_text("SomeProduct\n# a comment\n", encoding="utf-8")
    main(["--repo", "owner/name", "--terms-file", str(terms_file)],
         fetcher=_fetcher(items))
    assert "terms overlay: 1 terms" in capsys.readouterr().out


def test_fetch_failure_is_reported_not_swallowed(capsys):
    """A surface that could not be read is never reported clean."""
    def boom(repo):  # noqa: ARG001
        raise RuntimeError("gh exited 1: HTTP 401")

    rc = main(["--repo", "owner/name"], fetcher=boom)
    combined = capsys.readouterr()
    assert rc != 0
    assert "401" in (combined.out + combined.err), combined
    assert "0 finding" not in combined.out, "must not claim a clean surface"


def test_scan_surface_rejects_a_non_surface_item():
    with pytest.raises(AttributeError):
        scan_surface(["not an item"], terms=[])


# -------- machine-authored dependency PRs --------

def test_bot_authored_items_are_not_scanned():
    """A dependency bump names the upstream repo it bumps; that is its purpose.

    Reuses the `pr_citation_lint` exemption reasoning -- machine authors file
    dependency and automation PRs -- and covers both login forms GitHub emits:
    the `dependabot[bot]` trailer form and the `app/dependabot` form `gh` returns.
    """
    from qor.scripts.github_surface import is_machine_author

    assert is_machine_author("dependabot[bot]") is True
    assert is_machine_author("app/dependabot") is True
    assert is_machine_author("github-actions[bot]") is True
    assert is_machine_author("Knapp-Kevin") is False
    assert is_machine_author("") is False


def test_scan_skips_items_from_machine_authors():
    leak = "bumps https://github.com/pypa/gh-action-pypi-publish from 1 to 2\n"  # boundary-lint: ok=detector-own-fixture
    human = SurfaceItem("pr", 1, "body", leak, author="a-human")
    bot = SurfaceItem("pr", 2, "body", leak, author="app/dependabot")

    assert len(scan_surface([human], terms=[])) == 1
    assert scan_surface([bot], terms=[]) == []
    assert len(scan_surface([human, bot], terms=[])) == 1
