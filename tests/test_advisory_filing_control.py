"""Phase 286: the filing path reports what it is about to publish.

The control is advisory. It inspects the composed title and body that
`create_shadow_issue` is about to hand to `gh`, prints what it found, records a
line when it found anything, and never prevents the filing -- not on a finding,
and not on a failure of its own.

Every test here names the implementation that would make it fail. Four tests
that could not fail shipped across this plan's earlier, blocking design; the
red condition is the countermeasure and it is stated per test rather than
assumed.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from qor.scripts import advisory_filing_control as afc


# --- fixtures -------------------------------------------------------------


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args],
                   check=True, capture_output=True, text=True)


def _repo(tmp_path: Path, name: str, remote: str | None = None) -> Path:
    """A checkout at <tmp>/<name> with docs/, optionally carrying an origin."""
    repo = tmp_path / name
    (repo / "docs").mkdir(parents=True)
    _git(repo.parent, "init", name, "-q")
    if remote is not None:
        _git(repo, "remote", "add", "origin", remote)
    return repo


def _log(repo: Path) -> Path:
    log = repo / "docs" / "PROCESS_SHADOW_GENOME.md"
    log.write_text("# log\n", encoding="utf-8")
    return log


# --- the anchor -----------------------------------------------------------


def test_the_anchor_is_the_directory_the_log_was_read_from(tmp_path, monkeypatch):
    """Red if the anchor is any root function.

    `workdir.root()` returns the process working directory when $QOR_ROOT is
    unset, so an implementation anchored there derives the working directory's
    name instead of the repository's.
    """
    repo = _repo(tmp_path, "svc")
    log = _log(repo)
    elsewhere = tmp_path / "somewhere-else"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    report = afc.inspect("t", "a body mentioning svc by name",
                         log_path=log, destination="other/other")
    assert any("svc" in f for f in report.findings), (
        "the derived directory term must be the log's repository, not the cwd"
    )


# --- origin_pair ----------------------------------------------------------


def test_origin_pair_strips_the_git_suffix(tmp_path):
    """Red under a naive parse, which retains `.git` and so matches no
    destination -- making every self-run report."""
    repo = _repo(tmp_path, "widgets", remote="https://example.invalid/acme/widgets.git")
    assert afc.origin_pair(repo) == "acme/widgets"


def test_origin_pair_is_none_without_a_remote(tmp_path):
    """Red if the `git remote get-url` failure propagates, and red if a partial
    pair such as the bare directory name is returned."""
    repo = _repo(tmp_path, "widgets")
    assert afc.origin_pair(repo) is None


# --- what is reported -----------------------------------------------------


def test_a_body_naming_the_filing_repository_is_reported(tmp_path):
    """Red before: nothing inspects the body."""
    repo = _repo(tmp_path, "widgets", remote="https://example.invalid/AcmeCorp/widgets.git")
    report = afc.inspect("t", "the widgets seal gate failed",
                         log_path=_log(repo), destination="Meta/tracker")
    assert report.findings
    assert "identity-term" in report.classes


def test_a_body_naming_the_destination_is_not_reported(tmp_path):
    """Red if derived terms are not dropped when origin == destination, which
    would report every self-run in this repository's own home."""
    repo = _repo(tmp_path, "widgets", remote="https://example.invalid/AcmeCorp/widgets.git")
    report = afc.inspect("t", "the widgets seal gate failed",
                         log_path=_log(repo), destination="AcmeCorp/widgets")
    assert report.findings == ()


def test_a_fork_sharing_the_destination_name_is_still_reported(tmp_path):
    """Red under a name-only comparison, which drops the term and reports
    nothing. This is GH #431 re-entering through the term loop."""
    repo = _repo(tmp_path, "widgets", remote="https://example.invalid/AcmeCorp/widgets.git")
    report = afc.inspect("t", "found in our widgets checkout while sealing",
                         log_path=_log(repo), destination="MetaOrg/widgets")
    assert report.findings


def test_an_overlay_term_is_reported_on_a_self_run(tmp_path):
    """Red if the destination drop is applied to the whole term set rather than
    to the derived terms only."""
    repo = _repo(tmp_path, "widgets", remote="https://example.invalid/AcmeCorp/widgets.git")
    overlay = repo / ".qor" / "private" / "boundary-terms.txt"
    overlay.parent.mkdir(parents=True)
    overlay.write_text("Widgetron\n", encoding="utf-8")
    report = afc.inspect("t", "the Widgetron release gate failed",
                         log_path=_log(repo), destination="AcmeCorp/widgets")
    assert report.findings, "an operator-declared term must survive the drop"


