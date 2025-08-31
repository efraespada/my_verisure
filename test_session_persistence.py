#!/usr/bin/env python3
"""Test script for session persistence."""

import subprocess
import sys
import os
import time

def run_command(command, capture_output=True):
    """Run a CLI command and return the result."""
    try:
        if capture_output:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            return result.returncode, result.stdout, result.stderr
        else:
            result = subprocess.run(
                command,
                shell=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            return result.returncode, "", ""
    except Exception as e:
        return 1, "", str(e)

def test_session_persistence():
    """Test session persistence functionality."""
    print("🧪 Testing Session Persistence...")
    print("=" * 50)
    
    # Test 1: Check initial status
    print("1. Checking initial status...")
    returncode, stdout, stderr = run_command("source venv/bin/activate && python my_verisure_cli.py auth status")
    if returncode == 0:
        print("✅ Initial status check works")
        if "No configurado" in stdout:
            print("   ℹ️  No session found (expected)")
    else:
        print(f"❌ Initial status check failed: {stderr}")
        return False
    
    # Test 2: Show help for login
    print("\n2. Showing login help...")
    returncode, stdout, stderr = run_command("source venv/bin/activate && python my_verisure_cli.py auth login --help")
    if returncode == 0:
        print("✅ Login help works")
    else:
        print(f"❌ Login help failed: {stderr}")
        return False
    
    # Test 3: Show help for logout
    print("\n3. Showing logout help...")
    returncode, stdout, stderr = run_command("source venv/bin/activate && python my_verisure_cli.py auth logout --help")
    if returncode == 0:
        print("✅ Logout help works")
    else:
        print(f"❌ Logout help failed: {stderr}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Session persistence tests completed!")
    print("\nTo test full session persistence:")
    print("1. Run: python my_verisure_cli.py auth login")
    print("2. Complete the login process")
    print("3. Run: python my_verisure_cli.py auth status")
    print("4. Should show '✅ Autenticado'")
    print("5. Run: python my_verisure_cli.py auth logout")
    print("6. Run: python my_verisure_cli.py auth status")
    print("7. Should show '⚠️ No autenticado'")
    
    return True

if __name__ == "__main__":
    success = test_session_persistence()
    sys.exit(0 if success else 1)
