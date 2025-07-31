#!/usr/bin/env python3
"""
Test script to verify that device variables are now being sent correctly in OTP operations.
"""

import asyncio
import json
import logging
import sys
import os

# Add the custom_components directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

from custom_components.my_verisure.api.client import MyVerisureClient
from custom_components.my_verisure.api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureOTPError,
    MyVerisureDeviceAuthorizationError
)

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_variables_fix():
    """Test that device variables are now being sent correctly."""
    
    # Get credentials from environment or use defaults
    user = os.getenv('VERISURE_USER', 'test_user')
    password = os.getenv('VERISURE_PASSWORD', 'test_password')
    
    print(f"Testing device variables fix for user: {user}")
    print("=" * 60)
    
    client = MyVerisureClient(user=user, password=password)
    
    try:
        # Connect to the API
        print("1. Connecting to My Verisure API...")
        await client.connect()
        print("   ✓ Connected successfully")
        
        # Show device identifiers
        device_info = client.get_device_info()
        print("\n2. Device identifiers:")
        print(f"   UUID: {device_info.get('uuid')}")
        print(f"   Device Name: {device_info.get('device_name')}")
        print(f"   Device Brand: {device_info.get('device_brand')}")
        print(f"   Device OS: {device_info.get('device_os')}")
        print(f"   Device Version: {device_info.get('device_version')}")
        
        # Try to login
        print("\n3. Attempting login...")
        try:
            await client.login()
            print("   ✓ Login successful without OTP")
            return
        except MyVerisureOTPError as e:
            print(f"   ⚠ OTP required: {e}")
        except MyVerisureDeviceAuthorizationError as e:
            print(f"   ❌ Device authorization error: {e}")
            return
        except MyVerisureAuthenticationError as e:
            print(f"   ❌ Authentication failed: {e}")
            return
        
        # Get available phones
        print("\n4. Getting available phone numbers...")
        phones = client.get_available_phones()
        if not phones:
            print("   ❌ No phone numbers available")
            return
        
        print(f"   ✓ Found {len(phones)} phone number(s):")
        for phone in phones:
            print(f"     - ID {phone.get('id')}: {phone.get('phone')}")
        
        # Select first phone
        selected_phone = phones[0]
        phone_id = selected_phone.get('id')
        print(f"\n5. Selecting phone ID {phone_id}...")
        
        if not client.select_phone(phone_id):
            print("   ❌ Failed to select phone")
            return
        
        print("   ✓ Phone selected successfully")
        
        # Send OTP
        print("\n6. Sending OTP...")
        try:
            otp_data = client._otp_data
            record_id = phone_id  # Use the actual phone ID
            otp_hash = otp_data.get('otp_hash')
            
            print(f"   Using record_id: {record_id}")
            print(f"   Using otp_hash: {otp_hash}")
            
            if await client.send_otp(record_id, otp_hash):
                print("   ✓ OTP sent successfully")
                print("   📱 Please check your phone for the SMS")
            else:
                print("   ❌ Failed to send OTP")
                return
        except Exception as e:
            print(f"   ❌ Error sending OTP: {e}")
            return
        
        # Wait for user to enter OTP
        print("\n7. Waiting for OTP verification...")
        print("   Please enter the OTP code received via SMS:")
        
        otp_code = input("   OTP Code: ").strip()
        
        if not otp_code:
            print("   ❌ No OTP code provided")
            return
        
        print(f"\n8. Verifying OTP code: {otp_code}")
        print("   This should now include device variables in the request...")
        
        try:
            if await client.verify_otp(otp_code):
                print("   ✓ OTP verification successful")
                
                # Check device authorization status
                session_data = client._session_data
                need_auth = session_data.get('needDeviceAuthorization', False)
                
                if need_auth:
                    print("   ⚠ WARNING: Device is NOT authorized")
                    print("   ⚠ This device will require OTP on every login")
                    print("   ⚠ Please contact My Verisure support to authorize this device")
                else:
                    print("   ✓ Device is authorized")
                    print("   ✓ Future logins should not require OTP")
                
            else:
                print("   ❌ OTP verification failed")
                
        except MyVerisureDeviceAuthorizationError as e:
            print(f"   ❌ Device authorization failed: {e}")
            print("   This is the expected behavior for unauthorized devices")
            
        except MyVerisureOTPError as e:
            print(f"   ❌ OTP verification failed: {e}")
            
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        print("\n9. Cleaning up...")
        await client.disconnect()
        print("   ✓ Disconnected")

if __name__ == "__main__":
    asyncio.run(test_variables_fix()) 