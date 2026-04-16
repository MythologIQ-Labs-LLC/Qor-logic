"""Integration tests for packaging install-smoke (Phase 20).

These verify that the package installs correctly and key entry points
resolve. Skipped under default pytest (addopts excludes integration).
Run with: pytest -m integration tests/test_packaging_install.py
"""
from __future__ import annotations

import pytest


pytestmark = pytest.mark.integration


def test_qor_package_importable():
    """qor package and its subpackages import without error."""
    import qor
    import qor.scripts
    import qor.reliability
    assert hasattr(qor, "__name__")


def test_resources_resolve_schema():
    """qor.resources.schema() returns a traversable that exists."""
    from qor import resources
    schema = resources.schema("shadow_event.schema.json")
    # importlib.resources returns a Traversable; read_text should work
    text = schema.read_text(encoding="utf-8")
    assert "shadow_event" in text or "properties" in text


def test_workdir_root_returns_path():
    """qor.workdir.root() returns a Path object."""
    from qor import workdir
    from pathlib import Path
    r = workdir.root()
    assert isinstance(r, Path)


def test_scripts_importable_as_package():
    """Key script modules import via package path."""
    from qor.scripts import shadow_process
    from qor.scripts import session
    from qor.scripts import gate_chain
    assert callable(shadow_process.compute_id)
    assert callable(session.generate_id)
