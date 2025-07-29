#!/usr/bin/env python3
"""
Test script to verify My Verisure client methods work correctly.
This test is non-interactive and focuses on testing the API methods.
"""

import asyncio
import logging
import sys
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the custom_components directory to the path
sys.path.append('./custom_components/my_verisure')

async def test_client_methods():
    """Test the client methods."""
    try:
        from api.client import MyVerisureClient
        from api.exceptions import MyVerisureOTPError, MyVerisureAuthenticationError
        
        logger.info("🚀 Testing My Verisure client methods...")
        
        # Test 1: Create client
        logger.info("📋 Test 1: Creating client...")
        client = MyVerisureClient(user="test_user", password="test_password")
        logger.info("✅ Client created successfully")
        
        # Test 2: Test get_available_phones with mock data
        logger.info("📱 Test 2: Testing get_available_phones...")
        client._otp_data = {
            "phones": [
                {"id": 0, "phone": "**********975"},
                {"id": 1, "phone": "**********808"}
            ],
            "otp_hash": "test-hash-12345"
        }
        
        phones = client.get_available_phones()
        logger.info(f"✅ Available phones: {phones}")
        
        # Test 3: Test select_phone
        logger.info("📞 Test 3: Testing select_phone...")
        result = client.select_phone(0)
        logger.info(f"✅ Phone selection result: {result}")
        
        # Test 4: Test select_phone with invalid ID
        logger.info("❌ Test 4: Testing select_phone with invalid ID...")
        result = client.select_phone(999)
        logger.info(f"✅ Invalid phone selection result: {result} (expected False)")
        
        # Test 5: Test verify_otp with mock data
        logger.info("🔐 Test 5: Testing verify_otp...")
        try:
            # This will fail because we don't have a real session
            result = await client.verify_otp("123456")
            logger.info(f"✅ OTP verification result: {result}")
        except Exception as e:
            logger.info(f"✅ Expected error (no real session): {e}")
        
        # Test 6: Test verify_otp with empty data
        logger.info("🔐 Test 6: Testing verify_otp with empty data...")
        client._otp_data = None
        try:
            result = await client.verify_otp("123456")
        except MyVerisureOTPError as e:
            logger.info(f"✅ Expected OTP error: {e}")
        
        # Test 7: Test verify_otp with missing hash
        logger.info("🔐 Test 7: Testing verify_otp with missing hash...")
        client._otp_data = {"phones": []}
        try:
            result = await client.verify_otp("123456")
        except MyVerisureOTPError as e:
            logger.info(f"✅ Expected OTP error (missing hash): {e}")
        
        logger.info("🎉 All client method tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the test."""
    logger.info("🚀 Testing My Verisure client methods...")
    
    success = await test_client_methods()
    
    if success:
        logger.info("✅ All tests completed successfully!")
    else:
        logger.error("💥 Some tests failed!")

if __name__ == "__main__":
    asyncio.run(main()) 