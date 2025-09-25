"""Configuration for Core tests."""

import sys
from pathlib import Path

# Add the core directory to the Python path
core_dir = Path(__file__).parent.parent
sys.path.insert(0, str(core_dir))

# Also add the project root to the path for any cross-module imports
project_root = core_dir.parent
sys.path.insert(0, str(project_root))
