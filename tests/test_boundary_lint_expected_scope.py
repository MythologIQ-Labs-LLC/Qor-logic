"""Phase 303 (GH #457): terms-file BOM, --expect-scope, and the CLI form of
two shipped skill references.

The lint tests build their trees and terms files under tmp_path with
write_bytes, use one synthetic term, and call publication_boundary_lint in
process. The CI test takes the boundary step's own arguments from
.github/workflows/ci.yml. The CLI-form tests reduce each shipped line to one
boolean inside a helper, so a failing run prints only the file path.
"""
from __future__ import annotations

import contextlib
import io
import re
import shlex
import subprocess
from pathlib import Path

import pytest
import yaml

from qor.scripts import publication_boundary_lint as pbl

REPO = Path(__file__).resolve().parent.parent
CI = REPO / ".github" / "workflows" / "ci.yml"
TERM = "example-outside-cli"
BOM = chr(0xFEFF)
_VARIANTS = ("claude", "codex", "cursor", "kilo-code")
_TEMPLATE = "qor/skills/meta/qor-bootstrap/references/qor-bootstrap-templates.md"
_LADDER = "qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md"
_TEMPLATE_PATHS = [_TEMPLATE] + [
    f"qor/dist/variants/{v}/skills/qor-bootstrap/references/qor-bootstrap-templates.md"
    for v in _VARIANTS]
_LADDER_PATHS = [_LADDER] + [
    f"qor/dist/variants/{v}/skills/qor-substantiate/references/seal-gate-ladder.md"
    for v in _VARIANTS]


def _tree(tmp_path: Path, text: str = "# heading\n") -> Path:
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "a.md").write_bytes(text.encode("utf-8"))
    return root


def _overlay(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body.encode("utf-8"))
    return path


