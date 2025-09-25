"""My Verisure Core - Common library for My Verisure integration and CLI."""

__version__ = "1.0.0"
__author__ = "My Verisure Team"

# Export main components
from . import api
from . import repositories
from . import use_cases
from . import dependency_injection

__all__ = [
    "api",
    "repositories", 
    "use_cases",
    "dependency_injection",
]
