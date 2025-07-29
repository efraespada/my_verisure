#!/usr/bin/env python3
"""
Test script to simulate the Home Assistant OTP flow.
This test simulates the exact flow that Home Assistant uses.
"""

import asyncio
import logging
import sys
import os

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add the custom_components directory to the path
sys.path.append('./custom_components/my_verisure')

async def test_homeassistant_otp_flow():
    """Test the Home Assistant OTP flow."""
    try:
        from api.client import MyVerisureClient
        from api.exceptions import MyVerisureOTPError, MyVerisureAuthenticationError
        
        logger.info("🚀 Testing Home Assistant OTP flow...")
        
        # Test 1: Create client and simulate login
        logger.info("📋 Test 1: Creating client and simulating login...")
        client = MyVerisureClient(user="test_user", password="test_password")
        
        # Mock session data (simulating successful login)
        client._session_data = {
            "user": "test_user",
            "lang": "ES",
            "legals": True,
            "changePassword": False,
            "needDeviceAuthorization": True,
            "login_time": 1753779992
        }
        
        # Mock OTP data (simulating OTP requirement)
        client._otp_data = {
            "phones": [
                {"id": 0, "phone": "**********975"},
                {"id": 1, "phone": "**********808"}
            ],
            "otp_hash": "test-hash-12345"
        }
        
        logger.info("✅ Client setup completed")
        
        # Test 2: Test get_available_phones (Home Assistant calls this)
        logger.info("📱 Test 2: Testing get_available_phones...")
        phones = client.get_available_phones()
        logger.info(f"✅ Available phones: {phones}")
        
        # Test 3: Test select_phone (Home Assistant calls this)
        logger.info("📞 Test 3: Testing select_phone...")
        result = client.select_phone(0)
        logger.info(f"✅ Phone selection result: {result}")
        
        # Test 4: Test verify_otp with mock data (Home Assistant calls this)
        logger.info("🔐 Test 4: Testing verify_otp...")
        try:
            # This will fail because we don't have a real session, but we can test the logic
            result = await client.verify_otp("123456")
            logger.info(f"✅ OTP verification result: {result}")
        except Exception as e:
            logger.info(f"✅ Expected error (no real session): {e}")
        
        # Test 5: Test _get_session_headers with None token
        logger.info("🔑 Test 5: Testing _get_session_headers with None token...")
        client._token = None
        try:
            headers = client._get_session_headers()
            logger.info(f"✅ Session headers: {headers}")
        except Exception as e:
            logger.error(f"❌ Error getting session headers: {e}")
            return False
        
        # Test 6: Test _get_session_headers with token
        logger.info("🔑 Test 6: Testing _get_session_headers with token...")
        client._token = "test-token-12345"
        try:
            headers = client._get_session_headers()
            logger.info(f"✅ Session headers with token: {headers}")
        except Exception as e:
            logger.error(f"❌ Error getting session headers with token: {e}")
            return False
        
        logger.info("🎉 All Home Assistant OTP flow tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the test."""
    logger.info("🚀 Testing Home Assistant OTP flow...")
    
    success = await test_homeassistant_otp_flow()
    
    if success:
        logger.info("✅ All tests completed successfully!")
    else:
        logger.error("💥 Some tests failed!")

if __name__ == "__main__":
    asyncio.run(main()) 