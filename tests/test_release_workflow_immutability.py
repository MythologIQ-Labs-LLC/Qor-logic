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


def test_release_workflow_build_job_generates_sbom():
    """Phase 102 (GH #118 P1): build job must produce dist/sbom.json via cyclonedx-py."""
    workflow = _load(_RELEASE)
    build_steps = workflow["jobs"]["build"]["steps"]
    found = False
    for step in build_steps:
        run = step.get("run") or ""
        if "cyclonedx-py" in run and "sbom.json" in run:
            found = True
            break
    assert found, "build job must contain a step that runs cyclonedx-py and emits sbom.json"


def test_release_workflow_publish_job_assembles_evidence_bundle():
    """Phase 102 (GH #118 P1): publish job must assemble dist/evidence.json with
    git_sha, lockfile_sha256, and artifact_sha256sums fields."""
    workflow = _load(_RELEASE)
    publish_steps = workflow["jobs"]["publish"]["steps"]
    found_step = None
    for step in publish_steps:
        run = step.get("run") or ""
        if "evidence.json" in run and "git_sha" in run:
            found_step = step
            break
    assert found_step is not None, (
        "publish job must contain a step that writes dist/evidence.json"
    )
    run = found_step.get("run") or ""
    for required_field in ("git_sha", "lockfile_sha256", "artifact_sha256sums", "action_pins"):
        assert required_field in run, (
            f"evidence.json assembly must include the {required_field!r} field"
        )


def test_release_workflow_attaches_evidence_to_github_release():
    """Phase 102 (GH #118 P1): publish job must run `gh release create` attaching
    dist/*, sbom.json, evidence.json, and SHA256SUMS."""
    workflow = _load(_RELEASE)
    publish_steps = workflow["jobs"]["publish"]["steps"]
    gh_release_step = None
    for step in publish_steps:
        run = step.get("run") or ""
        if "gh release create" in run:
            gh_release_step = step
            break
    assert gh_release_step is not None, (
        "publish job must run `gh release create` to attach the evidence bundle"
    )
    run = gh_release_step.get("run") or ""
    for required_attachment in ("sbom.json", "evidence.json", "SHA256SUMS"):
        assert required_attachment in run, (
            f"gh release create must attach {required_attachment!r}"
        )
    # Ensure dist/*.whl and dist/*.tar.gz are also attached (the actual artifacts).
    assert "dist/*.whl" in run or ".whl" in run, "gh release create must attach .whl files"
    assert "dist/*.tar.gz" in run or ".tar.gz" in run, "gh release create must attach .tar.gz files"


def test_release_workflow_publish_job_verifies_via_pypi_pullback():
    """Phase 103 (GH #118 P2): publish job runs `pip download` from PyPI and
    compares SHA-256 sums against dist/SHA256SUMS after the publish step and
    before `gh release create`."""
    workflow = _load(_RELEASE)
    publish_steps = workflow["jobs"]["publish"]["steps"]
    publish_idx = None
    pullback_idx = None
    gh_release_idx = None
    for idx, step in enumerate(publish_steps):
        uses = step.get("uses", "")
        run = step.get("run") or ""
        if uses.startswith("pypa/gh-action-pypi-publish"):
            publish_idx = idx
        if "pip download" in run and "qor-logic" in run and "sha256sum" in run:
            pullback_idx = idx
        if "gh release create" in run:
            gh_release_idx = idx
    assert publish_idx is not None, "pypa publish step must be present"
    assert pullback_idx is not None, (
        "publish job must run a PyPI pull-back verification step "
        "(`pip download` qor-logic, then sha256sum compare)"
    )
    assert gh_release_idx is not None, "gh release create step must be present"
    assert publish_idx < pullback_idx < gh_release_idx, (
        f"order must be publish ({publish_idx}) -> pullback ({pullback_idx}) "
        f"-> gh release create ({gh_release_idx})"
    )


def test_pypi_pullback_step_has_bounded_retry():
    """The pull-back step must use bounded retries (no infinite loop)."""
    workflow = _load(_RELEASE)
    publish_steps = workflow["jobs"]["publish"]["steps"]
    pullback_step = None
    for step in publish_steps:
        run = step.get("run") or ""
        if "pip download" in run and "qor-logic" in run:
            pullback_step = step
            break
    assert pullback_step is not None, "pull-back step must exist"
    run = pullback_step.get("run") or ""
    # Bounded retry: must contain a fixed iteration count + a sleep + an exit on max
    assert "for i in 1 2 3" in run or "for i in 1 2 3 4 5 6" in run, (
        "pull-back step must use a bounded for-loop (not infinite while-true)"
    )
    assert "sleep" in run, (
        "pull-back step must sleep between retry attempts"
    )
    assert "exit 1" in run, (
        "pull-back step must exit non-zero on max-retry exhaustion"
    )


