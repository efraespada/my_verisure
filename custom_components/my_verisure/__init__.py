"""My Verisure integration."""

__version__ = "1.0.0"

# Import specific modules as needed
# Note: These imports are used by the integration
# flake8: noqa: F401, F403
from .core.api import *
from .core.repositories import *
from .core.use_cases import *
from .core.dependency_injection import *

# Import the integration module to expose the setup functions
from . import integration

# Expose the setup functions for Home Assistant
async_setup = integration.async_setup
async_setup_entry = integration.async_setup_entry
async_unload_entry = integration.async_unload_entry 