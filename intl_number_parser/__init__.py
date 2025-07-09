"""International Number Parser - A robust international number parsing library."""

from .candidates import LocaleCandidate, all_candidates
from .core import parse_number
from .detector import LocaleDetector
from .pandas_adapter import parse_series

__version__ = "0.1.0"
__author__ = "International Number Parser Team"
__license__ = "MIT"

__all__ = [
    "LocaleCandidate",
    "LocaleDetector",
    "all_candidates",
    "parse_number",
    "parse_series",
]
