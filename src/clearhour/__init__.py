"""Clear Hour command-line tool: `python -m clearhour`. Engine lives in src/forecast.py (shared, not duplicated)."""
import sys
from pathlib import Path

__version__ = "0.1.0"
REPO_ROOT = Path(__file__).resolve().parents[2]  # editable install: the checkout that holds src/ and scripts/
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
