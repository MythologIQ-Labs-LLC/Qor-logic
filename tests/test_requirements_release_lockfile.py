"""Phase 102 (GH #118 P1): requirements-release.txt hash-pinned lockfile tests."""
from __future__ import annotations

import pathlib
import re

import yaml

_LOCKFILE = pathlib.Path("requirements-release.txt")
_LOCKFILE_IN = pathlib.Path("requirements-release.in")
_RELEASE_YML = pathlib.Path(".github/workflows/release.yml")


def _read_lockfile() -> str:
    return _LOCKFILE.read_text(encoding="utf-8")


def test_lockfile_files_exist():
    assert _LOCKFILE.is_file(), "requirements-release.txt must be committed"
    assert _LOCKFILE_IN.is_file(), "requirements-release.in (source) must be committed"


def test_lockfile_pins_build_with_hash():
    text = _read_lockfile()
    m = re.search(r"^build==[0-9]+\.[0-9]+\.[0-9]+", text, re.MULTILINE)
    assert m is not None, "lockfile must pin 'build' to a specific version"
    # At least two hash lines tied to build (one per published wheel/sdist).
    # Look for at least two consecutive --hash lines after the build== line.
    build_block_re = re.compile(
        r"^build==[0-9]+\.[0-9]+\.[0-9]+(?:\s+\\?\n\s+--hash=sha256:[0-9a-f]{64})+",
        re.MULTILINE,
    )
    assert build_block_re.search(text) is not None, (
        "build package must carry at least one --hash=sha256:... line"
    )
    hash_count = len(re.findall(r"^\s+--hash=sha256:[0-9a-f]{64}", text, re.MULTILINE))
    assert hash_count >= 2, (
        f"lockfile must carry at least 2 SHA-256 hashes across pinned deps; got {hash_count}"
    )


def test_lockfile_hashes_are_sha256_format():
    text = _read_lockfile()
    hash_lines = re.findall(r"--hash=(\S+)", text)
    assert hash_lines, "lockfile must contain --hash entries"
    for h in hash_lines:
        assert h.startswith("sha256:"), f"hash {h!r} must use sha256: prefix"
        digest = h.split(":", 1)[1]
        assert re.match(r"^[0-9a-f]{64}$", digest), (
            f"hash digest {digest!r} must be 64 lowercase hex chars"
        )


def test_lockfile_covers_known_transitive_deps():
    text = _read_lockfile()
    # build's known transitives at lock time: packaging, pyproject-hooks, colorama.
    # The lockfile-generator may add `tomli` for older Pythons but that's optional.
    for pkg in ("packaging", "pyproject-hooks"):
        assert re.search(rf"^{pkg}==", text, re.MULTILINE), (
            f"lockfile must lock transitive dep {pkg!r}"
        )


def test_release_workflow_build_job_uses_require_hashes():
    workflow = yaml.safe_load(_RELEASE_YML.read_text(encoding="utf-8"))
    build_steps = workflow["jobs"]["build"]["steps"]
    found = False
    for step in build_steps:
        run = step.get("run") or ""
        if "pip install" in run and "--require-hashes" in run and "requirements-release.txt" in run:
            found = True
            break
    assert found, (
        "build job must run 'pip install --require-hashes -r requirements-release.txt'; "
        "bare 'pip install build' is disallowed under P1"
    )

    # Defense-in-depth: no bare 'pip install build' anywhere in build job
    for step in build_steps:
        run = step.get("run") or ""
        # Allow 'pip install --require-hashes -r requirements-release.txt' and
        # 'pip install cyclonedx-bom' (SBOM tool, non_goal-deferred per plan)
        if re.search(r"^\s*pip install build\b", run, re.MULTILINE):
            raise AssertionError(
                "bare 'pip install build' detected; must use --require-hashes form"
            )
