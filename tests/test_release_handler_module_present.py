"""Phase 55: tests for the release handler module."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_release_handler_register_function_exists():
    from qor.cli_handlers.release import register, dispatch
    assert callable(register)
    assert callable(dispatch)


def test_qor_cli_dispatches_release_subcommand():
    proc = subprocess.run(
        [sys.executable, "-m", "qor.cli", "release", "sbom", "--help"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0
    assert "sbom" in proc.stdout.lower()


def test_qor_cli_release_help_advertises_sbom_subcommand():
    proc = subprocess.run(
        [sys.executable, "-m", "qor.cli", "release", "--help"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0
    assert "sbom" in proc.stdout.lower()


def test_deliver_phase_in_validate_gate_artifact_phases():
    """Phase 55: closes pre-existing surface gap."""
    from qor.scripts.validate_gate_artifact import PHASES
    assert "deliver" in PHASES, "PHASES must include 'deliver' for qor-repo-release writes"


def test_deliver_schema_validates_minimal_payload():
    """Phase 55: deliver.schema.json accepts minimal payload."""
    from qor.scripts import validate_gate_artifact as vga
    payload = {
        "phase": "deliver",
        "ts": "2026-05-01T18:00:00Z",
        "session_id": "test-deliver",
        "version": "0.41.0",
    }
    errs = vga._validate_data("deliver", payload)
    assert errs == [], f"minimal deliver payload must validate; got: {errs}"


def test_deliver_schema_accepts_sbom_path_field():
    """Phase 55: optional sbom_path field validates."""
    from qor.scripts import validate_gate_artifact as vga
    payload = {
        "phase": "deliver",
        "ts": "2026-05-01T18:00:00Z",
        "session_id": "test-deliver",
        "version": "0.41.0",
        "sbom_path": "dist/sbom.cdx.json",
    }
    errs = vga._validate_data("deliver", payload)
    assert errs == [], f"deliver with sbom_path must validate; got: {errs}"


def test_deliver_schema_rejects_missing_version():
    from qor.scripts import validate_gate_artifact as vga
    payload = {
        "phase": "deliver",
        "ts": "2026-05-01T18:00:00Z",
        "session_id": "test-deliver",
    }
    errs = vga._validate_data("deliver", payload)
    assert errs, "deliver without version must fail validation"
