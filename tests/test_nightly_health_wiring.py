"""Phase 165: structural properties of the nightly-health workflow.

Text/regex assertions (no YAML parser dependency) over the workflow file --
the same property-test approach as the release-immutability guards. Each test
names the failure mode it locks (issue-named regression guards per GH #250c).
"""
from __future__ import annotations

import re
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "nightly-health.yml"


def _text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_workflow_declares_schedule_dispatch_and_permissions():
    text = _text()
    assert re.search(r"^\s*schedule:\s*$", text, re.MULTILINE), "nightly cron trigger missing"
    assert re.search(r"cron:\s*'0 9 \* \* \*'", text), "expected daily 09:00 UTC cron"
    assert "workflow_dispatch:" in text, "manual trigger missing (needed for post-merge D4 evidence)"
    assert re.search(r"issues:\s*write", text), "issue lifecycle needs issues: write"
    assert re.search(r"contents:\s*read", text), "checkout needs contents: read"
    assert not re.search(r"(contents|id-token|actions|packages):\s*write", text), (
        "nightly-health must not carry write permissions beyond issues"
    )


def test_workflow_runs_self_test_before_status_and_uses_lifecycle_idioms():
    text = _text()
    self_test = text.index("qor.scripts.status_json --self-test")
    status_run = text.index("qor.scripts.status_json --repo-root")
    assert self_test < status_run, "checker must validate itself before its verdict is trusted"
    assert "gh issue list --search" in text, "lifecycle: existing-issue search missing"
    assert "gh issue create" in text, "lifecycle: create path missing"
    assert "gh issue close" in text, "lifecycle: close path missing"
    title_key = "Nightly governance health"
    assert text.count(title_key) >= 2, "title key must appear in both create and close paths"
    # OWASP A03 (audit binding note): JSON payload reaches gh via env, never
    # inline ${{ }} interpolation inside a run body.
    run_bodies = re.findall(r"run: \|([\s\S]*?)(?=\n      - |\Z)", text)
    for body in run_bodies:
        assert "${{ steps." not in body, (
            "step output interpolated into a run body (Actions script-injection surface); "
            "pass it via env: instead"
        )


# Phase 283 (GH #432): the boundary step is documented "reports only" in three
# places and returns a non-zero exit into a bare `run:`, so a finding ended the
# job before the health-issue lifecycle. These tests execute the step's own
# shell body against a stubbed scanner rather than pattern-matching the YAML:
# a regex for `set +e` proves the string is present, not that the step survives
# a non-zero scanner.

import os
import shutil
import subprocess
import textwrap

import pytest

BOUNDARY_STEP = "publication boundary (GitHub surface)"


