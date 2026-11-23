#!/usr/bin/env python3
"""Compatibility entry point for the canonical CLI test gate.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from pathlib import Path
import subprocess


def main() -> int:
    """Run one CLI suite with Makefile interpreter selection and exit status."""
    root = Path(__file__).resolve().parents[2]
    return subprocess.run(["make", "test-cli"], cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