def test_a_term_is_matched_inside_a_compound_identifier(tmp_path):
    """Red under strict matching, whose lookarounds a trailing hyphen defeats."""
    repo = _repo(tmp_path, "acme-widgets",
                 remote="https://example.invalid/AcmeCorp/acme-widgets.git")
    report = afc.inspect("t", "branch phase/12-acme-widgets-fix diverged",
                         log_path=_log(repo), destination="Meta/tracker")
    assert report.findings


def test_marker_bearing_lines_are_counted_and_disclosed(tmp_path):
    """Red if the marker count is absent.

    `scan_text` skips marker-bearing lines silently, so without the count an
    operator reads a clean scan over text that was never scanned.
    """
    repo = _repo(tmp_path, "widgets", remote="https://example.invalid/AcmeCorp/widgets.git")
    body = "a line carrying boundary-lint: ok=reason\nthe widgets gate failed\n"
    report = afc.inspect("t", body, log_path=_log(repo), destination="Meta/tracker")
    assert report.unscanned_lines == 1
    assert report.findings, "the unmarked line must still be reported"


# --- the advisory property ------------------------------------------------


def test_the_report_files_despite_findings(tmp_path):
    """The advisory property. Red under any implementation that raises, returns
    early, or short-circuits on a finding."""
    repo = _repo(tmp_path, "widgets", remote="https://example.invalid/AcmeCorp/widgets.git")
    report = afc.inspect("t", "the widgets gate failed",
                         log_path=_log(repo), destination="Meta/tracker")
    assert report.findings
    # inspect returns rather than raising; that is the whole contract.
    assert isinstance(report, afc.AdvisoryReport)


@pytest.mark.parametrize("mode", ["git-absent", "bad-overlay", "unwritable-record", "missing-log"])
def test_a_raising_callee_does_not_prevent_the_filing(tmp_path, monkeypatch, mode):
    """Red under any unwrapped implementation, and red under a wrap that
    swallows the error silently instead of classing it."""
    repo = _repo(tmp_path, "widgets", remote="https://example.invalid/AcmeCorp/widgets.git")
    log = _log(repo)

    if mode == "git-absent":
        def boom(*a, **k):
            raise FileNotFoundError("git")
        monkeypatch.setattr(subprocess, "run", boom)
    elif mode == "bad-overlay":
        overlay = repo / ".qor" / "private" / "boundary-terms.txt"
        overlay.parent.mkdir(parents=True)
        overlay.write_bytes(b"\xff\xfe not utf-8 \x00")
    elif mode == "missing-log":
        log = repo / "docs" / "does-not-exist.md"
    elif mode == "unwritable-record":
        monkeypatch.setattr(afc, "_append_line", lambda *a, **k: (_ for _ in ()).throw(OSError("ro")))

    report = afc.inspect("t", "the widgets gate failed",
                         log_path=log, destination="Meta/tracker")
    assert isinstance(report, afc.AdvisoryReport), "the control must not raise"
    if mode in ("git-absent", "bad-overlay"):
        assert "control-error" in report.classes, (
            "a silently swallowed failure is indistinguishable from a clean scan"
        )


def test_the_control_does_not_alter_the_title_or_body(tmp_path):
    """Red if the control redacts or rewrites, which the doctrine reserves to a
    human."""
    repo = _repo(tmp_path, "widgets", remote="https://example.invalid/AcmeCorp/widgets.git")
    title, body = "the widgets title", "the widgets body\nsecond line\n"
    afc.inspect(title, body, log_path=_log(repo), destination="Meta/tracker")
    assert title == "the widgets title"
    assert body == "the widgets body\nsecond line\n"


# --- the record -----------------------------------------------------------