def test_pypi_pullback_step_fetches_wheel_and_sdist():
    """The pull-back must verify both artifact types, not pip's default choice."""
    workflow = _load(_RELEASE)
    publish_steps = workflow["jobs"]["publish"]["steps"]
    pullback_step = None
    for step in publish_steps:
        run = step.get("run") or ""
        if "pip download" in run and "qor-logic" in run:
            pullback_step = step
            break
    assert pullback_step is not None, "pull-back step must exist"
    run = pullback_step.get("run") or ""
    assert "--only-binary=:all:" in run, (
        "pull-back step must explicitly download the wheel artifact"
    )
    assert "--no-binary=:all:" in run, (
        "pull-back step must explicitly download the sdist artifact"
    )


def test_release_workflow_build_job_installs_sbom_tool_hash_pinned():
    """Phase 107 D-107.2: build job installs cyclonedx-bom via --require-hashes,
    not bare pip install."""
    workflow = _load(_RELEASE)
    build_steps = workflow["jobs"]["build"]["steps"]
    found = False
    for step in build_steps:
        run = step.get("run") or ""
        if "pip install" in run and "--require-hashes" in run and "requirements-sbom.txt" in run:
            found = True
            break
    assert found, (
        "build job must install SBOM tool via "
        "'pip install --require-hashes -r requirements-sbom.txt'"
    )
    # Defense-in-depth: no bare `pip install cyclonedx-bom`
    for step in build_steps:
        run = step.get("run") or ""
        if re.search(r"^\s*pip install cyclonedx-bom\b", run, re.MULTILINE):
            raise AssertionError(
                "bare 'pip install cyclonedx-bom' detected; must use --require-hashes form"
            )


def test_release_workflow_sbom_step_runs_cyclonedx_after_install():
    """Phase 107: cyclonedx-py invocation runs after the hash-pinned install."""
    workflow = _load(_RELEASE)
    build_steps = workflow["jobs"]["build"]["steps"]
    install_idx = None
    sbom_idx = None
    for idx, step in enumerate(build_steps):
        run = step.get("run") or ""
        if "requirements-sbom.txt" in run and "--require-hashes" in run:
            install_idx = idx
        if "cyclonedx-py" in run and "sbom.json" in run:
            sbom_idx = idx
    assert install_idx is not None, "SBOM install step required"
    assert sbom_idx is not None, "cyclonedx-py invocation step required"
    if install_idx != sbom_idx:
        assert install_idx < sbom_idx, (
            f"install (idx {install_idx}) must precede cyclonedx-py (idx {sbom_idx})"
        )


def test_release_workflow_publish_uses_separate_packages_dir():
    """Phase 104: pypa-publish must point at a separate `packages-dir`
    that contains only wheel + sdist (not at `dist/` which carries
    SHA256SUMS, sbom.json, evidence.json)."""
    workflow = _load(_RELEASE)
    publish_steps = workflow["jobs"]["publish"]["steps"]
    pypa_step = next(
        (s for s in publish_steps if s.get("uses", "").startswith("pypa/gh-action-pypi-publish")),
        None,
    )
    assert pypa_step is not None, "pypa-publish step must exist"
    with_kwargs = pypa_step.get("with") or {}
    packages_dir = with_kwargs.get("packages-dir")
    assert packages_dir not in (None, "", "dist/", "dist"), (
        f"pypa-publish must declare packages-dir distinct from 'dist/'; "
        f"got {packages_dir!r}. The dist/ directory carries non-distribution "
        f"files (SHA256SUMS, sbom.json, evidence.json) that twine rejects."
    )


def test_release_workflow_publish_only_dir_excludes_non_dist_files():
    """Phase 104: the prepare-publish step must copy ONLY *.whl and
    *.tar.gz; it must NOT copy SHA256SUMS, sbom.json, or evidence.json."""
    workflow = _load(_RELEASE)
    publish_steps = workflow["jobs"]["publish"]["steps"]
    prepare_step = None
    for step in publish_steps:
        run = step.get("run") or ""
        if "mkdir" in run and "dist-publish" in run and "cp dist/" in run:
            prepare_step = step
            break
    assert prepare_step is not None, (
        "publish job must contain a Prepare publish-only directory step "
        "that creates dist-publish/ and copies wheel+sdist into it"
    )
    run = prepare_step.get("run") or ""
    assert "*.whl" in run, "prepare step must copy *.whl files"
    assert "*.tar.gz" in run, "prepare step must copy *.tar.gz files"
    copy_line = next(
        (ln for ln in run.splitlines() if "cp dist/" in ln and "dist-publish" in ln),
        "",
    )
    for forbidden in ("SHA256SUMS", "sbom.json", "evidence.json"):
        assert forbidden not in copy_line, (
            f"prepare step copies forbidden non-dist file {forbidden!r} into dist-publish/; "
            f"line: {copy_line!r}"
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
