#!/usr/bin/env python3
"""Script to run CLI tests."""

import os
import subprocess
from pathlib import Path


def main():
    """Run CLI tests."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent
    tests_dir = Path(__file__).parent

    print("🚀 Running My Verisure CLI Tests")
    print("=" * 50)

    # Change to project root
    os.chdir(project_root)

    # Run tests with different options
    test_commands = [
        # Unit tests
        ["python", "-m", "pytest", str(tests_dir), "-m", "unit", "--tb=short"],
        # Integration tests
        [
            "python",
            "-m",
            "pytest",
            str(tests_dir),
            "-m",
            "integration",
            "--tb=short",
        ],
        # All tests
        ["python", "-m", "pytest", str(tests_dir), "--tb=short"],
        # Tests with coverage
        [
            "python",
            "-m",
            "pytest",
            str(tests_dir),
            "--cov=cli",
            "--cov-report=term-missing",
        ],
    ]

    for i, cmd in enumerate(test_commands, 1):
        print(f"\n📋 Test Run {i}: {' '.join(cmd[3:])}")
        print("-" * 30)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ Tests passed!")
                if result.stdout:
                    print(result.stdout)
            else:
                print("❌ Tests failed!")
                if result.stdout:
                    print("STDOUT:")
                    print(result.stdout)
                if result.stderr:
                    print("STDERR:")
                    print(result.stderr)

        except Exception as e:
            print(f"❌ Error running tests: {e}")

    print("\n🎉 Test execution completed!")


if __name__ == "__main__":
    main()
