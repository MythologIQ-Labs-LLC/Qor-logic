"""CycloneDX v1.5 SBOM emitter (Phase 55).

Hand-rolled emitter producing a CycloneDX 1.5-compatible JSON document.
Walks ``pyproject.toml`` for the Qor-logic root component; walks
``qor/skills/**/SKILL.md`` for skill components, ``qor/references/doctrine-*.md``
for doctrine components, and ``qor/dist/variants/*/manifest.json`` for variant
artifacts. Each component declares ``bom-ref``, ``name``, ``version``,
``purl`` (where applicable), ``type``, and ``description``.

Closes OWASP LLM05 (Supply Chain) at the manifest layer; downstream
vulnerability scanners consume the emitted document.

Per ``qor/references/doctrine-eu-ai-act.md`` Art. 50.
"""
from __future__ import annotations

import argparse
import json
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _read_version(repo_root: Path) -> str:
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.exists():
        return "0.0.0"
    with pyproject.open("rb") as fh:
        data = tomllib.load(fh)
    return str(data.get("project", {}).get("version", "0.0.0"))


def _emit_skill_components(
    repo_root: Path, version: str,
) -> list[dict[str, Any]]:
    skills_dir = repo_root / "qor" / "skills"
    components: list[dict[str, Any]] = []
    for skill_md in sorted(skills_dir.rglob("SKILL.md")):
        name = skill_md.parent.name
        components.append({
            "type": "file",
            "bom-ref": f"skill:{name}@{version}",
            "name": name,
            "version": version,
            "description": f"Qor-logic skill: {name}",
        })
    return components


def _emit_doctrine_components(
    repo_root: Path, version: str,
) -> list[dict[str, Any]]:
    doctrines_dir = repo_root / "qor" / "references"
    components: list[dict[str, Any]] = []
    for doctrine in sorted(doctrines_dir.glob("doctrine-*.md")):
        name = doctrine.stem
        components.append({
            "type": "file",
            "bom-ref": f"doctrine:{name}@{version}",
            "name": name,
            "version": version,
            "description": f"Qor-logic doctrine: {name}",
        })
    return components


def _emit_variant_components(
    repo_root: Path, version: str,
) -> list[dict[str, Any]]:
    variants_dir = repo_root / "qor" / "dist" / "variants"
    components: list[dict[str, Any]] = []
    if not variants_dir.exists():
        return components
    for manifest in sorted(variants_dir.glob("*/manifest.json")):
        host = manifest.parent.name
        components.append({
            "type": "framework",
            "bom-ref": f"variant:{host}@{version}",
            "name": host,
            "version": version,
            "description": f"Qor-logic variant for host: {host}",
        })
    return components


def emit(repo_root: Path) -> dict[str, Any]:
    """Emit a CycloneDX 1.5 SBOM dict for the repo at ``repo_root``."""
    version = _read_version(repo_root)
    skills = _emit_skill_components(repo_root, version)
    doctrines = _emit_doctrine_components(repo_root, version)
    variants = _emit_variant_components(repo_root, version)
    components = skills + doctrines + variants
    root_ref = f"qor-logic@{version}"

    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tools": [
                {"name": "Qor-logic", "version": version, "vendor": "MythologIQ"},
            ],
            "component": {
                "type": "application",
                "bom-ref": root_ref,
                "name": "qor-logic",
                "version": version,
                "purl": f"pkg:pypi/qor-logic@{version}",
                "description": "Qor-logic governance skills for AI coding hosts",
            },
        },
        "components": components,
        "dependencies": [
            {
                "ref": root_ref,
                "dependsOn": [c["bom-ref"] for c in components],
            },
        ],
    }


def write(repo_root: Path, out_path: Path) -> Path:
    """Emit SBOM and write to ``out_path`` (creates parent dirs as needed)."""
    sbom = emit(repo_root)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(sbom, indent=2), encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.sbom_emit")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=Path("dist/sbom.cdx.json"))
    args = parser.parse_args(argv)

    repo_root = args.repo_root or Path.cwd()
    out = write(repo_root, args.out)
    print(f"SBOM written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
