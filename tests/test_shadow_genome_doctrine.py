"""Phase 15: Shadow Genome countermeasures doctrine + SG-033 static analysis."""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-shadow-genome-countermeasures.md"
QOR_PLAN_SKILL = REPO_ROOT / "qor" / "skills" / "sdlc" / "qor-plan" / "SKILL.md"


def _collect_keyword_only_functions(root: Path) -> dict[str, tuple[Path, int, list[str]]]:
    """Return {fn_name: (def_file, lineno, positional_arg_names)}."""
    out: dict[str, tuple[Path, int, list[str]]] = {}
    for py in root.rglob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.args.kwonlyargs:
                positional = [a.arg for a in node.args.args]
                out[node.name] = (py, node.lineno, positional)
    return out


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _find_positional_violations(
    kwonly_fns: dict[str, tuple[Path, int, list[str]]],
    search_roots: list[Path],
) -> list[tuple[Path, int, str]]:
    violations: list[tuple[Path, int, str]] = []
    for root in search_roots:
        for py in root.rglob("*.py"):
            tree = ast.parse(py.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = _call_name(node)
                if name not in kwonly_fns:
                    continue
                _, _, positional = kwonly_fns[name]
                concrete_args = [a for a in node.args if not isinstance(a, ast.Starred)]
                if len(concrete_args) > len(positional):
                    violations.append((py, node.lineno, name))
    return violations


# ----- Doctrine content tests -----

def test_doctrine_shadow_genome_countermeasures_exists():
    assert DOCTRINE.exists(), f"Missing: {DOCTRINE}"


def test_doctrine_lists_all_sg_ids():
    body = DOCTRINE.read_text(encoding="utf-8")
    for sg in ("SG-016", "SG-017", "SG-019", "SG-020", "SG-021",
              "SG-032", "SG-033", "SG-034", "SG-035",
              "SG-036", "SG-037", "SG-038"):
        assert sg in body, f"Doctrine must contain {sg}"


def test_doctrine_documents_sg033_keyword_only_countermeasure():
    body = DOCTRINE.read_text(encoding="utf-8")
    assert re.search(r"SG-033.{0,500}keyword-only", body, re.DOTALL), (
        "SG-033 section must contain 'keyword-only' within 500 chars of the ID"
    )
    assert re.search(r"SG-033.{0,500}grep", body, re.DOTALL), (
        "SG-033 section must contain 'grep' within 500 chars of the ID"
    )


def test_doctrine_documents_sg032_batch_split_countermeasure():
    body = DOCTRINE.read_text(encoding="utf-8")
    assert re.search(r"SG-032.{0,500}(batch.split|batch-split|classify)",
                     body, re.DOTALL), (
        "SG-032 section must contain 'batch-split' or 'classify' within 500 chars of the ID"
    )


def test_qor_plan_skill_cites_countermeasures_doctrine():
    text = QOR_PLAN_SKILL.read_text(encoding="utf-8")
    assert "doctrine-shadow-genome-countermeasures.md" in text, (
        "qor-plan/SKILL.md must cite the countermeasures doctrine"
    )


# ----- SG-033 static analysis -----

def test_no_positional_calls_to_keyword_only_functions():
    scripts = REPO_ROOT / "qor" / "scripts"
    tests = REPO_ROOT / "tests"
    kwonly_fns = _collect_keyword_only_functions(scripts)
    violations = _find_positional_violations(kwonly_fns, [scripts, tests])
    assert violations == [], (
        "Positional calls to keyword-only functions: " +
        "; ".join(f"{p}:{ln} {name}" for p, ln, name in violations)
    )


# ----- Rule 4 regression tests -----

def test_star_unpack_call_not_flagged(tmp_path):
    """V-1 closure: ast.Starred in call args must not be counted as positional."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "module.py").write_text(
        "def target(event, *, attribution=None):\n"
        "    return event\n",
        encoding="utf-8",
    )
    (src / "caller.py").write_text(
        "from module import target\n"
        "def go(event, extra):\n"
        "    return target(event, *extra, attribution='UPSTREAM')\n",
        encoding="utf-8",
    )
    kwonly = _collect_keyword_only_functions(src)
    assert "target" in kwonly
    violations = _find_positional_violations(kwonly, [src])
    assert violations == [], f"Starred call falsely flagged: {violations}"


def test_proximity_anchor_fails_when_section_missing():
    """V-2 closure: the SG-033 proximity anchor must actually detect a missing section."""
    body = DOCTRINE.read_text(encoding="utf-8")
    stripped = re.sub(
        r"SG-033.*?(?=(?:\nSG-|\n## |\Z))",
        "SG-033 (section removed for test)\n\n",
        body,
        count=1,
        flags=re.DOTALL,
    )
    assert "SG-033" in stripped
    assert "keyword-only" not in re.search(
        r"SG-033.{0,500}", stripped, re.DOTALL,
    ).group(0), "Proximity anchor did not detect removed section"


def test_async_keyword_only_functions_detected(tmp_path):
    """V-4 closure: AsyncFunctionDef walkers discover async kwonly functions."""
    src = tmp_path / "async_src"
    src.mkdir()
    (src / "mod.py").write_text(
        "async def async_target(x, *, y=1):\n"
        "    return x + y\n",
        encoding="utf-8",
    )
    kwonly = _collect_keyword_only_functions(src)
    assert "async_target" in kwonly, "AsyncFunctionDef not discovered"


# ----- Phase 16: governance polish -----

QOR_AUDIT_SKILL = REPO_ROOT / "qor" / "skills" / "governance" / "qor-audit" / "SKILL.md"
STEP_EXTENSIONS = (
    REPO_ROOT / "qor" / "skills" / "sdlc" / "qor-plan" / "references" / "step-extensions.md"
)


def test_qor_audit_skill_cites_countermeasures_doctrine():
    text = QOR_AUDIT_SKILL.read_text(encoding="utf-8")
    assert "doctrine-shadow-genome-countermeasures.md" in text, (
        "qor-audit/SKILL.md must cite the countermeasures doctrine in its adversarial sweep"
    )


def test_qor_plan_step_extensions_reference_exists():
    assert STEP_EXTENSIONS.exists(), f"Missing: {STEP_EXTENSIONS}"
    body = STEP_EXTENSIONS.read_text(encoding="utf-8")
    assert "Step 0.5" in body
    assert "Step 1.a" in body
    skill = QOR_PLAN_SKILL.read_text(encoding="utf-8")
    assert "qor/skills/sdlc/qor-plan/references/step-extensions.md" in skill, (
        "qor-plan/SKILL.md must cite step-extensions.md"
    )


def test_step_extensions_content_moved_not_copied():
    """V-2 closure: verbatim extraction must move content, not copy it."""
    skill = QOR_PLAN_SKILL.read_text(encoding="utf-8")
    extensions = STEP_EXTENSIONS.read_text(encoding="utf-8")
    for anchor in ("InterdictionError", "capability_shortfall"):
        assert anchor in extensions, f"{anchor!r} must appear in step-extensions.md"
        assert anchor not in skill, (
            f"{anchor!r} must NOT appear in qor-plan/SKILL.md (content should be moved, not copied)"
        )


# ----- Phase 17a: SG-036, SG-037, SG-038 proximity anchors -----


def test_doctrine_documents_sg036_grace_period():
    body = DOCTRINE.read_text(encoding="utf-8")
    assert re.search(r"SG-036.{0,500}(grace period|deferral|inline)",
                     body, re.DOTALL), (
        "SG-036 section must contain 'grace period', 'deferral', or 'inline' "
        "within 500 chars of the ID"
    )


def test_doctrine_documents_sg037_surface_drift():
    body = DOCTRINE.read_text(encoding="utf-8")
    assert re.search(r"SG-037.{0,500}(surface|moves|combined)",
                     body, re.DOTALL), (
        "SG-037 section must contain 'surface', 'moves', or 'combined' "
        "within 500 chars of the ID"
    )


def test_doctrine_documents_sg038_prose_code_mismatch():
    body = DOCTRINE.read_text(encoding="utf-8")
    assert re.search(r"SG-038.{0,500}(prose|code block|lockstep)",
                     body, re.DOTALL), (
        "SG-038 section must contain 'prose', 'code block', or 'lockstep' "
        "within 500 chars of the ID"
    )
