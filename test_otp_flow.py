#!/usr/bin/env python3
"""
Test script to verify OTP flow works correctly.
"""

import sys
import asyncio
import logging

# Add the custom_components directory to the path
sys.path.append('./custom_components/my_verisure')

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_otp_flow():
    """Test the OTP flow."""
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
            "otp_hash": "test-hash"
        }
        
        logger.info("Testing phone selection...")
        
        # Test phone selection
        phones = client.get_available_phones()
        logger.info(f"Available phones: {phones}")
        
        # Test selecting phone ID 1
        if client.select_phone(1):
            logger.info("✅ Phone selection successful")
        else:
            logger.error("❌ Phone selection failed")
            return False
        
        # Test selecting phone ID 0
        if client.select_phone(0):
            logger.info("✅ Phone selection successful")
        else:
            logger.error("❌ Phone selection failed")
            return False
        
        # Test invalid phone ID
        if not client.select_phone(999):
            logger.info("✅ Invalid phone ID correctly rejected")
        else:
            logger.error("❌ Invalid phone ID should have been rejected")
            return False
        
        logger.info("🎉 All OTP flow tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the test."""
    logger.info("🚀 Testing OTP flow...")
    
    success = await test_otp_flow()
    
    if success:
        logger.info("✅ All tests passed!")
    else:
        logger.error("💥 Some tests failed!")

if __name__ == "__main__":
    asyncio.run(main()) 