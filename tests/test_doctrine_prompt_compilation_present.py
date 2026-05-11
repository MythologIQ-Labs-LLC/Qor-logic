"""Phase 50 doctrine presence + structure tests."""
from __future__ import annotations

from pathlib import Path

PATH = (
    Path(__file__).resolve().parent.parent
    / "qor" / "references" / "doctrine-prompt-compilation.md"
)


def _body():
    return PATH.read_text(encoding="utf-8")


def test_doctrine_file_exists():
    assert PATH.exists()


def test_doctrine_declares_v1_scope_section():
    body = _body()
    assert "## V1 scope" in body
    assert "Phase 50" in body


def test_doctrine_declares_v2_plus_deferrals_section():
    body = _body()
    assert "## V2+ deferrals" in body
    for token in ("Governance gate", "Rulepack registry", "Execution modes", "Evaluation loop"):
        assert token in body


def test_doctrine_states_stdlib_only_discipline():
    body = _body()
    assert "Stdlib-only discipline" in body
    assert "no Pydantic" in body or "No Pydantic" in body or "no Pydantic" in body.lower()


def test_doctrine_cites_anti_pattern_parallel_provider_compile_by_default():
    body = _body()
    assert "Anti-pattern" in body
    assert "parallel provider compile" in body.lower()
    assert "_PROVIDERS" in body or "compile_prompt" in body


def test_doctrine_cites_gh_39():
    body = _body()
    assert "#39" in body


def test_doctrine_cites_roadmap_doc():
    body = _body()
    assert "docs/roadmap-prompt-compiler.md" in body
