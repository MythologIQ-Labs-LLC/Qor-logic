"""Phase 55: CycloneDX SBOM emission tests."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from qor.scripts import sbom_emit

REPO_ROOT = Path(__file__).resolve().parent.parent


def _make_fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "qor" / "skills" / "alpha").mkdir(parents=True)
    (repo / "qor" / "skills" / "alpha" / "SKILL.md").write_text("---\nname: alpha\n---\n", encoding="utf-8")
    (repo / "qor" / "skills" / "beta").mkdir(parents=True)
    (repo / "qor" / "skills" / "beta" / "SKILL.md").write_text("---\nname: beta\n---\n", encoding="utf-8")
    (repo / "qor" / "references").mkdir(parents=True)
    (repo / "qor" / "references" / "doctrine-foo.md").write_text("# Doctrine Foo", encoding="utf-8")
    (repo / "qor" / "dist" / "variants" / "claude").mkdir(parents=True)
    (repo / "qor" / "dist" / "variants" / "claude" / "manifest.json").write_text("{}", encoding="utf-8")
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "qor-logic"\nversion = "9.9.9"\n', encoding="utf-8",
    )
    return repo


def test_sbom_emitter_produces_cyclonedx_v1_5_shape(tmp_path):
    sbom = sbom_emit.emit(_make_fixture_repo(tmp_path))
    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.5"
    assert sbom["metadata"]["tools"][0]["name"] == "Qor-logic"


def test_sbom_emitter_lists_qor_logic_root_component(tmp_path):
    sbom = sbom_emit.emit(_make_fixture_repo(tmp_path))
    component = sbom["metadata"]["component"]
    assert component["type"] == "application"
    assert component["bom-ref"] == "qor-logic@9.9.9"
    assert component["purl"].startswith("pkg:pypi/qor-logic@")


def test_sbom_emitter_lists_skill_components(tmp_path):
    sbom = sbom_emit.emit(_make_fixture_repo(tmp_path))
    skill_components = [c for c in sbom["components"] if c["bom-ref"].startswith("skill:")]
    assert len(skill_components) == 2
    names = {c["name"] for c in skill_components}
    assert names == {"alpha", "beta"}


def test_sbom_emitter_lists_doctrine_components(tmp_path):
    sbom = sbom_emit.emit(_make_fixture_repo(tmp_path))
    doctrine_components = [c for c in sbom["components"] if c["bom-ref"].startswith("doctrine:")]
    assert len(doctrine_components) == 1
    assert doctrine_components[0]["name"] == "doctrine-foo"


def test_sbom_emitter_lists_variant_components(tmp_path):
    sbom = sbom_emit.emit(_make_fixture_repo(tmp_path))
    variants = [c for c in sbom["components"] if c["bom-ref"].startswith("variant:")]
    assert len(variants) == 1
    assert variants[0]["name"] == "claude"


def test_sbom_emitter_dependencies_root_depends_on_all(tmp_path):
    sbom = sbom_emit.emit(_make_fixture_repo(tmp_path))
    assert sbom["dependencies"][0]["ref"] == "qor-logic@9.9.9"
    assert len(sbom["dependencies"][0]["dependsOn"]) == len(sbom["components"])


def test_sbom_emitter_writes_to_specified_out_path(tmp_path):
    repo = _make_fixture_repo(tmp_path)
    out = tmp_path / "x.json"
    written = sbom_emit.write(repo, out)
    assert written.exists()
    parsed = json.loads(written.read_text())
    assert parsed["bomFormat"] == "CycloneDX"


def test_skills_writing_deliver_gate_invoke_sbom_emit():
    """Co-occurrence behavior invariant: any SKILL.md whose frontmatter
    declares ``gate_writes: deliver`` must invoke ``sbom_emit.emit`` (or
    ``sbom_emit.write``) AND capture the path into a ``sbom_path`` payload field.
    """
    skills_dir = REPO_ROOT / "qor" / "skills"
    deliver_writers: list[Path] = []
    for skill in skills_dir.rglob("SKILL.md"):
        body = skill.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---", body, re.DOTALL)
        if not match:
            continue
        if re.search(r"^gate_writes\s*:\s*deliver\s*$", match.group(1), re.MULTILINE):
            deliver_writers.append(skill)

    assert deliver_writers, "expected >=1 SKILL.md declaring gate_writes: deliver"

    violators: list[str] = []
    for skill in deliver_writers:
        body = skill.read_text(encoding="utf-8")
        if "sbom_emit" not in body:
            violators.append(f"{skill.relative_to(REPO_ROOT)}: missing sbom_emit invocation")
        if "sbom_path" not in body:
            violators.append(f"{skill.relative_to(REPO_ROOT)}: missing sbom_path payload field")
    assert not violators, "deliver-gate-writing skills must emit SBOM: " + str(violators)


def test_release_cli_subcommand_emits_sbom(tmp_path):
    repo = _make_fixture_repo(tmp_path)
    out = tmp_path / "sbom.json"
    proc = subprocess.run(
        [sys.executable, "-m", "qor.cli", "release", "sbom",
         "--repo-root", str(repo), "--out", str(out)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, proc.stderr
    assert out.exists()
    sbom = json.loads(out.read_text())
    assert sbom["bomFormat"] == "CycloneDX"
