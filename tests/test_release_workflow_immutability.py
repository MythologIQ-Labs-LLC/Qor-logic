"""Phase 101 (GH #118 P0): structural assertions on release/CI/lint workflows.

Verifies the workflow-immutability + split-job + scoped-OIDC properties added
in Phase 101. These are policy properties: the workflow's STRUCTURE is its
behavior for a declarative CI config.
"""
from __future__ import annotations

import pathlib
import re

import yaml


_RELEASE = pathlib.Path(".github/workflows/release.yml")
_CI = pathlib.Path(".github/workflows/ci.yml")
_PR_LINT = pathlib.Path(".github/workflows/pr-lint.yml")

# Owners of Actions that must be SHA-pinned. Local repo refs (./.github/...)
# and Docker-image refs are out of scope; we only police the marketplace-ish
# `owner/repo@ref` shape here.
_SHA_RE = re.compile(r"^([a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+)@([0-9a-f]{40})$")


def _load(path: pathlib.Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _iter_uses_steps(workflow: dict):
    """Yield (job_name, step_index, step_dict) for every step that has a `uses:`."""
    for job_name, job in workflow["jobs"].items():
        for idx, step in enumerate(job.get("steps", [])):
            if "uses" in step:
                yield job_name, idx, step


def _assert_workflow_uses_sha_pinned(workflow_path: pathlib.Path) -> None:
    workflow = _load(workflow_path)
    text = workflow_path.read_text(encoding="utf-8").splitlines()
    failures: list[str] = []
    for job_name, idx, step in _iter_uses_steps(workflow):
        uses = step["uses"]
        m = _SHA_RE.match(uses)
        if not m:
            failures.append(
                f"{workflow_path}: jobs.{job_name}.steps[{idx}] uses={uses!r} "
                f"is not SHA-pinned (expected owner/repo@<40-hex-sha>)"
            )
            continue
        # Locate the line and confirm a # vX.Y.Z annotation comment is on it.
        sha = m.group(2)
        annotated = any(
            sha in line and re.search(r"#\s*v[0-9]+\.[0-9]+", line)
            for line in text
        )
        if not annotated:
            failures.append(
                f"{workflow_path}: jobs.{job_name}.steps[{idx}] uses={uses!r} "
                f"is SHA-pinned but lacks a '# vX.Y.Z' annotation comment"
            )
    assert not failures, "SHA-pin violations:\n  " + "\n  ".join(failures)


def test_release_workflow_actions_sha_pinned():
    _assert_workflow_uses_sha_pinned(_RELEASE)


def test_ci_workflow_actions_sha_pinned():
    _assert_workflow_uses_sha_pinned(_CI)


def test_pr_lint_workflow_actions_sha_pinned():
    _assert_workflow_uses_sha_pinned(_PR_LINT)


def test_release_workflow_split_jobs():
    workflow = _load(_RELEASE)
    jobs = workflow["jobs"]
    assert set(jobs.keys()) == {"build", "publish"}, (
        f"release.yml must define exactly jobs 'build' and 'publish'; "
        f"got {sorted(jobs.keys())}"
    )
    needs = jobs["publish"].get("needs")
    needs_list = [needs] if isinstance(needs, str) else (needs or [])
    assert needs_list == ["build"], (
        f"jobs.publish.needs must be ['build']; got {needs!r}"
    )


def test_release_workflow_id_token_scoped_to_publish_job():
    text = _RELEASE.read_text(encoding="utf-8")
    workflow = _load(_RELEASE)

    # Workflow-level permissions block must not contain id-token: write.
    top_perms = workflow.get("permissions") or {}
    if isinstance(top_perms, dict):
        assert top_perms.get("id-token") != "write", (
            "Workflow-level permissions must not include id-token: write"
        )

    # Build job permissions must not include id-token: write.
    build_perms = workflow["jobs"]["build"].get("permissions") or {}
    if isinstance(build_perms, dict):
        assert build_perms.get("id-token") != "write", (
            "build job permissions must not include id-token: write"
        )

    # Publish job permissions MUST include id-token: write.
    pub_perms = workflow["jobs"]["publish"].get("permissions") or {}
    assert isinstance(pub_perms, dict), (
        "publish job must declare an explicit permissions block"
    )
    assert pub_perms.get("id-token") == "write", (
        f"publish job permissions must include id-token: write; got {pub_perms!r}"
    )

    # Sanity: the literal 'id-token: write' appears exactly once in the file
    # text (defense-in-depth against permissions blocks declared in unusual
    # places like reusable-workflow callers).
    occurrences = len(re.findall(r"\bid-token:\s*write\b", text))
    assert occurrences == 1, (
        f"'id-token: write' must appear exactly once in release.yml; found {occurrences}"
    )


def test_release_workflow_publish_job_does_not_use_setup_python_cache():
    """The privileged publish job must not consume restorable pip cache state.

    The cleanest way to satisfy this is to NOT run setup-python in the publish
    job at all (pypa/gh-action-pypi-publish is a Docker action; the host
    interpreter is unused). If setup-python is present, its `with.cache` key
    must be absent.
    """
    workflow = _load(_RELEASE)
    publish_steps = workflow["jobs"]["publish"]["steps"]
    for idx, step in enumerate(publish_steps):
        uses = step.get("uses", "")
        if uses.startswith("actions/setup-python"):
            with_kwargs = step.get("with") or {}
            assert "cache" not in with_kwargs, (
                f"publish.steps[{idx}] uses setup-python with cache={with_kwargs.get('cache')!r}; "
                "publish job must not consume restorable cache state"
            )


def test_release_workflow_build_job_allows_pip_cache():
    """Positive assertion: build job is unprivileged and MAY use pip cache.

    Documents the asymmetry between build (allowed cache) and publish (no
    cache). If a future refactor accidentally removes cache from build, this
    test fails and the change must be justified.
    """
    workflow = _load(_RELEASE)
    build_steps = workflow["jobs"]["build"]["steps"]
    setup_python_steps = [
        s for s in build_steps if s.get("uses", "").startswith("actions/setup-python")
    ]
    assert len(setup_python_steps) >= 1, (
        "build job must run actions/setup-python (for python -m build)"
    )
    cache_values = [(s.get("with") or {}).get("cache") for s in setup_python_steps]
    assert any(c == "pip" for c in cache_values), (
        f"build job's setup-python must declare cache: pip; got {cache_values!r}"
    )


def test_release_workflow_artifact_handoff_with_sha_verify():
    workflow = _load(_RELEASE)
    build_steps = workflow["jobs"]["build"]["steps"]
    publish_steps = workflow["jobs"]["publish"]["steps"]

    # Build must upload an artifact named release-dist
    upload_steps = [
        s for s in build_steps if s.get("uses", "").startswith("actions/upload-artifact")
    ]
    assert len(upload_steps) == 1, (
        f"build job must contain exactly one upload-artifact step; found {len(upload_steps)}"
    )
    assert (upload_steps[0].get("with") or {}).get("name") == "release-dist", (
        "upload-artifact step must name the artifact 'release-dist'"
    )

    # Build must produce SHA256SUMS before upload
    sha_gen_idx = None
    upload_idx = None
    for idx, step in enumerate(build_steps):
        run = step.get("run") or ""
        if "sha256sum" in run and "SHA256SUMS" in run and "-c" not in run:
            sha_gen_idx = idx
        if step.get("uses", "").startswith("actions/upload-artifact"):
            upload_idx = idx
    assert sha_gen_idx is not None, (
        "build job must contain a step that generates dist/SHA256SUMS"
    )
    assert upload_idx is not None and sha_gen_idx < upload_idx, (
        "SHA256SUMS generation must run before upload-artifact"
    )

    # Publish must download artifact and verify SHA before publish
    download_idx = None
    verify_idx = None
    publish_idx = None
    for idx, step in enumerate(publish_steps):
        if step.get("uses", "").startswith("actions/download-artifact"):
            download_idx = idx
        run = step.get("run") or ""
        if "sha256sum -c" in run and "SHA256SUMS" in run:
            verify_idx = idx
        if step.get("uses", "").startswith("pypa/gh-action-pypi-publish"):
            publish_idx = idx
    assert download_idx is not None, "publish job must download the release-dist artifact"
    assert verify_idx is not None, "publish job must run 'sha256sum -c SHA256SUMS'"
    assert publish_idx is not None, "publish job must invoke pypa/gh-action-pypi-publish"
    assert download_idx < verify_idx < publish_idx, (
        f"order must be download ({download_idx}) -> verify ({verify_idx}) -> publish ({publish_idx})"
    )
