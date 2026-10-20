"""Make the source-layout package available without installing dependencies."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = str(ROOT / "src")
if SOURCE not in sys.path:
	sys.path.insert(0, SOURCE)
