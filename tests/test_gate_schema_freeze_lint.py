"""Phase 169 (GH #251b): artifact-freeze lint tests."""
from __future__ import annotations

import json
from pathlib import Path

from qor.scripts import gate_schema_freeze_lint as lint

_REPO = Path(__file__).resolve().parents[1]


def _setup(tmp_path: Path, schemas: list[str], registry: list[str],
           declared: list[str] | None = None) -> Path:
    schema_dir = tmp_path / "qor" / "gates" / "schema"
    schema_dir.mkdir(parents=True)
    for name in schemas:
        (schema_dir / f"{name}.schema.json").write_text("{}", encoding="utf-8")
    (tmp_path / "qor" / "gates" / "SCHEMA_REGISTRY.json").write_text(
        json.dumps({"schemas": registry}), encoding="utf-8")
    if declared is not None:
        sess = tmp_path / ".qor" / "gates" / "2026-07-04T1200-abc123"
        sess.mkdir(parents=True)
        (sess / "plan.json").write_text(json.dumps({
            "phase": "plan",
            "new_ceremony_artifacts": [
                {"name": f"{n}.schema.json",
                 "justification": "L3 justification " + "x" * 100} for n in declared
            ],
        }), encoding="utf-8")
    return tmp_path


def test_lint_flags_only_unregistered_undeclared(tmp_path, capsys):
    root = _setup(tmp_path, schemas=["plan", "shiny"], registry=["plan"])
    rc = lint.main(["--repo-root", str(root)])
    out = capsys.readouterr().out
    assert rc == 1
    assert "shiny" in out and "plan.schema.json" not in out.replace("shiny", "")
    # a plan-declared justification exempts it
    root2 = _setup(tmp_path / "b", schemas=["plan", "shiny"], registry=["plan"],
                   declared=["shiny"])
    rc = lint.main(["--repo-root", str(root2), "--session", "2026-07-04T1200-abc123"])
    assert rc == 0
    # fully registered: clean
    root3 = _setup(tmp_path / "c", schemas=["plan"], registry=["plan"])
    assert lint.main(["--repo-root", str(root3)]) == 0


def test_live_registry_matches_directory():
    registry = json.loads(
        (_REPO / "qor" / "gates" / "SCHEMA_REGISTRY.json").read_text(encoding="utf-8")
    )["schemas"]
    present = sorted(
        p.name.removesuffix(".schema.json")
        for p in (_REPO / "qor" / "gates" / "schema").glob("*.schema.json")
    )
    assert sorted(registry) == present, (
        "SCHEMA_REGISTRY.json must cover exactly the schemas in qor/gates/schema/ "
        "(register new ceremony artifacts deliberately per GH #251)"
    )
