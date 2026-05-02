"""Phase 57: missing .qor/hooks.yaml → empty hook list, no error."""
from __future__ import annotations

from pathlib import Path

from qor.scripts import gate_hooks


def test_missing_hooks_yaml_returns_empty_list(tmp_path: Path):
    # No .qor/hooks.yaml created
    targets = gate_hooks._load_config_file_hooks(tmp_path)
    assert targets == []


def test_missing_qor_dir_returns_empty_list(tmp_path: Path):
    # Not even .qor directory
    targets = gate_hooks._load_config_file_hooks(tmp_path)
    assert targets == []
