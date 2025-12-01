import os
import sys
from pathlib import Path

# add src/ to path so tests can import internal modules
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("MLOPS_ENV", "test")
