#!/usr/bin/env python3
"""My Verisure CLI - Executable script."""

import sys
import os

# Add the cli directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'cli'))

# Import and run the main CLI
from cli.main import main
import asyncio

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
