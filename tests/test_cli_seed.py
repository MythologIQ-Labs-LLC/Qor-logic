"""Phase 25 Phase 1: qorlogic seed CLI subcommand."""
from __future__ import annotations

import pytest


def test_cli_seed_default_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from qor.cli import main
    rc = main(["seed"])
    assert rc == 0
    assert (tmp_path / "docs/META_LEDGER.md").exists()


def test_cli_seed_with_target(tmp_path):
    from qor.cli import main
    rc = main(["seed", "--target", str(tmp_path)])
    assert rc == 0
    assert (tmp_path / "docs/META_LEDGER.md").exists()
    assert (tmp_path / ".qor/gates/.gitkeep").exists()


def test_cli_seed_listed_in_help(capsys):
    from qor.cli import main
    with pytest.raises(SystemExit):
        main(["--help"])
    help_text = capsys.readouterr().out
    assert "seed" in help_text


def test_cli_seed_idempotent_reports_skips(tmp_path, capsys):
    from qor.cli import main
    rc1 = main(["seed", "--target", str(tmp_path)])
    assert rc1 == 0
    capsys.readouterr()  # clear
    rc2 = main(["seed", "--target", str(tmp_path)])
    assert rc2 == 0
    out = capsys.readouterr().out
    assert "skipped" in out.lower() or "already" in out.lower()
