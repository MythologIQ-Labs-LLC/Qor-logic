"""Phase 75 P1: substantiate_capability CLI tests."""
import subprocess
import sys


def test_cli_prints_markdown_table_with_expected_columns():
    result = subprocess.run(
        [sys.executable, "-m", "qor.cli", "substantiate-capability"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    stdout = result.stdout
    assert "| Step | Requires | Present | Evidence |" in stdout, (
        "CLI must emit markdown table with the canonical four-column header"
    )
    # At least 12 rows: count occurrences of `|` per row times rows; simplest: count rows by line containing step id
    row_count = sum(1 for line in stdout.splitlines() if line.startswith("| ") and "Step" not in line and "---" not in line)
    assert row_count >= 12, f"Expected 12+ data rows; got {row_count}"


def test_cli_exit_code_zero_when_all_prereqs_present_on_python_host():
    result = subprocess.run(
        [sys.executable, "-m", "qor.cli", "substantiate-capability"],
        capture_output=True, text=True, check=False,
    )
    # V1 contract: CLI exit is always 0 (report is informational).
    assert result.returncode == 0, f"CLI exit must be 0 on Python host; got {result.returncode}: {result.stderr}"
