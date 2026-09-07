"""Phase 172: structural publication-boundary lint tests.

The lint enforces qor/references/doctrine-publication-boundary.md without
itself carrying any outside identity: structural patterns (absolute local
path shapes; foreign GitHub URLs; cross-repo issue shapes) plus an OPTIONAL
operator-local, gitignored terms file for identity terms.
"""
from __future__ import annotations

from pathlib import Path

from qor.scripts import publication_boundary_lint as pbl


def _run(tmp_path: Path, files: dict[str, str], terms: str | None = None) -> tuple[int, str]:
    import io
    from contextlib import redirect_stdout

    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    argv = ["--repo-root", str(tmp_path), "--no-git"]
    if terms is not None:
        tf = tmp_path / "terms.txt"
        tf.write_text(terms, encoding="utf-8")
        argv += ["--terms-file", str(tf)]
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = pbl.main(argv)
    return rc, buf.getvalue()


def test_flags_absolute_local_paths(tmp_path):
    rc, out = _run(tmp_path, {"docs/a.md": "see F:/SomeWorkspace/tool.py and /Users/dev/repo/x.py\n"})  # boundary-lint: ok=detector-own-fixture
    assert rc == 1
    assert "docs/a.md" in out.replace("\\", "/")
    assert out.count("[boundary]") == 2


def test_flags_foreign_github_urls_not_self(tmp_path):
    own = "https://github.com/MythologIQ-Labs-LLC/Qor-logic/issues/1"
    foreign = "https://github.com/other-org/other-repo/pull/2"  # boundary-lint: ok=detector-own-fixture
    rc, out = _run(tmp_path, {"docs/b.md": f"{own}\n{foreign}\n"})
    assert rc == 1
    assert "other-org/other-repo" in out
    assert "Qor-logic/issues/1" not in out


def test_flags_cross_repo_issue_shape(tmp_path):
    rc, out = _run(tmp_path, {"docs/c.md": "fixed in OtherRepo#123 but relates to #45 here\n"})  # boundary-lint: ok=detector-own-fixture
    assert rc == 1
    assert "OtherRepo#123" in out  # boundary-lint: ok=detector-own-fixture
    assert out.count("[boundary]") == 1  # bare #45 self-reference passes


def test_local_terms_file_overlay(tmp_path):
    files = {"docs/d.md": "the SecretSibling repo pattern\n"}
    rc, _ = _run(tmp_path, dict(files))
    assert rc == 0  # structural patterns alone do not know identity terms
    rc, out = _run(tmp_path, dict(files), terms="SecretSibling\n# comment line\n")
    assert rc == 1
    assert "SecretSibling" in out


def test_exit_codes(tmp_path):
    rc, out = _run(tmp_path, {"docs/clean.md": "a neutral sentence citing qor/scripts/x.py\n"})
    assert rc == 0
    assert "0 finding(s)" in out


def test_vendor_tree_is_a_declared_carve_out(tmp_path):
    """`qor/vendor/` third-party attribution is granted by doctrine, not scanned."""
    rc, out = _run(
        tmp_path,
        {"qor/vendor/skills/x/SOURCE.yml": "upstream: https://github.com/Other/thing\n"},  # boundary-lint: ok=detector-own-fixture
    )
    assert rc == 0, out
    assert "[boundary]" not in out

    rc, out = _run(
        tmp_path,
        {"qor/scripts/x.md": "upstream: https://github.com/Other/thing\n"},  # boundary-lint: ok=detector-own-fixture
    )
    assert rc == 1, "the same content outside the carve-out is still reported"


# --- Phase 268 (part of GH #431): a self-reference is not a cross-repo one ----
#
# `_CROSS_ISSUE_RE` matched any `Repo#123` shape, including references to the  # boundary-lint: ok=detector-own-fixture
# repository being scanned. Measured on the live GitHub surface, 5 of 17
# cross-repo issue-shape findings named Qor-logic itself. Those cannot be
# remediated -- naming your own issue is what a cross-reference is for -- so the
# detector reported findings nobody could clear, which is the failure mode
# `doctrine-publication-boundary.md:93-95` records for this control before
# Phase 208. The doctrine permits them outright at `:31`.