def _main(argv: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = pbl.main(argv)
    return rc, buf.getvalue()


def _ci_boundary_argv() -> list[str]:
    workflow = yaml.safe_load(CI.read_text(encoding="utf-8"))
    runs = [step["run"] for job in workflow["jobs"].values()
            for step in job.get("steps", [])
            if "publication_boundary_lint" in str(step.get("run", ""))]
    assert len(runs) == 1, runs
    argv = shlex.split(runs[0])
    assert argv[:3] == ["python", "-m", "qor.scripts.publication_boundary_lint"], argv
    return argv[3:]


def _single_line(rel: str, marker: str) -> str | None:
    lines = [ln for ln in (REPO / rel).read_text(encoding="utf-8").splitlines()
             if marker in ln]
    return lines[0] if len(lines) == 1 else None


def _template_names_our_verifier(rel: str) -> bool:
    line = _single_line(rel, "verify-ledger")
    if line is None:
        return False
    m = re.search(r"`([^`]*) verify-ledger`", line)
    if m is None or not m.group(1).split():
        return False
    return m.group(1).split()[-1] == "qor-logic"


def _ladder_step_invokes_our_cli(rel: str) -> bool:
    line = _single_line(rel, "scripts ledger_commitment --session")
    if line is None or not line.split():
        return False
    return line.split()[0] == "qor-logic"


def test_a_bom_does_not_turn_a_comment_into_a_term(tmp_path):
    terms = _overlay(tmp_path / "terms.txt", f"{BOM}# operator note\n{TERM}\n")
    assert pbl._load_terms(terms) == [TERM]


def test_a_bom_does_not_hide_the_first_term(tmp_path):
    root = _tree(tmp_path, f"uses {TERM} here\n")
    terms = _overlay(tmp_path / "terms.txt", f"{BOM}{TERM}\n")
    result = pbl.collect_findings(root, no_git=True, terms_file=terms)
    assert result.scope == "structural+identity"
    assert result.findings == [f"[boundary] docs/a.md:1: identity term: {TERM}"]


def test_a_bom_comment_only_overlay_claims_no_identity_scope(tmp_path):
    root = _tree(tmp_path)
    terms = _overlay(tmp_path / "terms.txt", f"{BOM}# operator note only\n")
    result = pbl.collect_findings(root, no_git=True, terms_file=terms)
    assert result.scope == "structural"


@pytest.mark.parametrize("expected,with_terms", [
    ("structural", False), ("structural+identity", True)])
def test_expect_scope_passes_when_the_achieved_scope_matches(tmp_path, expected, with_terms):
    root = _tree(tmp_path)
    argv = ["--repo-root", str(root), "--no-git", "--expect-scope", expected]
    if with_terms:
        argv += ["--terms-file", str(_overlay(tmp_path / "terms.txt", f"{TERM}\n"))]
    rc, out = _main(argv)
    assert rc == 0, out
    assert f"0 finding(s) [scope: {expected}]" in out


@pytest.mark.parametrize("expected,achieved,with_terms", [
    pytest.param("structural+identity", "structural", False,
                 id="identity-expected-not-reached"),
    pytest.param("structural", "structural+identity", True,
                 id="structural-expected-exceeded")])
def test_expect_scope_fails_closed_when_the_achieved_scope_differs(
        tmp_path, expected, achieved, with_terms):
    root = _tree(tmp_path)
    argv = ["--repo-root", str(root), "--no-git", "--expect-scope", expected]
    if with_terms:
        argv += ["--terms-file", str(_overlay(tmp_path / "terms.txt", f"{TERM}\n"))]
    rc, out = _main(argv)
    assert rc == 1, out
    assert "0 finding(s)" in out
    assert f"scope mismatch: expected {expected}, achieved {achieved}" in out


def test_expect_scope_does_not_mask_findings(tmp_path):
    root = _tree(tmp_path, "see /home/dev/repo/x.py\n")  # boundary-lint: ok=detector-own-fixture
    rc, out = _main(["--repo-root", str(root), "--no-git", "--expect-scope", "structural"])
    assert rc == 1, out
    assert "1 finding(s) [scope: structural]" in out
    assert "scope mismatch" not in out


def test_without_expect_scope_the_exit_code_is_unchanged(tmp_path):
    root = _tree(tmp_path)
    terms = _overlay(tmp_path / "terms.txt", f"{TERM}\n")
    rc, out = _main(["--repo-root", str(root), "--no-git", "--terms-file", str(terms)])
    assert rc == 0, out
    assert "0 finding(s) [scope: structural+identity]" in out


def test_the_ci_boundary_step_fails_when_its_scope_is_not_the_one_it_states(tmp_path):
    args = _ci_boundary_argv()
    assert "--expect-scope" in args, args
    assert args[args.index("--expect-scope") + 1] == "structural", args
    root = _tree(tmp_path)
    args[args.index("--repo-root") + 1] = str(root)
    rc, out = _main(args + ["--no-git"])
    assert rc == 0, out
    _overlay(root / ".qor" / "private" / "boundary-terms.txt", f"{TERM}\n")
    rc, out = _main(args + ["--no-git"])
    assert rc == 1, out
    assert "scope mismatch: expected structural, achieved structural+identity" in out


def test_the_default_overlay_path_is_not_committed():
    result = subprocess.run(
        ["git", "-C", str(REPO), "check-ignore", "-q", ".qor/private/boundary-terms.txt"],
        capture_output=True, check=False)
    assert result.returncode == 0


@pytest.mark.parametrize("rel", _TEMPLATE_PATHS)
def test_the_bootstrap_ledger_template_names_this_repositorys_verifier(rel):
    ours = _template_names_our_verifier(rel)
    assert ours, rel


@pytest.mark.parametrize("rel", _LADDER_PATHS)
def test_the_seal_ladder_commitment_step_invokes_this_repositorys_cli(rel):
    ours = _ladder_step_invokes_our_cli(rel)
    assert ours, rel
