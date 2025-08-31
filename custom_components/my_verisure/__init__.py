"""My Verisure integration."""

__version__ = "1.0.0"

# Import from core
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

# Import specific modules as needed
# Note: These imports are used by the integration
# flake8: noqa: F401, F403
from core.api import *
from core.repositories import *
from core.use_cases import *
from core.dependency_injection import * 