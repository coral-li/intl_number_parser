"""International Number Parser - A robust international number parsing library."""

from .candidates import LocaleCandidate, all_candidates
from .core import parse_number
from .detector import LocaleDetector

__version__ = "0.1.0"
__author__ = "International Number Parser Team"
__license__ = "MIT"

# Core functionality always available
__all__ = [
    "LocaleCandidate",
    "LocaleDetector",
    "all_candidates",
    "parse_number",
]

# Conditionally import pandas functionality
try:
    from .pandas_adapter import parse_series

    __all__ += ["parse_series"]
except ImportError:  # noqa: S110
    # pandas not available, parse_series will not be available
    # This is intentional - pandas is an optional dependency
    pass
