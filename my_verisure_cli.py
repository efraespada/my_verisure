#!/usr/bin/env python3
"""My Verisure CLI - Executable script."""

import asyncio
import sys

from cli.main import main

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
