#!/usr/bin/env python3
"""
Test script to debug request body being sent in OTP operations.
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

def print_request_data(title: str, data: dict):
    """Print request data in a formatted way."""
    print(f"\n{title}")
    print("=" * 50)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print()

async def test_body_debug():
    """Test and debug request body in OTP operations."""
    
    # Get credentials from environment or use defaults
    user = os.getenv('VERISURE_USER', 'test_user')
    password = os.getenv('VERISURE_PASSWORD', 'test_password')
    
    print(f"Debugging request body for user: {user}")
    print("=" * 60)
    
    client = MyVerisureClient(user=user, password=password)
    
    try:
        # Connect to the API
        print("1. Connecting to My Verisure API...")
        await client.connect()
        print("   ✓ Connected successfully")
        
        # Try to login
        print("2. Attempting login...")
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
        print("\n3. Getting available phone numbers...")
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
        print(f"\n4. Selecting phone ID {phone_id}...")
        
        if not client.select_phone(phone_id):
            print("   ❌ Failed to select phone")
            return
        
        print("   ✓ Phone selected successfully")
        
        # Show OTP send request body
        print("\n5. OTP Send Request Body...")
        otp_data = client._otp_data
        record_id = 0  # Default to first phone
        otp_hash = otp_data.get('otp_hash')
        
        otp_send_variables = {
            "recordId": record_id,
            "otpHash": otp_hash
        }
        
        otp_send_body = {
            "query": """
            mutation mkSendOTP($recordId: Int!, $otpHash: String!) {
                xSSendOtp(recordId: $recordId, otpHash: $otpHash) {
                    res
                    msg
                }
            }
            """,
            "variables": otp_send_variables
        }
        
        print_request_data("OTP SEND REQUEST BODY", otp_send_body)
        
        # Send OTP
        print("6. Sending OTP...")
        try:
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
        
        # Show OTP verification request body
        print(f"\n8. OTP Verification Request Body...")
        
        otp_verification_body = {
            "query": """
            mutation mkValidateDevice($idDevice: String, $idDeviceIndigitall: String, $uuid: String, $deviceName: String, $deviceBrand: String, $deviceOsVersion: String, $deviceVersion: String) {
                xSValidateDevice(
                    idDevice: $idDevice
                    idDeviceIndigitall: $idDeviceIndigitall
                    uuid: $uuid
                    deviceName: $deviceName
                    deviceBrand: $deviceBrand
                    deviceOsVersion: $deviceOsVersion
                    deviceVersion: $deviceVersion
                ) {
                    res
                    msg
                    hash
                    refreshToken
                    legals
                }
            }
            """,
            "variables": {}
        }
        
        print_request_data("OTP VERIFICATION REQUEST BODY", otp_verification_body)
        
        # Show what would be in the Security header
        security_header = {
            "token": otp_code,
            "type": "OTP",
            "otpHash": otp_data.get('otp_hash')
        }
        
        print_request_data("SECURITY HEADER CONTENT", security_header)
        
        print(f"\n9. Verifying OTP code: {otp_code}")
        
        try:
            if await client.verify_otp(otp_code):
                print("   ✓ OTP verification successful")
                
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
        print("\n10. Cleaning up...")
        await client.disconnect()
        print("   ✓ Disconnected")

if __name__ == "__main__":
    asyncio.run(test_body_debug()) 