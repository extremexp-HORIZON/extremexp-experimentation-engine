"""
eexp_engine_utils - Helper utilities for experimentation engine
"""

__version__ = "0.0.41"

# Import controller proxy
from .controller import UtilsProxy

# Create the utils proxy instance for transparent access
utils = UtilsProxy()

# Import types for type hints
from . import types

__all__ = [
    "utils",
    "types",
]
