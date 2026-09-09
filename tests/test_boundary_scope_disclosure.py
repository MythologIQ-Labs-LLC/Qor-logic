"""Phase 219 (GH #309 gap 2): a green boundary result must carry its own scope.

The terms overlay is gitignored on purpose -- a tracked denylist of private
identifiers in a public repository publishes the strings it exists to suppress.
So CI runs the four structural detectors only, and both identity-term leaks the
issue cites were invisible to it, correctly.

That cannot be fixed by scanning more. What can be fixed is that an unqualified
"0 findings" from CI and from a local run mean different things and currently
look identical. The scope travels with the result.
"""
from __future__ import annotations

import re
from pathlib import Path

from qor.scripts import publication_boundary_lint as lint


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "a.md").write_text("# Clean\n", encoding="utf-8")
    return root


def test_scope_reports_structural_only_without_overlay(tmp_path: Path):
    """No overlay present -- identity terms were not examined, and it says so."""
    result = lint.collect_findings(_repo(tmp_path), no_git=True, terms_file=None)

    assert result.scope == "structural", result.scope


def test_scope_reports_identity_when_overlay_present(tmp_path: Path):
    """Overlay present -- identity coverage is claimed only when it is real."""
    root = _repo(tmp_path)
    overlay = root / "terms.txt"
    overlay.write_text("AcmeInternal\n", encoding="utf-8")

    result = lint.collect_findings(root, no_git=True, terms_file=overlay)

    assert result.scope == "structural+identity", result.scope


def test_empty_overlay_is_structural_only(tmp_path: Path):
    """A present-but-empty overlay contributes no identity coverage.

    Claiming identity scope from an empty file would be the same false assurance
    the disclosure exists to prevent.
    """
    root = _repo(tmp_path)
    overlay = root / "terms.txt"
    overlay.write_text("# only comments\n\n", encoding="utf-8")

    assert lint.collect_findings(root, no_git=True, terms_file=overlay).scope == "structural"


def test_scope_is_machine_readable(tmp_path: Path):
    """The seal records the scope; it must not have to parse prose to do it."""
    result = lint.collect_findings(_repo(tmp_path), no_git=True, terms_file=None)

    assert isinstance(result.scope, str)
    assert isinstance(result.findings, list)
    assert result.scope in ("structural", "structural+identity")


# Phase 283 (GH #432): the doctrine states the scheduled scan is advisory but
# never stated what a consumer must do with the exit code carrying that report,
# and that omission is what let a consumer read an advisory signal as a gate.
# This binds the written rule to the one live consumer, so drift on either side
# fails rather than accumulating.

DOCTRINE = Path(__file__).resolve().parents[1] / "qor" / "references" / "doctrine-publication-boundary.md"
WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "nightly-health.yml"


def _doctrine_exit_dispositions() -> dict[str, str]:
    """Map each exit code the doctrine rules on to 'suppress' or 'route'."""
    text = DOCTRINE.read_text(encoding="utf-8")
    dispositions: dict[str, str] = {}
    for sentence in re.split(r"(?<=[.:])\s+", text):
        m = re.search(r"\bExit (\d)\b", sentence)
        if not m:
            continue
        if "suppress" in sentence.lower():
            dispositions[m.group(1)] = "suppress"
        elif "route" in sentence.lower():
            dispositions[m.group(1)] = "route"
    return dispositions


def _create_condition_boundary_codes() -> set[str]:
    text = WORKFLOW.read_text(encoding="utf-8")
    block = text[text.index("      - name: Create or update health issue"):]
    condition = re.search(r"^        if: (.+)$", block, re.MULTILINE).group(1)
    return set(re.findall(r"boundary_rc\s*==\s*'(\d)'", condition))


def test_the_doctrine_contract_and_the_workflow_condition_agree():
    dispositions = _doctrine_exit_dispositions()
    assert dispositions, (
        "the doctrine states no per-exit-code rule for a consumer of the "
        "scheduled scan; a consumer reading it cannot tell an advisory signal "
        "from a gate, which is the omission this phase repairs"
    )
    reports_on = _create_condition_boundary_codes()
    for code, disposition in sorted(dispositions.items()):
        if disposition == "route":
            assert code in reports_on, (
                f"doctrine routes exit {code} into the consumer's reporting path, "
                f"but the workflow does not report on it (reports on {sorted(reports_on)})"
            )
        else:
            assert code not in reports_on, (
                f"doctrine says a consumer suppresses exit {code}, but the workflow "
                f"opens an issue on it"
            )


def test_the_doctrine_rules_on_every_exit_code_the_scanner_returns():
    """A rule that omits a code leaves the next consumer to guess at it."""
    dispositions = _doctrine_exit_dispositions()
    assert set(dispositions) == {"1", "2"}, (
        "exit 1 and exit 2 each need an explicit disposition; exit 0 needs none "
        f"because nothing is reported on a clean scan (found: {sorted(dispositions)})"
    )
