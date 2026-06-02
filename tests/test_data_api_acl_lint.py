"""Behavioral tests for qor.scripts.data_api_acl_lint (Phase 121; GH #177).

Each test invokes the unit (analyze / main / parse_*) and asserts on its output,
not on artifact presence. Synthetic SQL is written under a tmp migrations dir.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts import data_api_acl_lint as acl


def _write_migration(base: Path, name: str, sql: str) -> Path:
    d = base / "supabase" / "migrations"
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text(sql, encoding="utf-8")
    return p


def _kinds(result: acl.AclResult) -> list[str]:
    return [f.kind for f in result.findings]


def test_missing_grant_flagged(tmp_path: Path) -> None:
    _write_migration(tmp_path, "0001_init.sql", "CREATE TABLE public.items (id int);\n")
    result = acl.analyze(tmp_path)
    grant_findings = [f for f in result.findings if f.kind == "missing-grant"]
    assert len(grant_findings) == 1
    assert "public.items" in grant_findings[0].object_name


def test_grant_to_authenticated_clears(tmp_path: Path) -> None:
    _write_migration(
        tmp_path,
        "0001_init.sql",
        "CREATE TABLE public.items (id int);\n"
        "GRANT SELECT ON public.items TO authenticated;\n",
    )
    result = acl.analyze(tmp_path)
    assert "missing-grant" not in _kinds(result)


def test_service_role_only_escape_clears(tmp_path: Path) -> None:
    _write_migration(
        tmp_path,
        "0001_init.sql",
        "-- qor:service-role-only\n"
        "CREATE TABLE public.secrets (id int);\n"
        "REVOKE ALL ON public.secrets FROM authenticated;\n",
    )
    result = acl.analyze(tmp_path)
    assert "missing-grant" not in _kinds(result)


def test_definer_view_flagged(tmp_path: Path) -> None:
    _write_migration(
        tmp_path,
        "0002_view.sql",
        "CREATE VIEW public.v AS SELECT id FROM public.items;\n",
    )
    result = acl.analyze(tmp_path)
    view_findings = [f for f in result.findings if f.kind == "definer-view"]
    assert len(view_findings) == 1
    assert "public.v" in view_findings[0].object_name


def test_security_invoker_view_clears(tmp_path: Path) -> None:
    _write_migration(
        tmp_path,
        "0002_view.sql",
        "CREATE VIEW public.v WITH (security_invoker = true) "
        "AS SELECT id FROM public.items;\n",
    )
    result = acl.analyze(tmp_path)
    assert "definer-view" not in _kinds(result)


def test_security_definer_fn_is_advisory(tmp_path: Path) -> None:
    _write_migration(
        tmp_path,
        "0003_fn.sql",
        "CREATE FUNCTION public.do_it() RETURNS void "
        "LANGUAGE sql SECURITY DEFINER AS $$ SELECT 1 $$;\n",
    )
    result = acl.analyze(tmp_path)
    assert "security-definer-fn" in _kinds(result)
    # Advisory only: a SECURITY DEFINER function alone does not fail the gate.
    assert acl.main(["--repo-root", str(tmp_path)]) == 0


def test_main_exit_1_on_blocking(tmp_path: Path) -> None:
    _write_migration(tmp_path, "0001_init.sql", "CREATE TABLE public.items (id int);\n")
    assert acl.main(["--repo-root", str(tmp_path)]) == 1


def test_main_exit_0_and_skip_line_when_no_migrations(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = acl.main(["--repo-root", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "SKIP:" in out


def test_non_api_schema_table_not_flagged(tmp_path: Path) -> None:
    _write_migration(
        tmp_path, "0001_init.sql", "CREATE TABLE internal.audit_log (id int);\n"
    )
    result = acl.analyze(tmp_path, api_schemas=("public",))
    assert _kinds(result) == []


def test_analyze_skipped_when_no_migrations(tmp_path: Path) -> None:
    result = acl.analyze(tmp_path)
    assert result.skipped is True
    assert result.findings == ()


def test_doctrine_documents_finding_kinds() -> None:
    """Inverse-coverage doc-contract: every emitted finding kind is documented
    in the reference, so the doc cannot drift from the code."""
    doc = Path("qor/references/doctrine-runtime-principal-fidelity.md").read_text(
        encoding="utf-8"
    )
    for kind in acl.KNOWN_FINDING_KINDS:
        assert kind in doc, f"finding kind {kind!r} not documented in reference"