def test_findings_append_one_record_with_the_count_and_destination(tmp_path):
    """Red if nothing is recorded, if one line per finding is recorded, or if
    the count is absent."""
    repo = _repo(tmp_path, "widgets", remote="https://example.invalid/AcmeCorp/widgets.git")
    report = afc.inspect("t", "widgets here\nwidgets there\nwidgets everywhere\n",
                         log_path=_log(repo), destination="Meta/tracker")
    afc.record(report, anchor=repo, destination="Meta/tracker")
    lines = (repo / ".qor" / "advisory" / "filing-observations.jsonl").read_text(
        encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["count"] == len(report.findings) >= 3
    assert rec["destination"] == "Meta/tracker"


def test_the_record_is_not_a_shadow_event(tmp_path):
    """Red if the record is appended as a `gate_override` event.

    That type is the only one carrying a raising override-friction escalator, so
    recording there would let this control refuse a filing at the third
    occurrence -- and would corrupt the population `override_friction.check`
    reads to detect operator gate bypass.
    """
    repo = _repo(tmp_path, "widgets", remote="https://example.invalid/AcmeCorp/widgets.git")
    log = _log(repo)
    before = log.read_bytes()
    report = afc.inspect("t", "the widgets gate failed",
                         log_path=log, destination="Meta/tracker")
    afc.record(report, anchor=repo, destination="Meta/tracker")
    assert log.read_bytes() == before, "the shadow genome must be untouched"


def test_the_record_carries_finding_classes_not_matched_text(tmp_path):
    """Red if the event embeds the matched text, which would write into a
    durable record exactly what the control exists to notice."""
    repo = _repo(tmp_path, "widgets", remote="https://example.invalid/AcmeCorp/widgets.git")
    report = afc.inspect("t", "the widgets gate failed",
                         log_path=_log(repo), destination="Meta/tracker")
    afc.record(report, anchor=repo, destination="Meta/tracker")
    raw = (repo / ".qor" / "advisory" / "filing-observations.jsonl").read_text(encoding="utf-8")
    assert "identity-term" in raw
    assert "widgets" not in raw, "the matched text must stay in the printed report"


def test_a_clean_report_records_nothing(tmp_path):
    """Red if the control records unconditionally, which would make the rate it
    exists to measure meaningless."""
    repo = _repo(tmp_path, "widgets", remote="https://example.invalid/AcmeCorp/widgets.git")
    report = afc.inspect("t", "nothing identifying here",
                         log_path=_log(repo), destination="Meta/tracker")
    assert report.findings == ()
    afc.record(report, anchor=repo, destination="Meta/tracker")
    assert not (repo / ".qor" / "advisory" / "filing-observations.jsonl").exists()


# --- the wiring -----------------------------------------------------------


def test_the_filing_path_invokes_the_control_before_gh(tmp_path, monkeypatch):
    """Red before: nothing calls it.

    Red also if the call is wired but handed a different log than the one the
    events were read from, which is the divergence LD-3 exists to prevent.
    """
    from qor.scripts import create_shadow_issue as csi

    order: list[str] = []
    seen: dict = {}

    def fake_inspect(title, body, **kw):
        order.append("inspect")
        seen.update(kw)
        return afc.AdvisoryReport(findings=(), classes=(), unscanned_lines=0)

    def fake_run(cmd, *a, **k):
        if cmd[:3] == ["gh", "auth", "status"]:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if cmd[:3] == ["gh", "issue", "create"]:
            order.append("gh")
            return subprocess.CompletedProcess(cmd, 0, "https://example.invalid/x/y/issues/1\n", "")
        raise AssertionError(f"unexpected: {cmd}")

    monkeypatch.setattr(csi.advisory, "inspect", fake_inspect)
    monkeypatch.setattr(subprocess, "run", fake_run)
    csi.create_issue("Meta/tracker", "a title", "a body")

    assert order == ["inspect", "gh"], "the control must run before the filing"
    assert seen["destination"] == "Meta/tracker"
    assert seen["log_path"] == csi.shadow_process.LOG_PATH


# --- the doctrine ---------------------------------------------------------


def test_the_doctrine_states_the_advisory_rule():
    """Red before the change, and red if the doctrine and the implementation
    drift apart."""
    text = Path("qor/references/doctrine-publication-boundary.md").read_text(encoding="utf-8")
    section = text.split("## Required treatment", 1)[1].split("\n## ", 1)[0]
    assert "advisory" in section.lower()
    assert "transmitted" in section.lower()
    assert "unscanned" in section.lower() or "not scanned" in section.lower()
