"""Compatibility import for the shared phase-level Result module."""

from pathlib import Path
import sys


PHASE_ROOT = Path(__file__).resolve().parents[1]
if str(PHASE_ROOT) not in sys.path:
    sys.path.insert(0, str(PHASE_ROOT))

from result import Err, Ok, Result  # noqa: E402, F401
