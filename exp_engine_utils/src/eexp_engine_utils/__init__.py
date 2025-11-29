"""
eexp_engine_utils - Helper utilities for experimentation engine
"""

__version__ = "0.0.43"

# Import controller proxy
from .controller import UtilsProxy

# Create the utils proxy instance for transparent access
utils = UtilsProxy()

__all__ = [
    "utils",
]
