"""My Verisure integration."""

__version__ = "1.0.0"

# Import from core
import sys
import os
# Add the my_verisure directory to the path so we can import core
my_verisure_path = os.path.dirname(__file__)
sys.path.insert(0, my_verisure_path)

# Import specific modules as needed
# Note: These imports are used by the integration
# flake8: noqa: F401, F403
from core.api import *
from core.repositories import *
from core.use_cases import *
from core.dependency_injection import * 