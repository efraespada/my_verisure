#!/usr/bin/env python3
"""Test script for My Verisure CLI."""

import subprocess
import sys
import os

def run_command(command):
    """Run a CLI command and return the result."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def test_cli():
    """Test the CLI functionality."""
    print("🧪 Testing My Verisure CLI...")
    print("=" * 50)
    
    # Test 1: Help command
    print("1. Testing help command...")
    returncode, stdout, stderr = run_command("source venv/bin/activate && python my_verisure_cli.py --help")
    if returncode == 0:
        print("✅ Help command works")
    else:
        print(f"❌ Help command failed: {stderr}")
        return False
    
    # Test 2: Auth status command
    print("\n2. Testing auth status command...")
    returncode, stdout, stderr = run_command("source venv/bin/activate && python my_verisure_cli.py auth status")
    if returncode == 0:
        print("✅ Auth status command works")
    else:
        print(f"❌ Auth status command failed: {stderr}")
        return False
    
    # Test 3: Auth help command
    print("\n3. Testing auth help command...")
    returncode, stdout, stderr = run_command("source venv/bin/activate && python my_verisure_cli.py auth --help")
    if returncode == 0:
        print("✅ Auth help command works")
    else:
        print(f"❌ Auth help command failed: {stderr}")
        return False
    
    # Test 4: Info help command
    print("\n4. Testing info help command...")
    returncode, stdout, stderr = run_command("source venv/bin/activate && python my_verisure_cli.py info --help")
    if returncode == 0:
        print("✅ Info help command works")
    else:
        print(f"❌ Info help command failed: {stderr}")
        return False
    
    # Test 5: Alarm help command
    print("\n5. Testing alarm help command...")
    returncode, stdout, stderr = run_command("source venv/bin/activate && python my_verisure_cli.py alarm --help")
    if returncode == 0:
        print("✅ Alarm help command works")
    else:
        print(f"❌ Alarm help command failed: {stderr}")
        return False
    
    # Test 6: Alarm arm help command
    print("\n6. Testing alarm arm help command...")
    returncode, stdout, stderr = run_command("source venv/bin/activate && python my_verisure_cli.py alarm arm --help")
    if returncode == 0:
        print("✅ Alarm arm help command works")
    else:
        print(f"❌ Alarm arm help command failed: {stderr}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All CLI tests passed!")
    print("\nThe CLI is ready to use. You can now:")
    print("1. Run: python my_verisure_cli.py auth login")
    print("2. Follow the interactive prompts")
    print("3. Use other commands like: python my_verisure_cli.py info installations")
    
    return True

if __name__ == "__main__":
    success = test_cli()
    sys.exit(0 if success else 1)