def test_qualified_self_reference_is_not_a_cross_repo_finding(tmp_path):
    rc, out = _run(tmp_path, {"docs/a.md": "fixed in Qor-logic#357\n"})
    assert rc == 0, out
    assert "[boundary]" not in out


def test_owner_qualified_self_reference_is_not_a_cross_repo_finding(tmp_path):
    rc, out = _run(tmp_path, {"docs/b.md": "see MythologIQ-Labs-LLC/Qor-logic#357\n"})
    assert rc == 0, out
    assert "[boundary]" not in out


def test_a_foreign_repo_issue_shape_is_still_a_finding(tmp_path):
    """Green before Phase 268; pins that the skip did not disable the detector."""
    rc, out = _run(tmp_path, {"docs/c.md": "fixed in OtherRepo#123\n"})  # boundary-lint: ok=detector-own-fixture
    assert rc == 1
    assert "OtherRepo#123" in out  # boundary-lint: ok=detector-own-fixture


def test_a_sibling_repo_whose_name_extends_this_one_is_still_a_finding(tmp_path):
    r"""The skip compares by exact name, not prefix.

    `[\w-]{2,}` is greedy and includes the hyphen, so `OtherRepo-plus#129`  # boundary-lint: ok=detector-own-fixture
    captures the full name. A `startswith` comparison would silently stop
    reporting a sibling repository whose name extends this one's.
    """
    rc, out = _run(tmp_path, {"docs/d.md": "see OtherRepo-plus#129\n"})  # boundary-lint: ok=detector-own-fixture
    assert rc == 1
    assert "OtherRepo-plus#129" in out  # boundary-lint: ok=detector-own-fixture


def test_a_line_citing_both_self_and_foreign_reports_only_the_foreign(tmp_path):
    """The shape that produced the false positive, with a synthetic foreign id.

    The real outside identifier this phase found on the live surface must not
    enter a tracked test; the doctrine prohibits it and a synthetic one carries
    the property exactly.
    """
    line = "Relay: ExternalRepo#97. Native owner: Qor-logic#357.\n"  # boundary-lint: ok=detector-own-fixture
    rc, out = _run(tmp_path, {"docs/e.md": line})
    assert rc == 1
    assert "ExternalRepo#97" in out  # boundary-lint: ok=detector-own-fixture
    assert "Qor-logic#357" not in out
    assert out.count("[boundary]") == 1


def test_a_foreign_repo_sharing_this_repos_name_is_still_a_finding(tmp_path):
    """The self-skip must compare the OWNER too, not the name alone.

    Phase 268 first shipped a name-only comparison and recorded the owner case
    as an accepted limitation. It is not acceptable: this detector gates CI
    fail-closed, so a widened blind spot in it under-reports a doctrine
    violation silently, and silent under-reporting is indistinguishable from a
    clean scan by the output the gate prints.

    A bare `Qor-logic#357` and an `<our-owner>/Qor-logic#357` are ours. A
    `<other-owner>/Qor-logic#5` is not.
    """
    rc, out = _run(tmp_path, {"docs/f.md": "see SomeOtherOrg/Qor-logic#5\n"})  # boundary-lint: ok=detector-own-fixture
    assert rc == 1
    assert "Qor-logic#5" in out  # boundary-lint: ok=detector-own-fixture


def test_a_backslash_separated_foreign_owner_is_still_a_finding(tmp_path):
    """The owner separator must cover `\\` and surrounding space, not just `/`.

    This project is Windows-primary and backslash paths appear in prose and in
    pasted tool output routinely -- the lint's own findings print as
    `docs\\plan-x.md` on this platform. An unrecognised separator makes the
    owner lookup return None, which this code reads as "ours" and skips, so
    every way of failing to see an owner fails toward silence on a fail-closed
    gate.
    """
    line = "see SomeOtherOrg\\Qor-logic#5" + chr(10)  # boundary-lint: ok=detector-own-fixture
    rc, out = _run(tmp_path, {"docs/g.md": line})
    assert rc == 1
    assert "Qor-logic#5" in out  # boundary-lint: ok=detector-own-fixture
