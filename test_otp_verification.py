#!/usr/bin/env python3
"""
Test script to verify OTP verification flow.
"""

import sys
import asyncio
import logging

# Add the custom_components directory to the path
sys.path.append('./custom_components/my_verisure')

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_otp_verification():
    """Test the OTP verification flow."""
    try:
        from api import MyVerisureClient
        from api.exceptions import MyVerisureOTPError
        
        # Create a mock client with OTP data
        client = MyVerisureClient(user="test", password="test")
        
        # Mock OTP data
        client._otp_data = {
            "phones": [
                {"id": 0, "phone": "**********975"},
                {"id": 1, "phone": "**********808"}
            ],
            "otp_hash": "test-hash-12345"
        }
        
        logger.info("Testing OTP verification...")
        
        # Test with a mock OTP code
        test_otp_code = "123456"
        
        try:
            # This will fail because we don't have a real session, but we can test the logic
            result = await client.verify_otp(test_otp_code)
            logger.info(f"OTP verification result: {result}")
        except Exception as e:
            logger.info(f"Expected error (no real session): {e}")
        
        # Test with empty OTP code
        try:
            result = await client.verify_otp("")
            logger.info(f"Empty OTP result: {result}")
        except Exception as e:
            logger.info(f"Expected error for empty OTP: {e}")
        
        # Test with None OTP code
        try:
            result = await client.verify_otp(None)
            logger.info(f"None OTP result: {result}")
        except Exception as e:
            logger.info(f"Expected error for None OTP: {e}")
        
        logger.info("🎉 OTP verification tests completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the test."""
    logger.info("🚀 Testing OTP verification...")
    
    success = await test_otp_verification()
    
    if success:
        logger.info("✅ All tests completed!")
    else:
        logger.error("💥 Some tests failed!")

if __name__ == "__main__":
    asyncio.run(main()) 