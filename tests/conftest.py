"""Pytest config: put qor/scripts and tests/ on sys.path for imports."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "qor" / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