def _find_bash() -> str | None:
    """A bash that can actually run a script.

    On Windows `shutil.which("bash")` can resolve to the WSL launcher, which
    reports "no installed distributions" and exits non-zero for every input --
    a red that says nothing about the body under test. Candidates are probed by
    execution rather than by path, so the check does not encode where any
    particular host keeps its shell.
    """
    candidates = [shutil.which("bash")]
    try:  # a Windows host's Git ships a bash beside its exec-path
        exec_path = subprocess.run(
            ["git", "--exec-path"], capture_output=True, text=True, timeout=30
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        exec_path = ""
    if exec_path:
        for parent in Path(exec_path).parents:
            candidates.append(str(parent / "bin" / "bash.exe"))
    for candidate in candidates:
        if not candidate or not os.path.exists(candidate):
            continue
        try:
            probe = subprocess.run(
                [candidate, "-c", "printf ok"], capture_output=True, text=True, timeout=30
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if probe.returncode == 0 and probe.stdout.strip() == "ok":
            return candidate
    return None


_BASH = _find_bash()


def _shell_path(path) -> str:
    """A path in the form the resolved shell resolves.

    Git Bash accepts a drive-letter path as an argument but will not match one
    as a PATH entry, so a stub directory handed over in that form never shadows
    anything and the real interpreter runs -- silently, with the test still red
    for a reason that has nothing to do with the body. `cygpath` is absent on
    Linux, where the plain path is already correct.
    """
    text = str(path)
    if _BASH is None:
        return text
    probe = subprocess.run(
        [_BASH, "-c", f'command -v cygpath >/dev/null && cygpath -u "{text}" || printf "%s" "{text}"'],
        capture_output=True, text=True,
    )
    return probe.stdout.strip() or text

needs_bash = pytest.mark.skipif(
    _BASH is None,
    reason="step bodies are POSIX shell; no working bash on this host",
)


def _step_block(name: str) -> str:
    """The YAML lines belonging to one step, by step name."""
    text = _text()
    marker = f"      - name: {name}\n"
    assert marker in text, f"no step named {name!r}"
    rest = text[text.index(marker) + len(marker):]
    nxt = re.search(r"^      - ", rest, re.MULTILINE)
    return rest[: nxt.start()] if nxt else rest


#: Actions expressions are not shell. `${{ github.repository }}` is a bad
#: substitution to bash, so a body carrying one aborts before the scanner runs
#: and every test below would fail on shell syntax rather than on the behaviour
#: under test -- the vacuous red this phase exists to avoid. The pre-change body
#: carries exactly one; Phase 283 moves it to `env: REPO`, after which this map
#: matches nothing and can be deleted.
_ACTIONS_EXPRESSIONS = {"${{ github.repository }}": "$REPO"}


def _step_run_body(name: str) -> str:
    """A step's `run:` body, accepting both the block and single-line forms.

    The pre-change boundary step is a single-line scalar and Phase 283 converts
    it to `run: |`. A helper that recognised only the block form would raise at
    HEAD, and every test below would go red helper-raised rather than by
    observing the body propagate a non-zero exit -- a vacuous red.
    """
    block = _step_block(name)
    m = re.search(r"^        run: \|\n((?:(?:          .*)?\n)*)", block, re.MULTILINE)
    body = None
    if m:
        body = textwrap.dedent(m.group(1))
    else:
        m = re.search(r"^        run: (.+)$", block, re.MULTILINE)
        if m:
            body = m.group(1) + "\n"
    if body is None:
        raise AssertionError(f"step {name!r} has no run: body")
    for expression, shell in _ACTIONS_EXPRESSIONS.items():
        body = body.replace(expression, shell)
    assert "${{" not in body, (
        f"step {name!r} carries an Actions expression bash cannot parse; add it "
        f"to _ACTIONS_EXPRESSIONS or move it to env:"
    )
    return body


def _run_step_body(tmp_path, *, exit_code, stdout="", stderr=""):
    """Execute the boundary step's body with a recording stub on PATH."""
    stub_dir = tmp_path / "stub"
    stub_dir.mkdir()
    argv_log = tmp_path / "argv.txt"
    stub = stub_dir / "python"
    stub.write_text(
        "#!/usr/bin/env bash\n"
        f'printf "%s\n" "$@" > {_shell_path(argv_log)}\n'
        + "".join(f'printf "%s\n" {line!r}\n' for line in stdout.splitlines())
        + "".join(f'printf "%s\n" {line!r} >&2\n' for line in stderr.splitlines())
        + f"exit {exit_code}\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)

    body = tmp_path / "body.sh"
    body.write_text(_step_run_body(BOUNDARY_STEP), encoding="utf-8")
    out_file = tmp_path / "gh_output"
    out_file.touch()
    summary_file = tmp_path / "gh_summary"
    summary_file.touch()

    env = dict(os.environ)
    env["GITHUB_OUTPUT"] = str(out_file)
    env["GITHUB_STEP_SUMMARY"] = str(summary_file)
    env["REPO"] = "ExampleOwner/ExampleRepo"
    # PATH is left in the host's own form. bash splits it on ":", but Windows
    # needs ";" for the launcher to resolve bash at all, and a ":"-joined value
    # corrupts that lookup badly enough that it falls through to the WSL stub,
    # which has no distribution installed. The stub directory is prepended from
    # inside the shell instead, where ":" is unambiguously correct, and the body
    # is sourced verbatim so nothing about it is rewritten.
    prelude = (
        f'export PATH="{_shell_path(stub_dir)}:$PATH"; . "{_shell_path(body)}"'
    )
    proc = subprocess.run(
        [_BASH, "-e", "-c", prelude], env=env, capture_output=True, text=True
    )
    outputs = dict(
        line.split("=", 1)
        for line in out_file.read_text(encoding="utf-8").splitlines()
        if "=" in line
    )
    argv = argv_log.read_text(encoding="utf-8").splitlines() if argv_log.exists() else []
    return proc.returncode, outputs, argv


COMPLETION = "github_surface: 18 finding(s) (structural only)"


@needs_bash
def test_boundary_step_body_exits_zero_when_the_scan_reports_findings(tmp_path):
    rc, outputs, _ = _run_step_body(tmp_path, exit_code=1, stdout=COMPLETION)
    assert rc == 0, "a finding must not fail the step; it ends the job"
    assert outputs["boundary_rc"] == "1"


@needs_bash
def test_boundary_step_body_exits_zero_when_the_scanner_cannot_read_the_surface(tmp_path):
    rc, outputs, _ = _run_step_body(
        tmp_path, exit_code=2, stderr="ERROR [github-surface] could not read the surface"
    )
    assert rc == 0
    assert outputs["boundary_rc"] == "2"


@needs_bash
def test_a_scanner_crash_is_classified_as_could_not_scan_not_as_findings(tmp_path):
    rc, outputs, _ = _run_step_body(
        tmp_path,
        exit_code=1,
        stdout="Traceback (most recent call last):",
        stderr="KeyError: 'number'",
    )
    assert rc == 0
    assert outputs["boundary_rc"] == "2", (
        "an unhandled exception exits 1, the same code as findings; without the "
        "completion-line check a crash reads as an ordinary advisory finding"
    )


@needs_bash
def test_a_clean_scan_is_reported_as_zero(tmp_path):
    rc, outputs, _ = _run_step_body(
        tmp_path, exit_code=0, stdout="github_surface: 0 finding(s) (structural only)"
    )
    assert rc == 0
    assert outputs["boundary_rc"] == "0"


@needs_bash
def test_the_step_invokes_the_scanner_module_with_the_repository_argument(tmp_path):
    _, _, argv = _run_step_body(tmp_path, exit_code=1, stdout=COMPLETION)
    assert argv[:2] == ["-m", "qor.scripts.github_surface"]
    assert "--repo" in argv
    assert argv[argv.index("--repo") + 1] == "ExampleOwner/ExampleRepo"


def _step_condition(name: str) -> str:
    """The `if:` expression of one step, by step name."""
    block = _step_block(name)
    m = re.search(r"^        if: (.+)$", block, re.MULTILINE)
    assert m, f"step {name!r} declares no if: condition"
    return m.group(1).strip().strip('"')


CREATE_STEP = "Create or update health issue"
CLOSE_STEP = "Close resolved health issue"


def _boundary_codes(condition: str) -> set[str]:
    """The boundary_rc literals a condition compares against."""
    return set(
        re.findall(r"steps\.boundary\.outputs\.boundary_rc\s*==\s*'(\d)'", condition)
    )


def test_lifecycle_opens_when_the_surface_could_not_be_scanned():
    codes = _boundary_codes(_step_condition(CREATE_STEP))
    assert codes == {"2"}, (
        "the create condition must react to a could-not-scan run; without it the "
        "only new reporting path this phase adds can be deleted with the whole "
        "suite still green"
    )


def test_the_create_and_close_boundary_codes_partition_the_scanner_contract():
    opens = _boundary_codes(_step_condition(CREATE_STEP))
    closes = _boundary_codes(_step_condition(CLOSE_STEP))
    assert not (opens & closes), f"a scanner outcome both opens and closes: {opens & closes}"
    assert opens | closes == {"0", "1", "2"}, (
        "every scanner outcome must reach one branch; a gap leaves an open issue "
        f"with nothing to close it (covered: {sorted(opens | closes)})"
    )


def test_every_step_output_reference_resolves_to_a_step_that_writes_it():
    text = _text()
    references = set(re.findall(r"steps\.([\w-]+)\.outputs\.([\w-]+)", text))
    assert references, "expected the workflow to consume step outputs"
    for step_id, key in sorted(references):
        assert re.search(rf"^        id: {re.escape(step_id)}$", text, re.MULTILINE), (
            f"'{step_id}.outputs.{key}' is read but no step declares id: {step_id}; "
            "Actions resolves an unknown step to the empty string in silence"
        )
        assert re.search(rf"{re.escape(key)}=", text), (
            f"no step writes '{key}' to $GITHUB_OUTPUT, so '{step_id}.outputs.{key}' "
            "is permanently empty"
        )


def test_the_boundary_step_precedes_the_checks_whose_outputs_gate_the_lifecycle():
    text = _text()
    boundary = text.index(f"      - name: {BOUNDARY_STEP}")
    assert boundary < text.index("        id: health"), "boundary must precede health"
    assert boundary < text.index("        id: smoke"), "boundary must precede smoke"


def test_both_lifecycle_conditions_declare_not_cancelled():
    for step in (CREATE_STEP, CLOSE_STEP):
        condition = _step_condition(step)
        assert "!cancelled()" in condition, f"{step}: needs !cancelled() to run after a failure"
        assert "always()" not in condition, (
            f"{step}: always() also fires on a run cancelled by cancel-in-progress, "
            "where every output is empty"
        )


def test_the_repository_reaches_the_scanner_through_env_not_interpolation():
    block = _step_block(BOUNDARY_STEP)
    assert re.search(r"^          REPO: \$\{\{ github\.repository \}\}$", block, re.MULTILINE)
    assert "${{" not in _step_run_body(BOUNDARY_STEP)


def test_the_lifecycle_reads_its_inputs_from_env_not_interpolation():
    block = _step_block(CREATE_STEP)
    for key in ("HEALTH_FAILED", "SMOKE_FAILED", "BOUNDARY_SUMMARY"):
        assert re.search(rf"^          {key}: ", block, re.MULTILINE), f"{key} not bound in env:"
    assert "${{" not in _step_run_body(CREATE_STEP)


def test_the_issue_body_carries_the_boundary_summary_from_step_output():
    block = _step_block(CREATE_STEP)
    assert "BOUNDARY_SUMMARY: ${{ steps.boundary.outputs.boundary_summary }}" in block
    assert "Publication boundary: %s" in _step_run_body(CREATE_STEP)


def test_the_close_comment_does_not_claim_every_check_is_green():
    body = _step_run_body(CLOSE_STEP)
    assert "All nightly checks green" not in body, (
        "the close comment asserted every check passed while boundary findings "
        "could still stand"
    )
    assert "BOUNDARY_SUMMARY" in body, "the close comment must say what the boundary reported"


@needs_bash
def test_a_boundary_only_failure_gets_its_own_title(tmp_path):
    """The two title branches must differ and both keep the searched prefix."""
    body = tmp_path / "create.sh"
    body.write_text(_step_run_body(CREATE_STEP).split("EXISTING=")[0], encoding="utf-8")
    titles = {}
    for label, health, smoke in (("boundary", "0", "0"), ("drift", "1", "0")):
        probe = subprocess.run(
            [_BASH, "-e", "-c", f'. "{_shell_path(body)}"; printf "%s" "$TITLE"'],
            env={**os.environ, "HEALTH_FAILED": health, "SMOKE_FAILED": smoke},
            capture_output=True, text=True,
        )
        assert probe.returncode == 0, probe.stderr
        titles[label] = probe.stdout.strip()
    assert titles["boundary"] != titles["drift"], (
        "a boundary-only failure reported the health-drift title above a green payload"
    )
    for title in titles.values():
        assert title.startswith("Nightly governance health"), (
            "both create and close search on this prefix"
        )
