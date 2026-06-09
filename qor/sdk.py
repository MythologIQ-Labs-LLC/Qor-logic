"""Stable downstream SDK facade (Phase 142).

Re-exports the enforcement entry points so consumers import a stable top-level
path. NOTE: the import package is ``qor`` (the PyPI distribution is
``qor-logic``); import as ``from qor.sdk import enforce``.
"""
from qor.compliance.enforce import ControlResult, Verdict, enforce, run_control

__all__ = ["enforce", "run_control", "Verdict", "ControlResult"]
