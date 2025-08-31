#!/usr/bin/env python3
"""Test script for My Verisure CLI."""

import sys
import os
from unittest.mock import patch
from io import StringIO

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from cli.main import create_parser, setup_logging


def test_cli():
    """Test the CLI functionality."""
    print("🧪 Testing My Verisure CLI...")
    print("=" * 50)

    # Test 1: Parser creation
    print("1. Testing parser creation...")
    parser = create_parser()
    assert parser is not None
    print("✅ Parser creation works")

    # Test 2: Help command
    print("\n2. Testing help command...")
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        parser.print_help()
        help_output = mock_stdout.getvalue()
        assert "My Verisure CLI" in help_output
        assert "auth" in help_output
        assert "info" in help_output
        assert "alarm" in help_output
    print("✅ Help command works")

    # Test 3: Auth subcommand parsing
    print("\n3. Testing auth subcommand parsing...")
    args = parser.parse_args(["auth", "status"])
    assert args.command == "auth"
    assert args.action == "status"
    print("✅ Auth subcommand parsing works")

    # Test 4: Info subcommand parsing
    print("\n4. Testing info subcommand parsing...")
    args = parser.parse_args(["info", "installations"])
    assert args.command == "info"
    assert args.action == "installations"
    print("✅ Info subcommand parsing works")

    # Test 5: Alarm subcommand parsing
    print("\n5. Testing alarm subcommand parsing...")
    args = parser.parse_args(["alarm", "status"])
    assert args.command == "alarm"
    assert args.action == "status"
    print("✅ Alarm subcommand parsing works")

    # Test 6: Alarm arm subcommand parsing
    print("\n6. Testing alarm arm subcommand parsing...")
    args = parser.parse_args(["alarm", "arm", "--mode", "away"])
    assert args.command == "alarm"
    assert args.action == "arm"
    assert args.mode == "away"
    print("✅ Alarm arm subcommand parsing works")

    # Test 7: Logging setup
    print("\n7. Testing logging setup...")
    with patch("logging.basicConfig") as mock_basic_config:
        setup_logging(verbose=True)
        mock_basic_config.assert_called_once()
    print("✅ Logging setup works")

    print("\n" + "=" * 50)
    print("🎉 All CLI tests passed!")
    print("\nThe CLI is ready to use. You can now:")
    print("1. Run: python my_verisure_cli.py auth login")
    print("2. Follow the interactive prompts")
    print(
        "3. Use other commands like: python my_verisure_cli.py info installations"
    )


if __name__ == "__main__":
    test_cli()
    sys.exit(0)
