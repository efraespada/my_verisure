#!/usr/bin/env python3
"""
Test script for My Verisure login.
This script allows you to test authentication with the GraphQL API.
"""

import asyncio
import logging
import sys
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add current directory to path to import the api module
sys.path.append('./custom_components/my_verisure')

try:
    from api.client import MyVerisureClient
    from api.exceptions import (
        MyVerisureAuthenticationError,
        MyVerisureConnectionError,
        MyVerisureError,
    )
except ImportError as e:
    logger.error(f"Could not import api module: {e}")
    logger.error("Make sure you are in the correct project directory")
    sys.exit(1)


async def test_login(user: str, password: str) -> None:
    """Test login with My Verisure API."""
    logger.info("🧪 Starting login test...")
    
    client = MyVerisureClient(user=user, password=password)
    
    try:
        # Connect
        logger.info("📡 Connecting to API...")
        await client.connect()
        logger.info("✅ Connection established")
        
        # Try login
        logger.info("🔐 Attempting login...")
        success = await client.login()
        
        if success:
            logger.info("✅ Login successful!")
            logger.info(f"🔑 Token obtained: {client._token[:20]}..." if client._token else "❌ No token obtained")
        else:
            logger.error("❌ Login failed")
            
    except MyVerisureAuthenticationError as e:
        logger.error(f"❌ Authentication error: {e}")
        logger.info("💡 Verify your user (DNI/NIE) and password")
        
    except MyVerisureConnectionError as e:
        logger.error(f"❌ Connection error: {e}")
        logger.info("💡 Verify your internet connection and API URL")
        
    except MyVerisureError as e:
        logger.error(f"❌ My Verisure error: {e}")
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        
    finally:
        # Disconnect
        logger.info("🔌 Disconnecting...")
        await client.disconnect()
        logger.info("✅ Disconnection completed")


def main():
    """Main function."""
    print("🚀 My Verisure Login Test Script")
    print("=" * 50)
    
    # Check arguments
    if len(sys.argv) != 3:
        print("Usage: python test_login.py <user> <password>")
        print("Example: python test_login.py 12345678D my_password")
        print("Note: The user should be your DNI/NIE (without letter)")
        sys.exit(1)
    
    user = sys.argv[1]
    password = sys.argv[2]
    
    print(f"👤 User: {user}")
    print(f"🔑 Password: {'*' * len(password)}")
    print()
    
    # Run test
    try:
        asyncio.run(test_login(user, password))
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error running test: {e}")


if __name__ == "__main__":
    main() 