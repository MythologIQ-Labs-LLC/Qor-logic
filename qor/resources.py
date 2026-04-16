"""Packaged-asset accessors for qor.

Uses importlib.resources so paths resolve correctly whether the package
is installed editable, from a wheel, or via sys.path manipulation.
"""
from __future__ import annotations

from importlib.resources import files


def _root():
    """Return a Traversable pointing at the ``qor`` package directory."""
    return files("qor")


def asset(*parts: str):
    """Resolve a packaged file path, e.g. ``asset("templates", "foo.md")``."""
    node = _root()
    for p in parts:
        node = node.joinpath(p)
    return node


def schema(name: str):
    """Shorthand for ``qor/gates/schema/<name>``."""
    return asset("gates", "schema", name)


def doctrine(name: str):
    """Shorthand for ``qor/references/<name>``."""
    return asset("references", name)
