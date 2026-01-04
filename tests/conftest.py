import sys
from pathlib import Path

# Ensure the src/ layout is importable in local test runs without installation.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.is_dir():
    sys.path.insert(0, str(SRC))
